# Windows AI Doctor

[中文](README.md) · v0.2.0 · Python 3.11+ · Windows first · standard library runtime

Inspect Codex CLI and Claude Code CLI PATH entries, duplicate installation clues, versions, launcher-specific dependencies, configuration syntax and Windows/WSL visibility. Produce English or Chinese Markdown/JSON/offline HTML reports, compare two saved results, and get evidence-based manual troubleshooting steps with opaque path references.

This is limited-scope v0.2 development. It diagnoses without installing, upgrading, repairing, logging in or calling a model API.

## New in v0.2

```powershell
python .\doctor.py --lang en --format all --output-dir .\reports\before
python .\doctor.py --format html --output-dir .\reports\html-only
python .\doctor.py --compare .\reports\before\report.en.json .\reports\after\report.en.json --lang en --format all --output-dir .\reports\comparison
```

Generate the `after` report separately after your manual changes, using the same diagnostic scope. HTML is one local file with inline styles, no script and no external resource dependencies; open it manually. `both` still means MD+JSON, while `all` means MD+JSON+HTML. Without a directory, both/all print Markdown; a single format prints that format.

Comparison only reads its two inputs. It never runs diagnostics or follows embedded paths/URLs. Output names are `comparison.en.md/json/html`. Completed comparison exits 0 regardless of errors in the old report; invalid arguments/input/export exit 2, interruption 130. Comparison conflicts with `--tools`, `--home`, `--project`, `--timeout`, `--no-version`, `--wsl-list`; option abbreviations are disabled.

Schema 1.0 diagnosis reports from v0.1 and v0.2 are accepted. Only known check IDs, states, numeric three-part versions, installation-group counts and scan-limit flags are compared. Time, language and path references are ignored. Opaque path numbers have no identity across runs; confirm matching environments yourself. Unknown, skipped, removed or restricted coverage never establish a fix; a pass only means this check passes now. Duplicate keys/IDs, unknown IDs/states/schema, linked files and excessive input are rejected. Arbitrary imported text is discarded. See the [comparison contract](docs/comparison.md).

Diagnosis lists errors, warnings and unknown checks first, then gives each check an observation, basis, fixed manual steps, official guidance and limitations. Suggested commands and links are never executed automatically.

## Run from source

No pip installation, administrator access or API key is needed:

```powershell
python .\doctor.py --lang en --output-dir .\reports\first
```

This writes `report.en.md` and `report.en.json`. Existing reports are preserved; use a new output directory on each run. Without an output directory, the default/`both` prints Markdown; `--format json` prints JSON alone for pipelines.

From a clean directory, replace the absolute script location as appropriate:

```powershell
python "D:\Projects\windows-ai-doctor\doctor.py" --lang en --output-dir ".\doctor-reports"
```

If `python` is unavailable, use your installed Python 3.11+ executable's absolute path. The project location above is an example; replace it with your extraction folder.

## Options

```powershell
python .\doctor.py --help
python .\doctor.py --tools codex --lang en --format json
python .\doctor.py --no-version --output-dir .\reports\files-only
python .\doctor.py --project "D:\Project with spaces" --output-dir .\reports\project
python .\doctor.py --timeout 2 --wsl-list --output-dir .\reports\wsl-list
```

- `--tools codex claude`: both by default; either can be selected.
- `--lang zh|en`, `--format both|md|json|html|all`: output language and format; both is MD+JSON and all is all three.
- `--home`: diagnostic home override. Existing `CODEX_HOME` / `CLAUDE_CONFIG_DIR` environment variables take priority over the default `.codex` / `.claude` directory. Use absolute local paths; unsupported overrides become unknown rather than silently falling back.
- `--project`: inspect only the explicit root's `.codex/config.toml`, `.claude/settings.json`, `.claude/settings.local.json`. No ancestor discovery or merged configuration evaluation.
- `--timeout`: 0.1–30 seconds per probe, default 3. At most two version probes per tool, including Node when needed. Capture is bounded at 16 KiB plus one overflow-detection byte. Other checks continue after failure.
- `--no-version`: execute no Codex, Claude or Node commands. Basic file/PATH/WSL registration inspection remains available without network. WSL execution is disabled by default.
- `--wsl-list`: explicitly permit the system `wsl.exe --list --running --quiet`, reporting counts only. Never launch a distribution or inspect its files. This option still runs the list query when combined with `--no-version`; omit it for no external commands.

Recognized native programs or npm entry files are queried directly, never through a `.cmd` / `.ps1` shell string. Unknown wrappers remain unknown. Trust the installed files on your PATH before probing; layout recognition does not verify publisher signatures.

npm recognition requires a complete known `cmd-shim 8.0.0` wrapper (Node with no extra arguments, or a direct native target). A path in a comment, truncated wrapper or added command does not permit probing the package. Other shim versions may remain unknown. See the [template attribution and license](THIRD_PARTY_NOTICES.md).

## Results and exit codes

| Status | Meaning |
| --- | --- |
| `pass` | This limited check passed or visibility was observed |
| `warn` | No callable PATH entry, multiple installation candidates, or limited scanning |
| `error` | Invalid supported syntax/root structure, or missing/incompatible Node for an identified JS entry |
| `unknown` | Unsupported layout, failed version query, permission/encoding limit, or insufficient evidence |
| `skipped` | Optional file absent, check disabled, or out of scope |

