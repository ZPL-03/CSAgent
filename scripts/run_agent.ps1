# 激活 AGENT 环境后运行入口，保证 Python 扩展依赖的 DLL 搜索路径完整。
param(
    [string]$CondaRoot = 'D:\anaconda3',
    [string]$Environment = 'AGENT',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArguments
)
$ErrorActionPreference = 'Stop'
$hook = Join-Path $CondaRoot 'shell\condabin\conda-hook.ps1'
if (-not (Test-Path -LiteralPath $hook -PathType Leaf)) {
    throw "Conda PowerShell hook 不存在：$hook"
}
. $hook
conda activate $Environment
if ($LASTEXITCODE -ne 0 -or -not $env:CONDA_PREFIX) {
    throw "无法激活 Conda 环境：$Environment"
}
$python = Join-Path $env:CONDA_PREFIX 'python.exe'
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = 'utf-8' }
if (-not $PythonArguments) { $PythonArguments = @('main.py') }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & $python -B @PythonArguments
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $code
