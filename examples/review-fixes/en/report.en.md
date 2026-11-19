# Windows AI Doctor

v0.1.0 · schema 1.0

2026-11-19T12:56:13+00:00

Pass: 6 · Warning: 2 · Error: 1 · Unknown: 6 · Not checked: 4

Paths use opaque references; the original mapping is not saved. Valid syntax does not establish service availability.

## system.platform — Pass

Current OS; only the current process environment is inspected.

```json
{
  "os": "Windows",
  "python": "3.12.10",
  "windows_target": true
}
```

Recommendation: Verify the effective environment in official documentation and the tool's own status view.

Recheck: Verify the effective environment in official documentation and the tool's own status view.

## codex.path — Warning

Some PATH candidates are blocked by links or access limits; existence is unverified, order is retained and they are not executed.

```json
{
  "entries": [
    {
      "path": "<PATH:1>",
      "command_name": "codex.cmd",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "checked",
      "existence_verified": true
    },
    {
      "path": "<PATH:2>",
      "command_name": "codex.com",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:3>",
      "command_name": "codex.exe",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:4>",
      "command_name": "codex.bat",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:5>",
      "command_name": "codex.cmd",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:6>",
      "command_name": "codex.ps1",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:7>",
      "command_name": "codex",
      "installation_group": 2,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    }
  ],
  "installation_groups": 2,
  "cmd_path_candidate": "<PATH:1>",
  "powershell_path_candidate": "<PATH:1>",
  "resolution_model": "PATH+PATHEXT; excludes CWD, aliases and functions",
  "scan_limited": false
}
```

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## codex.install — Unknown

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "unknown",
  "publisher_verified": false
}
```

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## codex.dependency — Unknown

Runtime checks depend on the identified entry; native programs do not universally require Node.js.

```json
{
  "runtime": "unknown"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## codex.version — Unknown

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "unrecognized_or_missing_runtime"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## codex.config.user — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "user",
  "location_source": "CODEX_HOME",
  "path": "<PATH:8>",
  "format": "TOML",
  "syntax": "valid"
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## codex.config.project — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "project",
  "effective_loading": "not_evaluated",
  "path": "<PATH:9>",
  "format": "TOML",
  "syntax": "valid"
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## claude.path — Warning

Some PATH candidates are blocked by links or access limits; existence is unverified, order is retained and they are not executed.

```json
{
  "entries": [
    {
      "path": "<PATH:10>",
      "command_name": "claude.com",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:11>",
      "command_name": "claude.exe",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:12>",
      "command_name": "claude.bat",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:13>",
      "command_name": "claude.cmd",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:14>",
      "command_name": "claude.ps1",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    },
    {
      "path": "<PATH:15>",
      "command_name": "claude",
      "installation_group": 1,
      "kind": "unknown",
      "path_access": "blocked",
      "existence_verified": false
    }
  ],
  "installation_groups": 1,
  "cmd_path_candidate": "<PATH:10>",
  "powershell_path_candidate": "<PATH:14>",
  "resolution_model": "PATH+PATHEXT; excludes CWD, aliases and functions",
  "scan_limited": false
}
```

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## claude.install — Unknown

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "unknown",
  "publisher_verified": false
}
```

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## claude.dependency — Unknown

Runtime checks depend on the identified entry; native programs do not universally require Node.js.

```json
{
  "runtime": "unknown"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## claude.version — Unknown

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "unrecognized_or_missing_runtime"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## claude.config.user — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "user",
  "location_source": "CLAUDE_CONFIG_DIR",
  "path": "<PATH:16>",
  "format": "JSON",
  "syntax": "valid"
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## claude.config.project — Not checked

This optional configuration file is absent; defaults are not a fault.

```json
{
  "layer": "project",
  "effective_loading": "not_evaluated",
  "path": "<PATH:17>",
  "format": "JSON",
  "syntax": "absent"
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## claude.config.local — Error

Configuration syntax or root structure is invalid; content and parser exception text are withheld.

```json
{
  "layer": "project_local",
  "effective_loading": "not_evaluated",
  "path": "<PATH:18>",
  "format": "JSON",
  "syntax": "invalid",
  "line": 1
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## wsl.launcher — Pass

Only the system WSL launcher is checked; presence does not prove component or distribution availability.

```json
{
  "present": true,
  "component_health": "not_checked"
}
```

Recommendation: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

Recheck: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

## wsl.inventory — Pass

Observe only the count of registered distributions for this user; no internal files are read.

```json
{
  "registered_count": 0,
  "reason": "registration_key_absent"
}
```

Recommendation: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

Recheck: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

## wsl.running — Not checked

Running state comes only from an explicitly enabled read-only list query; WSL is not executed by default.

```json
{
  "reason": "not_requested",
  "running_count": null
}
```

Recommendation: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

Recheck: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

## wsl.internal — Not checked

Commands and configuration inside distributions were not inspected; no distribution was launched.

```json
{}
```

Recommendation: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

Recheck: If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately.

## scope.unchecked — Not checked

Merged configuration is not computed; project ancestors, profiles, managed policy, aliases and shell execution policy are outside v0.1 scope.

```json
{}
```

Recommendation: Verify the effective environment in official documentation and the tool's own status view.

Recheck: Verify the effective environment in official documentation and the tool's own status view.
