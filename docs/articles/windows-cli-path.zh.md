# Windows 上 Claude / Codex 明明装了却找不到：先查终端选中了哪个入口

[English](windows-cli-path.en.md)

安装器显示成功，新的 PowerShell 却提示找不到 `claude`；另一个窗口能运行，编辑器里的终端又不行。这时，值得先确认两件事：**出问题的进程能看见哪个目录，它实际选中了哪个命令。**

下面是一套可以手动执行的排查顺序，最后附上我们开发的开源工具 Windows AI Doctor，用来把观察保存成报告，并比较处理前后的变化。本文的前后对照是 **SIMULATED（模拟案例）**，不代表真实用户事故或某台主机已修复。

## 先在出问题的终端里查

在那个无法启动工具的 PowerShell 窗口执行：

```powershell
Get-Command claude,codex -All -ErrorAction SilentlyContinue |
    Format-Table CommandType,Name,Source -AutoSize
where.exe claude
where.exe codex
```

如果只使用其中一个工具，另一个查不到是正常的。这里特意写 `where.exe`，避免与 PowerShell 的 `where` 别名混淆。`Get-Command -All` 可以列出同名命令及其优先顺序，也能让你看到同名的函数或别名。[微软命令查找说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/get-command?view=powershell-7.5)、[命令优先级说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_command_precedence?view=powershell-7.5)

先看结果属于哪一种：

| 观察 | 下一步核对 |
| --- | --- |
| 两种查询都找不到入口 | 核对实际安装目录是否出现在当前进程的 PATH；这还不能证明机器上没有安装 |
| 列出了不同目录的同名入口 | 核实各自来源、哪个入口优先；不要仅凭文件数量判断重复安装 |
| `Get-Command` 显示 Alias 或 Function | 先检查当前 PowerShell 的覆盖规则；PATH 报告不能代替这一步 |
| 独立终端正常，编辑器内失败 | 在两个窗口分别运行同一组查询，比较进程实际看到的环境 |

同一份 npm 安装可能提供 `.cmd`、`.ps1` 等多个入口，它们不等于多份安装。即使存在不同安装来源，也需要确认是否影响了当前命令，才决定如何整理。

## 为什么改过 PATH，旧窗口还看不见

查看当前窗口的这两项就够了：

```powershell
$env:PATH -split ';'
$env:PATHEXT
```

Windows 上的进程有自己的环境，子进程会继承父进程的环境。持久 PATH 改过之后，已经运行的编辑器仍可能把先前的环境交给新开的集成终端。因此，比较时要记录是哪个窗口；需要刷新环境时，完整退出并重新启动编辑器，再复查其中的终端。[微软环境变量说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-7.5)

手动处理的顺序是：确认你打算保留的官方安装来源和入口目录，在 Windows 的用户环境变量界面检查该目录，再重新打开相关应用，重跑上面的命令。对已经确认是旧安装的入口，按原安装方式的官方卸载步骤处理。先解决具体冲突，一次改一项，方便判断哪次修改起了作用。

如果实际运行的是 WSL 里的 shell，就在对应 Linux 环境检查。Windows 侧看见 WSL 启动器，不代表已经检查了发行版内部的 `claude` 或 `codex`。

## 把观察留成一份报告

