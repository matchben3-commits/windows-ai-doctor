## v0.3 更新 / Update

趋势和求助包共用有界白名单读取，不扫描、不执行命令、不访问报告内路径。求助包不保证诊断信号无法关联，用户须审阅后自行分享；无原始路径映射。exit_policy只由本次命令参数重建，派生模式忽略输入此字段。当前完整契约见 [v03-contract.md](v03-contract.md)。

> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# 隐私与执行边界 / Privacy and execution boundaries

## v0.2 新增边界 / New in v0.2

离线比较只读两个显式 JSON，不实例化诊断器，不执行版本/WSL/网络，也不访问输入中路径。2 MiB、16 层、20,000 节点、64 findings 限额及重复键/编号验证作用于整个输入；白名单仅保留已知 ID、状态和有限数字观察。任意 summary、recommendation、evidence 字符串、路径、URL 和自定义版本标签不复制到比较输出。输入文件同样逐级拒绝链接/重解析点，详见 [比较契约](comparison.md)。

HTML 使用转义后的文本、固定内嵌 CSS，无 JavaScript 和动态 URL/属性，设限制性 CSP。排障里的官方 URL 是固定文字，不加载资源。MD/JSON/HTML 导出先检查同名冲突，并用独占创建；失败/中断删除本次创建的文件，保留原文件；若清理失败会固定提示，不回显路径或异常。输出目录由调用者选择；不承诺输出路径没有链接或并发变动。

Comparison projects untrusted reports onto known IDs and limited numeric fields; arbitrary imported strings never enter output. HTML escapes dynamic text and contains no script or external resource dependency. Export rolls back only files newly created by this invocation; existing files are never removed. Output directory selection is caller-controlled, and concurrent replacement/hard links remain outside the model.

本轮新验证：[完整套件](../evidence/v02-tests.json)、[单独授权文件链接补测](../evidence/v02-authorized-links.json)、[显示核验](html-validation.md)、[本机检查](../evidence/v02-host/runs.json)。下文沿用的 dsh 单项链接证据属于 v0.1 历史。

## 读取什么 / What is read

- 当前进程 PATH/PATHEXT、配置目录环境变量、当前用户主目录位置。
- PATH 中固定命令名的文件是否存在、二进制头、已识别 npm 包的 `package.json` 和有限包装器/入口文件。
- 固定配置文件：用户 `config.toml` / `settings.json`；显式 `--project` 根的同名文件及 Claude `settings.local.json`。语法分析会在内存中接触配置值，但这些值不会成为报告字段。
- Windows 系统 WSL 启动器是否存在、当前用户 Lxss 注册子键的计数。

No authentication stores, `.claude.json`, chat/session history, unrelated folders or WSL internal files are opened. Syntax parsing necessarily sees configuration values in memory; those values are never copied into report fields. Fixed filenames do not constitute a forensic guarantee against concurrent hostile file replacement.

## 输出什么 / What leaves memory

报告只保留固定说明、状态、稳定编号、计数、严格完整匹配的版本号、退出码、路径代号、固定命令名及受支持的数字版本范围。路径代号全量替换原路径，不保存映射；无法通过本报告还原用户名或文件夹名。

Configuration keys/values, URLs, raw stdout/stderr, parser exception text and tracebacks are not exported. This avoids relying on a list of known secret formats: even an unknown secret in a config value or noisy version output is discarded. Paths are opaque references, not partially masked personal paths. CLI argument errors also withhold the supplied argument.

## 执行什么 / What runs

默认只对首个可识别的工具入口执行 `--version`，必要时另查 Node `--version`；不运行 `npx`、npm 安装、更新、登录或 agent 任务。直接参数列表调用，不运行 shell 包装器。版本调用的工作目录及 HOME/配置/缓存全部放临时目录，结束自动清理。

Only an OS environment allowlist is inherited, excluding API keys, credential variables, NODE_OPTIONS, PYTHONPATH and user configuration overrides. Scratch directories replace HOME and application configuration/cache locations. Updater/telemetry controls and an unavailable loopback proxy are set. This is **not** a full security or network sandbox: a third-party executable may ignore these settings or access OS services. `--no-version` skips all CLI/Node execution. Default WSL inspection executes no WSL command; adding `--wsl-list` explicitly permits the system list command even with `--no-version`.

Windows 创建查询进程时先挂起，加入关闭即终止的 Job Object 后再恢复；若不能建立此约束则查询不启动。正常退出、超时、输出超过上限均清理该进程树。POSIX 路径采用单独进程组，但本轮未在 POSIX 上实测。

## 文件边界 / File boundaries

配置只读且限制大小；配置、命令、包元数据/目标和 Node 统一从盘符逐级检查到叶子。发现符号链接、junction 或其他重解析点后，不查询其后代的元数据、存在性或内容；不先 `resolve`。受限候选保留 PATH 顺序并明确存在性未确认，不执行；Node 受限不误报为已确认缺失。Windows 仅访问固定本地盘，拒绝 `..` 和备用数据流路径。主机的 PATH、配置、注册表和安装文件均不由诊断器修改。唯一持久写入为用户选择的报告目录；已有同名报告不会覆盖。操作系统或第三方程序的缓存/服务行为不能凭此声明全部没有副作用。

