# Windows AI Doctor

[English](README.en.md) · v0.4.0 · Python 3.11+ · Windows 优先 · 运行时仅标准库

对 Codex CLI 和 Claude Code CLI 做本地有限体检：PATH 入口、重复安装线索、版本、入口所需运行时、配置语法及 Windows/WSL 可见状态。导出中英文 Markdown、JSON 和单文件离线 HTML，提供固定手动排障建议。默认只诊断，不安装、升级、修复、登录或调用模型 API。

## 第四版新增

- `--validate REPORT.json`：离线确认诊断输入可按已知字段与边界接受；重新计算数量，报告含error仍可有效。
- `--verify-support BUNDLE.zip`：在内存中核对固定成员、CRC、SHA及摘要一致性；不证明来源身份或任意文字的隐私。
- `--history ... --format csv`：UTF-8 BOM长表，只输出已知ID及有限状态/数字/布尔观察；缺失为missing，不推断修复。

```powershell
python .\doctor.py --validate first.json --format json
python .\doctor.py --verify-support .\reports\support-new\support-bundle.zip --lang en
python .\doctor.py --history first.json second.json --format csv --output-dir .\reports\csv-new
python .\examples\make_v04_demo.py .\reports\v04-demo-new
```

校验/核验支持both、md、json；csv只对history开放，不改变both/all。两种校验模式成功0、失败2、中断130；不运行新诊断。细节、空值及字节限额见[第四版契约](docs/v04-contract.md)。

## 第三版保留功能

- 多次体检趋势：汇总2–20份已有诊断，按输入顺序显示数量、每项状态和相邻变化。
- 求助包：按固定白名单重建中英文有限摘要及机器可读结果，生成带哈希清单的ZIP，由用户审阅和分享。
- 自定义退出条件：`--fail-on error warn unknown`，只改变本次诊断完成后的退出判定，不改变任何检查状态。

```powershell
python .\doctor.py --no-version --format all --output-dir .\reports\first
python .\doctor.py --history first.json second.json third.json --format all --output-dir .\reports\history-new
python .\doctor.py --support first.json --output-dir .\reports\support-new
python .\doctor.py --no-version --fail-on error warn unknown --format all --output-dir .\reports\strict-new
```

趋势和求助包只读明确输入，不扫描环境、不运行CLI/Node/WSL、不联网、不访问报告内路径。请自行确认趋势输入来自同一环境和相同检查范围，时间及路径代号不能证明身份。不计算健康评分；未知、未检查、缺失和扫描受限均不代表修复；通过只代表该项本次通过。

求助包是有限摘要，不保证任意诊断信号都无法关联，也无原始路径映射。ZIP含 summary.zh.md、summary.en.md、support.json、PRIVACY.txt、SHA256SUMS.txt；不含原报告文字、原JSON、配置、日志、环境值或截图，不自动发送。必须指定输出目录，与format/lang/fail-on及诊断参数冲突。详见 [第三版契约](docs/v03-contract.md)。

## 运行及安装

源码直接运行，无需管理员、pip或模型密钥：

```powershell
python .\doctor.py --help
python .\doctor.py --lang en --format json
python .\doctor.py --tools codex --project "D:\示例项目" --output-dir .\reports\project-new
python .\doctor.py --compare first.json second.json --lang zh --format all --output-dir .\reports\comparison-new
```

路径为示例，请替换为自己的文件。Python不在PATH时用已有Python 3.11+的绝对路径。也可在自己的虚拟环境运行 `python -m pip install <wheel文件>`，然后使用 `windows-ai-doctor` 同名入口。运行时无第三方依赖。

