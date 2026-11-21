"""Fixed offline check catalog. No diagnosis, inputs, environment, network or registry."""
from . import __version__
from .compare import IDS, STATES

MAX_CATALOG_IDS = 32
PROJECT_ONLY = frozenset({"codex.config.project", "claude.config.project", "claude.config.local"})

NOTICE = {
    "zh": ("本目录列出当前版本会生成的稳定检查 ID 及固定说明；不表示检查一定执行、环境健康，"
           "目录本身也不能验证安装。不读取输入文件，不运行诊断，不访问环境、注册表、网络或包内路径。"),
    "en": ("This catalog lists stable check IDs and fixed descriptions the current version can produce. "
           "It does not assert that checks always run, that the environment is healthy, or that the "
           "catalog itself verifies installations. No input files, diagnosis, environment, registry, "
           "network or packaged paths are consulted."),
}

# purpose/limitation stay fixed bilingual literals; never splice environment or user text.
ENTRIES = {
    "claude.config.local": {
        "target": "claude",
        "evidence_fields": ["layer", "effective_loading", "path", "format", "syntax", "line"],
        "purpose": {
            "zh": "在显式 --project 根下检查 Claude settings.local.json 的 UTF-8 语法与对象根。",
            "en": "With an explicit --project root, check UTF-8 syntax and an object root for Claude settings.local.json.",
        },
        "limitation": {
            "zh": "仅在提供 --project 时生成；不合并配置、不读账户、不判定本地覆盖是否生效。",
            "en": "Emitted only with --project; no merge evaluation, account checks, or proof that local overrides apply.",
        },
    },
    "claude.config.project": {
        "target": "claude",
        "evidence_fields": ["layer", "effective_loading", "path", "format", "syntax", "line"],
        "purpose": {
            "zh": "在显式 --project 根下检查 Claude 项目 settings.json 的 UTF-8 语法与对象根。",
            "en": "With an explicit --project root, check UTF-8 syntax and an object root for the Claude project settings.json.",
        },
        "limitation": {
            "zh": "仅在提供 --project 时生成；不向祖先遍历，不计算最终合并配置。",
            "en": "Emitted only with --project; ancestors are not walked and effective merged configuration is not computed.",
        },
    },
    "claude.config.user": {
        "target": "claude",
        "evidence_fields": ["layer", "location_source", "path", "format", "syntax", "line"],
        "purpose": {
            "zh": "检查用户层 Claude settings.json 的 UTF-8 语法与对象根。",
            "en": "Check UTF-8 syntax and an object root for the user-layer Claude settings.json.",
        },
        "limitation": {
            "zh": "文件可缺省；语法通过不等于登录、API 或服务可用；不输出配置键值。",
            "en": "The file may be absent; valid syntax does not establish login, API or service availability; config values are not exported.",
        },
    },
    "claude.dependency": {
        "target": "claude",
        "evidence_fields": ["runtime", "node_required", "scope", "node_found", "node_path_check",
                            "documented_package_engine", "reason", "version", "probe_reason"],
        "purpose": {
            "zh": "观察已识别 Claude 入口所需的运行时线索（原生或 Node）。",
            "en": "Observe runtime clues required by a recognized Claude launcher (native or Node).",
        },
        "limitation": {
            "zh": "只覆盖入口所需运行时；不验证完整依赖树或全部可选功能。",
            "en": "Covers launcher runtime only; the full dependency tree and optional features are not validated.",
        },
    },
    "claude.install": {
        "target": "claude",
        "evidence_fields": ["kind", "publisher_verified"],
        "purpose": {
            "zh": "根据入口布局观察 Claude 安装形式是否可识别。",
            "en": "Observe whether the Claude installation kind is recognizable from the launcher layout.",
        },
        "limitation": {
            "zh": "不是签名或发行方验证；未知形式不等于未安装。",
            "en": "Not signature or publisher verification; an unknown kind does not prove absence of an installation.",
        },
    },
    "claude.path": {
        "target": "claude",
        "evidence_fields": ["entries", "installation_groups", "cmd_path_candidate",
                            "powershell_path_candidate", "resolution_model", "scan_limited"],
        "purpose": {
            "zh": "在 PATH/PATHEXT 限定模型下观察 Claude 入口候选与安装组线索。",
            "en": "Observe Claude PATH/PATHEXT candidates and installation-group clues under the limited resolution model.",
        },
        "limitation": {
            "zh": "不扫描磁盘；不预测别名/函数；受限扫描不能证明未安装或无重复。",
            "en": "No disk search; aliases/functions are outside prediction; a limited scan cannot prove absence or uniqueness.",
        },
    },
    "claude.version": {
        "target": "claude",
        "evidence_fields": ["reason", "returncode", "version", "captured_bytes", "timeout_seconds"],
        "purpose": {
            "zh": "对已识别 Claude 入口做有界 --version 观察。",
            "en": "Perform a bounded --version observation against a recognized Claude launcher.",
        },
        "limitation": {
            "zh": "仅接受短且完整匹配的版本响应；通过只覆盖本次查询，不验证服务或任务。",
            "en": "Only short complete version responses are accepted; a pass covers this query only, not service or task availability.",
        },
    },
    "codex.config.project": {
        "target": "codex",
        "evidence_fields": ["layer", "effective_loading", "path", "format", "syntax", "line"],
        "purpose": {
            "zh": "在显式 --project 根下检查 Codex 项目 config.toml 的 UTF-8 语法与对象根。",
            "en": "With an explicit --project root, check UTF-8 syntax and an object root for the Codex project config.toml.",
        },
        "limitation": {
            "zh": "仅在提供 --project 时生成；不向祖先遍历，不计算最终合并配置。",
            "en": "Emitted only with --project; ancestors are not walked and effective merged configuration is not computed.",
        },
    },
    "codex.config.user": {
        "target": "codex",
        "evidence_fields": ["layer", "location_source", "path", "format", "syntax", "line"],
        "purpose": {
            "zh": "检查用户层 Codex config.toml 的 UTF-8 语法与对象根。",
            "en": "Check UTF-8 syntax and an object root for the user-layer Codex config.toml.",
        },
        "limitation": {
            "zh": "文件可缺省；语法通过不等于配置生效或服务可用；不输出配置键值。",
            "en": "The file may be absent; valid syntax does not establish effective configuration or service availability; config values are not exported.",
        },
    },
    "codex.dependency": {
        "target": "codex",
        "evidence_fields": ["runtime", "node_required", "scope", "node_found", "node_path_check",
                            "documented_package_engine", "reason", "version", "probe_reason"],
        "purpose": {
            "zh": "观察已识别 Codex 入口所需的运行时线索（原生或 Node）。",
            "en": "Observe runtime clues required by a recognized Codex launcher (native or Node).",
        },
        "limitation": {
            "zh": "只覆盖入口所需运行时；不验证完整依赖树或全部可选功能。",
            "en": "Covers launcher runtime only; the full dependency tree and optional features are not validated.",
        },
    },
    "codex.install": {
        "target": "codex",
        "evidence_fields": ["kind", "publisher_verified"],
        "purpose": {
            "zh": "根据入口布局观察 Codex 安装形式是否可识别。",
            "en": "Observe whether the Codex installation kind is recognizable from the launcher layout.",
        },
        "limitation": {
            "zh": "不是签名或发行方验证；未知形式不等于未安装。",
            "en": "Not signature or publisher verification; an unknown kind does not prove absence of an installation.",
        },
    },
    "codex.path": {
        "target": "codex",
        "evidence_fields": ["entries", "installation_groups", "cmd_path_candidate",
                            "powershell_path_candidate", "resolution_model", "scan_limited"],
        "purpose": {
            "zh": "在 PATH/PATHEXT 限定模型下观察 Codex 入口候选与安装组线索。",
            "en": "Observe Codex PATH/PATHEXT candidates and installation-group clues under the limited resolution model.",
        },
        "limitation": {
            "zh": "不扫描磁盘；不预测别名/函数；受限扫描不能证明未安装或无重复。",
            "en": "No disk search; aliases/functions are outside prediction; a limited scan cannot prove absence or uniqueness.",
        },
    },
    "codex.version": {
        "target": "codex",
        "evidence_fields": ["reason", "returncode", "version", "captured_bytes", "timeout_seconds"],
        "purpose": {
            "zh": "对已识别 Codex 入口做有界 --version 观察。",
            "en": "Perform a bounded --version observation against a recognized Codex launcher.",
        },
        "limitation": {
            "zh": "仅接受短且完整匹配的版本响应；通过只覆盖本次查询，不验证服务或任务。",
            "en": "Only short complete version responses are accepted; a pass covers this query only, not service or task availability.",
        },
    },
    "scope.unchecked": {
        "target": "scope",
        "evidence_fields": [],
        "purpose": {
            "zh": "标明账户、认证、聊天、完整配置合并与真实 AI 任务等范围外项未检查。",
            "en": "Record that accounts, authentication, chat history, full configuration merging and real AI tasks remain outside scope.",
        },
        "limitation": {
            "zh": "始终为 skipped 提示；不表示主机健康或其他检查已通过。",
            "en": "Always a skipped scope notice; it does not establish host health or that other checks passed.",
        },
    },
    "system.platform": {
        "target": "system",
        "evidence_fields": ["os", "python", "windows_target"],
        "purpose": {
            "zh": "记录当前解释器所见的操作系统类别与 Python 版本线索。",
            "en": "Record the OS class and Python version clues visible to the current interpreter.",
        },
        "limitation": {
            "zh": "不是硬件清单或补丁审计；Windows 目标标记只反映 os.name。",
            "en": "Not a hardware inventory or patch audit; the Windows-target flag reflects os.name only.",
        },
    },
    "wsl.internal": {
        "target": "wsl",
        "evidence_fields": [],
        "purpose": {
            "zh": "标明 WSL 发行版内部环境始终未检查。",
            "en": "Record that the WSL distribution interior is never inspected.",
        },
        "limitation": {
            "zh": "始终 skipped；不启动发行版，也不把未安装 WSL 判为 AI 工具故障。",
            "en": "Always skipped; distributions are not started and absence of WSL is not treated as an AI tool failure.",
        },
    },
    "wsl.inventory": {
        "target": "wsl",
        "evidence_fields": ["registered_count", "reason"],
        "purpose": {
            "zh": "在 Windows 上观察当前用户 Lxss 注册子键数量线索。",
            "en": "On Windows, observe the current-user Lxss registration subkey count clue.",
        },
        "limitation": {
            "zh": "不列出发行版名称；非 Windows 跳过；不是组件健康证明。",
            "en": "Distribution names are not listed; non-Windows hosts skip; this is not component-health proof.",
        },
    },
    "wsl.launcher": {
        "target": "wsl",
        "evidence_fields": ["present", "component_health", "reason"],
        "purpose": {
            "zh": "观察系统目录下的 WSL 启动器是否存在（原生格式线索）。",
            "en": "Observe whether the system-directory WSL launcher is present (native-format clue).",
        },
        "limitation": {
            "zh": "不检查组件健康；非 Windows 跳过；存在不等于发行版可用。",
            "en": "Component health is not checked; non-Windows hosts skip; presence does not establish a usable distribution.",
        },
    },
    "wsl.running": {
        "target": "wsl",
        "evidence_fields": ["reason", "running_count", "returncode"],
        "purpose": {
            "zh": "在显式 --wsl-list 时只读观察运行中发行版数量。",
            "en": "When --wsl-list is explicit, observe a read-only running-distribution count.",
        },
        "limitation": {
            "zh": "默认不执行；即使加 --no-version 也会在显式允许时查询；不输出名称。",
            "en": "Default is no execution; with explicit permission the list still runs even under --no-version; names are never exported.",
        },
    },
}

