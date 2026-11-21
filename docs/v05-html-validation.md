# v0.5 HTML 显示回归 / Display regression

2026-11-21，gpt。在本轮 Screen 面板的 Browser 标签页，使用 v0.5.0 渲染器从已有公开合成输入重新生成 20 次趋势 HTML，未运行真实环境诊断。

- 英文桌面视口 1280px：表格客户区 1050px，横滚 1841px 后，固定 ID 与 Run 20 同时可见。[截图](../evidence/v05-html/en-desktop-run20.png)。
- 中文 390 CSS px iframe：内容宽 375px，标题、版本和范围提示换行正常。表格客户区 349px，横滚 2542px 后固定 ID 与第20次同时可见。[首屏](../evidence/v05-html/zh-narrow-header.png)、[末列](../evidence/v05-html/zh-narrow-run20.png)。
- 英文同一 390 CSS px 条件：固定 ID、Run 20、状态文字及符号可见；表格聚焦有可见边框，按 ArrowLeft 后 scrollLeft 从 2542 变为 2502，实测移动 40px。[截图](../evidence/v05-html/en-narrow-run20.png)。

窄视图使用本轮 HTML 原文作为 iframe 的 srcdoc，不是物理手机。观察到状态文字、符号和颜色，以及受限白名单观察值。源码安全测试、结构检查和本次显示检查分开计数，不互相替代。

各次本地页面导航报告了发往 www.google.com:443 的请求被阻止，未归因其来源；不能由此声称整个浏览器没有联网尝试。未进行抓包、物理断网、真实手机或屏幕阅读器验收。

English: current v0.5 HTML was rendered from public synthetic inputs in Browser. Desktop and bilingual 390 CSS-pixel iframe checks showed the fixed ID and final run together. Keyboard scrolling moved the focused English table by 40px. The iframe checks do not constitute physical-device or screen-reader testing. A blocked Google request was reported and not attributed; no process-wide network claim is made.
