# Windows AI Doctor

v0.2.0 · schema 1.0

2026-11-19T14:01:33+00:00

Pass: 7 · Warning: 2 · Error: 0 · Unknown: 6 · Not checked: 4

Paths use opaque references; the original mapping is not saved. Valid syntax does not establish service availability.

## Review first (errors → warnings → unknown)

codex.path, claude.path, codex.install, codex.dependency, codex.version, claude.install, claude.dependency, claude.version

## system.platform — Pass

Current OS; only the current process environment is inspected.

```json
{
  "os": "Windows",
  "python": "3.12.10",
  "windows_target": true
}
```

Recommendation: This is an observation within a limited scope.

Recheck: Review errors first, then warnings and unknown results; after manual changes recheck with the same scope.

Basis: The report retains the check's specific status and evidence.

Limitations: Accounts, authentication, chat history, complete configuration merging and real AI tasks are not checked.

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

Recommendation: The scan is limited.

Recheck: Run Get-Command codex,claude -All and manually review entries outside the scan. Repeat diagnostics with a consistent scope. Official guidance (open manually): https://github.com/openai/codex/blob/main/README.md

Basis: scan_limited is true or a candidate is restricted.

Limitations: An incomplete candidate list cannot prove absence or uniqueness of installations.

## codex.install — Unknown

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "unknown",
  "publisher_verified": false
}
```

Recommendation: The entry format is unrecognized.

Recheck: Run Get-Command codex,claude -All and manually review installation provenance. Compare the wrapper with official setup guidance; an existing target alone does not validate its launcher. Official guidance (open manually): https://github.com/openai/codex/blob/main/README.md

Basis: The installation kind is unknown; native format or a complete npm template was not confirmed.

Limitations: Custom or newer wrappers can also be unknown; wrappers are never executed through a shell.

## codex.dependency — Unknown

Runtime checks depend on the identified entry; native programs do not universally require Node.js.

```json
{
  "runtime": "unknown"
}
```

Recommendation: The Node dependency cannot be determined.

Recheck: Run Get-Command node -All to inspect shell entries. Manually review restricted paths or the package engine range, then recheck. Official guidance (open manually): https://github.com/openai/codex/blob/main/README.md

Basis: The entry, Node path, version response or engine range could not be fully confirmed.

Limitations: Restricted paths, disabled probes and unknown responses do not establish that Node is missing.

## codex.version — Unknown

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "unrecognized_or_missing_runtime"
}
```

Recommendation: Version observations have a limited scope.

Recheck: After manually confirming the entry, run codex --version or claude --version. Official guidance (open manually): https://github.com/openai/codex/blob/main/README.md

Basis: Only short complete version responses are accepted; disabled or unknown responses do not pass.

Limitations: A pass covers this version query only, not service, login or task availability.

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

Recommendation: Configuration checks cover syntax only.

Recheck: Manually confirm that the user or explicit project layer is the intended scope. Consult official configuration guidance before making changes, then recheck. Official guidance (open manually): https://developers.openai.com/codex/config-basic/

Basis: syntax distinguishes valid, absent, unreadable, safety_limit and other observations.

Limitations: Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.

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

Recommendation: Configuration checks cover syntax only.

Recheck: Manually confirm that the user or explicit project layer is the intended scope. Consult official configuration guidance before making changes, then recheck. Official guidance (open manually): https://developers.openai.com/codex/config-basic/

Basis: syntax distinguishes valid, absent, unreadable, safety_limit and other observations.

Limitations: Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.

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

Recommendation: The preferred entry is restricted.

Recheck: Manually inspect whether the intended entry uses links, reparse points or a non-fixed drive. Run Get-Command codex,claude -All to inspect shell selection; retain the unknown result. Official guidance (open manually): https://code.claude.com/docs/en/setup

Basis: The selected candidate has path_access=blocked; existence is unverified.

Limitations: Links are not followed and a restricted preferred entry is not bypassed to execute a later program.

## claude.install — Unknown

Installation type is inferred from local layout; unknown entries are not executed.

```json
{
  "kind": "unknown",
  "publisher_verified": false
}
```

Recommendation: The entry format is unrecognized.

Recheck: Run Get-Command codex,claude -All and manually review installation provenance. Compare the wrapper with official setup guidance; an existing target alone does not validate its launcher. Official guidance (open manually): https://code.claude.com/docs/en/setup

Basis: The installation kind is unknown; native format or a complete npm template was not confirmed.

Limitations: Custom or newer wrappers can also be unknown; wrappers are never executed through a shell.

## claude.dependency — Unknown

Runtime checks depend on the identified entry; native programs do not universally require Node.js.

```json
{
  "runtime": "unknown"
}
```

Recommendation: The Node dependency cannot be determined.

Recheck: Run Get-Command node -All to inspect shell entries. Manually review restricted paths or the package engine range, then recheck. Official guidance (open manually): https://code.claude.com/docs/en/setup