Root-to-leaf checks reject a link before inspecting its descendants. This applies to configuration, executable headers, package metadata/targets and Node selection. Blocked candidates have unverified existence and are never run; an inaccessible earlier Node does not permit falling through to another runtime. This is a conservative static check, not a defense against concurrent hostile replacement or hard links. Complete known npm wrapper templates are required before a target query; arbitrary wrapper text is never interpreted.

Tests and demos write synthetic fixtures only inside temporary directories. Generated demo reports contain no real account/configuration values. Validation artifacts contain case names, outcomes and fixed descriptions rather than raw exception logs. The synthetic credentials in test source are intentionally fake and are not present in exported reports.

## 测试边界 / Validation boundary

已验证两种语言、多格式、stdout/stderr、坏配置、带用户名/密码/查询凭据 URL 的合成输入不会出现在输出；异常信息采取固定分类，不做不可靠的正则替换兜底。网络检查包括禁止 Python 网络 API 的真实 CLI 运行；未关闭主机网卡，也未对第三方二进制建立防火墙级隔离。真实 NTFS junction 回归已执行，跟踪并禁止链接之后的 `lstat/stat/is_file/open/resolve`，覆盖配置、命令、Node、包元数据及 JS/原生目标。常规进程缺少文件符号链接创建权限，该项会跳过；dsh 已在用户授权后通过单项临时管理员补测，见 [补测证据](../evidence/review-dsh/symlink-elevated.json)。这与真实 junction 回归分别记录。
## v0.7 更新 / Update

JUnit 只导出白名单 properties 与固定策略 failure/skipped 文案，不写入 summary、evidence、版本号、路径、主机名或时间戳。`--fail-on new` 仅依据基线投影出的 `new_findings`（added error/warn，排除扫描受限 path），不等于已确认故障根因。SARIF 指纹只用 check_id；`baselineState` 不含 absent；基线独有 ID 仍不进入 results。CSV 仍为 10 列，不因 new 增列。详见[第七版契约](v07-contract.md)。

JUnit exports only whitelisted properties and fixed policy failure/skipped text—never summaries, evidence, versions, paths, hostnames or timestamps. `--fail-on new` uses projected `new_findings` only (added error/warn, excluding scan-limited paths) and does not establish a root cause. SARIF fingerprints use check_id alone; `baselineState` has no absent; baseline-only IDs still omit from results. CSV stays ten columns. See the [v0.7 contract](v07-contract.md).

## v0.6 更新 / Update

`--baseline` 在诊断前经既有 `load_report` 读取；非法或链接基线拒绝且不启动探测。基线段、诊断 CSV 与 SARIF 只投影白名单观察（五态、数字版本、安装组、扫描限制及固定回归布尔），不复制基线路径、摘要、evidence 或任意输入文字。诊断 CSV 的基线列在无基线时留空；有基线时 `baseline_regression` 仅反映固定三种状态转移。SARIF 为无文件位置子集，不含 locations/artifacts/路径/时间戳，不宣称可直接用于 GitHub code scanning。基线文件及祖先目录真实链接须拒绝，目标内容读取与后代访问为 0。详见[第六版契约](v06-contract.md)。

`--baseline` is validated with the existing bounded reader before any probe. Baseline sections, diagnosis CSV and SARIF project only whitelisted observations—never baseline paths, summaries, evidence or free input text. Without a baseline, diagnosis CSV baseline columns stay empty; with one, `baseline_regression` reflects only the three fixed transitions. SARIF is a subset without file locations and does not claim direct GitHub code-scanning use. Real baseline file/ancestor links must reject with zero target-content reads and zero descendant access. See the [v0.6 contract](v06-contract.md).

## v0.5 更新 / Update

compare CSV 与 catalog/schema 均为离线导出：catalog 与 schema 不读取任何输入文件、不实例化诊断器、不访问环境/注册表/网络；compare CSV 只读两个显式诊断 JSON，沿用有界读取与链接拒绝，不新增读取面。单元格与目录条目只含固定枚举、已知 ID、白名单字段名和固定双语说明，不拼接环境值或用户输入。公式前缀自由文本即使出现在被忽略字段也不得进入 CSV。`--schema` 通过只表示形状；`--validate` 仍是接受权威。详见[第五版契约](v05-contract.md)。

compare CSV, catalog and schema are offline exports. Catalog/schema read no inputs, instantiate no Doctor and consult no environment/registry/network. compare CSV reads only the two explicit diagnosis JSON files under existing bounds and link rejection. Cells and catalog entries use fixed enums, known IDs, whitelisted field names and fixed bilingual prose only—never environment values or user text. Formula-leading free text in ignored fields still never reaches CSV. Passing `--schema` means shape only; `--validate` remains authoritative. See the [v0.5 contract](v05-contract.md).

## v0.4 更新 / Update

离线报告校验只确认已知字段与边界的可接受性，未知自由文本不作全面审核。求助包校验不解压落盘，只有结构、CRC、SHA和摘要一致性检查；清单没有自签名，不证明来源身份、机器现状、未经重新打包或隐私无泄漏。CSV只输出固定枚举与已知数字/布尔字段，不带原始文字或路径。所有入口均不自动分享。详见[第四版契约](v04-contract.md)。

Offline validation checks acceptability under known fields and bounds, not all free text. Bundle verification checks structure, CRC, SHA and summary consistency in memory; the unsigned manifest does not establish identity, machine state, absence of repackaging or privacy. CSV exports fixed IDs/enums and limited numeric/boolean observations, never source text or paths. No entry shares automatically. See the [v0.4 contract](v04-contract.md).

