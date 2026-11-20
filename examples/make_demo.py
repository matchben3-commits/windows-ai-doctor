"""Generate reproducible reports from temporary synthetic configurations only."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    destination = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "examples" / "generated").absolute()
    with tempfile.TemporaryDirectory(prefix="ai-doctor-demo-") as temp:
        home = Path(temp) / "演示 用户"
        codex, claude, project = home / "custom codex", home / "custom claude", home / "示例 项目"
        for folder in (codex, claude, project / ".claude", project / ".codex"):
            folder.mkdir(parents=True)
        (codex / "config.toml").write_text('model = "demo-only"\n[model_providers.example]\nbase_url = "https://demo:synthetic-password@example.invalid?api_key=synthetic-key"\n', encoding="utf-8")
        (claude / "settings.json").write_text('{"env":{"ANTHROPIC_API_KEY":"synthetic-key"}}', encoding="utf-8")
        (project / ".claude/settings.local.json").write_text('{"env":', encoding="utf-8")
        (project / ".codex/config.toml").write_text('model = "demo-only"', encoding="utf-8")
        # Valid package plus an intentionally broken selected shim: its target
        # must never be queried merely because the wrapper mentions its path.
        commands = home / "示例 commands"
        package = commands / "node_modules/@openai/codex"
        (package / "bin").mkdir(parents=True)
        (package / "package.json").write_text(json.dumps({"name": "@openai/codex", "bin": {"codex": "bin/codex.js"}}), encoding="utf-8")
        (package / "bin/codex.js").write_text('console.log("codex-cli 1.2.3")', encoding="utf-8")
        (commands / ("codex.cmd" if os.name == "nt" else "codex")).write_text(
            "@echo off\nrem node_modules/@openai/codex/bin/codex.js\nexit /b 7\n", encoding="utf-8")
        command_dirs = [str(commands)]
        junction = None
        if os.name == "nt":
            import _winapi
            target = home / "synthetic target"
            target.mkdir()
            (target / "claude.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
            junction = home / "示例 junction"
            _winapi.CreateJunction(str(target), str(junction))
            command_dirs.append(str(junction))
        env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}}
        env.update({"PATH": os.pathsep.join(command_dirs), "CODEX_HOME": str(codex), "CLAUDE_CONFIG_DIR": str(claude), "USERPROFILE": str(home), "HOME": str(home)})
        runs = []
        try:
            for lang in ("zh", "en"):
                command = [sys.executable, str(ROOT / "doctor.py"), "--home", str(home), "--project", str(project),
                           "--lang", lang, "--format", "all", "--output-dir", str(destination / lang)]
                result = subprocess.run(command, env=env, cwd=temp, capture_output=True, timeout=15)
                report_path = destination / lang / f"report.{lang}.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                versions = [f for f in report["findings"] if f["id"] == "codex.version"]
                runs.append({"language": lang, "exit_code": result.returncode,
                             "expected_exit_code": 1, "synthetic": True,
                             "broken_npm_wrapper_unknown": versions[0]["status"] == "unknown",
                             "real_junction_fixture": junction is not None})
            # Repair only the temporary synthetic config, then run diagnostics
            # again. Neither report is hand-edited and no host config changes.
            (project / ".claude/settings.local.json").write_text('{}', encoding="utf-8")
            for lang in ("zh", "en"):
                after = destination / "after" / lang
                result = subprocess.run([sys.executable, str(ROOT / "doctor.py"), "--home", str(home),
                                         "--project", str(project), "--lang", lang, "--format", "all",
                                         "--output-dir", str(after)], env=env, cwd=temp, capture_output=True, timeout=15)
                comparison = subprocess.run([sys.executable, str(ROOT / "doctor.py"), "--compare",
                    str(destination / lang / f"report.{lang}.json"), str(after / f"report.{lang}.json"),
                    "--format", "all", "--lang", lang, "--output-dir", str(destination / "comparison" / lang)],
                    env=env, cwd=temp, capture_output=True, timeout=15)
                if result.returncode != 0 or comparison.returncode != 0:
                    raise ValueError("synthetic_comparison_failed")
                runs.append({"language": lang, "exit_code": result.returncode, "expected_exit_code": 0,
                             "synthetic": True, "stage": "after_synthetic_config_fix", "comparison_exit_code": comparison.returncode,
                             "broken_npm_wrapper_unknown": True, "real_junction_fixture": junction is not None})
        finally:
            if junction is not None:
                junction.rmdir()
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "runs.json").write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")
        print("Synthetic demo reports generated; expected diagnostic exit code is 1.")
        return 0 if all(r["exit_code"] == r["expected_exit_code"] and r["broken_npm_wrapper_unknown"] for r in runs) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        print("Demo generation incomplete; details withheld.", file=sys.stderr)
        raise SystemExit(2)
