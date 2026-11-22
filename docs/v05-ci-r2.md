# v0.5.0 r2 CI correction and audit scope

The first hosted run, [44916911960](https://github.com/matchben3-commits/windows-ai-doctor/actions/runs/44916911960), passed all 138 cases on Python 3.11 and failed one case on Windows Python 3.14.10. This is a historical failed run, not approval of r2.

The unmodified case `test_compare_csv_real_child_process_only_reads_two_explicit_inputs` was reproduced on Windows with official Python 3.14.10. Its child exited 1 before comparison; the parent failed its return-code assertion. `argparse.ArgumentParser` constructs a formatter, whose `_set_color` first imports `_colorize`. The strict audit denied the attempted standard-library bytecode read. The CSV output assertions were not reached. Diagnostic probes retained the exact attempted read and traceback using synthetic data only.

The correction constructs and reuses `cli.parser()` before installing the audit, consistent with the schema and catalog tests. This boundary excludes interpreter/module startup and parser locale, terminal and color initialization. Argument parsing, both diagnosis-input loads, comparison and CSV output all remain inside the audit. This test proves the operation boundary, not a zero-read interpreter startup.

The file allowlist is unchanged: only the exact two explicit input paths, each opened once in read mode. No directory, standard-library path, module extension or other wildcard is allowed. Subprocess, socket, registry and directory-enumeration audit events still fail. `Doctor` remains forbidden. Environment access is additionally denied after bootstrap. BOM, LF and absence of the synthetic private marker remain required.

Only the test harness and documentation change; all 18 runtime modules remain byte-identical to the first candidate. The [r2 full-suite record](../evidence/v05-r2-tests.json) is a new single complete authorized run, separate from original-candidate results and focused probes. The [r2 build record](../evidence/v05-r2-package.json) covers newly built wheel and source distribution, isolated installation and uninstallation.

The original candidate ZIP, both original packages, first-run CI logs, failing reproduction and exact before-source hash are retained outside this source tree in the independently named r2 handoff directory. Independent review of r2 and new hosted Python 3.11/3.14 jobs remain required before publication. This correction does not push, tag or change a release.