assert set(ENTRIES) == IDS


def invalid_catalog(*_):
    raise ValueError("invalid_catalog")


def normalize_ids(ids):
    # CLI passes [] for --catalog with no IDs; empty means the full fixed set.
    if ids is None or ids == [] or ids == ():
        return sorted(IDS)
    if not isinstance(ids, (list, tuple)):
        invalid_catalog()
    if len(ids) > MAX_CATALOG_IDS:
        invalid_catalog()
    selected = []
    seen = set()
    for item in ids:
        if not isinstance(item, str) or item not in IDS:
            invalid_catalog()
        if item in seen:
            continue
        seen.add(item)
        selected.append(item)
    return sorted(selected)


def catalog_entry(check_id, lang):
    meta = ENTRIES[check_id]
    return {
        "id": check_id,
        "target": meta["target"],
        "availability": "project_only" if check_id in PROJECT_ONLY else "always",
        "produced_by_current_version": True,
        "purpose": dict(meta["purpose"]),
        "evidence_fields": list(meta["evidence_fields"]),
        "limitation": dict(meta["limitation"]),
    }


def catalog_report(ids=None, lang="zh"):
    if lang not in NOTICE:
        invalid_catalog()
    checks = [catalog_entry(check_id, lang) for check_id in normalize_ids(ids)]
    return {
        "schema_version": "1.0",
        "report_type": "catalog",
        "doctor_version": __version__,
        "language": lang,
        "checks": checks,
        "status_vocabulary": list(STATES),
        "notice": NOTICE[lang],
    }


