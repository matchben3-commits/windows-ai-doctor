"""Baseline transitions, safe machine exports and required real-link boundaries."""
import copy
import csv
import io
import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from test_v02 import item, source
from test_v05_integration import IntegrationFixture
import test_boundaries
from windows_ai_doctor import __version__, cli
from windows_ai_doctor.baseline import DIAGNOSIS_COLUMNS, baseline_report, diagnosis_csv
from windows_ai_doctor.catalog import catalog_report
from windows_ai_doctor.compare import MAX_BYTES, STATES, project
from windows_ai_doctor.report import html_report, markdown_report
from windows_ai_doctor.sarif import sarif_document, sarif_report


def diagnosis(*findings, lang="zh", matched=False):
    report = source(*copy.deepcopy(findings))
    report.update({"doctor_version": __version__, "generated_at": "2000-01-01T00:00:00+00:00", "language": lang,
                   "summary": {state: sum(f["status"] == state for f in findings) for state in STATES},
                   "privacy": {}, "priorities": [],
                   "exit_policy": {"fail_on": ["error"], "triggered": ["error"] if matched else [],
                                   "matched": matched, "meaning": "Synthetic policy"}})
    for finding in report["findings"]:
        finding.update({"summary": "固定观察" if lang == "zh" else "Fixed observation",
                        "recommendation": "Review", "recheck": "Recheck"})
    return report


