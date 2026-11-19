import json

LABELS = {
    "zh": {"pass": "通过", "warn": "提醒", "error": "异常", "unknown": "无法判断", "skipped": "未检查"},
    "en": {"pass": "Pass", "warn": "Warning", "error": "Error", "unknown": "Unknown", "skipped": "Not checked"},
}


def json_report(report):
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def markdown_report(report):
    zh = report["language"] == "zh"
    lines = ["# Windows AI Doctor", "", f"v{report['doctor_version']} · schema {report['schema_version']}",
             "", report["generated_at"], "",
             " · ".join(f"{LABELS[report['language']][s]}: {n}" for s, n in report["summary"].items()), "",
             "路径使用代号，原始映射未保存；语法通过不代表服务可用。" if zh else
             "Paths use opaque references; the original mapping is not saved. Valid syntax does not establish service availability.", ""]
    for finding in report["findings"]:
        lines.extend([f"## {finding['id']} — {LABELS[report['language']][finding['status']]}", "",
                      finding["summary"], "", "```json", json.dumps(finding["evidence"], ensure_ascii=False, indent=2),
                      "```", "", ("建议：" if zh else "Recommendation: ") + finding["recommendation"], "",
                      ("复查：" if zh else "Recheck: ") + finding["recheck"], ""])
    return "\n".join(lines)
