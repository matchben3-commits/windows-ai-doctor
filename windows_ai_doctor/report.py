import html
import json

from .compare import NOTES

LABELS = {
    "zh": {"pass": "通过", "warn": "提醒", "error": "异常", "unknown": "无法判断", "skipped": "未检查", "added": "新增", "removed": "移除", "changed": "变化"},
    "en": {"pass": "Pass", "warn": "Warning", "error": "Error", "unknown": "Unknown", "skipped": "Not checked", "added": "Added", "removed": "Removed", "changed": "Changed"},
}


def json_report(report):
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def markdown_report(report):
    if report.get("report_type") in ("validation", "support_verification"):
        from .validation import verification_markdown
        return verification_markdown(report)
    if report.get("report_type") == "history":
        return history_markdown(report)
    lang, zh = report["language"], report["language"] == "zh"
    comparison = report.get("report_type") == "comparison"
    lines = ["# Windows AI Doctor" + (" — " + ("前后对比" if zh else "Comparison") if comparison else ""), "", f"v{report['doctor_version']} · schema {report['schema_version']}",
             "", report["generated_at"], "",
             " · ".join(f"{LABELS[lang][s]}: {n}" for s, n in report["summary"].items()), ""]
    if comparison:
        lines.extend([report["notice"], "", ("无变化检查数：" if zh else "Unchanged checks: ") + str(report["unchanged"]), ""])
        if not report["changes"]:
            lines.extend(["比较字段无实质变化。" if zh else "No substantive changes in compared fields.", ""])
        for c in report["changes"]:
            lines.extend([f"## {c['id']} — {LABELS[lang][c['change']]}", "",
                          f"{c['before'] or '—'} → {c['after'] or '—'}", "", NOTES[lang][c["note"]], "",
                          "```json", json.dumps(c["details"], ensure_ascii=False, indent=2), "```", ""])
        return "\n".join(lines)
    if "exit_policy" in report:
        lines.extend(["## 退出条件" if zh else "## Exit conditions", "", policy_text(report), ""])
    lines.extend(["路径使用代号，原始映射未保存；语法通过不代表服务可用。" if zh else
                  "Paths use opaque references; the original mapping is not saved. Valid syntax does not establish service availability.", "",
                  "## 优先处理（异常 → 提醒 → 无法判断）" if zh else "## Review first (errors → warnings → unknown)", "",
                  ", ".join(report.get("priorities", [])) or ("无" if zh else "None"), ""])
    for finding in report["findings"]:
        lines.extend([f"## {finding['id']} — {LABELS[report['language']][finding['status']]}", "",
                      finding["summary"], "", "```json", json.dumps(finding["evidence"], ensure_ascii=False, indent=2),
                      "```", "", ("建议：" if zh else "Recommendation: ") + finding["recommendation"], "",
                      ("复查：" if zh else "Recheck: ") + finding["recheck"], ""])
        g = finding.get("guidance")
        if g:
            lines.extend([("判断依据：" if zh else "Basis: ") + g["basis"], "",
                          ("检查限制：" if zh else "Limitations: ") + g["limitation"], ""])
    return "\n".join(lines)


