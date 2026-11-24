"""Deterministic JUnit policy results over whitelisted diagnosis observations."""
import xml.etree.ElementTree as ET

from .compare import project

MESSAGES = {
    "zh": ("命中退出条件：", "新发现（相对基线）", "固定规则回归", "这是退出策略结果，不等于已确认故障根因。", "；"),
    "en": ("Selected exit condition: ", "New finding versus baseline", "Regression under fixed rules",
           "This is a policy result, not a confirmed root cause.", "; "),
}


def junit_report(report):
    current = project(report)
    selected = set(report["exit_policy"]["fail_on"])
    baseline = report.get("baseline")
    changes = {c["id"]: c["change"] for c in baseline["changes"]} if baseline is not None else {}
    new = set(baseline["new_findings"]) if baseline is not None else set()
    regressions = set(baseline["regressions"]) if baseline is not None else set()
    status_message, new_message, regression_message, notice, separator = MESSAGES[report["language"]]
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite")
    failures = skipped = 0
    for check_id, observation in sorted(current.items()):
        status = observation["status"]
        case = ET.SubElement(suite, "testcase", classname="windows-ai-doctor." + check_id.split(".", 1)[0], name=check_id)
        properties = ET.SubElement(case, "properties")
        values = {"status": status}
        if "scan_limited" in observation:
            values["scan_limited"] = str(observation["scan_limited"]).lower()
        if baseline is not None:
            values.update(baseline_change=changes.get(check_id, "unchanged"),
                          baseline_new=str(check_id in new).lower(),
                          baseline_regression=str(check_id in regressions).lower())
        for name, value in values.items():
            ET.SubElement(properties, "property", name=name, value=value)
        reasons = []
        if status in selected and status in ("error", "warn", "unknown"):
            reasons.append(status_message + status)
        if "new" in selected and check_id in new:
            reasons.append(new_message)
        if "regression" in selected and check_id in regressions:
            reasons.append(regression_message)
        if reasons:
            ET.SubElement(case, "failure", type="policy", message=separator.join(reasons)).text = notice
            failures += 1
        elif status == "skipped":
            ET.SubElement(case, "skipped")
            skipped += 1
    counts = {"tests": str(len(current)), "failures": str(failures), "skipped": str(skipped), "errors": "0"}
    root.attrib.update(name="Windows AI Doctor", **counts)
    suite.attrib.update(name="windows-ai-doctor", **counts)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
