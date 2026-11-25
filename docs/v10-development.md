# v1.0 实现与复跑入口

v1.0.0 的功能验收以 `c9d6113` 为基线，安装包采集入口在 `2f4d427` 验收。下文给出采集示例和复跑入口。

## dev3 新增

- `--retest-snapshots WORKING BEFORE AFTER` 从三份有界快照重新生成旧比较和当前比较，保留旧解释及证据引用。T3 须晚于两份旧快照，结果过期或来自其他会话时不用于判断本次成功或失败。
- PowerShell 原会话脚本增加 `-ProbeVersion`。默认采集仍不执行工具。显式版本查询只运行一个匹配的已识别启动器，走原有隔离运行器，输出仅保留完整三段数字。版本查询与原命令结果各有独立记录。
- 快照可选记录优先启动器目录代号。比较按进程 PATH、HKCU 和 HKLM 路径分别观察目录，复测可以显示同一持久层中的目录从 T2 进程缺失变为 T3 进程出现。旧快照仍可读取，缺少的新证据保持未知。实际刷新、继承历史或父进程来源不能从两个时间点反推。

```powershell
& .\scripts\Capture-WADSnapshot.ps1 -Command codex -SessionRole failing -Symptom wrong_version -ProbeVersion -OutputDirectory .\before
# 在复测会话重新采集，按本次实际结果选择 success、failure 或 unverified
& .\scripts\Capture-WADSnapshot.ps1 -Command codex -SessionRole failing -Symptom wrong_version -ProbeVersion -CommandResult failure -OutputDirectory .\after
python -B doctor.py --retest-snapshots .\working-snapshot\snapshot.json .\before\snapshot.json .\after\snapshot.json
```

## dev2 已实现

- 独立快照 schema：`report_type=environment_snapshot`、`schema_version=snapshot-1.0`；与诊断 schema 标识分离。闭合字段白名单，沿用 2 MiB、16 层、20,000 节点、重复键、数字令牌和文件/祖先重解析点边界；日期、结果来源及空值关系另作语义校验。
- `--snapshot-schema`、`--validate-snapshot FILE`、`--capture --command codex|claude`、`--compare-snapshots A B`、`--compare-key init|status|rotate|delete`，与旧模式互斥。采集及校验只提供 JSON；比较默认 MD，也可显式 JSON。不接受旧诊断退出策略或 CSV/SARIF/JUnit。
- 密钥由显式 init 建立，Windows 当前用户 DPAPI 保护，创建时即使用仅当前用户的受保护 DACL；访问时核验 owner、DACL 和逐级路径。status/采集/比较均不隐式创建目录或密钥。轮换以受保护临时文件原子替换；删除不擦除历史产物。原始密钥、SID 及异常细节不输出。
- 默认采集仅观察 PATH/PATHEXT/COMSPEC、HKCU/HKLM 对应环境项、候选文件及已识别启动器；不执行 CLI、Node、别名、函数或 WSL，不新增配置读取。路径、安装组、启动器内容及域使用不同 HMAC 用途；路径算法 `lexical-windows-v1` 不展开变量、不跟随链接、不折叠大小写。限额或不支持项保留 unknown/limited。
- 原会话 PowerShell 入口 `scripts/Capture-WADSnapshot.ps1`：在调用它的 runspace 查询固定目标命令元数据，通过有限 stdin 管道传给 Python，不导出函数体或别名展开。单独 Python 采集的原会话解析始终 unknown；输入标记为 `original_runspace_user_supplied`，不提供真实性认证。
- dev2 后续 BOM 修复分支仅在原会话 stdin 读取边界接受一个前导 UTF-8 BOM，兼容 Windows PowerShell 管道编码。CLI 的 64 KiB 原始输入上限包含 BOM；通用解码器的 2 MiB 上限和旧报告编码策略保持不变，重复 BOM、非法 UTF-8、重复键及字段白名单仍按原规则拒绝。
- 记录 `--session-role`、`--symptom`、`--command-result`。结果缺省 unverified；显式 success/failure 只生成 user_report，执行时间未知，不由解析或版本查询推导结果。比较显示来源、时间和会话关联，保留冲突。
- 同域且当前密钥可访问才比较代号。域不同、旧域失活、缺钥、算法不符均输出明确不可比、`differences=null`、退出 0；非法输入仍退出 2。unknown/受限项进入证据缺口。解释基础包含 PATH/优先命中差异、安装组优先级、别名/函数与外部程序差异，仅给 possible；直接观测事实才标 confirmed。两侧原会话结果均成功时只列差异；一致但仍报告故障时不凑原因。