class BaselineTests(IntegrationFixture):
    def test_all_twenty_five_state_pairs_have_exactly_three_regressions(self):
        for before in STATES:
            for after in STATES:
                old, new = project(source(item(status=before))), project(source(item(status=after)))
                result = baseline_report(old, new)
                expected = (before, after) in {("pass", "warn"), ("pass", "error"), ("warn", "error")}
                self.assertEqual(result["regressions"], ["codex.version"] if expected else [], (before, after))
                if before == after:
                    self.assertEqual((result["unchanged"], result["changes"]), (1, []))
                else:
                    self.assertEqual(result["changes"][0]["regression"], expected)

    def test_missing_false_true_scan_limits_on_each_side(self):
        for before in (None, False, True):
            for after in (None, False, True):
                old = project(source(item("codex.path", "pass", **({"scan_limited": before} if before is not None else {}))))
                new = project(source(item("codex.path", "error", **({"scan_limited": after} if after is not None else {}))))
                result = baseline_report(old, new)
                expected = before is not True and after is not True
                self.assertEqual(bool(result["regressions"]), expected, (before, after))

    def test_added_removed_changes_and_unchanged_are_sorted_and_deterministic(self):
        old = project(source(item("codex.version", "pass", version="1.2.3"), item("wsl.internal", "pass"),
                             item("system.platform", "pass")))
        new = project(source(item("codex.version", "warn", version="2.0.0"), item("claude.path", "error"),
                             item("system.platform", "pass")))
        result = baseline_report(old, new)
        self.assertEqual(result, baseline_report(old, new))
        self.assertEqual(result["summary"], {"added": 1, "removed": 1, "changed": 1})
        self.assertEqual(result["unchanged"], 1)
        self.assertEqual([c["id"] for c in result["changes"]], ["claude.path", "codex.version", "wsl.internal"])
        self.assertEqual([c["regression"] for c in result["changes"]], [False, True, False])
        self.assertEqual(result["changes"][1]["details"], {"version": {"before": "1.2.3", "after": "2.0.0"}})
        self.assertFalse({"generated_at", "language", "doctor_version", "report_type"} & result.keys())

    def test_malformed_derived_duplicate_and_bounded_inputs_fail_before_doctor(self):
        invalid_texts = ['{"schema_version":"1.0","findings":[],"x":1,"x":2}',
                         json.dumps(source(item(), item())), json.dumps(source(item(status="bad"))),
                         " " * (MAX_BYTES + 1), "[" * 17 + "0" + "]" * 17,
                         json.dumps({**source(), "ignored": list(range(20000))})]
        invalid_texts.extend(json.dumps({**source(), "report_type": kind}) for kind in
                             ("comparison", "history", "support", "validation", "support_verification", "catalog"))
        path = self.root / "input.json"
        with patch.object(cli, "Doctor", side_effect=AssertionError("diagnosis started on invalid input")):
            for text in invalid_texts:
                path.write_text(text, encoding="utf-8")
                self.assertEqual(self.invoke(["--baseline", path, "--format=json"])[0:2], (2, ""))

    def test_baseline_conflicts_and_regression_without_baseline_fail_before_reads(self):
        path = self.root / "SYNTHETIC_PRIVATE"
        with ExitStack() as stack:
            for name in ("Doctor", "load_report", "load_history", "verify_support"):
                stack.enter_context(patch.object(cli, name, side_effect=AssertionError("operation before argument validation")))
            for mode in (["--compare", path, path], ["--history", path, path], ["--support", path],
                         ["--validate", path], ["--verify-support", path], ["--catalog"], ["--schema"]):
                self.assertEqual(self.invoke([*mode, "--baseline", path])[0:2], (2, ""))
            self.assertEqual(self.invoke(["--fail-on=regression"])[0:2], (2, ""))
            self.assertEqual(self.invoke(["--fail-on", "error", "regression"])[0:2], (2, ""))

    def test_read_before_diagnosis_and_exit_policy_for_regression_and_other_conditions(self):
        path = self.write(source(item(status="pass")))
        for state, selected, expected in (("warn", ["regression"], 1), ("unknown", ["regression"], 0),
                                          ("unknown", ["regression", "unknown"], 1), ("pass", ["regression"], 0)):
            events = []
            original = cli.load_report
            def load(p): events.append("load"); return original(p)
            def run(): events.append("diagnosis"); return diagnosis(item(status=state))
            with patch.object(cli, "load_report", load):
                # Mock the constructed Doctor so this unit test never consults a real home.
                with patch.object(cli, "Doctor") as doctor:
                    doctor.return_value.run.side_effect = run
                    code, out, err = self.invoke(["--baseline", path, "--format=json", "--fail-on", *selected])
            self.assertEqual((code, err, events), (expected, "", ["load", "diagnosis"]))
            report = json.loads(out)
            self.assertEqual(report["summary"][state], 1)
            policy = report["exit_policy"]
            self.assertEqual(policy["matched"], bool(expected))
            self.assertEqual(policy["fail_on"], [s for s in ("error", "warn", "unknown", "regression") if s in selected])
            self.assertEqual(policy["triggered"], [s for s in policy["fail_on"] if s == state or s == "regression" and state == "warn"])
            self.assertIn("固定状态转移", policy["meaning"])

    def test_baseline_free_text_cannot_reach_reports(self):
        marker = '=SYNTHETIC_PRIVATE_<script>alert(1)</script>'
        imported = source(item("codex.version", "pass", version="1.2.3", path=marker))
        imported.update({"summary": marker, "language": marker, "generated_at": marker, "secret": marker})
        imported["findings"][0]["summary"] = marker
        path = self.write(imported)
        for lang in ("zh", "en"):
            for fmt in ("json", "md", "html", "csv", "sarif"):
                with patch.object(cli, "Doctor") as doctor:
                    doctor.return_value.run.return_value = diagnosis(item("codex.version", "warn", version="2.0.0"), lang=lang)
                    code, out, err = self.invoke(["--baseline", path, "--lang", lang, "--format", fmt, "--fail-on=regression"])
                self.assertEqual((code, err), (1, ""))
                self.assertNotIn("SYNTHETIC_PRIVATE", out)
                self.assertNotIn(str(path), out)

    def test_baseline_md_html_sections_precede_exit_and_escape_text(self):
        report = diagnosis(item(status="warn"))
        report["baseline"] = baseline_report(project(source(item())), project(report))
        md, html = markdown_report(report), html_report(report)
        self.assertLess(md.index("## 基线对比"), md.index("## 退出条件"))
        self.assertLess(html.index('id="baseline-comparison"'), html.index("退出条件"))
        self.assertIn("固定规则回归", md)
        self.assertIn("固定规则回归", html)
        for identifier in ("baseline-comparison", "baseline-heading", "baseline-counts", "baseline-changes"):
            self.assertEqual(html.count('id="' + identifier + '"'), 1)
        report["baseline"]["notice"] = '<script>"&unsafe"</script>'
        self.assertNotIn('<script>', html_report(report))
        self.assertIn("&lt;script&gt;&quot;&amp;unsafe&quot;&lt;/script&gt;", html_report(report))

    def test_no_baseline_adds_no_baseline_object_or_section_and_preserves_format_sets(self):
        for fmt, extensions in (("both", {"md", "json"}), ("all", {"md", "json", "html"})):
            folder = self.root / fmt
            report = diagnosis(item())
            with patch.object(cli, "Doctor") as doctor:
                doctor.return_value.run.return_value = report
                self.assertEqual(self.invoke(["--format", fmt, "--output-dir", folder])[0], 0)
            self.assertEqual({p.suffix[1:] for p in folder.iterdir()}, extensions)
            self.assertNotIn("baseline", json.loads((folder / "report.zh.json").read_text(encoding="utf-8")))
            self.assertNotIn("基线对比", (folder / "report.zh.md").read_text(encoding="utf-8"))

    def test_real_child_process_baseline_regression_exit_zero_one_and_bad_input_two(self):
        initial = self.cli("--no-version", "--format=json")
        self.assertEqual(initial.returncode, 0)
        baseline = json.loads(initial.stdout)
        path = self.write(baseline)
        same = self.cli("--no-version", "--baseline", str(path), "--fail-on=regression", "--format=json")
        self.assertEqual((same.returncode, same.stderr), (0, ""))
        self.assertEqual(json.loads(same.stdout)["baseline"]["regressions"], [])
        for finding in baseline["findings"]:
            if finding["id"] in ("codex.path", "claude.path"):
                finding["status"] = "pass"
        path.write_text(json.dumps(baseline), encoding="utf-8")
        worse = self.cli("--no-version", "--baseline", str(path), "--fail-on=regression", "--format=sarif")
        self.assertEqual((worse.returncode, worse.stderr), (1, ""))
        invocation = json.loads(worse.stdout)["runs"][0]["invocations"][0]
        self.assertEqual(invocation["exitCode"], 1)
        self.assertEqual(invocation["properties"]["baseline"]["regressions"], ["claude.path", "codex.path"])
        path.write_text("bad", encoding="utf-8")
        bad = self.cli("--baseline", str(path), "--format=sarif")
        self.assertEqual((bad.returncode, bad.stdout), (2, ""))


