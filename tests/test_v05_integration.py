"""v0.5 comparison CSV, structural schema, offline process and real-link tests."""
import copy
import csv
import io
import json
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_doctor import DoctorFixture, ROOT
from test_v02 import item, source
import test_boundaries
from schema_subset import accepts
from windows_ai_doctor import cli
from windows_ai_doctor.compare import (IDS, STATES, COMPARISON_COLUMNS, MAX_BYTES, MAX_DEPTH,
                                       MAX_NODES, MAX_FINDINGS, MAX_INSTALLATION_GROUPS, VERSION_PATTERN, load_report)
from windows_ai_doctor.diagnosis_schema import diagnosis_schema, schema_json


class IntegrationFixture(DoctorFixture):
    def write(self, obj, name="input.json"):
        path = self.root / name
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return path

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main(list(map(str, args)))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()


class ComparisonCSVTests(IntegrationFixture):
    def rows(self, before, after):
        a, b = self.write(before, "old.json"), self.write(after, "new.json")
        code, out, err = self.invoke(["--compare", a, b, "--format=csv"])
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.startswith("\ufeffsequence,"))
        self.assertNotIn("\r", out)
        return list(csv.reader(io.StringIO(out[1:])))

    def test_changes_sorted_and_all_observations_survive_status_only_changes(self):
        a = source(item("codex.version", "warn", version="1.2.3"),
                   item("claude.path", "warn", installation_groups=0, scan_limited=False),
                   item("wsl.internal", "skipped"))
        b = source(item("codex.version", "pass", version="1.2.3"),
                   item("claude.path", "pass", installation_groups=0, scan_limited=False),
                   item("system.platform", "unknown"))
        rows = self.rows(a, b)
        self.assertEqual(rows[0], list(COMPARISON_COLUMNS))
        self.assertEqual(rows[1:], [
            ["1", "claude.path", "changed", "warn", "pass", "passes_now", "", "", "0", "0", "false", "false"],
            ["2", "codex.version", "changed", "warn", "pass", "passes_now", "1.2.3", "1.2.3", "", "", "", ""],
            ["3", "system.platform", "added", "", "unknown", "added", "", "", "", "", "", ""],
            ["4", "wsl.internal", "removed", "skipped", "", "removed", "", "", "", "", "", ""],
        ])

    def test_no_changes_and_empty_inputs_only_emit_header(self):
        for report in (source(), source(item("codex.path", installation_groups=32, scan_limited=True))):
            self.assertEqual(self.rows(report, report), [list(COMPARISON_COLUMNS)])

    def test_missing_false_groups_bounds_numeric_versions_and_notes(self):
        a = source(item("codex.path", "warn"), item("claude.path", "pass", installation_groups=0, scan_limited=False),
                   item("codex.version", version="0.0.0"))
        b = source(item("codex.path", "unknown", installation_groups=0, scan_limited=False),
                   item("claude.path", "pass", installation_groups=32, scan_limited=True),
                   item("codex.version", version="9999.9999.9999"))
        rows = self.rows(a, b)[1:]
        self.assertEqual(rows[0][5:], ["unassessed", "", "", "0", "32", "false", "true"])
        self.assertEqual(rows[1][5:], ["unassessed", "", "", "", "0", "", "false"])
        self.assertEqual(rows[2][5:8], ["observations_changed", "0.0.0", "9999.9999.9999"])
        for status in ("unknown", "skipped"):
            self.assertEqual(self.rows(source(item(status="error")), source(item(status=status)))[1][5], "unassessed")

    def test_ignored_and_formula_text_never_reaches_cells(self):
        for prefix in ("=", "+", "-", "@"):
            marker = prefix + "SYNTHETIC_PRIVATE"
            before = source(item("codex.version", "warn", version=marker, path=marker, installation_groups=marker))
            after = source(item("codex.version", "pass", version={"text": marker}, scan_limited=marker))
            after.update({"generated_at": marker, "language": marker, "secret": marker})
            rows = self.rows(before, after)
            self.assertFalse(any("SYNTHETIC_PRIVATE" in cell or cell.startswith(("=", "+", "-", "@")) for row in rows for cell in row))

    def test_bilingual_bytes_and_old_format_sets(self):
        a, b = self.write(source(), "old.json"), self.write(source(item()), "new.json")
        outputs = []
        for lang in ("zh", "en"):
            dest = self.root / lang
            self.assertEqual(self.invoke(["--compare", a, b, "--format=csv", "--lang", lang, "--output-dir", dest]), (0, "", ""))
            outputs.append((dest / f"comparison.{lang}.csv").read_bytes())
            for fmt, expected in (("both", {"md", "json"}), ("all", {"md", "json", "html"})):
                folder = self.root / (lang + fmt)
                self.assertEqual(self.invoke(["--compare", a, b, "--format", fmt, "--lang", lang, "--output-dir", folder])[0], 0)
                self.assertEqual({p.suffix[1:] for p in folder.iterdir()}, expected)
                report = json.loads((folder / f"comparison.{lang}.json").read_text(encoding="utf-8"))
                self.assertEqual(set(report["changes"][0]), {"id", "change", "before", "after", "note", "details"})
        self.assertEqual(outputs[0], outputs[1])
        self.assertTrue(outputs[0].startswith(b"\xef\xbb\xbfsequence,"))

    def test_collision_and_partial_write_cleanup(self):
        path = self.write(source(item()))
        dest = self.root / "out"
        dest.mkdir()
        existing = dest / "comparison.zh.csv"
        existing.write_bytes(b"keep")
        self.assertEqual(self.invoke(["--compare", path, path, "--format=csv", "--output-dir", dest])[0], 2)
        self.assertEqual(existing.read_bytes(), b"keep")
        original = Path.open
        class Interrupted:
            def __init__(self, stream, exception): self.stream, self.exception = stream, exception
            def __enter__(self): self.stream.__enter__(); return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def write(self, value): self.stream.write(value[:8]); raise self.exception()
        for exception, expected in ((OSError, 2), (KeyboardInterrupt, 130)):
            folder = self.root / str(expected)
            folder.mkdir()
            keep = folder / "keep.txt"
            keep.write_bytes(b"keep")
            def guarded(p, *a, **kw):
                stream = original(p, *a, **kw)
                return Interrupted(stream, exception) if p.parent == folder and p.suffix == ".csv" else stream
            with patch.object(Path, "open", guarded):
                self.assertEqual(self.invoke(["--compare", path, path, "--format=csv", "--output-dir", folder])[0], expected)
            self.assertEqual(list(folder.iterdir()), [keep])

    def test_malformed_bounds_derived_and_duplicate_inputs_remain_rejected(self):
        good = self.write(source(), "good.json")
        bad = self.root / "bad.json"
        for text in ('{"schema_version":"1.0","findings":[],"x":1,"x":2}', "[" * 17 + "0" + "]" * 17,
                     " " * (MAX_BYTES + 1), json.dumps({**source(), "report_type": "catalog"}),
                     json.dumps(source(item(), item())), json.dumps(source(item("codex.path", installation_groups=True)))):
            bad.write_text(text, encoding="utf-8")
            for paths in ((bad, good), (good, bad)):
                self.assertEqual(self.invoke(["--compare", *paths, "--format=csv"])[0], 2)


