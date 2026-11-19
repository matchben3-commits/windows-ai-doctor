# 隐私与执行边界 / Privacy and execution boundaries

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
