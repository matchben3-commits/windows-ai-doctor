> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# HTML 实际显示核验 / Browser display validation

2026-11-19，gpt 在本机可用的内置浏览器实际打开本项目合成 HTML。以下是实现者自测，不替代 dsh 独立复核。报告由临时合成配置生成，不含用户真实配置。

| 样例 / Fixture | 实际观察 / Observation | 截图 / Screenshot |
| --- | --- | --- |
| 中文诊断，1280×720 视口 | 五种状态数字、处理顺序、中文正文可读；19 个检查；横向无溢出 | [中文桌面](../evidence/html/zh-desktop.png) |
| 390 CSS px iframe 内容视口 | 状态卡片自动换行，中文标题及长 ID 换行；不是手机硬件或完整浏览器窗口缩放 | [窄视口](../evidence/html/zh-narrow.png) |
| 长文本与注入字符串 | 合成 script/img/onerror 字符串显示为文本，长文换行；DOM 中 script/img/onerror 元素数 0，window.injected 未定义；无横向溢出 | [文字安全](../evidence/html/escaped-long.png) |
| 英文前后比较 | Added 0 / Removed 0 / Changed 1；18 unchanged；claude.config.local 的 error → pass 标注 This check passes now | [英文比较](../evidence/html/en-comparison.png) |

页面使用内嵌 CSS、无 JavaScript/外部字体/图片/链接依赖，HTML 文本转义并设 CSP。直接打开中文诊断、安全夹具和英文比较时，浏览器 performance resource entries 均为空。浏览器导航另报告尝试访问 www.google.com:443 且被阻止；尚未归因，不能据此声称浏览器进程完全没有网络尝试。报告 DOM 没有相应资源，静态检查也无加载资源标签。未做物理断网或流量抓包。

The mounted browser reported a blocked Google request on navigation. Report DOM and page Resource Timing show no external report resources, but this does not establish absence of all browser networking. Narrow rendering used a real 390 CSS-pixel iframe viewport; file-origin policy prevented reading the child viewport via parent JavaScript. The screenshot confirms responsive layout; this is not a device test.

复现：先运行 `python -B examples/make_demo.py examples/v02-complete`（要求目标不存在），再运行 `python -B tests/render_fixtures.py`。手动打开 examples 下的诊断/比较 HTML 及 evidence/html/narrow.html、security.html。检查截图对应区域，禁止仅用静态标签检查替代显示验证。