CSS = """
:root{color-scheme:light;font-family:system-ui,'Segoe UI',sans-serif;color:#17243a;background:#f2f5fa}
*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:auto;padding:32px 24px}
header{margin-bottom:24px}h1{font-size:clamp(1.6rem,5vw,2.5rem);margin:0 0 12px}
h2{font-size:1.15rem}p,li,pre,h2{overflow-wrap:anywhere}p,li{line-height:1.65}
.muted{color:#526078}.counts{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}
.count,article,.priority{border:1px solid #cdd6e4;background:white;border-radius:12px;padding:18px}
.count{min-width:115px;flex:1}.count strong{font-size:1.8rem;display:block}
article{margin:16px 0}article h2{margin:0 0 12px}.badge{font-weight:700}
.error{border-left:5px solid #b42318}.warn{border-left:5px solid #906400}
.unknown{border-left:5px solid #5d478b}.pass{border-left:5px solid #167345}
pre{white-space:pre-wrap;word-break:break-word;font-size:.86rem;background:#f4f6fa;padding:14px;border-radius:8px}
ol{padding-left:24px}.priority{border-left:5px solid #315cc9}footer{margin-top:32px}
@media(max-width:480px){main{padding:20px 12px}.count{min-width:90px;padding:12px}article{padding:14px}}
.table-scroll{overflow-x:auto;max-width:100%;border:1px solid #cdd6e4;border-radius:12px;background:white;margin:20px 0}
table{border-collapse:collapse;font-size:.9rem}caption{text-align:left;padding:14px;font-weight:700}
th,td{border:1px solid #d8e0ec;text-align:left;padding:12px;min-width:135px;vertical-align:top}
th{background:#eaf0fa}th[scope=row]{min-width:190px;position:sticky;left:0;z-index:1}td small{display:block;margin-top:8px;overflow-wrap:anywhere}
.table-scroll:focus{outline:3px solid #315cc9}
thead th:first-child{position:sticky;left:0;z-index:2}
"""


def html_report(report):
    if report.get("report_type") == "history":
        return history_html(report)
    # Dynamic content is text only; no dynamic URLs, attributes, styles or script.
    esc = lambda v: html.escape(str(v), quote=True)
    lang, zh = report["language"], report["language"] == "zh"
    comparison = report.get("report_type") == "comparison"
    title = "Windows AI Doctor" + (" · " + ("前后对比" if zh else "Comparison") if comparison else "")
    out = ['<!doctype html>', '<html lang="zh-CN">' if zh else '<html lang="en">', '<head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">',
           '<title>' + esc(title) + '</title><style>' + CSS + '</style></head><body><main>',
           '<header><h1>' + esc(title) + '</h1><p class="muted">v' + esc(report["doctor_version"]) +
           ' · schema ' + esc(report["schema_version"]) + ' · ' + esc(report["generated_at"]) + '</p></header>',
           '<section class="counts" aria-label="Status counts">']
    for state, n in report["summary"].items():
        out.append('<div class="count"><span>' + esc(LABELS[lang][state]) + '</span><strong>' + esc(n) + '</strong></div>')
    out.append('</section>')
    if comparison:
        out.append('<p class="priority">' + esc(report["notice"]) + '</p><p>' +
                   esc(("无变化检查数：" if zh else "Unchanged checks: ") + str(report["unchanged"])) + '</p>')
        if not report["changes"]:
            out.append('<p>' + ("比较字段无实质变化。" if zh else "No substantive changes in compared fields.") + '</p>')
        for c in report["changes"]:
            out.append('<article><h2>' + esc(c["id"]) + ' · ' + esc(LABELS[lang][c["change"]]) + '</h2><p>' +
                       esc(c["before"] or "—") + ' → ' + esc(c["after"] or "—") + '</p><p>' + esc(NOTES[lang][c["note"]]) +
                       '</p><pre>' + esc(json.dumps(c["details"], ensure_ascii=False, indent=2)) + '</pre></article>')
    else:
        if "exit_policy" in report:
            out.append('<section class="priority"><h2>' + ("退出条件" if zh else "Exit conditions") +
                       '</h2><p>' + esc(policy_text(report)) + '</p></section>')
        out.append('<section class="priority"><h2>' + ("优先处理：异常 → 提醒 → 无法判断" if zh else "Review first: errors → warnings → unknown") +
                   '</h2><p>' + esc(", ".join(report.get("priorities", [])) or ("无" if zh else "None")) + '</p></section>')
        for f in report["findings"]:
            cls = f["status"] if f["status"] in ("pass", "warn", "error", "unknown", "skipped") else "unknown"
            out.append('<article class="' + cls + '"><h2>' + esc(f["id"]) + ' · <span class="badge">' +
                       esc(LABELS[lang][cls]) + '</span></h2><p>' + esc(f["summary"]) + '</p><pre>' +
                       esc(json.dumps(f["evidence"], ensure_ascii=False, indent=2)) + '</pre>')
            g = f.get("guidance")
            if g:
                out.append('<h3>' + ("现象" if zh else "Observation") + '</h3><p>' + esc(g["phenomenon"]) +
                           '</p><p>' + esc(("判断依据：" if zh else "Basis: ") + g["basis"]) + '</p><h3>' +
                           ("手动复查步骤" if zh else "Manual recheck") + '</h3><ol>' +
                           ''.join('<li>' + esc(step) + '</li>' for step in g["steps"]) + '</ol><p class="muted">' +
                           esc(("检查限制：" if zh else "Limitations: ") + g["limitation"]) + '</p>')
            else:
                out.append('<p>' + esc(f["recommendation"]) + '</p><p>' + esc(f["recheck"]) + '</p>')
            out.append('</article>')
    out.append('<footer class="muted"><p>' + ("离线报告 · 路径原值、配置值和程序原始输出未保存。" if zh else
               "Offline report · Original paths, configuration values and raw program output are not saved.") + '</p></footer></main></body></html>\n')
    return '\n'.join(out)


