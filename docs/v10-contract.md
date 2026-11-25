# v1.0 跨终端故障定位契约

本文规定 v1.0.0 的快照、比较和复测边界。运行示例和复跑入口见 [实现与复跑](v10-development.md)。

主题：正常、故障会话各采集一次，解释 codex / claude 的命中差异，提供只读验证步骤，并允许后续采集推翻先前判断。

范围仅含进程 PATH 与持久化 PATH 不一致、重复安装抢占、PowerShell 别名/函数遮蔽。无自动修复、GUI、模型调用、自动上传或跨机器诊断。本文不修改已发布 tag、附件或历史契约。

## 1. v0.7 兼容契约

发布基线为 v0.7.0，commit `899e1c3`。开发树从 main `e292130` 建立；兼容基线另从公开 Release 下载 wheel，核对附件 digest 及 SHA256SUMS.txt 后在干净 venv 安装，不以本地源码替代已发布包。可运行入口及边界见 [开发状态](v10-development.md)。

| 接口 | v1.0 必须保留的含义 |
| --- | --- |
| 诊断 JSON | `schema_version="1.0"`；`findings[].id/status` 及既有 evidence 含义不变；仍接受未写 `report_type` 的旧诊断 JSON，若写则必须为 `diagnosis` |
| 诊断 schema | 既有 `$id` 不变；允许忽略未知附加字段；不收紧 v0.7 读取面；schema 只保证结构，`--validate` 仍是最终接受权威 |
| 诊断五态 | `pass / warn / error / unknown / skipped`，未知、受限、未检查均不证明故障或修复 |
| 输入边界 | 2 MiB、16 层、20,000 节点、64 findings；拒绝重复键/ID、非有限数及受限数字令牌；逐级拒绝输入文件及祖先重解析点，不读取其后代 |
| 版本投影 | 只比较 `.version` / `.dependency` 的完整数字三段版本；其他版本值仍接受但不投影，不改成拒绝 |
| PATH 投影 | 只在 `.path` 上约束 `installation_groups` 为整数令牌 0–32、`scan_limited` 为布尔；缺失与 0 / false 不混淆 |
| `--baseline` | 在启动任何诊断探测之前读取校验；只投影旧白名单，不重写本次诊断状态 |
| `--compare` / `--history` | 仍仅接收诊断 JSON；history 仍为 2–20 份、按传入顺序；不读报告内路径，不读本机比较密钥，不启动诊断 |
| `--validate` | 只校验诊断输入；拒绝新快照及快照比较产物；校验成功不证明健康、来源身份或隐私无泄漏 |
| `--support` | 继续只接收诊断 JSON、只输出既有白名单摘要；不接收快照，不递归打包工作目录 |
| 退出码 | 完成且未触发诊断策略为 0；触发策略为 1；参数、输入、读取或导出失败为 2；中断为 130；既有离线模式成功为 0 |
| `--fail-on` | 默认 `error`；归一化顺序 `error,warn,unknown,new,regression`；`new` / `regression` 必须有 `--baseline` |

`regression` 仍只指 changed 且发生 pass→warn、pass→error、warn→error，双侧扫描均非受限；added、removed、unknown/skipped 转移不算回归。

`new_findings` 仍只指 added 且本次为 error/warn，排除 `.path` 且 `scan_limited=true`。原始 `summary.added` 不改成这个数量。派生模式继续忽略输入的 `exit_policy`，不得信任其策略判定。

既有 19 个 check ID 按 ASCII 顺序保留；v1.0 不把新快照结论混入这些 ID：

```text
claude.config.local
claude.config.project
claude.config.user
claude.dependency
claude.install
claude.path
claude.version
codex.config.project
codex.config.user
codex.dependency
codex.install
codex.path
codex.version
scope.unchecked
system.platform
wsl.internal
wsl.inventory
wsl.launcher
wsl.running
```

1.x 保留这些 ID、字段含义、退出码和必选格式结构；仅增加可选字段或显式可选入口，不将新字段改成旧报告的必填项。v1.0 不弃用旧格式。

### 输出格式

