import argparse
import math
import sys
from pathlib import Path

from . import __version__
from .core import Doctor
from .report import json_report, markdown_report, html_report
from .compare import load_report, compare_reports, comparison_csv
from .diagnosis_schema import schema_json
from .history import load_history, history_report, history_csv
from .support import export_support
from .validation import validation_report, verification_report
from .verify_support import verify_support


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "参数错误，请查看 --help / Invalid arguments; see --help.\n")


def parser():
    p = SafeParser(allow_abbrev=False, description="Windows AI Doctor: 离线只读体检 / offline read-only diagnostics")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--tools", nargs="+", choices=("codex", "claude"), default=["codex", "claude"], help="选择工具 / select tools")
    p.add_argument("--lang", choices=("zh", "en"), default="zh", help="报告语言 / report language")
    p.add_argument("--format", choices=("both", "md", "json", "html", "all", "csv"), default="both", help="both=MD+JSON; all=MD+JSON+HTML; csv仅history/compare / csv history/compare only; catalog: both/md/json, default md; validate/verify-support: both/md/json; schema: no explicit format; stdout: both/all use MD")
    p.add_argument("--compare", nargs=2, type=Path, metavar=("OLD.json", "NEW.json"), help="离线对比，不运行诊断；禁用诊断参数 / offline comparison; conflicts with diagnostic options; output: comparison.LANG.FORMAT")
    p.add_argument("--history", nargs="+", type=Path, metavar="REPORT.json", help="2–20份诊断报告的离线趋势，按输入顺序 / offline history in input order; output: history.LANG.FORMAT")
    p.add_argument("--support", type=Path, metavar="REPORT.json", help="生成有限求助摘要ZIP，需输出目录；自行审阅分享，不保证无法关联，无原始路径映射 / limited support ZIP, requires output directory; review before sharing, signals may be linkable, no original path mapping")
    p.add_argument("--validate", type=Path, metavar="REPORT.json", help="离线校验诊断输入的已知字段与边界 / offline input validity under known fields and bounds")
    p.add_argument("--verify-support", type=Path, metavar="BUNDLE.zip", help="离线核验求助包结构/CRC/SHA/内部一致性，不证明来源或隐私 / offline bundle structure/CRC/SHA/consistency; no source or privacy assurance")
    p.add_argument("--catalog", nargs="*", metavar="CHECK_ID", help="导出固定19项检查目录，可选最多32个精确ID；默认md，不运行诊断 / export fixed 19-check catalog, up to 32 exact IDs; default md, no diagnosis")
    p.add_argument("--schema", action="store_true", help="导出确定性的诊断输入JSON Schema；仅允许output-dir / deterministic diagnosis input JSON Schema; only output-dir allowed; --validate remains authoritative")
    p.add_argument("--fail-on", nargs="+", choices=("error", "warn", "unknown"), help="诊断退出条件，默认error；选中状态出现则退出1，不改变检查状态 / diagnosis exit conditions, default error; matched states exit 1 without changing findings")
    p.add_argument("--output-dir", type=Path, help="新建报告目录 / report directory (existing reports are not overwritten)")
    p.add_argument("--home", type=Path, help="诊断目标用户目录 / diagnostic user home override")
    p.add_argument("--project", type=Path, help="只检查此项目根目录 / inspect only this explicit project root")
    p.add_argument("--timeout", type=float, default=3.0, help="每个版本/列表查询的秒数，0.1–30 / per probe seconds")
    p.add_argument("--no-version", action="store_true", help="不执行工具或 Node / skip CLI and Node execution")
    p.add_argument("--wsl-list", action="store_true", help="可选只读查询运行中的发行版数量 / optional read-only running distribution count")
    return p


def export_reports(rendered, directory, stem, lang):
    export_files({f"{stem}.{lang}.{fmt}": body for fmt, body in rendered.items()}, directory)


