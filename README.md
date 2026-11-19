# Windows AI Doctor

[English](README.en.md) · v0.1.0 · Python 3.11+ · Windows 优先 · 运行时仅标准库

检查 Codex CLI 和 Claude Code CLI 的 PATH 入口、重复安装线索、版本、按入口区分的运行时依赖、配置语法和 Windows/WSL 可见状态。导出中文或英文 Markdown / JSON 报告，路径使用不含原值的代号。

这是功能范围有限的 v0.1 首版。默认只诊断，不安装、升级、修复、登录或调用模型 API。

## 直接运行

无需 pip 安装、管理员权限或模型密钥。从解压目录运行：

```powershell
python .\doctor.py --lang zh --output-dir .\reports\first
```

生成 `report.zh.md` 和 `report.zh.json`。已有报告不会覆盖；再次运行请选择新目录。不指定输出目录时打印报告：默认/`both` 打印 Markdown，`--format json` 只打印 JSON，适合管道。

从任意干净目录启动（将脚本路径换为你的实际位置）：

```powershell
python "D:\Projects\windows-ai-doctor\doctor.py" --lang zh --output-dir ".\doctor-reports"
```

若 `python` 不在 PATH，请用自己已安装的 Python 3.11+ 的绝对路径替换命令中的 `python`。上述项目路径为示例，请替换为自己的解压位置。

## 常用命令

```powershell
python .\doctor.py --help
python .\doctor.py --tools codex --lang en --format json
python .\doctor.py --no-version --lang zh --output-dir .\reports\files-only
python .\doctor.py --project "D:\项目 空格" --output-dir .\reports\project
python .\doctor.py --timeout 2 --wsl-list --output-dir .\reports\wsl-list
```

- `--tools codex claude`：默认两种工具；可只选一种。
- `--lang zh|en`、`--format both|md|json`：语言和格式。
- `--home`：指定诊断目标用户目录，默认当前 Python 用户主目录。`CODEX_HOME` / `CLAUDE_CONFIG_DIR` 环境变量分别优先于默认 `.codex` / `.claude`。请使用绝对本地路径；相对、远程或链接配置记为无法判断，不悄悄回退。
- `--project`：额外检查**明确指定的项目根目录**中的 `.codex/config.toml`、`.claude/settings.json`、`.claude/settings.local.json`；不向上遍历项目或计算最终合并值。
- `--timeout`：每次版本/列表查询 0.1–30 秒，默认 3 秒，最多两次版本查询/工具（工具自身及必要的 Node）。捕获输出最多 16 KiB + 1 字节溢出检测。超时或输出过长后继续生成其他检查。
- `--no-version`：不执行 Codex、Claude、Node；只检查本地文件、PATH 和 WSL 注册信息。默认不会执行 WSL。
- `--wsl-list`：显式允许运行系统 `wsl.exe --list --running --quiet`，只报告数量；不启动发行版、不读取发行版内部文件。与 `--no-version` 同时使用仍会执行此显式列表查询；严格无外部命令时不要加它。

默认版本检查只运行识别出的原生程序，或直接运行已识别 npm 包入口，绝不把 `.cmd` / `.ps1` 拼入 shell。未知包装器、别名或不可识别布局保持未知。检查前应信任你 PATH 中的安装文件；识别布局**不等于验证发布者签名**。

npm 只接受已核对的 `cmd-shim 8.0.0` 完整标准包装形式（Node 无附加参数或直接原生目标）；注释里出现包路径、残缺或加入自定义命令均不会触发目标查询。其他 shim 版本可能保持未知。采用的模板及许可见 [第三方声明](THIRD_PARTY_NOTICES.md)。

## 如何理解报告

| 状态 | 意义 |
| --- | --- |
| `pass` / 通过 | 此有限检查已通过，或存在该可见信息 |
| `warn` / 提醒 | PATH 未发现入口、存在多个安装候选或检查受到限制 |
| `error` / 异常 | 支持的配置语法/根结构有误，或已识别 JS 入口缺失/不满足所需 Node |
| `unknown` / 无法判断 | 未识别安装、版本失败、权限/编码限制或证据不足 |
| `skipped` / 未检查 | 可选文件不存在、检查未启用或超出范围 |

退出码：`0` 已完成且无 `error`（仍可能有提醒/未知）；`1` 已完成且有 `error`；`2` 参数、诊断或导出未完成；`130` 手动中断。版本超时属于无法判断，因此通常仍退出 `0`。请结合 JSON `summary` 和稳定检查 `id` 判断覆盖范围。