- `--tools codex claude` 默认两种；`--home` 覆盖诊断用户目录。CODEX_HOME/CLAUDE_CONFIG_DIR分别优先于默认.codex/.claude位置。
- `--project` 只增加显式项目根目录的固定配置文件，不向祖先遍历或计算最终合并配置。
- `--timeout` 为每次查询0.1–30秒，默认3秒；`--no-version` 跳过CLI和Node执行。
- `--wsl-list` 是另行允许的只读运行中发行版列表，即使加no-version也会执行；严格无外部命令时不要使用。
- `--lang zh|en`，`--format both|md|json|html|all`；默认both=MD+JSON，all=三种。无输出目录时both/all打印MD，单格式打印对应内容。
- 诊断文件名report.LANG.FORMAT，比较为comparison，趋势为history。已有同名输出不覆盖；中断/写入失败清理本次新文件。
- compare/history/support互斥，均禁止诊断参数和fail-on；support另禁止format/lang。参数缩写和额外位置参数拒绝。

## 状态和退出码

| 状态 | 意义 |
| --- | --- |
| pass | 此有限检查本次通过或存在可见信息 |
| warn | 入口未发现、多安装线索或受限扫描 |
| error | 支持的配置语法/根结构错误，或已识别JS入口的Node缺失/不满足范围 |
| unknown | 布局、版本、权限、编码或证据不足，不能确认为故障 |
| skipped | 不存在的可选项、未启用或范围外 |

诊断完成后，出现任意选中的fail-on状态退出1，否则0；默认仅error。参数/输入/诊断/导出失败始终2，中断130。完成的比较/趋势/求助包/报告校验/求助包核验退出0，与输入的error数量无关。报告中的exit_policy明示所选状态、实际触发状态和含义；将unknown设为失败不等于确认故障。

诊断JSON保留schema 1.0，CLI附加exit_policy。诊断导入模式接受v0.1/v0.2/v0.3/v0.4的schema 1.0诊断，拒绝comparison/history/support/validation/support_verification派生类型；只保留已知ID、状态、纯数字版本、安装组数量和扫描限制。重复键/ID、非法状态/schema、超限输入和链接文件拒绝。每份2 MiB、16层、20,000节点；趋势最多20份。任意源文字不复制进派生输出。

## 隐私与范围

不读认证、会话、聊天或.claude.json。固定配置只做语法检查（UTF-8，最多1 MiB），不输出配置键值、任意异常、原始命令输出或真实路径。原路径映射不保存，PATH代号不能跨报告识别机器。配置、入口、Node、包元数据及报告输入逐级拒绝符号链接/junction/重解析点，不访问其后代；不承诺防御硬链接或并发恶意替换。

只查询已识别入口，不执行shell包装器；原生格式识别不等于签名验证。版本查询用临时HOME和受限环境，Windows用Job Object清理进程树；第三方程序不是完整安全沙箱。检查器不联网，第三方程序仍可能绕过代理。配置语法通过不表示登录、API、服务或全部功能可用。WSL内部始终未检查，默认不启动WSL。

[隐私细节](docs/privacy.md) · [规则依据与产品探测边界](docs/rules.md) · [比较契约](docs/comparison.md) · [第三版契约](docs/v03-contract.md)

## 示例与验证

```powershell
python -B .\examples\make_v04_demo.py .\reports\v04-demo-new
python -B .\tests\run_tests.py --evidence .\evidence\review-v04-tests.json
python -B .\tests\package_check.py .\evidence\review-v04-package.json
```

生成器前3份是明确编写的合成观察，非真实主机诊断。样例：[中文趋势](examples/v04/history-zh/history.zh.html)、[英文趋势](examples/v04/history-en/history.en.html)、[20次趋势](examples/v04/history20-zh/history.zh.html)。构建检查要求完整Python含venv/ensurepip及空的成品目录；依赖仅进入临时构建环境。当前本地结果、显示证据和未覆盖项见 [HANDOFF](HANDOFF.md)。

原v0.1/v0.2/v0.3材料、旧tests.json/build-install.json和旧SHA清单是历史记录，不能视为第四版通过。本轮独立复核、托管Windows/Python 3.11/3.14 CI与发布须分别验收。

[MIT许可证](LICENSE) · [第三方声明](THIRD_PARTY_NOTICES.md)

第四版当前状态见[开发交接](HANDOFF.md)。未标v04的既有证据（包括v0.1/v0.2/v0.3）属于历史；本轮权限实测、独立复核、托管CI及发布须分别验收。
