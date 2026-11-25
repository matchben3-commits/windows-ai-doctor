"""Read-only snapshot capture and conservative comparison."""
import json
import ntpath
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path

from .comparison_key import KeyStore, derive
from .compare import MAX_BYTES, decode_object
from .discovery import checked_stat, bounded_read, classify, local_absolute, PACKAGES
from .privacy import safe_version
from .runner import run_bounded
from .snapshot_schema import ALGORITHM, EXTENSIONS, NUMERIC_VERSION, validate_snapshot

EXTERNAL = {"application", "external_script"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def path_code(key, raw):
    # No expansion, case folding, resolve(), filesystem access or link traversal.
    # Case-sensitive Windows directories remain distinct. Algorithm is versioned.
    return "path_" + derive(key, "path/" + ALGORITHM, ntpath.normpath(raw).encode("utf-8", "surrogatepass"))


def environment(key, values, unavailable=False):
    result = {"path": {"status": "unknown", "entries": []},
              "pathext": {"status": "unknown", "entries": []},
              "comspec": {"status": "unknown", "path_code": None}}
    if unavailable:
        return result
    for name in ("PATH", "PATHEXT", "COMSPEC"):
        value = values.get(name)
        slot = result[name.lower()]
        if value is None:
            slot["status"] = "missing"
            continue
        if not isinstance(value, str) or len(value) > 32768:
            continue
        if name == "COMSPEC":
            if value and ntpath.isabs(value) and not value.startswith(("\\\\", "//")) and "%" not in value:
                slot.update(status="observed", path_code=path_code(key, value))
            continue
        pieces = value.split(";")
        limited = len(pieces) >= 256
        for piece in pieces[:256]:
            if name == "PATH":
                raw = piece.strip().strip('"')
                slot["entries"].append(path_code(key, raw))
                if not raw or not ntpath.isabs(raw) or raw.startswith(("\\\\", "//")) or "%" in raw:
                    limited = True
            elif piece.lower() in EXTENSIONS:
                slot["entries"].append(piece.lower())
            else:
                limited = True
        slot["status"] = "limited" if limited else "observed"
    return result


def persistent(key, user):
    if os.name != "nt":
        return environment(key, {}, True)
    import winreg
    root = winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE
    location = r"Environment" if user else r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    values = {}
    try:
        with winreg.OpenKey(root, location, 0, winreg.KEY_QUERY_VALUE) as handle:
            for name in ("PATH", "PATHEXT", "COMSPEC"):
                try:
                    value, kind = winreg.QueryValueEx(handle, name)
                    values[name] = value if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) else False
                except FileNotFoundError:
                    pass
                except OSError:
                    values[name] = False
    except OSError:
        return environment(key, {}, True)
    return environment(key, values)


