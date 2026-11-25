"""Independent cursor cross-checks for v0.7 JUnit / new / SARIF contracts."""
import json
import xml.etree.ElementTree as ET
from unittest.mock import patch

from test_v02 import item, source
from test_v05_integration import IntegrationFixture
from test_v06 import diagnosis
from test_v07 import compared
from windows_ai_doctor import __version__, cli
from windows_ai_doctor.compare import STATES
from windows_ai_doctor.junit import junit_report
from windows_ai_doctor.sarif import HELP_URI, SCHEMA_URI, sarif_document, sarif_report


PROPERTY_ORDER = ("status", "scan_limited", "baseline_change", "baseline_new", "baseline_regression")


def property_names(case):
    return tuple(p.get("name") for p in case.findall("properties/property"))


class CursorJUnitContract(IntegrationFixture):
    def test_nonhit_children_are_exactly_properties_with_fixed_order(self):
        """dsh freeze: every case has properties; non-hit pass/warn/unknown are properties-only."""
        report = compared(
            item("codex.path", "pass", scan_limited=False),
            item("claude.path", "warn", scan_limited=True),
            item("codex.version", "unknown"),
            item("wsl.internal", "pass"),
            item("system.platform", "error"),
            old=(item("wsl.internal", "pass"), item("system.platform", "pass")),
            selected=("error", "new", "regression"),
        )
        suite = ET.fromstring(junit_report(report)).find("testsuite")
        for case in suite:
            props = case.find("properties")
            self.assertIsNotNone(props)
            self.assertTrue(len(list(props)) >= 1)
            names = property_names(case)
            self.assertEqual(names[0], "status")
            self.assertEqual(names, tuple(n for n in PROPERTY_ORDER if n in names))
            if case.get("name") in ("codex.path", "claude.path", "codex.version", "wsl.internal"):
                self.assertEqual([n.tag for n in case], ["properties"])
                self.assertIsNone(case.find("failure"))
                self.assertIsNone(case.find("skipped"))
                self.assertIsNone(case.find("error"))
            if case.get("name") == "system.platform":
                self.assertEqual([n.tag for n in case], ["properties", "failure"])

    def test_skipped_keeps_properties_then_skipped_element(self):
        report = diagnosis(item("wsl.internal", "skipped"), item("codex.path", "pass"))
        cases = {c.get("name"): c for c in ET.fromstring(junit_report(report)).findall("testsuite/testcase")}
        skipped = cases["wsl.internal"]
        self.assertEqual([n.tag for n in skipped], ["properties", "skipped"])
        self.assertEqual(property_names(skipped), ("status",))
        self.assertEqual([n.tag for n in cases["codex.path"]], ["properties"])

    def test_scan_limited_property_only_when_evidence_has_field(self):
        report = diagnosis(
            item("codex.path", "warn", scan_limited=False),
            item("codex.version", "warn"),
            item("claude.path", "error", scan_limited=True),
        )
        props = {c.get("name"): property_names(c)
                 for c in ET.fromstring(junit_report(report)).findall("testsuite/testcase")}
        self.assertEqual(props["codex.path"], ("status", "scan_limited"))
        self.assertEqual(props["codex.version"], ("status",))
        self.assertEqual(props["claude.path"], ("status", "scan_limited"))

    def test_empty_findings_suite_counts_zero_and_no_cases(self):
        report = diagnosis()
        report["findings"] = []
        report["summary"] = dict.fromkeys(STATES, 0)
        root = ET.fromstring(junit_report(report))
        self.assertEqual(root.attrib["tests"], "0")
        self.assertEqual(root.attrib["failures"], "0")
        self.assertEqual(root.attrib["skipped"], "0")
        self.assertEqual(list(root.find("testsuite")), [])

    def test_warn_unknown_not_selected_never_emit_skipped(self):
        report = diagnosis(item("codex.version", "warn"), item("wsl.internal", "unknown"))
        for case in ET.fromstring(junit_report(report)).findall("testsuite/testcase"):
            self.assertIsNone(case.find("skipped"))
            self.assertIsNone(case.find("failure"))
            self.assertEqual([n.tag for n in case], ["properties"])