| 格式 | 冻结要求 |
| --- | --- |
| MD / HTML | 保留原段落及基线位置、既有固定元素 ID；`both=MD+JSON`、`all=MD+JSON+HTML`；stdout 的 both/all 仍只打印 MD；HTML 文本转义、无脚本及动态 URL |
| 诊断 CSV | UTF-8 BOM、LF，固定 10 列：`sequence,check_id,target,status,version,installation_groups,scan_limited,baseline_change,baseline_status,baseline_regression`；无基线时基线三列空；有基线按两侧 ID 并集，removed 行本次 status 空；ASCII 排序；中英正文相同 |
| compare / history CSV | 沿用各自既有表头和字段语义，不套用诊断 CSV 的 10 列；不复制自由文本或公式前缀输入 |
| SARIF | 2.1.0 无位置子集；results 仍仅 error/warn/unknown；无 locations/artifacts；`windowsAIDoctorCheckId/v1=check_id` 不作新路径指纹；baselineState 仅 new/updated/unchanged，无 absent；不宣称可直接用于 code scanning |
| JUnit | 每个 testcase 保留非空 properties；属性依次 status、可选 scan_limited、带基线时 baseline_change/baseline_new/baseline_regression；未命中策略只含 properties；skipped 为 properties 加 skipped；failure 只表达退出策略，不输出版本、路径、摘要或原始 evidence |
| 全部导出 | 保留输出排他创建、碰撞失败及仅清理本次新文件；CSV/SARIF/JUnit 导出成功时不混入保存提示 |

版本元数据允许随程序版本更新；时间戳只在原本允许它的格式中变化。语义回归比较以同一份输入和白名单投影为准，不拿两次实时扫描的环境漂移充当兼容性证据。

## 2. 新入口与产物分离（拟定）

以下是实现目标，当前 v0.7 不支持这些命令：

| 新入口 | 行为 |
| --- | --- |
| `--compare-key init/status/rotate/delete` | 显式管理本机比较状态；init 已存在则不覆盖；status 只读；rotate/delete 是用户主动调用，不由诊断或采集自动执行 |
| `--capture` | 在调用它的现场采集；须已有可访问的本机比较密钥，否则退出 2，不隐式初始化 |
| `--compare-snapshots A.json B.json` | 只读两个显式快照与当前本机比较状态；不执行工具、不访问快照内路径 |
| `--retest-snapshots WORKING.json BEFORE.json AFTER.json` | 只读三个快照与当前比较状态。T3 采集时间须严格晚于 T1、T2。输出为独立的 `snapshot_retest` / `snapshot-retest-1.0`，默认 MD，可选 JSON |
| `--validate-snapshot SNAPSHOT.json` | 独立有界校验快照；不声称验证其来源、采集真实性或现状 |
| `--snapshot-schema` | 导出独立快照结构 schema；不读环境或本机密钥 |

这些模式与既有主模式互斥。新采集使用 `--command codex|claude`、`--session-role working|failing|unspecified`、`--symptom none|not_found|wrong_version|config_error|other|unspecified`。非法值退出 2，固定错误提示不回显传入值。

解释故障须有目标一致的 working / failing 两侧，且故障侧症状明确；缺项时只能输出普通差异和证据缺口。working 侧允许 `none`。症状值是用户陈述，不是实测结果。v1.0 不提供症状自由文本入口；未来若增加，默认不进入快照、日志或支持包。

新采集可用 `--command-result success|failure|unverified` 记录用户对原命令运行结果的陈述，默认 `unverified`；该参数不执行命令。`success` / `failure` 的来源固定为 `user_report`，不能由参数选择或升级成 `controlled_test`。未提供结果或显式选 `unverified` 时，来源为 `none`。非法值沿用退出 2 和不回显输入的规则；结果记录详见第 3.1 节。

新快照首先提供 JSON；对比提供 MD / JSON，默认 MD。它们不复用诊断 CSV、SARIF 或 JUnit，不改变旧入口的格式集合和退出策略。

