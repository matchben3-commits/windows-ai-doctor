# Windows AI Doctor — 检查目录

v0.6.0 · schema 1.0

本目录列出当前版本会生成的稳定检查 ID 及固定说明；不表示检查一定执行、环境健康，目录本身也不能验证安装。不读取输入文件，不运行诊断，不访问环境、注册表、网络或包内路径。

状态词表：pass, warn, error, unknown, skipped

## claude.config.local

目标：claude

可用性：仅项目

当前版本生成：是

用途：在显式 --project 根下检查 Claude settings.local.json 的 UTF-8 语法与对象根。

证据字段：layer, effective_loading, path, format, syntax, line

限制：仅在提供 --project 时生成；不合并配置、不读账户、不判定本地覆盖是否生效。

## claude.config.project

目标：claude

可用性：仅项目

当前版本生成：是

用途：在显式 --project 根下检查 Claude 项目 settings.json 的 UTF-8 语法与对象根。

证据字段：layer, effective_loading, path, format, syntax, line

限制：仅在提供 --project 时生成；不向祖先遍历，不计算最终合并配置。

## claude.config.user

目标：claude

可用性：始终

当前版本生成：是

用途：检查用户层 Claude settings.json 的 UTF-8 语法与对象根。

证据字段：layer, location_source, path, format, syntax, line

限制：文件可缺省；语法通过不等于登录、API 或服务可用；不输出配置键值。

## claude.dependency

目标：claude

可用性：始终

当前版本生成：是

用途：观察已识别 Claude 入口所需的运行时线索（原生或 Node）。

证据字段：runtime, node_required, scope, node_found, node_path_check, documented_package_engine, reason, version, probe_reason

限制：只覆盖入口所需运行时；不验证完整依赖树或全部可选功能。

## claude.install

目标：claude

可用性：始终

当前版本生成：是

用途：根据入口布局观察 Claude 安装形式是否可识别。

证据字段：kind, publisher_verified

限制：不是签名或发行方验证；未知形式不等于未安装。

## claude.path

目标：claude

可用性：始终

当前版本生成：是

用途：在 PATH/PATHEXT 限定模型下观察 Claude 入口候选与安装组线索。

证据字段：entries, installation_groups, cmd_path_candidate, powershell_path_candidate, resolution_model, scan_limited

限制：不扫描磁盘；不预测别名/函数；受限扫描不能证明未安装或无重复。

## claude.version

目标：claude

可用性：始终

当前版本生成：是

用途：对已识别 Claude 入口做有界 --version 观察。

证据字段：reason, returncode, version, captured_bytes, timeout_seconds

限制：仅接受短且完整匹配的版本响应；通过只覆盖本次查询，不验证服务或任务。

## codex.config.project

目标：codex

可用性：仅项目

当前版本生成：是

用途：在显式 --project 根下检查 Codex 项目 config.toml 的 UTF-8 语法与对象根。

证据字段：layer, effective_loading, path, format, syntax, line

限制：仅在提供 --project 时生成；不向祖先遍历，不计算最终合并配置。

## codex.config.user

目标：codex

可用性：始终

当前版本生成：是

用途：检查用户层 Codex config.toml 的 UTF-8 语法与对象根。

证据字段：layer, location_source, path, format, syntax, line

限制：文件可缺省；语法通过不等于配置生效或服务可用；不输出配置键值。

## codex.dependency

目标：codex

可用性：始终

当前版本生成：是

用途：观察已识别 Codex 入口所需的运行时线索（原生或 Node）。

证据字段：runtime, node_required, scope, node_found, node_path_check, documented_package_engine, reason, version, probe_reason

限制：只覆盖入口所需运行时；不验证完整依赖树或全部可选功能。

## codex.install

目标：codex

可用性：始终

当前版本生成：是

用途：根据入口布局观察 Codex 安装形式是否可识别。

证据字段：kind, publisher_verified

限制：不是签名或发行方验证；未知形式不等于未安装。

## codex.path

目标：codex

可用性：始终

当前版本生成：是

用途：在 PATH/PATHEXT 限定模型下观察 Codex 入口候选与安装组线索。

证据字段：entries, installation_groups, cmd_path_candidate, powershell_path_candidate, resolution_model, scan_limited

限制：不扫描磁盘；不预测别名/函数；受限扫描不能证明未安装或无重复。

## codex.version

目标：codex

可用性：始终

当前版本生成：是

用途：对已识别 Codex 入口做有界 --version 观察。

证据字段：reason, returncode, version, captured_bytes, timeout_seconds

限制：仅接受短且完整匹配的版本响应；通过只覆盖本次查询，不验证服务或任务。

## scope.unchecked

目标：scope

可用性：始终

当前版本生成：是

用途：标明账户、认证、聊天、完整配置合并与真实 AI 任务等范围外项未检查。

证据字段：（无）

限制：始终为 skipped 提示；不表示主机健康或其他检查已通过。

## system.platform

目标：system

可用性：始终

当前版本生成：是

用途：记录当前解释器所见的操作系统类别与 Python 版本线索。

证据字段：os, python, windows_target

限制：不是硬件清单或补丁审计；Windows 目标标记只反映 os.name。

## wsl.internal

目标：wsl

可用性：始终

当前版本生成：是

用途：标明 WSL 发行版内部环境始终未检查。

证据字段：（无）

限制：始终 skipped；不启动发行版，也不把未安装 WSL 判为 AI 工具故障。

## wsl.inventory

目标：wsl

可用性：始终

当前版本生成：是

用途：在 Windows 上观察当前用户 Lxss 注册子键数量线索。

证据字段：registered_count, reason

限制：不列出发行版名称；非 Windows 跳过；不是组件健康证明。

## wsl.launcher

目标：wsl

可用性：始终

当前版本生成：是

用途：观察系统目录下的 WSL 启动器是否存在（原生格式线索）。

证据字段：present, component_health, reason

限制：不检查组件健康；非 Windows 跳过；存在不等于发行版可用。

## wsl.running

目标：wsl

可用性：始终

当前版本生成：是

用途：在显式 --wsl-list 时只读观察运行中发行版数量。

证据字段：reason, running_count, returncode

限制：默认不执行；即使加 --no-version 也会在显式允许时查询；不输出名称。

