# Windows AI Doctor

v0.7.0 · schema 1.0

2000-01-01T00:00:00+00:00

Pass: 2 · Warning: 1 · Error: 1 · Unknown: 2 · Not checked: 1

## Baseline comparison

Confirm that the baseline and current diagnosis cover the same environment and scope. Regression means only pass→warn, pass→error or warn→error without a scan limit; it does not establish a fault&#x27;s root cause. Added, removed, unknown and skipped checks do not establish a fix. Only states, numeric versions, installation-group counts and scan limits are compared.

Added: 2 · Removed: 1 · Changed: 3 · Regressions: 2 · Unchanged: 2 · New findings: 0

### claude.path — changed

pass → error

Observed fields or status changed.

**Regression under fixed rules**

```json
{
  "installation_groups": {
    "before": 1,
    "after": 0
  }
}
```

### claude.version — added

— → pass

Check added in this report.

```json
{
  "version": {
    "before": null,
    "after": "2.3.4"
  }
}
```

### codex.path — changed

warn → unknown

Unknown, not rechecked or scan limited; this does not establish a fix.

```json
{
  "scan_limited": {
    "before": false,
    "after": true
  }
}
```

### codex.version — changed

pass → warn

Observed fields or status changed.

**Regression under fixed rules**

```json
{
  "version": {
    "before": "1.2.3",
    "after": "1.2.4"
  }
}
```

### wsl.internal — added

— → skipped

Check added in this report.

```json
{}
```

### wsl.running — removed

pass → —

Not included this time; not rechecked.

```json
{}
```

## Exit conditions

Selected states: regression; triggered states: regression; selected conditions met: Yes. Meeting the selected exit conditions means a selected state occurred; unknown is not a confirmed fault. Operational failure exits 2; interruption exits 130. Regression means fixed state transitions without a scan limit; it does not establish a fault's root cause. New findings mean only added error/warn versus baseline, excluding scan-limited paths; they do not establish a fault's root cause.

Paths use opaque references; the original mapping is not saved. Valid syntax does not establish service availability.

## Review first (errors → warnings → unknown)

claude.path, codex.version, codex.path, scope.unchecked

## system.platform — Pass

Authored synthetic observation, not host state.

```json
{}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## claude.path — Error

Authored synthetic observation, not host state.

```json
{
  "installation_groups": 0,
  "scan_limited": false
}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## codex.version — Warning

Authored synthetic observation, not host state.

```json
{
  "version": "1.2.4"
}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## codex.path — Unknown

Authored synthetic observation, not host state.

```json
{
  "installation_groups": 1,
  "scan_limited": true
}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## claude.version — Pass

Authored synthetic observation, not host state.

```json
{
  "version": "2.3.4"
}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## scope.unchecked — Unknown

Authored synthetic observation, not host state.

```json
{}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.

## wsl.internal — Not checked

Authored synthetic observation, not host state.

```json
{}
```

Recommendation: Review the check scope.

Recheck: Recheck with a separate real diagnosis.
