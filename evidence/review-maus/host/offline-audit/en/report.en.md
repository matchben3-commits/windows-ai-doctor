# Windows AI Doctor

v0.1.0 · schema 1.0

2026-11-19T13:15:03+00:00

Pass: 7 · Warning: 1 · Error: 0 · Unknown: 3 · Not checked: 5

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

## codex.path — Pass

Entries are ordered by PATH; wrappers for one installation share a group.

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

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## codex.install — Pass

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "npm-js",
  "publisher_verified": false
}
```

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## codex.dependency — Unknown

Runtime checks depend on the identified entry; native programs do not universally require Node.js.

```json
{
  "runtime": "node",
  "node_found": true,
  "node_path_check": "found",
  "documented_package_engine": ">=16",
  "reason": "version_probe_disabled"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## codex.version — Not checked

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "disabled"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## codex.config.user — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "user",
  "location_source": "default_home",
  "path": "<PATH:4>",
  "format": "TOML",
  "syntax": "valid"
}
```

Recommendation: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

Recheck: Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets.

## claude.path — Warning

No callable entry in the current PATH; this does not prove the tool is absent from the machine.

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

Recommendation: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

Recheck: In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths.

## claude.install — Unknown

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "not_found",
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

## claude.version — Not checked

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "disabled"
}
```

Recommendation: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

Recheck: First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check.

## claude.config.user — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "user",
  "location_source": "default_home",
  "path": "<PATH:5>",
  "format": "JSON",
  "syntax": "valid"
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
