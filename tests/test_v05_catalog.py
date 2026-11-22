"""Direct catalog module and CLI boundary tests for v0.5. No privilege suite."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from windows_ai_doctor import cli
from windows_ai_doctor.catalog import (ENTRIES, MAX_CATALOG_IDS, PROJECT_ONLY, catalog_markdown,
                                       catalog_report)
from windows_ai_doctor.compare import IDS, STATES
from windows_ai_doctor.core import Doctor
from windows_ai_doctor.report import json_report


class CatalogFixture(unittest.TestCase):
    def setUp(self):
        fixture_root = ROOT / ".test-fixtures"
        fixture_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="ai-doctor-catalog-", dir=fixture_root)
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main(list(map(str, args)))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()


class CatalogModuleTests(CatalogFixture):
    def test_full_catalog_matches_ids_and_is_deterministic(self):
        zh = catalog_report([], "zh")
        en = catalog_report(None, "en")
        self.assertEqual(zh["report_type"], "catalog")
        self.assertEqual(zh["schema_version"], "1.0")
        self.assertEqual(zh["doctor_version"], "0.6.0")
        self.assertNotIn("generated_at", zh)
        self.assertEqual(zh["status_vocabulary"], list(STATES))
        self.assertEqual([c["id"] for c in zh["checks"]], sorted(IDS))
        self.assertEqual(len(zh["checks"]), 19)
        self.assertEqual(set(ENTRIES), IDS)
        self.assertEqual(json_report(zh), json_report(catalog_report([], "zh")))
        self.assertEqual(catalog_markdown(zh), catalog_markdown(catalog_report([], "zh")))
        self.assertTrue(catalog_markdown(zh).endswith("\n"))
        self.assertNotEqual(zh["notice"], en["notice"])
        self.assertEqual([c["id"] for c in en["checks"]], [c["id"] for c in zh["checks"]])
        self.assertEqual(en["checks"], zh["checks"])

    def test_project_only_marks_and_evidence_fields_are_fixed(self):
        report = catalog_report([], "zh")
        for check in report["checks"]:
            expected = "project_only" if check["id"] in PROJECT_ONLY else "always"
            self.assertEqual(check["availability"], expected)
            self.assertTrue(check["produced_by_current_version"])
            self.assertEqual(check["evidence_fields"], ENTRIES[check["id"]]["evidence_fields"])
            for field in ("purpose", "limitation"):
                self.assertEqual(set(check[field]), {"zh", "en"})
                self.assertEqual(check[field], ENTRIES[check["id"]][field])
                self.assertIsNot(check[field], ENTRIES[check["id"]][field])
            self.assertEqual(set(check), {"id", "target", "availability", "produced_by_current_version",
                                          "purpose", "evidence_fields", "limitation"})
        self.assertEqual(PROJECT_ONLY, {"codex.config.project", "claude.config.project", "claude.config.local"})

    def test_subset_dedupe_sort_and_reject_unknown_malformed_oversize(self):
        report = catalog_report(["wsl.internal", "system.platform", "wsl.internal", "codex.path"], "en")
        self.assertEqual([c["id"] for c in report["checks"]],
                         ["codex.path", "system.platform", "wsl.internal"])
        for bad in (["Codex.path"], ["codex.path!"], ["missing.id"], ["codex.path", None],
                    ["unknown.check"], ["codex.path"] * (MAX_CATALOG_IDS + 1), "codex.path"):
            with self.assertRaises(ValueError) as ctx:
                catalog_report(bad, "zh")
            self.assertEqual(str(ctx.exception), "invalid_catalog")
            self.assertNotIn("Codex", str(ctx.exception))
            self.assertNotIn("missing", str(ctx.exception))
            self.assertNotIn("unknown.check", str(ctx.exception))
        with self.assertRaises(ValueError):
            catalog_report(["codex.path"], "de")
        thirty_two = ["system.platform"] + ["codex.path"] * 31
        self.assertEqual([c["id"] for c in catalog_report(thirty_two, "zh")["checks"]],
                         ["codex.path", "system.platform"])

    def test_ids_match_synthetic_doctor_generation_set(self):
        home = self.root / "home"
        project = self.root / "project"
        home.mkdir()
        project.mkdir()
        env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}}
        env.update({"PATH": "", "PATHEXT": ".EXE;.CMD;.BAT;.COM", "USERPROFILE": str(home), "HOME": str(home)})
        with patch("windows_ai_doctor.core.system_wsl_launcher", return_value=None), \
                patch("windows_ai_doctor.core.registered_distributions", return_value=(0, "synthetic")):
            report = Doctor(env=env, home=home, tools=("codex", "claude"), project=project,
                            versions=False, wsl_list=False).run()
        generated = {f["id"] for f in report["findings"]}
        self.assertEqual(generated, IDS)
        for finding in report["findings"]:
            allowed = set(ENTRIES[finding["id"]]["evidence_fields"])
            self.assertTrue(set(finding["evidence"]).issubset(allowed),
                            msg=f"{finding['id']}: {set(finding['evidence']) - allowed}")


class CatalogCliTests(CatalogFixture):
    def test_default_md_stdout_json_both_and_directory_names(self):
        code, out, err = self.invoke(["--catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, catalog_markdown(catalog_report([], "zh")))
        code, out, err = self.invoke(["--catalog", "--format", "json", "--lang", "en"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, json_report(catalog_report([], "en")))
        code, out, err = self.invoke(["--catalog", "--format", "both"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, catalog_markdown(catalog_report([], "zh")))
        dest = self.root / "out"
        self.assertEqual(self.invoke(["--catalog", "system.platform", "codex.path",
                                      "--format", "both", "--output-dir", dest])[0], 0)
        names = sorted(p.name for p in dest.iterdir())
        self.assertEqual(names, ["catalog.zh.json", "catalog.zh.md"])
        body = json.loads((dest / "catalog.zh.json").read_text(encoding="utf-8"))
        self.assertEqual([c["id"] for c in body["checks"]], ["codex.path", "system.platform"])

    def test_unknown_id_exit_two_without_echo_and_format_conflicts(self):
        marker = "SYNTHETIC_UNKNOWN_ID.private"
        code, out, err = self.invoke(["--catalog", marker])
        self.assertEqual((code, out), (2, ""))
        self.assertNotIn(marker, err)
        self.assertNotIn(marker, out)
        for fmt in ("csv", "html", "all"):
            self.assertEqual(self.invoke(["--catalog", "--format", fmt])[0], 2)
        too_many = ["codex.path"] * 33
        self.assertEqual(self.invoke(["--catalog", *too_many])[0], 2)

    def test_collision_and_partial_write_cleanup(self):
        dest = self.root / "collision"
        dest.mkdir()
        existing = dest / "catalog.zh.md"
        existing.write_bytes(b"keep")
        self.assertEqual(self.invoke(["--catalog", "--output-dir", dest])[0], 2)
        self.assertEqual(existing.read_bytes(), b"keep")
        original = Path.open

        class Interrupted:
            def __init__(self, stream, exception):
                self.stream, self.exception = stream, exception

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *args):
                return self.stream.__exit__(*args)

            def write(self, value):
                self.stream.write(value[:8])
                raise self.exception()

        for exception, expected in ((OSError, 2), (KeyboardInterrupt, 130)):
            folder = self.root / f"cleanup-{expected}"
            folder.mkdir()
            keep = folder / "keep.txt"
            keep.write_bytes(b"keep")

            def guarded(p, *a, **kw):
                stream = original(p, *a, **kw)
                return Interrupted(stream, exception) if p.parent == folder and p.suffix == ".md" else stream

            with patch.object(Path, "open", guarded):
                self.assertEqual(self.invoke(["--catalog", "--output-dir", folder])[0], expected)
            self.assertEqual(list(folder.iterdir()), [keep])

    def test_real_child_process_catalog_has_no_input_or_external_access(self):
        # Scope: after argparse/locale bootstrap, the catalog export itself must not
        # open input paths, run Doctor, spawn commands, touch network/registry or scan dirs.
        # Python startup and argparse terminal/locale init are outside that export audit.
        script = '''import os, sys
sys.path.insert(0, sys.argv[1])
from windows_ai_doctor import cli
from windows_ai_doctor.catalog import catalog_markdown, catalog_report
parser = cli.parser()
cli.parser = lambda: parser
def denied(*a, **kw): raise AssertionError("forbidden offline operation")
def audit(event, args):
    if event == "open" or event.startswith(("subprocess.", "socket.", "winreg.", "os.listdir", "os.scandir")):
        denied()
class NoEnvironment(dict):
    __getitem__ = get = __iter__ = items = values = keys = __contains__ = denied
os.environ = NoEnvironment()
cli.Doctor = cli.load_report = cli.load_history = cli.verify_support = denied
sys.addaudithook(audit)
raise SystemExit(cli.main(["--catalog"]))
'''
        result = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT)],
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        expected = catalog_markdown(catalog_report([], "zh")).encode("utf-8")
        self.assertEqual(result.stdout, expected)

    def test_bilingual_directory_bytes_stable_without_timestamp(self):
        outputs = []
        for lang in ("zh", "en"):
            dest = self.root / lang
            code, out, err = self.invoke(["--catalog", "--format", "json", "--lang", lang, "--output-dir", dest])
            self.assertEqual(code, 0)
            path = dest / f"catalog.{lang}.json"
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("generated_at", text)
            self.assertEqual(text, json_report(catalog_report([], lang)))
            outputs.append(path.read_bytes())
        self.assertNotEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    raise SystemExit(unittest.main(verbosity=2))
