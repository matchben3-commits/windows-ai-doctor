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
