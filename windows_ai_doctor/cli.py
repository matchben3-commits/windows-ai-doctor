import argparse
import math
import sys
from pathlib import Path

from . import __version__
from .core import Doctor
from .report import json_report, markdown_report, html_report
from .compare import load_report, compare_reports


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "参数错误，请查看 --help / Invalid arguments; see --help.\n")


def parser():
    p = SafeParser(allow_abbrev=False, description="Windows AI Doctor: 离线只读体检 / offline read-only diagnostics")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--tools", nargs="+", choices=("codex", "claude"), default=["codex", "claude"], help="选择工具 / select tools")
    p.add_argument("--lang", choices=("zh", "en"), default="zh", help="报告语言 / report language")
    p.add_argument("--format", choices=("both", "md", "json", "html", "all"), default="both", help="both=MD+JSON; all=MD+JSON+HTML; stdout: both/all use MD")
    p.add_argument("--compare", nargs=2, type=Path, metavar=("OLD.json", "NEW.json"), help="离线对比，不运行诊断；禁用诊断参数 / offline comparison; conflicts with diagnostic options; output: comparison.LANG.FORMAT")
    p.add_argument("--output-dir", type=Path, help="新建报告目录 / report directory (existing reports are not overwritten)")
    p.add_argument("--home", type=Path, help="诊断目标用户目录 / diagnostic user home override")
    p.add_argument("--project", type=Path, help="只检查此项目根目录 / inspect only this explicit project root")
    p.add_argument("--timeout", type=float, default=3.0, help="每个版本/列表查询的秒数，0.1–30 / per probe seconds")
    p.add_argument("--no-version", action="store_true", help="不执行工具或 Node / skip CLI and Node execution")
    p.add_argument("--wsl-list", action="store_true", help="可选只读查询运行中的发行版数量 / optional read-only running distribution count")
    return p


def export_reports(rendered, directory, stem, lang):
    directory.mkdir(parents=True, exist_ok=True)
    targets = {fmt: directory / f"{stem}.{lang}.{fmt}" for fmt in rendered}
    if any(path.exists() or path.is_symlink() for path in targets.values()):
        raise FileExistsError("report_exists")
    created = []
    try:
        for fmt, path in targets.items():
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                created.append(path)
                stream.write(rendered[fmt])
    except BaseException:
        cleanup_ok = True
        for path in reversed(created):
            try:
                path.unlink()
            except OSError:
                cleanup_ok = False
        print("导出中断；本次新文件已清理 / Export interrupted; new files removed." if cleanup_ok else
              "导出中断；部分本次文件未能清理 / Export interrupted; some new files could not be removed.", file=sys.stderr)
        raise


def main(argv=None):
    # Consistent UTF-8 for Windows pipes as well as terminals.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        raw_args = list(sys.argv[1:] if argv is None else argv)
        args = parser().parse_args(raw_args)
        if not math.isfinite(args.timeout) or not 0.1 <= args.timeout <= 30:
            parser().error("")
        comparison = args.compare is not None
        diagnostic_options = {"--tools", "--home", "--project", "--timeout", "--no-version", "--wsl-list"}
        if comparison and any(token.split("=", 1)[0] in diagnostic_options for token in raw_args):
            parser().error("")
        report = compare_reports(load_report(args.compare[0]), load_report(args.compare[1]), args.lang) if comparison else Doctor(home=args.home, lang=args.lang, tools=tuple(dict.fromkeys(args.tools)),
                        timeout=args.timeout, versions=not args.no_version,
                        project=args.project, wsl_list=args.wsl_list).run()
        formats = ("md", "json") if args.format == "both" else ("md", "json", "html") if args.format == "all" else (args.format,)
        renderers = {"md": markdown_report, "json": json_report, "html": html_report}
        rendered = {fmt: renderers[fmt](report) for fmt in formats}
        if args.output_dir is None:
            # JSON goes alone to stdout for pipelines; both defaults to Markdown.
            print(rendered["md"] if "md" in rendered else next(iter(rendered.values())), end="")
        else:
            export_reports(rendered, args.output_dir, "comparison" if comparison else "report", args.lang)
            print("报告已保存（路径未回显）。" if args.lang == "zh" else "Reports saved (paths withheld).")
        return 0 if comparison else 1 if report["summary"]["error"] else 0
    except KeyboardInterrupt:
        print("已中断 / Interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, RecursionError, UnicodeError):
        print("诊断或导出未完成；详细异常已隐藏 / Diagnosis or export incomplete; exception details withheld.", file=sys.stderr)
        return 2