def catalog_markdown(report):
    zh = report["language"] == "zh"
    lines = [
        "# Windows AI Doctor — " + ("检查目录" if zh else "Check catalog"),
        "",
        f"v{report['doctor_version']} · schema {report['schema_version']}",
        "",
        report["notice"],
        "",
        ("状态词表：" if zh else "Status vocabulary: ") + ", ".join(report["status_vocabulary"]),
        "",
    ]
    for check in report["checks"]:
        availability = ("仅项目" if zh else "project only") if check["availability"] == "project_only" else ("始终" if zh else "always")
        fields = ", ".join(check["evidence_fields"]) if check["evidence_fields"] else ("（无）" if zh else "(none)")
        lines.extend([
            f"## {check['id']}",
            "",
            ("目标：" if zh else "Target: ") + check["target"],
            "",
            ("可用性：" if zh else "Availability: ") + availability,
            "",
            ("当前版本生成：" if zh else "Produced by current version: ") + ("是" if check["produced_by_current_version"] else "否"),
            "",
            ("用途：" if zh else "Purpose: ") + check["purpose"][report["language"]],
            "",
            ("证据字段：" if zh else "Evidence fields: ") + fields,
            "",
            ("限制：" if zh else "Limitation: ") + check["limitation"][report["language"]],
            "",
        ])
    return "\n".join(lines) + "\n"
