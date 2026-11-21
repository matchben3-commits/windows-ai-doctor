"""Generate authored synthetic v0.4 examples; no live machine diagnosis."""
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "examples/v04").absolute()
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        raise ValueError("new_example_directory_required")
    runs = []
    for n, state in enumerate(("error", "unknown", "pass"), 1):
        findings = [{"id": "codex.version", "status": state, "evidence": {"version": f"1.2.{n}"}},
                    {"id": "codex.path", "status": "warn" if n == 2 else "pass",
                     "evidence": {"installation_groups": n, "scan_limited": n == 2}},
                    {"id": "scope.unchecked", "status": "skipped", "evidence": {}}]
        if n != 2:
            findings.append({"id": "codex.config.user", "status": state, "evidence": {}})
        report = {"schema_version": "1.0", "report_type": "diagnosis", "findings": findings}
        (dest / f"run{n}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    def run(label, *args):
        result = subprocess.run([sys.executable, "-B", ROOT / "doctor.py", *map(str, args)],
                                capture_output=True, cwd=dest, timeout=30)
        runs.append({"step": label, "exit_code": result.returncode, "expected_exit_code": 0})
        if result.returncode:
            raise RuntimeError("synthetic_example_failed")
    a, b, c = (dest / f"run{n}.json" for n in (1, 2, 3))
    run("support", "--support", a, "--output-dir", dest / "support")
    for lang in ("zh", "en"):
        run("validation_" + lang, "--validate", a, "--lang", lang, "--output-dir", dest / ("validation-" + lang))
        run("verification_" + lang, "--verify-support", dest / "support/support-bundle.zip", "--lang", lang,
            "--output-dir", dest / ("verification-" + lang))
        run("csv_" + lang, "--history", a, b, c, "--format", "csv", "--lang", lang, "--output-dir", dest / ("csv-" + lang))
        run("history_" + lang, "--history", a, b, c, "--format", "all", "--lang", lang, "--output-dir", dest / ("history-" + lang))
        run("history20_" + lang, "--history", *([a, b, c] * 6 + [b, c]), "--format", "html", "--lang", lang,
            "--output-dir", dest / ("history20-" + lang))
    (dest / "runs.json").write_text(json.dumps({"synthetic": True, "exit_code": 0, "steps": runs}, indent=2) + "\n", encoding="utf-8")
    print("v0.4 synthetic examples: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
