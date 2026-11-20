"""Fixed bilingual advice selected from observations, never from config values."""

# phenomenon, basis, manual steps, limitation (Chinese / English)
ADVICE = {
    "missing": (
        ("PATH 未发现可选入口。", "本次限定范围中没有选中的 CMD/PATHEXT 候选。", ["在实际使用的 PowerShell 中运行 Get-Command codex,claude -All，核对入口。", "按官方安装说明人工检查安装位置；调整后打开新终端再体检。"], "不扫描磁盘；未发现不等于未安装。"),
        ("No selectable PATH entry was found.", "No CMD/PATHEXT candidate was selected in this scan.", ["Run Get-Command codex,claude -All in your actual PowerShell to inspect entries.", "Manually review installation locations using the official setup guide; open a new terminal before rechecking."], "No disk search is performed; absence from PATH does not prove absence of installation.")),
    "multiple": (
        ("发现多个安装组。", "installation_groups 大于 1；同组包装器已合并。", ["运行 Get-Command codex,claude -All，确认日常终端实际选择。", "人工核对保留的安装方式与 PATH 顺序，再运行体检。"], "多个安装组只是线索，不能据此断定冲突；别名和函数未纳入预测。"),
        ("Multiple installation groups were observed.", "installation_groups exceeds 1; wrappers in the same group are combined.", ["Run Get-Command codex,claude -All to inspect your actual shell selection.", "Manually review intended installations and PATH order, then rerun diagnostics."], "Multiple groups do not establish a conflict; aliases and functions are outside the prediction.")),
    "blocked": (
        ("优先入口受读取限制。", "选中候选的 path_access 为 blocked，存在性未确认。", ["人工检查预期入口是否经过链接、重解析点或非固定本地盘。", "运行 Get-Command codex,claude -All 核对终端选择；保留本次无法判断结论。"], "不会沿链接读取，也不会跳过受限优先入口执行后续程序。"),
        ("The preferred entry is restricted.", "The selected candidate has path_access=blocked; existence is unverified.", ["Manually inspect whether the intended entry uses links, reparse points or a non-fixed drive.", "Run Get-Command codex,claude -All to inspect shell selection; retain the unknown result."], "Links are not followed and a restricted preferred entry is not bypassed to execute a later program.")),
    "limited": (
        ("扫描范围受限。", "scan_limited 为 true，或存在受限候选。", ["运行 Get-Command codex,claude -All，人工核对未能覆盖的入口。", "在范围一致时重新体检。"], "候选列表不完整，不能证明未安装或不存在重复安装。"),
        ("The scan is limited.", "scan_limited is true or a candidate is restricted.", ["Run Get-Command codex,claude -All and manually review entries outside the scan.", "Repeat diagnostics with a consistent scope."], "An incomplete candidate list cannot prove absence or uniqueness of installations.")),
    "wrapper": (
        ("入口形式未识别。", "安装形式为 unknown；未满足原生格式或完整 npm 模板。", ["运行 Get-Command codex,claude -All，人工核对安装来源。", "对照官方安装说明检查包装器；不要因目标文件存在就判定入口正常。"], "自定义或新版包装器也可能未知；本工具不通过 shell 执行包装器。"),
        ("The entry format is unrecognized.", "The installation kind is unknown; native format or a complete npm template was not confirmed.", ["Run Get-Command codex,claude -All and manually review installation provenance.", "Compare the wrapper with official setup guidance; an existing target alone does not validate its launcher."], "Custom or newer wrappers can also be unknown; wrappers are never executed through a shell.")),
    "node_missing": (
        ("已识别的 npm JS 入口缺少可用 Node 候选。", "runtime=node 且 node_path_check=missing；仅在此范围确认缺少。", ["运行 Get-Command node -All 与 node --version，人工核对运行环境。", "按对应工具官方说明人工处理依赖，再次体检。"], "只适用于已识别的 JS 入口；原生入口不通用要求 Node。"),
        ("A recognized npm JS entry has no Node candidate in scope.", "runtime=node and node_path_check=missing confirm absence only within the inspected scope.", ["Run Get-Command node -All and node --version to manually inspect the runtime.", "Use the tool's official setup guide to address dependencies manually, then recheck."], "This applies only to a recognized JS entry; native entries do not universally require Node.")),
    "node_old": (
        ("Node 版本低于本地包声明的最低版本。", "已解析版本与简单 >= 引擎范围比较失败。", ["运行 node --version 核对日常终端版本。", "按官方说明人工选择兼容运行时，再次体检。"], "仅解释简单最低版本范围，不验证完整依赖或所有可选功能。"),
        ("Node is below the minimum declared by the local package.", "A parsed version failed comparison with a simple >= engine range.", ["Run node --version to inspect the version in your daily shell.", "Manually choose a compatible runtime using official guidance, then recheck."], "Only simple minimum ranges are interpreted; complete dependencies and optional features are not validated.")),
    "node_unknown": (
        ("Node 依赖无法判断。", "入口或 Node 路径、版本响应、引擎范围未能完整确认。", ["运行 Get-Command node -All 核对终端入口。", "人工检查受限路径或本地包引擎范围，再体检。"], "路径受限、探测关闭或响应未知均不等于未安装。"),
        ("The Node dependency cannot be determined.", "The entry, Node path, version response or engine range could not be fully confirmed.", ["Run Get-Command node -All to inspect shell entries.", "Manually review restricted paths or the package engine range, then recheck."], "Restricted paths, disabled probes and unknown responses do not establish that Node is missing.")),
    "timeout": (
        ("版本查询超时。", "reason=timeout；进程树已按有界策略清理。", ["人工确认安装来源后，在自己的终端运行 codex --version 或 claude --version。", "核对等待时间与终端表现，再选择是否重新体检。"], "超时不能定位网络、权限或程序内部原因；不代表服务一定故障。"),
        ("The version query timed out.", "reason=timeout; the bounded process-tree cleanup policy was applied.", ["After manually confirming installation provenance, run codex --version or claude --version in your terminal.", "Review elapsed time and terminal behavior before repeating diagnostics."], "Timeout alone does not identify a network, permission or internal failure, or establish service failure.")),
    "nonzero": (
        ("版本查询返回非零退出码。", "reason=nonzero_exit；原始输出未保留。", ["人工确认安装来源后运行 codex --version 或 claude --version。", "在本地查看其提示；分享前先删除凭据和路径。"], "只保留退出码，不推断账户、网络或具体故障。"),
        ("The version query returned a nonzero exit code.", "reason=nonzero_exit; raw output was discarded.", ["After manually confirming provenance, run codex --version or claude --version.", "Review its message locally and remove credentials and paths before sharing."], "Only the exit code is retained; account, network and specific causes are not inferred.")),
    "version": (
        ("版本观察有范围限制。", "仅接受短且完整匹配的版本响应；禁用或未知响应不算通过。", ["人工确认入口后运行 codex --version 或 claude --version。"], "版本通过仅表示本次版本查询通过，不验证服务、登录或实际任务。"),
        ("Version observations have a limited scope.", "Only short complete version responses are accepted; disabled or unknown responses do not pass.", ["After manually confirming the entry, run codex --version or claude --version."], "A pass covers this version query only, not service, login or task availability.")),
    "config_bad": (
        ("配置语法或根结构无效。", "syntax 为 invalid 或 invalid_structure；不保留配置内容。", ["在本地编辑器查看对应配置；若报告有行号，先检查该行附近。", "按官方配置说明人工修正并保存 UTF-8，然后重新体检。"], "只检查单文件语法和对象根；不计算配置合并或账户有效性。"),
        ("Configuration syntax or root structure is invalid.", "syntax is invalid or invalid_structure; configuration content is discarded.", ["Inspect the corresponding file locally; use the reported line number if present.", "Manually correct it using official configuration guidance, save as UTF-8 and rerun diagnostics."], "Only per-file syntax and an object root are checked, not configuration merging or account validity.")),
    "config": (
        ("配置只做有限语法检查。", "syntax 区分 valid、absent、unreadable 和 safety_limit 等观察。", ["人工核对本次用户层或显式项目层是否是预期检查范围。", "需要修改时先参照官方配置说明，再运行体检。"], "文件可缺省；语法通过不等于配置生效或服务可用；受限文件不继续读取。"),
        ("Configuration checks cover syntax only.", "syntax distinguishes valid, absent, unreadable, safety_limit and other observations.", ["Manually confirm that the user or explicit project layer is the intended scope.", "Consult official configuration guidance before making changes, then recheck."], "Files can be optional; valid syntax does not establish effective configuration or service availability; restricted files are not read further.")),
    "wsl": (
        ("WSL 内部环境未检查。", "Windows 启动器和注册数量仅是外部观察；内部检查始终跳过。", ["若实际在 WSL 内使用工具，请在自己选定的发行版内单独核对安装。", "仅需查看 Windows 注册列表时，可人工运行 wsl --list --quiet。"], "本工具不启动发行版，也不把未安装 WSL 判为 AI 工具故障。"),
        ("The WSL internal environment is not checked.", "Windows launcher and registration counts are external observations; internal checks always remain skipped.", ["If you use tools inside WSL, inspect installation separately inside the distribution you select yourself.", "To inspect the Windows registration list only, manually run wsl --list --quiet."], "This tool does not start distributions or treat absence of WSL as an AI tool failure.")),
    "scope": (
        ("此项仅反映限定范围内的观察。", "报告保留具体检查状态与证据。", ["先处理异常，再核对提醒和无法判断项；手动调整后按相同范围重新体检。"], "不检查账户、认证、聊天记录、完整配置合并或实际 AI 任务。"),
        ("This is an observation within a limited scope.", "The report retains the check's specific status and evidence.", ["Review errors first, then warnings and unknown results; after manual changes recheck with the same scope."], "Accounts, authentication, chat history, complete configuration merging and real AI tasks are not checked.")),
}


