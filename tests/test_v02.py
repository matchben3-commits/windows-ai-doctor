"""Behavioral regressions for offline import, export and evidence-based advice."""
import copy
import io
import json
import os
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from test_doctor import DoctorFixture, finding, ROOT
import test_boundaries
from windows_ai_doctor import cli
from windows_ai_doctor.compare import load_report, compare_reports, MAX_BYTES, MAX_FINDINGS
from windows_ai_doctor.guidance import guidance, priorities
from windows_ai_doctor.report import html_report, json_report, markdown_report


def source(*findings):
    return {"schema_version": "1.0", "findings": list(findings)}


def item(id="codex.version", status="pass", **evidence):
    return {"id": id, "status": status, "evidence": evidence}


class V02Tests(DoctorFixture):
    def write(self, obj, name="input.json"):
        path = self.root / name
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return path

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main(args)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_all_and_html_formats_bilingual_keep_both_contract(self):
        for lang in ("zh", "en"):
            for fmt, extensions in (("all", {"md", "json", "html"}), ("both", {"md", "json"}), ("html", {"html"})):
                dest = self.root / (fmt + lang)
                p = self.cli("--no-version", "--format", fmt, "--lang", lang, "--output-dir", str(dest))
                self.assertEqual(p.returncode, 0)
                self.assertEqual({f.suffix[1:] for f in dest.iterdir()}, extensions)
                for f in dest.iterdir():
                    self.assertNotIn(str(self.home), f.read_text(encoding="utf-8"))
        a, b = self.cli("--no-version"), self.cli("--no-version", "--format", "both")
        self.assertTrue(a.stdout.startswith("# Windows AI Doctor"))
        self.assertTrue(b.stdout.startswith("# Windows AI Doctor"))

    def test_export_preserves_existing_and_cleans_partial_files(self):
        dest = self.root / "export"
        dest.mkdir()
        existing = dest / "report.zh.json"
        existing.write_bytes(b"ORIGINAL")
        self.assertEqual(self.cli("--format", "all", "--output-dir", str(dest)).returncode, 2)
        self.assertEqual(list(dest.iterdir()), [existing])
        self.assertEqual(existing.read_bytes(), b"ORIGINAL")
        existing.unlink()
        original = Path.open
        def failing(path, *args, **kwargs):
            if path.name == "report.zh.json":
                raise OSError("SYNTHETIC_PRIVATE_EXCEPTION")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", failing), redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(OSError):
                cli.export_reports({"md": "first", "json": "second"}, dest, "report", "zh")
        self.assertEqual(list(dest.iterdir()), [])
        self.assertNotIn("SYNTHETIC_PRIVATE", err.getvalue())
        self.assertIn("new files removed", err.getvalue())

    def test_export_interrupt_cleans_created_files_and_exits_130(self):
        path = self.write(source(item(status="error")))
        original = Path.open
        def interrupt(path, *args, **kwargs):
            if path.name == "comparison.zh.json":
                raise KeyboardInterrupt()
            return original(path, *args, **kwargs)
        dest = self.root / "interrupted"
        with patch.object(Path, "open", interrupt):
            code, out, err = self.invoke(["--compare", str(path), str(path), "--format", "all", "--output-dir", str(dest)])
        self.assertEqual(code, 130)
        self.assertEqual(list(dest.iterdir()), [])

    def test_compare_ignores_language_time_path_and_all_arbitrary_text(self):
        a = source(item(version="1.2.3"), item("codex.path", installation_groups=1, scan_limited=False))
        b = copy.deepcopy(a)
        for obj, lang, ref in ((a, "zh", "<PATH:1>"), (b, "en", "<PATH:999>")):
            obj.update(language=lang, generated_at=lang, summary="SYNTHETIC_PRIVATE_SUMMARY")
            for f in obj["findings"]:
                f.update(summary="SYNTHETIC_PRIVATE_TEXT", recommendation="SYNTHETIC_PRIVATE_TEXT")
                f["evidence"].update(path=ref, url="https://example.invalid/SYNTHETIC_PRIVATE_URL")
        result = compare_reports(load_report(self.write(a)), load_report(self.write(b, "new.json")))
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["unchanged"], 2)
        for render in (json_report, markdown_report, html_report):
            self.assertNotIn("SYNTHETIC_PRIVATE", render(result))
            self.assertNotIn("example.invalid", render(result))

    def test_compare_versions_groups_limits_and_status_transitions(self):
        a = source(item(version="1.2.3"), item("codex.path", installation_groups=2, scan_limited=False),
                   item("codex.config.user", "error"), item("claude.version", "error"),
                   item("wsl.running", "error"), item("claude.config.user", "error"))
        b = source(item(version="1.2.4"), item("codex.path", installation_groups=1, scan_limited=True),
                   item("codex.config.user", "unknown"), item("claude.version", "skipped"),
                   item("claude.config.user", "pass"), item("wsl.internal", "skipped"))
        result = compare_reports(load_report(self.write(a)), load_report(self.write(b, "new.json")))
        c = {v["id"]: v for v in result["changes"]}
        self.assertEqual(c["codex.version"]["details"]["version"], {"before": "1.2.3", "after": "1.2.4"})
        self.assertTrue(c["codex.path"]["details"]["scan_limited"]["after"])
        self.assertEqual(c["codex.path"]["note"], "unassessed")
        self.assertEqual(c["codex.config.user"]["note"], "unassessed")
        self.assertEqual(c["claude.version"]["note"], "unassessed")
        self.assertEqual(c["wsl.running"]["note"], "removed")
        self.assertEqual(c["wsl.internal"]["change"], "added")
        self.assertEqual(c["claude.config.user"]["note"], "passes_now")
        self.assertEqual(result["summary"], {"added": 1, "removed": 1, "changed": 5})

    def test_compare_never_invokes_diagnostics_or_follows_embedded_paths(self):
        a = source(item(status="error", path="Z:/SYNTHETIC_PRIVATE_PATH", version="1.2.3"))
        path = self.write(a)
        forbidden = lambda *a, **k: self.fail("comparison invoked a diagnostic or network probe")
        with ExitStack() as stack:
            for target in ("windows_ai_doctor.cli.Doctor", "subprocess.Popen", "socket.socket", "windows_ai_doctor.core.registered_distributions"):
                stack.enter_context(patch(target, forbidden))
            original = Path.lstat
            def guard(p, *a, **k):
                self.assertNotIn("SYNTHETIC_PRIVATE_PATH", str(p))
                return original(p, *a, **k)
            stack.enter_context(patch.object(Path, "lstat", guard))
            for fmt in ("md", "json", "html", "all", "both"):
                code, out, err = self.invoke(["--compare", str(path), str(path), "--format", fmt])
                self.assertEqual((code, err), (0, ""))
                self.assertNotIn("SYNTHETIC_PRIVATE", out)

    def test_compare_conflicting_options_and_abbreviations_exit_2(self):
        path = self.write(source())
        for options in (("--no-version",), ("--timeout=1",), ("--tools", "codex"), ("--home", str(self.home)),
                        ("--project", str(self.home)), ("--wsl-list",), ("--hom", str(self.home))):
            code, out, err = self.invoke(["--compare", str(path), str(path), *options])
            self.assertEqual(code, 2)
            self.assertNotIn(str(self.home), out + err)

    def test_import_rejects_invalid_shapes_ids_status_and_count(self):
        invalid = [[], {}, source(1), source(item("malicious<script>")), source(item(status="SYNTHETIC_PRIVATE")),
                   source(item(), item()), source(item(evidence={})), source(*[item()] * (MAX_FINDINGS + 1)),
                   {"schema_version": "2.0", "findings": []}, {"schema_version": "1.0", "report_type": "comparison", "findings": []},
                   source(item("codex.path", installation_groups=True)), source(item("codex.path", installation_groups=33)),
                   source(item("codex.path", scan_limited="true"))]
        invalid[6]["findings"][0]["evidence"] = []
        for obj in invalid:
            path = self.write(obj)
            code, out, err = self.invoke(["--compare", str(path), str(path)])
            self.assertEqual(code, 2)
            self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
            self.assertNotIn("malicious", out + err)

    def test_import_rejects_duplicate_keys_deep_huge_and_nonfinite_json(self):
        for text in ('{"schema_version":"1.0","schema_version":"1.0","findings":[]}',
                     '{"schema_version":"1.0","findings":[],"extra":{"a":1,"a":2}}',
                     '{"schema_version":"1.0","findings":[],"extra":NaN}',
                     '{"schema_version":"1.0","findings":[],"extra":1e999}',
                     '[' * 100 + '0' + ']' * 100, '{bad SYNTHETIC_PRIVATE_TEXT',
                     '{"extra":' + '1' * 1000 + '}', ' ' * (MAX_BYTES + 1)):
            p = self.root / "bad.json"
            p.write_text(text, encoding="utf-8")
            code, out, err = self.invoke(["--compare", str(p), str(p)])
            self.assertEqual(code, 2)
            self.assertNotIn("SYNTHETIC_PRIVATE", out + err)

    def test_import_node_string_budgets_apply_to_ignored_fields(self):
        for extra in ([None] * 20001, "a" * 32769):
            p = self.write({**source(), "ignored": extra})
            with self.assertRaises(ValueError):
                load_report(p)

    def test_import_version_tags_are_not_exported(self):
        a = self.write(source(item(version="1.2.3-SYNTHETIC_PRIVATE")))
        b = self.write(source(item(version="1.2.4")), "b.json")
        result = compare_reports(load_report(a), load_report(b))
        self.assertEqual(result["changes"][0]["details"]["version"], {"before": None, "after": "1.2.4"})
        self.assertNotIn("SYNTHETIC_PRIVATE", json_report(result))

    def test_html_escapes_dynamic_text_and_has_no_active_resource_tags(self):
        report = self.doctor(versions=False)
        payload = '<script>window.injected=1</script><img src="https://example.invalid" onerror="alert(1)">`'
        f = report["findings"][0]
        f["summary"] = payload
        f["evidence"]["test"] = payload
        f["guidance"]["steps"] = [payload]
        output = html_report(report)
        self.assertIn("&lt;script&gt;", output)
        tags = []
        class Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                tags.append(tag)
                self_check = [name for name, value in attrs if name.startswith("on") or name in ("src", "href")]
                if self_check:
                    raise AssertionError("active attribute found")
        Parser().feed(output)
        self.assertFalse(set(tags) & {"script", "link", "img", "iframe", "object", "base", "form"})
        self.assertIn("Content-Security-Policy", output)

    def test_guidance_distinguishes_missing_blocked_and_unsupported_node(self):
        scenarios = [("codex.path", "warn", {"cmd_path_candidate": None}, "missing"),
                     ("codex.path", "warn", {"cmd_path_candidate": "<PATH:1>", "entries": [{"path": "<PATH:1>", "path_access": "blocked"}]}, "blocked"),
                     ("codex.path", "warn", {"cmd_path_candidate": "<PATH:1>", "installation_groups": 2}, "multiple"),
                     ("codex.install", "unknown", {"kind": "unknown"}, "wrapper"),
                     ("codex.dependency", "error", {"runtime": "node", "node_path_check": "missing"}, "node_missing"),
                     ("codex.dependency", "unknown", {"runtime": "node", "node_path_check": "blocked"}, "node_unknown"),
                     ("codex.dependency", "error", {"runtime": "node", "version": "1.0.0"}, "node_old"),
                     ("codex.version", "unknown", {"reason": "timeout"}, "timeout"),
                     ("codex.version", "unknown", {"reason": "nonzero_exit"}, "nonzero"),
                     ("codex.config.user", "error", {"syntax": "invalid"}, "config_bad"),
                     ("wsl.internal", "skipped", {}, "wsl")]
        for id, status, evidence, code in scenarios:
            for lang in ("zh", "en"):
                g = guidance(item(id, status, **evidence), lang)
                self.assertEqual(g["code"], code)
                self.assertTrue(g["steps"] and g["basis"] and g["limitation"])
        report = self.doctor(versions=False)
        self.assertEqual(report["priorities"], priorities(report["findings"]))
        for f in report["findings"]:
            self.assertEqual(f["recheck"], " ".join(f["guidance"]["steps"]))
            for render in (markdown_report, html_report):
                self.assertIn(f["guidance"]["limitation"], render(report))

    def test_read_old_v01_report_without_guidance(self):
        path = ROOT / "examples/review-fixes/zh/report.zh.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(original["doctor_version"], "0.1.0")
        safe = load_report(path)
        self.assertTrue(safe)
        self.assertEqual(compare_reports(safe, safe)["changes"], [])


