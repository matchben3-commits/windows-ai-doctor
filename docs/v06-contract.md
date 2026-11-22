# v0.6 基线、诊断 CSV 与 SARIF 契约 / Baseline, diagnosis CSV and SARIF contract

第六版在保留第五版全部入口与安全边界的前提下，增加三项诊断侧能力：`--baseline` 与 `--fail-on regression`、诊断 `--format csv`、诊断 `--format sarif`（无文件位置子集）。运行时仅标准库；版本号 0.6.0。回归定义以前面逐字枚举的三种状态转移为准（pass→warn、pass→error、warn→error）；任务书中“四种”字样为笔误，不另扩范围。

v0.6 keeps every v0.5 entry and safety bound, and adds three diagnosis-side capabilities: `--baseline` with `--fail-on regression`, diagnosis `--format csv`, and diagnosis `--format sarif` (subset without file locations). Runtime remains standard-library only; version is 0.6.0. Regression means exactly the three enumerated transitions (pass→warn, pass→error, warn→error); the task book's “four” wording is a typo and does not expand scope.

## 共同边界 / Shared bounds

- `--baseline` 仅诊断模式；与 compare/history/support/validate/verify-support/catalog/schema 互斥；可与既有诊断参数、`--format`、`--lang`、`--output-dir`、`--fail-on` 组合。
- `--fail-on` 增加 `regression`；单独或组合使用时必须同时提供 `--baseline`，否则退出 2。默认仍为 `error`。
- 基线经 `load_report` 在任何诊断探测之前读取与校验；非法基线不得启动 Doctor。边界同既有：schema 1.0、诊断类型、2 MiB / 16 层 / 20,000 节点、拒绝链接与派生类型。
- 成功诊断未触发 fail-on 退出 0，触发退出 1；参数/输入/导出失败 2，中断 130。csv/sarif 有输出目录时排他创建、碰撞退出 2、失败/中断只清理本次文件，且不打印“报告已保存”。

`--baseline` is diagnosis-only and mutually exclusive with offline modes. `regression` in `--fail-on` requires `--baseline`. Baseline validation precedes any probe. Exit codes and exclusive export rules match the product: 0/1 for completed diagnosis policy, 2 for argument/input/export failure, 130 for interruption. csv/sarif directory exports stay silent on success.

## 基线对比与回归 / Baseline comparison and regression

- 诊断完成后附加顶层 `baseline`：`schema_version="1.0"`、`summary`（added/removed/changed）、`unchanged`、`changes`、`regressions`、固定双语 `notice`。无 `generated_at`、无输入路径或自由文本。
- `changes` 沿用 compare 的 `id`/`change`/`before`/`after`/`note`/`details`，并增加布尔 `regression`。`change`∈`added`/`removed`/`changed`；`note` 仅五码。
- 仅白名单投影：五态、数字三段版本、0–32 安装组、布尔扫描限制。同一版本同一输入可重复 diff（本次报告自身 `generated_at` 除外）。
- **回归**（须同时满足）：`change==changed`；`(before, after)` ∈ `{(pass,warn),(pass,error),(warn,error)}`；两侧 `scan_limited` 均不是 `true`（缺失按非 true）。`added`/`removed`、向好变化、`pass→unknown`/`pass→skipped`/`unknown→error`/`skipped→error` 等均非回归。
- `regressions` 为满足条件的 ID 升序数组，与各项 `regression` 一致。`--fail-on regression` 在该数组非空时触发；与 `error`/`warn`/`unknown` 组合时任一触发即退出 1。`exit_policy.meaning` 须写明回归只是固定状态转移，不等于已确认故障根因。
- MD/HTML：摘要之后、退出条件之前插入基线段；固定 ID `baseline-comparison` / `baseline-heading` / `baseline-counts` / `baseline-changes`；动态文字 HTML 转义；无脚本/URL/样式。无 `--baseline` 时既有输出语义不变（版本号除外）；`both`/`all` 格式集合不变。

Baseline is an additive audit section and does not rewrite current diagnosis states. Regressions are the three transitions above without scan limits. Markdown/HTML place the baseline section after the summary and before exit conditions, with the fixed element IDs listed above.

## 诊断 CSV / Diagnosis CSV

`--format csv` 对 diagnosis/history/compare 开放；validate/verify-support/support/catalog/schema 显式 csv 继续拒绝。诊断 CSV 是本次报告扁平投影，不另跑诊断、不读输入内路径。

Diagnosis `--format csv` is available for diagnosis/history/compare. Other modes still reject explicit csv. The diagnosis CSV is a flat projection of the completed report only.

