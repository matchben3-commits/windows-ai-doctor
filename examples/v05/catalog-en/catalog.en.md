# Windows AI Doctor — Check catalog

v0.7.0 · schema 1.0

This catalog lists stable check IDs and fixed descriptions the current version can produce. It does not assert that checks always run, that the environment is healthy, or that the catalog itself verifies installations. No input files, diagnosis, environment, registry, network or packaged paths are consulted.

Status vocabulary: pass, warn, error, unknown, skipped

## claude.config.local

Target: claude

Availability: project only

Produced by current version: 是

Purpose: With an explicit --project root, check UTF-8 syntax and an object root for Claude settings.local.json.

Evidence fields: layer, effective_loading, path, format, syntax, line

Limitation: Emitted only with --project; no merge evaluation, account checks, or proof that local overrides apply.

## claude.config.project

Target: claude

Availability: project only

Produced by current version: 是

Purpose: With an explicit --project root, check UTF-8 syntax and an object root for the Claude project settings.json.

Evidence fields: layer, effective_loading, path, format, syntax, line

Limitation: Emitted only with --project; ancestors are not walked and effective merged configuration is not computed.

## claude.config.user

Target: claude

Availability: always

Produced by current version: 是

Purpose: Check UTF-8 syntax and an object root for the user-layer Claude settings.json.

Evidence fields: layer, location_source, path, format, syntax, line

Limitation: The file may be absent; valid syntax does not establish login, API or service availability; config values are not exported.

## claude.dependency

Target: claude

Availability: always

Produced by current version: 是

Purpose: Observe runtime clues required by a recognized Claude launcher (native or Node).

Evidence fields: runtime, node_required, scope, node_found, node_path_check, documented_package_engine, reason, version, probe_reason

Limitation: Covers launcher runtime only; the full dependency tree and optional features are not validated.

## claude.install

Target: claude

Availability: always

Produced by current version: 是

Purpose: Observe whether the Claude installation kind is recognizable from the launcher layout.

Evidence fields: kind, publisher_verified

Limitation: Not signature or publisher verification; an unknown kind does not prove absence of an installation.

## claude.path

Target: claude

Availability: always

Produced by current version: 是

Purpose: Observe Claude PATH/PATHEXT candidates and installation-group clues under the limited resolution model.

Evidence fields: entries, installation_groups, cmd_path_candidate, powershell_path_candidate, resolution_model, scan_limited

Limitation: No disk search; aliases/functions are outside prediction; a limited scan cannot prove absence or uniqueness.

## claude.version

Target: claude

Availability: always

Produced by current version: 是

Purpose: Perform a bounded --version observation against a recognized Claude launcher.

Evidence fields: reason, returncode, version, captured_bytes, timeout_seconds

Limitation: Only short complete version responses are accepted; a pass covers this query only, not service or task availability.

## codex.config.project

Target: codex

Availability: project only

Produced by current version: 是

Purpose: With an explicit --project root, check UTF-8 syntax and an object root for the Codex project config.toml.

Evidence fields: layer, effective_loading, path, format, syntax, line

Limitation: Emitted only with --project; ancestors are not walked and effective merged configuration is not computed.

## codex.config.user

Target: codex

Availability: always

Produced by current version: 是

Purpose: Check UTF-8 syntax and an object root for the user-layer Codex config.toml.

Evidence fields: layer, location_source, path, format, syntax, line

Limitation: The file may be absent; valid syntax does not establish effective configuration or service availability; config values are not exported.

## codex.dependency

Target: codex

Availability: always

Produced by current version: 是

Purpose: Observe runtime clues required by a recognized Codex launcher (native or Node).

Evidence fields: runtime, node_required, scope, node_found, node_path_check, documented_package_engine, reason, version, probe_reason

Limitation: Covers launcher runtime only; the full dependency tree and optional features are not validated.

## codex.install

Target: codex

Availability: always

Produced by current version: 是

Purpose: Observe whether the Codex installation kind is recognizable from the launcher layout.

Evidence fields: kind, publisher_verified

Limitation: Not signature or publisher verification; an unknown kind does not prove absence of an installation.

## codex.path

Target: codex

Availability: always

Produced by current version: 是

Purpose: Observe Codex PATH/PATHEXT candidates and installation-group clues under the limited resolution model.

Evidence fields: entries, installation_groups, cmd_path_candidate, powershell_path_candidate, resolution_model, scan_limited

Limitation: No disk search; aliases/functions are outside prediction; a limited scan cannot prove absence or uniqueness.

## codex.version

Target: codex

Availability: always

Produced by current version: 是

Purpose: Perform a bounded --version observation against a recognized Codex launcher.

Evidence fields: reason, returncode, version, captured_bytes, timeout_seconds

Limitation: Only short complete version responses are accepted; a pass covers this query only, not service or task availability.

## scope.unchecked

Target: scope

Availability: always

Produced by current version: 是

Purpose: Record that accounts, authentication, chat history, full configuration merging and real AI tasks remain outside scope.

Evidence fields: (none)

Limitation: Always a skipped scope notice; it does not establish host health or that other checks passed.

## system.platform

Target: system

Availability: always

Produced by current version: 是

Purpose: Record the OS class and Python version clues visible to the current interpreter.

Evidence fields: os, python, windows_target

Limitation: Not a hardware inventory or patch audit; the Windows-target flag reflects os.name only.

## wsl.internal

Target: wsl

Availability: always

Produced by current version: 是

Purpose: Record that the WSL distribution interior is never inspected.

Evidence fields: (none)

Limitation: Always skipped; distributions are not started and absence of WSL is not treated as an AI tool failure.

## wsl.inventory

Target: wsl

Availability: always

Produced by current version: 是

Purpose: On Windows, observe the current-user Lxss registration subkey count clue.

Evidence fields: registered_count, reason

Limitation: Distribution names are not listed; non-Windows hosts skip; this is not component-health proof.

## wsl.launcher

Target: wsl

Availability: always

Produced by current version: 是

Purpose: Observe whether the system-directory WSL launcher is present (native-format clue).

Evidence fields: present, component_health, reason

Limitation: Component health is not checked; non-Windows hosts skip; presence does not establish a usable distribution.

## wsl.running

Target: wsl

Availability: always

Produced by current version: 是

Purpose: When --wsl-list is explicit, observe a read-only running-distribution count.

Evidence fields: reason, running_count, returncode

Limitation: Default is no execution; with explicit permission the list still runs even under --no-version; names are never exported.

