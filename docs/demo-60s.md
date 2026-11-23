# 60 秒演示脚本（录屏用）

总时长约 55–65 秒。合成案例，口播与字幕都要出现 **SIMULATED**。不出镜也可：只录终端 + 浏览器。

## 0:00–0:08 现象
画面：PowerShell 提示 `claude : The term 'claude' is not recognized`（可用本地伪造提示，勿冒充真实用户机）。
口播：Windows 上 Claude / Codex 明明装过，这个终端却找不到。

## 0:08–0:18 安装并跑诊断
画面：三行 quick start（venv → pip 装 Release wheel → `python -m windows_ai_doctor --no-version --lang en --format all`）。
口播：离线只读，不修系统、不登录、不调模型。

## 0:18–0:38 读报告
画面：打开 `report-en.html`，先滚到 **SIMULATED** 条幅，再停在 `claude.path` warn。
字幕：`installation_groups` / PATH 候选；真实路径仍要在本机用 `Get-Command` / `where.exe` 核对。
口播：先看 error，再看是不是重复安装组在抢 PATH。

## 0:38–0:50 手动处理 + 复查
画面：剪辑一句 `Get-Command claude,codex -All`，然后 `report-after-zh.html` 的 baseline 卡片（claude.path: warn→pass）。
口播：一次只改一项，新开终端再比。

## 0:50–1:00 收束
画面：演示页 CTA + GitHub 地址。
口播：完整样例和排障文在仓库；这是模拟演示，不是自动修复。

## 关键帧清单（导出 PNG）
1. `frame-01-symptom.png` — 找不到命令
2. `frame-02-cli.png` — 诊断命令
3. `frame-03-report.png` — 报告首屏含 SIMULATED（可用 `report-en.png`）
4. `frame-04-path-finding.png` — `claude.path` 卡片
5. `frame-05-baseline.png` — baseline 回归段
6. `frame-06-cta.png` — `index.html` 首屏

录屏完成后把 GIF/MP4 放进本目录的 `media/`（可选）；本资产包不强制附带视频文件。