class SchemaTests(IntegrationFixture):
    """Directional compatibility: reader acceptance implies schema acceptance.

    Schema may accept more because token and resource limits belong to the
    reader; --validate remains the sole authority for tool acceptance.
    """
    def test_schema_and_parser_constants_match_and_no_external_refs(self):
        doc = diagnosis_schema()
        self.assertEqual(doc["$defs"]["finding"]["properties"]["id"]["enum"], sorted(IDS))
        self.assertEqual(doc["$defs"]["finding"]["properties"]["status"]["enum"], list(STATES))
        self.assertEqual(doc["properties"]["findings"]["maxItems"], MAX_FINDINGS)
        self.assertEqual(doc["$defs"]["path_evidence"]["properties"]["installation_groups"]["maximum"], MAX_INSTALLATION_GROUPS)
        self.assertEqual(doc["x-version-projection"]["pattern"], VERSION_PATTERN)
        self.assertIs(doc["x-parser-limits"]["integer_tokens_for_path_groups"], True)
        self.assertEqual([doc["x-parser-limits"][k] for k in ("max_bytes", "max_depth", "max_nodes")], [MAX_BYTES, MAX_DEPTH, MAX_NODES])
        todo = [doc]
        while todo:
            value = todo.pop()
            if isinstance(value, dict):
                if "$ref" in value: self.assertTrue(value["$ref"].startswith("#/"))
                todo.extend(value.values())
            elif isinstance(value, list): todo.extend(value)

    def test_structural_samples_follow_directional_compatibility(self):
        # These shape samples agree in both directions. The separate parser
        # limit cases below deliberately demonstrate wider schema acceptance.
        good = [source(), {**source(item()), "report_type": "diagnosis"},
                source(*(item(id, STATES[n % len(STATES)]) for n, id in enumerate(sorted(IDS))))]
        for value in (0, 32):
            good.append(source(item("codex.path", installation_groups=value, scan_limited=False)))
        good.extend((source({"id": "codex.path", "status": "pass"}),
                     source(item("claude.path")),
                     source(item("claude.path", installation_groups=0, scan_limited=True))))
        bad = [[], None, {}, {"schema_version": 1.0, "findings": []}, {"schema_version": "1.0", "findings": {}},
               {**source(), "report_type": "catalog"}, source({"id": "codex.version"}), source(item("Codex.version")),
               source(item(status="missing")), source(item("codex.path", installation_groups=True)),
               source(item("codex.path", installation_groups=-1)), source(item("codex.path", installation_groups=33)),
               source(item("codex.path", installation_groups=1.5)), source(item("codex.path", scan_limited=0)),
               source({"id": "codex.version", "status": "pass", "evidence": []}), source(*([item()] * 65))]
        for value in (None, "1"):
            bad.append(source(item("claude.path", installation_groups=value)))
        for value in (None, "false"):
            bad.append(source(item("claude.path", scan_limited=value)))
        visited = set()
        for expected, samples in ((True, good), (False, bad)):
            for obj in samples:
                self.assertEqual(accepts(diagnosis_schema(), obj, visited=visited), expected)
                path = self.write(obj)
                self.assertEqual(self.invoke(["--validate", path])[0], 0 if expected else 2)
        self.assertTrue({"$ref", "type", "required", "properties", "additionalProperties", "const", "enum",
                         "items", "maxItems", "minimum", "maximum", "if", "then"} <= visited)

    def test_legacy_versions_and_ignored_nonpath_observations_remain_accepted(self):
        for version in (None, "=SYNTHETIC_PRIVATE", "1.2", "10000.0.0", 12, {}, []):
            obj = source(item("codex.version", version=version, installation_groups="private", scan_limited="private"))
            self.assertTrue(accepts(diagnosis_schema(), obj))
            path = self.write(obj)
            self.assertEqual(self.invoke(["--validate", path])[0], 0)
            self.assertIsNone(load_report(path)["codex.version"]["version"])
        numeric = source(item("codex.version", version="1.2.3"))
        self.assertTrue(accepts(diagnosis_schema(), numeric))
        numeric_path = self.write(numeric)
        self.assertEqual(self.invoke(["--validate", numeric_path])[0], 0)
        self.assertEqual(load_report(numeric_path)["codex.version"]["version"], "1.2.3")
        for id in sorted(IDS - {"codex.path", "claude.path"}):
            obj = source(item(id, installation_groups=True, scan_limited={"ignored": 1}))
            self.assertTrue(accepts(diagnosis_schema(), obj))
            self.assertEqual(self.invoke(["--validate", self.write(obj)])[0], 0)
        for id in ("codex.path", "claude.path"):
            obj = source(item(id, installation_groups=True, scan_limited={"ignored": 1}))
            self.assertFalse(accepts(diagnosis_schema(), obj))
            self.assertEqual(self.invoke(["--validate", self.write(obj)])[0], 2)

    def test_mathematical_integer_and_parser_extra_limits_are_distinguished(self):
        # Expected directional difference: schema accepts mathematical integers;
        # --validate rejects non-integer JSON tokens. Do not tighten the schema.
        path = self.root / "input.json"
        for spelling in ("1.0", "1e0", "-0.0"):
            text = '{"schema_version":"1.0","findings":[{"id":"codex.path","status":"pass","evidence":{"installation_groups":' + spelling + '}}]}'
            self.assertTrue(accepts(diagnosis_schema(), json.loads(text)))
            path.write_text(text, encoding="utf-8")
            self.assertEqual(self.invoke(["--validate", path])[0], 2)
        obj = source(item(), item())
        self.assertTrue(accepts(diagnosis_schema(), obj))
        self.assertEqual(self.invoke(["--validate", self.write(obj)])[0], 2)
        for obj in ({**source(), "ignored": "x" * 32769}, {**source(), "ignored": [0] * 20001}):
            self.assertTrue(accepts(diagnosis_schema(), obj))
            self.assertEqual(self.invoke(["--validate", self.write(obj)])[0], 2)

    def test_evaluator_uses_schema_semantics_and_rejects_unsupported_keywords(self):
        self.assertTrue(accepts({"type": "integer"}, 1.0))
        for value in (True, "1", 1.5): self.assertFalse(accepts({"type": "integer"}, value))
        self.assertFalse(accepts({"const": 1}, True))
        self.assertTrue(accepts({"const": 1}, 1.0))
        with self.assertRaises(AssertionError): accepts({"not": {}}, {})
        with self.assertRaises(AssertionError): accepts({"$ref": "https://invalid.example/schema"}, {})

    def test_export_is_deterministic_silent_and_preserves_collision(self):
        code, first, err = self.invoke(["--schema"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(first, schema_json())
        self.assertEqual(first, self.invoke(["--schema"])[1])
        self.assertNotIn("generated_at", first)
        dest = self.root / "out"
        self.assertEqual(self.invoke(["--schema", "--output-dir", dest]), (0, "", ""))
        path = dest / "schema.diagnosis.json"
        self.assertEqual(path.read_bytes(), first.encode("utf-8"))
        self.assertEqual(self.invoke(["--schema", "--output-dir", dest])[0], 2)
        self.assertEqual(path.read_bytes(), first.encode("utf-8"))

    def test_schema_partial_write_error_and_interruption_cleanup(self):
        original = Path.open
        for exception, expected in ((OSError, 2), (KeyboardInterrupt, 130)):
            dest = self.root / str(expected)
            dest.mkdir()
            keep = dest / "keep.txt"
            keep.write_text("keep")
            class Interrupted:
                def __enter__(self): self.stream.__enter__(); return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def write(self, value): self.stream.write(value[:10]); raise exception()
            def guarded(p, *a, **kw):
                stream = original(p, *a, **kw)
                if p.parent == dest and p.name == "schema.diagnosis.json":
                    proxy = Interrupted(); proxy.stream = stream; return proxy
                return stream
            with patch.object(Path, "open", guarded):
                self.assertEqual(self.invoke(["--schema", "--output-dir", dest])[0], expected)
            self.assertEqual(list(dest.iterdir()), [keep])


class V05ModeTests(IntegrationFixture):
    def test_explicit_default_conflicts_and_abbreviations_fail_before_reads(self):
        path = self.root / "SYNTHETIC_PRIVATE"
        modes = [["--schema"], ["--catalog"], ["--compare", path, path, "--format=csv"]]
        diagnostics = [["--home", path], ["--project", path], ["--tools", "codex", "claude"], ["--timeout=3.0"],
                       ["--no-version"], ["--wsl-list"], ["--fail-on=error"]]
        with ExitStack() as stack:
            for name in ("load_report", "load_history", "verify_support", "Doctor"):
                stack.enter_context(patch.object(cli, name, side_effect=AssertionError("read before argument validation")))
            for mode in modes:
                for extra in diagnostics:
                    code, out, err = self.invoke([*mode, *extra])
                    self.assertEqual((code, out), (2, ""))
                    self.assertNotIn("SYNTHETIC_PRIVATE", err)
            for extra in (["--lang=zh"], ["--format=both"], ["--format=json"], ["--catalog"], ["--history", path, path],
                          ["--validate", path], ["--verify-support", path], ["--support", path], ["--compare", path, path]):
                self.assertEqual(self.invoke(["--schema", *extra])[0], 2)
            for fmt in ("csv", "html", "all"):
                self.assertEqual(self.invoke(["--catalog", "--format", fmt])[0], 2)
            for args in (["--sche"], ["--catal"], ["--compare", path, path, "--form=csv"]):
                self.assertEqual(self.invoke(args)[0], 2)

    def test_schema_real_child_process_has_no_input_environment_or_external_access(self):
        script = '''import os, sys
sys.path.insert(0, sys.argv[1])
from windows_ai_doctor import cli
# Establish argparse's standard-library locale/terminal bootstrap before checking
# whether the actual export operation consults diagnostic environment values.
parser = cli.parser()
cli.parser = lambda: parser
def denied(*a, **kw): raise AssertionError("forbidden offline operation")
def audit(event, args):
    if event == "open" or event.startswith(("subprocess.", "socket.", "winreg.", "os.listdir", "os.scandir")): denied()
class NoEnvironment(dict):
    __getitem__ = get = __iter__ = items = values = keys = __contains__ = denied
os.environ = NoEnvironment()
cli.Doctor = cli.load_report = cli.load_history = cli.verify_support = denied
sys.addaudithook(audit)
raise SystemExit(cli.main(["--schema"]))
'''
        result = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT)], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.decode("utf-8"), schema_json())

    def test_compare_csv_real_child_process_only_reads_two_explicit_inputs(self):
        a = self.write(source(item("codex.version", "warn", version="1.2.3", path="Z:/SYNTHETIC_PRIVATE")), "old.json")
        b = self.write(source(item("codex.version", "pass", version="2.0.0")), "new.json")
        script = '''import os, sys
sys.path.insert(0, sys.argv[1])
from windows_ai_doctor import cli
from pathlib import Path
import ctypes  # Windows local-drive guard lazily imports this standard library.
# Scope: audit the comparison after argparse's locale/terminal/color bootstrap.
# Python 3.14 first imports _colorize while constructing the parser. Reuse that
# parser; argument parsing and the comparison still run inside the strict audit.
parser = cli.parser()
cli.parser = lambda: parser
allowed = {str(Path(v).absolute()) for v in sys.argv[2:]}
seen = []
def denied(*a, **kw): raise AssertionError("forbidden offline operation")
def audit(event, args):
    if event.startswith(("subprocess.", "socket.", "winreg.", "os.listdir", "os.scandir")): denied()
    if event == "open":
        if str(args[0]) not in allowed or args[1] != "r": denied()
        seen.append(str(args[0]))
class NoEnvironment(dict):
    __getitem__ = get = __iter__ = items = values = keys = __contains__ = denied
os.environ = NoEnvironment()
sys.addaudithook(audit)
cli.Doctor = denied
code = cli.main(["--compare", *sys.argv[2:], "--format=csv"])
if sorted(seen) != sorted(allowed): denied()
raise SystemExit(code)
'''
        result = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT), str(a), str(b)], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith(b"\xef\xbb\xbfsequence,"))
        self.assertNotIn(b"\r", result.stdout)
        self.assertNotIn(b"SYNTHETIC_PRIVATE", result.stdout + result.stderr)
        self.offline_access_evidence = {
            "audit_starts_after": "argparse construction; before argument parsing and comparison",
            "explicit_input_reads": 2, "extra_file_access_attempts": 0,
            "environment_access_attempts": 0, "external_access_attempts": 0,
            "csv_bom_lf_and_private_marker_checks_passed": True,
        }


