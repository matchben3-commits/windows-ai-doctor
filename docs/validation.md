> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# 实跑验收记录 / Validation

## v0.2 本轮自测：2026-11-19

本节保留 2026-11-19 实现者 gpt 的自测记录：Windows build 26200，64 位 Python 3.12.10。2026-11-20 独立复核和终审范围见 [v0.2 发布审查](release-review-v0.2.md)；不将历史记录冒充当日新测试。

| 验证 | 本次结果 | 机器证据 |
| --- | --- | --- |
| 整套测试 | 56 项；54 通过、2 跳过、0 失败、0 错误，退出 0 | [逐项记录](../evidence/v02-tests.json) |
| 原 39 项回归 | 本次 38 通过、1 跳过；位于同一套件的 test_doctor/test_boundaries | 同上 |
| 新增 17 项 | 本次 16 通过、1 跳过；输入边界、比较语义/隐私、参数冲突、HTML转义、排障、导出失败/中断、真实 junction/文件链接 | 同上 |
| 单独授权补测 | 两项真实文件符号链接 2 通过、0 跳过、退出 0；源代码前后哈希一致 | [测试](../evidence/v02-authorized-links.json)、[进程退出码](../evidence/v02-authorized-process.json) |
| 本机中英正常/禁网 API | 四次退出 0，全部导出 MD/JSON/HTML；配置字节和父环境未改 | [主机记录](../evidence/v02-host/runs.json) |
| 实际 HTML 浏览器 | 中文桌面、390px 内容视口、转义长文本、英文对比均检查并截图 | [显示核验](html-validation.md) |
| wheel 和 sdist | sdist → wheel 构建；分别在干净临时 venv 安装、运行控制台命令、中英文三格式和对比、卸载成功 | [构建安装记录](../evidence/build-install.json) |
| Windows CI | 定义已提供，Python 3.11/3.14 + Node 24；托管结果待发布阶段验证 | [.github/workflows/windows.yml](../.github/workflows/windows.yml) |

普通进程两项跳过都因不能创建真实文件符号链接（原配置项、新报告输入项）。依据用户明确授权，在临时管理员进程独立补测两项，均通过。不能合并声称一次完整 56 通过；以前单项授权记录也保留原时间归属。

新测试实际验证：禁止比较模式实例化 Doctor/运行子进程/网络/注册表；嵌入路径不访问；相同观察但语言/时间/代号不同无变化；数字版本、安装组、扫描限制和新增/移除/状态变化可见；error 转 unknown/skipped 或检查消失不报修复；拒绝畸形/重复/过深/超大/非有限/未知 schema 和 ID；任意输入文案及秘密标记不导出；真实 junction 不访问后代；导出冲突保留已有文件，部分失败/中断清理本次文件。原 npm 损坏包装器和进程树清理回归保留。

当前主机仍识别 Codex 0.169.0，Claude 无 PATH 入口。未验证真实 Claude、WSL 内部/运行发行版、其他 Windows/Python 组合、POSIX、物理断网或第三方进程防火墙隔离。仅禁止 Python 网络 API 的运行不等于物理断网；实际浏览器报告的被阻止 Google 请求见显示核验记录。

This iteration is implementer validation, not independent review. All 56 distinct tests have pass evidence across an ordinary full run and a separate two-case authorized supplement; they did not all pass in one full run. Both distributions are actually installed, exercised and uninstalled in temporary clean environments. Hosted CI, other Python/OS versions, real Claude and WSL internals remain unverified.

## v0.1 历史自测（下文保留原始归属）

日期：2026-11-19（北京时间）。以下为 gpt 返工时的历史自测记录。随后 dsh 独立复核与 MausBot 终审结果见 [发布审查](release-review.md)，历史测试数量保留原归属。具体变更见 [返工说明](rework.md)。

## 环境与结果

- Windows NT `10.0`、build `26200`；Python `3.12.10`、64 位。
- 测试：**39 项，38 PASS、1 SKIP、0 FAIL、0 ERROR**，运行器退出 `0`。逐项结果及精确时间见 [tests.json](../evidence/tests.json)。
- Node 已存在，合成 npm JS 入口测试实际调用 Node；原生 PE 样例用本机已有 C# 编译器临时生成，未安装工具。
- 本机检测：Codex CLI `0.169.0`、Node `24.19.0`；同一 npm 安装的 `.cmd`、`.ps1`、无扩展包装器合并为 1 组。当前 PATH 未发现 Claude CLI；不声称整机无 Claude。
- 用户层 Codex TOML 与 Claude settings JSON 的语法通过。WSL 系统启动器可见，当前用户注册键不存在；返工本机检查不执行 WSL，运行状态及内部均未检查。
- 干净临时工作目录中的中文/英文普通试跑均退出 `0`；启用禁止 Python 网络操作的中文/英文基础检查也均退出 `0`。四次均导出 MD/JSON。
- 本机试跑前后，只比较允许读取的两种用户配置文件字节与父进程环境：均保持一致；比较值/哈希没有导出。该比较不构成对整个操作系统副作用的审计。