## 复跑

兼容复跑需要完整 Python 3.11+，包括 venv 和 ensurepip。各证据目录必须全新，独立保存原始记录。

```powershell
python -B tests/v10_release_compat.py --wheel <已核验的windows_ai_doctor-0.7.0-py3-none-any.whl> --evidence <全新兼容证据目录>
python -B tests/v10_snapshot_gate.py --evidence <全新快照证据目录>
python -B tests/v10_interrupt.py --evidence <全新中断证据目录>
python -B tests/run_tests.py --evidence <独立套件结果.json>
```

旧 wheel 固定 SHA-256：`6a030e06696febe5747ecdc22223ec761db896e04ce4269f444089ad4013d0b6`。须使用从公开 Release 取得且已经核验来源、附件 digest 和 SHA256SUMS.txt 的文件，不能以本地源码充当发布包。兼容脚本在干净 venv 安装它，以实际 all/csv/sarif/junit 和 baseline SARIF/JUnit 输出验证旧 JSON 读取；固定观察经过两版真实 CLI 比较全部旧字段，只豁免精确的工具版本和允许变化的时间。CSV/JUnit 逐字节核对，MD/HTML/SARIF 另作结构检查。

`v10_snapshot_gate.py` 把 LOCALAPPDATA/HOME/临时目录等重定向到自己的证据子目录，使用专用密钥并在完成时删除它。它保留命令、原始产物和断言，覆盖 XC-C5 交叉拒绝、XC-C6 只读无隐式写入、DPAPI/ACL 失败关闭、轮换/删除、原 runspace 函数未执行、真实 junction 零后代访问及合成解释反例。缺少真实文件 symlink 权限、第二用户取证或完整真实场景时明确输出 BLOCKED、退出 1，不将部分通过称为整组放行。

`v10_interrupt.py` 使用独立隐藏控制台，向正在等待有限采集 stdin 的真实 CLI 进程发送 Windows CTRL_C_EVENT，记录目标自身退出码 130；只插入 stdin 就绪通知，不替换产品函数或注入 KeyboardInterrupt。它不覆盖版本探测子进程的中断清理。

原会话采集示例（须先显式初始化自己的比较密钥）：

```powershell
python -B doctor.py --compare-key init
& .\scripts\Capture-WADSnapshot.ps1 -Command codex -SessionRole working -Symptom none -CommandResult success -OutputDirectory .\working-snapshot
python -B doctor.py --validate-snapshot .\working-snapshot\snapshot.json
```

success 在这里仅为用户自述。辅助脚本不运行 codex；参数不会升级成 controlled_test。开发和验收必须使用各自专用 LOCALAPPDATA，不能借示例操作真实用户比较状态。

将 wheel 或 sdist 安装到 Windows 虚拟环境后，辅助脚本也会安装到该环境的 `Scripts` 目录。初始化使用该环境的入口，采集仍在要检查的 PowerShell 会话中运行：

```powershell
& .\.wad-env\Scripts\windows-ai-doctor.exe --compare-key init
& .\.wad-env\Scripts\Capture-WADSnapshot.ps1 -Command codex -SessionRole working -Symptom none -OutputDirectory .\working-snapshot
```

## 验收记录与适用范围

- `c9d6113` 的 High IL 完整套件 209 项和快照权限检查 220 项均通过。双用户 ACL/DPAPI 在密钥实现相同的 `06f9e10` 上独立实测。复跑时，真实链接建链报 WinError 1314 计为门禁失败。
- 域匹配只表示同一比较域。三类 PowerShell 场景与复测需保留实跑与原始快照。测试启动器用于受控验收，用户安装和业务命令的结果取决于本次实际取证。
- 原会话采集已在 Windows PowerShell 验收，wheel 与 sdist 均包含辅助脚本。其他 shell 的原会话采集未验收。
- 根 `SHA256SUMS.txt` 校验源码文件。Release 附件中的同名清单校验独立下载的安装包和源码 ZIP。`HANDOFF.md` 记录 v0.7 的历史交接。

XC-C1–C4 是兼容脚本的清单名称，XC-C5 是交叉拒绝，XC-C6 是无隐式状态；dsh 验收表的 C5/C6/C7 分别对应格式冻结、独立快照和无隐式状态，编号不能混用。
