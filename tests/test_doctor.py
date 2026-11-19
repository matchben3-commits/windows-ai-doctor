import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from windows_ai_doctor.core import Doctor
from windows_ai_doctor.discovery import bounded_read, discover
from windows_ai_doctor.privacy import safe_version
from windows_ai_doctor.report import json_report, markdown_report
from windows_ai_doctor.runner import Result, clean_env, run_bounded

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
CSC = Path(os.environ.get("SystemRoot", "C:/Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"


def finding(report, id):
    return next(f for f in report["findings"] if f["id"] == id)


class DoctorFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-doctor-test-")
        self.root = Path(self.temp.name)
        self.home = self.root / "private user 用户"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}}
        self.env.update({"PATH": "", "PATHEXT": ".EXE;.CMD;.BAT;.COM", "USERPROFILE": str(self.home), "HOME": str(self.home)})

    def tearDown(self):
        self.temp.cleanup()

    def doctor(self, **kwargs):
        return Doctor(env=self.env, home=self.home, **kwargs).run()

    def cli(self, *args, cwd=None, env=None):
        return subprocess.run([sys.executable, str(ROOT / "doctor.py"), "--home", str(self.home), *args],
                              env=self.env if env is None else env, cwd=cwd or self.root,
                              capture_output=True, timeout=20, encoding="utf-8", errors="strict")

    def npm(self, directory, *, tool="codex", script=None):
        if not NODE:
            self.skipTest("node fixture runtime unavailable")
        directory.mkdir(parents=True, exist_ok=True)
        name = "@openai/codex" if tool == "codex" else "@anthropic-ai/claude-code"
        package = directory / "node_modules" / name
        (package / "bin").mkdir(parents=True, exist_ok=True)
        (package / "package.json").write_text(json.dumps({"name": name, "bin": {tool: "bin/tool.js"},
                                                        "engines": {"node": ">=16"}}), encoding="utf-8")
        (package / "bin/tool.js").write_text(script or 'console.log("codex-cli 1.2.3")', encoding="utf-8")
        marker = f"node_modules/{name}/bin/tool.js"
        for suffix in (".cmd", ".ps1", ""):
            template = (ROOT / "tests/fixtures" / ("npm-node" + (suffix or ".sh") + ".txt")).read_text(encoding="utf-8")
            template = template.replace("node_modules/@openai/codex/bin/codex.js", marker)
            template = template.replace("node_modules\\@openai\\codex\\bin\\codex.js", marker.replace("/", "\\"))
            (directory / (tool + suffix)).write_text(template, encoding="utf-8")
        self.env["PATH"] = os.pathsep.join((str(directory), str(Path(NODE).parent)))
        return package

    def native(self, directory, tool="codex", body='Console.WriteLine("codex-cli 1.2.3"); return 0;'):
        if os.name != "nt" or not CSC.is_file():
            self.skipTest("optional Windows fixture compiler unavailable")
        directory.mkdir(parents=True, exist_ok=True)
        source = directory / "fixture.cs"
        source.write_text("using System; public class Fixture { public static int Main(string[] args) {" + body + "}}", encoding="utf-8")
        exe = directory / (tool + ".exe")
        result = subprocess.run([str(CSC), "/nologo", "/target:exe", "/out:" + str(exe), str(source)],
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, "fixture compilation failed")
        return exe

