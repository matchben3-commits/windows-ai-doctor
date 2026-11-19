import argparse
import math
import sys
from pathlib import Path

from . import __version__
from .core import Doctor
from .report import json_report, markdown_report


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "参数错误，请查看 --help / Invalid arguments; see --help.\n")


def parser():
    p = SafeParser(description="Windows AI Doctor: 离线只读体检 / offline read-only diagnostics")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--tools", nargs="+", choices=("codex", "claude"), default=["codex", "claude"], help="选择工具 / select tools")
    p.add_argument("--lang", choices=("zh", "en"), default="zh", help="报告语言 / report language")
    p.add_argument("--format", choices=("both", "md", "json"), default="both", help="报告格式 / report format")
    p.add_argument("--output-dir", type=Path, help="新建报告目录 / report directory (existing reports are not overwritten)")
    p.add_argument("--home", type=Path, help="诊断目标用户目录 / diagnostic user home override")
    p.add_argument("--project", type=Path, help="只检查此项目根目录 / inspect only this explicit project root")
    p.add_argument("--timeout", type=float, default=3.0, help="每个版本/列表查询的秒数，0.1–30 / per probe seconds")
    p.add_argument("--no-version", action="store_true", help="不执行工具或 Node / skip CLI and Node execution")
    p.add_argument("--wsl-list", action="store_true", help="可选只读查询运行中的发行版数量 / optional read-only running distribution count")
    return p


def main(argv=None):
    # Consistent UTF-8 for Windows pipes as well as terminals.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        args = parser().parse_args(argv)
        if not math.isfinite(args.timeout) or not 0.1 <= args.timeout <= 30:
            parser().error("")
        report = Doctor(home=args.home, lang=args.lang, tools=tuple(dict.fromkeys(args.tools)),
                        timeout=args.timeout, versions=not args.no_version,
                        project=args.project, wsl_list=args.wsl_list).run()
        formats = ("md", "json") if args.format == "both" else (args.format,)
        rendered = {fmt: markdown_report(report) if fmt == "md" else json_report(report) for fmt in formats}
        if args.output_dir is None:
            # JSON goes alone to stdout for pipelines; both defaults to Markdown.
            print(rendered["md"] if "md" in rendered else rendered["json"], end="")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            targets = {fmt: args.output_dir / f"report.{args.lang}.{fmt}" for fmt in formats}
            if any(path.exists() for path in targets.values()):
                print("已有报告，请使用新目录 / Report exists; use a new directory.", file=sys.stderr)
                return 2
            for fmt, path in targets.items():
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(rendered[fmt])
            print("报告已保存（路径未回显）。" if args.lang == "zh" else "Reports saved (paths withheld).")
        return 1 if report["summary"]["error"] else 0
    except KeyboardInterrupt:
        print("已中断 / Interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, RecursionError):
        print("诊断或导出未完成；详细异常已隐藏 / Diagnosis or export incomplete; exception details withheld.", file=sys.stderr)
        return 2