需要向别人求助或比较处理前后状态时，可以用 [Windows AI Doctor](https://github.com/matchben3-commits/windows-ai-doctor)。我们参与开发了这个项目；它检查有限的本地线索，提供手动建议，并导出中文或英文报告。

下面使用包含 `venv` / `pip` 的常规 Python 3.11+ 发行版，在独立虚拟环境安装固定的 v0.6.0 Release wheel。安装需要联网；本节诊断使用 `--no-version`，不启动 Claude、Codex 或 Node。安装来源是 GitHub Release，而非 PyPI；附件校验和见 [v0.6.0 下载页](https://github.com/matchben3-commits/windows-ai-doctor/releases/tag/v0.6.0)。

```powershell
python -m venv .wad-venv
.\.wad-venv\Scripts\python.exe -m pip install --no-deps https://github.com/matchben3-commits/windows-ai-doctor/releases/download/v0.6.0/windows_ai_doctor-0.6.0-py3-none-any.whl
.\.wad-venv\Scripts\python.exe -m windows_ai_doctor --no-version --lang zh --format all --output-dir .\reports\before
```

打开本地的 `reports\before\report.zh.html`，或者把 `report.zh.md` 当作文字报告阅读。目录需要使用新的名字；已有同名报告不会被覆盖。只查 Claude 时可在诊断命令中加 `--tools claude`。

如果解释器提示缺少 `venv`，它可能是精简发行版；可改用常规 Python，或从上述 Release 下载源码 ZIP，在解压目录用 `python .\doctor.py` 替代下文的 `.\.wad-venv\Scripts\python.exe -m windows_ai_doctor`，其余诊断参数相同。

先看 `claude.path` / `codex.path`：安装组数量、PATH 候选、扫描是否受限。报告使用 `<PATH:1>` 这样的代号，真实路径仍要在本机通过前面的命令核对。代号在不同报告之间不代表同一个目录。

**SIMULATED：下面三行是为解释检查范围设计的情形。**

| 情形 | `claude.path` | 安装组数量 | 能说明什么 |
| --- | --- | --- | --- |
| 当前 PATH 没有入口 | `warn` | 0 | 在检查范围内没有选出入口 |
| 当前 PATH 有一个可检查的入口组 | `pass` | 1 | 该 PATH 检查通过，CLI 本身仍需验证 |
| 当前 PATH 有两个独立入口组 | `warn` | 2 | 需要人工确认哪个入口应当生效 |

这些状态不是“整台机器健康”的评级。`--no-version` 会跳过版本查询；`unknown` 是无法判断；`skipped` 是没有检查。路径涉及扫描限制时，也不能据此得出完整结论。工具的 PATH 模型不包含当前 PowerShell 的别名、函数和执行策略。

## 手动处理后，再用同样的范围复查

保留第一份 JSON，在修改后重新打开的终端中运行：

```powershell
.\.wad-venv\Scripts\python.exe -m windows_ai_doctor --no-version --lang zh --baseline .\reports\before\report.zh.json --fail-on regression --format all --output-dir .\reports\after
```

使用同一台机器、相同工具选择和相同检查范围，比较才有意义。这个命令把有限观察的差异放进新报告；`--fail-on regression` 只对扫描未受限的 `pass → warn`、`pass → error`、`warn → error` 返回 1。返回 0 表示没有命中所选退出条件，仍可能有原先就存在的告警。参数或导出失败返回 2。

例如，上表的“0 组变 1 组”可以说明 PATH 检查由 `warn` 变为 `pass`，不能证明账号登录、网络访问和实际任务都正常。最后仍要在原来出问题的终端里启动工具，重试原任务。Claude 可启动后，还可以运行官方的 `claude doctor` 查看安装和设置诊断。[Claude 官方验证步骤](https://code.claude.com/docs/en/setup#verify-your-installation)

## 求助时，什么反馈最有用

项目不会自动上传报告；报告不导出配置值和原始命令输出，分享前仍请自行审阅。诊断也不会替你安装、卸载或自动修复。若移除 `--no-version`，诊断会尝试运行已识别的版本入口；这不构成对第三方程序的强制网络隔离。

如果愿意反馈，请在 [项目 issue](https://github.com/matchben3-commits/windows-ai-doctor/issues) 写清：在哪种终端失败、期待发生什么、相关检查编号和状态、手动处理后有什么变化。无需粘贴全部环境变量或个人目录。尤其欢迎“报告说能找到，但实际仍启动不了”的情况，它能帮助我们判断哪些检查还不够。

项目地址：[matchben3-commits/windows-ai-doctor](https://github.com/matchben3-commits/windows-ai-doctor)。需要以后排障时再找到它，可以收藏仓库。

---

适用版本：Windows AI Doctor v0.6.0。官方参考页面核对日期：2026-11-22（北京时间）。示例情形为 SIMULATED；没有使用真实用户反馈或虚构成功率。
