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
"""


def html_report(report):
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