- 文件 `report.LANG.csv`；UTF-8 BOM、`\n`、标准 csv 引号。无输出目录时 stdout 只输出 CSV。
- 固定 10 列：`sequence,check_id,target,status,version,installation_groups,scan_limited,baseline_change,baseline_status,baseline_regression`。
- 无基线：行为本次全部 finding，三列基线字段全部留空（不得用空串冒充 `false`）。有基线：本次与基线 finding 的并集；基线独有行 `status` 留空且 `baseline_change=removed`。
- 按 `check_id` ASCII 升序，`sequence` 从 1 连续递增。`target`∈`system`/`codex`/`claude`/`wsl`/`scope`；`status` 为五态或空；`version` 仅 `.version`/`.dependency` 数字三段；`installation_groups` 仅 `.path` 的 0–32；`scan_limited` 仅 `.path` 的 `true`/`false`，缺失留空。缺失、`0`、`false` 可区分。
- 有基线：`baseline_change`∈`unchanged`/`added`/`removed`/`changed`；`baseline_status` 为基线侧状态（`added` 留空）；`baseline_regression` 为 `true`/`false` 且仅固定回归定义为 `true`。
- 中英 CSV 正文逐字节相同；公式前缀与输入文字不得进入单元格；空报告仅 BOM+表头。

Chinese and English diagnosis CSV bodies are byte-identical. Formula-leading free text never reaches cells.

## SARIF 2.1.0（无文件位置子集）/ SARIF 2.1.0 without locations

`--format sarif` 仅诊断（可与 `--baseline`）；其他模式显式 sarif 拒绝。`both`/`all` 集合不变，SARIF 只能显式选择。

`--format sarif` is diagnosis-only (optionally with `--baseline`). Other modes reject explicit sarif. `both`/`all` sets are unchanged.

- 文件 `report.LANG.sarif`；UTF-8 无 BOM、LF、`ensure_ascii=False`、2 空格缩进、末尾换行。
- 顶层：`$schema`（固定 OASIS 2.1.0 cos02 标识 URI）、`version="2.1.0"`、单元素 `runs`。无外部 `$ref`、不联网。
- `tool.driver`：`name="Windows AI Doctor"`、`semanticVersion=0.6.0`、仓库 `informationUri`、`rules` 覆盖 catalog 全部 19 个 ID（ASCII 升序）。规则文案按 `--lang` 取 catalog 的 purpose/limitation，与 catalog 同源；`helpUri` 指向本契约文档。
- `results`：仅 `error`/`warn`/`unknown`（映射为 error/warning/note）；按 `ruleId` 升序；含 `ruleId`、合法 `ruleIndex`、`level`、固定 summary 消息及 `properties.status`/`target`（有则含 `scan_limited`）。**无** `locations`/`artifacts`、原始路径、evidence 值。`pass`/`skipped` 不生成结果，但其计数与 `scan_limited` ID 出现在 invocation properties。
- `invocations[0]`：`executionSuccessful=true`；`exitCode` 为最终 fail-on 决定的 0 或 1；properties 含 language/schema_version/summary/fail_on/triggered/matched/scan_limited_checks/notice；有基线时再含 baseline 的 summary/unchanged/regressions。
- `runs[0].properties`：`status_vocabulary`、固定 notice、`diagnosis_schema_version`。无时间戳、机器名、路径或命令行。
- 同报告同语言双次渲染逐字节一致；中英同构。**如实声明**：不含源文件位置，不宣称可直接用于 GitHub code scanning；`executionSuccessful` 只表示工具完成执行；未知/扫描受限不代表故障或修复。

This is a SARIF 2.1.0 subset without source-file locations. Direct GitHub code-scanning upload is not claimed.

## 代码含义 / Code meanings

| 代码 / Code | 含义 / Meaning |
| --- | --- |
| `added` / `removed` / `changed` / `unchanged` | 相对基线的出现、消失、白名单观察变化或未变 |
| `pass→warn` / `pass→error` / `warn→error` | 唯一三种回归转移（双侧非 scan_limited=true） |
| `true` / `false`（CSV `baseline_regression`） | 是否满足固定回归定义；无基线时该列留空 |
| error / warning / note（SARIF level） | 分别对应诊断 error / warn / unknown |

基线、诊断 CSV 与 SARIF 均不计算健康评分；unknown/skipped/removed/scan_limited/added 从不证明修复。

None of these exports compute a health score; unknown/skipped/removed/scan_limited/added never establish a fix.

## 复跑示例 / Reproducible examples

```powershell
python .\examples\make_v06_demo.py .\reports\v06-demo-new
python .\doctor.py --no-version --baseline baseline.json --fail-on regression --format all --output-dir .\reports\baseline-new
python .\doctor.py --no-version --format csv --lang zh
python .\doctor.py --no-version --format sarif --output-dir .\reports\sarif-new
```

生成器只写合成观察与派生导出，不把主机诊断结果当作示例正文。权限受限时必需真实链接用例须失败并阻塞验收；授权后完整套件单独计数，禁止与普通权限结果拼接。

The generator writes authored synthetic observations and derived exports. When link privileges are unavailable, required real-link cases must fail and block acceptance; after authorization, the complete suite is counted separately and must not be spliced with the unprivileged run.
