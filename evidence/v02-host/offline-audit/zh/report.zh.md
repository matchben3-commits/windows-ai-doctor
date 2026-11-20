# Windows AI Doctor

v0.2.0 · schema 1.0

2026-11-19T14:00:56+00:00

通过: 7 · 提醒: 1 · 异常: 0 · 无法判断: 3 · 未检查: 5

路径使用代号，原始映射未保存；语法通过不代表服务可用。

## 优先处理（异常 → 提醒 → 无法判断）

claude.path, codex.dependency, claude.install, claude.dependency

## system.platform — 通过

当前操作系统；仅检查当前进程可见环境。

```json
{
  "os": "Windows",
  "python": "3.12.10",
  "windows_target": true
}
```

建议：此项仅反映限定范围内的观察。

复查：先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。

判断依据：报告保留具体检查状态与证据。

检查限制：不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。

## codex.path — 通过

按 PATH 顺序列出入口；同一安装的包装入口合并计数。

```json
{
  "entries": [
    {
      "path": "<PATH:1>",
      "command_name": "codex.cmd",
      "installation_group": 1,
      "kind": "npm-js",
      "path_access": "checked",
      "existence_verified": true
    },
    {
      "path": "<PATH:2>",
      "command_name": "codex.ps1",
      "installation_group": 1,
      "kind": "npm-js",
      "path_access": "checked",
      "existence_verified": true
    },
    {
      "path": "<PATH:3>",
      "command_name": "codex",
      "installation_group": 1,
      "kind": "npm-js",
      "path_access": "checked",
      "existence_verified": true
    }
  ],
  "installation_groups": 1,
  "cmd_path_candidate": "<PATH:1>",
  "powershell_path_candidate": "<PATH:2>",
  "resolution_model": "PATH+PATHEXT; excludes CWD, aliases and functions",
  "scan_limited": false
}
```

建议：此项仅反映限定范围内的观察。

复查：先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。 官方说明（手动查看）：https://github.com/openai/codex/blob/main/README.md

判断依据：报告保留具体检查状态与证据。

检查限制：不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。

## codex.install — 通过

安装方式仅由本地文件结构推断；未知入口不执行。

```json
{
  "kind": "npm-js",
  "publisher_verified": false
}
```

建议：此项仅反映限定范围内的观察。

复查：先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。 官方说明（手动查看）：https://github.com/openai/codex/blob/main/README.md

判断依据：报告保留具体检查状态与证据。

检查限制：不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。

## codex.dependency — 无法判断

只检查所识别入口的运行时依赖；原生程序不统一要求 Node.js。

```json
{
  "runtime": "node",
  "node_found": true,
  "node_path_check": "found",
  "documented_package_engine": ">=16",
  "reason": "version_probe_disabled"
}
```

建议：Node 依赖无法判断。

复查：运行 Get-Command node -All 核对终端入口。 人工检查受限路径或本地包引擎范围，再体检。 官方说明（手动查看）：https://github.com/openai/codex/blob/main/README.md

判断依据：入口或 Node 路径、版本响应、引擎范围未能完整确认。

检查限制：路径受限、探测关闭或响应未知均不等于未安装。

## codex.version — 未检查

仅接受完整匹配的版本响应；未保留原始输出。

```json
{
  "reason": "disabled"
}
```

建议：版本观察有范围限制。

复查：人工确认入口后运行 codex --version 或 claude --version。 官方说明（手动查看）：https://github.com/openai/codex/blob/main/README.md

判断依据：仅接受短且完整匹配的版本响应；禁用或未知响应不算通过。

检查限制：版本通过仅表示本次版本查询通过，不验证服务、登录或实际任务。

## codex.config.user — 通过

仅检查指定配置文件的语法；不验证登录、模型服务、键名或最终生效值。

```json
{
  "layer": "user",
  "location_source": "default_home",
  "path": "<PATH:4>",
  "format": "TOML",
  "syntax": "valid"
}
```

建议：配置只做有限语法检查。

复查：人工核对本次用户层或显式项目层是否是预期检查范围。 需要修改时先参照官方配置说明，再运行体检。 官方说明（手动查看）：https://developers.openai.com/codex/config-basic/

判断依据：syntax 区分 valid、absent、unreadable 和 safety_limit 等观察。

检查限制：文件可缺省；语法通过不等于配置生效或服务可用；受限文件不继续读取。

## claude.path — 提醒

当前 PATH 未发现可调用入口；不等于机器上完全未安装。

```json
{
  "entries": [],
  "installation_groups": 0,
  "cmd_path_candidate": null,
  "powershell_path_candidate": null,
  "resolution_model": "PATH+PATHEXT; excludes CWD, aliases and functions",
  "scan_limited": false
}
```

建议：PATH 未发现可选入口。

复查：在实际使用的 PowerShell 中运行 Get-Command codex,claude -All，核对入口。 按官方安装说明人工检查安装位置；调整后打开新终端再体检。 官方说明（手动查看）：https://code.claude.com/docs/en/setup

判断依据：本次限定范围中没有选中的 CMD/PATHEXT 候选。

