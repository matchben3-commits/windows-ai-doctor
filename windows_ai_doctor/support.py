"""Rebuild a small support summary; never archive the imported document."""
import hashlib
import json
import sys
import zipfile

from . import __version__
from .history import counts

NOTICE = {
    "zh": "这是用于求助的有限摘要，请自行审阅后分享；不会自动发送。不保证任意诊断信号都无法关联。无原始路径映射。未收录配置、日志、凭据、原报告文字和原始输出；未做新扫描。状态数量不是健康评分，未检查或未知不代表通过。",
    "en": "This is a limited support summary. Review it before sharing; it is not sent automatically. Diagnostic signals may still be linkable. No original path mapping is available. Configuration, logs, credentials, original report text and raw output are omitted; no new scan was performed. Counts are not a health score; skipped or unknown checks are not passes.",
}


def support_members(projected):
    # projected is the whitelist result from load_report, not the raw input.
    result = {"schema_version": "1.0", "report_type": "support", "doctor_version": __version__,
              "summary": counts(projected),
              "findings": [{"id": id, "status": f["status"],
                            "evidence": {k: v for k, v in f.items() if k != "status"}}
                           for id, f in sorted(projected.items())]}
    members = {"support.json": (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")}
    from .report import LABELS
    for lang in ("zh", "en"):
        lines = ["# Windows AI Doctor — " + ("求助摘要" if lang == "zh" else "Support summary"),
                 "", NOTICE[lang], "", " · ".join(f"{LABELS[lang][s]}: {n}" for s, n in result["summary"].items()),
                 "", "| ID | " + ("状态 | 有限观察 |" if lang == "zh" else "Status | Limited observations |"), "| --- | --- | --- |"]
        for f in result["findings"]:
            lines.append(f"| {f['id']} | {LABELS[lang][f['status']]} | " + json.dumps(f["evidence"], sort_keys=True) + " |")
        members[f"summary.{lang}.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    members["PRIVACY.txt"] = (NOTICE["zh"] + "\n\n" + NOTICE["en"] + "\n").encode("utf-8")
    members["SHA256SUMS.txt"] = ("\n".join(hashlib.sha256(data).hexdigest() + "  " + name
                                                 for name, data in sorted(members.items())) + "\n").encode("ascii")
    return members


def export_support(projected, directory):
    members = support_members(projected)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "support-bundle.zip"
    created = False
    try:
        with target.open("xb") as stream:
            created = True
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, data in members.items():
                    archive.writestr(name, data)
    except BaseException:
        if created:
            try:
                target.unlink()
            except OSError:
                print("求助包中断；本次文件未能清理 / Support export interrupted; new file could not be removed.", file=sys.stderr)
        raise
