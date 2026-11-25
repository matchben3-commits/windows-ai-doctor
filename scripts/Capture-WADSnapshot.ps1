<# Run in the original runspace. Query command metadata without invoking it.
   ProbeVersion separately requests a bounded, isolated query for a recognized launcher.
   The transient pipe contains only command/type/path. No function body, alias
   expansion, profile, arbitrary environment or raw output is read or saved. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('codex','claude')][string]$Command,
    [ValidateSet('working','failing','unspecified')][string]$SessionRole='unspecified',
    [ValidateSet('none','not_found','wrong_version','config_error','other','unspecified')][string]$Symptom='unspecified',
    [ValidateSet('success','failure','unverified')][string]$CommandResult='unverified',
    [switch]$ProbeVersion,
    [string]$Python='python',
    [string]$OutputDirectory
)
$captureKind = 'unknown'
$capturePath = $null
try {
    $captureInfo = Microsoft.PowerShell.Core\Get-Command -Name $Command -ErrorAction Stop
    switch ([string]$captureInfo.CommandType) {
        'Alias' { $captureKind = 'alias' }
        'Function' { $captureKind = 'function' }
        'Application' { $captureKind = 'application'; $capturePath = $captureInfo.Path }
        'ExternalScript' { $captureKind = 'external_script'; $capturePath = $captureInfo.Path }
    }
} catch [System.Management.Automation.CommandNotFoundException] {
    $captureKind = 'missing'
} catch {
    $captureKind = 'unknown'
}
$captureMetadata = @{command=$Command; kind=$captureKind; path=$capturePath} |
    Microsoft.PowerShell.Utility\ConvertTo-Json -Compress
$sourceEntry = Join-Path $PSScriptRoot '..\doctor.py'
$sourceModule = Join-Path $PSScriptRoot '..\windows_ai_doctor\__main__.py'
if ((Test-Path -LiteralPath $sourceEntry -PathType Leaf) -and (Test-Path -LiteralPath $sourceModule -PathType Leaf)) {
    $captureArguments = @('-I','-B',$sourceEntry)
} else {
    $installedPython = Join-Path $PSScriptRoot 'python.exe'
    if (-not $PSBoundParameters.ContainsKey('Python') -and (Test-Path -LiteralPath $installedPython -PathType Leaf)) {
        $Python = $installedPython
    }
    $captureArguments = @('-I','-B','-m','windows_ai_doctor')
}
$captureArguments += @('--capture', '--command', $Command,
    '--session-role', $SessionRole, '--symptom', $Symptom, '--command-result', $CommandResult, '--session-metadata-stdin')
if ($OutputDirectory) { $captureArguments += @('--output-dir', $OutputDirectory) }
if ($ProbeVersion) { $captureArguments += '--probe-version' }
$captureEncoding = $OutputEncoding
try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $captureMetadata | & $Python @captureArguments
} finally {
    $OutputEncoding = $captureEncoding
}
# Preserve LASTEXITCODE for a caller to inspect; do not exit its runspace.
