param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(0, 1, 2)]
    [int]$Seed,
    [switch]$StartTraining
)

$ErrorActionPreference = 'Stop'
$TaskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$TaskPython = Join-Path $TaskRoot 'backend/venv/Scripts/python.exe'
$TaskLauncher = Join-Path $PSScriptRoot 'manual_training.py'
if (-not (Test-Path -LiteralPath $TaskPython -PathType Leaf)) {
    throw 'The existing backend CLI interpreter is missing.'
}

if ($StartTraining) {
    Write-Host "Starting seed $Seed training after frozen-input verification."
    & $TaskPython -B -I -u $TaskLauncher --seed $Seed --start-training
} else {
    Write-Host "Checking seed $Seed inputs only. No training will start."
    & $TaskPython -B -I -u $TaskLauncher --seed $Seed
}
if ($LASTEXITCODE -ne 0) {
    throw "Seed $Seed launcher stopped with exit code $LASTEXITCODE. Preserve output and logs."
}
