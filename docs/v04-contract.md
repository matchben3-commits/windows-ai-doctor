# v0.4 离线输入与导出契约 / Offline input and export contract

本轮三个入口沿用标准库、有界读取及从盘符根到文件逐级拒绝链接/重解析点的策略。只读取明确输入，不运行诊断器、外部命令、WSL、网络或注册表查询，不访问输入文字中的路径，不自动分享。并发恶意替换与硬链接身份不在此路径检查模型内。

These three entries use the standard library and bounded local input reads, rejecting links/reparse points root to leaf. They do not run diagnosis, commands, WSL, network or registry queries, follow embedded paths, or share anything. Concurrent hostile path replacement and hard-link identity are outside this path-check model.

## 模式、格式与退出 / Modes, formats and exits

诊断、compare、history、support、validate、verify-support六种模式互斥；派生模式拒绝显式诊断参数和fail-on，包括显式默认值、等号参数；参数不能缩写。

Diagnosis, compare, history, support, validate and verify-support are mutually exclusive. Derived modes reject explicit diagnostic options and fail-on, including defaults and equals syntax. Abbreviated options are disabled.

| 模式 / Mode | 格式 / Formats | 文件前缀 / Stem |
| --- | --- | --- |
| validate | both (默认/default), md, json | validation |
| verify-support | both (默认/default), md, json | support-verification |
| history | both, md, json, html, all, csv | history |

both始终MD+JSON，all始终MD+JSON+HTML，CSV必须单独选择。文件为`前缀.zh/en.扩展名`。无输出目录时both输出MD，json只输出JSON，csv只输出CSV；CSV写入目录时stdout为空。排他创建文件，碰撞退出2且保留旧文件，失败或中断只清理本次已创建文件。校验成功退出0，即使输入诊断含error；任何输入、核验或导出失败2，中断130。失败只输出固定提示，不回显原始路径、内容或异常。

both remains MD+JSON and all remains MD+JSON+HTML; CSV is explicit and separate. Files are `stem.zh/en.extension`. Without an output directory, both emits Markdown, json emits JSON alone and csv emits CSV alone. CSV directory exports leave stdout empty. Exclusive file creation preserves existing files; a collision exits 2. Failed/interrupted exports clean only files created in that attempt. Successful validation or verification exits 0 even if diagnosis checks contain errors. Input, verification and export failures exit 2; interruption exits 130. Failure messages never echo input paths, content or exceptions.

## validate

`--validate REPORT.json`接受v0.1/v0.2/v0.3/v0.4 schema1.0诊断输入，拒绝所有派生类型。共用现有2MiB、16层、20,000节点、32,768字符字符串、64条findings及数字解析限额；全输入拒绝重复键和非有限数。已知ID唯一、状态来自五态，数量/布尔观察类型受限；数字版本只保留`1.2.3`样式，其他版本文本忽略。未知字段忽略且不复制。

`--validate REPORT.json` accepts schema 1.0 diagnoses from v0.1–v0.4 and rejects every derived type. The existing 2 MiB, depth 16, 20,000 nodes, 32,768-character strings, 64 findings and numeric-parser bounds apply, including ignored fields. Duplicate keys and nonfinite numbers are rejected throughout. IDs are known and unique, states are one of the five fixed states, and count/boolean observations are typed and bounded. Only numeric versions such as `1.2.3` survive projection; other version text is ignored. Unknown fields are ignored and never copied.

结果`report_type=validation`，独立`valid=true`、`check_count`、重新计算的五态`summary`与固定范围提示。不是未知自由文本审核，不证明报告健康、完整或同一机器。空findings合法，明确检查数0，不称其健康或完整。

The result uses `report_type=validation`, `valid=true`, `check_count`, recomputed five-state `summary` and a fixed scope notice. It does not comprehensively audit free text or prove health, completeness or machine identity. Empty findings are accepted with a check count of zero.

## verify-support

`--verify-support BUNDLE.zip`在内存中校验，不解压落盘。只接受五个精确普通文件：support.json、summary.zh.md、summary.en.md、PRIVACY.txt、SHA256SUMS.txt。缺失、多余、重复、目录、穿越路径、绝对路径、反斜杠、NUL名、符号链接与其他特殊类型拒绝。

`--verify-support BUNDLE.zip` verifies in memory without extracting to disk. Exactly five regular members are accepted: support.json, summary.zh.md, summary.en.md, PRIVACY.txt and SHA256SUMS.txt. Missing, extra, duplicate, directory, traversing, absolute, backslash, NUL, symlink and other special members are rejected.