class CompareJunctionTests(DoctorFixture):
    def test_report_file_symlink_is_rejected_without_reading_target(self):
        target = self.root / "synthetic-auth.json"
        target.write_text('{"private":"SYNTHETIC_PRIVATE_AUTH"}', encoding="utf-8")
        link = self.root / "report.json"
        try:
            link.symlink_to(target)
        except OSError:
            self.fail("Required file-symlink fixture needs user-authorized privilege; acceptance blocked")
        self.assertEqual(link.lstat().st_reparse_tag, 0xA000000C)
        audit = {"kind": "file_symlink", "reparse_tag": hex(link.lstat().st_reparse_tag), "content_read_attempts": 0}
        self.link_evidence = [audit]
        original = Path.open
        def guarded(p, *a, **k):
            if p in (link, target):
                audit["content_read_attempts"] += 1
                self.fail("import opened linked content")
            return original(p, *a, **k)
        with patch.object(Path, "open", guarded):
            with self.assertRaises(ValueError):
                load_report(link)

    def test_report_ancestor_junction_is_rejected_before_descendant_access(self):
        if os.name != "nt":
            self.skipTest("Windows junction regression")
        target = self.root / "target"
        target.mkdir()
        (target / "old.json").write_text(json.dumps(source()), encoding="utf-8")
        with test_boundaries.BoundaryTests.junction(self, target) as link:
            with test_boundaries.BoundaryTests.no_descendant_access(self, link):
                with self.assertRaises(ValueError):
                    load_report(link / "old.json")

    def test_nonlocal_report_rejected_before_metadata(self):
        if os.name != "nt":
            self.skipTest("Windows path regression")
        with patch.object(Path, "lstat", side_effect=AssertionError("remote metadata access")):
            with self.assertRaises(ValueError):
                load_report(Path(r"\\invalid-host\share\report.json"))
