"""Executable v0.7 Release-wheel compatibility gate (standard library only).

Creates a clean venv, installs the specified verified wheel without network,
generates real legacy reports without executing CLI/Node, then exercises the
candidate readers. A separate authored fixture compares identical observations
through the real old/new CLI and renderers. No synthetic result proves a host
fault, and this gate alone does not accept the new snapshot functionality.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/v10_compat_fixture.py"
WHEEL_SHA256 = "6a030e06696febe5747ecdc22223ec761db896e04ce4269f444089ad4013d0b6"
STATES = ("pass", "warn", "error", "unknown", "skipped")
IDS = """claude.config.local claude.config.project claude.config.user
claude.dependency claude.install claude.path claude.version
codex.config.project codex.config.user codex.dependency codex.install
codex.path codex.version scope.unchecked system.platform wsl.internal
wsl.inventory wsl.launcher wsl.running""".split()
CSV_COLUMNS = "sequence,check_id,target,status,version,installation_groups,scan_limited,baseline_change,baseline_status,baseline_regression".split(",")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def authored():
    items = []
    for index, check_id in enumerate(IDS):
        evidence = {}
        if check_id.endswith((".version", ".dependency")):
            evidence["version"] = "1.2.3"
        if check_id.endswith(".path"):
            evidence.update(installation_groups=2, scan_limited=False)
        items.append({"id": check_id, "target": check_id.split(".")[0],
                      "status": STATES[index % len(STATES)], "evidence": evidence,
                      "summary": "SIMULATED / 合成观察", "recommendation": "Review scope / 核对范围",
                      "recheck": "Separate real diagnosis / 另行实测"})
    by_id = {item["id"]: item for item in items}
    by_id["claude.path"]["status"] = "error"
    by_id["codex.version"]["status"] = "warn"
    by_id["codex.version"]["evidence"]["version"] = "1.2.4"
    by_id["codex.path"].update(status="unknown", evidence={"installation_groups": 1, "scan_limited": True})
    document = {"schema_version": "1.0", "report_type": "diagnosis",
                "doctor_version": "fixture", "generated_at": "2000-01-01T00:00:00+00:00",
                "language": "en", "findings": items,
                "summary": {state: sum(f["status"] == state for f in items) for state in STATES},
                "privacy": {"synthetic": True}, "priorities": []}
    baseline = copy.deepcopy(document)
    baseline.pop("report_type")  # Published reader's older accepted shape.
    baseline["findings"] = [f for f in baseline["findings"] if f["id"] != "claude.path"]
    for item in baseline["findings"]:
        if item["id"] == "codex.version":
            item.update(status="pass", evidence={"version": "1.2.3"})
    # Imported summary is deliberately stale; readers must recompute it.
    baseline["summary"] = {state: 999 for state in STATES}
    return document, baseline


def old_fields_equal(old, new, path="$", allowed=None):
    """Check every legacy field, allowing only additive object keys."""
    allowed = allowed or set()
    if path in allowed:
        return
    if isinstance(old, dict):
        assert isinstance(new, dict), path
        for key in old:
            assert key in new, path + "." + key
            old_fields_equal(old[key], new[key], path + "." + key, allowed)
    elif isinstance(old, list):
        assert isinstance(new, list) and len(old) == len(new), path
        for index, value in enumerate(old):
            old_fields_equal(value, new[index], f"{path}[{index}]", allowed)
    else:
        assert type(old) is type(new) and old == new, path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == WHEEL_SHA256
    dest = args.evidence.absolute()
    dest.mkdir(parents=True, exist_ok=False)
    steps, checks, comparisons = [], [], []
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}

    def run(label, command, expected=(0,), timeout=45):
        result = subprocess.run([str(arg) for arg in command], cwd=dest, env=env,
                                capture_output=True, timeout=timeout)
        if result.stdout:
            (dest / (label + ".stdout")).write_bytes(result.stdout)
        if result.stderr:
            (dest / (label + ".stderr")).write_bytes(result.stderr)
        steps.append({"label": label, "command": [str(arg) for arg in command],
                      "exit_code": result.returncode, "expected": list(expected),
                      "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr)})
        write_json(dest / "steps.json", steps)
        assert result.returncode in expected, label + ":" + str(result.returncode)
        return result

    def check(label, passed=True):
        assert passed, label
        checks.append(label)

    venv = dest / "legacy-venv"
    run("create_venv", [sys.executable, "-m", "venv", venv], timeout=90)
    legacy_python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run("install_wheel", [legacy_python, "-I", "-m", "pip", "install", "--no-index", "--no-deps", "--no-compile", wheel])
    imported = run("installed_identity", [legacy_python, "-I", "-c",
                   "import json,windows_ai_doctor as w;print(json.dumps({'version':w.__version__,'module':w.__file__}))"])
    identity = json.loads(imported.stdout)
    check("XC-C1_installed_release_070", identity["version"] == "0.7.0" and venv in Path(identity["module"]).parents)
    old = [legacy_python, "-I", "-B", "-m", "windows_ai_doctor"]
    new = [sys.executable, "-I", "-B", ROOT / "doctor.py"]
    candidate_version = run("candidate_version", new + ["--version"]).stdout.decode().strip()
    check("candidate_is_release_100", candidate_version == "1.0.0")
    write_json(dest / "runtime.json", {"python": sys.version, "legacy": identity,
               "candidate_version": candidate_version, "wheel_sha256": WHEEL_SHA256})
    home, project = dest / "home", dest / "project"
    home.mkdir()
    project.mkdir()
    real_options = ["--no-version", "--home", home, "--project", project, "--lang", "en"]
    # These are actual observations from the release wheel; no CLI/Node is executed.
    for fmt in ("all", "csv", "sarif", "junit"):
        run("legacy_host_" + fmt, old + real_options + ["--format", fmt, "--output-dir", dest / ("legacy-host-" + fmt)], (0, 1))
    legacy_report = dest / "legacy-host-all/report.en.json"
    for fmt in ("sarif", "junit"):
        run("legacy_host_baseline_" + fmt, old + real_options + ["--baseline", legacy_report, "--format", fmt,
            "--output-dir", dest / ("legacy-host-baseline-" + fmt)], (0, 1))
    check("XC-C1_real_release_formats_exist", all((dest / folder / filename).is_file() for folder, filename in (
        ("legacy-host-all", "report.en.json"), ("legacy-host-all", "report.en.md"), ("legacy-host-all", "report.en.html"),
        ("legacy-host-csv", "report.en.csv"), ("legacy-host-sarif", "report.en.sarif"), ("legacy-host-junit", "report.en.junit.xml"))))
    # Both real release output and missing-report_type legacy shape are reader inputs.
    old_shape = json.loads(legacy_report.read_bytes())
    old_shape.pop("report_type", None)
    old_shape_path = dest / "legacy-no-report-type.json"
    write_json(old_shape_path, old_shape)
    for index, path in enumerate((legacy_report, old_shape_path)):
        for label, options in (("validate", ["--validate", path]), ("compare", ["--compare", path, legacy_report]),
                               ("history", ["--history", path, legacy_report])):
            run(f"candidate_read_{index}_{label}", new + options + ["--format", "json"])
    run("candidate_host_baseline", new + real_options + ["--baseline", legacy_report, "--format", "json"], (0, 1))
    check("XC-C2_release_and_old_shape_readers")
    current, baseline = authored()
    current_path, baseline_path = dest / "authored-current.json", dest / "authored-baseline-no-type.json"
    write_json(current_path, current)
    write_json(baseline_path, baseline)
    fixture_old = [legacy_python, "-I", "-B", FIXTURE, "--observations", current_path]
    fixture_new = [sys.executable, "-I", "-B", FIXTURE, "--source-root", ROOT, "--observations", current_path]

    def compare(label, options, kind="json", fixture=False, expected=(0,)):
        commands = (fixture_old, fixture_new) if fixture else (old, new)
        bodies = [run(label + "_" + name, command + options, expected).stdout for name, command in zip(("old", "new"), commands)]
        exemptions = []
        if kind == "json":
            objects = [json.loads(body) for body in bodies]
            exemptions = ["$.doctor_version"]
            if objects[0].get("report_type") in ("comparison", "history"):
                exemptions.append("$.generated_at")
            old_fields_equal(*objects, allowed=set(exemptions))
        elif kind == "sarif":
            exemptions = ["$.runs[0].tool.driver.version", "$.runs[0].tool.driver.semanticVersion"]
            old_fields_equal(*(json.loads(body) for body in bodies), allowed=set(exemptions))
        elif kind in ("md", "html"):
            # Only the exact displayed tool-version header may differ.
            bodies[0] = bodies[0].replace(b"v0.7.0 \xc2\xb7 schema", b"v<TOOL_VERSION> \xc2\xb7 schema")
            bodies[1] = bodies[1].replace(("v" + candidate_version + " · schema").encode(), b"v<TOOL_VERSION> \xc2\xb7 schema")
            exemptions = ["displayed_tool_version_header"]
            assert bodies[0] == bodies[1], label
        else:
            assert bodies[0] == bodies[1], label
        comparisons.append({"label": label, "equal_legacy_fields": True, "exemptions": exemptions})
        return bodies[0]

    for lang in ("zh", "en"):
        for with_baseline in (False, True):
            options = ["--lang", lang]
            if with_baseline:
                options += ["--baseline", baseline_path, "--fail-on", "new", "regression"]
            for fmt in ("json", "md", "html", "csv", "sarif", "junit"):
                body = compare(f"golden_{lang}_{int(with_baseline)}_{fmt}", options + ["--format", fmt], fmt, True, (1,))
                if fmt == "csv":
                    check(f"XC-C4_csv10_{lang}_{with_baseline}", body.startswith(b"\xef\xbb\xbf") and next(csv.reader(io.StringIO(body.decode("utf-8-sig")))) == CSV_COLUMNS)
                if fmt == "sarif":
                    document = json.loads(body)
                    check(f"XC-C4_sarif_{lang}_{with_baseline}", document["version"] == "2.1.0" and b'"locations"' not in body and b'"artifacts"' not in body)
                if fmt == "junit":
                    root = ET.fromstring(body)
                    cases = root.findall("testsuite/testcase")
                    order = ["status", "scan_limited", "baseline_change", "baseline_new", "baseline_regression"]
                    check(f"XC-C4_junit_{lang}_{with_baseline}", len(cases) == 19 and all(
                        list(case)[0].tag == "properties" and len(case[0]) > 0 and
                        [p.get("name") for p in case[0]] == sorted([p.get("name") for p in case[0]], key=order.index)
                        for case in cases))
    # Exercise all exit-policy choices and exactly compare old/new fields.
    for selected in (("error",), ("warn",), ("unknown",), ("new",), ("regression",), ("regression", "new", "warn", "error", "new")):
        body = compare("policy_" + "_".join(selected), ["--baseline", baseline_path, "--fail-on", *selected, "--format", "json"], fixture=True, expected=(1,))
        policy_doc = json.loads(body)
        check("XC-C3_policy_" + "_".join(selected), policy_doc["baseline"]["new_findings"] == ["claude.path"] and policy_doc["baseline"]["regressions"] == ["codex.version"])
    compare("policy_zero", ["--baseline", current_path, "--fail-on", "new", "regression", "--format", "json"], fixture=True)
    for name, options in (("validate", ["--validate", baseline_path]), ("compare", ["--compare", baseline_path, current_path]),
                          ("history", ["--history", baseline_path, current_path]), ("catalog", ["--catalog"])):
        body = compare("offline_" + name, options + ["--format", "json"])
        if name == "catalog":
            catalog = json.loads(body)
            check("XC-C3_catalog19", [entry["id"] for entry in catalog["checks"]] == IDS)
    for name, options in (("compare", ["--compare", baseline_path, current_path]), ("history", ["--history", baseline_path, current_path])):
        compare("offline_" + name + "_csv", options + ["--format", "csv"], "csv")
    # Preserve permissive version values, missing/false/zero distinctions and unknown additions.
    permissive = {"schema_version": "1.0", "findings": [
        {"id": "codex.version", "status": "warn", "evidence": {"version": "preview-build"}},
        {"id": "codex.path", "status": "warn", "evidence": {"installation_groups": 0, "scan_limited": False}},
        {"id": "claude.path", "status": "unknown", "evidence": {}}], "future_optional": {"value": "ignored"}}
    path = dest / "legacy-permissive.json"
    write_json(path, permissive)
    compare("permissive_validate", ["--validate", path, "--format", "json"])
    compare("permissive_compare", ["--compare", path, current_path, "--format", "json"])
    # Parameter/input errors remain 2. New-mode evidence is a separate gate.
    for index, options in enumerate((["--fail-on", "new"], ["--validate", current_path, "--no-version"], ["--history", current_path])):
        for name, command in (("old", old), ("new", new)):
            run(f"error2_{index}_{name}", command + options, (2,))
    check("XC-C3_exit0_exit1_exit2")
    write_json(dest / "semantic-diff.json", {"all_equal": True, "comparisons": comparisons})
    result = {"status": "PASS", "scope": "legacy compatibility foundation, not complete Gate C or v1 acceptance",
              "checks_passed": len(checks), "commands": len(steps), "checks": checks,
              "not_covered_by_this_gate": ["XC-C5 cross-rejection and XC-C6 no implicit key writes: tests/v10_snapshot_gate.py",
                          "exit130 actual CTRL_C_EVENT: tests/v10_interrupt.py", "full independent A/B/P/R acceptance"],
              "synthetic_comparisons": True, "real_release_reports": True, "real_cli_or_node_executed": False}
    write_json(dest / "result.json", result)
    print(json.dumps({key: result[key] for key in ("status", "checks_passed", "commands", "scope")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
