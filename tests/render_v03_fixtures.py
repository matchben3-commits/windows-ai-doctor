"""Local 390px iframe QA without changing browser settings."""
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_ai_doctor.report import html_report

dest = ROOT / "evidence/v03-html"
dest.mkdir(parents=True, exist_ok=True)
for lang in ("zh", "en"):
    # Refresh renderings from saved synthetic data after style changes.
    for name in ("history-" + lang, "history-20-" + lang):
        folder = ROOT / "examples/v03" / name
        if name.startswith("history-20"):
            from windows_ai_doctor.history import load_history, history_report
            paths = [ROOT / "examples/v03" / f"run{n}.json" for n in (1, 2, 3)] * 6
            paths += [ROOT / "examples/v03/run2.json", ROOT / "examples/v03/run3.json"]
            doc = history_report(load_history(paths), lang)
        else:
            doc = json.loads((folder / f"history.{lang}.json").read_text(encoding="utf-8"))
        (folder / f"history.{lang}.html").write_text(html_report(doc), encoding="utf-8")
    (dest / ("narrow-" + lang + ".html")).write_text('''<!doctype html><html lang="''' + lang + '''"><meta charset="utf-8"><title>390px history QA</title>
<style>body{margin:12px;background:#dde4ed}iframe{display:block;width:390px;height:680px;border:0}</style>
<iframe title="390 CSS pixel history viewport" src="../../examples/v03/history-20-''' + lang + '/history.' + lang + '.html"></iframe></html>', encoding="utf-8")
print("v03 local QA fixtures created")