class DoctorTests(DoctorFixture):
    def test_missing_both_cli_and_bilingual_status_ids(self):
        out = self.root / "out 输出"
        a = self.cli("--lang", "zh", "--output-dir", str(out))
        b = self.cli("--lang", "en", "--format", "json")
        self.assertEqual((a.returncode, b.returncode), (0, 0))
        zh = json.loads((out / "report.zh.json").read_text(encoding="utf-8"))
        en = json.loads(b.stdout)
        for tool in ("codex", "claude"):
            self.assertEqual(finding(zh, tool + ".path")["evidence"]["entries"], [])
            self.assertEqual(finding(zh, tool + ".path")["status"], "warn")
        self.assertEqual([(f["id"], f["status"]) for f in zh["findings"]],
                         [(f["id"], f["status"]) for f in en["findings"]])
        self.assertNotEqual(zh["findings"][0]["summary"], en["findings"][0]["summary"])

    def test_real_npm_query_in_chinese_space_directory_and_wrapper_dedup(self):
        self.npm(self.root / "工具 路径")
        proc = self.cli("--format", "json", "--tools", "codex")
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(finding(report, "codex.version")["evidence"]["version"], "1.2.3")
        evidence = finding(report, "codex.path")["evidence"]
        self.assertEqual(evidence["installation_groups"], 1)
        self.assertEqual(len(evidence["entries"]), 3 if os.name == "nt" else 1)
        self.assertEqual(finding(report, "codex.path")["status"], "pass")

    def test_distinct_installations_shadow_in_path_order(self):
        a, b = self.root / "a", self.root / "b"
        self.npm(a)
        self.npm(b)
        self.env["PATH"] = os.pathsep.join((str(a), str(b), str(Path(NODE).parent)))
        report = self.doctor(versions=False)
        f = finding(report, "codex.path")
        self.assertEqual(f["evidence"]["installation_groups"], 2)
        self.assertEqual(f["status"], "warn")
        self.assertEqual(f["evidence"]["cmd_path_candidate"], f["evidence"]["entries"][0]["path"])

    def test_unknown_wrapper_is_never_executed(self):
        directory = self.root / "unknown"
        directory.mkdir()
        suffix = ".cmd" if os.name == "nt" else ""
        (directory / ("codex" + suffix)).write_text("arbitrary untrusted command", encoding="utf-8")
        self.env["PATH"] = str(directory)
        def forbidden(*a, **kw):
            raise AssertionError("must not execute")
        report = self.doctor(runner=forbidden)
        self.assertEqual(finding(report, "codex.install")["status"], "unknown")
        self.assertEqual(finding(report, "codex.version")["status"], "unknown")

    def test_native_cli_with_spaces_does_not_require_node(self):
        exe = self.native(self.root / "原生 工具")
        self.env["PATH"] = str(exe.parent)
        proc = self.cli("--format", "json")
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(finding(report, "codex.version")["evidence"]["version"], "1.2.3")
        self.assertFalse(finding(report, "codex.dependency")["evidence"]["node_required"])

    def test_claude_native_and_npm_native_without_node(self):
        exe = self.native(self.root / "claude native", tool="claude",
                          body='Console.WriteLine("2.1.0 (Claude Code)"); return 0;')
        self.env["PATH"] = str(exe.parent)
        report = self.doctor(tools=("claude",))
        self.assertEqual(finding(report, "claude.version")["evidence"]["version"], "2.1.0")
        self.assertFalse(finding(report, "claude.dependency")["evidence"]["node_required"])
        package = exe.parent / "node_modules/@anthropic-ai/claude-code"
        package.mkdir(parents=True)
        shutil.copyfile(exe, package / "claude.exe")
        exe.unlink()
        (package / "package.json").write_text(json.dumps({"name": "@anthropic-ai/claude-code", "bin": {"claude": "claude.exe"}}), encoding="utf-8")
        wrapper = (ROOT / "tests/fixtures/npm-native.cmd.txt").read_text(encoding="utf-8")
        (exe.parent / "claude.cmd").write_text(wrapper, encoding="utf-8")
        report = self.doctor(tools=("claude",))
        self.assertEqual(finding(report, "claude.install")["evidence"]["kind"], "npm-native")
        self.assertEqual(finding(report, "claude.version")["evidence"]["version"], "2.1.0")

    def test_npm_missing_or_incompatible_node_is_conditional_error(self):
        directory = self.root / "npm"
        package = self.npm(directory)
        self.env["PATH"] = str(directory)
        self.assertEqual(finding(self.doctor(), "codex.dependency")["status"], "error")
        self.env["PATH"] += os.pathsep + str(Path(NODE).parent)
        metadata = package / "package.json"
        content = json.loads(metadata.read_text(encoding="utf-8"))
        content["engines"]["node"] = ">=9999"
        metadata.write_text(json.dumps(content), encoding="utf-8")
        report = self.doctor()
        self.assertEqual(finding(report, "codex.dependency")["status"], "error")

    def test_oversized_cli_output_still_completes_other_checks(self):
        self.npm(self.root / "noisy", script='process.stdout.write("x".repeat(1000000))')
        proc = self.cli("--format", "json")
        self.assertEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertEqual(finding(report, "codex.version")["evidence"]["reason"], "output_limit")
        self.assertEqual(finding(report, "wsl.internal")["status"], "skipped")

    def test_reparse_guard_without_symlink_privilege(self):
        from types import SimpleNamespace
        import stat
        fake = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_file_attributes=0x400)
        with patch.object(Path, "lstat", return_value=fake), patch.object(Path, "open", side_effect=AssertionError("must not open")):
            with self.assertRaises(ValueError):
                bounded_read(self.home / ".codex/config.toml")

    def test_custom_home_overrides_invalid_default_and_both_config_errors_continue(self):
        for tool, variable, dirname, filename in (
            ("codex", "CODEX_HOME", ".codex", "config.toml"),
            ("claude", "CLAUDE_CONFIG_DIR", ".claude", "settings.json")):
            default = self.home / dirname
            default.mkdir()
            (default / filename).write_text("invalid", encoding="utf-8")
            custom = self.root / (tool + " 自定义")
            custom.mkdir()
            (custom / filename).write_text('model = "sample"' if tool == "codex" else '{}', encoding="utf-8")
            self.env[variable] = str(custom)
        report = self.doctor()
        for tool in ("codex", "claude"):
            self.assertEqual(finding(report, tool + ".config.user")["status"], "pass")
        (Path(self.env["CODEX_HOME"]) / "config.toml").write_text('x = [', encoding="utf-8")
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "settings.json").write_text('{"x":', encoding="utf-8")
        proc = self.cli("--format", "json")
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        for tool in ("codex", "claude"):
            self.assertEqual(finding(report, tool + ".config.user")["status"], "error")
        self.assertTrue(any(f["id"] == "wsl.internal" for f in report["findings"]))

    def test_json_strictness_and_large_or_non_utf8_config(self):
        directory = self.home / ".claude"
        directory.mkdir()
        path = directory / "settings.json"
        for content in (b"[]", b'{"x":NaN}', b'{"x":Infinity}'):
            path.write_bytes(content)
            self.assertEqual(finding(self.doctor(), "claude.config.user")["status"], "error")
        for content in (b"x" * (1024 * 1024 + 1), b"\xff"):
            path.write_bytes(content)
            self.assertEqual(finding(self.doctor(), "claude.config.user")["status"], "unknown")

    def test_relative_override_not_silently_replaced(self):
        self.env["CODEX_HOME"] = "relative"
        f = finding(self.doctor(), "codex.config.user")
        self.assertEqual(f["status"], "unknown")
        self.assertEqual(f["evidence"]["location_source"], "CODEX_HOME")

    def test_project_layer_syntax_and_no_auth_or_history_reads(self):
        project = self.root / "project"
        (project / ".claude").mkdir(parents=True)
        (project / ".claude/settings.local.json").write_text('{}', encoding="utf-8")
        for directory in (self.home / ".codex", self.home / ".claude"):
            directory.mkdir()
            for name in ("auth.json", ".credentials.json", "history.jsonl", "chat.txt"):
                (directory / name).write_text("private", encoding="utf-8")
        opened = []
        original = Path.open
        def track(path, *args, **kwargs):
            opened.append(path.name)
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", track):
            report = self.doctor(project=project)
        self.assertEqual(finding(report, "claude.config.local")["status"], "pass")
        self.assertTrue(all(name not in opened for name in ("auth.json", ".credentials.json", "history.jsonl", "chat.txt")))

    def test_config_link_to_auth_is_not_read(self):
        directory = self.home / ".codex"
        directory.mkdir()
        secret = directory / "auth.json"
        secret.write_text("private", encoding="utf-8")
        try:
            (directory / "config.toml").symlink_to(secret)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        self.assertEqual(finding(self.doctor(), "codex.config.user")["status"], "unknown")

    def test_timeout_and_nonzero_continue_reports(self):
        self.npm(self.root / "slow", script='setTimeout(() => {}, 30000)')
        start = time.monotonic()
        proc = self.cli("--timeout", "0.3", "--format", "json")
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(finding(json.loads(proc.stdout), "codex.version")["evidence"]["reason"], "timeout")
        self.npm(self.root / "exit", script='process.stderr.write("private error"); process.exit(7)')
        proc = self.cli("--format", "json")
        report = json.loads(proc.stdout)
        f = finding(report, "codex.version")
        self.assertEqual(f["status"], "unknown")
        self.assertEqual(f["evidence"]["returncode"], 7)
        self.assertTrue("private error" not in proc.stdout + proc.stderr)

    def test_sensitive_markers_never_reach_json_markdown_stdout_stderr(self):
        markers = ["SYNTHETIC_PRIVATE_TOKEN_987654", "SYNTHETIC_PRIVATE_USER_987654", "SYNTHETIC_PASSWORD_987654"]
        path = self.root / markers[1]
        payload = "sk-" + markers[0] + " https://" + markers[1] + ":" + markers[2] + "@example.invalid/a?api_key=" + markers[0]
        self.npm(path, script="process.stdout.write(" + json.dumps(payload) + "); process.stderr.write(" + json.dumps(payload) + "); process.exit(9)")
        directory = self.home / ".claude"
        directory.mkdir()
        # Malformed syntax: a parser would normally echo the failing line/value.
        (directory / "settings.json").write_text('{"password": ' + payload, encoding="utf-8")
        config = self.home / ".codex"
        config.mkdir()
        (config / "config.toml").write_text('token = "' + payload + '"', encoding="utf-8")
        for language in ("zh", "en"):
            out = self.root / language
            proc = self.cli("--lang", language, "--output-dir", str(out))
            self.assertEqual(proc.returncode, 1)
            outputs = proc.stdout + proc.stderr + "".join(p.read_text(encoding="utf-8") for p in out.iterdir())
            self.assertTrue(all(v not in outputs for v in [*markers, str(self.home), str(path), "example.invalid"]))

    def test_socket_denied_offline_bilingual_reports(self):
        def deny(*args, **kwargs):
            raise AssertionError("network access forbidden")
        with patch.object(socket, "socket", deny), patch.object(socket, "create_connection", deny), patch.object(socket, "getaddrinfo", deny), patch.object(socket, "gethostname", deny):
            for lang in ("zh", "en"):
                report = self.doctor(lang=lang)
                self.assertTrue(json.loads(json_report(report))["findings"])
                self.assertTrue(markdown_report(report))

    def test_real_cli_with_network_audit_denied(self):
        for lang in ("zh", "en"):
            proc = subprocess.run([sys.executable, str(ROOT / "tests/offline_check.py"),
                                   "--home", str(self.home), "--lang", lang, "--format", "json"],
                                  env=self.env, cwd=self.root, capture_output=True,
                                  timeout=10, encoding="utf-8")
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(proc.stdout)["language"], lang)

    def test_wsl_default_never_executes_and_synthetic_visibility(self):
        if os.name != "nt":
            self.skipTest("Windows WSL scenarios")
        def deny(*args, **kwargs):
            raise AssertionError("WSL must not execute by default")
        with patch("windows_ai_doctor.core.system_wsl_launcher", return_value=None), patch("windows_ai_doctor.core.registered_distributions", return_value=(0, "registration_key_absent")):
            report = self.doctor(runner=deny)
            self.assertFalse(finding(report, "wsl.launcher")["evidence"]["present"])
            self.assertEqual(finding(report, "wsl.internal")["status"], "skipped")
        exe = self.native(self.root / "wsl", tool="wsl", body="return 0;")
        with patch("windows_ai_doctor.core.system_wsl_launcher", return_value=exe), patch("windows_ai_doctor.core.registered_distributions", return_value=(1, "registry_observation")):
            report = self.doctor(wsl_list=True)
            self.assertEqual(finding(report, "wsl.running")["evidence"]["running_count"], 0)
            self.assertEqual(finding(report, "wsl.internal")["status"], "skipped")
        with patch("windows_ai_doctor.core.system_wsl_launcher", return_value=exe), patch("windows_ai_doctor.core.registered_distributions", return_value=(None, "registry_unreadable")):
            report = self.doctor(runner=deny)
            self.assertEqual(finding(report, "wsl.inventory")["status"], "unknown")
            self.assertEqual(finding(report, "wsl.running")["status"], "skipped")

    def test_cli_invalid_args_and_export_errors_hide_paths(self):
        marker = "SYNTHETIC_PRIVATE_ARGUMENT_987654"
        for args in (("--timeout", marker), ("--timeout", "nan"), ("--tools", marker), ("--" + marker,)):
            proc = self.cli(*args)
            self.assertEqual(proc.returncode, 2)
            self.assertTrue(marker not in proc.stdout + proc.stderr)
        out = self.root / marker
        out.write_text("occupied", encoding="utf-8")
        proc = self.cli("--output-dir", str(out))
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(marker not in proc.stdout + proc.stderr)

    def test_existing_reports_preserved_and_clean_cwd_start(self):
        out = self.root / "reports"
        proc = self.cli("--output-dir", str(out))
        self.assertEqual(proc.returncode, 0)
        content = (out / "report.zh.json").read_bytes()
        proc = self.cli("--output-dir", str(out))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(content, (out / "report.zh.json").read_bytes())
        self.assertEqual(self.cli("--help").returncode, 0)

    def test_version_allowlist_rejects_noise_or_urls(self):
        self.assertEqual(safe_version("codex-cli 1.2.3\n", "codex"), "1.2.3")
        self.assertEqual(safe_version("2.1.0 (Claude Code)", "claude"), "2.1.0")
        for text in ("codex-cli 1.2.3\nprivate", "https://user:password@example.invalid", "codex-cli 1.2.3\x1b]8;;url"):
            self.assertIsNone(safe_version(text, "codex"))

    def test_clean_environment_excludes_tokens_and_config_override(self):
        self.env.update({"ANTHROPIC_API_KEY": "private", "OPENAI_API_KEY": "private", "NODE_OPTIONS": "private", "PYTHONPATH": "private"})
        envroot = self.root / "env"
        envroot.mkdir()
        result = clean_env(envroot, self.env)
        self.assertTrue(all(k not in result for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "NODE_OPTIONS", "PYTHONPATH")))
        self.assertEqual(result["DISABLE_UPDATES"], "1")
        self.assertTrue(Path(result["CODEX_HOME"]).is_relative_to(envroot))

    def test_runner_caps_output_and_terminates_process_tree(self):
        result = run_bounded([sys.executable, "-c", 'print("x"*1000000)'], timeout=2, limit=1024)
        self.assertEqual(result.reason, "output_limit")
        self.assertLessEqual(result.captured_bytes, 1025)
        pidfile = self.root / "child.pid"
        code = "import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)"
        result = run_bounded([sys.executable, "-c", code, str(pidfile)], timeout=0.6)
        self.assertEqual(result.reason, "timeout")
        self.assertTrue(pidfile.is_file())
        pid = int(pidfile.read_text())
        if os.name == "nt":
            import ctypes as c
            k = c.WinDLL("kernel32", use_last_error=True)
            k.OpenProcess.argtypes = [c.c_ulong, c.c_int, c.c_ulong]
            k.OpenProcess.restype = c.c_void_p
            k.WaitForSingleObject.argtypes = [c.c_void_p, c.c_ulong]
            k.CloseHandle.argtypes = [c.c_void_p]
            handle = k.OpenProcess(0x100000, False, pid)
            if handle:
                self.assertEqual(k.WaitForSingleObject(handle, 0), 0)
                k.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                # A killed child may briefly remain a zombie until init reaps it.
                status = Path(f"/proc/{pid}/stat")
                self.assertTrue(status.exists() and ") Z " in status.read_text())

    def test_runner_child_exit_also_removes_descendants(self):
        pidfile = self.root / "child.pid"
        code = "import subprocess,sys; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); Path(sys.argv[1]).write_text(str(p.pid)); print('done')"
        result = run_bounded([sys.executable, "-c", code, str(pidfile)], timeout=2)
        self.assertEqual(result.reason, "ok")
        self.assertTrue("done" in result.output)
        pid = int(pidfile.read_text())
        if os.name == "nt":
            import ctypes as c
            k = c.WinDLL("kernel32", use_last_error=True)
            k.OpenProcess.argtypes = [c.c_ulong, c.c_int, c.c_ulong]
            k.OpenProcess.restype = c.c_void_p
            k.WaitForSingleObject.argtypes = [c.c_void_p, c.c_ulong]
            k.CloseHandle.argtypes = [c.c_void_p]
            handle = k.OpenProcess(0x100000, False, pid)
            if handle:
                self.assertEqual(k.WaitForSingleObject(handle, 0), 0)
                k.CloseHandle(handle)
        else:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                status = Path(f"/proc/{pid}/stat")
                self.assertTrue(status.exists() and ") Z " in status.read_text())


if __name__ == "__main__":
    unittest.main()