class DiagnosisCSVTests(IntegrationFixture):
    def rows(self, report):
        text = diagnosis_csv(report)
        self.assertTrue(text.startswith("\ufeff"))
        self.assertNotIn("\r", text)
        return list(csv.reader(io.StringIO(text[1:])))

    def test_ten_columns_union_sequence_removed_rows_and_unchanged_baseline(self):
        report = diagnosis(item("codex.version", "warn", version="2.0.0"), item("claude.path", "pass", installation_groups=0, scan_limited=False), item("system.platform", "pass"))
        old = project(source(item("codex.version", "pass", version="1.0.0"), item("wsl.internal", "pass"), item("system.platform", "pass")))
        report["baseline"] = baseline_report(old, project(report))
        rows = self.rows(report)
        self.assertEqual(rows[0], list(DIAGNOSIS_COLUMNS))
        self.assertEqual(rows[1:], [
            ["1", "claude.path", "claude", "pass", "", "0", "false", "added", "", "false"],
            ["2", "codex.version", "codex", "warn", "2.0.0", "", "", "changed", "pass", "true"],
            ["3", "system.platform", "system", "pass", "", "", "", "unchanged", "pass", "false"],
            ["4", "wsl.internal", "wsl", "", "", "", "", "removed", "pass", "false"],
        ])

    def test_missing_zero_false_numeric_bounds_empty_and_bilingual_bytes(self):
        report = diagnosis(item("claude.path", installation_groups=0, scan_limited=False), item("codex.path"),
                           item("codex.version", version="1.2.3"), item("claude.dependency", version="=PRIVATE"))
        rows = self.rows(report)
        self.assertEqual(rows[2][5:], ["0", "false", "", "", ""])
        self.assertEqual(rows[3][4:], ["", "", "", "", "", ""])
        self.assertEqual(rows[4][4], "1.2.3")
        report["language"] = "en"
        self.assertEqual(diagnosis_csv(report), diagnosis_csv({**report, "language": "zh"}))
        self.assertEqual(self.rows(diagnosis()), [list(DIAGNOSIS_COLUMNS)])
        for value in (0, 32):
            self.assertEqual(self.rows(diagnosis(item("codex.path", installation_groups=value)))[1][5], str(value))

    def test_formula_prefixes_and_ignored_text_never_reach_any_cell(self):
        for prefix in ("=", "+", "-", "@"):
            marker = prefix + "SYNTHETIC_PRIVATE"
            report = diagnosis(item("codex.version", version=marker, path=marker), item("codex.path", path=marker))
            report.update({"summary": marker, "generated_at": marker, "language": marker})
            for finding in report["findings"]:
                finding["summary"] = marker
            self.assertTrue(all(not cell.startswith(("=", "+", "-", "@")) and "SYNTHETIC_PRIVATE" not in cell for row in self.rows(report) for cell in row))

    def test_real_csv_stdout_is_pure_bom_lf_and_bilingual(self):
        zh = self.cli("--no-version", "--format=csv", "--lang=zh")
        en = self.cli("--no-version", "--format=csv", "--lang=en")
        self.assertEqual((zh.returncode, en.returncode, zh.stderr, en.stderr), (0, 0, "", ""))
        self.assertEqual(zh.stdout, en.stdout)
        self.assertEqual(next(csv.reader(io.StringIO(zh.stdout[1:]))), list(DIAGNOSIS_COLUMNS))