上述主机记录、时间及各运行退出码见 [host-review-fixes/runs.json](../evidence/host-review-fixes/runs.json)。

另运行 `python tests/edge_check.py`（退出 0）：复用独立复核脚本的两项合成反例，未改动项目外复核原件；精简结果见 [rework-edges.json](../evidence/rework-edges.json)。损坏包装器实际退出 7，检查器为 unknown；junction 内工具头没有打开。

另运行 `python tests/check_artifacts.py`（退出 0）：Python 源文件在内存编译、生成报告/运行记录、全部本地 Markdown 链接及报告敏感标记检查通过，精确数量见 [artifact-check.json](../evidence/artifact-check.json)。[SHA256SUMS.txt](../SHA256SUMS.txt) 可用于核对交接文件快照；任何复跑改写证据后，应再次运行该检查器刷新清单。

## 复现命令与本轮实际退出码

在项目根运行：

```powershell
python tests/run_tests.py --evidence evidence/tests-rerun.json
# 本轮等效命令（evidence/tests.json）：退出 0

python examples/make_demo.py .\reports\demo-new
# 本轮目标 examples/review-fixes：生成器退出 0；两个诊断子命令各退出 1（故意坏配置）

python tests/host_check.py .\reports\host-rerun
# 本轮目标 evidence/host-review-fixes：运行器退出 0；内部四次诊断均退出 0

python tests/offline_check.py --lang zh --format json
python tests/offline_check.py --lang en --format json
# 两种语言的独立进程检查均已运行，退出 0
```

`host_check.py` 内部从全新临时目录执行绝对路径入口，与 README 的“从任意干净目录启动”方式一致。它不在干净目录安装包或写配置。复跑请选择新报告目录；现有报告被拒绝覆盖是预期行为。

## 任务书场景对应证据

| 必须场景 | 已运行的证据与判断 |
| --- | --- |
| 两种工具未安装 | `test_missing_both_cli_and_bilingual_status_ids`：临时空 PATH，真实 CLI 导出两种语言，未发现入口为提醒，退出 0 |
| 中文与空格路径 | `test_real_npm_query_in_chinese_space_directory_and_wrapper_dedup`：临时 npm JS 入口真实查询 `1.2.3`；`test_native_cli_with_spaces_does_not_require_node`：原生合成程序同样可查询 |
| 多 PATH 候选、等价包装器 | `test_distinct_installations_shadow_in_path_order`：两个合成包分两组且优先顺序保留；单包三个包装器一组，不报警冲突 |
| 坏配置、继续其余检查 | `test_custom_home_overrides_invalid_default_and_both_config_errors_continue`：JSON/TOML 都损坏后真实 CLI 退出 1，仍包含 WSL 项；严格 JSON、编码和大小限制另测 |
| 自定义目录与未知安装 | 上述覆盖测试验证两个官方环境变量优先级；`test_relative_override_not_silently_replaced` 不对无效覆盖悄悄回退；`test_unknown_wrapper_is_never_executed` 验证未知入口无执行 |
| 按入口区分依赖 | Codex npm JS 缺 Node/版本不足为异常；Claude 原生及 npm-native 合成入口无 Node 仍成功；不将安装时 Node 要求误作原生运行时要求 |
| 超时、非零退出、输出过长 | `test_timeout_and_nonzero_continue_reports` 真实挂起脚本/退出 7；`test_oversized_cli_output_still_completes_other_checks` 真实超长输出；均有界结束并保留其余报告 |
| 临时进程清理 | `test_runner_caps_output_and_terminates_process_tree` 实际创建父子进程，超时后检查子进程已退出；`test_runner_child_exit_also_removes_descendants` 也检查父正常退出后的子进程终止 |
| WSL 无启动器、未运行、不可见 | `test_wsl_default_never_executes_and_synthetic_visibility`：注入无启动器/无可见注册、注册不可读；合成列表程序实际返回空列表，运行数量为 0；内部始终未检查。真实主机仅覆盖启动器可见但列表失败 |
| 敏感令牌、个人路径、带凭据 URL | `test_sensitive_markers_never_reach_json_markdown_stdout_stderr`：真实版本子进程输出假令牌/用户名/密码/URL，配置也包含假值；两语 MD/JSON/stdout/stderr 均无标记；CLI 参数与导出异常另测 |
| 离线、中英一致 | `test_real_cli_with_network_audit_denied` 真实独立 CLI 的 Python 网络操作被禁止仍导出；中英文 ID/状态一致另测；主机两语同样执行此检查 |
| 认证与历史不读取 | `test_project_layer_syntax_and_no_auth_or_history_reads` 放置合成认证/历史文件并跟踪打开动作，没有访问这些文件 |
| npm 损坏包装器 | `test_broken_marker_wrapper_exit7_never_queries_package`、`test_all_wrapper_variants_reject_marker_only_and_added_commands`：完整标准包装器之外不执行，不借包目标报版本通过；六份真实生成的黄金文件独立验证标准形式 |
| 链接安全 | `test_real_junction_*` 实际创建 NTFS junction，跟踪并禁止链接后代的 `lstat/stat/is_file/open/resolve`，覆盖配置、工具头、Node、包元数据与 JS/原生目标；真实文件符号链接仍因权限不足 SKIP |
| 相对交付目录 | `test_demo_relative_destination_survives_clean_child_cwd`、`test_host_relative_destination_and_default_no_wsl_execution`：相对目录在调用方定位，不落入子进程临时目录；本机检查默认不执行 WSL |

