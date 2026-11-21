"""Independent npm golden files and real temporary NTFS junction regressions."""
import json
import os
import stat
import subprocess
import sys
import unittest
from contextlib import contextmanager, ExitStack
from pathlib import Path
from unittest.mock import patch

from test_doctor import DoctorFixture, finding, ROOT
from windows_ai_doctor.discovery import bounded_read, checked_stat, classify, discover, find_node, is_native
from windows_ai_doctor.npm_shims import known_wrapper
from windows_ai_doctor.report import json_report, markdown_report


class BoundaryTests(DoctorFixture):
    @contextmanager
    def junction(self, target, name="junction"):
        import _winapi
        link = self.root / name
        self.assertTrue(target.resolve().is_relative_to(self.root.resolve()))
        self.assertTrue(link.absolute().is_relative_to(self.root.resolve()))
        _winapi.CreateJunction(str(target), str(link))
        try:
            self.assertTrue(link.lstat().st_file_attributes & 0x400)
            if not hasattr(self, "link_evidence"):
                self.link_evidence = []
            self.link_evidence.append({"kind": "directory_junction", "reparse_tag": hex(link.lstat().st_reparse_tag), "descendant_access_attempts": 0})
            yield link
        finally:
            link.rmdir()  # remove only the junction, never its target

    @contextmanager
    def no_descendant_access(self, link):
        """Fail on metadata, resolution or reads past the real link itself."""
        calls = []
        def guarded(original, label):
            def invoke(path, *args, **kwargs):
                if path != link and path.is_relative_to(link):
                    if hasattr(self, "link_evidence"):
                        self.link_evidence[-1]["descendant_access_attempts"] += 1
                    raise AssertionError("access beyond rejected ancestor: " + label)
                if label == "lstat":
                    calls.append(path)
                return original(path, *args, **kwargs)
            return invoke
        with ExitStack() as stack:
            for method in ("lstat", "stat", "is_file", "open", "resolve"):
                stack.enter_context(patch.object(Path, method, guarded(getattr(Path, method), method)))
            yield calls

    def test_six_golden_wrappers_from_real_cmd_shim(self):
        for label, marker, node in (
            ("node", "node_modules/@openai/codex/bin/codex.js", True),
            ("native", "node_modules/@anthropic-ai/claude-code/claude.exe", False)):
            for suffix in (".cmd", ".ps1", ""):
                path = ROOT / "tests/fixtures" / ("npm-" + label + (suffix or ".sh") + ".txt")
                content = path.read_text(encoding="utf-8")
                self.assertTrue(known_wrapper(content, suffix, marker, node=node))
                self.assertFalse(known_wrapper(content + "\nexit 7\n", suffix, marker, node=node))
                self.assertFalse(known_wrapper("exit 7\n" + content, suffix, marker, node=node))
                self.assertFalse(known_wrapper(content[:-12], suffix, marker, node=node))
                self.assertFalse(known_wrapper(content, suffix, marker + ".other", node=node))

    def test_broken_marker_wrapper_exit7_never_queries_package(self):
        directory = self.root / "broken-wrapper"
        self.npm(directory)
        suffix = ".cmd" if os.name == "nt" else ""
        wrapper = directory / ("codex" + suffix)
        wrapper.write_text("@echo off\nrem node_modules/@openai/codex/bin/tool.js\nexit /b 7\n", encoding="utf-8")
        if os.name == "nt":
            cmd = Path(os.environ["SystemRoot"]) / "System32/cmd.exe"
            actual = subprocess.run([str(cmd), "/d", "/c", str(wrapper), "--version"],
                                    env=self.env, capture_output=True, timeout=5)
            self.assertEqual(actual.returncode, 7)
        def forbidden(*args, **kwargs):
            raise AssertionError("a broken selected wrapper must not execute its package")
        for lang in ("zh", "en"):
            report = self.doctor(tools=("codex",), lang=lang, runner=forbidden)
            self.assertEqual(finding(report, "codex.install")["evidence"]["kind"], "unknown")
            self.assertEqual(finding(report, "codex.version")["status"], "unknown")
            self.assertNotIn('"version": "1.2.3"', json_report(report) + markdown_report(report))

    def test_all_wrapper_variants_reject_marker_only_and_added_commands(self):
        directory = self.root / "variants"
        self.npm(directory)
        for suffix in (".cmd", ".ps1", ""):
            path = directory / ("codex" + suffix)
            original = path.read_text(encoding="utf-8")
            for broken in ("node_modules/@openai/codex/bin/tool.js", "exit 7\n" + original,
                           original + "\nexit 7\n", original.replace("tool.js", "absent.js")):
                path.write_text(broken, encoding="utf-8")
                entry = classify(path, "codex", [])
                self.assertEqual(entry.kind, "unknown")
                self.assertEqual(entry.argv, [])
            path.write_text(original, encoding="utf-8")

    def test_package_bin_parent_or_absolute_escape_is_unknown(self):
        directory = self.root / "escape"
        package = self.npm(directory)
        metadata = package / "package.json"
        original = json.loads(metadata.read_text(encoding="utf-8"))
        for target in ("../tool.js", "bin/../bin/tool.js", "/bin/tool.js", "bin//tool.js"):
            original["bin"]["codex"] = target
            metadata.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(Path, "resolve", side_effect=AssertionError("must not resolve")):
                entry = classify(directory / "codex.cmd", "codex", [])
            self.assertEqual(entry.kind, "unknown")
            self.assertEqual(entry.argv, [])

    def test_node_shim_cannot_be_reinterpreted_as_native_target(self):
        directory = self.root / "mismatched"
        package = self.npm(directory)
        (package / "bin/tool.js").write_bytes(b"MZ_SYNTHETIC_ONLY" if os.name == "nt" else b"\x7fELF_SYNTHETIC_ONLY")
        entry = classify(directory / ("codex.cmd" if os.name == "nt" else "codex"), "codex", [])
        self.assertEqual(entry.kind, "unknown")
        self.assertEqual(entry.argv, [])

    def test_unsupported_paths_do_not_query_metadata(self):
        paths = [self.root / "a/../b", Path("relative")]
        if os.name == "nt":
            paths.extend([Path(r"\\example.invalid\share\tool.exe"), self.root / "file:stream"])
        for path in paths:
            with patch.object(Path, "lstat", side_effect=AssertionError("must not query metadata")):
                with self.assertRaises(ValueError):
                    checked_stat(path)

    @unittest.skipUnless(os.name == "nt", "real NTFS junction test")
    def test_real_junction_blocks_config_native_discovery_and_node_before_leaf(self):
        target = self.root / "target"
        target.mkdir()
        (target / "codex.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
        (target / "node.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
        (target / "config.toml").write_text('model = "synthetic"', encoding="utf-8")
        (target / "settings.json").write_text('{}', encoding="utf-8")
        with self.junction(target) as link, self.no_descendant_access(link) as calls:
            self.assertFalse(is_native(link / "codex.exe"))
            self.assertEqual(calls, [*reversed(link.parents), link])
            with self.assertRaises(ValueError):
                bounded_read(link / "config.toml")
            self.assertEqual(classify(link / "codex.exe", "codex", []).argv, [])
            self.assertIsNone(find_node(link, []))
            self.env.update(PATH=str(link), CODEX_HOME=str(link), CLAUDE_CONFIG_DIR=str(link))
            entries, selected, _, _ = discover("codex", self.env)
            self.assertTrue(entries)
            self.assertEqual(selected.kind, "unknown")
            self.assertTrue(all(e.path_access == "blocked" and not e.argv for e in entries))
            with patch("windows_ai_doctor.core.run_bounded", side_effect=AssertionError("must not run")):
                report = self.doctor(runner=lambda *a, **kw: self.fail("must not run"))
            for tool in ("codex", "claude"):
                self.assertEqual(finding(report, tool + ".config.user")["status"], "unknown")
                self.assertEqual(finding(report, tool + ".install")["status"], "unknown")
                self.assertEqual(finding(report, tool + ".version")["status"], "unknown")
                self.assertEqual(finding(report, tool + ".path")["status"], "warn")
                self.assertTrue(all(not e["existence_verified"] for e in finding(report, tool + ".path")["evidence"]["entries"]))

    @unittest.skipUnless(os.name == "nt", "real NTFS junction test")
    def test_real_junction_package_metadata_and_bin_never_followed(self):
        for part in ("node_modules", "node_modules/@openai", "node_modules/@openai/codex", "node_modules/@openai/codex/bin"):
            directory = self.root / ("package-" + str(len(part)))
            self.npm(directory)
            origin = directory / part
            target = self.root / ("moved-" + str(len(part)))
            self.assertTrue(origin.resolve().is_relative_to(self.root.resolve()))
            self.assertTrue(target.absolute().is_relative_to(self.root.resolve()))
            origin.rename(target)
            import _winapi
            _winapi.CreateJunction(str(target), str(origin))
            try:
                with self.no_descendant_access(origin):
                    entry = classify(directory / "codex.cmd", "codex", [])
                    self.assertEqual(entry.kind, "unknown")
                    self.assertEqual(entry.argv, [])
            finally:
                origin.rmdir()

    @unittest.skipUnless(os.name == "nt", "real NTFS junction test")
    def test_real_junction_runtime_does_not_fall_through_to_later_node(self):
        directory = self.root / "runtime"
        self.npm(directory)
        target = self.root / "node-target"
        target.mkdir()
        (target / "node.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
        later = self.root / "later"
        later.mkdir()
        (later / "node.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
        with self.junction(target) as link, self.no_descendant_access(link):
            self.assertIsNone(find_node(directory, [link, later]))
            entry = classify(directory / "codex.cmd", "codex", [link, later])
            self.assertEqual(entry.kind, "npm-js")
            self.assertIsNone(entry.node)
            self.assertEqual(entry.argv, [])
            self.env["PATH"] = os.pathsep.join((str(directory), str(link), str(later)))
            report = self.doctor(tools=("codex",), runner=lambda *a, **kw: self.fail("must not run"))
            self.assertEqual(finding(report, "codex.dependency")["status"], "unknown")
            self.assertEqual(finding(report, "codex.dependency")["evidence"]["node_path_check"], "blocked")

    @unittest.skipUnless(os.name == "nt", "real NTFS junction test")
    def test_real_junction_native_package_target_is_unknown(self):
        directory = self.root / "native-package"
        package = directory / "node_modules/@anthropic-ai/claude-code"
        package.parent.mkdir(parents=True)
        target = self.root / "native-target"
        target.mkdir()
        (target / "package.json").write_text(json.dumps({"name": "@anthropic-ai/claude-code",
                                                       "bin": {"claude": "claude.exe"}}), encoding="utf-8")
        (target / "claude.exe").write_bytes(b"MZ_SYNTHETIC_ONLY")
        wrapper = (ROOT / "tests/fixtures/npm-native.cmd.txt").read_text(encoding="utf-8")
        (directory / "claude.cmd").write_text(wrapper, encoding="utf-8")
        import _winapi
        _winapi.CreateJunction(str(target), str(package))
        try:
            with self.no_descendant_access(package):
                entry = classify(directory / "claude.cmd", "claude", [])
                self.assertEqual(entry.kind, "unknown")
                self.assertEqual(entry.argv, [])
        finally:
            package.rmdir()

    @unittest.skipUnless(os.name == "nt", "real NTFS junction test")
    def test_real_junction_rejected_even_if_leaf_missing(self):
        target = self.root / "empty-target"
        target.mkdir()
        with self.junction(target) as link, self.no_descendant_access(link):
            with self.assertRaisesRegex(ValueError, "linked_path"):
                bounded_read(link / "missing/config.toml")

    def test_broken_first_node_does_not_use_later_runtime(self):
        directory = self.root / "local-runtime"
        self.npm(directory)
        (directory / ("node.exe" if os.name == "nt" else "node")).write_text("not native", encoding="utf-8")
        self.assertIsNone(find_node(directory, [Path(os.environ.get("SystemRoot", str(self.root)))]))
        entry = classify(directory / ("codex.cmd" if os.name == "nt" else "codex"), "codex", [])
        self.assertEqual(entry.argv, [])

    def test_demo_relative_destination_survives_clean_child_cwd(self):
        proc = subprocess.run([sys.executable, str(ROOT / "examples/make_demo.py"), "demo 输出"],
                              cwd=self.root, env=self.env, capture_output=True, timeout=15)
        self.assertEqual(proc.returncode, 0)
        for lang in ("zh", "en"):
            path = self.root / "demo 输出" / lang / f"report.{lang}.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(finding(report, "codex.version")["status"], "unknown")
            self.assertEqual(finding(report, "claude.config.local")["status"], "error")
            self.assertTrue(path.with_suffix(".md").is_file())

    def test_host_relative_destination_and_default_no_wsl_execution(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tests/host_check.py"), "host 输出"],
                              cwd=self.root, env=self.env, capture_output=True, timeout=20)
        self.assertEqual(proc.returncode, 0)
        record = json.loads((self.root / "host 输出/runs.json").read_text(encoding="utf-8"))
        self.assertTrue(record["config_bytes_unchanged"])
        self.assertTrue(record["parent_environment_unchanged"])
        self.assertEqual(len(record["runs"]), 4)
        for run in record["runs"]:
            self.assertNotIn("--wsl-list", run["command"])
            self.assertTrue(run["json_and_markdown_exist"])