检查限制：不扫描磁盘；未发现不等于未安装。

## claude.install — 无法判断

安装方式仅由本地文件结构推断；未知入口不执行。

```json
{
  "kind": "not_found",
  "publisher_verified": false
}
```

建议：此项仅反映限定范围内的观察。

复查：先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。 官方说明（手动查看）：https://code.claude.com/docs/en/setup

判断依据：报告保留具体检查状态与证据。

检查限制：不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。

## claude.dependency — 无法判断

只检查所识别入口的运行时依赖；原生程序不统一要求 Node.js。

```json
{
  "runtime": "unknown"
}
```

建议：Node 依赖无法判断。

复查：运行 Get-Command node -All 核对终端入口。 人工检查受限路径或本地包引擎范围，再体检。 官方说明（手动查看）：https://code.claude.com/docs/en/setup

判断依据：入口或 Node 路径、版本响应、引擎范围未能完整确认。

检查限制：路径受限、探测关闭或响应未知均不等于未安装。

## claude.version — 未检查

仅接受完整匹配的版本响应；未保留原始输出。

```json
{
  "reason": "disabled"
}
```

建议：版本观察有范围限制。

复查：人工确认入口后运行 codex --version 或 claude --version。 官方说明（手动查看）：https://code.claude.com/docs/en/setup

判断依据：仅接受短且完整匹配的版本响应；禁用或未知响应不算通过。

检查限制：版本通过仅表示本次版本查询通过，不验证服务、登录或实际任务。

## claude.config.user — 通过

仅检查指定配置文件的语法；不验证登录、模型服务、键名或最终生效值。

```json
{
  "layer": "user",
  "location_source": "default_home",
  "path": "<PATH:5>",
  "format": "JSON",
  "syntax": "valid"
}
```

建议：配置只做有限语法检查。

复查：人工核对本次用户层或显式项目层是否是预期检查范围。 需要修改时先参照官方配置说明，再运行体检。 官方说明（手动查看）：https://code.claude.com/docs/en/settings

判断依据：syntax 区分 valid、absent、unreadable 和 safety_limit 等观察。

检查限制：文件可缺省；语法通过不等于配置生效或服务可用；受限文件不继续读取。

## wsl.launcher — 通过

只检查系统 WSL 启动器；存在不等于组件或发行版可用。

```json
{
  "present": true,
  "component_health": "not_checked"
}
```

建议：WSL 内部环境未检查。

复查：若实际在 WSL 内使用工具，请在自己选定的发行版内单独核对安装。 仅需查看 Windows 注册列表时，可人工运行 wsl --list --quiet。 官方说明（手动查看）：https://learn.microsoft.com/en-us/windows/wsl/basic-commands

判断依据：Windows 启动器和注册数量仅是外部观察；内部检查始终跳过。

检查限制：本工具不启动发行版，也不把未安装 WSL 判为 AI 工具故障。

## wsl.inventory — 通过

只观察当前用户已注册发行版数量，不读取内部文件。

```json
{
  "registered_count": 0,
  "reason": "registration_key_absent"
}
```

建议：WSL 内部环境未检查。

复查：若实际在 WSL 内使用工具，请在自己选定的发行版内单独核对安装。 仅需查看 Windows 注册列表时，可人工运行 wsl --list --quiet。 官方说明（手动查看）：https://learn.microsoft.com/en-us/windows/wsl/basic-commands

判断依据：Windows 启动器和注册数量仅是外部观察；内部检查始终跳过。

检查限制：本工具不启动发行版，也不把未安装 WSL 判为 AI 工具故障。

## wsl.running — 未检查

运行状态只由显式启用的只读列表查询判断；默认不执行 WSL。

```json
{
  "reason": "not_requested",
  "running_count": null
}
```

建议：WSL 内部环境未检查。

复查：若实际在 WSL 内使用工具，请在自己选定的发行版内单独核对安装。 仅需查看 Windows 注册列表时，可人工运行 wsl --list --quiet。 官方说明（手动查看）：https://learn.microsoft.com/en-us/windows/wsl/basic-commands

判断依据：Windows 启动器和注册数量仅是外部观察；内部检查始终跳过。

检查限制：本工具不启动发行版，也不把未安装 WSL 判为 AI 工具故障。

## wsl.internal — 未检查

未检查发行版内部命令或配置；没有启动发行版。

```json
{}
```

建议：WSL 内部环境未检查。

复查：若实际在 WSL 内使用工具，请在自己选定的发行版内单独核对安装。 仅需查看 Windows 注册列表时，可人工运行 wsl --list --quiet。 官方说明（手动查看）：https://learn.microsoft.com/en-us/windows/wsl/basic-commands

判断依据：Windows 启动器和注册数量仅是外部观察；内部检查始终跳过。

检查限制：本工具不启动发行版，也不把未安装 WSL 判为 AI 工具故障。

## scope.unchecked — 未检查

未计算合并配置；项目祖先、配置档、管理策略、别名与终端执行策略不在首版范围。

```json
{}
```

建议：此项仅反映限定范围内的观察。

复查：先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。

判断依据：报告保留具体检查状态与证据。

检查限制：不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。
