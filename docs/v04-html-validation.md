# v0.4 HTML 显示回归 / Display regression

2026-11-21，gpt在本轮Screen面板的Browser标签页打开第四版合成趋势报告进行显示检查，未改报告样式。

- 英文20次桌面视图：横滚至Run 20后固定ID列仍可见。视口1280px，表格客户区1050px。[截图](../evidence/v04-html/en-desktop-run20.png)。
- 中文390 CSS px iframe：标题和范围提示换行，页面内容宽375px，表格独立滚动；固定ID与第20次同时可见。表格客户区349px，横滚2542px。[首屏](../evidence/v04-html/zh-narrow-header.png)、[末列](../evidence/v04-html/zh-narrow-run20.png)。
- 英文390 CSS px iframe：ID与Run 20同时可见，区域聚焦后ArrowLeft使scrollLeft从2542变为2502，实际键盘横滚40px。[末列](../evidence/v04-html/en-narrow-run20.png)。

窄视口是实际390 CSS像素iframe，srcdoc内容来自本轮生成HTML原文；不是物理手机。截图显示状态的符号、文字和颜色以及有限观察。字符串/结构安全测试另行记录，不能替代显示验收。

导航报告对www.google.com:443的请求被阻止，来源未归因。HTML自身只用内嵌样式；不能声称整个浏览器没有联网尝试。未做抓包、物理断网、真实手机或屏幕阅读器验收。首次打开误用了不存在的history-20路径，失败不计作通过；随后使用实际history20路径成功打开。最初file iframe不能从父页访问其DOM，随后用相同HTML的srcdoc夹具完成窄视口测量。

English: the current Browser rendered bilingual 20-run histories. The desktop and 390 CSS-pixel iframe checks showed the fixed ID and final run together; keyboard scrolling was verified. These are rendered iframe checks, not physical-device or screen-reader tests. A blocked Google request was reported and not attributed; no process-wide network claim is made.
