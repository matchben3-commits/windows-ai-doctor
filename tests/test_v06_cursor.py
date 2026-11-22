"""Independent cursor cross-checks for v0.6 baseline / CSV / SARIF contracts."""
import csv
import io
import json
from contextlib import ExitStack
from unittest.mock import patch

from test_v02 import item, source
from test_v05_integration import IntegrationFixture
from test_v06 import diagnosis
from windows_ai_doctor import __version__, cli
from windows_ai_doctor.baseline import DIAGNOSIS_COLUMNS, baseline_report, diagnosis_csv
from windows_ai_doctor.catalog import catalog_report
from windows_ai_doctor.compare import project
from windows_ai_doctor.sarif import HELP_URI, SCHEMA_URI, sarif_document, sarif_report


class CursorBaselineContract(IntegrationFixture):
    def test_non_regression_transitions_and_scan_limited_true_blocks(self):
        cases = [
            ("pass", "unknown", False),
            ("pass", "skipped", False),
            ("pass", "pass", False),
            ("warn", "pass", False),
            ("error", "warn", False),
            ("unknown", "error", False),
            ("skipped", "error", False),
            ("warn", "error", True),
        ]
        for before, after, expected in cases:
            result = baseline_report(project(source(item(status=before))), project(source(item(status=after))))
            self.assertEqual(bool(result["regressions"]), expected, (before, after))
        limited = baseline_report(
            project(source(item("codex.path", "pass", scan_limited=True))),
            project(source(item("codex.path", "error", scan_limited=False))))
        self.assertEqual(limited["regressions"], [])

    def test_exit_policy_meaning_mentions_fixed_transitions_only(self):
        path = self.write(source(item(status="pass")))
        with patch.object(cli, "Doctor") as doctor:
            doctor.return_value.run.return_value = diagnosis(item(status="warn"))
            code, out, err = self.invoke(
                ["--baseline", path, "--fail-on=regression", "--format=json", "--lang=zh"])
        self.assertEqual((code, err), (1, ""))
        meaning = json.loads(out)["exit_policy"]["meaning"]
        self.assertIn("固定状态转移", meaning)
        self.assertIn("不等于已确认故障根因", meaning)
        self.assertNotIn("四种", meaning)

    def test_no_baseline_csv_leaves_baseline_columns_blank_not_false(self):
        report = diagnosis(item("codex.path", installation_groups=0, scan_limited=False))
        row = next(csv.reader(io.StringIO(diagnosis_csv(report)[1:])))
        self.assertEqual(row, list(DIAGNOSIS_COLUMNS))
        body = next(csv.reader(io.StringIO(diagnosis_csv(report)[1:].split("\n", 1)[1])))
        self.assertEqual(body[7:], ["", "", ""])
        self.assertNotEqual(body[7:], ["", "", "false"])


class CursorCSVContract(IntegrationFixture):
    def test_removed_and_added_baseline_status_rules(self):
        report = diagnosis(item("codex.version", "warn", version="2.0.0"))
        old = project(source(item("codex.version", "pass", version="1.0.0"), item("wsl.internal", "pass")))
        report["baseline"] = baseline_report(old, project(report))
        rows = {row[1]: row for row in csv.reader(io.StringIO(diagnosis_csv(report)[1:]))}
        self.assertEqual(rows["codex.version"][7:], ["changed", "pass", "true"])
        self.assertEqual(rows["wsl.internal"][3], "")
        self.assertEqual(rows["wsl.internal"][7:], ["removed", "pass", "false"])
        added = diagnosis(item("claude.path", "pass", installation_groups=1, scan_limited=False))
        added["baseline"] = baseline_report({}, project(added))
        added_row = next(r for r in csv.reader(io.StringIO(diagnosis_csv(added)[1:])) if r[1] == "claude.path")
        self.assertEqual(added_row[7:], ["added", "", "false"])

    def test_offline_modes_still_reject_diagnosis_csv_and_sarif(self):
        path = self.root / "input.json"
        path.write_text("{}", encoding="utf-8")
        with ExitStack() as stack:
            for name in ("Doctor", "load_report", "load_history", "verify_support"):
                stack.enter_context(patch.object(cli, name, side_effect=AssertionError("read before validation")))
            for mode in (["--validate", path], ["--verify-support", path], ["--support", path],
                         ["--catalog"], ["--schema"]):
                self.assertEqual(self.invoke([*mode, "--format=csv"])[0:2], (2, ""))
            for mode in (["--compare", path, path], ["--history", path, path], ["--validate", path],
                         ["--catalog"], ["--schema"]):
                self.assertEqual(self.invoke([*mode, "--format=sarif"])[0:2], (2, ""))