def elevation():
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes as W
    from .comparison_key import WindowsProtection
    try:
        protection = WindowsProtection()
    except (OSError, ValueError):
        return None
    token, size, elevated = W.HANDLE(), W.DWORD(), W.DWORD()
    if not protection.advapi.OpenProcessToken(protection.kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        return None
    try:
        if protection.advapi.GetTokenInformation(token, 20, ctypes.byref(elevated), ctypes.sizeof(elevated), ctypes.byref(size)):
            return bool(elevated.value)
    finally:
        protection.kernel.CloseHandle(token)
    return None


def launcher(key, entry):
    unknown = {"status": "unknown", "content_code": None, "version": None, "version_source": "none"}
    if entry.kind not in ("native", "npm-native", "npm-js") or entry.path_access != "checked":
        return unknown
    try:
        before = checked_stat(entry.path)
        raw = bounded_read(entry.path)
        after = checked_stat(entry.path)
        signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        if signature(before) != signature(after) or not stat.S_ISREG(after.st_mode) or len(raw) != after.st_size:
            return unknown
        return {**unknown, "status": "observed", "content_code": "launcher_" + derive(key, "launcher", raw)}
    except (OSError, ValueError):
        return unknown


def read_session(raw, command):
    # PowerShell's native stdin pipe may carry one leading UTF-8 BOM. Accept
    # it only at this transport boundary; count it toward the input limit and
    # preserve the shared report decoder's validation and encoding policies.
    if len(raw) > MAX_BYTES:
        raise ValueError("invalid_session")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    value = decode_object(raw)
    if (not isinstance(value, dict) or set(value) != {"command", "kind", "path"}
            or value["command"] != command or value["kind"] not in ("application", "external_script", "alias", "function", "missing", "unknown")):
        raise ValueError("invalid_session")
    path = value["path"]
    if value["kind"] in ("application", "external_script"):
        if not isinstance(path, str) or len(path) > 32768 or not ntpath.isabs(path) or path.startswith(("\\\\", "//")):
            raise ValueError("invalid_session")
    elif path is not None:
        raise ValueError("invalid_session")
    return value


def capture_entries(command, values):
    """Keep case and PATH ordering; legacy discovery folds case for diagnostics.

    Case-sensitive directories cannot be merged for cross-snapshot identity.
    No candidate is invoked and rejected directories have no descendant access.
    """
    dirs, limited = [], False
    pieces = values.get("PATH", "").split(";")
    limited = len(pieces) >= 256
    for raw in pieces[:256]:
        value = raw.strip().strip('"')
        if value and local_absolute(value) and ".." not in Path(value).parts:
            dirs.append(Path(value))
        else:
            limited = True
    extensions = [s.lower() for s in values.get("PATHEXT", "").split(";") if s.lower() in EXTENSIONS]
    suffixes = list(dict.fromkeys([*extensions, ".ps1", ""]))
    entries = []
    for directory in dirs:
        for suffix in suffixes:
            path = directory / (command + suffix)
            try:
                if not stat.S_ISREG(checked_stat(path).st_mode):
                    continue
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                limited = True
                # An inaccessible earlier PATH entry prevents priority claims.
                continue
            entry = classify(path, command, dirs)
            if entry.kind == "npm-js":
                entry.group = str(path.parent / "node_modules" / PACKAGES[command])
            elif entry.kind == "npm-native":
                entry.group = entry.argv[0]
            else:
                entry.group = str(path)
            entries.append(entry)
            if len(entries) >= 256:
                return entries, True
    return entries, limited


def capture(command, role="unspecified", symptom="unspecified", result="unverified", session=None, probe_version=False):
    key = KeyStore().load()  # fail before inspection; never initializes state
    stamp = now()
    safe_env = {name: os.environ[name] for name in ("PATH", "PATHEXT", "COMSPEC") if name in os.environ}
    # Discovery receives only the whitelist, never a copy of all variables.
    projection = environment(key, safe_env)
    entries, limited = capture_entries(command, safe_env)
    limited = limited or any(projection[f]["status"] != "observed" for f in ("path", "pathext"))
    candidates = [{"path_code": path_code(key, str(e.path)),
                   "installation_code": "installation_" + derive(key, "installation/" + ALGORITHM, e.group.encode("utf-8", "surrogatepass")),
                   "kind": e.kind, "access": e.path_access,
                   "node_code": path_code(key, str(e.node)) if e.node else None, "launcher": launcher(key, e)} for e in entries]
    elevated = elevation()
    resolution = {"status": "unknown", "source": "none", "kind": "unknown", "target": command,
                  "preferred_code": None, "candidates": candidates, "scan_limited": limited}
    tool_execution = "not_performed"
    if session is not None:
        resolution.update(status="unknown" if session["kind"] == "unknown" else "observed",
                          source="original_runspace_user_supplied", kind=session["kind"],
                          preferred_code=path_code(key, session["path"]) if session["path"] else None)
        if session["path"]:
            resolution["preferred_directory_code"] = path_code(key, ntpath.dirname(session["path"]))
    if probe_version and resolution["preferred_code"] is not None:
        # Session metadata selects an already-inspected candidate, never an argv.
        matching = [(entry, candidate) for entry, candidate in zip(entries, candidates)
                    if candidate["path_code"] == resolution["preferred_code"]]
        if len(matching) == 1 and matching[0][0].argv:
            entry, candidate = matching[0]
            tool_execution = "version_probe"
            probe = run_bounded(entry.argv)
            version = safe_version(probe.output, command) if probe.reason == "ok" and probe.returncode == 0 else None
            if version and re.fullmatch(NUMERIC_VERSION, version):
                candidate["launcher"].update(version=version, version_source="bounded_version_probe")
    snapshot = {"report_type": "environment_snapshot", "schema_version": "snapshot-1.0", "captured_at": stamp,
                "command": command, "session_role": role, "symptom": symptom, "algorithm": ALGORITHM,
                "scope": {"code": "scope_" + derive(key, "scope", b"current"), "key_status": "available"},
                "context": {"shell": "powershell" if session is not None else "unknown", "elevated": elevated,
                            "elevation_status": "unknown" if elevated is None else "observed"},
                "environment": projection,
                "persistent_environment": {"user": persistent(key, True), "machine": persistent(key, False)},
                "resolution": resolution, "observations": {"tool_execution": tool_execution},
                "command_result": {"status": result, "source": "none" if result == "unverified" else "user_report",
                                   "recorded_at": stamp, "executed_at": None,
                                   "session_match": "unknown" if result == "unverified" else "original"}}
    return validate_snapshot(snapshot)


def current_scope():
    try:
        return KeyStore().status()
    except (OSError, ValueError):
        return {"status": "unavailable", "scope_code": None}


def original_result(snap):
    result = snap["command_result"]
    return result["status"] if result["session_match"] == "original" else "unverified"


def preferred_version(snap):
    resolution = snap["resolution"]
    return next((c["launcher"]["version"] for c in resolution["candidates"]
                 if c["path_code"] == resolution["preferred_code"] and c["launcher"]["version"] is not None), None)


def path_membership(layer, directory):
    if layer["status"] == "observed":
        return "present" if directory in layer["entries"] else "absent"
    return "missing" if layer["status"] == "missing" else "unknown"


def path_layers(snap, directory):
    return {"process": path_membership(snap["environment"]["path"], directory),
            **{layer: path_membership(data["path"], directory)
               for layer, data in snap["persistent_environment"].items()}}


def installations(resolution):
    return {candidate["path_code"]: candidate["installation_code"]
            for candidate in resolution["candidates"]
            if candidate["access"] == "checked" and candidate["kind"] != "unknown"}


def compare_snapshots(a, b, lang="zh", *, current=None):
    if current is None:
        current = current_scope()
    reason = ("algorithm_mismatch" if a["algorithm"] != b["algorithm"] or a["algorithm"] != ALGORITHM else
              "scope_mismatch" if a["scope"]["code"] != b["scope"]["code"] else
              "key_unavailable" if current["status"] != "available" else
              "inactive_scope" if a["scope"]["code"] != current["scope_code"] else None)
    report = {"report_type": "snapshot_comparison", "schema_version": "snapshot-comparison-1.0", "language": lang,
              "times": {"A": a["captured_at"], "B": b["captured_at"]},
              "comparability": "incomparable" if reason else "same_scope", "reason": reason,
              "differences": None, "facts": [], "explanations": [], "evidence_gaps": [],
              "command_results": {"A": a["command_result"], "B": b["command_result"]},
              "user_reports": {"A": {k: a[k] for k in ("command", "session_role", "symptom")},
                               "B": {k: b[k] for k in ("command", "session_role", "symptom")}},
              "outcome": "incomparable" if reason else "differences_only",
              "verification": [],
              "notice": "仅限 T1/T2 的观测；比较域不认证来源，不能保证当前仍相同。 / Observations at T1/T2 only; scope does not authenticate sources or establish current state."}
    if reason:
        return report
    differences, gaps = [], []
    def observed(label, left, right, ready):
        if not ready:
            gaps.append(label)
        elif left != right:
            differences.append(label)
            report["facts"].append({"level": "confirmed", "observation": label})
    for layer in ("environment", "user", "machine"):
        av = a["environment"] if layer == "environment" else a["persistent_environment"][layer]
        bv = b["environment"] if layer == "environment" else b["persistent_environment"][layer]
        for field in ("path", "pathext", "comspec"):
            observed(layer + "." + field, av[field], bv[field], av[field]["status"] == bv[field]["status"] == "observed")
    ar, br = a["resolution"], b["resolution"]
    ready = ar["status"] == br["status"] == "observed" and not ar["scan_limited"] and not br["scan_limited"]
    observed("resolution.preferred", (ar["kind"], ar["preferred_code"]), (br["kind"], br["preferred_code"]), ready)
    for field in ("launcher", "node_code"):
        def candidate_value(candidate):
            if field == "launcher":
                launcher_data = candidate["launcher"]
                return (launcher_data["status"], launcher_data["content_code"])
            return candidate[field]

        observed("resolution." + field,
                 [(c["path_code"], candidate_value(c)) for c in ar["candidates"]],
                 [(c["path_code"], candidate_value(c)) for c in br["candidates"]],
                 not ar["scan_limited"] and not br["scan_limited"] and all(
                     c["access"] == "checked" and c["kind"] != "unknown" and c["launcher"]["status"] == "observed"
                     for r in (ar, br) for c in r["candidates"]))
    if a["command"] == b["command"]:
        versions = [preferred_version(snap) for snap in (a, b)]
        if any(v is not None for v in versions):
            report["preferred_versions"] = dict(zip(("A", "B"), versions))
            observed("resolution.version", *versions, all(v is not None for v in versions))
    if not ready:
        gaps.append("original_session_resolution")
    for side, snap in (("A", a), ("B", b)):
        if snap["resolution"]["scan_limited"] or any(c["access"] == "blocked" for c in snap["resolution"]["candidates"]):
            gaps.append(side + ".candidate_access_or_limit")
        if any(c["launcher"]["status"] == "unknown" for c in snap["resolution"]["candidates"]):
            gaps.append(side + ".launcher_content")
    observed("context.elevated", a["context"]["elevated"], b["context"]["elevated"], a["context"]["elevation_status"] == b["context"]["elevation_status"] == "observed")
    report["differences"] = differences
    pair = {a["session_role"], b["session_role"]} == {"working", "failing"} and a["command"] == b["command"]
    working, failing = (a, b) if a["session_role"] == "working" else (b, a)
    directory = working["resolution"].get("preferred_directory_code")
    failing_layers = None
    if pair and ready and directory is not None:
        working_layers, failing_layers = path_layers(working, directory), path_layers(failing, directory)
        report["working_launcher_directory"] = {"working": working_layers, "failing": failing_layers}
        if failing_layers["process"] == "absent" and "present" in (failing_layers["user"], failing_layers["machine"]):
            report["facts"].append({"level": "confirmed", "observation": "working_launcher_directory_missing_from_failing_process_path"})
    successes = a["command"] == b["command"] and all(original_result(s) == "success" for s in (a, b))
    if successes:
        report["outcome"] = "both_commands_succeeded"
    elif not differences:
        report["outcome"] = "no_explanatory_difference"
        if any(original_result(s) == "unverified" for s in (a, b)):
            gaps.append("original_command_execution")
    else:
        if not pair or failing["symptom"] in ("none", "unspecified"):
            gaps.append("working_failing_pair_and_symptom")
        elif failing["symptom"] in ("other", "config_error"):
            gaps.append("symptom_outside_explanation_scope")
        elif ready and "resolution.preferred" in differences:
            kinds = {ar["kind"], br["kind"]}
            if kinds & {"alias", "function"} and kinds & EXTERNAL:
                report["explanations"].append({"level": "possible", "scenario": "alias_function_shadowing"})
                gaps.append("alias_function_execution_effect")
            if "environment.path" in differences and kinds <= EXTERNAL | {"missing"}:
                report["explanations"].append({"level": "possible", "scenario": "process_path_difference"})
                if failing_layers is None or "unknown" in (failing_layers["user"], failing_layers["machine"]):
                    gaps.append("persistent_path_membership")
                gaps.append("path_refresh_history")
            a_installs, b_installs = installations(ar), installations(br)
            a_selected, b_selected = a_installs.get(ar["preferred_code"]), b_installs.get(br["preferred_code"])
            if (kinds <= EXTERNAL and a_selected and b_selected and a_selected != b_selected
                    and any(len(set(groups.values())) > 1 for groups in (a_installs, b_installs))
                    and not any(c["access"] == "blocked" for r in (ar, br) for c in r["candidates"])):
                report["explanations"].append({"level": "possible", "scenario": "multiple_launcher_precedence"})
            if failing["symptom"] == "wrong_version" and not all(preferred_version(s) for s in (a, b)):
                gaps.append("independent_safe_numeric_version")
            if report["explanations"]:
                report["outcome"] = "possible_explanation"
                report["verification"] = ["Get-Command -Name " + a["command"] + " -All | Select-Object CommandType"]
        else:
            gaps.append("symptom_resolution_link")
    for side, snap in (("A", a), ("B", b)):
        result = snap["command_result"]
        if result["status"] == "unverified" or result["session_match"] != "original":
            gaps.append(side + ".original_command_result")
        if ((snap["session_role"] == "failing" or snap["symptom"] not in ("none", "unspecified")) and result["status"] == "success") or (snap["session_role"] == "working" and result["status"] == "failure"):
            gaps.append(side + ".result_symptom_conflict")
    report["evidence_gaps"] = list(dict.fromkeys(gaps))
    return report


def comparison_markdown(report, *, end_label="T2"):
    zh = report["language"] == "zh"
    outcomes = {
        "incomparable": ("不可比", "Incomparable"),
        "both_commands_succeeded": ("两侧记录均为原会话成功；只记录差异，不解释故障。", "Both records report original-session success; differences only."),
        "no_explanatory_difference": ("未发现可解释差异；未知项不证明完整环境一致。", "No explanatory difference found; unknown fields do not establish equal environments."),
        "differences_only": ("普通差异与证据缺口", "Differences and evidence gaps"),
        "possible_explanation": ("可能解释；尚不能确认故障归因。", "Possible explanations; causation is unconfirmed."),
    }
    notice = report["notice"].replace("T1/T2", f"T1/{end_label}")
    lines = ["# Windows AI Doctor", "", "T1 (A): " + report["times"]["A"], end_label + " (B): " + report["times"]["B"], "",
             outcomes[report["outcome"]][0 if zh else 1], "", notice, ""]
    if report["reason"]:
        lines += [report["reason"], ""]
    for side, result in report["command_results"].items():
        if result["source"] == "user_report":
            label = ("用户报告成功" if result["status"] == "success" else "用户报告失败") if zh else "User reports " + result["status"]
        elif result["source"] == "controlled_test":
            label = ("受控测试：" if zh else "Controlled test: ") + result["status"]
        else:
            label = "原命令结果未验证" if zh else "Original command result unverified"
        lines.append(f"- {side}: {label}; executed_at={result['executed_at'] or 'unknown'}; session_match={result['session_match']}")
    for field in ("user_reports", "differences", "facts", "explanations", "evidence_gaps", "verification",
                  "preferred_versions", "working_launcher_directory"):
        if field not in report:
            continue
        lines += ["", field + ":", "", "```json", json.dumps(report[field], ensure_ascii=False, indent=2), "```"]
    return "\n".join(lines) + "\n"