Exit `0`: completed without errors, possibly with unknown/warning results. Exit `1`: completed with errors. Exit `2`: invalid arguments or incomplete diagnosis/export. Exit `130`: interrupted. A version timeout is unknown and does not itself cause exit `1`. Inspect `summary` and stable finding `id` values.

Opaque `<PATH:1>` references correlate entries within one report; the original mapping is not persisted. Command names and entry order help local review. To inspect actual paths in the original terminal, manually run `Get-Command codex,claude -All`, `where.exe codex`, and `where.exe claude`. Candidates are predictions from PATH/PATHEXT only: CWD search, aliases, functions and shell policy are not modeled.

Multiple entries do not prove a conflict; recognized npm wrappers for one installation share a group. Missing PATH entries do not prove a tool is absent from the machine. Valid syntax does not establish authentication, API availability or valid effective settings. A WSL launcher does not establish healthy WSL components; distribution internals remain unchecked.

`path_access=blocked` and `existence_verified=false` mean an ancestor check stopped before the candidate's existence could be confirmed. Its PATH position is retained to avoid bypassing a possibly earlier command; installation and version remain unknown and it is not run. A blocked Node path is unknown, while a confirmed missing runtime is a dependency error.

## Privacy and offline operation

No authentication files, `.claude.json`, session history or conversation text are read. Configuration values, private paths, arbitrary exception messages and raw process output are not exported. Only fixed configuration filenames are read, with UTF-8, JSON object/TOML syntax, a 1 MiB cap and link/reparse rejection. Windows scanning excludes UNC, mapped network drives and removable media.

Configuration, commands, package metadata/targets and Node paths are checked from root to leaf before existence, header or content checks. Junctions, symlinks and other reparse points stop inspection before descendant metadata or content is accessed. Paths containing `..` or Windows alternate data streams are also rejected. Hard links and concurrent hostile replacement are outside this model.

Version probes use temporary HOME/config/cache locations and an OS environment allowlist. Claude updater/telemetry controls and an unavailable loopback proxy are set. Windows process trees use a kill-on-close Job; containment failure prevents execution. The doctor opens no network connections. Installed third-party programs are not a complete security sandbox and may ignore proxy settings; use `--no-version` for basic inspection without their execution. See [privacy](docs/privacy.md).

## Reproduce the demo and tests

```powershell
python .\examples\make_demo.py .\reports\demo-new
python .\tests\run_tests.py --evidence .\evidence\tests-rerun.json
python .\tests\offline_check.py --format json
```

The synthetic demo includes an invalid configuration, a broken npm wrapper and a real temporary Windows junction. Before runs exit `1`; after correcting only the temporary synthetic config, after runs and comparisons exit `0`. The successful generator exits `0` and cleans temporary fixtures. Current examples: [English diagnosis](examples/v02-complete/en/report.en.html), [中文诊断](examples/v02-complete/zh/report.zh.html), [English comparison](examples/v02-complete/comparison/en/comparison.en.html), [中文对比](examples/v02-complete/comparison/zh/comparison.zh.html). These are synthetic observations, not host repair results.

The test runner uses the standard library. Live JS fixtures borrow existing Node; Windows native fixtures borrow the existing .NET Framework C# compiler. Neither is installed by the tests. Missing optional conditions are reported as skips. [Validation](docs/validation.md) and [current machine evidence](evidence/v02-tests.json) distinguish real host results from synthetic scenarios. The offline audit check denies Python network operations; it does not disconnect host networking.

## Scope

[Rules and official sources](docs/rules.md) · [Privacy](docs/privacy.md) · [Validation and limitations](docs/validation.md) · [Release review](docs/release-review-v0.2.md)

v0.2 does not validate full configuration schemas, profiles, ancestor layers, managed policy, authentication, service availability, actual agent tasks, IDE/desktop installations, WSL internals, all package-manager shims or publisher signatures. Historical issues are not universal fault rules. Upstream changes can require rule updates.

Licensed under [MIT](LICENSE); npm wrapper templates retain their [ISC notice](THIRD_PARTY_NOTICES.md). This iteration actually builds an sdist and a wheel from it, installs each in a clean temporary venv, exercises the console entry, Chinese/English exports and comparison, then uninstalls it. See [build/install evidence](evidence/build-install.json). Install the wheel in your own venv using `python -m pip install <wheel-file>` or run directly from source. Build dependencies are temporary build/setuptools/wheel packages; runtime uses only the standard library.

v0.2 ordinary suite: 56 cases, 54 passes, 2 skips, no failures/errors, exit 0. A separate user-authorized file-link supplement passed both cases with no skips, exit 0. This is not a single 56-pass full suite. See [handoff](HANDOFF.md), [validation](docs/validation.md) and [actual browser display checks](docs/html-validation.md). The 2026-11-20 independent review again recorded 54 passes and 2 skips, plus a separate 13-case audit with all cases passing. Both file-link cases still skipped for permissions today; the prior same-source supplement keeps its original date. Hosted Windows/Python 3.11 and 3.14 results and publication status are linked from the [v0.2 review](docs/release-review-v0.2.md) and [releases](https://github.com/matchben3-commits/windows-ai-doctor/releases). The [v0.1 review](docs/release-review.md) remains historical evidence.
