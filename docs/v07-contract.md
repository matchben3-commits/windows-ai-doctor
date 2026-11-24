# v0.7 JUnit、新发现与 SARIF 基线契约 / JUnit, new findings and SARIF baseline contract

第七版在保留第六版全部入口与安全边界的前提下，增加三项诊断侧能力：`--format junit`、`--fail-on new`（须 `--baseline`）、以及 SARIF 的 `baselineState` / `partialFingerprints` / `new_findings`。运行时仅标准库；版本号 0.7.0。不新增检查项，不改变 19 项 catalog。

v0.7 keeps every v0.6 entry and safety bound, and adds three diagnosis-side capabilities: `--format junit`, `--fail-on new` (requires `--baseline`), and SARIF `baselineState` / `partialFingerprints` / `new_findings`. Runtime remains standard-library only; version is 0.7.0. The 19-check catalog is unchanged.

## 共同边界 / Shared bounds

- `--format junit` 与 `--format sarif` 一样仅诊断模式（可与 `--baseline` 组合）；compare/history/support/validate/verify-support/catalog/schema 显式拒绝。`both` 仍为 MD+JSON，`all` 仍为 MD+JSON+HTML；JUnit/SARIF 只能显式选择。
- `--fail-on` 增加 `new`；与 `regression` 一样必须同时提供 `--baseline`，否则退出 2。默认仍为 `error`。合法选择顺序固定为 `error` → `warn` → `unknown` → `new` → `regression`，重复项去重。
- 退出码沿用诊断语义：未命中 fail-on 为 0，命中为 1，参数/输入/导出失败 2，中断 130。JUnit/SARIF 渲染本身不改变退出判定。
- 有输出目录时排他创建、碰撞退出 2、失败/中断只清理本次文件；`junit`/`sarif`/`csv` 成功时不打印“报告已保存”。

`--format junit` is diagnosis-only. `new` in `--fail-on` requires `--baseline`. Exit codes and exclusive export rules match the product. Directory exports for junit/sarif/csv stay silent on success.

## JUnit XML / JUnit XML

- 文件名 `report.LANG.junit.xml`；UTF-8（无 BOM）、LF、2 空格缩进、末尾换行；无时间戳、无主机名。
- 无输出目录时 stdout 只输出该 XML，不混入 Markdown、保存提示或调试文本。
- XML 声明 `<?xml version="1.0" encoding="UTF-8"?>`；根 `<testsuites name="Windows AI Doctor">`，单个 `<testsuite name="windows-ai-doctor">`；两者均含 `tests`/`failures`/`skipped`/`errors="0"`；不写 `hostname`/`timestamp`/`time`/`package`。
- 每个 finding 一个 `<testcase>`，按 `check_id` ASCII 升序；`classname="windows-ai-doctor.<target>"`，`name="<check_id>"`；不写 `time`/`file`/`line`。
- **每个** `<testcase>` 都带非空 `<properties>`，未命中退出条件的 `pass`/`warn`/`unknown` 同样保留。子 `<property>` 只允许按固定顺序出现：`status` → `scan_limited`（仅 evidence 有该布尔字段时，`true`/`false`）→ `baseline_change` → `baseline_new` → `baseline_regression`。后三者仅在 `--baseline` 时出现；`baseline_change` 为 `added`/`changed`/`unchanged`，`baseline_new` 和 `baseline_regression` 为 `true`/`false` 文本。
- 未命中的用例**只含** `<properties>`，不含 `<failure>`/`<skipped>`/`<error>`；`warn`/`unknown` 未命中时不得生成 `<skipped>`。
- `status=skipped`：保留 properties，再带 `<skipped/>`。
- 生成 `<failure type="policy">` 当且仅当：status 属于本次选中的 `error`/`warn`/`unknown`；或选中 `new` 且 ID∈`baseline.new_findings`；或选中 `regression` 且 ID∈`baseline.regressions`。`message` 由固定双语短句按固定顺序拼接；正文只允许固定说明（策略结果 ≠ 已确认故障根因）。
- 不得把 finding 的 summary、evidence、版本号、路径、配置值或原始输出写入 XML。

