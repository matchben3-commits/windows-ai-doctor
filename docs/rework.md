# dsh 两项复核问题的返工交接

2026-11-19，北京时间。以下保留 gpt 修正与自测的历史记录；后续独立复核和终审见 [发布审查](release-review.md)。

## 两项结果

| 退回问题 | 修正与实际验证 |
| --- | --- |
| 损坏 npm 包装器被包目标版本掩盖 | 取消子串判定，完整匹配已知 `cmd-shim 8.0.0` Node/直接原生模板。残缺、marker-only、前后加命令、目标不符均 unknown，不执行目标。原反例 CMD 实际退出 7，检查器安装/版本 unknown、版本为空 |
| junction 绕过读取边界 | 统一 `checked_stat`，从盘符到叶子逐级 lstat；遇到链接/重解析点立即停止，不触及后代元数据/存在性/内容，不 resolve 包目标。真实 NTFS junction 下配置拒读、工具头未打开；Node、包元数据及 JS/原生目标另有回归 |

路径受限时记录 `path_access=blocked`、`existence_verified=false`，保留优先顺序而不执行或悄悄选择后面的安装。Node 的 blocked/unrecognized 保持未知，只有确定 missing 才判依赖缺失。原生头仍只读 4 字节，不把大程序当作超大配置拒绝。

## 变更文件

| 文件 | 内容 |
| --- | --- |
| `windows_ai_doctor/discovery.py` | 根到叶安全检查；所有命令、Node、包元数据/目标共享；bin 纯词法边界；完整 npm 模板；受限候选与 Node 原因分类 |
| `windows_ai_doctor/npm_shims.py` | 已知标准模板的有限匹配，绝不解释/执行包装器 |
| `windows_ai_doctor/core.py`、`messages.py` | 路径受限的双语解释和存在性字段；Node 受限保持未知；系统 WSL 头检查同样用安全路径 |
| `tests/test_doctor.py` | 原 marker-only 正例改为完整真实黄金文件；原生 npm 正例同样修正 |
| `tests/test_boundaries.py` | 包装正负例、真实 junction 全链路、无后代访问、受限 Node、bin 越界及输出目录回归 |
| `tests/fixtures/`、`THIRD_PARTY_NOTICES.md` | 真实 cmd-shim 生成的六份独立黄金文件、来源及 ISC 许可；运行无需 npm |
| `tests/edge_check.py` | 从 dsh 原反例脚本复制合成场景；输出改到本项目，增加正确性和退出码检查；不改项目外原件 |
| `examples/make_demo.py` | 合成坏入口/junction 的双语样例；修正相对报告目录定位 |
| `tests/host_check.py` | 相对目录先定位；本轮默认不执行 WSL |
| `tests/check_artifacts.py` | 覆盖本轮及既有报告/证据，检查文档、源码、敏感标记，刷新清单 |
| READMEs、rules/privacy/validation、HANDOFF | 同步新边界、实际结果、未覆盖范围与交接命令 |
| `evidence/tests.json`、`rework-edges.json`、`host-review-fixes/`、`examples/review-fixes/` | 本轮新鲜实跑证据与报告 |
| `SHA256SUMS.txt`、`evidence/artifact-check.json` | 交付文件清单与检查结果 |

## 本轮实跑

39 项测试：38 通过、1 跳过（文件符号链接创建权限）、0 失败/错误。真实 junction 测试均通过。原反例脚本、双语示例生成器、本机四次非破坏性检查、交付文件检查均退出 0；示例诊断内部两次退出预期的 1。

本机标准 npm Codex 仍识别为 `0.169.0`，Node `24.19.0`；三个包装入口同组。两份允许配置的字节与父进程环境比较一致。

复现命令、精简结果和报告入口见 [HANDOFF.md](../HANDOFF.md) 与 [validation.md](validation.md)。[原反例结果](../evidence/rework-edges.json) 只包含固定状态、退出码和布尔值。[文件清单](../SHA256SUMS.txt) 覆盖项目交付，自身除外；复跑改写证据后须再刷新清单。

## 限制

完整匹配只覆盖已核对的 npm 形式，其他版本、自定义参数或布局可能未知。当时文件符号链接因权限不足未测，随后 dsh 授权单项补测已通过；真实 Claude 发行包、WSL 发行版、其他系统/架构及 wheel 安装仍未实测。保守链接拒绝不等于硬链接、并发恶意替换、签名验证或第三方程序网络沙箱。公开包保留 `review-fixes` 修订证据，首轮旧证据保留在本地原快照。
