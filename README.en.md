# Windows AI Doctor

[中文](README.md) · v0.4.0 · Python 3.11+ · Windows first · standard library runtime

Limited local diagnostics for Codex CLI and Claude Code CLI: PATH entries, duplicate installation clues, versions, launcher-specific runtimes, configuration syntax and Windows/WSL visibility. Export English or Chinese Markdown, JSON and standalone offline HTML with manual guidance. It diagnoses without installing, upgrading, repairing, logging in or calling model APIs.

## New in v0.4

- `--validate REPORT.json`: accept diagnoses under known fields and bounds, recomputing counts; error findings do not invalidate an input.
- `--verify-support BUNDLE.zip`: verify fixed members, CRC, SHA and summary consistency in memory; this does not prove source identity or privacy of arbitrary text.
- `--history ... --format csv`: UTF-8 BOM long tables with known IDs and limited state/numeric/boolean observations. Missing checks use missing; repairs are not inferred.

```powershell
python .\doctor.py --validate first.json --lang en --format json
python .\doctor.py --verify-support .\reports\support-new\support-bundle.zip --lang en
python .\doctor.py --history first.json second.json --format csv --output-dir .\reports\csv-new
python .\examples\make_v04_demo.py .\reports\v04-demo-new
```

Validation and verification support both/md/json. CSV is history-only; both/all retain their output sets. Successful validation/verification exits 0, failure 2, interruption 130, without a new diagnosis. See the [v0.4 contract](docs/v04-contract.md) for bounds and empty-value meanings.

## Retained from v0.3

- History over 2–20 saved diagnoses, ordered by the command line, with counts, per-check observations and adjacent changes.
- A support ZIP rebuilt from a fixed whitelist, containing bilingual limited summaries, machine-readable observations and member hashes; review it before sharing.
- Custom `--fail-on error warn unknown` conditions, affecting only the completed diagnosis exit decision.

```powershell
python .\doctor.py --no-version --lang en --format all --output-dir .\reports\first
python .\doctor.py --history first.json second.json third.json --lang en --format all --output-dir .\reports\history-new
python .\doctor.py --support first.json --output-dir .\reports\support-new
python .\doctor.py --no-version --fail-on error warn unknown --lang en --format all --output-dir .\reports\strict-new
```

History and support only read their explicit inputs: no new diagnosis, CLI/Node/WSL calls, networking or access to embedded paths. Confirm that histories cover the same environment and scope yourself; timestamps and opaque paths cannot establish machine identity. Counts are not a health score. Unknown, skipped, missing or scan-limited checks never establish a fix; a pass covers this check now only.

The support bundle is a limited summary, not a guarantee of unlinkability; no original path mapping exists. Its five fixed members are summary.zh.md, summary.en.md, support.json, PRIVACY.txt and SHA256SUMS.txt. Source text/JSON, configuration, logs, environment values and screenshots are omitted. Nothing is sent automatically. An output directory is required; format/lang/fail-on and diagnostic options conflict with support. See the [v0.3 contract](docs/v03-contract.md).

## Run or install

Source execution needs no administrator, pip or API key:

```powershell
python .\doctor.py --help
python .\doctor.py --tools codex --lang en --format json
python .\doctor.py --project "D:\Example project" --output-dir .\reports\project-new
python .\doctor.py --compare first.json second.json --lang en --format all --output-dir .\reports\comparison-new
```

Replace sample paths with your own files. If Python is not on PATH, use your installed Python 3.11+ absolute executable path. Alternatively install a wheel in your own venv with `python -m pip install <wheel-file>` and use `windows-ai-doctor`. Runtime has no third-party dependencies.

