> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# v0.1.0 发布审查 / Release review

日期 / Date: 2026-11-19, China time (UTC+08:00).

这是功能范围有限的源码首版，运行时只需 Python 标准库。MIT 许可证；npm/cmd-shim 8.0.0 模板保留 ISC 许可。官方规则及具体适用范围见 [rules](rules.md)，执行和隐私边界见 [privacy](privacy.md)。

## 测试归属 / Test provenance

| 执行者 / Reviewer | 结果 / Result | 证据 / Evidence |
| --- | --- | --- |
| gpt，返工自测 | 39 项：38 PASS, 1 SKIP, 0 FAIL/ERROR, exit 0 | [历史自测](../evidence/tests.json) |
| dsh，第二轮独立完整测试 | 39 项：38 PASS, 1 SKIP, 0 FAIL/ERROR, exit 0 | [独立测试](../evidence/review-dsh/tests.json) |
| dsh，用户授权单项补测 | 真实文件符号链接：1 PASS, 0 SKIP, 0 FAIL/ERROR | [单项管理员补测](../evidence/review-dsh/symlink-elevated.json) |
| MausBot，终审独立完整测试 | 39 项：38 PASS, 1 SKIP, 0 FAIL/ERROR, exit 0 | [终审复跑](../evidence/review-maus/tests.json) |

The dsh ordinary run and authorized supplemental run together provide passing records for all **39 distinct test cases**. This is **not** one complete run with 39 passes. Creating file symlinks requires a Windows privilege unavailable to ordinary runs on this host; the product itself does not require administrator access. No system settings were changed for the supplemental test.

## 两项返工复核 / Rework verification

损坏 npm 包装器实际退出 7，doctor 保持 unknown，不绕过损坏入口借包目标报通过。真实 NTFS junction 在访问后代元数据和内容前被拒绝。原始反例的独立结果见 [dsh edge evidence](../evidence/review-dsh/edge-results.json)。六份真实 cmd-shim 8.0.0 生成文件与 fixture 对照结果见 [shim generation](../evidence/review-dsh/shim-generation.json)。

MausBot reviewed discovery, process containment, report privacy, license notices and publication documents. Original 68-file hashes were checked before staging; Python implementation, tests and fixtures were copied byte-for-byte. Only public documentation and review evidence were prepared in a separate release folder. See [source integrity](../evidence/review-maus/source-integrity.json).

## 本机与离线边界 / Host and offline scope

本机中英文普通及禁止 Python 网络 API 的检查，均从干净临时目录启动；运行结果见 [终审主机记录](../evidence/review-maus/host/runs.json)。仅比较允许配置文件的内存字节及父进程环境，不读取认证或聊天记录。真实 Codex npm JS 入口识别到 0.169.0。当前 PATH 未找到 Claude，不据此判断整机未安装。

No WSL distribution was started. Denying Python network APIs does not establish physical disconnection or a firewall sandbox for third-party binaries.

## 未覆盖 / Remaining limits

Real Claude distributions, Codex native/WinGet/Scoop installations, real WSL distributions, other Windows/Python/architecture combinations, physical disconnection, wheel/pip installation and hosted CI have not been validated. Hard links, malicious concurrent replacement, publisher signatures and full effective configuration evaluation are outside the guarantee. The file-symlink case **has** been supplementally tested; do not list it as never tested.

本地旧样例和含工作目录的内部交接不进入公开包；公开示例使用合成数据，主机证据仅保留脱敏字段。发布校验清单见 [SHA256SUMS](../SHA256SUMS.txt)。
