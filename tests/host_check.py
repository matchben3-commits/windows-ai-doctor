"""Record fresh non-destructive host runs from a clean temporary working directory.

Compare only the allowed configuration files in memory; no values/hashes are
written. No account, authentication or history files are accessed.
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_ai_doctor.discovery import bounded_read


def snapshot():
    result = {}
    for variable, default, filename in (("CODEX_HOME", ".codex", "config.toml"),
                                        ("CLAUDE_CONFIG_DIR", ".claude", "settings.json")):
        root = Path(os.environ.get(variable) or Path.home() / default)
        try:
            result[variable] = bounded_read(root / filename)
        except (OSError, ValueError):
            result[variable] = None
    return result


def main():
    destination = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "evidence" / "host-final").absolute()
    before = snapshot()
    env_before = dict(os.environ)
    runs = []
    with tempfile.TemporaryDirectory(prefix="ai-doctor-clean-cwd-") as clean:
        for mode, script, extras in (("normal", ROOT / "doctor.py", []),
                                     ("offline-audit", ROOT / "tests/offline_check.py", [])):
            for lang in ("zh", "en"):
                output = destination / mode / lang
                command = [sys.executable, str(script), "--lang", lang,
                           "--timeout", "3", "--format", "all", *extras, "--output-dir", str(output)]
                proc = subprocess.run(command, cwd=clean, capture_output=True, timeout=30)
                path = output / f"report.{lang}.json"
                report = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
                runs.append({"mode": mode, "language": lang, "exit_code": proc.returncode,
                             "clean_cwd": True,
                             "command": "python <checkout>/" + str(script.relative_to(ROOT)).replace("\\", "/") + " --lang " + lang + " --timeout 3 --format all " + " ".join(extras) + " --output-dir <new-report-directory>",
                             "summary": report["summary"] if report else None,
                             "json_and_markdown_exist": path.is_file() and (output / f"report.{lang}.md").is_file(),
                             "html_exists": (output / f"report.{lang}.html").is_file()})
    unchanged = before == snapshot()
    env_unchanged = env_before == dict(os.environ)
    record = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "os": "Windows" if os.name == "nt" else sys.platform,
              "windows_version": list(sys.getwindowsversion()[:3]) if os.name == "nt" else None,
              "python": ".".join(map(str, sys.version_info[:3])), "python_bits": 64 if sys.maxsize > 2**32 else 32,
              "config_bytes_unchanged": unchanged, "parent_environment_unchanged": env_unchanged,
              "comparison_scope": "allowed user config.toml and settings.json only; values/hashes not exported",
              "runs": runs}
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "runs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    good = unchanged and env_unchanged and all(r["exit_code"] in (0, 1) and r["json_and_markdown_exist"] and r["html_exists"] for r in runs)
    print("host_check=" + ("PASS" if good else "FAIL") + "; config/environment comparison=" + str(unchanged and env_unchanged))
    return 0 if good else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        print("Host validation incomplete; details withheld.", file=sys.stderr)
        raise SystemExit(2)
