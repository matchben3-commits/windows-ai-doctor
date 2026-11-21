# v0.3.0 开发交接

三项功能已实现：2–20次离线趋势、白名单重建的双语求助ZIP、可选诊断退出条件。保持Python 3.11+和标准库运行时、稳定ID、默认MD+JSON及旧版诊断输入兼容。候选尚未发布；dsh独立复核和MausBot终审、托管CI仍是后续门槛。

## 本轮证据

- [完整逐项测试](evidence/v03-tests.json)：本地78项，76通过、2权限跳过、0失败/错误，真实进程退出0。两项跳过是配置文件符号链接及报告文件符号链接，未申请提权或更改开发者模式；真实NTFS junction回归正常执行。旧版补测不能算本轮通过。
- [三项功能合成样例](examples/v03/runs.json)：3次趋势、20次趋势、中英文退出条件及求助包；记录每次实际/预期退出码。run1–3是明确编写的合成观察，不是真实主机诊断；退出条件示例只使用临时空目录。
- 求助包测试实际解压固定五成员、CRC、四成员SHA清单及敏感标记；拒绝将support派生JSON重新输入。离线测试禁止Doctor、命令/网络入口及对嵌入路径的元数据访问。见test_v03逐项记录。
- [实际HTML显示核验](docs/v03-html-validation.md)：中文、英文、20列表格和390px真实iframe视口，保留末列与固定ID同时显示的截图。Browser报告过被阻止的Google访问，不据此声称整个浏览器无联网尝试。
- [构建安装记录](evidence/v03-package.json)：由package_check在本候选构建时生成，各步真实退出码及成品SHA在其中；本交接冻结以该记录exit_code=0为门槛。脚本从sdist构建wheel，分别在干净venv安装、验证隔离导入/版本、双语诊断/趋势、比较、求助包、fail-on退出1及卸载。
- [基线与变更](evidence/v03-baseline.json)、[交付静态检查](evidence/v03-artifact-check.json)、[当前逐文件SHA](SHA256SUMS.txt)。文件名含v0.1/v0.2、旧tests.json/build-install.json/artifact-check.json、历史SHA和[旧交接](docs/historical-v02-HANDOFF.md)仅代表原轮次，不代表第三版。

## 新入口与退出码

```powershell
python -B doctor.py --history first.json second.json third.json --format all --output-dir reports/history-new
python -B doctor.py --support first.json --output-dir reports/support-new
python -B doctor.py --no-version --fail-on error warn unknown --format all --output-dir reports/strict-new
```

诊断所选状态出现为1，否则0；默认error。参数/输入/操作/导出失败2，中断130优先。完成比较、趋势或求助包均0。fail-on不改检查状态，unknown仍是无法判断。所有选项禁用缩写。完整字段、大小、派生类型及冲突矩阵见 [第三版契约](docs/v03-contract.md)。

## 干净副本复核

```powershell
python -B tests/run_tests.py --evidence evidence/review-v03-tests.json
python -B examples/make_v03_demo.py reports/review-v03-demo-new
python -B tests/package_check.py evidence/review-v03-package.json
python -B tests/check_artifacts.py
```

使用新空目录复制冻结候选。构建脚本要求dist为空；在复核副本中保留候选dist至该副本之外，再使用空dist运行。使用完整Python含venv/ensurepip进行构建；嵌入版Python只用于标准库测试，不含venv。解释器的本机绝对路径和源码ZIP校验值在交给dsh的本地开发记录中，公开源码不携带用户目录。

构建依赖只进入任务临时builder，不安装系统依赖、不上传PyPI；每个安装环境都在脚本退出前卸载和清理。当前CI定义保持Windows/Python3.11及3.14，运行完整套件和扩展安装入口验证；本地Python3.12.10结果不能代替托管矩阵。

## 边界与接续

不修改旧版目录、用户真实配置、环境或系统策略，不启动WSL，不新建监控，不推送GitHub。输入只读固定本地普通文件，逐级拒绝链接/重解析点；派生输出不复制自由文本。输出路径由调用者负责；并发替换和硬链接不是完整安全边界。求助摘要仍可能被关联，须自行审阅分享。

未验证真实Claude发行包、真实WSL内部、其他操作系统、手机设备、屏幕阅读器、物理断网或第三方程序防火墙隔离。此开发交付也不声称第三版托管CI或Release已完成。dsh从冻结候选独立副本复核后，再交MausBot核对远端main/tag/Release及真实托管结果，避免重复发布，不force push、不移动旧标签。
