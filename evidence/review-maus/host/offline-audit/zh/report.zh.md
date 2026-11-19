# Windows AI Doctor

v0.1.0 · schema 1.0

2026-11-19T13:15:03+00:00

通过: 7 · 提醒: 1 · 异常: 0 · 无法判断: 3 · 未检查: 5

路径使用代号，原始映射未保存；语法通过不代表服务可用。

## system.platform — 通过

当前操作系统；仅检查当前进程可见环境。

```json
{
  "os": "Windows",
  "python": "3.12.10",
  "windows_target": true
}
```

建议：请在工具官方文档及自身状态页面核实实际生效环境。

复查：请在工具官方文档及自身状态页面核实实际生效环境。

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

建议：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

复查：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

## codex.install — 通过

安装方式仅由本地文件结构推断；未知入口不执行。

```json
{
  "kind": "npm-js",
  "publisher_verified": false
}
```

建议：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

复查：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

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

建议：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

复查：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

## codex.version — 未检查

仅接受完整匹配的版本响应；未保留原始输出。

```json
{
  "reason": "disabled"
}
```

建议：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

复查：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

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

建议：在本机编辑器中复核对应层的配置语法；不要将包含密钥的全文上传。

复查：在本机编辑器中复核对应层的配置语法；不要将包含密钥的全文上传。

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

建议：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

复查：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

## claude.install — 无法判断

安装方式仅由本地文件结构推断；未知入口不执行。

```json
{
  "kind": "not_found",
  "publisher_verified": false
}
```

建议：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

复查：在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。

## claude.dependency — 无法判断

只检查所识别入口的运行时依赖；原生程序不统一要求 Node.js。

```json
{
  "runtime": "unknown"
}
```

建议：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

复查：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

## claude.version — 未检查

仅接受完整匹配的版本响应；未保留原始输出。

```json
{
  "reason": "disabled"
}
```

建议：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

复查：先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。

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

建议：在本机编辑器中复核对应层的配置语法；不要将包含密钥的全文上传。

复查：在本机编辑器中复核对应层的配置语法；不要将包含密钥的全文上传。

## wsl.launcher — 通过

只检查系统 WSL 启动器；存在不等于组件或发行版可用。

```json
{
  "present": true,
  "component_health": "not_checked"
}
```

建议：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

复查：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

## wsl.inventory — 通过

只观察当前用户已注册发行版数量，不读取内部文件。

```json
{
  "registered_count": 0,
  "reason": "registration_key_absent"
}
```

建议：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

复查：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

## wsl.running — 未检查

运行状态只由显式启用的只读列表查询判断；默认不执行 WSL。

```json
{
  "reason": "not_requested",
  "running_count": null
}
```

建议：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

复查：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

## wsl.internal — 未检查

未检查发行版内部命令或配置；没有启动发行版。

```json
{}
```

建议：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

复查：如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。

## scope.unchecked — 未检查

未计算合并配置；项目祖先、配置档、管理策略、别名与终端执行策略不在首版范围。

```json
{}
```

建议：请在工具官方文档及自身状态页面核实实际生效环境。

复查：请在工具官方文档及自身状态页面核实实际生效环境。
