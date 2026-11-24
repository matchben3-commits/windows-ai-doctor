# v0.7.0 开发交接 / Development handoff

2026-11-24，北京时间。gpt 主实现及最终集成，cursor 交叉审查、独立补测、文档与合成示例。开发基线为 main `9b591aba6bc19222511eba69135f31abbe672f7f`；第六版产品基线为 `10b9a347ce01efb5e767849bf801c3ee372940d3`。版本 0.7.0，运行时仅标准库，catalog 保持 19 项。

gpt implements and integrates; cursor contributes independent tests, cross-review, documentation and synthetic examples. The candidate starts from main 9b591ab, preserving the documentation site. Runtime dependencies remain standard-library only.

## 功能与边界 / Behavior and bounds

- `--format junit` 仅诊断模式；UTF-8 无 BOM、LF、确定性、无时间戳或路径。每个 testcase 保留非空 properties；未命中项只含 properties，skipped 项再带 skipped，命中策略项生成 policy failure。failure 不代表已确认故障根因。
- `--fail-on new` 必须带 baseline；只计 added error/warn，排除 scan_limited 的 `.path`。JSON/MD/HTML/SARIF/JUnit 贯通；CSV 仍为 10 列。
- SARIF 增加稳定指纹 `windowsAIDoctorCheckId/v1`，有基线时增加 new/updated/unchanged 与仅 results 的状态计数。无 absent、locations、artifacts，不宣称可直接用于 GitHub code scanning。
- `baseline_change` 的值为 added/changed/unchanged；只有 `baseline_new` 和 `baseline_regression` 为 true/false。详情见 [第七版契约](docs/v07-contract.md)。
- 保留全部旧入口、安全边界、排他导出与退出码。`both` 仍为 MD+JSON，`all` 仍为 MD+JSON+HTML。历史 v0.4/v0.5/v0.6 契约保持原字节；Pages 的 v0.6 合成报告保持历史标识。

JUnit failures express selected exit policy. New findings are baseline additions with error/warn status, excluding scan-limited path checks. SARIF fingerprints contain only check IDs. Unknown, skipped, removed and absent observations do not prove a repair.

## 完整测试与权限门槛 / Complete suite and permission gate

当前发现集为 203 个唯一用例：保留全部 v0.6 的 168 个 ID，新增 gpt 23 项与 cursor 12 项。必须一次完整运行 203 PASS、0 FAIL、0 ERROR、0 SKIP、实际进程退出 0；不得拼接独立运行，也不得用 CI 或旧版记录替代本机授权完整套件。

完整运行需要 Windows、Node、.NET 合成夹具编译器及真实符号链接创建权限。11 项必需 symlink 和 junction 回归不能跳过。链接只创建在合成夹具内，审计 reparse tag、目标内容读取次数与后代访问次数；不更改开发者模式、系统安全策略或真实配置。

The suite discovers 203 unique cases: all 168 previous IDs plus 35 new cases. Acceptance requires one complete zero-skip, zero-failure run with actual exit 0. Unprivileged failures remain separate evidence. Link targets and descendants are guarded by access audits.

本轮实测结果以冻结候选内 `evidence/v07-tests.json`、`evidence/v07-process.json` 和外部开发交接为准。缺少授权记录或存在未通过门槛时，候选仍待验收；本文件不以历史结果代替本轮执行。

## 构建与示例 / Packaging and examples

`tests/package_check.py` 在任务临时环境构建 sdist，再从 sdist 构建 wheel；两包分别在干净 venv 安装，检查 console/module、新旧入口、双语 JUnit、new 退出 1、同基线退出 0、缺基线退出 2，然后卸载。构建步骤、实际退出码、包哈希见 `evidence/v07-package.json`；依赖不安装到系统 Python。

`examples/make_v07_demo.py` 只使用预设合成观察，不运行真实主机诊断。示例包含双语 JSON/MD/HTML/CSV/SARIF/JUnit，new 与 regression 策略退出及相同基线退出 0。v0.4/v0.5/v0.6 生成器及文件名集合保留。生成示例的 CLI 运行不计入 203 项产品测试。

Both distributions are installed, exercised and uninstalled in isolated environments. Examples use authored observations with fixed time. Packaging and example verification are separate from product-test counts.

HTML 桌面与 390 CSS px iframe 的实际显示检查见 [HTML 显示核验](docs/v07-html-validation.md)；它不代表物理手机、触摸、屏幕阅读器或抓包验收。

```powershell
python -B tests/run_tests.py --evidence evidence/review-v07-tests.json
python -B tests/package_check.py evidence/review-v07-package.json --artifacts-dir reports/packages-new
python -B examples/make_v07_demo.py reports/v07-demo-new
python -B tests/check_artifacts.py
```

校验脚本更新根 `SHA256SUMS.txt`，不把旧的 v0.6 清单当作本轮证据。分发成品放外部交付目录；源码根 dist 不留成品，候选不包含临时环境、夹具或字节码。

尚未覆盖：真实 Claude 发行包、WSL 内部、物理手机、屏幕阅读器、网络抓包。本机测试之外，dsh 独立复核、本轮 Windows Python 3.11/3.14 CI、MausBot 终审发布及匿名附件回验均为后续独立门槛。实现阶段不 push、不建 tag/Release、不设监控、不发送求助包。

Independent review, hosted CI and publication remain separate gates. This local implementation handoff performs no GitHub writes.