def export_files(contents, directory):
    directory.mkdir(parents=True, exist_ok=True)
    targets = {name: directory / name for name in contents}
    if any(path.exists() or path.is_symlink() for path in targets.values()):
        raise FileExistsError("report_exists")
    created = []
    try:
        for name, path in targets.items():
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                created.append(path)
                stream.write(contents[name])
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
            stream.reconfigure(encoding="utf-8", errors="backslashreplace", newline="\n")
    try:
        raw_args = list(sys.argv[1:] if argv is None else argv)
        args = parser().parse_args(raw_args)
        if not math.isfinite(args.timeout) or not 0.1 <= args.timeout <= 30:
            parser().error("")
        comparison = args.compare is not None
        history = args.history is not None
        support = args.support is not None
        validating = args.validate is not None
        verifying = args.verify_support is not None
        catalog = args.catalog is not None
        schema = args.schema
        offline = comparison or history or support or validating or verifying or catalog or schema
        if sum((comparison, history, support, validating, verifying, catalog, schema)) > 1:
            parser().error("")
        diagnostic_options = {"--tools", "--home", "--project", "--timeout", "--no-version", "--wsl-list"}
        explicit = {token.split("=", 1)[0] for token in raw_args}
        if offline and explicit & (diagnostic_options | {"--fail-on"}):
            parser().error("")
        if args.format == "csv" and not (history or comparison):
            parser().error("")
        if (validating or verifying) and args.format not in ("both", "md", "json"):
            parser().error("")
        if schema:
            if explicit & {"--format", "--lang"}:
                parser().error("")
            rendered_schema = schema_json()
            if args.output_dir is None:
                print(rendered_schema, end="")
            else:
                export_files({"schema.diagnosis.json": rendered_schema}, args.output_dir)
            return 0
        if catalog:
            if args.format not in ("both", "md", "json") or len(args.catalog) > 32:
                parser().error("")
            from .catalog import catalog_report, catalog_markdown
            report = catalog_report(args.catalog, args.lang)
            fmt = args.format if "--format" in explicit else "md"
            rendered_catalog = {kind: (catalog_markdown(report) if kind == "md" else json_report(report))
                                for kind in (("md", "json") if fmt == "both" else (fmt,))}
            if args.output_dir is None:
                print(rendered_catalog["md"] if "md" in rendered_catalog else rendered_catalog["json"], end="")
            else:
                export_reports(rendered_catalog, args.output_dir, "catalog", args.lang)
                print("目录已保存（路径未回显）。" if args.lang == "zh" else "Catalog saved (paths withheld).")
            return 0
        if support:
            if args.output_dir is None or explicit & {"--format", "--lang"}:
                parser().error("")
            export_support(load_report(args.support), args.output_dir)
            print("求助摘要已保存，请自行审阅后分享；路径未回显 / Support summary saved; review before sharing; paths withheld.")
            return 0
        if validating:
            report = validation_report(load_report(args.validate), args.lang)
        elif verifying:
            report = verification_report(verify_support(args.verify_support), args.lang)
        elif history:
            report = history_report(load_history(args.history), args.lang)
        elif comparison:
            old, new = load_report(args.compare[0]), load_report(args.compare[1])
            report = compare_reports(old, new, args.lang)
        else:
            report = Doctor(home=args.home, lang=args.lang, tools=tuple(dict.fromkeys(args.tools)),
                        timeout=args.timeout, versions=not args.no_version,
                        project=args.project, wsl_list=args.wsl_list).run()
            selected = [s for s in ("error", "warn", "unknown") if s in (args.fail_on or ["error"])]
            triggered = [s for s in selected if report["summary"][s]]
            report["exit_policy"] = {"fail_on": selected, "triggered": triggered, "matched": bool(triggered),
                "meaning": ("达到所选退出条件仅表示出现选中状态；无法判断不等于已确认故障。操作失败退出2，中断130。" if args.lang == "zh" else
                            "Meeting the selected exit conditions means a selected state occurred; unknown is not a confirmed fault. Operational failure exits 2; interruption exits 130.")}
        formats = ("md", "json") if args.format == "both" else ("md", "json", "html") if args.format == "all" else (args.format,)
        renderers = {"md": markdown_report, "json": json_report, "html": html_report, "csv": history_csv}
        rendered = {"csv": comparison_csv(old, new)} if comparison and args.format == "csv" else {fmt: renderers[fmt](report) for fmt in formats}
        if args.output_dir is None:
            # JSON goes alone to stdout for pipelines; both defaults to Markdown.
            print(rendered["md"] if "md" in rendered else next(iter(rendered.values())), end="")
        else:
            stem = "validation" if validating else "support-verification" if verifying else "history" if history else "comparison" if comparison else "report"
            export_reports(rendered, args.output_dir, stem, args.lang)
            if args.format != "csv":
                print("报告已保存（路径未回显）。" if args.lang == "zh" else "Reports saved (paths withheld).")
        return 0 if offline else int(report["exit_policy"]["matched"])
    except KeyboardInterrupt:
        print("已中断 / Interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, RecursionError, UnicodeError):
        print("诊断或导出未完成；详细异常已隐藏 / Diagnosis or export incomplete; exception details withheld.", file=sys.stderr)
        return 2
