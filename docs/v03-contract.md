# v0.3.0 离线派生与退出条件 / Offline derivatives and exit policies

## 输入契约 / Input contract

比较、趋势和求助包共用 `compare.load_report`：仅接受 UTF-8、schema 1.0、report_type 缺省或 diagnosis 的诊断输入，兼容 v0.1/v0.2/v0.3。comparison/history/support 派生类型一律拒绝，即使手工添加 findings。不是完整源报告校验器：只验证并提取下列有限观察，缺失的原文说明不会被补当成检查覆盖。

Known unique check IDs and pass/warn/error/unknown/skipped are required. Input summary, language, time, priorities, arbitrary text and paths are discarded. Counts are recalculated. Only numeric three-part versions (1–4 digits per part), installation_groups (integer 0–32), and scan_limited (boolean) survive with check IDs and states. Versions with free-form tags become null. Unknown IDs are rejected; unknown fields are ignored within the same structural budgets.

每份最多 2 MiB（含读取后溢出检测），嵌套最多16层、总节点20,000、单字符串32,768字符、findings最多64项。整数文本最多12字符、浮点文本最多32字符。重复JSON键、重复ID、非法状态/schema、非有限数、非UTF-8、非法JSON、超限输入拒绝。普通文件必须在固定本地盘；自根到叶逐级拒绝链接和重解析点，不探测被拒祖先之后的后代。不读取输入所指路径或URL。并发恶意替换和硬链接仍在边界之外。

## 多次趋势 / History

```powershell
python doctor.py --history first.json second.json third.json --lang zh --format all --output-dir reports/history-new
```

2–20份，21份和单份在读取前拒绝。最大编码输入总量40 MiB；投影后才累计保留，原JSON逐份释放。按参数先后顺序，重复同一个文件允许且作为不同次序；不按时间排序、不推断同一机器。用户自行确认环境及检查范围相同。每次状态数量、每项状态和有限观察，以及相邻新增/缺失/变化分别显示；无健康评分。

Unknown/skipped/missing/scan-limited observations never establish a fix. An error becoming pass is described only as this check passing now, and a limited scan keeps the uncertainty note. No broad claim of repair is made. Time, language, filenames and path-reference changes produce no trend.

JSON `report_type=history`；`snapshots` 含顺序/数量/检查数，`checks` 为按ID的观察序列，缺失为null，`transitions` 为相邻变化，顶层summary仅为最后一次数量。HTML有中英文顺序标签、状态文字和符号、固定颜色、可键盘聚焦的横向表格。输出 `history.LANG.md/json/html`，both默认MD+JSON，all为三种；stdout both/all为MD，单格式为该格式。

## 求助包 / Support bundle

```powershell
python doctor.py --support first.json --output-dir reports/support-new
```

只生成 `support-bundle.zip`，不自动发送。固定五成员：summary.zh.md、summary.en.md、support.json、PRIVACY.txt、SHA256SUMS.txt。SHA清单覆盖除自身外四个成员的UTF-8原字节。JSON `report_type=support`，只有程序版本、重算状态汇总和按ID重建的状态/有限观察，无输入时间、路径映射或原始JSON。不能再作为诊断比较输入。

This is a limited support summary, not an assertion of irreversible anonymity. Review it before sharing; diagnostic signals may be linkable. It has no original path mapping. It omits source report text, credentials, configuration, logs, environment values, screenshots and raw process output. No new diagnosis, command, registry/WSL query or network access occurs.

support必须指定输出目录，与format/lang/fail-on及所有诊断参数冲突。包使用排他二进制创建，已有包保留；写入失败/中断只删除本次新建的包，不删除其他文件。输出目录由调用者负责；不防御输出路径链接或并发替换。

## 退出条件 / Exit policy

```powershell
python doctor.py --no-version --fail-on error warn unknown --format all --output-dir reports/strict-new
```

仅诊断模式，允许error/warn/unknown一个或多个，按固定顺序去重；默认error。改变诊断完成后的退出判定，不改任何finding、优先级或故障定义。JSON增添兼容字段 `exit_policy={fail_on,triggered,matched,meaning}`；MD/HTML同时展示条件、触发状态与含义。unknown被选中不表示已确认故障。派生模式禁止fail-on，所有参数禁用缩写，任意额外位置参数拒绝。

Diagnosis: 1 if any selected state occurs, otherwise 0. Operational/argument/input/export failures: 2, interruption: 130, regardless of selected conditions. Completed comparison/history/support: 0, regardless of imported error counts. Diagnosis remains schema 1.0 with additive CLI policy metadata; old readers can ignore that field. Direct core Doctor API still returns observations without a CLI exit policy.

## 验证与历史 / Verification and history

当前第三版测试和构建证据由 [HANDOFF](../HANDOFF.md) 指定。所有v0.1/v0.2命名材料及旧 tests.json/build-install.json/artifact-check.json 是历史记录。第二版正式托管结果不算第三版CI通过。旧包、旧标签与旧开发目录不在本轮修改范围内。