Basis: The entry, Node path, version response or engine range could not be fully confirmed.

Limitations: Restricted paths, disabled probes and unknown responses do not establish that Node is missing.

## claude.version — Unknown

Only a complete matching version response is accepted; raw output is discarded.

```json
{
  "reason": "unrecognized_or_missing_runtime"
}
```

Recommendation: Version observations have a limited scope.

Recheck: After manually confirming the entry, run codex --version or claude --version. Official guidance (open manually): https://code.claude.com/docs/en/setup

Basis: Only short complete version responses are accepted; disabled or unknown responses do not pass.

Limitations: A pass covers this version query only, not service, login or task availability.

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

Recommendation: Configuration checks cover syntax only.

Recheck: Manually confirm that the user or explicit project layer is the intended scope. Consult official configuration guidance before making changes, then recheck. Official guidance (open manually): https://code.claude.com/docs/en/settings

Basis: syntax distinguishes valid, absent, unreadable, safety_limit and other observations.

Limitations: Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.

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

Recommendation: Configuration checks cover syntax only.

Recheck: Manually confirm that the user or explicit project layer is the intended scope. Consult official configuration guidance before making changes, then recheck. Official guidance (open manually): https://code.claude.com/docs/en/settings

Basis: syntax distinguishes valid, absent, unreadable, safety_limit and other observations.

Limitations: Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.

## claude.config.local — Pass

Syntax only for the named configuration file; login, model service, keys and effective values are not validated.

```json
{
  "layer": "project_local",
  "effective_loading": "not_evaluated",
  "path": "<PATH:18>",
  "format": "JSON",
  "syntax": "valid"
}
```

Recommendation: Configuration checks cover syntax only.

Recheck: Manually confirm that the user or explicit project layer is the intended scope. Consult official configuration guidance before making changes, then recheck. Official guidance (open manually): https://code.claude.com/docs/en/settings

Basis: syntax distinguishes valid, absent, unreadable, safety_limit and other observations.

Limitations: Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.

## wsl.launcher — Pass

Only the system WSL launcher is checked; presence does not prove component or distribution availability.

```json
{
  "present": true,
  "component_health": "not_checked"
}
```

Recommendation: The WSL internal environment is not checked.

Recheck: If you use tools inside WSL, inspect installation separately inside the distribution you select yourself. To inspect the Windows registration list only, manually run wsl --list --quiet. Official guidance (open manually): https://learn.microsoft.com/en-us/windows/wsl/basic-commands

Basis: Windows launcher and registration counts are external observations; internal checks always remain skipped.

Limitations: This tool does not start distributions or treat absence of WSL as an AI tool failure.

## wsl.inventory — Pass

Observe only the count of registered distributions for this user; no internal files are read.

```json
{
  "registered_count": 0,
  "reason": "registration_key_absent"
}
```

Recommendation: The WSL internal environment is not checked.

Recheck: If you use tools inside WSL, inspect installation separately inside the distribution you select yourself. To inspect the Windows registration list only, manually run wsl --list --quiet. Official guidance (open manually): https://learn.microsoft.com/en-us/windows/wsl/basic-commands

Basis: Windows launcher and registration counts are external observations; internal checks always remain skipped.

Limitations: This tool does not start distributions or treat absence of WSL as an AI tool failure.

## wsl.running — Not checked

Running state comes only from an explicitly enabled read-only list query; WSL is not executed by default.

```json
{
  "reason": "not_requested",
  "running_count": null
}
```

Recommendation: The WSL internal environment is not checked.

Recheck: If you use tools inside WSL, inspect installation separately inside the distribution you select yourself. To inspect the Windows registration list only, manually run wsl --list --quiet. Official guidance (open manually): https://learn.microsoft.com/en-us/windows/wsl/basic-commands

Basis: Windows launcher and registration counts are external observations; internal checks always remain skipped.

Limitations: This tool does not start distributions or treat absence of WSL as an AI tool failure.

## wsl.internal — Not checked

Commands and configuration inside distributions were not inspected; no distribution was launched.

```json
{}
```

Recommendation: The WSL internal environment is not checked.

Recheck: If you use tools inside WSL, inspect installation separately inside the distribution you select yourself. To inspect the Windows registration list only, manually run wsl --list --quiet. Official guidance (open manually): https://learn.microsoft.com/en-us/windows/wsl/basic-commands

Basis: Windows launcher and registration counts are external observations; internal checks always remain skipped.

Limitations: This tool does not start distributions or treat absence of WSL as an AI tool failure.

## scope.unchecked — Not checked

Merged configuration is not computed; project ancestors, profiles, managed policy, aliases and shell execution policy are outside v0.1 scope.

```json
{}
```

Recommendation: This is an observation within a limited scope.

Recheck: Review errors first, then warnings and unknown results; after manual changes recheck with the same scope.

Basis: The report retains the check's specific status and evidence.

Limitations: Accounts, authentication, chat history, complete configuration merging and real AI tasks are not checked.
