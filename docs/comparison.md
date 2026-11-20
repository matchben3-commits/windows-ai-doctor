# 离线对比契约 / Offline comparison contract

`python doctor.py --compare OLD.json NEW.json --lang zh --format all --output-dir reports/comparison-new`

该模式仅打开两个明确指定的固定本地盘普通文件。不运行 Doctor、CLI、Node、注册表检查、WSL 或网络；不访问输入内的路径/URL。入口从根到叶检查，拒绝链接和重解析点及其后代；继承不防御并发替换/硬链接的边界。

Reads only the two explicit files, never embedded paths. No diagnostic probes run. Input files use the same conservative local-drive and root-to-leaf link policy as diagnosis.

## 输入与边界 / Input limits

- UTF-8 JSON 对象、`schema_version="1.0"`；`report_type` 缺省或为 `diagnosis`。兼容 v0.1 和 v0.2 诊断输出；不接受对比输出作为诊断输入。
- findings 为数组，最多 64 项，ID 必须属于当前已知检查 ID 且不重复；状态仅 pass/warn/error/unknown/skipped。evidence 缺省为对象，存在时必须为对象。
- 读取前限制 2 MiB；解码前限制 16 层括号嵌套；总节点最多 20,000；单字符串最多 32,768 字符；整数文本最多 12 字符、浮点文本最多 32 字符，拒绝非有限数、重复 JSON 键和非法 JSON。这些限制也作用于被忽略字段。
- 只采用 `{tool}.version`/`{tool}.dependency` 的纯数字三段版本（每段 1–4 位），`{tool}.path` 的 installation_groups（0–32 整数）和 scan_limited（布尔）。其他字段仅解析以验证有界 JSON，完全不复制到输出。含发布标签的版本不比较，以免导出任意字符串。
- 未要求源 summary/文案完整；它们无论存在或合法与否都不用于结论。未知额外字段被忽略但仍受结构限额；未知检查 ID 拒绝。

Versioned schema-1.0 diagnosis input only. Known IDs, unique keys/IDs and enumerated states are required. Ignored text still shares the size, depth and node budgets. Only numeric versions, group counts and scan-limit flags survive the projection; arbitrary summaries, recommendations, paths and metadata are discarded. This is a limited comparison projection, not a full report-schema validator.

## 判断 / Interpretation

按 ID 比较新增、移除、状态及受支持观察。忽略时间、语言、PATH 代号和任意文案。`<PATH:1>` 跨次无身份意义，不能证明同一路径或同一主机；环境相同须人工确认。版本相同而状态变化仍显示，状态相同而数字版本变化也显示。

`error → unknown/skipped` 为无法判断；移除为本次未包含、未再检查。范围限制变化明示 scan_limited，不当作修复。`error → pass` 仅说该检查本次通过。比较没有覆盖到的其他证据不代表未变化。输出不推断“整个问题已解决”。

Unknown/skipped/removed checks and reduced coverage never establish a fix. A pass states that this check passes now only. Reports do not establish host identity, path identity or changes in arbitrary evidence fields.

## 输出与退出 / Output and exit

文件名 `comparison.zh.md/json/html`（英文为 en）；默认 both=MD+JSON，all=三种。无目录时 both/all 输出 MD，json/html 单独输出对应格式。已存在文件不覆盖，失败清理本次新文件；中断退出 130，其他参数/输入/导出失败 2。完成比较退出 0，与历史报告 error 数量无关。

`--tools`、`--home`、`--project`、`--timeout`、`--no-version`、`--wsl-list` 与比较冲突；不接受参数缩写。输入错误只输出固定消息，不回显路径、源数据或原始异常。
