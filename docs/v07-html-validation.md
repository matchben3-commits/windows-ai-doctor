# v0.7 基线 HTML 显示核验 / Baseline HTML display validation

2026-11-24，北京时间。使用 `examples/make_v07_demo.py` 的预设合成观察；不执行主机诊断。中文与英文报告均实际在浏览器渲染。

Authored synthetic observations were rendered in a real browser. The example generator replaces Doctor with an authored fixture before invoking the CLI; no host diagnostic probe runs.

- 桌面 viewport 约 1280 CSS px 宽；中英文均检查基线段、计数及“新发现 / New findings”。
- 窄屏为两个独立 iframe，各固定 `width:390px`、`height:720px` CSS；外层实测 iframe `clientWidth=390`。中英文并排截图已人工查看。
- 固定 ID `baseline-comparison`、`baseline-heading`、`baseline-counts`、`baseline-changes` 各出现一次；基线段位于摘要之后、退出条件之前。
- 合成计数：added 3、removed 1、changed 2、regressions 1、unchanged 2、**new findings 1**（`claude.path` 为基线缺失的 added error）。`codex.version` 为 pass→warn 固定规则回归。
- 页面无脚本元素。浏览器报告了一个指向 www.google.com 的被阻止请求；未把浏览器日志当作抓包，也不据此声称完全没有网络行为。
- 截图与 DOM 数值保存在本轮联调证据目录的 `html/` 子目录；该目录在仓库之外，不随发布包分发。

Desktop ~1280 CSS px. Narrow layout used two 390×720 CSS px iframes. All four fixed IDs were unique. New-findings count 1 and the fixed-rule regression were checked. Screenshots and recorded DOM values remain in the run's evidence folder outside this repository.

本核验仅证明合成报告在桌面浏览器与 iframe 布局中的显示，不是物理手机、触摸、屏幕阅读器或网络抓包验收。Pages 上的 v0.6.0 SIMULATED 样例未改动。

This is desktop-browser and iframe layout validation, not physical-phone, touch, screen-reader or packet-capture acceptance. Historical v0.6.0 Pages samples remain unchanged.