- `--tools codex claude` defaults to both; `--home` overrides the target home. CODEX_HOME/CLAUDE_CONFIG_DIR take priority over default .codex/.claude locations.
- `--project` inspects only fixed configuration files at that explicit root, not ancestor layers or effective merged settings.
- `--timeout` is 0.1–30 seconds per query, default 3; `--no-version` skips CLI/Node execution.
- `--wsl-list` separately permits a read-only running-distribution list even with no-version; omit it for no external commands.
- `--lang zh|en`; `--format both|md|json|html|all`. Default both is MD+JSON; all is three formats. Without an output directory, both/all print MD, single formats print that format.
- Filenames: report.LANG.FORMAT, comparison.LANG.FORMAT and history.LANG.FORMAT. Existing files are preserved; failed/interrupted writes remove only newly created files.
- compare/history/support are mutually exclusive and reject diagnostic options and fail-on; support also rejects format/lang. Option abbreviations and extra positional arguments are rejected.

## Interpretation and exit codes

| State | Meaning |
| --- | --- |
| pass | This limited check passes now or visibility was observed |
| warn | Missing PATH entry, duplicate clues or limited scanning |
| error | Invalid supported syntax/root structure, or missing/incompatible Node for an identified JS entry |
| unknown | Insufficient layout/version/permission/encoding evidence, not a confirmed fault |
| skipped | Optional item absent, disabled or outside scope |

Completed diagnosis exits 1 when any selected fail-on state occurs, otherwise 0. Default selects only error. Invalid arguments/input, incomplete diagnosis or export always exit 2; interruption exits 130. Completed comparison/history/support exit 0 regardless of imported error counts. Reports show exit_policy selections, triggered states and meaning; selecting unknown does not make it a confirmed fault.

Diagnosis remains schema 1.0 with additive CLI exit_policy metadata. Import modes accept v0.1/v0.2/v0.3/v0.4 schema-1.0 diagnosis input and reject comparison/history/support/validation/support_verification derivatives. Only known IDs, states, numeric versions, installation-group counts and scan limits survive. Duplicate keys/IDs, invalid states/schema, oversized or linked input are rejected. Each file is capped at 2 MiB, 16 levels and 20,000 nodes; history allows 20 files. Arbitrary source text never reaches derivative output.

## Privacy and scope

No authentication, session, chat or .claude.json files are read. Only fixed configuration syntax is checked (UTF-8, at most 1 MiB); keys/values, arbitrary exceptions, raw process output and private paths are not exported. Original path mappings are not saved; opaque references cannot identify a machine across reports. Configuration, executables, Node, packages and report inputs reject links/junctions/reparse points root to leaf before any descendant access. Hard links and hostile concurrent replacement remain outside the model.

Only recognized targets are queried, never shell wrappers; binary recognition is not publisher-signature validation. Probes use temporary HOME and restricted environments, with Windows Job Object process-tree cleanup. Installed third-party programs are not a complete security sandbox and may bypass proxies. The doctor itself does not connect to the network. Valid configuration syntax does not establish authentication/API/service availability or complete tool operation. WSL internals remain unchecked and WSL is not started by default.

[Privacy](docs/privacy.md) · [Official sources and detection limits](docs/rules.md) · [Comparison](docs/comparison.md) · [v0.3 contract](docs/v03-contract.md)

## Examples and validation

```powershell
python -B .\examples\make_v04_demo.py .\reports\v04-demo-new
python -B .\tests\run_tests.py --evidence .\evidence\review-v04-tests.json
python -B .\tests\package_check.py .\evidence\review-v04-package.json
```

The first three inputs are explicitly authored synthetic observations, not real-host diagnoses. Examples: [English history](examples/v04/history-en/history.en.html), [中文趋势](examples/v04/history-zh/history.zh.html), [20-run history](examples/v04/history20-en/history.en.html). Build checks require complete Python with venv/ensurepip and an empty artifact directory; dependencies stay in temporary build environments. [HANDOFF](HANDOFF.md) identifies current local results, display evidence and untested scope.

All v0.1/v0.2/v0.3 materials, old tests.json/build-install.json and old manifests are historical. Fourth-version independent review, hosted Windows/Python 3.11/3.14 CI and publication require separate verification.

[MIT](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md)

Current v0.4 status is in [HANDOFF](HANDOFF.md). Existing evidence not identified as v04, including v0.1/v0.2/v0.3 results, is historical. Required local permission tests, independent review, hosted CI and publication are separate v0.4 gates.
