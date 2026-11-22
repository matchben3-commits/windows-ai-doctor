"""Offline SARIF 2.1.0 without file locations or imported evidence."""
import json

from . import __version__
from .catalog import catalog_report
from .compare import STATES, project

SCHEMA_URI = "https://docs.oasis-open.org/sarif/sarif/v2.1.0/cos02/schemas/sarif-schema-2.1.0.json"
REPOSITORY_URI = "https://github.com/matchben3-commits/windows-ai-doctor"
HELP_URI = REPOSITORY_URI + "/blob/main/docs/v06-contract.md"
LEVELS = {"error": "error", "warn": "warning", "unknown": "note"}
NOTICE = {
    "zh": "无文件位置的 SARIF 2.1.0 子集；不含源文件位置，不宣称可直接用于 GitHub code scanning。executionSuccessful 仅表示工具完成执行，不表示健康或通过。未知或扫描受限不代表故障或修复。",
    "en": "SARIF 2.1.0 subset without source-file locations; direct GitHub code scanning use is not claimed. executionSuccessful means only that the tool completed, not health or a pass. Unknown or scan-limited observations establish neither a fault nor a fix.",
}


def sarif_document(report):
    lang = report["language"]
    current = project(report)
    checks = catalog_report(lang=lang)["checks"]
    rules = [{"id": check["id"], "name": check["id"],
              "shortDescription": {"text": check["purpose"][lang]},
              "fullDescription": {"text": check["limitation"][lang]},
              "help": {"text": check["limitation"][lang]}, "helpUri": HELP_URI,
              "defaultConfiguration": {"level": "warning"},
              "properties": {key: check[key] for key in ("target", "availability", "evidence_fields")}}
             for check in checks]
    indices = {rule["id"]: index for index, rule in enumerate(rules)}
    findings = {finding["id"]: finding for finding in report["findings"]}
    results = []
    for check_id, observation in sorted(current.items()):
        status = observation["status"]
        if status not in LEVELS:
            continue
        properties = {"status": status, "target": check_id.split(".", 1)[0]}
        if "scan_limited" in observation:
            properties["scan_limited"] = observation["scan_limited"]
        results.append({"ruleId": check_id, "ruleIndex": indices[check_id], "level": LEVELS[status],
                        "message": {"text": findings[check_id]["summary"]}, "properties": properties})
    policy = report["exit_policy"]
    properties = {"language": lang, "schema_version": "1.0",
                  "summary": {state: sum(item["status"] == state for item in current.values()) for state in STATES},
                  "fail_on": list(policy["fail_on"]), "triggered": list(policy["triggered"]),
                  "matched": policy["matched"],
                  "scan_limited_checks": [check_id for check_id in sorted(current) if current[check_id].get("scan_limited") is True],
                  "notice": NOTICE[lang]}
    if "baseline" in report:
        properties["baseline"] = {key: report["baseline"][key] for key in ("summary", "unchanged", "regressions")}
    return {"$schema": SCHEMA_URI, "version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "Windows AI Doctor", "semanticVersion": __version__,
                            "informationUri": REPOSITORY_URI, "rules": rules}},
        "results": results,
        "invocations": [{"executionSuccessful": True, "exitCode": int(policy["matched"]), "properties": properties}],
        "properties": {"status_vocabulary": list(STATES), "notice": NOTICE[lang], "diagnosis_schema_version": "1.0"},
    }]}


def sarif_report(report):
    return json.dumps(sarif_document(report), ensure_ascii=False, indent=2) + "\n"