`<PATH:1>` 等代号仅用于同一份报告内关联入口；没有保存可逆映射，也不能直接复制成路径。`command_name` 和列表顺序帮助在本机对应。查看真实路径请在原终端手动运行 `Get-Command codex,claude -All`、`where.exe codex`、`where.exe claude`。报告只预测 PATH/PATHEXT 下的 CMD 和 PowerShell 候选；不代表当前交互终端的别名、函数、执行策略或 CWD 搜索结果。

多入口并不等于冲突；识别为同一 npm 安装的包装器合并计数。PATH 未发现也不等于整机未安装。配置语法通过不代表登录成功、API 可用、模型或权限配置有效。WSL 启动器存在不代表 WSL 组件健康或已安装发行版；内部环境始终标为未检查。

`path_access=blocked`、`existence_verified=false` 表示在检查路径祖先时受限，尚未确认其中的命令文件存在。为避免跳过潜在优先入口，报告保留该候选的 PATH 顺序，安装与版本保持未知且不执行。Node 路径受限也记为未知，只有已确认缺失才报缺依赖。

## 隐私与离线

不读取认证文件、`.claude.json`、会话、历史、聊天正文，不输出配置键值、任意异常文本、原始命令输出或私有路径。配置仅限固定文件名，UTF-8、JSON 对象/TOML，最多 1 MiB，拒绝链接/重解析路径。Windows 只扫描固定本地盘；UNC、映射网络盘和移动盘不参与检查。

配置、命令、包元数据/目标和 Node 都先从盘符到叶子逐级检查，遇到 junction、符号链接或其他重解析点立即停止，不查询其后代的存在性、元数据或内容。包含 `..` 或 Windows 备用数据流的路径也保守拒绝；不宣称防御硬链接或并发恶意替换。

版本命令使用临时 HOME/配置/缓存目录、密钥环境变量白名单隔离、关闭 Claude 自动更新/遥测的变量和不可用本地代理。Windows 用 Job Object 限制进程树，包含失败则不启动查询。检查器自身不创建网络连接；第三方程序仍是用户本机程序，并非完整安全沙箱，也不能保证它不绕过代理。需要只读离线基础检查时用 `--no-version`。详情见 [隐私边界](docs/privacy.md)。

## 可复现样例与测试

```powershell
python .\examples\make_demo.py .\reports\demo-new
python .\tests\run_tests.py --evidence .\evidence\tests-rerun.json
python .\tests\offline_check.py --format json
```

演示只在临时目录创建合成配置、损坏的 npm 包装器和 Windows junction，包含一个故意损坏的配置，因此两种语言的子命令退出 `1` 是预期结果；示例生成器成功退出 `0`。临时目录自动清理。修订报告见 [中文](examples/review-fixes/zh/report.zh.md)、[English](examples/review-fixes/en/report.en.md)。

测试运行器只需标准库。真实 npm JS 入口测试借用已存在的 Node；Windows 原生样例借用系统已有的 .NET Framework C# 编译器，不会安装它们。缺少可选条件时如实 `SKIP`。具体实跑数量、退出码及覆盖边界见 [验收记录](docs/validation.md) 和 [机器证据](evidence/tests.json)。`offline_check.py` 在真实 CLI 进程内禁止 Python 网络操作，不等同于禁用主机网卡。

## 规则与限制

[官方规则依据](docs/rules.md) · [隐私说明](docs/privacy.md) · [验收与未覆盖范围](docs/validation.md) · [发布审查](docs/release-review.md)

首版不检查完整配置 schema、配置档/祖先层/管理策略、账户/服务可用性、CLI 功能任务、IDE/桌面版本、WSL 内部环境、所有包管理器 shim 或发布者签名。只识别明确布局，不针对历史 Issue 推断普遍故障。实际产品版本变化可能需要更新规则。

采用 [MIT 许可证](LICENSE)，npm 包装模板的 ISC 许可见 [第三方声明](THIRD_PARTY_NOTICES.md)。可选 Python 打包元数据已提供；源码直接运行已验收，wheel/pip 安装路径尚未验收。

发布审查：常规全套 38 通过、1 跳过；该跳过项已由 dsh 在用户授权后单独补测通过，39 个不同测试项均有通过记录，并非一次全套 39 通过。终审另复跑常规全套得到 38 通过、1 跳过。详见 [发布审查与证据](docs/release-review.md)。