## 样例报告

- 合成中文：[Markdown](../examples/review-fixes/zh/report.zh.md)、[JSON](../examples/review-fixes/zh/report.zh.json)。
- 合成英文：[Markdown](../examples/review-fixes/en/report.en.md)、[JSON](../examples/review-fixes/en/report.en.json)。
- [合成运行退出码](../examples/review-fixes/runs.json)：两次诊断均为预期退出 `1`。
- 主机普通试跑：[中文](../evidence/host-review-fixes/normal/zh/report.zh.md)、[英文](../evidence/host-review-fixes/normal/en/report.en.md)，同目录各附 JSON。
- 禁止 Python 网络操作：[中文](../evidence/host-review-fixes/offline-audit/zh/report.zh.md)、[英文](../evidence/host-review-fixes/offline-audit/en/report.en.md)，同目录各附 JSON。

公开示例仅来自临时合成配置；包含故意坏配置的状态是教学用途。真实主机报告没有配置值、真实路径或账户信息。

## 明确未实测或不覆盖

1. **真实 Claude 发行包、Codex 原生/WinGet/Scoop 安装**：合成 PE/包布局验证的是机制，不能代替各发行安装兼容测试。
2. **真实 WSL 已安装/停止/运行的发行版**：没有启动它们来造场景；本机列表失败如实记未知。没有检查 WSL 内部路径、配置或服务。
3. **硬链接与并发替换**：不属于完整安全边界。文件符号链接在 gpt 历史自测中权限不足跳过，随后已由 dsh 授权单项补测通过；见 [补测证据](../evidence/review-dsh/symlink-elevated.json)。
4. **物理断网、第三方进程网络隔离**：未关网卡、未改防火墙；验证的是检查器在禁止 Python 网络 API 时可完成基础检查。默认版本程序不是网络沙箱。
5. **Python 3.11、Windows 10/ARM64、POSIX、受限组织权限**：本轮只实测上述 Windows/Python 3.12 64 位主机；不推断其他矩阵已通过。
6. **完整配置生效性**：不核验 schema 键名、配置档、祖先项目层、管理策略或认证。Claude 在配置/管理层中二次设置配置目录的情况未计算；仅用当前进程变量定位。
7. **交互终端解析**：不复现 CWD、别名、函数、执行策略；报告中的 PowerShell 优先候选是 PATH 预测。只执行首个 CMD 候选，不执行所有重复入口。
8. **Python wheel/pip 安装与代码托管 CI**：元数据存在但未构建安装；源码直接运行已实测。代码托管 CI 未执行；没有设置监控/定时任务。发布状态以仓库和版本页面为准。

## 交付清理

临时故障、C# 源码/可执行文件、junction 及子进程在各测试结束清理；不留 `__pycache__` 或依赖安装。公开包保留返工后 `host-review-fixes` / `examples/review-fixes`，首轮旧样例仅留在本地原开发快照中。没有创建自动化任务。
