"""Static bilingual finding text; untrusted strings never become prose."""
TEXT = {
    "platform": ("当前操作系统；仅检查当前进程可见环境。", "Current OS; only the current process environment is inspected."),
    "paths": ("按 PATH 顺序列出入口；同一安装的包装入口合并计数。", "Entries are ordered by PATH; wrappers for one installation share a group."),
    "paths_blocked": ("部分 PATH 候选受链接或访问限制，存在性未确认；保留原顺序且不执行。", "Some PATH candidates are blocked by links or access limits; existence is unverified, order is retained and they are not executed."),
    "missing": ("当前 PATH 未发现可调用入口；不等于机器上完全未安装。", "No callable entry in the current PATH; this does not prove the tool is absent from the machine."),
    "duplicate": ("发现多个安装候选；优先入口可能遮蔽后续入口，不能据此判定损坏。", "Multiple installation candidates; earlier entries may shadow later ones. This does not prove a fault."),
    "install": ("安装方式仅由本地文件结构推断；未知入口不执行。", "Installation type is inferred from local layout; unknown entries are not executed."),
    "version": ("仅接受完整匹配的版本响应；未保留原始输出。", "Only a complete matching version response is accepted; raw output is discarded."),
    "dependency": ("只检查所识别入口的运行时依赖；原生程序不统一要求 Node.js。", "Runtime checks depend on the identified entry; native programs do not universally require Node.js."),
    "config": ("仅检查指定配置文件的语法；不验证登录、模型服务、键名或最终生效值。", "Syntax only for the named configuration file; login, model service, keys and effective values are not validated."),
    "config_bad": ("配置语法或根结构不符合要求；没有输出内容或解析异常正文。", "Configuration syntax or root structure is invalid; content and parser exception text are withheld."),
    "config_missing": ("未发现此可选配置文件；缺省配置不是故障。", "This optional configuration file is absent; defaults are not a fault."),
    "config_unreadable": ("配置未读取：权限、链接、非本地路径、大小或编码限制。", "Configuration was not read: permissions, links, nonlocal path, size or encoding limit."),
    "wsl_launcher": ("只检查系统 WSL 启动器；存在不等于组件或发行版可用。", "Only the system WSL launcher is checked; presence does not prove component or distribution availability."),
    "wsl_inventory": ("只观察当前用户已注册发行版数量，不读取内部文件。", "Observe only the count of registered distributions for this user; no internal files are read."),
    "wsl_state": ("运行状态只由显式启用的只读列表查询判断；默认不执行 WSL。", "Running state comes only from an explicitly enabled read-only list query; WSL is not executed by default."),
    "wsl_inside": ("未检查发行版内部命令或配置；没有启动发行版。", "Commands and configuration inside distributions were not inspected; no distribution was launched."),
    "scope": ("未计算合并配置；项目祖先、配置档、管理策略、别名与终端执行策略不在首版范围。", "Merged configuration is not computed; project ancestors, profiles, managed policy, aliases and shell execution policy are outside v0.1 scope."),
    "review_path": ("在原终端手动查看 Get-Command codex,claude -All 及 where.exe codex / where.exe claude；本报告的路径代号不含原路径。", "In the original terminal inspect Get-Command codex,claude -All and where.exe codex / where.exe claude; report path references contain no original paths."),
    "review_version": ("先确认优先入口可信，再在终端手动查询 --version；不要依据此项自动升级。", "First verify the preferred entry is trusted, then manually query --version; do not auto-upgrade based on this check."),
    "review_config": ("在本机编辑器中复核对应层的配置语法；不要将包含密钥的全文上传。", "Review syntax at the corresponding configuration layer in a local editor; do not upload the full file containing secrets."),
    "review_wsl": ("如需确认，手动运行 wsl.exe --list --verbose；Windows 与 WSL 需要分别体检。", "If needed, manually run wsl.exe --list --verbose; diagnose Windows and WSL separately."),
    "review_scope": ("请在工具官方文档及自身状态页面核实实际生效环境。", "Verify the effective environment in official documentation and the tool's own status view."),
}


def message(key, lang):
    return TEXT[key][0 if lang == "zh" else 1]
