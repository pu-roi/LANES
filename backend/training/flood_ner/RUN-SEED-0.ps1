param([switch]$StartTraining)

$ErrorActionPreference = 'Stop'
$TaskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$TaskPython = Join-Path $TaskRoot 'backend/venv/Scripts/python.exe'
$TaskLauncher = Join-Path $PSScriptRoot 'manual_training.py'
if (-not (Test-Path -LiteralPath $TaskPython -PathType Leaf)) {
    throw 'The existing backend CLI interpreter is missing.'
}

if ($StartTraining) {
    Write-Host 'Starting primary seed 0 training after frozen-input verification.'
    & $TaskPython -B -I -u $TaskLauncher --start-training
} else {
    Write-Host 'Checking frozen inputs only. No training will start.'
    & $TaskPython -B -I -u $TaskLauncher
}
if ($LASTEXITCODE -ne 0) {
    throw "Seed 0 launcher stopped with exit code $LASTEXITCODE. Preserve the output and logs."
}
