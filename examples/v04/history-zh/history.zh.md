# Windows AI Doctor — 多次体检趋势

v0.4.0 · schema 1.0

2026-11-21T10:50:57+00:00

顺序以命令行输入为准。请自行确认所有报告来自同一环境和相同检查范围；不推断机器身份。状态数量不是健康评分。缺失、未知、未检查或扫描受限均不代表修复；通过仅指该项本次通过。仅比较已知检查的状态、数字版本、安装组数量和扫描限制。

## 各次状态数量

| 顺序 | 通过 | 提醒 | 异常 | 无法判断 | 未检查 |
| --- | --- | --- | --- | --- | --- |
| 第1次 | 1 | 0 | 2 | 0 | 1 |
| 第2次 | 0 | 1 | 0 | 1 | 1 |
| 第3次 | 3 | 0 | 0 | 0 | 1 |

## 检查状态与有限观察

| ID | 第1次 | 第2次 | 第3次 |
| --- | --- | --- | --- |
| codex.config.user | × 异常 | — 未包含 | ✓ 通过 |
| codex.path | ✓ 通过 {"installation_groups": 1, "scan_limited": false} | ! 提醒 {"installation_groups": 2, "scan_limited": true} | ✓ 通过 {"installation_groups": 3, "scan_limited": false} |
| codex.version | × 异常 {"version": "1.2.1"} | ? 无法判断 {"version": "1.2.2"} | ✓ 通过 {"version": "1.2.3"} |
| scope.unchecked | — 未检查 | — 未检查 | — 未检查 |

## 第1次 → 第2次

无变化检查数：1

- codex.config.user: error → —. 本次未包含，未再检查。 {}

- codex.path: pass → warn. 无法判断、未再检查或扫描受限，不代表修复。 {"installation_groups": {"before": 1, "after": 2}, "scan_limited": {"before": false, "after": true}}

- codex.version: error → unknown. 无法判断、未再检查或扫描受限，不代表修复。 {"version": {"before": "1.2.1", "after": "1.2.2"}}

## 第2次 → 第3次

无变化检查数：1

- codex.config.user: — → pass. 本次新增检查。 {}

- codex.path: warn → pass. 该检查本次通过。 {"installation_groups": {"before": 2, "after": 3}, "scan_limited": {"before": true, "after": false}}

- codex.version: unknown → pass. 该检查本次通过。 {"version": {"before": "1.2.2", "after": "1.2.3"}}
