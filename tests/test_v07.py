"""New-finding policy, portable JUnit and SARIF baseline contracts."""
import copy
import csv
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from test_v02 import item, source
from test_v05_integration import IntegrationFixture
from test_v06 import diagnosis
from windows_ai_doctor import cli
from windows_ai_doctor.baseline import baseline_report, diagnosis_csv
from windows_ai_doctor.compare import STATES, project
from windows_ai_doctor.junit import junit_report
from windows_ai_doctor.report import html_report, markdown_report
from windows_ai_doctor.sarif import sarif_document, sarif_report


def compared(*findings, old=(), selected=("new",), lang="zh"):
    report = diagnosis(*findings, lang=lang)
    report["baseline"] = baseline_report(project(source(*old)), project(report), lang)
    report["exit_policy"]["fail_on"] = list(selected)
    return report


class NewFindingTests(IntegrationFixture):
    def test_added_error_and_warn_are_new_and_ascii_sorted(self):
        b = compared(item("codex.version", "error"), item("claude.path", "warn"))["baseline"]
        self.assertEqual(b["new_findings"], ["claude.path", "codex.version"])
        self.assertEqual(b["summary"], {"added": 2, "removed": 0, "changed": 0})
        self.assertEqual(b["regressions"], [])

    def test_added_pass_unknown_skipped_are_not_new(self):
        for state in ("pass", "unknown", "skipped"):
            b = compared(item(status=state))["baseline"]
            self.assertEqual(b["new_findings"], [])
            self.assertEqual(b["summary"]["added"], 1)

    def test_added_scan_limited_path_excluded_but_absent_false_included(self):
        for limited in (None, False, True):
            for state in ("warn", "error"):
                report = compared(item("codex.path", state, **({"scan_limited": limited} if limited is not None else {})))
                self.assertEqual(report["baseline"]["new_findings"], [] if limited is True else ["codex.path"])

    def test_non_path_ignored_scan_limit_cannot_suppress_new(self):
        report = compared(item("codex.version", "warn", scan_limited=True))
        self.assertEqual(report["baseline"]["new_findings"], ["codex.version"])

    def test_changed_and_removed_are_not_new_in_all_state_transitions(self):
        for before in STATES:
            for after in STATES:
                b = compared(item(status=after), old=(item(status=before), item("wsl.internal", "error")))["baseline"]
                self.assertEqual(b["new_findings"], [])

    def test_new_requires_baseline_before_doctor_or_input_reads(self):
        with patch.object(cli, "Doctor", side_effect=AssertionError("unexpected diagnosis")), patch.object(cli, "load_report", side_effect=AssertionError("unexpected read")):
            for selected in (("new",), ("warn", "new"), ("regression", "new")):
                self.assertEqual(self.invoke(["--fail-on", *selected])[:2], (2, ""))

    def test_mixed_policy_order_deduplication_and_triggered_are_exact(self):
        path = self.write(source(item("codex.version", "pass")))
        with patch.object(cli, "Doctor") as doctor:
            doctor.return_value.run.return_value = diagnosis(item("codex.version", "error"), item("claude.path", "warn"), item("wsl.internal", "unknown"))
            code, out, err = self.invoke(["--baseline", path, "--format=json", "--fail-on", "regression", "new", "warn", "new", "unknown", "error"])
        self.assertEqual((code, err), (1, ""))
        policy = json.loads(out)["exit_policy"]
        self.assertEqual(policy["fail_on"], ["error", "warn", "unknown", "new", "regression"])
        self.assertEqual(policy["triggered"], policy["fail_on"])
        self.assertIs(policy["matched"], True)
        for text in ("added", "error/warn", "扫描受限", "故障根因"):
            self.assertIn(text, policy["meaning"])

    def test_md_html_new_count_and_fixed_id_and_csv_ten_columns(self):
        for lang, label in (("zh", "新发现: 1"), ("en", "New findings: 1")):
            report = compared(item("codex.path", "warn"), item("wsl.internal", "skipped"), lang=lang)
            self.assertIn(label, markdown_report(report))
            text = html_report(report)
            self.assertIn(label, text)
            self.assertEqual(text.count('id="baseline-counts"'), 1)
            rows = list(csv.reader(io.StringIO(diagnosis_csv(report)[1:])))
            self.assertTrue(all(len(row) == 10 for row in rows))

    def test_real_new_policy_exit_one_and_same_baseline_exit_zero(self):
        empty = self.write(source())
        result = self.cli("--no-version", "--baseline", str(empty), "--fail-on=new", "--format=json")
        self.assertEqual((result.returncode, result.stderr), (1, ""))
        doc = json.loads(result.stdout)
        self.assertEqual(doc["baseline"]["new_findings"], ["claude.path", "codex.path"])
        current = self.write(doc, "same.json")
        same = self.cli("--no-version", "--baseline", str(current), "--fail-on=new", "--format=json")
        self.assertEqual((same.returncode, same.stderr), (0, ""))
        self.assertEqual(json.loads(same.stdout)["baseline"]["new_findings"], [])


