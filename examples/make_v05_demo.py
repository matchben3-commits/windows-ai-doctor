"""Generate authored synthetic v0.5 examples; no live machine diagnosis."""
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "examples/v05").absolute()
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        raise ValueError("new_example_directory_required")
    runs = []

    def run(label, *args, expect=0):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "doctor.py"), *map(str, args)],
                                capture_output=True, cwd=dest, timeout=30)
        runs.append({"step": label, "exit_code": result.returncode, "expected_exit_code": expect})
        if result.returncode != expect:
            raise RuntimeError("synthetic_example_failed:" + label)

    old = {
        "schema_version": "1.0",
        "report_type": "diagnosis",
        "findings": [
            {"id": "codex.version", "status": "warn", "evidence": {"version": "1.2.3"}},
            {"id": "claude.path", "status": "warn",
             "evidence": {"installation_groups": 0, "scan_limited": False}},
            {"id": "wsl.internal", "status": "skipped", "evidence": {}},
        ],
    }
    new = {
        "schema_version": "1.0",
        "report_type": "diagnosis",
        "findings": [
            {"id": "codex.version", "status": "pass", "evidence": {"version": "1.2.3"}},
            {"id": "claude.path", "status": "pass",
             "evidence": {"installation_groups": 0, "scan_limited": False}},
            {"id": "system.platform", "status": "unknown", "evidence": {}},
        ],
    }
    (dest / "old.json").write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")
    (dest / "new.json").write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")

    for lang in ("zh", "en"):
        run("catalog_" + lang, "--catalog", "--format", "both", "--lang", lang,
            "--output-dir", dest / ("catalog-" + lang))
        run("catalog_subset_" + lang, "--catalog", "system.platform", "codex.path",
            "--format", "json", "--lang", lang, "--output-dir", dest / ("catalog-subset-" + lang))
        run("compare_csv_" + lang, "--compare", dest / "old.json", dest / "new.json",
            "--format", "csv", "--lang", lang, "--output-dir", dest / ("compare-csv-" + lang))
    run("schema", "--schema", "--output-dir", dest / "schema")
    (dest / "runs.json").write_text(
        json.dumps({"synthetic": True, "exit_code": 0, "steps": runs}, indent=2) + "\n",
        encoding="utf-8")
    print("v0.5 synthetic examples: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
