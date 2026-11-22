# v0.6 基线 HTML 显示核验 / Baseline HTML display validation

2026-11-22，北京时间。使用 `examples/make_v06_demo.py` 的预设合成观察；不执行主机诊断。中文与英文报告均实际在浏览器渲染。

Authored synthetic observations were rendered in a real browser. The example generator replaces Doctor with an authored fixture before invoking the CLI; no host diagnostic probe runs.

- 桌面 viewport 为 1280 × 720 CSS px；中文与英文均检查基线段、计数及回归标记。
- 窄屏为两个独立 iframe，各 `innerWidth=390` CSS px，`clientWidth=scrollWidth=375`（垂直滚动条占 15 px），媒体查询 `max-width:480px` 生效。中英文均无水平溢出的段落、标题或代码块。
- 固定 ID `baseline-comparison`、`baseline-heading`、`baseline-counts`、`baseline-changes` 各出现一次；基线段位于摘要之后、退出条件之前。
- 合成计数：added 2、removed 1、changed 3、regressions 2、unchanged 2。两处回归为 `claude.path`（pass→error）与 `codex.version`（pass→warn）。`codex.path` 的 scan_limited=true 未标回归；added/removed 均未标回归。
- 实际滚动检查了两处回归卡片；已人工查看桌面双语、390 px 双语和第二处回归的截图。截图及 DOM 数值保存在内部开发交接材料中。
- 页面无脚本元素，报告页面资源计时列表为空。浏览器报告了一个指向 www.google.com 的被阻止请求；未把浏览器日志或资源计时当作抓包，也不据此声称完全没有网络行为。

Desktop viewport: 1280 × 720 CSS px. Each narrow-layout iframe had an actual 390 CSS px viewport; its 375 px document width matched its client width, with no overflowing baseline text blocks. All four fixed IDs were unique. Both fixed-rule regressions and the scan-limited non-regression were checked. Counts were 2 added, 1 removed, 3 changed, 2 regressions and 2 unchanged.

本核验仅证明合成报告在桌面浏览器与 iframe 布局中的显示，不是物理手机、触摸、屏幕阅读器或网络抓包验收。

This is desktop-browser and iframe layout validation, not physical-phone, touch, screen-reader or packet-capture acceptance.
