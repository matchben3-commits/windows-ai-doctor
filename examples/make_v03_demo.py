"""Public synthetic samples; all paths/configs used by diagnosis are temporary."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_ai_doctor import __version__
from windows_ai_doctor.compare import STATES


def main():
    dest = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "examples/v03").absolute()
    dest.mkdir(parents=True, exist_ok=True)
    records = []
    # Explicitly authored synthetic observations, not claims about a real host.
    for n, status in enumerate(("error", "unknown", "pass"), 1):
        findings = [{"id": id, "target": "codex" if id.startswith("codex") else "system", "status": s,
                     "summary": "合成示例 / Synthetic example", "evidence": evidence,
                     "recommendation": "请人工核对范围 / Confirm scope manually", "recheck": "仅为合成数据 / Synthetic data only"}
                    for id, s, evidence in (("codex.config.user", status, {}),
                                           ("codex.version", "pass", {"version": f"1.2.{n}"}),
                                           ("codex.path", "warn" if n == 2 else "pass", {"installation_groups": 1, "scan_limited": n == 2}),
                                           ("scope.unchecked", "skipped", {}))]
        doc = {"schema_version": "1.0", "report_type": "diagnosis", "doctor_version": __version__,
               "generated_at": "synthetic input; order is given by the command line", "language": "zh",
               "summary": {s: sum(f["status"] == s for f in findings) for s in STATES},
               "findings": findings, "priorities": []}
        (dest / f"run{n}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def run(label, flags, expected=0, env=None):
        p = subprocess.run([sys.executable, "-B", str(ROOT / "doctor.py"), *map(str, flags)],
                           env=env, capture_output=True, timeout=30, cwd=dest)
        records.append({"step": label, "exit_code": p.returncode, "expected_exit_code": expected, "synthetic": True})
        if p.returncode != expected:
            raise RuntimeError("demo_step_failed")
    for lang in ("zh", "en"):
        run("history_" + lang, ["--history", *(dest / f"run{n}.json" for n in (1, 2, 3)), "--lang", lang, "--format", "all", "--output-dir", dest / ("history-" + lang)])
        run("history_20_" + lang, ["--history", *([dest / "run1.json", dest / "run2.json", dest / "run3.json"] * 6 + [dest / "run2.json", dest / "run3.json"]),
                                   "--lang", lang, "--format", "html", "--output-dir", dest / ("history-20-" + lang)])
    run("support", ["--support", dest / "run1.json", "--output-dir", dest / "support"])
    with tempfile.TemporaryDirectory(prefix="wad-v03-demo-") as temp:
        home = Path(temp)
        env = {k: v for k, v in os.environ.items() if k.upper() in ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE")}
        env.update(PATH="", HOME=str(home), USERPROFILE=str(home), PYTHONDONTWRITEBYTECODE="1")
        for lang in ("zh", "en"):
            run("fail_on_unknown_" + lang, ["--home", home, "--no-version", "--fail-on", "unknown", "--format", "all", "--lang", lang,
                                           "--output-dir", dest / ("policy-" + lang)], 1, env)
    (dest / "runs.json").write_text(json.dumps({"exit_code": 0, "synthetic": True, "steps": records}, indent=2) + "\n", encoding="utf-8")
    print("v0.3 synthetic examples: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
