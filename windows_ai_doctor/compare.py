"""Bounded schema-1.0 reader. Imported text and paths never reach output."""
import csv
import io
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .discovery import bounded_read

STATES = ("pass", "warn", "error", "unknown", "skipped")
IDS = {"system.platform", "scope.unchecked", "wsl.launcher", "wsl.inventory", "wsl.running", "wsl.internal", "claude.config.local"} | {
    tool + "." + part for tool in ("codex", "claude")
    for part in ("path", "install", "dependency", "version", "config.user", "config.project")}
MAX_BYTES, MAX_DEPTH, MAX_NODES, MAX_FINDINGS = 2 * 1024 * 1024, 16, 20000, 64
VERSION_PATTERN = r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}"
MAX_INSTALLATION_GROUPS = 32


def invalid(*_):
    raise ValueError("invalid_report")


def pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            invalid()
        obj[key] = value
    return obj


def integer(value):
    if len(value) > 12:
        invalid()
    return int(value)


def floating(value):
    if len(value) > 32:
        invalid()
    n = float(value)
    if not math.isfinite(n):
        invalid()
    return n


def check_depth(text):
    # Bound nesting before invoking the JSON decoder (including ignored fields).
    depth, quoted, escaped = 0, False, False
    for c in text:
        if quoted:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                invalid()
        elif c in "]}":
            depth -= 1


def check_nodes(obj):
    todo, count = [obj], 0
    while todo:
        item = todo.pop()
        count += 1
        if count > MAX_NODES:
            invalid()
        if isinstance(item, dict):
            todo.extend(item.keys())
            todo.extend(item.values())
        elif isinstance(item, list):
            todo.extend(item)
        elif isinstance(item, str) and len(item) > 32768:
            invalid()


def numeric_version(value):
    # Free-form prerelease tags could carry private text. Compare numeric only.
    if isinstance(value, str) and re.fullmatch(VERSION_PATTERN, value):
        return value
    return None


def project(obj):
    if not isinstance(obj, dict) or obj.get("schema_version") != "1.0" or obj.get("report_type", "diagnosis") != "diagnosis":
        invalid()
    findings = obj.get("findings")
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        invalid()
    result = {}
    for f in findings:
        if not isinstance(f, dict):
            invalid()
        id, status = f.get("id"), f.get("status")
        if not isinstance(id, str) or id not in IDS or id in result or not isinstance(status, str) or status not in STATES:
            invalid()
        e = f.get("evidence", {})
        if not isinstance(e, dict):
            invalid()
        safe = {"status": status}
        if id.endswith((".version", ".dependency")):
            safe["version"] = numeric_version(e.get("version"))
        if id.endswith(".path"):
            if "installation_groups" in e:
                n = e["installation_groups"]
                if type(n) is not int or not 0 <= n <= MAX_INSTALLATION_GROUPS:
                    invalid()
                safe["installation_groups"] = n
            if "scan_limited" in e:
                if type(e["scan_limited"]) is not bool:
                    invalid()
                safe["scan_limited"] = e["scan_limited"]
        result[id] = safe
    return result


def load_report(path):
    # absolute() is lexical; no resolve(), exists() or probe before bounded_read.
    raw = bounded_read(Path(path).absolute(), MAX_BYTES)
    return project(decode_object(raw))


def decode_object(raw):
    if len(raw) > MAX_BYTES:
        invalid()
    text = raw.decode("utf-8")
    check_depth(text)
    obj = json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                     parse_float=floating, parse_constant=invalid)
    check_nodes(obj)
    return obj


def compare_reports(old, new, lang="zh"):
    changes = []
    for id in sorted(old.keys() | new.keys()):
        a, b = old.get(id), new.get(id)
        if a == b:
            continue
        kind = "added" if a is None else "removed" if b is None else "changed"
        note = "added" if a is None else "removed" if b is None else "unassessed" if b["status"] in ("unknown", "skipped") or b.get("scan_limited") is True else "passes_now" if b["status"] == "pass" and a["status"] != "pass" else "observations_changed"
        details = {}
        for key in ("version", "installation_groups", "scan_limited"):
            av, bv = (a or {}).get(key), (b or {}).get(key)
            if av != bv:
                details[key] = {"before": av, "after": bv}
        changes.append({"id": id, "change": kind, "before": a["status"] if a else None,
                        "after": b["status"] if b else None, "note": note, "details": details})
    return {"schema_version": "1.0", "report_type": "comparison", "doctor_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "language": lang,
            "summary": {kind: sum(c["change"] == kind for c in changes) for kind in ("added", "removed", "changed")},
            "unchanged": sum(old.get(id) == new.get(id) for id in old.keys() & new.keys()),
            "changes": changes,
            "notice": ("请自行确认两份报告来自相同环境和检查范围；路径代号跨次无身份意义。通过仅代表此项本次通过；未知、未检查和移除均不代表修复。仅比较数字版本、安装组数量和扫描限制，其他证据未比较。" if lang == "zh" else
                       "Confirm that both reports cover the same environment and scope; path references have no identity across runs. A pass covers this check now only; unknown, skipped and removed checks do not establish a fix. Only numeric versions, installation-group counts and scan limits are compared; other evidence is not compared.")}


COMPARISON_COLUMNS = ("sequence", "check_id", "change", "before_status", "after_status", "note",
                      "version_before", "version_after", "installation_groups_before", "installation_groups_after",
                      "scan_limited_before", "scan_limited_after")


def comparison_csv(old, new):
    """Only consume projections returned by load_report; never imported text."""
    stream = io.StringIO(newline="")
    stream.write("\ufeff")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(COMPARISON_COLUMNS)
    for sequence, change in enumerate(compare_reports(old, new)["changes"], 1):
        before, after = old.get(change["id"], {}), new.get(change["id"], {})
        observations = []
        for key in ("version", "installation_groups", "scan_limited"):
            for side in (before, after):
                value = side.get(key)
                observations.append("" if value is None else str(value).lower() if type(value) is bool else value)
        writer.writerow((sequence, change["id"], change["change"], change["before"] or "",
                         change["after"] or "", change["note"], *observations))
    return stream.getvalue()


NOTES = {
    "zh": {"added": "本次新增检查。", "removed": "本次未包含，未再检查。", "unassessed": "无法判断、未再检查或扫描受限，不代表修复。", "passes_now": "该检查本次通过。", "observations_changed": "观察字段或状态变化。"},
    "en": {"added": "Check added in this report.", "removed": "Not included this time; not rechecked.", "unassessed": "Unknown, not rechecked or scan limited; this does not establish a fix.", "passes_now": "This check passes now.", "observations_changed": "Observed fields or status changed."},
}