class CursorNewPolicyContract(IntegrationFixture):
    def test_new_alone_and_with_error_reject_without_baseline(self):
        with patch.object(cli, "Doctor", side_effect=AssertionError("unexpected diagnosis")):
            for args in (["--fail-on", "new"], ["--fail-on", "error", "new"], ["--fail-on=new"]):
                self.assertEqual(self.invoke(args)[:2], (2, ""))

    def test_new_failure_message_zh_and_property_baseline_new(self):
        report = compared(item("claude.path", "warn"), selected=("new",), lang="zh")
        case = ET.fromstring(junit_report(report)).find("testsuite/testcase")
        self.assertEqual(case.find("failure").get("message"), "新发现（相对基线）")
        names = property_names(case)
        self.assertEqual(names, ("status", "baseline_change", "baseline_new", "baseline_regression"))
        values = {p.get("name"): p.get("value") for p in case.findall("properties/property")}
        self.assertEqual(values["baseline_new"], "true")
        self.assertEqual(values["baseline_change"], "added")

    def test_real_cli_new_without_baseline_exits_two_before_doctor(self):
        result = self.cli("--no-version", "--fail-on=new", "--format=junit")
        self.assertEqual((result.returncode, result.stdout), (2, ""))


class CursorSarifContract(IntegrationFixture):
    def test_help_uri_version_and_fingerprint_key_are_fixed(self):
        document = sarif_document(diagnosis(item(status="error")))
        run = document["runs"][0]
        self.assertEqual(document["$schema"], SCHEMA_URI)
        self.assertEqual(run["tool"]["driver"]["semanticVersion"], __version__)
        self.assertEqual(__version__, "1.0.0")
        self.assertTrue(HELP_URI.endswith("/docs/v07-contract.md"))
        self.assertTrue(all(r["helpUri"] == HELP_URI for r in run["tool"]["driver"]["rules"]))
        self.assertEqual(run["results"][0]["partialFingerprints"],
                         {"windowsAIDoctorCheckId/v1": "codex.version"})

    def test_absent_baseline_ids_never_appear_as_results(self):
        report = compared(item("codex.version", "error"),
                          old=(item("codex.version", "pass"), item("wsl.launcher", "error")))
        run = sarif_document(report)["runs"][0]
        self.assertEqual([r["ruleId"] for r in run["results"]], ["codex.version"])
        self.assertNotIn("absent", {r.get("baselineState") for r in run["results"]})
        self.assertEqual(run["invocations"][0]["properties"]["baseline"]["result_baseline_states"],
                         {"new": 0, "updated": 1, "unchanged": 0})

    def test_bilingual_structure_byte_stable_and_no_locations(self):
        bodies = []
        for lang in ("zh", "en"):
            report = compared(item("codex.path", "warn"), item("system.platform", "pass"), lang=lang)
            text = sarif_report(report)
            self.assertEqual(text, sarif_report(report))
            self.assertNotIn('"locations"', text)
            self.assertNotIn('"artifacts"', text)
            self.assertFalse(text.startswith("\ufeff"))
            bodies.append([(r["ruleId"], r["baselineState"], sorted(r["partialFingerprints"]))
                           for r in json.loads(text)["runs"][0]["results"]])
        self.assertEqual(*bodies)

    def test_junit_stdout_pure_xml_no_saved_hint_mixed_with_new(self):
        empty = self.write(source())
        result = self.cli("--no-version", "--baseline", str(empty), "--fail-on=new",
                          "--format=junit", "--lang=en")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        root = ET.fromstring(result.stdout)
        self.assertEqual(root.tag, "testsuites")
        for marker in ("Reports saved", "报告已保存", "PRIVATE", "\r"):
            self.assertNotIn(marker, result.stdout)
        self.assertTrue(any(c.find("failure") is not None for c in root.findall("testsuite/testcase")))
