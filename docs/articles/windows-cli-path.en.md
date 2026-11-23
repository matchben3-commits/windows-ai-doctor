# Claude or Codex is installed, but Windows cannot find it. Which command is your terminal choosing?

[中文](windows-cli-path.zh.md)

An installer finishes successfully. One PowerShell window can run `claude`, while an editor's terminal cannot. Before changing the installation again, check **which directories the failing process can see and which command its shell selects**.

This walkthrough starts with commands you can use independently, then shows how our open-source project, Windows AI Doctor, can save a report and compare observations after a manual change. The before-and-after scenario is **SIMULATED**, not a customer incident or evidence that a real machine was repaired.

## Start inside the terminal that fails

Run this in that PowerShell window:

```powershell
Get-Command claude,codex -All -ErrorAction SilentlyContinue |
    Format-Table CommandType,Name,Source -AutoSize
where.exe claude
where.exe codex
```

If you use only one tool, an absent result for the other is expected. The `.exe` matters: `where` can be a PowerShell alias. `Get-Command -All` shows matching commands in precedence order, including aliases and functions. [Microsoft's command lookup documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/get-command?view=powershell-7.5) and [command precedence guide](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_command_precedence?view=powershell-7.5)

| Observation | What to investigate |
| --- | --- |
| Neither lookup finds an entry | Whether the intended installation directory is in this process's PATH; the tool may still exist elsewhere |
| Entries appear in different directories | Their origins and selection order; file count alone does not establish duplicate installations |
| An alias or function appears | PowerShell's local overrides, which a PATH-only inspection cannot settle |
| A standalone terminal works but an editor's terminal fails | Run the same queries in both and compare the environments they actually use |

One npm installation can provide several launchers, such as `.cmd` and `.ps1`. Multiple filenames are not automatically multiple installations. Even separate installation sources need investigation before deciding which, if any, to remove.

## Check the environment the process actually has

Inspect these two values locally:

```powershell
$env:PATH -split ';'
$env:PATHEXT
```

Child processes inherit their parent's environment. An editor that was already running when the persistent PATH changed may still give a newly opened integrated terminal its earlier environment. Fully quit and reopen the editor when refreshing that environment, then repeat the lookup in its terminal. [Microsoft's environment variable documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-7.5)

For a manual change, first identify the official installation you intend to keep and its entry directory. Check that directory in Windows' user environment variable settings, reopen the relevant application, and rerun the lookup. If an entry belongs to a confirmed obsolete installation, follow the original installation method's official removal instructions. Change one thing at a time so the next observation is useful.

If the failing shell is inside WSL, investigate inside that Linux environment. Finding a Windows WSL launcher does not establish that a CLI is installed or healthy within a distribution.

## Save the observations for comparison or help

[Windows AI Doctor](https://github.com/matchben3-commits/windows-ai-doctor) is a project we help develop. It collects limited local clues, adds manual guidance, and exports Chinese or English reports.

With a standard Python 3.11+ distribution that includes `venv` and `pip`, create a separate environment and install the pinned v0.6.0 wheel from GitHub Release. Installation needs internet access; the diagnostic command below uses `--no-version` and does not launch Claude, Codex, or Node. This installs from a Release URL, rather than PyPI. Checksums are on the [v0.6.0 release page](https://github.com/matchben3-commits/windows-ai-doctor/releases/tag/v0.6.0).

```powershell
python -m venv .wad-venv
.\.wad-venv\Scripts\python.exe -m pip install --no-deps https://github.com/matchben3-commits/windows-ai-doctor/releases/download/v0.6.0/windows_ai_doctor-0.6.0-py3-none-any.whl
.\.wad-venv\Scripts\python.exe -m windows_ai_doctor --no-version --lang en --format all --output-dir .\reports\before
```

Open `reports\before\report.en.html` locally, or read `report.en.md`. Choose a new output directory each time; existing report files are not overwritten. Add `--tools claude` to the diagnostic command if you only want to inspect Claude.

If your interpreter reports that `venv` is missing, it may be a minimal distribution. Use a standard Python installation, or download the source ZIP from that Release. From its extracted directory, substitute `python .\doctor.py` for `.\.wad-venv\Scripts\python.exe -m windows_ai_doctor` in the commands below; keep the diagnostic arguments.

Start with `claude.path` or `codex.path`: installation-group counts, PATH candidates, and whether inspection was limited. Reports replace paths with references such as `<PATH:1>`; use the local lookup commands to inspect actual paths. A reference has no directory identity across separate reports.

**SIMULATED: these scenarios illustrate the PATH check's scope.**

| Scenario | `claude.path` | Installation groups | What it establishes |
| --- | --- | --- | --- |
| No entry in the inspected PATH | `warn` | 0 | No entry was selected within that inspection scope |
| One inspectable entry group | `pass` | 1 | This PATH check passes; the CLI still needs verification |
| Two separate entry groups | `warn` | 2 | A person should confirm which entry ought to take effect |

This is not a whole-machine health rating. `--no-version` skips version queries. `unknown` means the tool could not determine a result; `skipped` means it did not perform that check. Limited scans need separate investigation. The PATH model also excludes PowerShell aliases, functions, and execution policy.

## Rerun after the manual change

Keep the first JSON report. In the reopened terminal, use it as a baseline:

```powershell
.\.wad-venv\Scripts\python.exe -m windows_ai_doctor --no-version --lang en --baseline .\reports\before\report.en.json --fail-on regression --format all --output-dir .\reports\after
```

Use the same machine, tool selection, and inspection scope. The new report compares a limited set of observations. `--fail-on regression` returns 1 for `pass → warn`, `pass → error`, or `warn → error` when neither scan is limited. Exit 0 means the selected exit condition was not met; existing warnings may remain. Argument or export errors return 2.

In the simulated table, moving from zero groups to one can turn the PATH finding from `warn` to `pass`. It does not establish that authentication, network access, or an actual task works. Launch the intended CLI in the originally failing terminal and retry that task. Once Claude can launch, its official `claude doctor` offers installation and settings diagnostics. [Claude's installation verification instructions](https://code.claude.com/docs/en/setup#verify-your-installation)

## Feedback that helps improve the checks

Reports are not uploaded automatically. They omit configuration values and raw command output; review a report before sharing it. The diagnostic tool does not install, uninstall, or repair software. Removing `--no-version` allows recognized version entry points to run; this is not an enforced network sandbox for third-party executables.

If you try it, a useful [issue](https://github.com/matchben3-commits/windows-ai-doctor/issues) describes the failing terminal, expected behavior, relevant check IDs and states, and what changed after your manual step. You do not need to post your full environment or personal directories. Cases where the report finds an entry but the command still fails are particularly useful: they show us where the current checks fall short.

Project: [matchben3-commits/windows-ai-doctor](https://github.com/matchben3-commits/windows-ai-doctor). Star it if you want to find it again for a future troubleshooting session.

---

Applies to Windows AI Doctor v0.6.0. Official reference pages checked on November 22, 2026, China time. All illustrated scenarios are SIMULATED; no customer testimonials or success rates are claimed.