快照必含 `report_type="environment_snapshot"`、`schema_version="snapshot-1.0"`；快照对比必含 `report_type="snapshot_comparison"`、`schema_version="snapshot-comparison-1.0"`。快照 schema 标识拟为 `schemas/environment-snapshot-1.0.schema.json`，与 diagnosis-1.0 的标识及版本值均不同；本地校验不访问此标识 URL。

## 3. 快照字段与采集边界（拟定）

| 字段 | 内容及限制 |
| --- | --- |
| `captured_at` | UTC 采集时间；所有结论标明 A/B 的 T1/T2，不声称当前仍相同 |
| `command` / `session_role` / `symptom` | 上述固定枚举；不接收任意命令、参数或原始错误文本 |
| `scope` | 只含不透明比较域代号和当前密钥状态；不含密钥、用户名、SID、机器名或原始绑定材料 |
| `context` | shell 为 powershell/cmd/git_bash/unknown；提权用 `elevated` 布尔，若无法观测则单独 observation 状态为 unknown，不把 false 当未知 |
| `environment` | 仅 PATH、PATHEXT、COMSPEC 的安全投影；PATH 为保持顺序的路径代号，PATHEXT 为受限扩展名枚举，COMSPEC 只留路径代号及读取状态；不输出原值，也不输出其他环境变量名 |
| `persistent_environment` | HKCU/HKLM 对应环境层的相同白名单投影及读取状态；无法读取为 unknown，不当作缺失；不能仅按两层字符串拼接就声称等于新进程的有效 PATH |
| `resolution` | 原会话优先命中类型、路径候选顺序、已识别启动器及 Node 的路径代号、访问状态；别名/函数仅输出类型及固定目标命令，不输出函数体、脚本块、别名原始展开或任意文字 |
| `launcher` | 启动器内容代号、完整读取状态、可选安全数字版本及来源；内容代号不代表版本，路径代号不代表同一个文件 |
| `observations` | 直接观察的状态和值；与 symptom 分开；unknown、受限及缺项保留原因枚举 |
| `command_result` | 必填的原命令结果记录；结果、来源、执行时间及原会话关联分开存储，缺省明确为未验证；不得由解析成功、找到文件或版本查询推导，详见第 3.1 节 |

读入上限沿用 2 MiB、16 层、20,000 节点；路径/候选列表各最多 256 项。达到上限必须标记受限，不能据截断列表确认未安装、无候选或候选优先级。字符串、令牌、重复键及重解析点防护沿用诊断读取器；快照新增字段另建白名单，不直接复用任意 evidence。

PowerShell 通过用户在原 runspace 中执行辅助脚本采集解析元数据；另开 `powershell -NoProfile` 或 Python 子进程不能代表调用者别名/函数。单独调用 Python 采集而没有原会话证据时，shell 解析状态为 unknown。辅助脚本不得调用命中的别名/函数、加载用户 profile 或导出函数体。

采集默认不执行 CLI/Node，只观察解析和文件；若用户显式要求版本观察，仍须沿用 v0.7 已识别入口、环境白名单、临时 HOME、限时限量和进程树约束。安全版本探测不是原会话原命令复现，不能据此证明用户业务命令可运行。

PowerShell 辅助脚本的 `-ProbeVersion` 可对原会话匹配到的一个已识别启动器请求版本查询。快照仅记录完整三段数字及 `bounded_version_probe` 来源。路径超出已检查候选时跳过查询，别名及函数也跳过。版本比较单列数字结果，启动器内容观察保持自己的含义。

只读验证可使用固定命令元数据查询；不执行未知包装器、不启动 WSL、不改 PATH/配置/注册表。用户显式选择的快照输出与比较密钥管理是允许的文件写入，应与普通诊断的“无隐式持久状态”说明分开。

### 3.1 原命令运行结果与证据来源（拟定）

`command_result` 始终指当前快照 `command` 对应的用户原命令及本次采集阶段；不得用另一条参数、用途或会话不同的命令替代。结果记录不包含原始参数、退出输出或错误文本，也不据结果推断具体失败原因。