def policy_text(report):
    p, zh = report["exit_policy"], report["language"] == "zh"
    return (("所选状态：" if zh else "Selected states: ") + ", ".join(p["fail_on"]) +
            ("；触发状态：" if zh else "; triggered states: ") + (", ".join(p["triggered"]) or ("无" if zh else "None")) +
            ("；达到所选退出条件：" if zh else "; selected conditions met: ") +
            (("是" if p["matched"] else "否") if zh else ("Yes" if p["matched"] else "No")) + ". " + p["meaning"])


def observation_text(observation, lang):
    if observation is None:
        return "— 未包含" if lang == "zh" else "— Missing"
    symbols = {"pass": "✓", "warn": "!", "error": "×", "unknown": "?", "skipped": "—"}
    status = observation["status"]
    return symbols[status] + " " + LABELS[lang][status]


def history_markdown(report):
    lang, zh = report["language"], report["language"] == "zh"
    sequence = lambda n: f"第{n}次" if zh else f"Run {n}"
    lines = ["# Windows AI Doctor — " + ("多次体检趋势" if zh else "History"), "",
             f"v{report['doctor_version']} · schema {report['schema_version']}", "", report["generated_at"], "", report["notice"], "",
             "## 各次状态数量" if zh else "## Counts by run", "",
             "| " + ("顺序" if zh else "Sequence") + " | " + " | ".join(LABELS[lang][s] for s in LABELS[lang] if s in report["summary"]) + " |",
             "| --- | " + " | ".join("---" for s in report["summary"]) + " |"]
    for snap in report["snapshots"]:
        lines.append("| " + sequence(snap["sequence"]) + " | " + " | ".join(str(n) for n in snap["summary"].values()) + " |")
    lines.extend(["", "## 检查状态与有限观察" if zh else "## Check states and limited observations", "",
                  "| ID | " + " | ".join(sequence(s["sequence"]) for s in report["snapshots"]) + " |",
                  "| --- | " + " | ".join("---" for _ in report["snapshots"]) + " |"])
    for check in report["checks"]:
        cells = []
        for o in check["observations"]:
            detail = {k: v for k, v in (o or {}).items() if k != "status"}
            cells.append(observation_text(o, lang) + (" " + json.dumps(detail, ensure_ascii=False) if detail else ""))
        lines.append("| " + check["id"] + " | " + " | ".join(cells) + " |")
    for step in report["transitions"]:
        lines.extend(["", "## " + sequence(step["from"]) + " → " + sequence(step["to"]), ""])
        lines.append(("无变化检查数：" if zh else "Unchanged checks: ") + str(step["unchanged"]))
        if not step["changes"]:
            lines.append("比较字段无实质变化。" if zh else "No substantive changes in compared fields.")
        for c in step["changes"]:
            lines.extend(["", f"- {c['id']}: {c['before'] or '—'} → {c['after'] or '—'}. " + NOTES[lang][c["note"]] + " " + json.dumps(c["details"], ensure_ascii=False)])
    return "\n".join(lines) + "\n"