class CursorSarifContract(IntegrationFixture):
    def test_help_uri_schema_uri_and_pass_skipped_absent_from_results(self):
        report = diagnosis(
            item("codex.path", "pass", scan_limited=False),
            item("claude.version", "warn"),
            item("wsl.internal", "skipped"),
            item("system.platform", "error"),
            item("scope.unchecked", "unknown"))
        document = sarif_document(report)
        self.assertEqual(document["$schema"], SCHEMA_URI)
        driver = document["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["semanticVersion"], __version__)
        self.assertEqual(driver["rules"][0]["helpUri"], HELP_URI)
        self.assertTrue(HELP_URI.endswith("docs/v06-contract.md"))
        results = document["runs"][0]["results"]
        self.assertEqual([r["ruleId"] for r in results],
                         ["claude.version", "scope.unchecked", "system.platform"])
        self.assertEqual({r["level"] for r in results}, {"warning", "note", "error"})
        self.assertNotIn("codex.path", [r["ruleId"] for r in results])
        self.assertNotIn("wsl.internal", [r["ruleId"] for r in results])
        props = document["runs"][0]["invocations"][0]["properties"]
        self.assertEqual(props["summary"]["pass"], 1)
        self.assertEqual(props["summary"]["skipped"], 1)

    def test_english_rules_match_catalog_language_and_structure_isomorphic(self):
        zh = diagnosis(item("codex.version", "unknown"), lang="zh")
        en = diagnosis(item("codex.version", "unknown"), lang="en")
        zh_doc, en_doc = sarif_document(zh), sarif_document(en)
        zh_rules = zh_doc["runs"][0]["tool"]["driver"]["rules"]
        en_rules = en_doc["runs"][0]["tool"]["driver"]["rules"]
        catalog_zh = catalog_report(lang="zh")["checks"]
        catalog_en = catalog_report(lang="en")["checks"]
        self.assertEqual([r["id"] for r in zh_rules], [c["id"] for c in catalog_zh])
        self.assertEqual([r["id"] for r in en_rules], [c["id"] for c in catalog_en])
        for rule, check in zip(en_rules, catalog_en):
            self.assertEqual(rule["shortDescription"]["text"], check["purpose"]["en"])
            self.assertEqual(rule["fullDescription"]["text"], check["limitation"]["en"])
        def structure(obj):
            if isinstance(obj, dict):
                return {key: structure(value) for key, value in obj.items()}
            if isinstance(obj, list):
                return [structure(value) for value in obj]
            return type(obj).__name__
        self.assertEqual(structure(zh_doc), structure(en_doc))
        self.assertEqual(sarif_report(en), sarif_report(en))

    def test_no_baseline_omits_baseline_properties_and_csv_blank_columns(self):
        report = diagnosis(item("codex.version", "error", version="1.2.3"))
        invocation = sarif_document(report)["runs"][0]["invocations"][0]
        self.assertNotIn("baseline", invocation["properties"])
        row = next(r for r in csv.reader(io.StringIO(diagnosis_csv(report)[1:])) if r[1] == "codex.version")
        self.assertEqual(row[7:], ["", "", ""])