class SarifTests(IntegrationFixture):
    def test_all_rules_match_catalog_metadata_and_result_indices_levels(self):
        report = diagnosis(*(item(check_id, state) for check_id, state in zip(
            ("codex.path", "claude.version", "system.platform", "wsl.internal", "scope.unchecked"), STATES)))
        run = sarif_document(report)["runs"][0]
        rules = run["tool"]["driver"]["rules"]
        self.assertEqual(len(rules), 19)
        self.assertEqual(run["tool"]["driver"]["semanticVersion"], "0.6.0")
        for rule, check in zip(rules, catalog_report()["checks"]):
            self.assertEqual(rule["id"], check["id"])
            self.assertEqual(rule["shortDescription"]["text"], check["purpose"]["zh"])
            self.assertEqual(rule["fullDescription"]["text"], check["limitation"]["zh"])
            self.assertEqual(rule["help"]["text"], check["limitation"]["zh"])
            self.assertEqual(rule["properties"], {k: check[k] for k in ("target", "availability", "evidence_fields")})
            self.assertEqual(rule["defaultConfiguration"], {"level": "warning"})
        self.assertEqual([(r["ruleId"], r["level"]) for r in run["results"]],
                         [("claude.version", "warning"), ("system.platform", "error"), ("wsl.internal", "note")])
        for result in run["results"]:
            self.assertEqual(rules[result["ruleIndex"]]["id"], result["ruleId"])
        self.assertEqual(run["invocations"][0]["properties"]["summary"], dict.fromkeys(STATES, 1))

    def test_scan_limits_baseline_properties_and_exit_code_zero_one(self):
        for matched in (False, True):
            report = diagnosis(item("codex.path", "warn", scan_limited=True), item("claude.path", "pass", scan_limited=True), matched=matched)
            report["baseline"] = baseline_report({}, project(report))
            invocation = sarif_document(report)["runs"][0]["invocations"][0]
            self.assertIs(invocation["executionSuccessful"], True)
            self.assertEqual(invocation["exitCode"], int(matched))
            self.assertEqual(invocation["properties"]["scan_limited_checks"], ["claude.path", "codex.path"])
            self.assertEqual(invocation["properties"]["baseline"], {"summary": {"added": 2, "removed": 0, "changed": 0}, "unchanged": 0, "regressions": []})
            self.assertTrue(sarif_document(report)["runs"][0]["results"][0]["properties"]["scan_limited"])

    def test_determinism_no_evidence_paths_time_or_external_references_and_bilingual_structure(self):
        outputs = []
        for lang in ("zh", "en"):
            report = diagnosis(item("codex.version", "unknown", path="Z:/SYNTHETIC_PRIVATE", version="1.2.3"), lang=lang)
            text = sarif_report(report)
            self.assertEqual(text, sarif_report(report))
            self.assertTrue(text.endswith("\n"))
            self.assertFalse(text.startswith("\ufeff"))
            self.assertNotIn("\r", text)
            for forbidden in ('"locations"', '"artifacts"', '"generated_at"', '"$ref"', '"evidence"', "SYNTHETIC_PRIVATE", "2000-01-01"):
                self.assertNotIn(forbidden, text)
            document = json.loads(text)
            self.assertEqual(document["version"], "2.1.0")
            self.assertEqual(len(document["runs"]), 1)
            self.assertNotIn("baseline", document["runs"][0]["invocations"][0]["properties"])
            outputs.append(document)
        def structure(obj):
            if isinstance(obj, dict): return {key: structure(value) for key, value in obj.items()}
            if isinstance(obj, list): return [structure(value) for value in obj]
            return type(obj).__name__
        self.assertEqual(structure(outputs[0]), structure(outputs[1]))
        self.assertEqual([r["ruleId"] for r in outputs[0]["runs"][0]["results"]], [r["ruleId"] for r in outputs[1]["runs"][0]["results"]])

    def test_csv_sarif_collisions_and_partial_write_error_interrupt_cleanup(self):
        original = Path.open
        for fmt in ("csv", "sarif"):
            folder = self.root / fmt
            folder.mkdir()
            existing = folder / ("report.zh." + fmt)
            existing.write_bytes(b"keep")
            with patch.object(cli, "Doctor") as doctor:
                doctor.return_value.run.return_value = diagnosis(item())
                self.assertEqual(self.invoke(["--format", fmt, "--output-dir", folder])[0], 2)
            self.assertEqual(existing.read_bytes(), b"keep")
            existing.unlink()
            for exception, code in ((OSError, 2), (KeyboardInterrupt, 130)):
                class Interrupted:
                    def __init__(self, stream): self.stream = stream
                    def __enter__(self): self.stream.__enter__(); return self
                    def __exit__(self, *args): return self.stream.__exit__(*args)
                    def write(self, text): self.stream.write(text[:10]); raise exception()
                def guarded(p, *args, **kwargs):
                    stream = original(p, *args, **kwargs)
                    return Interrupted(stream) if p == existing else stream
                keep = folder / "other.txt"
                keep.write_bytes(b"keep")
                with patch.object(Path, "open", guarded), patch.object(cli, "Doctor") as doctor:
                    doctor.return_value.run.return_value = diagnosis(item())
                    self.assertEqual(self.invoke(["--format", fmt, "--output-dir", folder])[0], code)
                self.assertEqual(list(folder.iterdir()), [keep])
            keep.unlink()
            for lang in ("zh", "en"):
                with patch.object(cli, "Doctor") as doctor:
                    doctor.return_value.run.return_value = diagnosis(item(), lang=lang)
                    self.assertEqual(self.invoke(["--format", fmt, "--lang", lang, "--output-dir", folder]), (0, "", ""))
                content = (folder / f"report.{lang}.{fmt}").read_bytes()
                self.assertEqual(content.startswith(b"\xef\xbb\xbf"), fmt == "csv")
                self.assertNotIn(b"\r", content)

    def test_sarif_is_diagnosis_only_and_invalid_modes_do_not_read(self):
        path = self.root / "input.json"
        with ExitStack() as stack:
            for name in ("Doctor", "load_report", "load_history", "verify_support"):
                stack.enter_context(patch.object(cli, name, side_effect=AssertionError("read before validation")))
            for mode in (["--compare", path, path], ["--history", path, path], ["--validate", path],
                         ["--verify-support", path], ["--support", path], ["--catalog"], ["--schema"]):
                self.assertEqual(self.invoke([*mode, "--format=sarif"])[0:2], (2, ""))


