"""Fixed, non-echoing results for offline validity and bundle checks."""
from . import __version__
from .history import counts

VALIDATION_NOTICE = {
    "zh": "仅确认报告可按当前已知字段和边界接受；未知字段已忽略，未全面审核自由文本，未运行诊断。检查数为0不表示健康或完整。状态数量重新计算，报告有效不表示检查通过。",
    "en": "Acceptable under current known fields and bounds only; unknown fields were ignored. Free text was not comprehensively audited and no diagnosis was run. Zero checks do not establish health or completeness. Counts were recomputed; a valid report does not mean its checks passed.",
}
VERIFICATION_NOTICE = {
    "zh": "仅核对固定成员、CRC、SHA及求助摘要的内部一致性；清单没有自签名，不能证明来源身份、机器现状、未经重新打包或包内任意文字不含私密信息。未解压落盘、执行、扫描或分享。",
    "en": "Checks fixed members, CRC, SHA and support-summary consistency only. The manifest is not self-signed. This does not establish source identity, current machine state, absence of repackaging, or privacy of arbitrary bundle text. Nothing was extracted to disk, executed, scanned or shared.",
}


def validation_report(projected, lang="zh"):
    return {"schema_version": "1.0", "report_type": "validation", "doctor_version": __version__,
            "language": lang, "valid": True, "check_count": len(projected), "summary": counts(projected),
            "notice": VALIDATION_NOTICE[lang]}


def verification_report(metrics, lang="zh"):
    return {"schema_version": "1.0", "report_type": "support_verification", "doctor_version": __version__,
            "language": lang, "verified": True, **metrics, "notice": VERIFICATION_NOTICE[lang]}


def verification_markdown(report):
    zh = report["language"] == "zh"
    validating = report["report_type"] == "validation"
    title = ("报告输入校验通过" if zh else "Report input accepted") if validating else ("求助包完整性核验通过" if zh else "Support bundle integrity verified")
    lines = ["# Windows AI Doctor — " + title, "", report["notice"], ""]
    if validating:
        lines.extend([("已知检查数：" if zh else "Known checks: ") + str(report["check_count"]), ""])
        lines.extend(f"- {state}: {count}" for state, count in report["summary"].items())
    else:
        for name in ("member_count", "archive_bytes", "uncompressed_bytes"):
            lines.append(f"- {name}: {report[name]}")
    return "\n".join(lines) + "\n"
