# v0.5.0 开发交接 / Development handoff

2026-11-21。第五版新增 compare CSV、19 项稳定检查目录及诊断输入 JSON Schema。gpt 负责集成，cursor 共同实现目录、文档与联调；dsh 独立复核，MausBot 终审、托管 CI 与发布。独立复核、托管 Windows Python 3.11/3.14 CI 与正式发布仍待完成。

v0.5 adds comparison CSV, a fixed 19-check catalog and a diagnosis-input JSON Schema. gpt integrated the release; cursor contributed the catalog, documentation and integration checks. Independent review, hosted Windows Python 3.11/3.14 CI and publication remain pending.

## 本轮完整套件 / Current complete suite

本轮在用户已授权的单次临时管理员进程中实跑 **138 项唯一测试，138 PASS、0 FAIL、0 ERROR、0 SKIP，真实进程退出 0**；保留全部 106 项旧测试。运行时及测试 Python 源码前后哈希一致，合成临时夹具已清空。完整逐项结果见 [v05-tests.json](evidence/v05-tests.json)。此前普通权限局部结果单独记录，不与本轮拼接。

One user-authorized administrator process completed **138 unique tests: 138 PASS, 0 FAIL, 0 ERROR, 0 SKIP; actual exit 0**, including all 106 existing cases. Python sources were unchanged across the run and generated temporary fixtures were removed. The per-case record is linked above. Earlier focused runs are separate records.

真实链接包含原有 5 项必需 symlink 及 compare CSV OLD/NEW 文件与祖先目录 4 项，tag 为 `0xa000000c`；全部 junction 回归同时执行，tag 为 `0xa0000003`。新用例的目标内容读取及祖先链接后代访问尝试均为 0。只操作合成夹具，未改开发者模式、安全策略或真实配置。

The nine required real symlink cases and all junction regressions ran. The new comparison cases recorded zero target-content reads or descendant access. Only synthetic fixtures were used; no developer-mode, security-policy or real-configuration changes were made.

## 入口与边界 / Entry points and bounds

- compare CSV：12 个固定 ASCII 列，UTF-8 BOM/LF，只输出变化项；缺失、0、false 可区分；中英正文逐字节相同，任意输入文字不进入单元格。
- catalog：默认 Markdown，支持 md/json/both；JSON 的 `purpose`/`limitation` 各保留 `zh`/`en` 对象，Markdown 按语言选文；19 ID、3 项 project_only、32 参数上限、确定性与离线审计均覆盖。
- schema：draft 2020-12，语言无关、无外部引用；按 dsh 2026-11-21 裁定采用单向一致，`--validate` 是唯一接受权威。非数字版本接受但不投影、非 `.path` 上的组数和扫描字段忽略、数学整数与整数 JSON 令牌的预期差异均有明确测试；见[第五版契约](docs/v05-contract.md)。

Comparison CSV uses twelve fixed columns and safe projected values. Catalog JSON preserves both languages in each purpose/limitation object. Schema follows the adjudicated one-way compatibility rule: parser acceptance implies schema acceptance, while the schema may accept more. `--validate` is the sole acceptance authority.

## 构建、示例与显示 / Packaging, examples and display

两个发行包的本轮构建、干净安装、新旧入口和卸载记录保存为 `evidence/v05-package.json`；逐步实际退出码与预期退出码、包哈希以该执行记录为准。源码根不保留分发成品，构建依赖只进入临时环境。

The current build/install record is `evidence/v05-package.json`, containing actual and expected step exits and both artifact hashes. Distribution files stay outside the source tree and build dependencies use temporary environments.

可复跑合成示例见 [examples/v05/runs.json](examples/v05/runs.json)，不是主机诊断。双语 HTML 的桌面、390 CSS px、固定 ID/第 20 次同屏及键盘实际横滚显示记录见 [v05-html-validation.md](docs/v05-html-validation.md)。这不是物理手机、屏幕阅读器或抓包验收。

```powershell
python -B tests/run_tests.py --evidence evidence/review-v05-tests.json
python -B tests/package_check.py evidence/review-v05-package.json --artifacts-dir reports/packages-new
python -B examples/make_v05_demo.py reports/v05-demo-new
python -B tests/check_artifacts.py
```

完整套件需要 Windows、Node、.NET 夹具编译器及真实链接创建权限。权限缺失须阻塞验收，不能跳过必需用例。旧 v0.1–v0.4 证据只代表历史；真实 Claude 发行包、WSL 内部、物理手机、屏幕阅读器及抓包未覆盖。未进行本轮 GitHub 写入或发布。

The complete suite requires Windows, Node, the .NET fixture compiler and real-link creation rights; missing rights block acceptance. Earlier-version evidence is historical. Real Claude distributions, WSL internals, physical phones, screen readers and packet capture are outside this local verification. No v0.5 GitHub write or publication has occurred.
