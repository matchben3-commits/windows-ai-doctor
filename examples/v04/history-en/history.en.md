# Windows AI Doctor — History

v0.4.0 · schema 1.0

2026-11-21T10:50:57+00:00

Order follows the command line. Confirm that all reports cover the same environment and scope; machine identity is not inferred. Counts are not a health score. Missing, unknown, skipped or scan-limited checks do not establish a fix; a pass covers this check now only. Only known check states, numeric versions, installation-group counts and scan limits are compared.

## Counts by run

| Sequence | Pass | Warning | Error | Unknown | Not checked |
| --- | --- | --- | --- | --- | --- |
| Run 1 | 1 | 0 | 2 | 0 | 1 |
| Run 2 | 0 | 1 | 0 | 1 | 1 |
| Run 3 | 3 | 0 | 0 | 0 | 1 |

## Check states and limited observations

| ID | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| codex.config.user | × Error | — Missing | ✓ Pass |
| codex.path | ✓ Pass {"installation_groups": 1, "scan_limited": false} | ! Warning {"installation_groups": 2, "scan_limited": true} | ✓ Pass {"installation_groups": 3, "scan_limited": false} |
| codex.version | × Error {"version": "1.2.1"} | ? Unknown {"version": "1.2.2"} | ✓ Pass {"version": "1.2.3"} |
| scope.unchecked | — Not checked | — Not checked | — Not checked |

## Run 1 → Run 2

Unchanged checks: 1

- codex.config.user: error → —. Not included this time; not rechecked. {}

- codex.path: pass → warn. Unknown, not rechecked or scan limited; this does not establish a fix. {"installation_groups": {"before": 1, "after": 2}, "scan_limited": {"before": false, "after": true}}

- codex.version: error → unknown. Unknown, not rechecked or scan limited; this does not establish a fix. {"version": {"before": "1.2.1", "after": "1.2.2"}}

## Run 2 → Run 3

Unchanged checks: 1

- codex.config.user: — → pass. Check added in this report. {}

- codex.path: warn → pass. This check passes now. {"installation_groups": {"before": 2, "after": 3}, "scan_limited": {"before": true, "after": false}}

- codex.version: unknown → pass. This check passes now. {"version": {"before": "1.2.2", "after": "1.2.3"}}
