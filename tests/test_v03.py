"""Adversarial behavior tests for history, support privacy and exit policies."""
import copy
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from test_doctor import DoctorFixture, ROOT
from test_v02 import source, item
from windows_ai_doctor import cli
from windows_ai_doctor.compare import IDS, MAX_BYTES, load_report
from windows_ai_doctor.history import history_report, load_history
from windows_ai_doctor.report import html_report, markdown_report, json_report


class V03Tests(DoctorFixture):
    def write(self, obj, name="input.json"):
        path = self.root / name
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return path

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main([str(v) for v in args])
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_history_three_runs_unknown_pass_and_scope_loss(self):
        inputs = [source(item(status="error"), item("codex.path", "error", scan_limited=False), item("wsl.running", "error")),
                  source(item(status="unknown"), item("codex.path", "pass", scan_limited=True)),
                  source(item(status="pass"), item("codex.path", "skipped"), item("wsl.internal", "skipped"))]
        paths = [self.write(obj, str(n) + ".json") for n, obj in enumerate(inputs)]
        doc = history_report(load_history(paths))
        self.assertEqual([r["sequence"] for r in doc["snapshots"]], [1, 2, 3])
        changes = [{c["id"]: c for c in step["changes"]} for step in doc["transitions"]]
        self.assertEqual(changes[0]["codex.version"]["note"], "unassessed")
        self.assertEqual(changes[0]["codex.path"]["note"], "unassessed")
        self.assertEqual(changes[0]["wsl.running"]["note"], "removed")
        self.assertEqual(changes[1]["codex.version"]["note"], "passes_now")
        self.assertEqual(changes[1]["wsl.internal"]["change"], "added")
        self.assertEqual(doc["summary"], {"pass": 1, "warn": 0, "error": 0, "unknown": 0, "skipped": 2})

    def test_history_ignores_timestamps_language_refs_and_private_text(self):
        obj = source(item(version="1.2.3"), item("codex.path", installation_groups=1, scan_limited=False))
        a, b = copy.deepcopy(obj), copy.deepcopy(obj)
        a.update(generated_at="2099-SYNTHETIC_PRIVATE", language="zh")
        b.update(generated_at="1900-SYNTHETIC_PRIVATE", language="en")
        for n, x in enumerate((a, b)):
            x.update(summary={"error": 999}, ignored={"html": '<script>SYNTHETIC_PRIVATE</script>'})
            for f in x["findings"]:
                f.update(summary="SYNTHETIC_PRIVATE", recommendation="SYNTHETIC_PRIVATE")
                f["evidence"].update(path=f"<PATH:{n}>", url="https://example.invalid/SYNTHETIC_PRIVATE")
        doc = history_report(load_history([self.write(a), self.write(b, "b.json")]))
        self.assertEqual(doc["transitions"][0]["changes"], [])
        self.assertEqual(doc["snapshots"][0]["summary"]["error"], 0)
        for renderer in (html_report, markdown_report, json_report):
            self.assertNotIn("SYNTHETIC_PRIVATE", renderer(doc))
            self.assertNotIn("example.invalid", renderer(doc))

    def test_history_versions_counts_and_limits_are_observed(self):
        a = self.write(source(item(version="1.2.3"), item("codex.path", installation_groups=1, scan_limited=False)))
        b = self.write(source(item(version="1.2.4"), item("codex.path", installation_groups=2, scan_limited=True)), "b.json")
        doc = history_report(load_history([a, b]))
        changes = {c["id"]: c["details"] for c in doc["transitions"][0]["changes"]}
        self.assertEqual(changes["codex.version"]["version"], {"before": "1.2.3", "after": "1.2.4"})
        self.assertEqual(changes["codex.path"]["installation_groups"]["after"], 2)
        self.assertTrue(changes["codex.path"]["scan_limited"]["after"])

    def test_history_twenty_accepted_twentyone_rejected_before_reads(self):
        path = self.write(source(item()))
        code, out, err = self.invoke(["--history", *([path] * 20), "--format", "json"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(json.loads(out)["snapshots"]), 20)
        with patch("windows_ai_doctor.history.load_report", side_effect=AssertionError("must not read")):
            for paths in ([path], [path] * 21):
                self.assertEqual(self.invoke(["--history", *paths])[0], 2)

    def test_history_bilingual_all_formats_and_stdout(self):
        path = self.write(source(item(status="error")))
        for lang in ("zh", "en"):
            dest = self.root / lang
            self.assertEqual(self.invoke(["--history", path, path, "--lang", lang, "--format", "all", "--output-dir", dest])[0], 0)
            self.assertEqual({p.name for p in dest.iterdir()}, {f"history.{lang}.{ext}" for ext in ("md", "json", "html")})
            for fmt, prefix in (("both", "# Windows"), ("all", "# Windows"), ("json", "{"), ("html", "<!doctype")):
                code, out, err = self.invoke(["--history", path, path, "--lang", lang, "--format", fmt])
                self.assertEqual((code, err), (0, ""))
                self.assertTrue(out.startswith(prefix))

    def test_offline_modes_never_scan_execute_network_or_embedded_paths(self):
        path = self.write(source(item(path="Z:/SYNTHETIC_PRIVATE", version="1.2.3")))
        with ExitStack() as stack:
            for target in ("windows_ai_doctor.cli.Doctor", "subprocess.Popen", "socket.socket", "windows_ai_doctor.core.registered_distributions"):
                stack.enter_context(patch(target, side_effect=AssertionError("offline violation")))
            original = Path.lstat
            def guard(p, *a, **kw):
                self.assertNotIn("SYNTHETIC_PRIVATE", str(p))
                return original(p, *a, **kw)
            stack.enter_context(patch.object(Path, "lstat", guard))
            for opts in (["--history", path, path, "--format", "all"],
                         ["--support", path, "--output-dir", self.root / "bundle"]):
                code, out, err = self.invoke(opts)
                self.assertEqual((code, err), (0, ""))
                self.assertNotIn("SYNTHETIC_PRIVATE", out)

    def test_offline_conflicts_rejected_before_input_read(self):
        path = self.root / "SYNTHETIC_PRIVATE-missing.json"
        with patch("windows_ai_doctor.cli.load_report", side_effect=AssertionError("must not read")), patch("windows_ai_doctor.cli.load_history", side_effect=AssertionError("must not read")):
            for mode in (["--history", path, path], ["--support", path, "--output-dir", self.root / "out"]):
                for extra in (["--home", self.home], ["--tools", "codex"], ["--timeout=1"], ["--no-version"], ["--wsl-list"], ["--project", self.home], ["--fail-on", "warn"]):
                    code, out, err = self.invoke([*mode, *extra])
                    self.assertEqual(code, 2)
                    self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
            for opts in (["--history", path, path, "--compare", path, path], ["--history", path, path, "--support", path],
                         ["--support", path], ["--support", path, "--output-dir", self.root, "--lang=zh"],
                         ["--support", path, "--output-dir", self.root, "--format=both"], ["--compare", path, path, "--fail-on", "error"]):
                self.assertEqual(self.invoke(opts)[0], 2)

    def test_derived_json_types_rejected_by_all_importing_modes(self):
        for kind in ("comparison", "history", "support"):
            path = self.write({**source(item()), "report_type": kind})
            for opts in (["--history", path, path], ["--compare", path, path], ["--support", path, "--output-dir", self.root / kind]):
                self.assertEqual(self.invoke(opts)[0], 2)

    def test_new_import_modes_reject_schema_ids_statuses_and_duplicate_findings(self):
        invalid = [[], {}, source(item("SYNTHETIC_PRIVATE")), source(item(status="invalid")), source(item(), item()),
                   {"schema_version": "1.1", "findings": []}, source(item("codex.path", installation_groups=True)),
                   source(item("codex.path", scan_limited=1)), source(item("codex.path", installation_groups=-1))]
        for obj in invalid:
            path = self.write(obj)
            for opts in (["--history", path, path], ["--support", path, "--output-dir", self.root / "invalid"]):
                code, out, err = self.invoke(opts)
                self.assertEqual(code, 2)
                self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
        self.assertFalse((self.root / "invalid").exists())

    def test_new_modes_reject_duplicate_keys_budgets_and_invalid_json(self):
        texts = ['{"schema_version":"1.0","findings":[],"x":{"a":1,"a":2}}',
                 '[' * 17 + '0' + ']' * 17, ' ' * (MAX_BYTES + 1),
                 json.dumps({**source(), "x": [0] * 20001}), json.dumps({**source(), "x": "x" * 32769}),
                 '{"schema_version":"1.0","findings":[],"x":Infinity}', '{bad SYNTHETIC_PRIVATE']
        path = self.root / "bad.json"
        for text in texts:
            path.write_text(text, encoding="utf-8")
            for opts in (["--history", path, path], ["--support", path, "--output-dir", self.root / "invalid"]):
                code, out, err = self.invoke(opts)
                self.assertEqual(code, 2)
                self.assertNotIn("SYNTHETIC_PRIVATE", out + err)

    def test_support_zip_fixed_members_crc_hashes_whitelist_and_privacy(self):
        payload = source(item(version="1.2.3"), item("codex.path", "warn", installation_groups=2, scan_limited=True))
        payload.update(generated_at="SYNTHETIC_PRIVATE_TIME", summary={"pass": 900}, unknown="SYNTHETIC_PRIVATE")
        for f in payload["findings"]:
            f.update(summary="SYNTHETIC_PRIVATE", recommendation="SYNTHETIC_PRIVATE", target="SYNTHETIC_PRIVATE")
            f["evidence"].update(path="C:/SYNTHETIC_PRIVATE", url="https://example.invalid/SYNTHETIC_PRIVATE", html='<img src="SYNTHETIC_PRIVATE">')
        path = self.write(payload)
        before = path.read_bytes()
        dest = self.root / "bundle"
        code, out, err = self.invoke(["--support", path, "--output-dir", dest])
        self.assertEqual((code, err), (0, ""))
        with zipfile.ZipFile(dest / "support-bundle.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {"summary.zh.md", "summary.en.md", "support.json", "PRIVACY.txt", "SHA256SUMS.txt"})
            data = {n: archive.read(n) for n in archive.namelist()}
            for n, raw in data.items():
                self.assertNotIn(b"SYNTHETIC_PRIVATE", raw)
                self.assertNotIn(b"example.invalid", raw)
            for line in data["SHA256SUMS.txt"].decode().splitlines():
                digest, name = line.split("  ")
                self.assertEqual(hashlib.sha256(data[name]).hexdigest(), digest)
            doc = json.loads(data["support.json"])
            self.assertEqual(doc["report_type"], "support")
            self.assertEqual(doc["summary"]["pass"], 1)
            self.assertEqual(doc["summary"]["warn"], 1)
            self.assertNotIn("generated_at", doc)
            self.assertIn("有限摘要", data["summary.zh.md"].decode())
            self.assertIn("linkable", data["summary.en.md"].decode())
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn("SYNTHETIC_PRIVATE", out)
        support_input = self.root / "support.json"
        support_input.write_bytes(data["support.json"])
        self.assertEqual(self.invoke(["--history", support_input, path])[0], 2)

    def test_support_drops_free_form_versions_and_recomputes_summary(self):
        path = self.write(source(item(version="1.2.3-SYNTHETIC_PRIVATE")))
        self.assertEqual(self.invoke(["--support", path, "--output-dir", self.root / "out"])[0], 0)
        with zipfile.ZipFile(self.root / "out/support-bundle.zip") as archive:
            doc = json.loads(archive.read("support.json"))
            self.assertIsNone(doc["findings"][0]["evidence"]["version"])
            self.assertNotIn(b"SYNTHETIC_PRIVATE", archive.read("support.json"))

    def test_support_collision_and_midwrite_failure_preserve_old_files(self):
        path = self.write(source(item()))
        dest = self.root / "out"
        dest.mkdir()
        old = dest / "keep.txt"
        old.write_bytes(b"KEEP")
        self.assertEqual(self.invoke(["--support", path, "--output-dir", dest])[0], 0)
        bundle = dest / "support-bundle.zip"
        before = bundle.read_bytes()
        self.assertEqual(self.invoke(["--support", path, "--output-dir", dest])[0], 2)
        self.assertEqual(bundle.read_bytes(), before)
        bundle.unlink()
        original = zipfile.ZipFile.writestr
        def fail(archive, name, *a, **kw):
            if name == "summary.en.md":
                raise OSError("SYNTHETIC_PRIVATE")
            return original(archive, name, *a, **kw)
        with patch.object(zipfile.ZipFile, "writestr", fail):
            code, out, err = self.invoke(["--support", path, "--output-dir", dest])
        self.assertEqual(code, 2)
        self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
        self.assertEqual(list(dest.iterdir()), [old])

    def test_history_partial_export_and_support_interrupt_cleanup(self):
        path = self.write(source(item()))
        original = Path.open
        def fail(p, *a, **kw):
            if p.name == "history.zh.json":
                raise OSError("SYNTHETIC_PRIVATE")
            return original(p, *a, **kw)
        dest = self.root / "out"
        with patch.object(Path, "open", fail):
            self.assertEqual(self.invoke(["--history", path, path, "--format", "all", "--output-dir", dest])[0], 2)
        self.assertEqual(list(dest.iterdir()), [])
        with patch.object(zipfile.ZipFile, "writestr", side_effect=KeyboardInterrupt):
            self.assertEqual(self.invoke(["--support", path, "--output-dir", dest])[0], 130)
        self.assertEqual(list(dest.iterdir()), [])

    def test_history_export_collision_preserves_existing(self):
        path = self.write(source(item()))
        dest = self.root / "out"
        dest.mkdir()
        old = dest / "history.zh.json"
        old.write_bytes(b"KEEP")
        self.assertEqual(self.invoke(["--history", path, path, "--format", "all", "--output-dir", dest])[0], 2)
        self.assertEqual(list(dest.iterdir()), [old])
        self.assertEqual(old.read_bytes(), b"KEEP")

    def test_history_html_twenty_columns_semantics_and_no_resources(self):
        path = self.write(source(*(item(id) for id in sorted(IDS))))
        doc = history_report(load_history([path] * 20))
        for lang in ("zh", "en"):
            doc["language"] = lang
            text = html_report(doc)
            self.assertIn("第20次" if lang == "zh" else "Run 20", text)
            self.assertIn("overflow-x:auto", text)
            self.assertIn('tabindex="0"', text)
            tags = []
            class Parser(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    tags.append(tag)
                    if any(k in ("src", "href") or k.startswith("on") for k, v in attrs):
                        raise AssertionError("active attribute")
            Parser().feed(text)
            self.assertFalse(set(tags) & {"script", "iframe", "img", "object", "link", "form"})
            self.assertIn("Content-Security-Policy", text)

    def test_fail_on_default_and_dedup_never_changes_findings(self):
        report = self.doctor(versions=False)
        report["summary"] = {"pass": 0, "warn": 1, "error": 0, "unknown": 1, "skipped": 0}
        before = copy.deepcopy(report["findings"])
        with patch("windows_ai_doctor.cli.Doctor") as doctor:
            doctor.return_value.run.side_effect = lambda: copy.deepcopy(report)
            for flags, expected, selected in (([], 0, ["error"]), (["--fail-on", "warn"], 1, ["warn"]),
                                             (["--fail-on", "unknown", "warn", "unknown"], 1, ["warn", "unknown"])):
                code, out, err = self.invoke(["--format", "json", *flags])
                self.assertEqual((code, err), (expected, ""))
                doc = json.loads(out)
                self.assertEqual(doc["findings"], before)
                self.assertEqual(doc["exit_policy"]["fail_on"], selected)
                self.assertEqual(doc["exit_policy"]["matched"], bool(expected))

    def test_fail_on_real_process_default_warn_unknown_and_error(self):
        for flags, expected in (([], 0), (["--fail-on", "warn"], 1), (["--fail-on", "unknown"], 1)):
            p = self.cli("--no-version", "--format", "json", *flags)
            self.assertEqual(p.returncode, expected)
            doc = json.loads(p.stdout)
            self.assertEqual(doc["exit_policy"]["matched"], bool(expected))
        config = self.home / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text("bad = [", encoding="utf-8")
        self.assertEqual(self.cli("--no-version").returncode, 1)
        self.assertEqual(self.cli("--no-version", "--fail-on", "unknown").returncode, 1)

    def test_policy_visible_in_bilingual_markdown_json_html(self):
        for lang in ("zh", "en"):
            dest = self.root / lang
            proc = self.cli("--no-version", "--lang", lang, "--format", "all", "--fail-on", "unknown", "--output-dir", str(dest))
            self.assertEqual(proc.returncode, 1)
            doc = json.loads((dest / f"report.{lang}.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["exit_policy"]["triggered"], ["unknown"])
            for fmt in ("md", "html"):
                text = (dest / f"report.{lang}.{fmt}").read_text(encoding="utf-8")
                self.assertIn("unknown", text)
                self.assertIn("无法判断不等于已确认故障" if lang == "zh" else "unknown is not a confirmed fault", text)

    def test_policy_invalid_args_and_failure_interrupt_priority(self):
        for opts in (["--fail-on", "pass"], ["--fail-on", "warn", "POSITION"], ["--fail-o", "error"], ["--fail-on"]):
            self.assertEqual(self.invoke(opts)[0], 2)
        with patch("windows_ai_doctor.cli.Doctor", side_effect=RuntimeError("SYNTHETIC_PRIVATE")):
            code, out, err = self.invoke(["--fail-on", "warn"])
            self.assertEqual(code, 2)
            self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
        with patch("windows_ai_doctor.cli.Doctor", side_effect=KeyboardInterrupt):
            self.assertEqual(self.invoke(["--fail-on", "warn"])[0], 130)
        dest = self.root / "out"
        dest.mkdir()
        (dest / "report.zh.json").write_bytes(b"KEEP")
        self.assertEqual(self.cli("--no-version", "--format", "all", "--fail-on", "warn", "--output-dir", str(dest)).returncode, 2)

    def test_history_old_v01_v02_diagnoses_remain_accepted(self):
        paths = [ROOT / "examples/review-fixes/zh/report.zh.json", ROOT / "examples/v02-complete/zh/report.zh.json"]
        self.assertEqual(self.invoke(["--history", *paths, "--format", "json"])[0], 0)

    def test_missing_and_nonlocal_inputs_hide_details(self):
        for path in (self.root / "SYNTHETIC_PRIVATE.json", Path(r"\\invalid-host\share\SYNTHETIC_PRIVATE.json")):
            for opts in (["--history", path, path], ["--support", path, "--output-dir", self.root / "out"]):
                code, out, err = self.invoke(opts)
                self.assertEqual(code, 2)
                self.assertNotIn("SYNTHETIC_PRIVATE", out + err)