class V05RequiredLinks(IntegrationFixture):
    def assert_link(self, side, directory=False, junction=False):
        good = self.write(source(), "good.json")
        target = self.root / "target"
        target.mkdir()
        content = target / "input.json"
        content.write_bytes(b"SYNTHETIC_PRIVATE")
        link = self.root / ("ancestor" if directory else "file.json")
        if junction:
            with test_boundaries.BoundaryTests.junction(self, target, name=link.name) as link:
                with test_boundaries.BoundaryTests.no_descendant_access(self, link):
                    args = [link / "input.json", good] if side == "old" else [good, link / "input.json"]
                    self.assertEqual(self.invoke(["--compare", *args, "--format=csv"])[0], 2)
            return
        try:
            link.symlink_to(target if directory else content, target_is_directory=directory)
        except OSError as exc:
            self.fail(f"Required compare CSV {side} real symlink needs authorized privilege (winerror {exc.winerror}); acceptance blocked")
        self.assertEqual(link.lstat().st_reparse_tag, 0xA000000C)
        self.link_evidence = [{"side": side, "kind": "directory_symlink" if directory else "file_symlink",
                               "reparse_tag": hex(link.lstat().st_reparse_tag), "content_read_attempts": 0,
                               "descendant_access_attempts": 0}]
        original = Path.open
        def guarded(p, *a, **kw):
            if p == content or p == link or p.is_relative_to(link):
                self.link_evidence[-1]["content_read_attempts"] += 1
                self.fail("linked content opened")
            return original(p, *a, **kw)
        with patch.object(Path, "open", guarded):
            if directory:
                with test_boundaries.BoundaryTests.no_descendant_access(self, link):
                    args = [link / "input.json", good] if side == "old" else [good, link / "input.json"]
                    self.assertEqual(self.invoke(["--compare", *args, "--format=csv"])[0], 2)
            else:
                args = [link, good] if side == "old" else [good, link]
                self.assertEqual(self.invoke(["--compare", *args, "--format=csv"])[0], 2)

    def test_compare_csv_old_file_real_symlink_zero_target_reads(self): self.assert_link("old")
    def test_compare_csv_new_file_real_symlink_zero_target_reads(self): self.assert_link("new")
    def test_compare_csv_old_ancestor_real_symlink_zero_descendant_access(self): self.assert_link("old", directory=True)
    def test_compare_csv_new_ancestor_real_symlink_zero_descendant_access(self): self.assert_link("new", directory=True)
    def test_compare_csv_old_ancestor_real_junction_zero_descendant_access(self): self.assert_link("old", directory=True, junction=True)
    def test_compare_csv_new_ancestor_real_junction_zero_descendant_access(self): self.assert_link("new", directory=True, junction=True)
