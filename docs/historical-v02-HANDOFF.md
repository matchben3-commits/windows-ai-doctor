> 历史快照：这是 v0.2.0 开发交接，原相对链接从项目根目录解释；其中本轮、待发布和验证状态仅指当时，不代表第三版。

# v0.2.0 开发交接 / Development handoff

本轮三项功能已实现：离线单文件 HTML；两份 JSON 离线对比；按证据选择的中英文排障。保留原 CLI、稳定检查编号、默认 MD+JSON、npm 完整模板及逐级拒绝链接策略。开发阶段未发布；2026-11-20 后续独立复核、终审和正式发布状态见 [v0.2 发布审查](../docs/release-review-v0.2.md) 与版本页。

## 本轮证据

- [测试逐项记录](../evidence/v02-tests.json)：56 项，54 通过、2 跳过、0 失败/错误，退出 0。原 39 项是本次套件中的 38 通过、1 跳过；新增 17 项为 16 通过、1 跳过。
- [用户授权的独立两项补测](../evidence/v02-authorized-links.json)及[真实进程退出码](../evidence/v02-authorized-process.json)：配置文件链接和报告输入链接均通过，2 通过、0 跳过、退出 0。不是一次完整 56 通过。补测中记录的核心源文件哈希保持一致。
- [四次本机检查](../evidence/v02-host/runs.json)：中英文常规和禁止 Python 网络 API 均退出 0；允许读取的用户配置字节及父环境未变。Codex 0.169.0；未执行 WSL。
- [原始两项反例本轮复跑](../evidence/v02-edges.json)：损坏包装器实际退出 7、doctor unknown；真实 junction 未读取后代，脚本退出 0。
- [实际 HTML 显示核验](../docs/html-validation.md)：桌面中文、390px iframe 视口、长文本/注入文本、英文对比，保留截图。
- [源码包/wheel 构建与安装](../evidence/build-install.json)：从 sdist 构建 wheel；分别在干净临时虚拟环境安装、实际命令入口、中文/英文全部格式、对比、卸载验证。
- [变更及基线清单](../evidence/v02-baseline.json)、[SHA-256 文件清单](../SHA256SUMS.txt)。旧 examples/review-fixes、review-dsh、review-maus 及其他原证据仍归 v0.1 历史，不代表第二版新验证。

## 干净目录复跑

将完整目录复制到新的空目录；使用已安装的 Python 3.11+，无需模型密钥或系统配置变动：

```powershell
python -B .\tests\run_tests.py --evidence .\evidence\review-tests.json
python -B .\examples\make_demo.py .\reports\review-demo
python -B .\doctor.py --compare .\reports\review-demo\zh\report.zh.json .\reports\review-demo\after\zh\report.zh.json --format all --output-dir .\reports\review-comparison
python -B .\tests\host_check.py .\evidence\review-host
python -B .\tests\edge_check.py
python -B .\tests\check_artifacts.py
```

文件链接测试需创建符号链接权限。用户已授权补测；如需重做，只在具有该权限的临时进程运行 `python -B .\tests\authorized_links.py .\evidence\review-authorized-links.json`，该脚本拒绝覆盖已有结果。不要更改系统策略或开发者模式。

构建需完整 Python（含 venv/ensurepip）及仅用于临时构建环境的网络依赖。先将本次 dist 成品保留到交付目录之外的新备份，再在复核副本中移除 dist，使其为空，然后执行：

```powershell
python -B .\tests\package_check.py .\evidence\review-package.json
```

脚本创建临时 builder 和两个独立安装环境，只在临时环境获取 build/setuptools/wheel，保留 dist 成品，自动清理虚拟环境。精简嵌入版 Python 没有 venv；本轮使用 Python 官方文档列出的 NuGet Python 3.12.10，解压到任务临时目录，未安装到系统，验收后移除。

## 复核关注点与未覆盖

对比仅接受 schema 1.0 诊断报告，按已知 ID 重建状态、纯数字三段版本、安装组数量及 scan_limited；不复用任意输入文案，也不读取其中路径。详见 [比较契约](../docs/comparison.md)。状态丢失、未知、未查、范围受限不宣称修复。

Windows CI 定义已提供（Python 3.11/3.14、Node 24），托管结果待发布阶段验证。本轮实际系统为 Windows build 26200、Python 3.12.10；未验证真实 Claude 发行包、真实 WSL 内部/运行发行版、其他 Windows/Python 组合、POSIX、物理断网或防火墙隔离。浏览器报告过被阻止的 Google 请求，页面资源列表为空；详见显示核验边界。

以上为 2026-11-19 开发交接快照；后续复核和发布记录见 [v0.2 发布审查](../docs/release-review-v0.2.md)。开发阶段未创建监控、未上传 GitHub/PyPI，未修改用户配置或启动 WSL。
