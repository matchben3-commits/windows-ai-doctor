# Windows AI Doctor — Comparison

v0.2.0 · schema 1.0

2026-11-19T14:01:33+00:00

Added: 0 · Removed: 0 · Changed: 1

Confirm that both reports cover the same environment and scope; path references have no identity across runs. A pass covers this check now only; unknown, skipped and removed checks do not establish a fix. Only numeric versions, installation-group counts and scan limits are compared; other evidence is not compared.

Unchanged checks: 18

## claude.config.local — Changed

error → pass

This check passes now.

```json
{}
```
