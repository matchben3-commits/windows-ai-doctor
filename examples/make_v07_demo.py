"""Deterministic authored v0.7 examples; no host diagnostic probes are executed.

The child fixture replaces Doctor before calling the real CLI. All observations
and report time are authored constants. This is not a live-host test result.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def finding(check_id, status, **evidence):
    return {"id": check_id, "status": status, "evidence": evidence}


def observations():
    return [finding("system.platform", "pass"),
            finding("claude.path", "error", installation_groups=0, scan_limited=False),
            finding("codex.version", "warn", version="1.2.4"),
            finding("codex.path", "unknown", installation_groups=1, scan_limited=True),
            finding("claude.version", "pass", version="2.3.4"),
            finding("scope.unchecked", "unknown"), finding("wsl.internal", "skipped")]


def fixture_cli(argv):
    from windows_ai_doctor import __version__, cli
    from windows_ai_doctor.compare import STATES

    class AuthoredDoctor:
        def __init__(self, **kwargs):
            self.lang = kwargs["lang"]

        def run(self):
            zh = self.lang == "zh"
            items = observations()
            for item in items:
                item.update(target=item["id"].split(".", 1)[0],
                            summary="预设合成观察，不代表主机状态。" if zh else "Authored synthetic observation, not host state.",
                            recommendation="自行核对检查范围。" if zh else "Review the check scope.",
                            recheck="使用实际诊断另行复查。" if zh else "Recheck with a separate real diagnosis.")
            return {"schema_version": "1.0", "report_type": "diagnosis",
                    "doctor_version": __version__, "generated_at": "2000-01-01T00:00:00+00:00",
                    "language": self.lang,
                    "summary": {state: sum(item["status"] == state for item in items) for state in STATES},
                    "findings": items, "privacy": {"synthetic": True},
                    "priorities": [item["id"] for state in ("error", "warn", "unknown")
                                   for item in items if item["status"] == state]}

    cli.Doctor = AuthoredDoctor
    return cli.main(argv)


def main():
    dest = (Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / "examples/v07").absolute()
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        raise ValueError("new_example_directory_required")
    runs = []

    def run(label, *args, expect=0):
        result = subprocess.run([sys.executable, "-B", str(Path(__file__).absolute()),
                                 "--fixture-cli", *map(str, args)],
                                capture_output=True, cwd=dest, timeout=30)
        runs.append({"step": label, "exit_code": result.returncode, "expected_exit_code": expect})
        if result.returncode != expect:
            raise RuntimeError("synthetic_example_failed:" + label + ":" + str(result.returncode))
        return result

    # Baseline omits claude.path so current error is an added new-finding;
    # codex.version stays pass→warn regression. Both gates are exercised.
    baseline = {"schema_version": "1.0", "report_type": "diagnosis", "findings": [
        finding("system.platform", "pass"),
        finding("codex.version", "pass", version="1.2.3"),
        finding("codex.path", "warn", installation_groups=1, scan_limited=False),
        finding("scope.unchecked", "unknown"), finding("wsl.running", "pass")]}
    current = {"schema_version": "1.0", "report_type": "diagnosis", "findings": observations()}
    for name, document in (("baseline.json", baseline), ("current.json", current)):
        (dest / name).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    for lang in ("zh", "en"):
        folder = dest / ("baseline-" + lang)
        run("baseline_all_" + lang, "--baseline", dest / "baseline.json", "--fail-on", "new", "regression",
            "--lang", lang, "--format", "all", "--output-dir", folder, expect=1)
        report = json.loads((folder / ("report." + lang + ".json")).read_text(encoding="utf-8"))
        md = (folder / ("report." + lang + ".md")).read_text(encoding="utf-8")
        label = "新发现: 1" if lang == "zh" else "New findings: 1"
        if (report["baseline"]["new_findings"] != ["claude.path"]
                or report["baseline"]["regressions"] != ["codex.version"]
                or label not in md):
            raise RuntimeError("baseline_new_findings")
        html = (folder / ("report." + lang + ".html")).read_text(encoding="utf-8")
        for identifier in ("baseline-comparison", "baseline-heading", "baseline-counts", "baseline-changes"):
            if html.count('id="' + identifier + '"') != 1:
                raise RuntimeError("baseline_html_id")
        if label not in html:
            raise RuntimeError("baseline_html_new_count")

    csv_bodies = []
    for lang in ("zh", "en"):
        result = run("diagnosis_csv_" + lang, "--baseline", dest / "baseline.json",
                     "--fail-on", "new", "--lang", lang, "--format", "csv", expect=1)
        text = result.stdout.decode("utf-8")
        header = ("sequence,check_id,target,status,version,installation_groups,"
                  "scan_limited,baseline_change,baseline_status,baseline_regression")
        if not text.startswith("\ufeff" + header + "\n") or "\r" in text:
            raise RuntimeError("diagnosis_csv_encoding")
        if len(header.split(",")) != 10:
            raise RuntimeError("diagnosis_csv_columns")
        csv_bodies.append(result.stdout)
        (dest / ("report." + lang + ".csv")).write_bytes(result.stdout)
    if csv_bodies[0] != csv_bodies[1]:
        raise RuntimeError("diagnosis_csv_language")

    for lang in ("zh", "en"):
        folder = dest / ("sarif-" + lang)
        run("diagnosis_sarif_" + lang, "--baseline", dest / "baseline.json", "--fail-on", "new",
            "--lang", lang, "--format", "sarif", "--output-dir", folder, expect=1)
        body = (folder / ("report." + lang + ".sarif")).read_text(encoding="utf-8")
        document = json.loads(body)
        run_obj = document["runs"][0]
        baseline_props = run_obj["invocations"][0]["properties"]["baseline"]
        if (document["version"] != "2.1.0" or '"locations"' in body
                or baseline_props["new_findings"] != ["claude.path"]
                or any("partialFingerprints" not in r for r in run_obj["results"])
                or any("baselineState" not in r for r in run_obj["results"])):
            raise RuntimeError("sarif_structure")

    junit_bodies = []
    for lang in ("zh", "en"):
        folder = dest / ("junit-" + lang)
        run("diagnosis_junit_" + lang, "--baseline", dest / "baseline.json", "--fail-on", "new",
            "--lang", lang, "--format", "junit", "--output-dir", folder, expect=1)
        path = folder / ("report." + lang + ".junit.xml")
        text = path.read_text(encoding="utf-8")
        if text.startswith("\ufeff") or "\r" in text or not text.endswith("\n"):
            raise RuntimeError("junit_encoding")
        root = ET.fromstring(text)
        cases = list(root.find("testsuite"))
        if not cases or any(c.find("properties") is None for c in cases):
            raise RuntimeError("junit_properties")
        nonhit = [c for c in cases if c.find("failure") is None and c.find("skipped") is None]
        if not nonhit or any([n.tag for n in c] != ["properties"] for c in nonhit):
            raise RuntimeError("junit_nonhit_children")
        junit_bodies.append([(c.get("name"), [n.tag for n in c],
                              [p.get("name") for p in c.findall("properties/property")]) for c in cases])
        stdout = run("diagnosis_junit_stdout_" + lang, "--baseline", dest / "baseline.json",
                     "--fail-on", "new", "--lang", lang, "--format", "junit", expect=1)
        if stdout.stdout != path.read_bytes():
            raise RuntimeError("junit_stdout_bytes")
    if [row[:2] for row in junit_bodies[0]] != [row[:2] for row in junit_bodies[1]]:
        raise RuntimeError("junit_language_structure")

    same = run("same_baseline_exit_0", "--baseline", dest / "current.json", "--fail-on", "new",
               "--format", "junit")
    same_root = ET.fromstring(same.stdout)
    if same_root.get("failures") != "0" or int(same.returncode) != 0:
        raise RuntimeError("unexpected_same_baseline_new")

    (dest / "runs.json").write_text(
        json.dumps({"synthetic": True, "live_host_probes": False, "exit_code": 0, "steps": runs}, indent=2) + "\n",
        encoding="utf-8")
    print("v0.7 synthetic examples: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(fixture_cli(sys.argv[2:]) if len(sys.argv) > 1 and sys.argv[1] == "--fixture-cli" else main())
