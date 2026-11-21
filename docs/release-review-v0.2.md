> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# v0.2.0 发布审查 / Release review

2026-11-20，北京时间。dsh 独立复核；MausBot 负责最终候选、公开材料和发布检查。本文件记录本地验证的范围；是否已经发布以 [版本页](https://github.com/matchben3-commits/windows-ai-doctor/releases) 为准，具体托管运行从版本说明链接。

## 功能与候选

新增单文件离线 HTML、schema 1.0 两份诊断报告的离线比较、按证据细化的中英文手动排障步骤。默认 MD+JSON、稳定检查 ID、无覆盖导出和原安全边界保留。运行时仍只有 Python 3.11+ 标准库。保留 v0.1 历史证据；不覆盖其日期、版本或测试含义。

MausBot 核实发布前 main 为 v0.1.0 提交 `aa99e952d77f418e7bbf932e6219c44707abd4f7`，没有后来提交。dsh 与实现者的 12 个运行时模块一致，终审不改产品源码；[模块 SHA](../evidence/review-v02-dsh/source-integrity.json)。公开文件只增补审查证据、发布说明和安装材料，清除内部目录引用。

## 独立复核的真实结果

| 检查 | 2026-11-20 结果 | 证据 |
| --- | --- | --- |
| 完整 56 项 | 54 通过、2 跳过、0 失败/错误，进程退出 0 | [逐项](../evidence/review-v02-dsh/initial-suite.json) |
| 额外独立检查 | 13 项通过，0 跳过/失败/错误，退出 0；包括状态转换矩阵、精确字节/深度/节点边界、输入隔离、真实 junction | [逐项](../evidence/review-v02-dsh/independent-audit.json) |
| 文件符号链接补测 | 今日 0 通过、2 跳过、退出 1，权限不足；昨日独立 2 通过、0 跳过、进程退出 0，五文件 SHA 与候选一致 | [今日](../evidence/review-v02-dsh/initial-links.json)、[昨日](../evidence/v02-authorized-links.json)、[昨日进程](../evidence/v02-authorized-process.json) |
| 源码包及 wheel | 23 步退出 0；从 sdist 构建 wheel；两个独立 venv 安装、控制台入口、中英三格式、比较、卸载和移除导入检查 | [安装记录](../evidence/review-v02-dsh/package-check.json) |
| 主机顺序检查 | 四次中英普通/禁止 Python 网络 API 均退出 0，后续检查配置字节和父环境不变 | [完整复跑](../evidence/review-v02-dsh/host-sequential.json) |

统计分开呈现：不把原套件、扩展检查或昨日链接补测相加称为一次全套通过。MausBot 的最终公开副本复跑见 [逐项测试](../evidence/review-v02-maus/tests.json) 与 [构建安装](../evidence/review-v02-maus/package.json)。

终审最初在较长工作目录中创建打包 venv 时 ensurepip 退出 1，打包检查退出 2；没有进入产品安装验证。保持候选源码不变，在本任务新建的短路径副本中重跑，23 个步骤全部通过；未更改 Windows 长路径策略，临时副本已清理。最终源码包和 wheel 来自这次成功构建。

## 初次配置变化与显示边界

dsh 初次 host_check 为配置字节比较不一致（四个诊断命令自身均退出 0），父环境不变。[初次记录](../evidence/review-v02-dsh/host-initial.json) 原样保留；随后 [逐次检查](../evidence/review-v02-dsh/host-investigation.json) 及完整顺序复跑均一致。首次变化来源未能归因，不能证明写入方，也不声称已审计整个桌面活动。版本探测使用临时 HOME、配置和缓存目录，但不是强制网络或凭据沙箱。

dsh 用挂载的内置 Browser 实际打开当日合成 HTML：中文 1280×720、390 CSS px iframe、长文本/注入字符串及英文比较均可读，无横向溢出，活动 script/img/onerror 为 0；英文 error→pass 仅表示本次检查通过。原始截图和完整独立复核报告保留在本地交接包。开发者 11 月 19 日的 [显示记录及截图](html-validation.md) 继续保留历史归属。导航报告过被拦截的 Google 请求，报告文档 Resource Timing 为空；没有据此声称浏览器进程完全没有联网，也未做抓包或物理断网。窄视口是 iframe，不是手机硬件测试。

## 托管检查与限制

[Windows 工作流](../.github/workflows/windows.yml) 对 Python 3.11、3.14 和 Node 24 运行真实套件及两种发行包的构建安装。必须确认本次候选托管结果成功，再创建正式 v0.2.0 标签；[Actions](https://github.com/matchben3-commits/windows-ai-doctor/actions) 和版本说明提供运行结果。本地证据不替代托管结果，也不提前承诺托管文件链接用例具备权限。

未验证真实 Claude 发行包、真实 WSL 内部/运行发行版、所有 Windows 版本及架构、POSIX、物理断网或第三方程序强制隔离；不覆盖硬链接与并发恶意替换。不上传 PyPI，不修改用户配置或系统设置，不启动 WSL。

The independent ordinary suite recorded 54 passes and 2 permission skips. A separate 13-case audit passed; the two successful file-link cases belong to the prior-day same-source supplement. The first host configuration-byte mismatch remains unexplained; later per-run and full sequential comparisons matched. Hosted Windows 3.11/3.14 tests must succeed before tagging. No claim is made for real Claude packages, WSL internals, all architectures or physical network isolation.
