# v0.7.0 — 2026-11-24 (local candidate; independent review and hosted CI pending)

- Add diagnosis `--format junit`: deterministic UTF-8/LF policy XML; every testcase has non-empty `<properties>` (status → optional scan_limited → baseline_*); non-hit pass/warn/unknown are properties-only; failures express selected exit policy only.
- Add `--fail-on new` (requires `--baseline`): added error/warn versus baseline, excluding scan-limited `.path`; JSON `baseline.new_findings`; MD/HTML “New findings” count; CSV stays ten columns.
- Extend SARIF with stable `partialFingerprints.windowsAIDoctorCheckId/v1`, optional `baselineState` (new/updated/unchanged, no absent), and `new_findings` / `result_baseline_states` under invocation baseline properties; `helpUri` → v07 contract.
- Preserve all v0.6 entries, safety bounds and exit codes; runtime stays standard-library only; version 0.7.0.

# v0.6.0 — 2026-11-22 (published; historical baseline for v0.7)

- Add `--baseline BASE.json` with additive diagnosis `baseline` audit section; reuse compare projections; no free text, paths or timestamps in the baseline object.
- Add `--fail-on regression` (requires `--baseline`): only pass→warn, pass→error or warn→error without scan_limited=true count as regressions; meaning text states fixed transitions, not confirmed root causes.
- Extend diagnosis `--format csv` to ten whitelisted columns including baseline fields; UTF-8 BOM; Chinese/English bodies byte-identical; history/compare CSV unchanged.
- Add diagnosis `--format sarif` as a SARIF 2.1.0 subset without file locations: 19 catalog-sourced rules, error/warn/unknown results only, optional baseline properties; both/all sets unchanged.
- Preserve all v0.5 entries, safety bounds and exit codes; runtime stays standard-library only; version 0.6.0.

# v0.5.0 — 2026-11-21 (published; historical baseline for v0.6)

- Add compare `--format csv` change tables with twelve whitelisted observation columns, UTF-8 BOM and byte-identical Chinese/English bodies; both/all sets unchanged.
- Add offline `--catalog` for the fixed 19-check directory (default md); no input reads, diagnosis, environment, registry or network access.
- Add deterministic `--schema` JSON Schema export; document one-way consistency with `load_report` (schema may be wider; `--validate` sole acceptance authority).
- Preserve all v0.4 entries, safety bounds and exit codes; runtime stays standard-library only.
- r2: reproduce the Python 3.14.10 comparison-CSV audit failure at argparse's first `_colorize` import. Construct and reuse the parser before the operation audit; retain exact two-input read checks and all external-access bans, and deny environment access during the audited operation. Runtime code is unchanged.

# v0.4.0 — 2026-11-21 (historical local development baseline)

- Add offline diagnosis validity checks with recomputed counts and fixed scope notices; validity is separate from health.
- Add bounded in-memory support ZIP verification for fixed regular members, CRC, SHA and support-summary consistency, compatible with v0.3 bundles. This does not authenticate source identity or guarantee privacy of arbitrary text.
- Add history-only UTF-8 BOM CSV long tables from whitelisted observations. Preserve missing checks and empty fields without inferring fixes; both/all output sets are unchanged.
- Make any skipped required test block suite success. Real file/ancestor links require actual local execution; restricted fixture creation is a failed acceptance gate until authorized and retested.
- Extend installed-package checks for all new entries; keep distribution artifacts separate from source snapshots.

# v0.3.0 — 2026-11-21 (historical release)

- Ordered offline history for 2–20 schema-1.0 diagnoses, bilingual MD/JSON/HTML, per-run counts and adjacent changes without health scoring.
- Limited support ZIP rebuilt from whitelisted observations, bilingual summaries, fixed privacy notice and SHA-256 member manifest. No source text or automatic sharing.
- Configurable diagnosis exit conditions (--fail-on error/warn/unknown), additive JSON policy metadata and visible explanations in every format.
- Shared bounded input and derivative-type rejection; scan-limited transitions retain uncertainty even when the supplied status is pass.
- New privacy, offline-mode, input-budget, cleanup, exit-priority and installed-entry checks; independent review and hosted CI remain separate gates.

The entries below describe historical versions, not current candidate verification.

# Changelog

## 0.2.0 — local development, 2026-11-19

- Add offline, script-free, single-file HTML diagnosis and comparison reports in Chinese and English. `--format html` exports HTML; `all` exports MD+JSON+HTML. Existing `both` remains MD+JSON.
- Add bounded, read-only `--compare OLD.json NEW.json`, compatible with v0.1 schema 1.0. Rebuild changes using known IDs and limited numeric fields; do not compare opaque path identities or import arbitrary source text. Removed, unknown and skipped checks never establish a fix.
- Add evidence-selected bilingual observations, basis, manual recheck steps, official guidance and limitations, plus error/warning/unknown review order.
- Preserve complete npm shim recognition, root-to-leaf link rejection, process-tree cleanup and privacy boundaries. Disable argument abbreviation to keep comparison conflicts explicit.
- Add new import/export/security regressions, real link supplements, browser display evidence, sdist-to-wheel build and isolated installation/uninstallation checks, and Windows CI definition (Python 3.11 and 3.14). Hosted CI results await release-stage validation.

## 0.1.0 — published 2026-11-19

- Initial limited Codex/Claude PATH, launcher, dependency, version, config-syntax and Windows/WSL visibility checks with bilingual MD/JSON and opaque path references.
- Final release included complete npm-shim validation and root-to-leaf reparse rejection. Routine full suite: 38 passed, 1 skipped; authorized separate single-case supplement passed. These are historical v0.1 results.