def history_html(report):
    esc = lambda v: html.escape(str(v), quote=True)
    lang, zh = report["language"], report["language"] == "zh"
    sequence = lambda n: f"第{n}次" if zh else f"Run {n}"
    title = "Windows AI Doctor · " + ("多次体检趋势" if zh else "History")
    out = ['<!doctype html><html lang="' + ('zh-CN' if zh else 'en') + '"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">',
           '<title>' + esc(title) + '</title><style>' + CSS + '</style></head><body><main><header><h1>' + esc(title) +
           '</h1><p>v' + esc(report["doctor_version"]) + ' · schema 1.0 · ' + esc(report["generated_at"]) + '</p></header>',
           '<p class="priority">' + esc(report["notice"]) + '</p>',
           '<div class="table-scroll" tabindex="0" role="region" aria-label="' + ('各次状态数量' if zh else 'Counts by run') + '"><table><caption>' +
           ('各次状态数量' if zh else 'Counts by run') + '</caption><thead><tr><th scope="col">' + ('顺序' if zh else 'Sequence') + '</th>' +
           ''.join('<th scope="col">' + esc(LABELS[lang][s]) + '</th>' for s in report["summary"]) + '</tr></thead><tbody>']
    for snap in report["snapshots"]:
        out.append('<tr><th scope="row">' + sequence(snap["sequence"]) + '</th>' + ''.join('<td>' + str(n) + '</td>' for n in snap["summary"].values()) + '</tr>')
    out.append('</tbody></table></div><p>' + ('表格可横向滚动；选择表格区域后也可使用方向键。' if zh else 'Tables scroll horizontally; focus a table region to use the arrow keys.') + '</p>')
    out.append('<div class="table-scroll" tabindex="0" role="region" aria-label="' + ('检查状态' if zh else 'Check states') + '"><table><caption>' +
               ('检查状态与有限观察' if zh else 'Check states and limited observations') + '</caption><thead><tr><th scope="col">ID</th>' +
               ''.join('<th scope="col">' + sequence(s["sequence"]) + '</th>' for s in report["snapshots"]) + '</tr></thead><tbody>')
    for check in report["checks"]:
        out.append('<tr><th scope="row">' + esc(check["id"]) + '</th>')
        for o in check["observations"]:
            detail = {k: v for k, v in (o or {}).items() if k != "status"}
            cls = o["status"] if o and o["status"] in ("pass", "warn", "error", "unknown", "skipped") else "unknown"
            out.append('<td class="' + cls + '"><span class="badge">' + esc(observation_text(o, lang)) + '</span>' +
                       ('<small>' + esc(json.dumps(detail, ensure_ascii=False)) + '</small>' if detail else '') + '</td>')
        out.append('</tr>')
    out.append('</tbody></table></div>')
    for step in report["transitions"]:
        out.append('<article><h2>' + sequence(step["from"]) + ' → ' + sequence(step["to"]) + '</h2><p>' +
                   ('无变化检查数：' if zh else 'Unchanged checks: ') + str(step["unchanged"]) + '</p>')
        if not step["changes"]:
            out.append('<p>' + ('比较字段无实质变化。' if zh else 'No substantive changes in compared fields.') + '</p>')
        for c in step["changes"]:
            out.append('<h3>' + esc(c["id"]) + '</h3><p>' + esc(c["before"] or '—') + ' → ' + esc(c["after"] or '—') +
                       '</p><p>' + esc(NOTES[lang][c["note"]]) + '</p><pre>' + esc(json.dumps(c["details"], ensure_ascii=False)) + '</pre>')
        out.append('</article>')
    out.append('<footer><p>' + ('离线汇总；未做新扫描，未读取报告所指路径。' if zh else 'Offline summary; no new scan or access to paths embedded in reports.') + '</p></footer></main></body></html>\n')
    return '\n'.join(out)
