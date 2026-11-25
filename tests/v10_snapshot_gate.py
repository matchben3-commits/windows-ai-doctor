"""Dev2 integration evidence, separate from the inherited 203-case suite.

All state is under a fresh caller-chosen directory. Authored explanation cases
are labelled synthetic; they do not replace independent real-scene acceptance.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from windows_ai_doctor import snapshot, snapshot_schema
from windows_ai_doctor.comparison_key import KeyStore, WindowsProtection
from windows_ai_doctor.compare import MAX_BYTES, decode_object


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def session_transport_checks(check):
    # Windows PowerShell can prepend one UTF-8 BOM to its native stdin pipe.
    bom = b"\xef\xbb\xbf"
    value = {"command": "codex", "kind": "function", "path": None}
    raw = json.dumps(value).encode("utf-8")
    check("session_plain_utf8", snapshot.read_session(raw, "codex") == value)
    check("session_utf8_bom_crlf", snapshot.read_session(bom + raw + b"\r\n", "codex") == value)
    application = {**value, "kind": "application", "path": "C:\\测试\\codex.exe"}
    check("session_bom_unicode_path", snapshot.read_session(bom + json.dumps(application, ensure_ascii=False).encode("utf-8"), "codex") == application)
    padded = bom + raw + b" " * (MAX_BYTES - len(bom + raw))
    check("session_bom_exact_byte_limit", snapshot.read_session(padded, "codex") == value)
    for label, payload in (
        ("double_bom", bom + bom + raw),
        ("misplaced_bom", b" " + bom + raw),
        ("duplicate_key", bom + b'{"command":"codex","command":"codex","kind":"function","path":null}'),
        ("invalid_utf8", bom + raw + b"\xff"),
        ("oversize_with_bom", padded + b" "),
        ("oversize_plain", raw + b" " * (MAX_BYTES + 1 - len(raw))),
        ("unknown_field", bom + json.dumps({**value, "private": "DEV2_PRIVATE_CANARY"}).encode("utf-8")),
        ("wrong_command", bom + raw.replace(b"codex", b"claude")),
    ):
        try:
            snapshot.read_session(payload, "codex")
        except ValueError:
            check("session_reject_" + label)
        else:
            raise AssertionError("session_accepted_" + label)
    try:
        decode_object(bom + raw)
    except ValueError:
        check("legacy_decoder_bom_policy_unchanged")
    else:
        raise AssertionError("legacy_decoder_bom_policy_changed")


def authored():
    empty = snapshot.environment(b"x" * 32, {}, True)
    return {"report_type": "environment_snapshot", "schema_version": "snapshot-1.0", "captured_at": "2026-11-25T00:00:00Z",
            "command": "codex", "session_role": "unspecified", "symptom": "unspecified", "algorithm": snapshot_schema.ALGORITHM,
            "scope": {"code": "scope_" + "0" * 64, "key_status": "available"},
            "context": {"shell": "unknown", "elevated": None, "elevation_status": "unknown"},
            "environment": copy.deepcopy(empty), "persistent_environment": {"user": copy.deepcopy(empty), "machine": copy.deepcopy(empty)},
            "resolution": {"status": "unknown", "source": "none", "kind": "unknown", "target": "codex",
                           "preferred_code": None, "candidates": [], "scan_limited": False},
            "observations": {"tool_execution": "not_performed"},
            "command_result": {"status": "unverified", "source": "none", "recorded_at": "2026-11-25T00:00:00Z",
                               "executed_at": None, "session_match": "unknown"}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    dest = args.evidence.absolute()
    dest.mkdir(parents=True, exist_ok=False)
    checks, steps, blocked = [], [], []
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    for name in ("LOCALAPPDATA", "APPDATA", "HOME", "USERPROFILE", "TEMP", "TMP"):
        folder = dest / ("sandbox-" + name.lower())
        folder.mkdir()
        env[name] = str(folder)
    tools_a, tools_b = dest / "tools-a", dest / "tools-b"
    tools_a.mkdir()
    tools_b.mkdir()
    # Header-only native fixtures test classification/fingerprinting, not execution.
    for folder, value in ((tools_a, b"MZdev2-fixture-A"), (tools_b, b"MZdev2-fixture-B")):
        (folder / "codex.exe").write_bytes(value)
    env.update(PATH=str(tools_a) + ";" + str(tools_b), PATHEXT=".EXE;.CMD", COMSPEC=str(Path(env["SYSTEMROOT"]) / "System32/cmd.exe"),
               WAD_PRIVATE_CANARY="DEV2_PRIVATE_CANARY_7a31")
    command = [sys.executable, "-I", "-B", str(ROOT / "doctor.py")]
    state = Path(env["LOCALAPPDATA"])
    def signature():
        return {f.relative_to(state).as_posix(): (f.stat().st_mtime_ns, hashlib.sha256(f.read_bytes()).hexdigest())
                for f in state.rglob("*") if f.is_file()}
    def check(label, truth=True):
        if not truth:
            raise AssertionError(label)
        checks.append(label)
        write(dest / "checks.json", checks)
    def run(label, options, expected=(0,), input=None, override=None):
        proc = subprocess.run(command + list(map(str, options)), env=override or env, cwd=dest,
                              input=input, capture_output=True, timeout=60)
        if proc.stdout:
            (dest / (label + ".stdout")).write_bytes(proc.stdout)
        if proc.stderr:
            (dest / (label + ".stderr")).write_bytes(proc.stderr)
        steps.append({"label": label, "command": command + list(map(str, options)), "exit_code": proc.returncode,
                      "expected": list(expected), "stdout_bytes": len(proc.stdout), "stderr_bytes": len(proc.stderr)})
        write(dest / "steps.json", steps)
        check(label + ".exit", proc.returncode in expected)
        check(label + ".non_echo", b"DEV2_PRIVATE_CANARY" not in proc.stdout + proc.stderr)
        return proc.stdout
    session_transport_checks(check)
    old = dest / "diagnosis.json"
    write(old, {"schema_version": "1.0", "findings": [{"id": "codex.path", "status": "pass", "evidence": {}}]})
    sample = dest / "authored.json"
    write(sample, authored())
    # XC-C6 first-use: missing state stays absent in every read-only path.
    for label, options in (
        ("schema", ["--snapshot-schema"]), ("key_missing", ["--compare-key", "status"]),
        ("snapshot_validate", ["--validate-snapshot", sample]),
        ("diagnosis_validate", ["--validate", old, "--format", "json"]),
        ("diagnosis_compare", ["--compare", old, old, "--format", "json"]),
        ("diagnosis_history", ["--history", old, old, "--format", "json"]),
        ("diagnosis_catalog", ["--catalog", "--format", "json"]), ("diagnosis_schema", ["--schema"]),
        ("diagnosis_support", ["--support", old, "--output-dir", dest / "support"]),
        ("diagnosis_baseline", ["--baseline", old, "--home", env["HOME"], "--project", tools_a, "--no-version", "--format", "json"])):
        run(label, options, (0, 1) if label == "diagnosis_baseline" else (0,))
        check(label + ".no_key_creation", not list(state.iterdir()))
    run("capture_missing", ["--capture", "--command", "codex"], (2,))
    missing = json.loads(run("compare_missing", ["--compare-snapshots", sample, sample, "--format", "json"]))
    check("missing_key_incomparable_not_zero", missing["reason"] == "key_unavailable" and missing["differences"] is None and not list(state.iterdir()))
    schema = json.loads((dest / "schema.stdout").read_bytes())
    check("independent_schema_identity", "environment-snapshot-1.0" in schema["$id"] and schema["properties"]["schema_version"]["const"] == "snapshot-1.0")
    run("key_init", ["--compare-key", "init"])
    initialized = signature()
    run("key_init_existing", ["--compare-key", "init"], (2,))
    check("init_preserves_existing", signature() == initialized)
    # Exercise the actual CLI stdin boundary, including a deterministic BOM.
    session_args = ["--capture", "--command", "codex", "--session-metadata-stdin"]
    session_raw = b'{"command":"codex","kind":"function","path":null}\r\n'
    for label, payload in (("session_cli_plain", session_raw), ("session_cli_bom", b"\xef\xbb\xbf" + session_raw)):
        captured_session = json.loads(run(label, session_args, input=payload))
        check(label + ".original_function", captured_session["resolution"]["kind"] == "function"
              and captured_session["resolution"]["source"] == "original_runspace_user_supplied"
              and captured_session["observations"]["tool_execution"] == "not_performed")
    session_limit = b"\xef\xbb\xbf" + session_raw
    session_limit += b" " * (65536 - len(session_limit))
    at_limit = json.loads(run("session_cli_bom_limit", session_args, input=session_limit))
    check("session_cli_bom_limit.original_function", at_limit["resolution"]["kind"] == "function")
    run("session_cli_bom_over_limit", session_args, (2,), input=session_limit + b" ")
    run("session_cli_bom_invalid_utf8", session_args, (2,), input=b"\xef\xbb\xbf" + session_raw + b"\xff")
    run("session_cli_bom_duplicate", session_args, (2,), input=b'\xef\xbb\xbf{"command":"codex","command":"DEV2_PRIVATE_CANARY","kind":"function","path":null}')
    check("session_cli_preserves_key", signature() == initialized)
    # Capture with no original-runspace evidence must keep resolution unknown.
    captured = json.loads(run("capture", ["--capture", "--command", "codex"]))
    check("python_capture_unknown_original_resolution", captured["resolution"]["status"] == "unknown" and captured["command_result"]["source"] == "none")
    check("capture_candidates_and_launcher_only", len(captured["resolution"]["candidates"]) == 2 and all(c["launcher"]["content_code"].startswith("launcher_") for c in captured["resolution"]["candidates"]))
    product = json.dumps(captured)
    check("capture_privacy_canaries", all(value not in product for value in (str(dest).replace("\\", "\\\\"), "DEV2_PRIVATE_CANARY", "WAD_PRIVATE_CANARY", "MZdev2-fixture")))
    cap_path = dest / "captured.json"
    write(cap_path, captured)
    comparison = json.loads(run("compare_self", ["--compare-snapshots", cap_path, cap_path, "--format", "json"]))
    comparison_path = dest / "comparison.json"
    write(comparison_path, comparison)
    check("same_scope_unknown_not_equal_environment", comparison["comparability"] == "same_scope" and "original_session_resolution" in comparison["evidence_gaps"])
    # XC-C5 explicit cross-feeding matrix. Both new artifacts are rejected by all
    # old report consumers; the new reader rejects diagnosis/schema/comparison.
    for kind, path in (("snapshot", cap_path), ("comparison", comparison_path)):
        for mode, tail in (("validate", [path]), ("baseline", [path, "--no-version"]),
                           ("compare", [path, old]), ("history", [old, path]),
                           ("support", [path, "--output-dir", dest / (kind + "-bad-support")])):
            run("cross_" + kind + "_" + mode, ["--" + mode, *tail], (2,))
    for index, path in enumerate((old, comparison_path, dest / "schema.stdout")):
        run("new_reader_reject_" + str(index), ["--validate-snapshot", path], (2,))
    for index, options in enumerate((
        ["--capture", "--command", "DEV2_PRIVATE_CANARY"], ["--capture", "--command", "codex", "--symptom", "DEV2_PRIVATE_CANARY"],
        ["--capture", "--command", "codex", "--command-result", "DEV2_PRIVATE_CANARY"],
        ["--capture", "--command", "codex", "--no-version"], ["--snapshot-schema", "--schema"],
        ["--snapshot-schema", "--format", "json"], ["--capture"], ["--compare-key", "status", "--home", tools_a],
        ["--compare-snapshots", cap_path, cap_path, "--fail-on", "warn"], ["--command", "codex"],
        ["--validate-snapshot", cap_path, "--format", "csv"], ["--capture", "--command", "codex", "--format", "both"],
        ["--compare-key", "rotate", "--output-dir", dest / "bad-key-export"])):
        run("arguments_" + str(index), options, (2,))
    malformed = [b'{"report_type":"environment_snapshot","report_type":"environment_snapshot"}', b'{"x":NaN}',
                 b'{"x":1234567890123}', b'{"x":' + b'[' * 17 + b'0' + b']' * 17 + b'}', b' ' * (2 * 1024 * 1024 + 1), b'\xff',
                 json.dumps({**captured, "private": "DEV2_PRIVATE_CANARY"}).encode()]
    for index, raw in enumerate(malformed):
        bad = dest / ("malformed-" + str(index) + ".json")
        bad.write_bytes(raw)
        run("bounds_" + str(index), ["--validate-snapshot", bad], (2,))
    for label, modify in (
        ("result_none_success", lambda s: s["command_result"].update(status="success")),
        ("controlled_no_time", lambda s: s["command_result"].update(status="failure", source="controlled_test")),
        ("invalid_time", lambda s: s.update(captured_at="2026-02-30T00:00:00Z")),
        ("candidate_limit", lambda s: s["resolution"].update(candidates=s["resolution"]["candidates"] * 129)),
        ("elevation_null", lambda s: s["context"].update(elevated=None, elevation_status="observed")),
        ("launcher_unknown_with_code", lambda s: s["resolution"]["candidates"][0]["launcher"].update(status="unknown"))):
        bad = copy.deepcopy(captured)
        modify(bad)
        path = dest / (label + ".json")
        write(path, bad)
        run(label, ["--validate-snapshot", path], (2,))
    # Read-only paths neither mutate key bytes/mtime nor execute diagnosis.
    with patch.dict(os.environ, env, clear=True), patch("windows_ai_doctor.cli.Doctor", side_effect=AssertionError("diagnosis_started")):
        from windows_ai_doctor import cli
        from contextlib import redirect_stdout, redirect_stderr
        import io
        for options in (["--snapshot-schema"], ["--validate-snapshot", str(cap_path)],
                        ["--compare-snapshots", str(cap_path), str(cap_path), "--format", "json"],
                        ["--compare-key", "status"]):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                check("readonly_no_diagnosis_" + options[0], cli.main(options) == 0)
    check("readonly_key_unchanged", signature() == initialized)
    with patch.dict(os.environ, env, clear=True):
        from windows_ai_doctor.discovery import Entry
        large = dest / "codex-large.exe"
        large.write_bytes(b"MZ" + b"x" * (1024 * 1024))
        check("oversize_launcher_no_partial_identity", snapshot.launcher(KeyStore().load(), Entry(large, kind="native"))["content_code"] is None)
        sample_entry = Entry(tools_a / "codex.exe", kind="native")
        original_read = snapshot.bounded_read
        def changing_read(path):
            raw = original_read(path)
            path.write_bytes(raw + b"changed-fixture")
            return raw
        with patch.object(snapshot, "bounded_read", changing_read):
            check("changing_launcher_no_identity", snapshot.launcher(KeyStore().load(), sample_entry)["content_code"] is None)
    # Key separation, protection failure and atomic-rotation failure boundaries.
    with patch.dict(os.environ, env, clear=True):
        store = KeyStore()
        material, encrypted = store.load(), store.path.read_bytes()
        protection = WindowsProtection()
        protection.verify(store.directory)
        protection.verify(store.path)
        check("protected_single_user_dacl_verified")
        check("dpapi_not_plaintext", material not in encrypted)
        from windows_ai_doctor.comparison_key import derive
        check("hmac_purpose_separation", len({derive(material, purpose, b"same-input") for purpose in ("path", "launcher", "scope", "installation")}) == 4)
        check("no_key_material_in_capture", material.hex() not in product)
        original_state = signature()
        with patch("windows_ai_doctor.comparison_key.os.replace", side_effect=OSError("fixture_replace_failure")):
            try:
                store.manage("rotate")
            except OSError:
                pass
            else:
                raise AssertionError("rotation_failure_accepted")
        check("failed_rotation_keeps_old_key", signature() == original_state and not list(store.directory.glob("*.tmp")))
        store.path.write_bytes(b"corrupt-test-ciphertext")
        corrupt = signature()
        check("corrupt_dpapi_unavailable", store.status()["status"] == "unavailable")
        run("corrupt_key_capture", ["--capture", "--command", "codex"], (2,))
        run("corrupt_key_rotate", ["--compare-key", "rotate"], (2,))
        check("corrupt_state_not_reinitialized", signature() == corrupt)
        store.path.write_bytes(encrypted)
        icacls = str(Path(env["SYSTEMROOT"]) / "System32/icacls.exe")
        broaden = subprocess.run([icacls, str(store.path), "/grant", "*S-1-1-0:R"], capture_output=True, timeout=10)
        try:
            check("unsafe_acl_fixture_created", broaden.returncode == 0)
            check("unsafe_acl_fails_closed", store.status()["status"] == "unavailable")
            run("unsafe_acl_capture", ["--capture", "--command", "codex"], (2,))
        finally:
            restored = subprocess.run([icacls, str(store.path), "/remove:g", "*S-1-1-0"], capture_output=True, timeout=10)
        check("safe_acl_restored", restored.returncode == 0 and store.status()["status"] == "available")
    import zipfile
    bundle = next((dest / "support").glob("*.zip"))
    with zipfile.ZipFile(bundle) as archive:
        contents = b"\n".join(archive.read(name) for name in archive.namelist())
        check("support_excludes_snapshot_key_codes", all(token not in contents for token in
              (b"scope_", b"launcher_", b"installation_", b"key.dat", b"environment_snapshot", material.hex().encode())))
    run("capture_export", ["--capture", "--command", "codex", "--output-dir", dest / "capture-export"])
    saved = (dest / "capture-export/snapshot.json").read_bytes()
    run("capture_export_collision", ["--capture", "--command", "codex", "--output-dir", dest / "capture-export"], (2,))
    check("export_collision_preserves_snapshot", saved == (dest / "capture-export/snapshot.json").read_bytes())
    # Original runspace helper: a function with a private body must not execute.
    ps = Path(env["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    marker = dest / "function-was-executed.txt"
    ps_script = dest / "helper-fixture.ps1"
    quote = lambda s: "'" + str(s).replace("'", "''") + "'"
    ps_script.write_text("function codex { [IO.File]::WriteAllText(" + quote(marker) + ", 'DEV2_PRIVATE_CANARY') }\n& " + quote(ROOT / "scripts/Capture-WADSnapshot.ps1") + " -Command codex -SessionRole failing -Symptom not_found -Python " + quote(sys.executable) + "\nexit $LASTEXITCODE\n", encoding="utf-8")
    proc = subprocess.run([str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)], env=env, capture_output=True, timeout=60)
    (dest / "original-runspace.stdout").write_bytes(proc.stdout)
    if proc.stderr:
        (dest / "original-runspace.stderr").write_bytes(proc.stderr)
    check("helper_exit", proc.returncode == 0)
    helper = json.loads(proc.stdout)
    check("helper_function_without_invocation", helper["resolution"]["kind"] == "function" and not marker.exists() and b"DEV2_PRIVATE_CANARY" not in proc.stdout + proc.stderr)
    # Authored interpretation cases deliberately remain distinct from live tests.
    with patch.dict(os.environ, env, clear=True):
        a, b = copy.deepcopy(captured), copy.deepcopy(captured)
        for s, role, directory in ((a, "working", tools_a), (b, "failing", tools_b)):
            s.update(session_role=role, symptom="none" if role == "working" else "wrong_version")
            s["resolution"].update(status="observed", source="original_runspace_user_supplied", kind="application",
                                   preferred_code=snapshot.path_code(KeyStore().load(), str(directory / "codex.exe")))
        b["environment"]["path"]["entries"].reverse()
        report = snapshot.compare_snapshots(a, b)
        write(dest / "synthetic-positive.json", report)
        check("synthetic_path_and_precedence_possible", {e["scenario"] for e in report["explanations"]} == {"process_path_difference", "multiple_launcher_precedence"} and all(e["level"] == "possible" for e in report["explanations"]))
        b["resolution"].update(kind="alias", preferred_code=None)
        check("synthetic_alias_only_possible", "alias_function_shadowing" in {e["scenario"] for e in snapshot.compare_snapshots(a, b)["explanations"]})
        for s in (a, b):
            s["command_result"].update(status="success", source="user_report", session_match="original")
        report = snapshot.compare_snapshots(a, b)
        write(dest / "synthetic-path-both-success.json", report)
        check("synthetic_both_success_no_fault_claim", report["outcome"] == "both_commands_succeeded" and not report["explanations"] and not report["verification"])
        check("user_report_rendering", "用户报告成功" in snapshot.comparison_markdown(report))
        b = copy.deepcopy(a)
        b.update(session_role="failing", symptom="not_found")
        b["command_result"].update(status="failure")
        report = snapshot.compare_snapshots(a, b)
        check("synthetic_equal_no_invented_reason", report["outcome"] == "no_explanatory_difference" and not report["explanations"])
        b["resolution"]["scan_limited"] = True
        report = snapshot.compare_snapshots(a, b)
        check("limited_not_counted_as_resolution_difference", "resolution.preferred" not in report["differences"] and "B.candidate_access_or_limit" in report["evidence_gaps"])
        unknown_env = snapshot.environment(b"x" * 32, {"PATH": ";".join([str(tools_a)] * 256), "PATHEXT": ".EXE;.PRIVATE", "COMSPEC": "relative"})
        check("bounds_mark_limited", unknown_env["path"]["status"] == "limited" and unknown_env["pathext"]["status"] == "limited" and unknown_env["comspec"]["status"] == "unknown")
    # Real junction and file symlink defenses with zero target/descendant probes.
    junction = dest / "junction"
    target = dest / "junction-target"
    target.mkdir()
    write(target / "snapshot.json", captured)
    made = subprocess.run([str(Path(env["SYSTEMROOT"]) / "System32/cmd.exe"), "/d", "/c", "mklink", "/J", str(junction), str(target)], capture_output=True, timeout=10)
    check("junction_creation", made.returncode == 0 and junction.lstat().st_reparse_tag == 0xA0000003)
    original_open, original_lstat = Path.open, Path.lstat
    accesses = []
    def guarded_open(path, *a, **kw):
        if path == target or target in path.parents or path == junction or junction in path.parents:
            accesses.append("content")
            raise AssertionError("linked_content")
        return original_open(path, *a, **kw)
    def guarded_lstat(path, *a, **kw):
        if path == target or target in path.parents or junction in path.parents:
            accesses.append("descendant_metadata")
            raise AssertionError("linked_descendant")
        return original_lstat(path, *a, **kw)
    with patch.object(Path, "open", guarded_open), patch.object(Path, "lstat", guarded_lstat):
        try:
            snapshot_schema.load_snapshot(junction / "snapshot.json")
        except ValueError:
            pass
        else:
            raise AssertionError("junction_accepted")
    check("junction_zero_target_access", not accesses)
    with patch.dict(os.environ, {**env, "LOCALAPPDATA": str(junction)}, clear=True):
        with patch.object(Path, "open", guarded_open), patch.object(Path, "lstat", guarded_lstat):
            key_unavailable = KeyStore().status()["status"] == "unavailable"
            try:
                KeyStore().manage("init")
            except ValueError:
                pass
            else:
                raise AssertionError("key_init_followed_junction")
        check("key_ancestor_junction_fails_closed", key_unavailable)
        check("key_init_rejects_junction")
    check("key_junction_zero_target_access", not accesses)
    link = dest / "file-symlink.json"
    try:
        link.symlink_to(cap_path)
    except OSError as error:
        blocked.append({"gate": "real_file_symlink", "winerror": getattr(error, "winerror", None)})
    else:
        check("file_symlink_real", link.lstat().st_reparse_tag == 0xA000000C)
        with patch.object(Path, "open", side_effect=AssertionError("symlink_target_read")):
            try:
                snapshot_schema.load_snapshot(link)
            except ValueError:
                pass
            else:
                raise AssertionError("symlink_accepted")
        check("file_symlink_zero_target_reads")
    rotated = json.loads(run("key_rotate", ["--compare-key", "rotate"]))
    check("rotation_changes_scope", rotated["scope_code"] != captured["scope"]["code"])
    inactive = json.loads(run("old_scope_inactive", ["--compare-snapshots", cap_path, cap_path, "--format", "json"]))
    check("old_scope_null_differences", inactive["reason"] == "inactive_scope" and inactive["differences"] is None)
    new_cap = dest / "new-capture.json"
    new_cap.write_bytes(run("new_scope_capture", ["--capture", "--command", "codex"]))
    mismatch = json.loads(run("scope_mismatch", ["--compare-snapshots", cap_path, new_cap, "--format", "json"]))
    check("scope_mismatch_not_identity_guess", mismatch["reason"] == "scope_mismatch" and mismatch["differences"] is None)
    future = copy.deepcopy(captured)
    future["algorithm"] = "lexical-windows-v2"
    future_path = dest / "future-algorithm.json"
    write(future_path, future)
    incompatible = json.loads(run("algorithm_mismatch", ["--compare-snapshots", future_path, cap_path, "--format", "json"]))
    check("algorithm_mismatch_null", incompatible["reason"] == "algorithm_mismatch" and incompatible["differences"] is None)
    run("key_delete", ["--compare-key", "delete"])
    deleted = json.loads(run("deleted_key_comparison", ["--compare-snapshots", cap_path, cap_path, "--format", "json"]))
    check("deleted_key_no_recovery", deleted["reason"] == "key_unavailable" and deleted["differences"] is None and not (state / "WindowsAIDoctor/comparison/key.dat").exists())
    blocked += [{"gate": "cross_user_DPAPI_and_ACL", "reason": "independent second-user execution not performed"},
                {"gate": "A_B_R_full_real_scenarios", "reason": "synthetic explanation cases and helper evidence do not replace independent real-scene acceptance"}]
    result = {"status": "BLOCKED", "checks_passed": len(checks), "commands": len(steps), "blocked": blocked,
              "XC-C5": "PASS for recorded cross-feeding matrix", "XC-C6": "PASS in isolated LOCALAPPDATA; old and snapshot read-only paths",
              "state_root": str(state), "test_key_deleted": True, "synthetic_interpretation_cases": True}
    write(dest / "result.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