Every testcase carries non-empty `<properties>`. Non-selected pass/warn/unknown cases contain only those properties. Skipped cases keep properties and add `<skipped/>`. Failures express exit policy only.

## `--fail-on new` / New findings

一个检查是“新发现”，当且仅当：相对基线 `change` 为 `added`；本次状态为 `error` 或 `warn`；若 ID 以 `.path` 结尾且本次 `scan_limited` 为 `true`，不计入。

A finding is “new” iff it is baseline `added`, status is `error` or `warn`, and a `.path` ID with `scan_limited=true` is excluded.

- `added` 且 `pass`/`unknown`/`skipped` 不算；`removed`/`changed`（向好或向坏）都不算；`new` 不是“任何新增 ID”的同义词。
- 诊断 JSON 的 `baseline` 增加 `new_findings`（升序 ID 数组），与 `regressions` 并列；`summary.added` 仍是原始 added 计数。
- `--fail-on new` 在 `new_findings` 非空时触发退出 1；与其他条件组合时任一触发即退出 1。`exit_policy.meaning` 须写明新发现只是相对基线的 added error/warn（排除扫描受限 path），不等于已确认故障根因。
- CSV 保持 v0.6 的 10 列不变；MD/HTML 基线段在既有计数中增加“新发现 / New findings”，固定 ID `baseline-counts` 不变。

## SARIF 基线状态与指纹 / SARIF baseline state and fingerprints

在 v0.6 无文件位置 SARIF 2.1.0 子集上做加法：

- `helpUri` → `docs/v07-contract.md`；`semanticVersion` 随 `__version__` 为 0.7.0。
- 每个 `results[]` 增加 `partialFingerprints`：固定单键 `"windowsAIDoctorCheckId/v1"` = `check_id`；无基线时也写；不得加入状态、版本或路径。
- 有 `--baseline` 时每个 result 增加 `baselineState`：`added`→`"new"`，`changed`→`"updated"`，未出现在 changes 中→`"unchanged"`。不生成 `"absent"`；基线独有、本次未出现的检查仍不进入 `results`（未出现 ≠ 已修复）。
- `invocations[0].properties.baseline` 增加 `new_findings`，并可含 `result_baseline_states`（仅统计本次实际生成的 results，键 `new`/`updated`/`unchanged`，缺省 0）。
- 无 `locations`/`artifacts`/路径/时间戳；不宣称可直接用于 GitHub code scanning。

Fingerprints are stable across runs. Absent baseline IDs never appear as SARIF results; absence does not mean fixed.

## 代码含义 / Code meanings

| 代码 / Code | 含义 / Meaning |
| --- | --- |
| `new_findings` | 相对基线 added 且本次为 error/warn（排除 scan_limited 的 `.path`） |
| `baseline_new` / `baseline_regression`（JUnit） | 该 ID 是否分别属于 `new_findings` / `regressions` |
| `baselineState` new/updated/unchanged | 对应 change added/changed/未变；无 absent |
| `windowsAIDoctorCheckId/v1` | 稳定指纹，值为 check_id |

JUnit、新发现与 SARIF 扩展均不计算健康评分；unknown/skipped/removed/scan_limited/added 从不证明修复。

None of these exports compute a health score; unknown/skipped/removed/scan_limited/added never establish a fix.

## 复跑示例 / Reproducible examples

```powershell
python .\examples\make_v07_demo.py .\reports\v07-demo-new
python .\doctor.py --no-version --format junit --lang en
python .\doctor.py --no-version --baseline baseline.json --fail-on new --format junit --output-dir .\reports\junit-new
python .\doctor.py --no-version --baseline baseline.json --fail-on new regression --format sarif --output-dir .\reports\sarif-new
```

生成器只写合成观察与派生导出。权限受限时必需真实链接用例须失败并阻塞验收；授权后完整套件单独计数，禁止与普通权限结果拼接。历史契约 [v0.6](v06-contract.md) / [v0.5](v05-contract.md) / [v0.4](v04-contract.md) 原字节保留。

The generator writes authored synthetic observations. When link privileges are unavailable, required real-link cases must fail and block acceptance. Historical v0.6/v0.5/v0.4 contracts remain byte-stable.