| 字段 | 取值及含义 |
| --- | --- |
| `status` | `success / failure / unverified`，显示“成功／失败／未验证”；未验证不等于成功或失败 |
| `source` | `user_report / controlled_test / none`，分别为用户自述、受控测试、无结果证据；来源标签不提供身份认证 |
| `recorded_at` | UTC，本次采集记录该结果的时间；不能充当原命令执行时间 |
| `executed_at` | UTC 或 null；实际执行时间未知则为 null，不用采集时间补齐 |
| `session_match` | `original / other / unknown`，说明结果是否属于原会话；用户自述的关联仍按自述展示，不能升级成实测 |

默认记录如下；这里只是契约示例，不是本机实测：

```json
{
  "status": "unverified",
  "source": "none",
  "recorded_at": "2026-11-24T13:30:00Z",
  "executed_at": null,
  "session_match": "unknown"
}
```

`source=none` 必须对应 `status=unverified`、`executed_at=null`、`session_match=unknown`；`success` / `failure` 必须有非 none 来源。`user_report` 只接受用户明确提供的成功或失败，不从 `session_role` 或 `symptom` 自动填写；通过上述参数录入时，`executed_at=null`，`session_match=original` 表示用户自述属于原会话。

`controlled_test` 仅用于独立验收流程中，对已登记的原命令场景进行受控执行后产生的结果；须记录非空执行时间，并在仓库外取证材料中关联测试用例、会话和当次执行记录。普通采集及原 runspace 辅助脚本不得为填此字段执行原命令、别名或函数；安全版本探测也不得生成此类结果。`other / unknown` 会话的结果保留展示，但不证明原会话可运行；受控执行未取得结果时保留 `unverified`，不按超时或取证失败猜测原命令结果。

结果和症状或会话标签冲突时，保留双方记录并显示证据冲突；不得静默改写结果。跨次复测必须新建本次结果记录，不能沿用上次成功或失败。报告显示来源、执行时间（未知则明示）及会话关联；仅有用户自述时必须写“用户报告成功／失败”，不得称为实测或将解释升级成 `confirmed`。支持包继续只导出旧诊断白名单，不新增这组记录。

## 4. 比较密钥、代号与可比性（拟定）

密钥拟存 `%LOCALAPPDATA%\WindowsAIDoctor\comparison\key.dat`，由显式 init 创建随机 256 位材料；按 Windows 当前用户保护，并对目录和文件设置限制当前用户访问的 ACL。保护或权限核验失败则初始化失败，不降级为公共可读文件。管理操作逐级拒绝链接/重解析点；轮换原子替换，失败保留旧状态。该位置、保护方式和权限仍须 Windows 实测后定稿。

路径、启动器内容、比较域分别用独立用途标签的 HMAC-SHA-256 派生；保留完整摘要，不输出裸路径/内容哈希，不把密钥或中间值写入产物。输入路径只进行不访问文件系统的词法规范化，保守处理大小写与大小写敏感目录；无法证明等价时不合并，不调用 resolve 跟随链接。具体规范化算法属于快照版本语义，变更须更换算法标识并判旧新不可比。

内容代号仅针对通过既有安全边界识别、完整有界读取的启动器；超限、读取失败或读取期间变化则为 unknown，不以部分内容生成身份代号。配置文件绝不生成内容指纹，也不新增配置读取。配置观察若复用旧诊断，只能保留原允许的路径代号与解析结果。

| 条件 | 对比结果 |
| --- | --- |
| 两份快照比较域相同，且与当前可访问密钥域、规范化算法一致 | 允许比较对应代号；仅说明同一比较域，不提供身份认证或来源真实性保证 |
| 两份比较域不同 | `comparability=incomparable`，原因 `scope_mismatch`；只说明比较域不一致，不猜换机器、换用户或轮换 |
| 两份域相同但与当前密钥不一致 | `incomparable`，原因 `inactive_scope`；旧产物不被改写 |
| 当前密钥不存在或无法访问 | `incomparable`，原因 `key_unavailable`；不自动创建或恢复密钥 |
| 快照算法不兼容 | `incomparable`，原因 `algorithm_mismatch` |

