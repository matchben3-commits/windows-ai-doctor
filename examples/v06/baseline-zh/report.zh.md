# Windows AI Doctor

v0.7.0 · schema 1.0

2000-01-01T00:00:00+00:00

通过: 2 · 提醒: 1 · 异常: 1 · 无法判断: 2 · 未检查: 1

## 基线对比

请自行确认基线与本次诊断来自相同环境和检查范围。回归仅指未受扫描限制时 pass→warn、pass→error 或 warn→error 的固定状态转移，不等于已确认故障根因。新增、移除、未知和未检查均不代表修复。只比较状态、数字版本、安装组数量和扫描限制。

新增: 2 · 移除: 1 · 变化: 3 · 回归: 2 · 未变化: 2 · 新发现: 0

### claude.path — changed

pass → error

观察字段或状态变化。

**固定规则回归**

```json
{
  "installation_groups": {
    "before": 1,
    "after": 0
  }
}
```

### claude.version — added

— → pass

本次新增检查。

```json
{
  "version": {
    "before": null,
    "after": "2.3.4"
  }
}
```

### codex.path — changed

warn → unknown

无法判断、未再检查或扫描受限，不代表修复。

```json
{
  "scan_limited": {
    "before": false,
    "after": true
  }
}
```

### codex.version — changed

pass → warn

观察字段或状态变化。

**固定规则回归**

```json
{
  "version": {
    "before": "1.2.3",
    "after": "1.2.4"
  }
}
```

### wsl.internal — added

— → skipped

本次新增检查。

```json
{}
```

### wsl.running — removed

pass → —

本次未包含，未再检查。

```json
{}
```

## 退出条件

所选状态：regression；触发状态：regression；达到所选退出条件：是. 达到所选退出条件仅表示出现选中状态；无法判断不等于已确认故障。操作失败退出2，中断130。 回归仅指未受扫描限制的固定状态转移，不等于已确认故障根因。 新发现仅指相对基线 added 的 error/warn（排除扫描受限的 path），不等于已确认故障根因。

路径使用代号，原始映射未保存；语法通过不代表服务可用。

## 优先处理（异常 → 提醒 → 无法判断）

claude.path, codex.version, codex.path, scope.unchecked

## system.platform — 通过

预设合成观察，不代表主机状态。

```json
{}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## claude.path — 异常

预设合成观察，不代表主机状态。

```json
{
  "installation_groups": 0,
  "scan_limited": false
}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## codex.version — 提醒

预设合成观察，不代表主机状态。

```json
{
  "version": "1.2.4"
}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## codex.path — 无法判断

预设合成观察，不代表主机状态。

```json
{
  "installation_groups": 1,
  "scan_limited": true
}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## claude.version — 通过

预设合成观察，不代表主机状态。

```json
{
  "version": "2.3.4"
}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## scope.unchecked — 无法判断

预设合成观察，不代表主机状态。

```json
{}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。

## wsl.internal — 未检查

预设合成观察，不代表主机状态。

```json
{}
```

建议：自行核对检查范围。

复查：使用实际诊断另行复查。
