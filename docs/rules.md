# 规则依据与适用边界 / Rules and scope

核对日期：2026-11-19（北京时间）。依据为本轮实际打开的官方文档和 OpenAI 仓库源文件；网页可能继续变化。适用范围为 v0.1 的有限本地观察，不承诺覆盖全部上游版本。

## 官方来源

| 来源 | 本次用于确认的事实 | 适用范围 |
| --- | --- | --- |
| [OpenAI Codex README](https://github.com/openai/codex/blob/main/README.md) | 存在 Windows 原生/独立安装途径 | 原生入口，不将 Node 视为通用依赖 |
| [Codex npm package.json](https://github.com/openai/codex/blob/main/codex-cli/package.json) | `@openai/codex`、`bin/codex.js`、当前 `engines.node >=16` | 已识别 npm JS 包；实现优先读取本地包引擎字段，只有简单 `>=major[.minor[.patch]]` 范围才判断版本 |
| [Codex npm launcher](https://github.com/openai/codex/blob/main/codex-cli/bin/codex.js) | JS 包入口再定位平台程序 | 直接通过 Node 调用入口，避免运行 shell 包装器 |
| [Codex config basics](https://developers.openai.com/codex/config-basic/) | 用户 TOML、项目层及信任条件 | 仅查用户层和显式项目根的语法，不计算最终有效配置 |
| [Codex advanced config](https://developers.openai.com/codex/config-advanced/) | `CODEX_HOME` 覆盖默认 `~/.codex` | 只打开 `config.toml`，不打开其中列出的认证/历史文件 |
| [Codex Windows](https://developers.openai.com/codex/windows/) | Windows 原生与 WSL 是不同执行环境 | 不要求必须安装 WSL，也不以 Windows 检查代替 WSL 检查 |
| [Claude Code setup](https://code.claude.com/docs/en/setup) | 原生安装和 `--version`；当前 npm 包也可携带原生二进制 | 依赖按实际入口格式区分。该页当前的 npm 安装 Node 要求不作为所有已安装 CLI 的运行时要求 |
| [Claude settings](https://code.claude.com/docs/en/settings) | 用户/项目/项目本地 JSON；存在管理层及优先规则 | 只作各文件独立语法检查，不评估覆盖、列表合并、管理策略或生效键 |
| [Claude environment variables](https://code.claude.com/docs/en/env-vars) | `CLAUDE_CONFIG_DIR`；更新和非必要流量控制变量 | 仅当前进程环境中的目录覆盖；不尝试从已加载管理策略/配置 `env` 推断二次覆盖 |
| [Claude CLI reference](https://code.claude.com/docs/en/cli-reference) | 版本查询 CLI | 仅 `--version`，不运行 `doctor`、登录、安装、更新或实际任务 |
| [Microsoft WSL basic commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands) | `--list`、`--running`、`--quiet` 为列表选项 | 只有 `--wsl-list` 显式启用时执行系统列表命令；绝不运行发行版命令 |
| [npm cmd-shim 8.0.0](https://github.com/npm/cmd-shim/blob/v8.0.0/lib/index.js) | npm 标准 CMD/PowerShell/sh 包装器的生成形式；本机已有相同版本的生成器输出已实测 | 只匹配完整的无附加参数 Node 或直接原生目标形式；仅空行、行首尾空白及 CRLF/LF 可不同，自定义/残缺/其他版本可能未知 |
| [Python Path.lstat](https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.lstat)、[Microsoft reparse points](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points) | lstat 的叶子不跟随语义；重解析点可用于目录链接和挂载目录 | 先从根逐级拒绝链接/重解析祖先，再访问后代；这是本项目保守读取策略，并非所有 Windows 工具的运行要求 |

OpenAI 文档本轮部分重定向至 `learn.chatgpt.com/docs/...`；上表保留官方稳定入口。没有从历史 Issue 创建“所有版本均故障”的规则。

## 稳定检查编号

| 编号 | 观察与判断 |
| --- | --- |
| `system.platform` | Windows 为目标；其他系统输出范围提醒 |
| `{tool}.path` | 只枚举 PATH 的固定文件名；Windows 受 PATHEXT 影响；`.ps1`/无扩展入口也作为线索列出。缺失/多组/扫描受限为提醒 |
| `{tool}.install` | 本地布局推断 `native` / `npm-native` / `npm-js`；其他为未知，包管理器来源/签名不作推断 |
| `{tool}.dependency` | 原生入口不要求 Node；已识别 npm JS 入口检查 Node 与可解释的本地 engines 范围；缺失或低于该范围为异常 |
| `{tool}.version` | 只查询按 PATH/PATHEXT 选出的 CMD 候选。完整匹配版本才通过；非零/超时/输出过长/无法启动/未知入口为无法判断 |
| `{tool}.config.user` | `CODEX_HOME/config.toml` 或 `CLAUDE_CONFIG_DIR/settings.json`，未设则用户主目录默认位置；语法异常为错误，文件缺失为未检查 |
| `{tool}.config.project` | 仅在 `--project` 时检查显式根中的配置文件；不判断信任状态或上级仓库层 |
| `claude.config.local` | 显式项目根的 `.claude/settings.local.json` |
| `wsl.launcher` | 只看系统启动器是否存在；不是 WSL 功能验收 |
| `wsl.inventory` | 只读 HKCU Lxss 子键数量；缺键仅说明当前用户无可见注册信息。此项是实现观察，不是微软承诺的稳定接口 |
| `wsl.running` | 默认未检查；显式列表成功时只保留数量。退出失败/异常输出为无法判断 |
| `wsl.internal` | 永远未检查，不启动发行版、不读取内部配置 |
| `scope.unchecked` | 明示完整合并配置、管理/配置档/祖先层及交互终端解析未覆盖 |

## 实现策略而非上游故障规则

- 路径只导出代号和固定命令名；原始映射不保存。最多 512 个 PATH 项、32 个工具候选，达到上限明确提醒。
- 只检查 Windows 固定本地盘；跳过 UNC、映射网络盘、移动盘和隐式当前目录。
- JSON 需要对象根、拒绝 NaN/Infinity；TOML 用 Python 3.11+ `tomllib`。仅支持 UTF-8、单文件 1 MiB；不做键名/schema/服务有效性验证。
- 所有配置、命令、包元数据/目标及 Node 路径均从根到叶逐级 `lstat`，拒绝链接/重解析点后不再查询后代。拒绝 `..` 与 Windows 备用数据流，不用 `resolve` 跟随包目标。Windows 文件替换竞争和硬链接不是完整安全边界。
- 包元数据、包装器各限 64 KiB；JS 入口识别限 1 MiB。超大/复杂历史版本或自定义 shim 可能保持未知。
- 原生识别依据可见二进制格式，并不验证签名。npm 要求包名、词法受限的 bin 及完整标准包装模板一致，不执行包装器；只有路径子串不成立。Node 包装器不能转而作为原生目标执行。模板基于 `cmd-shim 8.0.0`，不是对所有历史/未来版本兼容的承诺。
- 受限 PATH 候选保留顺序，`path_access=blocked`、`existence_verified=false` 明示存在性尚未检查，不以路径受限推断安装成功或缺失。受限/不可识别的优先 Node 不回退到后续 Node，依赖为未知。
- 版本命令只作用于首个 CMD 候选，不对所有重复入口执行；当前 PowerShell 的别名、函数、CWD、执行策略可能改变实际结果。
- 原生运行依赖之外的特性（Git、搜索、插件等）未验收，不据此声明完整功能正常。
- 版本查询的临时 HOME、关闭更新/遥测变量和代理是减少副作用的措施，并非网络或凭据访问的强制沙箱；`--no-version` 可跳过它们。

## 本机版本覆盖

本轮实际安装覆盖为 Windows 上的 Codex npm JS 启动器 `0.169.0`（Node `24.19.0`）。Claude CLI 的本机 PATH 无入口；Claude 原生和 npm-native 只用合成程序验证识别与调用机制，不能称为真实发行包兼容测试。详细实跑记录见 [validation.md](validation.md)。
