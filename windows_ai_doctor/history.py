"""Ordered offline trends over bounded, projected diagnosis inputs."""
import csv
import io
from datetime import datetime, timezone

from . import __version__
from .compare import STATES, compare_reports, load_report

MAX_REPORTS = 20


def history_csv(report):
    stream = io.StringIO(newline="")
    stream.write("\ufeff")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("sequence", "check_id", "status", "version", "installation_groups", "scan_limited"))
    for n in range(len(report["snapshots"])):
        for check in report["checks"]:
            observation = check["observations"][n] or {}
            limited = observation.get("scan_limited")
            writer.writerow((n + 1, check["id"], observation.get("status", "missing"),
                             observation.get("version") or "", observation.get("installation_groups", ""),
                             "" if limited is None else str(limited).lower()))
    return stream.getvalue()


def counts(report):
    return {state: sum(f["status"] == state for f in report.values()) for state in STATES}


def load_history(paths):
    if not 2 <= len(paths) <= MAX_REPORTS:
        raise ValueError("history_count")
    # At most 40 MiB of encoded input; each input also has depth/node limits.
    return [load_report(path) for path in paths]


def history_report(reports, lang="zh"):
    if not 2 <= len(reports) <= MAX_REPORTS:
        raise ValueError("history_count")
    return {"schema_version": "1.0", "report_type": "history", "doctor_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "language": lang,
            "summary": counts(reports[-1]),
            "snapshots": [{"sequence": n, "summary": counts(report), "check_count": len(report)}
                          for n, report in enumerate(reports, 1)],
            "checks": [{"id": id, "observations": [report.get(id) for report in reports]}
                       for id in sorted(set().union(*(r.keys() for r in reports)))],
            "transitions": [{"from": n, "to": n + 1, **{k: v for k, v in compare_reports(a, b, lang).items()
                             if k in ("summary", "unchanged", "changes")}}
                            for n, (a, b) in enumerate(zip(reports, reports[1:]), 1)],
            "notice": ("顺序以命令行输入为准。请自行确认所有报告来自同一环境和相同检查范围；不推断机器身份。状态数量不是健康评分。缺失、未知、未检查或扫描受限均不代表修复；通过仅指该项本次通过。仅比较已知检查的状态、数字版本、安装组数量和扫描限制。" if lang == "zh" else
                       "Order follows the command line. Confirm that all reports cover the same environment and scope; machine identity is not inferred. Counts are not a health score. Missing, unknown, skipped or scan-limited checks do not establish a fix; a pass covers this check now only. Only known check states, numeric versions, installation-group counts and scan limits are compared.")}
