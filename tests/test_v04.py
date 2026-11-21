"""Offline validity, hostile archives, formula safety and real link regressions."""
import copy
import csv
import hashlib
import io
import json
import os
import struct
import subprocess
import sys
import zipfile
import zlib
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_doctor import DoctorFixture, ROOT
from test_v02 import source, item
import test_boundaries
from windows_ai_doctor import cli
from windows_ai_doctor.compare import IDS, MAX_BYTES, load_report
from windows_ai_doctor.support import support_members
from windows_ai_doctor.verify_support import MAX_ZIP_BYTES, MAX_MEMBER_BYTES, MAX_TOTAL_BYTES, verify_support


class V04Tests(DoctorFixture):
    def write(self, obj, name="input.json"):
        path = self.root / name
        path.write_text(json.dumps(obj), encoding="utf-8")
        return path

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli.main([str(v) for v in args])
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def bundle(self, members=None, name="bundle.zip", compression=zipfile.ZIP_DEFLATED):
        members = members if members is not None else support_members({"codex.version": {"status": "error", "version": "1.2.3"}})
        path = self.root / name
        with zipfile.ZipFile(path, "w", compression=compression) as archive:
            entries = members.items() if isinstance(members, dict) else members
            for key, value in entries:
                archive.writestr(key, value)
        return path

    def manifest(self, members):
        members = dict(members)
        members["SHA256SUMS.txt"] = ("".join(hashlib.sha256(data).hexdigest() + "  " + name + "\n"
                  for name, data in sorted(members.items()) if name != "SHA256SUMS.txt")).encode("ascii")
        return members

    def test_validation_recomputes_counts_and_separates_health(self):
        findings = [item(id, state) for id, state in zip(sorted(IDS), ("pass", "warn", "error", "unknown", "skipped"))]
        path = self.write({**source(*findings), "summary": {"pass": 99999}, "ignored": "SYNTHETIC_PRIVATE"})
        for lang in ("zh", "en"):
            code, out, err = self.invoke(["--validate", path, "--lang", lang, "--format", "json"])
            doc = json.loads(out)
            self.assertEqual((code, err), (0, ""))
            self.assertTrue(doc["valid"])
            self.assertEqual(doc["report_type"], "validation")
            self.assertEqual(doc["check_count"], 5)
            self.assertEqual(doc["summary"], dict.fromkeys(("pass", "warn", "error", "unknown", "skipped"), 1))
            self.assertNotIn("SYNTHETIC_PRIVATE", out)
        empty = self.write(source(), "empty.json")
        self.assertEqual(json.loads(self.invoke(["--validate", empty, "--format=json"])[1])["check_count"], 0)

    def test_validation_accepts_historical_schema_inputs(self):
        for relative in ("examples/review-fixes/zh/report.zh.json", "examples/v02/zh/report.zh.json", "examples/v03/run1.json"):
            self.assertEqual(self.invoke(["--validate", ROOT / relative])[0], 0, relative)

    def test_validation_rejects_malformed_duplicate_deep_and_budget_inputs(self):
        path = self.root / "SYNTHETIC_PRIVATE.json"
        invalid = ['{"schema_version":"1.0","findings":[],"x":{"a":1,"a":2}}',
                   '[' * 17 + '0' + ']' * 17, ' ' * (MAX_BYTES + 1),
                   json.dumps({**source(), "x": [0] * 20001}), json.dumps({**source(), "x": "x" * 32769}),
                   '{bad SYNTHETIC_PRIVATE', '{"x":Infinity}', json.dumps(source(item(status="=SYNTHETIC_PRIVATE"))),
                   json.dumps(source(item("codex.path", scan_limited=1)))]
        for text in invalid:
            path.write_text(text, encoding="utf-8")
            code, out, err = self.invoke(["--validate", path])
            self.assertEqual((code, out), (2, ""))
            self.assertNotIn("SYNTHETIC_PRIVATE", err)

    def test_derived_results_rejected_in_every_diagnosis_import_mode(self):
        for kind in ("comparison", "history", "support", "validation", "support_verification"):
            path = self.write({**source(item()), "report_type": kind})
            for args in (["--validate", path], ["--compare", path, path], ["--history", path, path, "--format=csv"],
                         ["--support", path, "--output-dir", self.root / kind]):
                self.assertEqual(self.invoke(args)[0], 2)

    def test_all_modes_conflict_and_explicit_defaults_rejected_before_reads(self):
        path = self.root / "SYNTHETIC_PRIVATE"
        modes = [["--validate", path], ["--verify-support", path], ["--history", path, path], ["--compare", path, path],
                 ["--support", path, "--output-dir", self.root]]
        with ExitStack() as stack:
            for target in ("windows_ai_doctor.cli.load_report", "windows_ai_doctor.cli.load_history", "windows_ai_doctor.cli.verify_support", "windows_ai_doctor.cli.Doctor"):
                stack.enter_context(patch(target, side_effect=AssertionError("input read before conflict check")))
            for mode in modes[:2]:
                for extra in (["--tools", "codex", "claude"], ["--home", self.home], ["--project", self.root], ["--timeout=3.0"],
                              ["--no-version"], ["--wsl-list"], ["--fail-on=error"], ["--vali", path], ["--verify-s", path]):
                    self.assertEqual(self.invoke([*mode, *extra])[0], 2)
                for fmt in ("html", "all", "csv"):
                    self.assertEqual(self.invoke([*mode, "--format=" + fmt])[0], 2)
            for n, mode in enumerate(modes):
                for other in modes[n + 1:]:
                    self.assertEqual(self.invoke([*mode, *other])[0], 2)
            for mode in ([], modes[0], modes[1], modes[4]):
                self.assertEqual(self.invoke([*mode, "--format=csv"])[0], 2)

    def test_validation_and_verification_bilingual_export_formats(self):
        report, bundle = self.write(source(item())), self.bundle()
        for flag, path, stem in (("--validate", report, "validation"), ("--verify-support", bundle, "support-verification")):
            for lang in ("zh", "en"):
                for fmt, extensions in (("both", {"md", "json"}), ("md", {"md"}), ("json", {"json"})):
                    dest = self.root / (stem + lang + fmt)
                    code, out, err = self.invoke([flag, path, "--lang", lang, "--format", fmt, "--output-dir", dest])
                    self.assertEqual((code, err), (0, ""))
                    self.assertEqual({f.name for f in dest.iterdir()}, {f"{stem}.{lang}.{ext}" for ext in extensions})
                    self.assertEqual(self.invoke([flag, path, "--format", fmt])[1][0], "{" if fmt == "json" else "#")

    def test_old_v03_bundle_compatibility_and_new_roundtrip(self):
        old = ROOT / "examples/v03/support/support-bundle.zip"
        self.assertEqual(verify_support(old)["member_count"], 5)
        report = self.write(source(item(), item("codex.path", "warn", installation_groups=2, scan_limited=False)))
        dest = self.root / "new"
        self.assertEqual(self.invoke(["--support", report, "--output-dir", dest])[0], 0)
        code, out, err = self.invoke(["--verify-support", dest / "support-bundle.zip", "--format=json"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["report_type"], "support_verification")

    def test_zip_member_sets_duplicates_paths_and_special_types(self):
        normal = support_members({})
        bad_sets = [{k: v for k, v in normal.items() if k != "PRIVACY.txt"}, {**normal, "extra": b"x"},
                    [*normal.items(), ("support.json", b"{}")]]
        for name in ("../support.json", "/support.json", "C:/support.json", "dir\\support.json", "support.json/", "SUPPORT.JSON", "support.json\x00tail"):
            changed = dict(normal)
            del changed["support.json"]
            changed[name] = b"{}"
            bad_sets.append(changed)
        for members in bad_sets:
            # zipfile itself truncates a NUL at creation, so inject separately below.
            if any("\x00" in (k.filename if isinstance(k, zipfile.ZipInfo) else k) for k in (members if isinstance(members, dict) else [])):
                continue
            self.assertEqual(self.invoke(["--verify-support", self.bundle(members)])[0], 2)
        for mode in (0o120777, 0o040755, 0o020600, 0o010600):
            special = zipfile.ZipInfo("support.json")
            special.create_system = 3
            special.external_attr = mode << 16
            changed = [(special if k == "support.json" else k, v) for k, v in normal.items()]
            self.assertEqual(self.invoke(["--verify-support", self.bundle(changed)])[0], 2)

    def test_zip_bad_manifest_hash_duplicate_missing_or_extra_lines(self):
        normal = support_members({})
        manifest = normal["SHA256SUMS.txt"]
        cases = [manifest.replace(manifest[:64], b"0" * 64, 1), manifest + manifest.splitlines(True)[0],
                 b"\n".join(manifest.splitlines()[:-1]) + b"\n", manifest + b"0" * 64 + b"  ../private\n",
                 manifest.replace(b"  ", b" ", 1), b"SYNTHETIC_PRIVATE", manifest + b"\n"]
        for data in cases:
            bad = {**normal, "SHA256SUMS.txt": data}
            code, out, err = self.invoke(["--verify-support", self.bundle(bad)])
            self.assertEqual((code, out), (2, ""))
            self.assertNotIn("SYNTHETIC_PRIVATE", err)

    def test_support_semantics_bad_schema_states_counts_and_observations(self):
        normal = support_members({"codex.version": {"status": "pass", "version": "1.2.3"}})
        valid = json.loads(normal["support.json"])
        invalid = [{**valid, "schema_version": "2.0"}, {**valid, "report_type": "diagnosis"}, {**valid, "summary": {}},
                   {**valid, "summary": {**valid["summary"], "pass": True}},
                   {**valid, "summary": {**valid["summary"], "pass": 2}}, {**valid, "findings": [*valid["findings"]] * 2}]
        for finding in (item("unknown"), item(status="invalid"), item(version="=SYNTHETIC_PRIVATE"),
                        item("codex.path", installation_groups=True), item("codex.path", installation_groups=33),
                        item("codex.path", scan_limited=1), item("wsl.internal", version="1.2.3"), item(path="SYNTHETIC_PRIVATE")):
            invalid.append({**valid, "findings": [finding]})
        for obj in invalid:
            members = self.manifest({**normal, "support.json": json.dumps(obj).encode()})
            self.assertEqual(self.invoke(["--verify-support", self.bundle(members)])[0], 2)
        for text in ('{"schema_version":"1.0","schema_version":"1.0"}', '[' * 17 + '0' + ']' * 17,
                     json.dumps({**valid, "ignored": [0] * 20001}), json.dumps({**valid, "ignored": "x" * 32769})):
            self.assertEqual(self.invoke(["--verify-support", self.bundle(self.manifest({**normal, "support.json": text.encode()}))])[0], 2)

    def test_zip_archive_member_and_total_size_budgets_before_decompression(self):
        path = self.root / "huge.zip"
        path.write_bytes(b"0" * (MAX_ZIP_BYTES + 1))
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        normal = support_members({})
        for members in ({**normal, "PRIVACY.txt": b"0" * (MAX_MEMBER_BYTES + 1)},
                        {**normal, "PRIVACY.txt": b"0" * MAX_MEMBER_BYTES, "summary.zh.md": b"0" * MAX_MEMBER_BYTES}):
            path = self.bundle(members)
            with patch("zlib.decompressobj", side_effect=AssertionError("over-budget content decompressed")):
                self.assertEqual(self.invoke(["--verify-support", path])[0], 2)

    def test_zip_compression_encryption_and_truncation_rejected(self):
        normal = support_members({})
        for compression in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
            self.assertEqual(self.invoke(["--verify-support", self.bundle(normal, compression=compression)])[0], 2)
        path = self.bundle(normal)
        raw = path.read_bytes()
        for data in (b"", b"not a zip SYNTHETIC_PRIVATE", raw[:-10], raw[:40]):
            path.write_bytes(data)
            self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        data = bytearray(raw)
        local, central = data.index(b"PK\x03\x04"), data.index(b"PK\x01\x02")
        struct.pack_into("<H", data, local + 6, 1)
        struct.pack_into("<H", data, central + 8, 1)
        path.write_bytes(data)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)

    def test_zip_crc_damage_local_header_mismatch_and_overlap_rejected(self):
        path = self.bundle(compression=zipfile.ZIP_STORED)
        raw = path.read_bytes()
        name_size, extra_size = struct.unpack_from("<HH", raw, 26)
        start = 30 + name_size + extra_size
        damaged = bytearray(raw)
        damaged[start] ^= 1
        path.write_bytes(damaged)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        mismatch = bytearray(raw)
        struct.pack_into("<H", mismatch, 8, zipfile.ZIP_DEFLATED)
        path.write_bytes(mismatch)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        changed = bytearray(raw)
        first = changed.index(b"PK\x01\x02")
        second = changed.index(b"PK\x01\x02", first + 4)
        struct.pack_into("<I", changed, second + 42, 0)
        path.write_bytes(changed)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)

    def test_deflate_actual_length_bounded_despite_false_declared_size_and_crc(self):
        # Forge central AND local size/CRC for the prefix. A ZipExtFile reader
        # trusting file_size can accept that prefix; our decoder must reject it.
        members = support_members({})
        members["PRIVACY.txt"] = b"A" * (MAX_MEMBER_BYTES + 100)
        path = self.bundle(members)
        data = bytearray(path.read_bytes())
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entry = archive.getinfo("PRIVACY.txt")
            struct.pack_into("<I", data, entry.header_offset + 22, 1)
            struct.pack_into("<I", data, entry.header_offset + 14, zlib.crc32(b"A"))
        pos = data.index(b"PK\x01\x02")
        while True:
            namesize, extrasize, commentsize = struct.unpack_from("<HHH", data, pos + 28)
            if data[pos + 46:pos + 46 + namesize] == b"PRIVACY.txt":
                struct.pack_into("<I", data, pos + 24, 1)
                struct.pack_into("<I", data, pos + 16, zlib.crc32(b"A"))
                break
            pos += 46 + namesize + extrasize + commentsize
        path.write_bytes(data)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)

    def test_bundle_arbitrary_text_is_not_echoed_or_claimed_private(self):
        members = support_members({})
        members.update({k: b"SYNTHETIC_PRIVATE Z:/private https://example.invalid =formula"
                        for k in ("summary.zh.md", "summary.en.md", "PRIVACY.txt")})
        path = self.bundle(self.manifest(members))
        for fmt in ("both", "md", "json"):
            code, out, err = self.invoke(["--verify-support", path, "--format", fmt])
            self.assertEqual((code, err), (0, ""))
            self.assertNotIn("SYNTHETIC_PRIVATE", out)
            self.assertNotIn("example.invalid", out)

    def test_zip_streaming_descriptors_validated_and_stored_supported(self):
        class Unseekable(io.BytesIO):
            def seek(self, *args): raise OSError("not seekable")
        stream = Unseekable()
        members = support_members({})
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in members.items(): archive.writestr(name, value)
        path = self.root / "streaming.zip"
        raw = stream.getvalue()
        path.write_bytes(raw)
        self.assertEqual(verify_support(path)["member_count"], 5)
        damaged = bytearray(raw)
        descriptor = damaged.index(b"PK\x07\x08")
        damaged[descriptor + 4] ^= 1
        path.write_bytes(damaged)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        self.assertEqual(verify_support(self.bundle(compression=zipfile.ZIP_STORED))["member_count"], 5)

    def test_zip_nul_names_and_dos_nonregular_attributes_rejected(self):
        path = self.bundle()
        raw = path.read_bytes().replace(b"PRIVACY.txt", b"PRIVACY\x00txt")
        path.write_bytes(raw)
        self.assertEqual(self.invoke(["--verify-support", path])[0], 2)
        for attribute in (0x10, 0x08, 0x40):
            special = zipfile.ZipInfo("support.json")
            special.create_system = 0
            special.external_attr = attribute
            members = [(special if k == "support.json" else k, v) for k, v in support_members({}).items()]
            self.assertEqual(self.invoke(["--verify-support", self.bundle(members)])[0], 2)

    def test_csv_all_states_missing_order_and_bilingual_values(self):
        ids = sorted(IDS)[:6]
        a = self.write(source(*(item(id, state) for id, state in zip(ids, ("pass", "warn", "error", "unknown", "skipped", "pass")))))
        b = self.write(source(item(ids[0])), "b.json")
        outputs = []
        for lang in ("zh", "en"):
            code, out, err = self.invoke(["--history", a, b, "--format=csv", "--lang", lang])
            self.assertEqual((code, err), (0, ""))
            self.assertTrue(out.startswith("\ufeffsequence,check_id,status,version,installation_groups,scan_limited\n"))
            rows = list(csv.DictReader(io.StringIO(out.lstrip("\ufeff"))))
            self.assertEqual(len(rows), 12)
            self.assertEqual([(r["sequence"], r["check_id"]) for r in rows], [(str(n), id) for n in (1, 2) for id in ids])
            self.assertEqual([r["status"] for r in rows[:5]], ["pass", "warn", "error", "unknown", "skipped"])
            self.assertTrue(all(r["status"] == "missing" and not any(r[k] for k in ("version", "installation_groups", "scan_limited")) for r in rows[7:]))
            outputs.append(out)
        self.assertEqual(*outputs)

    def test_csv_known_union_projection_numeric_boolean_and_formula_safety(self):
        for prefix in ("=", "+", "-", "@"):
            obj = {**source(item(version=prefix + "SYNTHETIC_PRIVATE"), item("codex.path", installation_groups=0, scan_limited=False)),
                   "summary": prefix + "SYNTHETIC_PRIVATE", "generated_at": "SYNTHETIC_PRIVATE"}
            obj["findings"][0]["evidence"]["path"] = "Z:/SYNTHETIC_PRIVATE"
            path = self.write(obj)
            code, out, err = self.invoke(["--history", path, path, "--format=csv"])
            self.assertEqual((code, err), (0, ""))
            self.assertNotIn("SYNTHETIC_PRIVATE", out)
            cells = list(csv.reader(io.StringIO(out.lstrip("\ufeff"))))
            self.assertEqual(cells[1][4:], ["0", "false"])
            self.assertTrue(all(not c.startswith(("=", "+", "-", "@")) for row in cells for c in row if c))
        path = self.write(source(item(version="1.2.3"), item("codex.path", installation_groups=32, scan_limited=True)))
        self.assertIn("1.2.3", self.invoke(["--history", path, path, "--format=csv"])[1])

    def test_csv_two_twenty_twentyone_boundaries_and_bom_export(self):
        path = self.write(source(item()))
        for n in (2, 20):
            code, out, err = self.invoke(["--history", *([path] * n), "--format=csv"])
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(len(list(csv.reader(io.StringIO(out)))) - 1, n)
        for n in (1, 21):
            self.assertEqual(self.invoke(["--history", *([path] * n), "--format=csv"])[0], 2)
        for lang in ("zh", "en"):
            dest = self.root / lang
            code, out, err = self.invoke(["--history", path, path, "--format=csv", "--lang", lang, "--output-dir", dest])
            self.assertEqual((code, err, out), (0, "", ""))
            self.assertTrue((dest / f"history.{lang}.csv").read_bytes().startswith(b"\xef\xbb\xbfsequence,"))

    def test_new_exports_preserve_collisions_and_cleanup_only_new_files(self):
        report, bundle = self.write(source(item())), self.bundle()
        for stem, args, ext in (("validation", ["--validate", report], "json"),
                               ("support-verification", ["--verify-support", bundle], "json"),
                               ("history", ["--history", report, report, "--format=csv"], "csv")):
            dest = self.root / stem
            dest.mkdir()
            existing = dest / f"{stem}.zh.{ext}"
            existing.write_bytes(b"keep")
            self.assertEqual(self.invoke([*args, "--output-dir", dest])[0], 2)
            self.assertEqual(existing.read_bytes(), b"keep")
            self.assertEqual(len(list(dest.iterdir())), 1)
        original = Path.open
        for interrupt, expected in ((OSError, 2), (KeyboardInterrupt, 130)):
            for stem, args in (("validation", ["--validate", report]), ("support-verification", ["--verify-support", bundle])):
                dest = self.root / (stem + str(expected))
                dest.mkdir()
                keep = dest / "keep.txt"
                keep.write_text("keep")
                def guarded(p, *a, **kw):
                    if p.parent == dest and p.suffix == ".json":
                        raise interrupt("SYNTHETIC_PRIVATE")
                    return original(p, *a, **kw)
                with patch.object(Path, "open", guarded):
                    code, out, err = self.invoke([*args, "--output-dir", dest])
                self.assertEqual(code, expected)
                self.assertEqual(list(dest.iterdir()), [keep])
                self.assertNotIn("SYNTHETIC_PRIVATE", out + err)

    def test_csv_partial_write_interrupt_cleanup(self):
        report = self.write(source(item()))
        dest = self.root / "csv-interrupt"
        original = Path.open
        class InterruptingStream:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): self.stream.__enter__(); return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def write(self, value):
                self.stream.write(value[:10])
                raise KeyboardInterrupt
        def guarded(p, *a, **kw):
            stream = original(p, *a, **kw)
            return InterruptingStream(stream) if p.suffix == ".csv" else stream
        with patch.object(Path, "open", guarded):
            self.assertEqual(self.invoke(["--history", report, report, "--format=csv", "--output-dir", dest])[0], 130)
        self.assertEqual(list(dest.iterdir()), [])

    def test_new_offline_modes_prohibit_doctor_process_network_registry_and_embedded_paths(self):
        path = self.write(source(item(version="1.2.3", path="Z:/SYNTHETIC_PRIVATE")))
        bundle = self.bundle()
        original = Path.lstat
        with ExitStack() as stack:
            for target in ("windows_ai_doctor.cli.Doctor", "subprocess.Popen", "socket.socket", "socket.getaddrinfo",
                           "windows_ai_doctor.core.registered_distributions", "winreg.OpenKey"):
                stack.enter_context(patch(target, side_effect=AssertionError("offline violation")))
            def guard(p, *a, **kw):
                self.assertNotIn("SYNTHETIC_PRIVATE", str(p))
                return original(p, *a, **kw)
            stack.enter_context(patch.object(Path, "lstat", guard))
            for args in (["--validate", path], ["--verify-support", bundle], ["--history", path, path, "--format=csv"]):
                self.assertEqual(self.invoke(args)[0], 0)

    def test_real_child_process_offline_audit(self):
        path = self.write(source(item(version="1.2.3", path="Z:/SYNTHETIC_PRIVATE")))
        bundle = self.bundle()
        script = '''import sys
sys.path.insert(0, sys.argv[1])
from windows_ai_doctor import cli
def audit(event, args):
    if event.startswith(("subprocess.", "socket.", "winreg.")):
        raise AssertionError("forbidden offline operation")
    if event in ("open", "os.stat") and args and "SYNTHETIC_PRIVATE" in str(args[0]):
        raise AssertionError("imported path access")
sys.addaudithook(audit)
cli.Doctor = lambda **kw: (_ for _ in ()).throw(AssertionError("diagnosis invoked"))
raise SystemExit(cli.main(sys.argv[2:]))
'''
        for args in (["--validate", path, "--format=json"], ["--verify-support", bundle, "--format=json"], ["--history", path, path, "--format=csv"]):
            result = subprocess.run([sys.executable, "-B", "-c", script, str(ROOT), *map(str, args)], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(b"SYNTHETIC_PRIVATE", result.stdout + result.stderr)

    def assert_file_link_rejected(self, mode, suffix):
        target = self.root / ("synthetic-target" + suffix)
        target.write_bytes(b"SYNTHETIC_PRIVATE")
        link = self.root / ("file-link" + suffix)
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.fail(f"Required {mode} real file symlink needs user-authorized privilege (winerror {exc.winerror}); acceptance blocked")
        self.assertEqual(link.lstat().st_reparse_tag, 0xA000000C)
        self.link_evidence = [{"kind": "file_symlink", "reparse_tag": hex(link.lstat().st_reparse_tag), "content_read_attempts": 0}]
        original, attempts = Path.open, []
        def guard(p, *a, **kw):
            if p in (target, link):
                self.link_evidence[0]["content_read_attempts"] += 1
                attempts.append(str(p))
                self.fail("linked content opened")
            return original(p, *a, **kw)
        with patch.object(Path, "open", guard):
            self.assertEqual(self.invoke([mode, link])[0], 2)
        self.assertEqual(attempts, [])

    def test_validate_real_file_symlink_rejected_without_read(self):
        self.assert_file_link_rejected("--validate", ".json")

    def test_verify_real_file_symlink_rejected_without_read(self):
        self.assert_file_link_rejected("--verify-support", ".zip")

    def test_new_json_zip_ancestor_junctions_rejected_before_descendant_access(self):
        target = self.root / "target"
        target.mkdir()
        for mode, suffix in (("--validate", ".json"), ("--verify-support", ".zip")):
            (target / ("input" + suffix)).write_bytes(b"SYNTHETIC_PRIVATE")
            with test_boundaries.BoundaryTests.junction(self, target) as link:
                self.assertEqual(link.lstat().st_reparse_tag, 0xA0000003)
                with test_boundaries.BoundaryTests.no_descendant_access(self, link):
                    self.assertEqual(self.invoke([mode, link / ("input" + suffix)])[0], 2)

    def test_new_json_zip_ancestor_symlinks_rejected_before_descendant_access(self):
        target = self.root / "target"
        target.mkdir()
        link = self.root / "directory-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.fail(f"Required real directory symlink needs user-authorized privilege (winerror {exc.winerror}); acceptance blocked")
        self.assertEqual(link.lstat().st_reparse_tag, 0xA000000C)
        self.link_evidence = [{"kind": "directory_symlink", "reparse_tag": hex(link.lstat().st_reparse_tag), "descendant_access_attempts": 0}]
        for mode, suffix in (("--validate", ".json"), ("--verify-support", ".zip")):
            (target / ("input" + suffix)).write_bytes(b"SYNTHETIC_PRIVATE")
            with test_boundaries.BoundaryTests.no_descendant_access(self, link):
                self.assertEqual(self.invoke([mode, link / ("input" + suffix)])[0], 2)
