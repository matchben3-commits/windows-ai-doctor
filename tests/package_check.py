"""Build wheel through sdist; install both in clean venvs, check and uninstall.

Requires a complete Python with venv/ensurepip. Build dependencies are fetched
into temporary task directories only. No package is published.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = Path(sys.argv[1]).absolute() if len(sys.argv) == 2 else ROOT / "evidence/build-install.json"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    if list(dist.iterdir()):
        raise ValueError("dist_must_be_empty")
    scratch = ROOT / ".task-build"
    scratch.mkdir(exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="packaging-", dir=scratch) as temp:
        task = Path(temp)
        env = dict(os.environ)
        env.update(PIP_CACHE_DIR=str(task / "cache"), PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONDONTWRITEBYTECODE="1")
        def run(label, argv, *, cwd=task, expected=0, environment=env):
            result = subprocess.run([str(v) for v in argv], cwd=cwd, env=environment,
                                    capture_output=True, timeout=240)
            records.append({"step": label, "exit_code": result.returncode, "expected_exit_code": expected})
            if result.returncode != expected:
                raise RuntimeError("packaging_step_failed")
            print(label + ": PASS", flush=True)
            return result
        def create(name):
            folder = task / name
            venv.EnvBuilder(with_pip=True).create(folder)
            return folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        builder = create("builder")
        run("isolated_build_dependencies", [builder, "-m", "pip", "install", "build", "setuptools>=68", "wheel"])
        wheelhouse = task / "wheelhouse"
        run("cache_sdist_build_dependencies", [builder, "-m", "pip", "download", "--dest", wheelhouse, "setuptools>=68", "wheel"])
        tree = task / "source"
        shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(".task-build", "dist", "build", "*.egg-info", "__pycache__", ".git", "evidence"))
        # The default builds an sdist then builds the wheel from that sdist.
        run("build_sdist_and_wheel", [builder, "-m", "build", "--no-isolation", "--outdir", dist, tree])
        wheels, sources = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sources) != 1:
            raise ValueError("artifact_count")
        for kind, artifact in (("wheel", wheels[0]), ("sdist", sources[0])):
            python = create("install-" + kind)
            run(kind + "_venv_isolated", [python, "-I", "-c", "import sys; assert sys.prefix != sys.base_prefix"])
            if kind == "sdist":
                run("sdist_offline_build_dependencies", [python, "-m", "pip", "install", "--no-index", "--find-links", wheelhouse, "setuptools>=68", "wheel"])
            run(kind + "_install", [python, "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", artifact])
            run(kind + "_installed_import", [python, "-I", "-c", "import sys, pathlib, windows_ai_doctor; assert pathlib.Path(windows_ai_doctor.__file__).is_relative_to(sys.prefix); assert windows_ai_doctor.__version__ == '0.2.0'"])
            entry = python.parent / ("windows-ai-doctor.exe" if os.name == "nt" else "windows-ai-doctor")
            version = run(kind + "_console_entry", [entry, "--version"])
            if version.stdout.decode("utf-8").strip() != "0.2.0":
                raise ValueError("wrong_version")
            home = task / ("home-" + kind)
            home.mkdir()
            clean = {k: v for k, v in env.items() if k.upper() in ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR")}
            clean.update(PATH="", USERPROFILE=str(home), HOME=str(home))
            for lang in ("zh", "en"):
                output = task / (kind + lang)
                run(kind + "_" + lang + "_all", [entry, "--home", home, "--no-version", "--format", "all", "--lang", lang, "--output-dir", output], environment=clean)
                doc = json.loads((output / ("report." + lang + ".json")).read_text(encoding="utf-8"))
                if doc["doctor_version"] != "0.2.0" or len(list(output.iterdir())) != 3:
                    raise ValueError("installed_export")
                if lang == "zh" and "手动复查" not in (output / "report.zh.html").read_text(encoding="utf-8"):
                    raise ValueError("chinese_export")
            run(kind + "_compare", [entry, "--compare", task / (kind + "zh/report.zh.json"), task / (kind + "en/report.en.json"), "--format", "all", "--output-dir", task / (kind + "comparison")], environment=clean)
            run(kind + "_uninstall", [python, "-m", "pip", "uninstall", "--yes", "windows-ai-doctor"])
            run(kind + "_import_removed", [python, "-I", "-c", "import importlib.util; assert importlib.util.find_spec('windows_ai_doctor') is None"])
            if entry.exists():
                raise ValueError("console_entry_not_removed")
        versions = run("build_dependency_versions", [builder, "-c", "import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ('build','setuptools','wheel')}))"])
        record = {"generated_at": datetime.now(timezone.utc).isoformat(), "python": sys.version.split()[0],
                  "exit_code": 0, "build": "sdist then wheel from sdist", "clean_working_directory": True,
                  "dependencies": json.loads(versions.stdout), "steps": records,
                  "artifacts": [{"file": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [*wheels, *sources]],
                  "system_python_changed": False, "temporary_venvs_removed": True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("build_install=PASS; both distributions installed and uninstalled", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print("Packaging validation incomplete; exception details withheld.", file=sys.stderr)
        raise SystemExit(2)