- ZIP最多4MiB；每成员最多2MiB；总解压最多4MiB。先检查所有成员头部的限额再解压，实际解压另有上限；不只相信声明长度。ZIP at most 4 MiB, each member at most 2 MiB, total uncompressed at most 4 MiB. All declared budgets are checked before decompression, and actual decompression is independently bounded.
- 仅stored/deflated；拒绝加密、不支持压缩、截断、头部不一致、成员重叠、实际长度不符及CRC错误。Only stored/deflated; encryption, unsupported compression, truncation, inconsistent headers, overlap, length and CRC errors are rejected.
- 清单恰好列出另外四成员，无重复/遗漏，64位十六进制SHA加双空格与精确文件名；逐个重算。Manifest lists exactly the other four members, each with a 64-digit hexadecimal SHA, two spaces and the exact name; all hashes are recomputed.
- support.json有相同有界JSON及重复键检查，必须schema1.0、report_type=support；校验已知唯一ID、五态、适用于该ID的数字版本/0–32整数/布尔字段，summary必须等于重新计算的五态数量。v0.3生成格式兼容，support仍不能回灌为诊断。support.json uses the same bounded JSON decoder and duplicate-key checks, requires schema 1.0 and report_type=support, validates unique known IDs, states and ID-specific numeric-version/count/boolean fields, and checks summary against recomputed counts. v0.3 bundles remain compatible; support is never accepted as a diagnosis.

结果`report_type=support_verification`只输出固定提示、成员数、归档字节和解压字节数，不输出包内文字。清单没有自签名：通过只证明结构和内部一致性，不能证明来源身份、机器现状、未经重新打包或包内任意文字不含私密信息。任意文字即使带敏感内容也不由此核验全面审核。

The `support_verification` result contains fixed text and member/archive/uncompressed byte counts, never bundle text. The manifest is not self-signed: success proves structure and internal consistency only, not source identity, machine state, absence of repackaging or privacy of arbitrary text.

## history CSV

`--history A.json B.json ... --format csv`接受2–20份诊断，遵守原输入限额和投影规则，按命令行顺序。UTF-8 BOM、标准库csv输出；固定ASCII列`sequence,check_id,status,version,installation_groups,scan_limited`。对全部输入中出现的已知ID取并集，每次各一行，先sequence后check_id排序；从未出现的ID不虚构检查。状态为五态或missing；缺失时其他观察空。无证据字段空，整数0与false保留，布尔值true/false。中英CSV内容相同。

`--history A.json B.json ... --format csv` accepts 2–20 diagnoses under the existing input and projection bounds, ordered by the command line. The standard csv writer emits a UTF-8 BOM and fixed ASCII columns: `sequence,check_id,status,version,installation_groups,scan_limited`. Each known ID appearing in any input has one row per input, sorted by sequence then check_id. IDs never observed are not invented. States are the five fixed values or missing. Missing checks have empty observations; absent evidence is empty, while integer zero and false are retained. Booleans are true/false; Chinese and English CSV values are identical.

不输出路径、原始时间、语言、原文、URL、未知字段或任意版本标签。单元格只来自固定枚举/已知ID/受限数字或布尔值，因此公式开头的自由文本不会进入输出，不依赖引号防公式。是有限观察投影，不计算健康评分，不推断修复或同一机器。

No paths, original timestamps, language, arbitrary text, URLs, unknown fields or version tags are exported. Cells come only from fixed enums/IDs and bounded numeric/boolean fields; formula-leading free text cannot enter cells. Safety does not depend on CSV quoting. This is a limited observation projection, not a health score or an inference of repairs or machine identity.

## 验证与历史 / Validation and history

本轮本机权限受限时，必需链接用例失败并阻塞验收，不能跳过后声称通过；授权后须重跑完整套件，保留先前失败记录。Windows Python3.11/3.14 CI必须本轮实跑，定义文件和历史证据不等于通过。源码根dist保持为空，构建成品可通过`tests/package_check.py EVIDENCE.json --artifacts-dir OUTSIDE_DIR`独立交付。

Unavailable local link privileges fail required cases and block acceptance. After authorization, rerun the full suite and retain prior records. Current Windows Python 3.11/3.14 CI must actually run; workflow definitions and historical evidence are not a pass. Keep source-root dist empty; packaging supports `tests/package_check.py EVIDENCE.json --artifacts-dir OUTSIDE_DIR` for separate artifacts.