class JUnitTests(IntegrationFixture):
    def test_counts_default_policy_order_and_fixed_attributes(self):
        report = diagnosis(item("wsl.internal", "skipped"), item("codex.version", "error"), item("claude.path", "warn"))
        root = ET.fromstring(junit_report(report))
        counts = {"tests": "3", "failures": "1", "skipped": "1", "errors": "0"}
        self.assertEqual(root.attrib, {"name": "Windows AI Doctor", **counts})
        suite = root.find("testsuite")
        self.assertEqual(suite.attrib, {"name": "windows-ai-doctor", **counts})
        self.assertEqual([c.get("name") for c in suite], ["claude.path", "codex.version", "wsl.internal"])
        self.assertEqual([c.get("classname") for c in suite], ["windows-ai-doctor.claude", "windows-ai-doctor.codex", "windows-ai-doctor.wsl"])

    def test_skipped_and_nonselected_states_have_no_failure(self):
        report = diagnosis(*(item(check, state) for check, state in zip(("codex.path", "claude.path", "codex.version", "wsl.internal", "system.platform"), STATES)))
        suite = ET.fromstring(junit_report(report)).find("testsuite")
        self.assertEqual([c.get("name") for c in suite if c.find("failure") is not None], ["codex.version"])
        self.assertEqual([c.get("name") for c in suite if c.find("skipped") is not None], ["system.platform"])
        for case in suite:
            self.assertEqual(case.find("properties/property").get("name"), "status")
            if case.get("name") in ("codex.path", "claude.path", "wsl.internal"):
                self.assertEqual([n.tag for n in case], ["properties"])

    def test_multiselected_new_regression_reasons_are_ordered_one_failure_each(self):
        report = compared(item("codex.version", "error"), item("claude.path", "warn"), old=(item("codex.version", "pass"),), selected=("error", "warn", "new", "regression"), lang="en")
        cases = ET.fromstring(junit_report(report)).findall("testsuite/testcase")
        self.assertEqual([c.find("failure").get("message") for c in cases], [
            "Selected exit condition: warn; New finding versus baseline",
            "Selected exit condition: error; Regression under fixed rules"])
        self.assertTrue(all(len(c.findall("failure")) == 1 for c in cases))

    def test_baseline_properties_added_changed_unchanged_and_booleans(self):
        report = compared(item("codex.path", "warn", scan_limited=False), item("codex.version", "warn"), item("wsl.internal", "unknown"),
                          old=(item("codex.version", "pass"), item("wsl.internal", "unknown")))
        cases = ET.fromstring(junit_report(report)).findall("testsuite/testcase")
        props = {c.get("name"): {p.get("name"): p.get("value") for p in c.findall("properties/property")} for c in cases}
        self.assertEqual(props["codex.path"], {"status": "warn", "scan_limited": "false", "baseline_change": "added", "baseline_new": "true", "baseline_regression": "false"})
        self.assertEqual(props["codex.version"]["baseline_change"], "changed")
        self.assertEqual(props["codex.version"]["baseline_regression"], "true")
        self.assertEqual(props["wsl.internal"]["baseline_change"], "unchanged")

    def test_determinism_encoding_and_bilingual_structure(self):
        outputs = []
        for lang in ("zh", "en"):
            report = compared(item(status="error"), lang=lang)
            text = junit_report(report)
            self.assertEqual(text, junit_report(report))
            self.assertTrue(text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'))
            self.assertTrue(text.endswith("\n"))
            self.assertNotIn("\r", text)
            self.assertFalse(text.startswith("\ufeff"))
            root = ET.fromstring(text)
            outputs.append([(node.tag, sorted(node.attrib.keys())) for node in root.iter()])
        self.assertEqual(*outputs)

    def test_xml_escapes_fixed_message_and_never_imports_arbitrary_text(self):
        report = diagnosis(item(status="error", version="1.2.3", path="PRIVATE_EVIDENCE"))
        report["findings"][0]["summary"] = "PRIVATE_SUMMARY"
        report["generated_at"] = "PRIVATE_TIME"
        with patch.dict("windows_ai_doctor.junit.MESSAGES", {"zh": ('Selected <&"', "new", "regression", "Fixed <&> policy", "; ")}):
            text = junit_report(report)
        root = ET.fromstring(text)
        failure = root.find("testsuite/testcase/failure")
        self.assertEqual(failure.get("message"), 'Selected <&"error')
        self.assertEqual(failure.text, "Fixed <&> policy")
        for marker in ("PRIVATE_", "1.2.3", 'timestamp=', 'hostname=', 'time=', 'file=', 'line='):
            self.assertNotIn(marker, text)

    def test_real_stdout_and_file_bytes_are_equal_and_no_saved_message(self):
        result = self.cli("--no-version", "--format=junit", "--lang=en")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        ET.fromstring(result.stdout)
        dest = self.root / "out"
        saved = self.cli("--no-version", "--format=junit", "--lang=en", "--output-dir", str(dest))
        self.assertEqual((saved.returncode, saved.stdout, saved.stderr), (0, "", ""))
        self.assertEqual((dest / "report.en.junit.xml").read_bytes(), result.stdout.encode("utf-8"))
        self.assertEqual(len(list(dest.iterdir())), 1)

    def test_offline_modes_reject_junit_before_reads(self):
        p = self.root / "unread.json"
        with patch.object(cli, "load_report", side_effect=AssertionError("unexpected read")), patch.object(cli, "load_history", side_effect=AssertionError("unexpected read")), patch.object(cli, "verify_support", side_effect=AssertionError("unexpected read")):
            for mode in (["--compare", p, p], ["--history", p, p], ["--support", p], ["--validate", p], ["--verify-support", p], ["--catalog"], ["--schema"]):
                self.assertEqual(self.invoke([*mode, "--format=junit"])[:2], (2, ""))

    def test_collision_preserves_existing_and_creates_nothing(self):
        dest = self.root / "out"
        dest.mkdir()
        path = dest / "report.zh.junit.xml"
        path.write_bytes(b"existing")
        with patch.object(cli, "Doctor") as doctor:
            doctor.return_value.run.return_value = diagnosis(item())
            code, out, _ = self.invoke(["--format=junit", "--output-dir", dest])
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(path.read_bytes(), b"existing")

    def check_cleanup(self, exception, expected):
        dest = self.root / "out"
        original = Path.open
        class InterruptedWriter:
            def __enter__(writer):
                writer.stream = original(dest / "report.zh.junit.xml", "x", encoding="utf-8")
                return writer
            def write(writer, text):
                writer.stream.write(text[:10])
                raise exception
            def __exit__(writer, *args):
                writer.stream.close()
        def opening(path, mode="r", *args, **kwargs):
            return InterruptedWriter() if path.name == "report.zh.junit.xml" and mode == "x" else original(path, mode, *args, **kwargs)
        with patch.object(cli, "Doctor") as doctor, patch.object(Path, "open", opening):
            doctor.return_value.run.return_value = diagnosis(item())
            code, out, _ = self.invoke(["--format=junit", "--output-dir", dest])
        self.assertEqual((code, out), (expected, ""))
        self.assertEqual(list(dest.iterdir()), [])

    def test_partial_write_cleanup_exit_two(self):
        self.check_cleanup(OSError("synthetic failure"), 2)

    def test_keyboard_interrupt_cleanup_exit_130(self):
        self.check_cleanup(KeyboardInterrupt(), 130)


class SarifBaselineTests(IntegrationFixture):
    def test_baseline_states_and_result_only_counts(self):
        report = compared(item("codex.path", "warn"), item("codex.version", "error"), item("wsl.internal", "unknown"), item("system.platform", "pass"),
                          old=(item("codex.version", "pass"), item("wsl.internal", "unknown"), item("wsl.launcher", "error")))
        run = sarif_document(report)["runs"][0]
        self.assertEqual({r["ruleId"]: r["baselineState"] for r in run["results"]}, {"codex.path": "new", "codex.version": "updated", "wsl.internal": "unchanged"})
        baseline = run["invocations"][0]["properties"]["baseline"]
        self.assertEqual(baseline["new_findings"], ["codex.path"])
        self.assertEqual(baseline["result_baseline_states"], {"new": 1, "updated": 1, "unchanged": 1})

    def test_no_baseline_omits_states_and_fingerprints_stable_across_versions_states(self):
        outputs = []
        for state in ("warn", "unknown", "error"):
            report = diagnosis(item(status=state, version="1.2.3"))
            run = sarif_document(report)["runs"][0]
            self.assertNotIn("baseline", run["invocations"][0]["properties"])
            result = run["results"][0]
            self.assertNotIn("baselineState", result)
            outputs.append(result["partialFingerprints"])
        self.assertEqual(outputs, [{"windowsAIDoctorCheckId/v1": "codex.version"}] * 3)

    def test_scan_limited_added_result_is_new_state_but_not_policy_new(self):
        report = compared(item("codex.path", "warn", scan_limited=True))
        run = sarif_document(report)["runs"][0]
        self.assertEqual(run["results"][0]["baselineState"], "new")
        self.assertEqual(run["invocations"][0]["properties"]["baseline"]["new_findings"], [])
        self.assertEqual(sarif_report(report), sarif_report(copy.deepcopy(report)))