def select(f):
    id, e = f["id"], f["evidence"]
    if id.endswith(".path"):
        selected = e.get("cmd_path_candidate")
        if any(v.get("path") == selected and v.get("path_access") == "blocked" for v in e.get("entries", [])):
            return "blocked"
        if e.get("scan_limited") or any(v.get("path_access") == "blocked" for v in e.get("entries", [])):
            return "limited"
        if not selected:
            return "missing"
        if e.get("installation_groups", 0) > 1:
            return "multiple"
    if id.endswith(".install") and e.get("kind") == "unknown":
        return "wrapper"
    if id.endswith(".dependency") and f["status"] != "pass":
        if e.get("runtime") == "node" and e.get("node_path_check") == "missing":
            return "node_missing"
        return "node_old" if f["status"] == "error" else "node_unknown"
    if id.endswith(".version"):
        return e["reason"] if e.get("reason") in ("timeout", "nonzero") else "nonzero" if e.get("reason") == "nonzero_exit" else "version"
    if ".config." in id:
        return "config_bad" if e.get("syntax") in ("invalid", "invalid_structure") else "config"
    if id.startswith("wsl."):
        return "wsl"
    return "scope"


def guidance(finding, lang):
    key = select(finding)
    phenomenon, basis, steps, limitation = ADVICE[key][0 if lang == "zh" else 1]
    tool = finding["id"].split(".")[0]
    if tool == "wsl":
        source = "https://learn.microsoft.com/en-us/windows/wsl/basic-commands"
    elif tool == "claude":
        source = "https://code.claude.com/docs/en/settings" if ".config." in finding["id"] else "https://code.claude.com/docs/en/setup"
    elif tool == "codex":
        source = "https://developers.openai.com/codex/config-basic/" if ".config." in finding["id"] else "https://github.com/openai/codex/blob/main/README.md"
    else:
        source = None
    steps = list(steps)
    if source:
        steps.append(("官方说明（手动查看）：" if lang == "zh" else "Official guidance (open manually): ") + source)
    return {"code": key, "phenomenon": phenomenon, "basis": basis,
            "steps": steps, "limitation": limitation}


def priorities(findings):
    return [f["id"] for state in ("error", "warn", "unknown") for f in findings if f["status"] == state]