不可比是有效产物的明确业务结果：成功导出结果退出 0，`differences` 为 null，不输出“无差异”或零差异计数，也不进入故障解释；非法输入、交叉产物或导出失败仍退出 2。新快照模式不使用 `--fail-on`。

同用户关系是两份输入之间的关系，不在单份快照里填“与另一份相同”。对比只输出 `same_scope / incomparable / unknown` 这样的证据范围，不输出账户标识。比较域匹配依赖密钥按本机当前用户隔离且不导出；代号本身不能证明机器/用户身份，故意复制密钥或伪造输入不在真实性保证内。

rotate 使新旧域不可比；delete 后当前本地对比不能使用旧域，普通诊断及旧诊断 JSON 的 compare/history 不受影响。删除只移除比较状态，不擦除历史快照，也不撤销已经分享的代号之间的关联。两份旧快照即使相互同域，本地也必须满足当前密钥可用规则。

支持包必须显式排除密钥、原始快照、比较域/路径/内容代号和症状自由文本；只导出旧诊断白名单。密钥、DPAPI 原文、原始路径及异常详情都不得出现在 stdout/stderr、日志或错误中。不承诺脱敏代号无法关联。

## 5. 解释与反例规则

报告分开呈现用户自述、直接观察、解释级别、缺失证据与验证步骤。三级解释为 `confirmed`、`possible`、`missing_evidence`（显示“missing evidence / 缺少证据”）。`confirmed` 只限定到已观察事实；不能把它扩写为根因已证实。

| 场景 | 允许确认的事实 | 归因边界 |
| --- | --- | --- |
| 进程 PATH 未刷新 | 采集时进程 PATH 与可读持久化层存在差异，候选命中不同 | 仅凭差异不能确认刷新历史、父进程来源或重启可解；解释故障须结合故障侧解析证据；无历史证据时“未刷新”只为 possible |
| 重复安装抢占 | 可访问候选存在多个且两会话优先命中不同启动器 | 多个安装不等于故障；版本不对须有独立安全版本观察，不以内容代号变化冒充版本变化 |
| 别名/函数遮蔽 | 原 runspace 的优先命中是别名/函数，另一侧为外部程序 | 别名可能正确转发，不能仅凭类型断言找不到；未观察展开或执行效果则对应症状解释为 possible / missing_evidence，不调用函数验证 |

两项硬反例：

1. 两份有效、可比快照的已观测项一致，用户仍报告故障：输出“未发现可解释差异”，列原会话执行结果等缺口，不凑原因。若关键项 unknown，应同时显示该限制，不称完整环境一致。
2. PATH 不同但两侧 `command_result.status=success` 且 `session_match=original`：只记录差异，不声称解释故障，不建议重启或修复。两侧均为受控测试时可写“受控测试中两边都能跑”；含用户自述时按实际来源写“用户报告成功”，不得冒充实测。任一侧为未验证或会话关联不成立时，只列证据缺口，不能断言两边都能跑；安全版本查询不能替代原命令结果。

unknown 与扫描受限记录到证据缺口，不计作可解释差异；两侧提权状态不同则显式列为上下文条件，不直接认定为原因。配置报错及 other 超出三类解释能力时，只展示相关观察和缺口。

任何建议只给操作条件、只读验证命令、预期可观察变化；不自动执行修复，不承诺“重启即可”“已修复”或“根因是”。结论注明截至 T1/T2，复测保留此前 possible 的证据并允许新结果推翻；差异消失与故障消失分别记录。

复测差异消失而新的原会话结果仍为 `failure` 时，明确显示“相关差异已消失，原命令仍失败”，并注明是用户自述还是受控测试；此前仅凭该差异提出的解释不能继续作为充分解释。结果为 `unverified` 或会话关联为 `other / unknown` 时，显示“相关差异已消失，原命令结果未验证”；不得从差异消失推导故障消失。即使结果为 `success`，也只陈述该次执行成功，不据此确认原差异是根因或当前仍可运行。

