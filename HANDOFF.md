# v0.4.0 开发交接 / Development handoff

2026-11-21。三项离线功能已实现；按本轮明确授权，完整本机套件106通过、0失败、0错误、0跳过，管理员进程退出0。实现者自测通过，待独立复核、托管CI和发布。

Implemented all three offline entries. The single complete user-authorized local suite passed 106/106 with no failures, errors or skips; process exit 0. Independent review, hosted CI and publication remain pending.

- 正式基线v0.3.0公开源码SHA256：`232a159d474ed1e65ddb4dba5f6727c5788e4c86011374db2fec98c1301ccf61`，195文件及194条原清单重新逐项匹配。
- 新增[第四版契约](docs/v04-contract.md)：validate、verify-support、history CSV；原诊断、比较、趋势HTML、求助包、fail-on保留。
- 本轮[完整授权实测](evidence/v04-tests.json)106/106通过；真实符号链接tag=0xA000000C、junction=0xA0000003，内容/后代访问审计均0。先前[普通权限结果](evidence/v04-tests-before-permission.json)101通过、5权限失败、0跳过仍单独保留，禁止拼接计数。
- 构建安装43步全部符合预期，wheel/sdist分别在干净环境安装、运行新旧入口并卸载；分发包独立交付，不放入源码ZIP。当前证据见[evidence/v04-package.json](evidence/v04-package.json)。
- [本轮HTML显示回归](docs/v04-html-validation.md)。390px iframe不代表真实手机。
- [第三版旧交接](docs/historical-v03-HANDOFF.md)及未标v04的既有证据属于历史，不能作为第四版结果。

Reproduce in a fresh source copy:

```powershell
python -B tests/run_tests.py --evidence evidence/review-v04-tests.json
python -B examples/make_v04_demo.py reports/review-v04-demo-new
python -B tests/package_check.py evidence/review-v04-package.json --artifacts-dir reports/review-v04-packages-new
python -B tests/check_artifacts.py
```

完整套件需要Windows、Node、.NET夹具编译器及真实文件/目录符号链接创建权限；不更改开发者模式、安全策略或真实配置。运行时产品不要求管理员。授权后须重跑完整套件并保留先前记录，不能拼接计数。

The full suite requires Windows, Node, the .NET fixture compiler and real symlink creation privileges. No developer-mode, security-policy or real-configuration changes. The product runtime does not require administrator privileges. After authorization, rerun the full suite and keep prior records separately.

未覆盖真实Claude发行包、WSL内部、真实手机、屏幕阅读器、抓包或物理断网。当前仅3.12本机开发验证；Windows Python3.11/3.14本轮托管CI须在终审另验。
