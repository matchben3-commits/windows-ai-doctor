"""Create local-only browser QA fixtures; never open the browser automatically."""
import copy
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_ai_doctor.report import html_report

destination = ROOT / "evidence/html"
destination.mkdir(parents=True, exist_ok=True)
report = json.loads((ROOT / "examples/v02-complete/zh/report.zh.json").read_text(encoding="utf-8"))
report = copy.deepcopy(report)
f = report["findings"][0]
f["summary"] = '公开合成显示夹具：<script>window.injected=1</script><img src="https://invalid.invalid" onerror="alert(1)">；' + '长文本换行检查' * 50
(destination / "security.html").write_text(html_report(report), encoding="utf-8")
(destination / "narrow.html").write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>390px viewport QA</title>
<style>body{margin:12px;background:#dde4ed}iframe{display:block;width:390px;height:650px;border:0}</style>
<iframe title="390 CSS pixel report viewport" src="security.html"></iframe></html>''', encoding="utf-8")
print("Local browser fixtures created; report source is synthetic.")
