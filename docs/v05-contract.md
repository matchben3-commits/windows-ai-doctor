# v0.5 离线导出契约 / Offline export contract

第五版在保留第四版全部入口与安全边界的前提下，增加三项离线导出：compare `--format csv`、`--catalog`、`--schema`。三者都不运行诊断、不读认证、不启动 WSL（catalog/schema 亦不读输入文件）。运行时仅标准库；版本号 0.5.0。

v0.5 keeps every v0.4 entry and safety bound, and adds three offline exports: compare `--format csv`, `--catalog`, and `--schema`. None of them run diagnosis or read credentials; catalog/schema also read no input files. Runtime remains standard-library only; version is 0.5.0.

## 共同边界 / Shared bounds

- 模式互斥：诊断、compare、history、support、validate、verify-support、catalog、schema。
- 派生模式拒绝显式诊断参数与 `--fail-on`（含显式默认值与等号写法）；参数不可缩写。
- 成功 0，参数/导出失败 2，中断 130；失败提示不回显路径、内容或异常。
- 有输出目录时排他创建；碰撞退出 2 且保留旧文件；失败/中断只清理本次新文件。

Modes are mutually exclusive. Derived modes reject explicit diagnostic options and `--fail-on`, including defaults and equals forms. Abbreviated options are disabled. Success exits 0; argument/export failures exit 2; interruption exits 130. Failure text never echoes paths, content or exceptions. Directory exports use exclusive creation; collisions exit 2 and keep existing files; failed/interrupted exports clean only files created in that attempt.

## compare CSV

`--compare OLD.json NEW.json --format csv` 仅对 history/compare 开放；其他模式显式 `csv` 继续拒绝。既有 `both`/`md`/`json`/`html`/`all` 集合与 compare JSON 结构不变。

`--compare OLD.json NEW.json --format csv` is available only for history/compare; other modes still reject an explicit `csv`. Existing `both`/`md`/`json`/`html`/`all` sets and the compare JSON shape stay unchanged.

- 文件 `comparison.zh.csv` / `comparison.en.csv`；UTF-8 BOM、`\n`、标准 csv 引号。无输出目录时 stdout 只输出 CSV。
- 固定 12 列表头：`sequence,check_id,change,before_status,after_status,note,version_before,version_after,installation_groups_before,installation_groups_after,scan_limited_before,scan_limited_after`。
- 只列实际变化，按 `check_id` 升序，`sequence` 从 1 递增；无变化时仅 BOM+表头。`change`∈`added`/`removed`/`changed`；`note` 仅五个固定码。
- 值来自白名单投影：五态、数字版本正则、0–32 安装组、布尔扫描限制。缺失与 `false` 可区分（缺失留空）。中英 CSV 正文逐字节相同。
- 输入文字与公式前缀（`=`/`+`/`-`/`@`）不得进入单元格。OLD/NEW 文件及祖先目录链接须真实拒绝，目标内容读取为 0。

Files are `comparison.zh.csv` / `comparison.en.csv` with a UTF-8 BOM, LF endings and the standard csv writer. Without an output directory, stdout is CSV only. The twelve fixed columns and change/note vocabularies above apply. Only changed checks appear, sorted by `check_id`. Empty change sets emit BOM+header only. Whitelisted observations distinguish missing from `false`. Chinese and English CSV bodies are byte-identical. Formula-leading free text never reaches cells. Real OLD/NEW file and ancestor links must reject with zero target-content reads.

## catalog

`--catalog [CHECK_ID ...]` 离线导出稳定检查目录；不读取输入、不运行诊断、不访问环境/注册表/网络/包内路径。

`--catalog [CHECK_ID ...]` exports the stable check catalog offline. It reads no inputs, runs no diagnosis, and consults no environment, registry, network or packaged paths.

- 覆盖 schema 1.0 接受的 19 个检查 ID，与产品 `IDS` 及「两工具 + 显式 project」实际生成集合一致。
- 每项含 `id`、`target`（`system`/`codex`/`claude`/`wsl`/`scope`）、`availability`（`always`/`project_only`）、`produced_by_current_version`、双语 `purpose`/`limitation`（JSON 均为含 `zh`/`en` 的对象，Markdown 按 `language` 选文）、固定 ASCII `evidence_fields`。
- `codex.config.project`、`claude.config.project`、`claude.config.local` 为 `project_only`，其余 `always`；当前版本全部会生成。
- 格式：`both`/`md`/`json`，**默认 `md`**（与诊断默认 `both` 不同）。显式 `html`/`csv`/`all` 拒绝。无输出目录时 `md`/`json` 打印对应内容，`both` 只打印 Markdown。有输出目录时创建 `catalog.zh.md`/`catalog.zh.json`/`catalog.en.md`/`catalog.en.json` 中对应项。
- JSON：`report_type=catalog`、`schema_version=1.0`、`doctor_version`、`language`、`checks`、`status_vocabulary`（五态）、固定 `notice`；**无 `generated_at`**，同版本同语言可 diff。
- ID 精确匹配、区分大小写；最多 32 个原始参数；重复按首次去重后仍按 ASCII 升序；未知/畸形退出 2 且不回显。空参数列表表示全量 19 项。

