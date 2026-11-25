"""Compare new original-session evidence with a prior two-snapshot comparison."""
import json

from .snapshot import compare_snapshots, comparison_markdown, current_scope, original_result


SCENARIO_EVIDENCE = {
    "alias_function_shadowing": ("resolution.preferred",),
    "process_path_difference": ("environment.path", "resolution.preferred"),
    "multiple_launcher_precedence": ("resolution.preferred",),
}


def retest_snapshots(working, before, after, lang):
    scope = current_scope()
    prior = compare_snapshots(working, before, lang, current=scope)
    current = compare_snapshots(working, after, lang, current=scope)
    reason = prior["reason"] or current["reason"]
    if not reason and len({s["command"] for s in (working, before, after)}) != 1:
        reason = "target_mismatch"
    cutoff = max(working["captured_at"], before["captured_at"])
    if not reason and after["captured_at"] <= cutoff:
        reason = "retest_not_newer"
    if reason:
        return {"report_type": "snapshot_retest", "schema_version": "snapshot-retest-1.0", "language": lang,
                "times": {"T1": working["captured_at"], "T2": before["captured_at"], "T3": after["captured_at"]},
                "comparability": "incomparable", "reason": reason, "prior": None, "current": None,
                "changes_since_before": None, "explanation_reviews": [], "original_command_status": "unverified"}

    result = after["command_result"]
    stale_result = (result["recorded_at"] != after["captured_at"]
                    or (result["executed_at"] is not None and not cutoff < result["executed_at"] <= result["recorded_at"]))
    if stale_result:
        after = {**after, "command_result": {"status": "unverified", "source": "none",
                                            "recorded_at": after["captured_at"], "executed_at": None,
                                            "session_match": "unknown"}}
        current = compare_snapshots(working, after, lang, current=scope)
    status = original_result(after)
    change = compare_snapshots(before, after, lang, current=scope)
    current["notice"] = current["notice"].replace("T1/T2", "T1/T3")
    same_context = (working["session_role"] == "working" and before["session_role"] == after["session_role"] == "failing"
                    and after["symptom"] == before["symptom"])
    reviews = []
    for explanation in prior["explanations"]:
        scenario = explanation["scenario"]
        evidence = SCENARIO_EVIDENCE[scenario]
        if scenario == "multiple_launcher_precedence" and "resolution.version" in prior["differences"]:
            evidence += ("resolution.version",)
        relation, assessment = "unassessed", "insufficient_evidence"
        if same_context and not set(evidence).intersection(current["evidence_gaps"]):
            remaining = set(evidence).intersection(current["differences"])
            if not remaining:
                relation, assessment = "disappeared", "no_longer_sufficient"
            elif remaining == set(evidence):
                relation = "retained"
                if any(e["scenario"] == scenario for e in current["explanations"]) and status != "success":
                    assessment = "still_possible"
                elif status == "success":
                    assessment = "no_current_failure_observed"
        reviews.append({"scenario": scenario, "prior_level": explanation["level"], "prior_evidence": list(evidence),
                        "relation": relation, "assessment": assessment})
    report = {"report_type": "snapshot_retest", "schema_version": "snapshot-retest-1.0", "language": lang,
              "times": {"T1": working["captured_at"], "T2": before["captured_at"], "T3": after["captured_at"]},
              "comparability": "same_scope", "reason": None, "prior": prior, "current": current,
              "changes_since_before": change["differences"], "explanation_reviews": reviews,
              "original_command_status": status}
    if stale_result:
        report["stale_command_result"] = result
    before_layers = prior.get("working_launcher_directory", {}).get("failing")
    after_layers = current.get("working_launcher_directory", {}).get("failing")
    if same_context and before_layers and after_layers and before_layers["process"] == "absent" and after_layers["process"] == "present":
        layers = [name for name in ("user", "machine") if before_layers[name] == after_layers[name] == "present"]
        if layers:
            report["path_transition"] = {"directory": "working_launcher", "process_before": "absent",
                                         "process_after": "present", "persistent_layers_observed_both_times": layers}
    return report


def retest_markdown(report):
    zh = report["language"] == "zh"
    lines = ["# Windows AI Doctor", "", "三时点复测" if zh else "Three-snapshot retest", ""]
    lines.extend(f"{label}: {time}" for label, time in report["times"].items())
    if report["reason"]:
        lines += ["", ("不可比：" if zh else "Incomparable: ") + report["reason"]]
        return "\n".join(lines) + "\n"
    status = report["original_command_status"]
    label = {
        "failure": ("原命令仍失败", "The original command still failed"),
        "unverified": ("原命令结果未验证", "The original command result is unverified"),
        "success": ("本次原命令成功", "The original command succeeded on this attempt"),
    }[status][0 if zh else 1]
    result = report["current"]["command_results"]["B"]
    if status != "unverified" and result["source"] == "user_report":
        label += "（用户自述）" if zh else " (user report)"
    elif status != "unverified" and result["source"] == "controlled_test":
        label += "（受控测试）" if zh else " (controlled test)"
    lines += ["", f"{label}。" if zh else f"{label}.",
              f"executed_at={result['executed_at'] or 'unknown'}, session_match={result['session_match']}"]
    for item in report["explanation_reviews"]:
        lines += ["", item["scenario"]]
        if item["relation"] == "disappeared":
            lines.append(("相关差异已消失，" + label + "。上次的解释已不充分。") if zh else
                         "The relevant differences disappeared. " + label + ". The prior explanation is no longer sufficient.")
        elif item["relation"] == "retained":
            lines.append("相关差异仍存在。" if zh else "The relevant differences remain.")
        else:
            lines.append("证据不足，无法判断相关差异是否仍存在。" if zh else
                         "Evidence is insufficient to determine whether the relevant differences remain.")
    for field in ("explanation_reviews", "changes_since_before", "path_transition", "stale_command_result"):
        if field in report:
            lines += ["", field, "", "```json", json.dumps(report[field], ensure_ascii=False, indent=2), "```"]
    for key, heading in (("prior", "T1 ↔ T2"), ("current", "T1 ↔ T3")):
        detail = comparison_markdown(report[key], end_label=heading[-2:])
        lines += ["", "## " + heading, "", detail.removeprefix("# Windows AI Doctor\n\n").rstrip()]
    return "\n".join(lines) + "\n"
