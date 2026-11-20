"""Independent dsh boundary probes; all fixtures are synthetic and temporary."""
import sys
sys.dont_write_bytecode = True
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence"
sys.path.insert(0, str(ROOT))
from windows_ai_doctor.core import Doctor
from windows_ai_doctor.discovery import is_native, bounded_read


def item(report, key):
    return next(f for f in report["findings"] if f["id"] == key)


def main():
    results = {}
    with tempfile.TemporaryDirectory(prefix="dsh-doctor-edge-") as tmp:
        temp = Path(tmp)
        home = temp / "home"
        home.mkdir()
        node = shutil.which("node")
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}}
        env.update(PATH="", PATHEXT=".EXE;.CMD", USERPROFILE=str(home), HOME=str(home))
        if node:
            folder = temp / "broken-wrapper"
            package = folder / "node_modules/@openai/codex"
            (package / "bin").mkdir(parents=True)
            (package / "package.json").write_text(json.dumps({
                "name": "@openai/codex", "bin": {"codex": "bin/codex.js"},
                "engines": {"node": ">=16"}}), encoding="utf-8")
            (package / "bin/codex.js").write_text('console.log("codex-cli 1.2.3");', encoding="utf-8")
            wrapper = folder / "codex.cmd"
            wrapper.write_text("@echo off\nrem node_modules/@openai/codex/bin/codex.js\nexit /b 7\n", encoding="utf-8")
            env["PATH"] = os.pathsep.join((str(folder), str(Path(node).parent)))
            report = Doctor(env=env, home=home, tools=("codex",)).run()
            # Fixed locally generated wrapper, no untrusted command interpolation.
            cmd = Path(os.environ["SystemRoot"]) / "System32/cmd.exe"
            actual = subprocess.run([str(cmd), "/d", "/c", str(wrapper), "--version"],
                                    capture_output=True, timeout=5, env=env)
            results["broken_wrapper"] = {
                "actual_exit_code": actual.returncode,
                "doctor_install": item(report, "codex.install")["evidence"]["kind"],
                "doctor_version_status": item(report, "codex.version")["status"],
                "doctor_version": item(report, "codex.version")["evidence"].get("version")}
        if os.name == "nt":
            import _winapi
            target = temp / "junction-target"
            target.mkdir()
            (target / "codex.exe").write_bytes(b"MZ" + b"SYNTHETIC_ONLY")
            (target / "config.toml").write_text('model = "synthetic"', encoding="utf-8")
            junction = temp / "junction"
            _winapi.CreateJunction(str(target), str(junction))
            try:
                opened = []
                original_open = Path.open
                def track(path, *args, **kwargs):
                    opened.append(str(path))
                    return original_open(path, *args, **kwargs)
                with patch.object(Path, "open", track):
                    native = is_native(junction / "codex.exe")
                config_blocked = False
                try:
                    bounded_read(junction / "config.toml")
                except ValueError:
                    config_blocked = True
                results["real_junction"] = {
                    "config_read_blocked": config_blocked,
                    "native_read_followed_junction": str(junction / "codex.exe") in opened,
                    "native_classification": native}
            finally:
                junction.rmdir()
    good = (results.get("broken_wrapper", {}).get("actual_exit_code") == 7
            and results.get("broken_wrapper", {}).get("doctor_install") == "unknown"
            and results.get("broken_wrapper", {}).get("doctor_version_status") == "unknown"
            and results.get("broken_wrapper", {}).get("doctor_version") is None
            and results.get("real_junction", {}).get("native_read_followed_junction") is False
            and results.get("real_junction", {}).get("native_classification") is False
            and results.get("real_junction", {}).get("config_read_blocked") is True)
    results.update(generated_at=datetime.now(timezone.utc).isoformat(), exit_code=0 if good else 1)
    (OUT / "v02-edges.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results))
    return results["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        print("Boundary check incomplete; details withheld.", file=sys.stderr)
        raise SystemExit(2)
