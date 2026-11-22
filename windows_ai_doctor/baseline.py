"""Deterministic baseline comparisons over the bounded reader's projections."""
import csv
import html
import io
import json

from .compare import NOTES, compare_reports, project

NOTICE = {
    "zh": "请自行确认基线与本次诊断来自相同环境和检查范围。回归仅指未受扫描限制时 pass→warn、pass→error 或 warn→error 的固定状态转移，不等于已确认故障根因。新增、移除、未知和未检查均不代表修复。只比较状态、数字版本、安装组数量和扫描限制。",
    "en": "Confirm that the baseline and current diagnosis cover the same environment and scope. Regression means only pass→warn, pass→error or warn→error without a scan limit; it does not establish a fault's root cause. Added, removed, unknown and skipped checks do not establish a fix. Only states, numeric versions, installation-group counts and scan limits are compared.",
}
REGRESSION_PAIRS = {("pass", "warn"), ("pass", "error"), ("warn", "error")}
DIAGNOSIS_COLUMNS = ("sequence", "check_id", "target", "status", "version",
                     "installation_groups", "scan_limited", "baseline_change",
                     "baseline_status", "baseline_regression")


def baseline_report(old, new, lang="zh"):
    comparison = compare_reports(old, new, lang)
    changes = comparison["changes"]
    for change in changes:
        check_id = change["id"]
        change["regression"] = (
            change["change"] == "changed"
            and (change["before"], change["after"]) in REGRESSION_PAIRS
            and old[check_id].get("scan_limited") is not True
            and new[check_id].get("scan_limited") is not True
        )
    return {"schema_version": "1.0", "summary": comparison["summary"],
            "unchanged": comparison["unchanged"], "changes": changes,
            "regressions": [c["id"] for c in changes if c["regression"]],
            "notice": NOTICE[lang]}


def diagnosis_csv(report):
    """Never export free text, paths or arbitrary evidence from a diagnosis."""
    current = project(report)
    baseline = report.get("baseline")
    changes = {c["id"]: c for c in baseline["changes"]} if baseline is not None else {}
    stream = io.StringIO(newline="")
    stream.write("\ufeff")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(DIAGNOSIS_COLUMNS)
    for sequence, check_id in enumerate(sorted(current.keys() | changes.keys()), 1):
        observation = current.get(check_id, {})
        values = []
        for key in ("version", "installation_groups", "scan_limited"):
            value = observation.get(key)
            values.append("" if value is None else str(value).lower() if type(value) is bool else value)
        baseline_values = ("", "", "")
        if baseline is not None:
            change = changes.get(check_id)
            baseline_values = (change["change"], change["before"] or "", str(change["regression"]).lower()) if change else (
                "unchanged", observation["status"], "false")
        writer.writerow((sequence, check_id, check_id.split(".", 1)[0],
                         observation.get("status", ""), *values, *baseline_values))
    return stream.getvalue()


def baseline_counts(baseline, lang):
    labels = {"zh": ("新增", "移除", "变化", "回归", "未变化"),
              "en": ("Added", "Removed", "Changed", "Regressions", "Unchanged")}[lang]
    values = [baseline["summary"][key] for key in ("added", "removed", "changed")]
    values.extend((len(baseline["regressions"]), baseline["unchanged"]))
    return " · ".join(f"{label}: {value}" for label, value in zip(labels, values))


def baseline_markdown(baseline, lang):
    esc = lambda value: html.escape(str(value), quote=True)
    zh = lang == "zh"
    lines = ["## 基线对比" if zh else "## Baseline comparison", "", esc(baseline["notice"]), "",
             esc(baseline_counts(baseline, lang)), ""]
    if not baseline["changes"]:
        lines.extend(["比较字段无实质变化。" if zh else "No substantive changes in compared fields.", ""])
    for change in baseline["changes"]:
        marker = ("固定规则回归" if zh else "Regression under fixed rules") if change["regression"] else ""
        lines.extend([f"### {esc(change['id'])} — {esc(change['change'])}", "",
                      esc(change["before"] or "—") + " → " + esc(change["after"] or "—"), "",
                      esc(NOTES[lang][change["note"]]), ""])
        if marker:
            lines.extend(["**" + marker + "**", ""])
        lines.extend(["```json", json.dumps(change["details"], ensure_ascii=False, indent=2), "```", ""])
    return lines


def baseline_html(baseline, lang):
    esc = lambda value: html.escape(str(value), quote=True)
    zh = lang == "zh"
    out = ['<section id="baseline-comparison" aria-labelledby="baseline-heading">',
           '<h2 id="baseline-heading">' + ("基线对比" if zh else "Baseline comparison") + '</h2>',
           '<p>' + esc(baseline["notice"]) + '</p>',
           '<p id="baseline-counts">' + esc(baseline_counts(baseline, lang)) + '</p>',
           '<div id="baseline-changes">']
    if not baseline["changes"]:
        out.append('<p>' + ("比较字段无实质变化。" if zh else "No substantive changes in compared fields.") + '</p>')
    for change in baseline["changes"]:
        out.append('<article><h3>' + esc(change["id"]) + ' · ' + esc(change["change"]) + '</h3><p>' +
                   esc(change["before"] or "—") + ' → ' + esc(change["after"] or "—") + '</p><p>' +
                   esc(NOTES[lang][change["note"]]) + '</p>')
        if change["regression"]:
            out.append('<p><strong>' + ("固定规则回归" if zh else "Regression under fixed rules") + '</strong></p>')
        out.append('<pre>' + esc(json.dumps(change["details"], ensure_ascii=False, indent=2)) + '</pre></article>')
    out.append('</div></section>')
    return '\n'.join(out)
