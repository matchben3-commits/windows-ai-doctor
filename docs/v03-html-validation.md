# 第三版 HTML 实际显示核验 / Actual display checks

2026-11-21，gpt 在本轮挂载的 Browser 中直接打开本地合成报告；实现者自测，不替代 dsh 独立复核。未更改浏览器设置。

| 样例 | 观察 | 证据 |
| --- | --- | --- |
| 中文3次趋势，1280×720 | 中文标题、各次数量、异常/未知/通过状态文字与符号可读 | [截图](../evidence/v03-html/zh-desktop.png) |
| 英文20次，1280×720，滚至最后一列 | Run 20清晰，水平滚动条移动；ID列和ID表头固定，状态有颜色、符号和文字 | [截图](../evidence/v03-html/en-desktop-run20.png) |
| 中文390 CSS px iframe | 标题和隐私/范围说明换行；表格区域独立滚动，不撑宽页面 | [首屏](../evidence/v03-html/zh-narrow-header.png)、[状态矩阵](../evidence/v03-html/zh-narrow-matrix.png) |
| 中文390px，横向滚至20次 | 第20次与固定ID列仍可同时读取 | [截图](../evidence/v03-html/zh-narrow-run20.png) |
| 英文390px，首列与末列 | 左侧ID固定，Run 1/Run 20可读，Unknown/Error/Pass有符号辅助；区域可聚焦 | [首列](../evidence/v03-html/en-narrow-left.png)、[末列](../evidence/v03-html/en-narrow-run20.png) |

窄视口是实际390 CSS像素iframe内容区，不是手机硬件或整个浏览器窗口缩放。通过点击最后一列实际将表格横向滚至Run 20；截图证明固定ID和末列同时可见。静态结构测试另拒绝script/img/link/form及外部资源属性，并检查CSP；它不替代本次显示检查。

Browser导航多次报告对www.google.com:443的访问被阻止，来源未归因。报告生成的HTML只用内嵌样式，无外部资源依赖；不能由此声称整个浏览器进程没有联网尝试。本轮没有抓包、物理断网、手机设备或屏幕阅读器验收。

Reproduce with `python -B examples/make_v03_demo.py` in a fresh copy without generated examples, or use a new destination; then run `python -B tests/render_v03_fixtures.py` and open evidence/v03-html/narrow-zh.html or narrow-en.html. The three-run and twenty-run samples are synthetic.
