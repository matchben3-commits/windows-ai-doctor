"""Read-only delivery checks plus a sanitized result/manifest, no dependencies."""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def delivery_files():
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", ".task-build", "build") and not d.endswith(".egg-info")]
        for name in names:
            yield Path(folder) / name


def main():
    issues = []
    files = sorted(delivery_files())
    source_count = 0
    for path in files:
        if path.suffix == ".py":
            source_count += 1
            try:
                compile(path.read_text(encoding="utf-8"), "<source>", "exec")
            except (SyntaxError, UnicodeError):
                issues.append("python_source_invalid")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "#")):
                    continue
                if not (path.parent / target.split("#")[0]).exists():
                    issues.append("broken_local_document_link")
    report_files = [p for p in files if p.suffix in (".json", ".md", ".html") and
                    (p.is_relative_to(ROOT / "examples") or p.is_relative_to(ROOT / "evidence"))]
    for path in report_files:
        text = path.read_text(encoding="utf-8")
        if any(marker.casefold() in text.casefold() for marker in
               ("SYNTHETIC_PRIVATE_", "SYNTHETIC_PASSWORD_", "synthetic-key", "synthetic-password", "example.invalid", "C:\\Users\\", "C:/Users/")):
            issues.append("private_marker_in_report")
        if path.name.startswith("report.") and path.suffix == ".json":
            report = json.loads(text)
            ids = [f["id"] for f in report["findings"]]
            if len(ids) != len(set(ids)) or report["schema_version"] != "1.0":
                issues.append("report_schema_or_duplicate_id")
            for f in report["findings"]:
                if not all(k in f for k in ("id", "target", "status", "summary", "evidence", "recommendation", "recheck")):
                    issues.append("finding_missing_field")
    if any("__pycache__" in p.relative_to(ROOT).parts for p in files):
        issues.append("bytecode_cache_present")
    record = {"generated_at": datetime.now(timezone.utc).isoformat(), "exit_code": 0 if not issues else 1,
              "python_sources_compiled_in_memory": source_count,
              "generated_report_files_checked": len(report_files),
              "local_markdown_links_checked": True, "private_report_marker_scan": "passed" if not issues else "see_issue_codes",
              "issues": sorted(set(issues))}
    (ROOT / "evidence/artifact-check.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    # Exclude the manifest itself to avoid a recursive checksum dependency.
    files = sorted(p for p in delivery_files() if p.name != "SHA256SUMS.txt")
    manifest = [hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(ROOT).as_posix() for p in files]
    (ROOT / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"artifact_check={'PASS' if not issues else 'FAIL'}; sources={source_count}; reports={len(report_files)}; issues={len(issues)}")
    return record["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError):
        print("Artifact verification incomplete; details withheld.", file=sys.stderr)
        raise SystemExit(2)