class BaselineRequiredLinks(IntegrationFixture):
    def assert_link(self, directory=False, junction=False):
        target = self.root / "target"
        target.mkdir()
        content = target / "input.json"
        content.write_text(json.dumps(source(item())), encoding="utf-8")
        link = self.root / ("ancestor" if directory else "file.json")
        with ExitStack() as stack:
            if junction:
                stack.enter_context(test_boundaries.BoundaryTests.junction(self, target, name=link.name))
            else:
                try:
                    link.symlink_to(target if directory else content, target_is_directory=directory)
                except OSError as exc:
                    self.fail(f"Required baseline real symlink needs authorized privilege (winerror {exc.winerror}); acceptance blocked")
                self.assertEqual(link.lstat().st_reparse_tag, 0xA000000C)
                self.link_evidence = [{"kind": "directory_symlink" if directory else "file_symlink", "reparse_tag": hex(link.lstat().st_reparse_tag), "descendant_access_attempts": 0}]
            self.link_evidence[-1]["content_read_attempts"] = 0
            original = Path.open
            def guarded(p, *args, **kwargs):
                if p in (content, link) or p.is_relative_to(link):
                    self.link_evidence[-1]["content_read_attempts"] += 1
                    self.fail("baseline link content read")
                return original(p, *args, **kwargs)
            stack.enter_context(patch.object(Path, "open", guarded))
            stack.enter_context(patch.object(cli, "Doctor", side_effect=AssertionError("diagnosis on rejected baseline")))
            if directory:
                stack.enter_context(test_boundaries.BoundaryTests.no_descendant_access(self, link))
            self.assertEqual(self.invoke(["--baseline", link / "input.json" if directory else link, "--format=csv"])[0:2], (2, ""))

    def test_baseline_file_real_symlink_zero_target_reads(self): self.assert_link()
    def test_baseline_ancestor_real_symlink_zero_descendant_access(self): self.assert_link(directory=True)
    def test_baseline_ancestor_real_junction_zero_descendant_access(self): self.assert_link(directory=True, junction=True)