复测逐条保留旧解释和依赖的观察项。关键观察缺失、受限或只消除部分相关差异时，关系显示为证据不足。工作侧优先启动器的目录可选记录为路径代号。报告按进程、用户持久层、系统持久层分别显示这个目录是否出现。如果 T2 的进程 PATH 缺少该目录、T3 出现，且同一持久层在两次都可读并含该目录，复测记录这次变化。Windows 的刷新动作及父进程历史需要单独证据。

## 6. 兼容与验收取证

本节是完整验收清单。dev2 提供旧报告兼容、快照交叉拒绝、密钥无隐式写入及真实 Ctrl+C 退出 130 的独立复跑入口；完整 v1.0 功能验收仍未完成，单项结果不能替代整组 Gate 放行。

1. 从 v0.7.0 Release 取得 wheel，核对公开附件摘要；在独立干净 venv 安装，记录下载来源、字节数、SHA-256 和 Python 版本，不用当前源码冒充已发布包。
2. 由该 wheel 生成 `--format all`、csv、sarif、junit，补带 baseline 的 SARIF/JUnit。MD/HTML/CSV/SARIF/JUnit 是输出语义比较样本，不新增这些格式的输入解析器。
3. 用 v1.0 对步骤 2 的诊断 JSON 执行 `--validate`、`--baseline`、`--compare`、`--history`；保留旧版未写 report_type 的合法样本及现有宽松接受面反例。
4. 在同一受控输入上比较两版 check ID→status、summary、白名单投影、new/regression 结果及退出策略。忽略项仅限版本元数据和允许出现的生成时间；任意其他旧字段差异都须解释，不能统一删除后宣称等值。
5. 执行新旧产物交叉拒绝、新 schema 有界读取、真实文件/祖先 symlink 与 junction 零目标访问、三类正向场景、两条反例、未知/受限、提权差异、轮换/删除及支持包排除测试。
6. 权限不足导致必需真实链接或用户隔离测试不能完成时，单独记录阻断；不同权限运行分别计数，不拼接为完整 PASS。
7. 原命令结果取证覆盖：默认未验证、用户自述成功/失败、受控测试成功/失败、执行时间未知、其他/未知会话关联、结果与症状冲突、版本查询成功但原命令未验证。分别验证来源展示及非法字段组合拒绝；为 PATH 反例和复测仍失败保留独立受控执行记录，不以用户参数冒充实测。

与 dsh 验收表对照：

| Gate | 本文约束位置 | 待提交证据 |
| --- | --- | --- |
| C1–C7 | 第 1、2、6 节 | Release wheel、干净环境输出、键级 diff、格式比对、交叉拒绝和无隐式状态记录 |
| A1–A6 | 第 2、3、4 节 | 症状输入、原 runspace 采集、时间/提权、白名单、不可比、采集不执行原命令及结果来源记录 |
| B1–B7 | 第 3.1、5 节 | 三类正向、两条反例、三级结论、受限输入、T1/T2 样例及双侧原命令结果 |
| P1–P7 | 第 4 节 | ACL/保护核验、换用户访问拒绝、密钥生命周期、产物敏感值检索、支持包解包审计 |
| R1–R3 | 第 3.1、5 节 | 复测差异保留/消失、原判断被推翻及本次原命令成功/失败/未验证的独立证据 |

待实现并经联调确认后，才能将本草案改成冻结契约。尤其不得把比较域相等、单个别名命中或安全版本查询写成原故障已经复现。

## 7. 核对来源

- dsh：2026-11-24《v1.0 验收表》，按本群契约补充解释 A2 的跨输入比较域关系。
- 本地 v0.7：`docs/v05-contract.md`、`docs/v06-contract.md`、`docs/v07-contract.md`、`docs/privacy.md`。
- 本地实现：`windows_ai_doctor/cli.py`、`compare.py`、`baseline.py`、`catalog.py`、`diagnosis_schema.py`、`core.py`、`privacy.py`。
- 群内截至 2026-11-24 的 v1.0 决定与 MausBot 补充：输出语义核对、症状自由文本排除、密钥域不匹配只说明可证实原因、原命令运行结果与证据来源分开记录。