Covers the 19 schema-1.0 IDs, identical to product `IDS` and to the generation set with both tools plus an explicit project. Entries carry the fields above. The three project config IDs are `project_only`. Formats are `both`/`md`/`json` with **default `md`** (unlike diagnosis default `both`). Explicit `html`/`csv`/`all` are rejected. Directory names follow `catalog.LANG.ext`. JSON uses `report_type=catalog` with no `generated_at`. IDs are exact and case-sensitive, at most 32 raw arguments, first-seen dedupe then ASCII sort; unknown/malformed IDs exit 2 without echo. An empty ID list means the full set of 19.

模块接口：`catalog_report(ids, lang)` 返回上述对象（`ids=[]`/`None` 为全量）；`catalog_markdown(report)` 返回带末尾换行的 Markdown。未知 ID 抛固定 `ValueError("invalid_catalog")`，不回显输入。

Module API: `catalog_report(ids, lang)` returns the object above (`ids=[]`/`None` = full set); `catalog_markdown(report)` returns Markdown with a trailing newline. Unknown IDs raise the fixed `ValueError("invalid_catalog")` without echoing input.

## schema

`--schema` 输出 draft 2020-12 诊断输入 JSON Schema；无外部 `$ref`；`$id` 仅为标识，不发起请求。仅允许可选 `--output-dir`；显式 `--format`/`--lang`/诊断参数/`--fail-on` 拒绝。无输出目录时 stdout 只输出该 JSON；有目录时排他创建 `schema.diagnosis.json`。

`--schema` emits a draft 2020-12 diagnosis-input JSON Schema with no external `$ref`. The `$id` is an identifier only and is never fetched. Only optional `--output-dir` is allowed; explicit `--format`/`--lang`/diagnostic options/`--fail-on` are rejected. Without an output directory, stdout is that JSON alone; with a directory, `schema.diagnosis.json` is created exclusively.

### 与 `--validate` / `load_report` 的权威关系（务必如实）

最终口径（dsh 2026-11-21 裁定）：schema 与 `load_report` 为**单向一致**——`load_report` 接受的输入，schema 必须接受；允许 schema 因解析器附加限制更宽；**`--validate` 是唯一接受权威**。schema 通过只表示形状匹配。不得收紧 v0.4 读取面。

三项差异（保持现状，按单向一致理解）：

1. **非数字版本：接受但不投影**。读取器对非数字/`None`/非字符串版本不报错，投影为 `None`；数字版本正则仅在 `x-version-projection` 注解，不是 schema 的通用拒绝条件。
2. **安装组 / 扫描限制：仅约束 `.path`**。仅当 finding ID 以 `.path` 结尾且字段存在时检查 `installation_groups`（0–32 整数）与 `scan_limited`（布尔）；其他 ID 上的同名字段忽略，schema 与读取器均接受。
3. **JSON Schema `integer` 数学语义**：draft 2020-12 接受 `1.0`/`1e0`；产品解析器按整数 JSON 令牌拒绝。该**预期差异**记入 `x-parser-limits.integer_tokens_for_path_groups`，不得用非标准断言或测试技巧伪造双方接受面相等。

Final rule (dsh 2026-11-21): schema and `load_report` are **one-way consistent**—every input `load_report` accepts must also pass the schema; the schema may be wider where parser-only limits apply; **`--validate` is the sole acceptance authority**. Passing this schema means structural shape only. It does not establish health, completeness, trusted origin or machine identity. Parser limits (2 MiB, depth 16, 20 000 nodes, duplicate keys/IDs, long tokens, non-finite numbers, integer tokens for path groups) remain enforced by the reader. The three gaps above are expected under one-way consistency, not contradictions.

## CSV 与 catalog 代码含义 / Code meanings

| 代码 / Code | 含义 / Meaning |
| --- | --- |
| `added` / `removed` / `changed` | 比较侧出现、消失或白名单观察变化 |
| `added` / `removed` / `unassessed` / `passes_now` / `observations_changed` | compare note 五码；`unassessed` 含变为 unknown/skipped |
| `pass`/`warn`/`error`/`unknown`/`skipped` | 诊断五态；catalog 的 `status_vocabulary` |
| `always` / `project_only` | catalog 可用性；后者仅在显式 `--project` 时生成 |

CSV 与 catalog 均不计算健康评分，不把 unknown/skipped/removed/scan_limited 当作修复证明。

Neither CSV nor catalog computes a health score; unknown/skipped/removed/scan_limited never establish a fix.

## 复跑示例 / Reproducible examples

```powershell
python .\examples\make_v05_demo.py .\reports\v05-demo-new
python .\doctor.py --catalog --format json
python .\doctor.py --catalog system.platform codex.path --lang en --output-dir .\reports\catalog-new
python .\doctor.py --compare old.json new.json --format csv --output-dir .\reports\compare-csv-new
python .\doctor.py --schema --output-dir .\reports\schema-new
```

生成器只写合成观察与离线导出，不跑主机诊断。权限受限时必需真实链接用例须失败并阻塞验收；授权后完整套件单独计数，禁止与普通权限结果拼接。

The generator writes authored synthetic observations and offline exports only. When link privileges are unavailable, required real-link cases must fail and block acceptance; after authorization, the complete suite is counted separately and must not be spliced with the unprivileged run.
