param([switch]$Current)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$configurationPath = Join-Path $PSScriptRoot 'public/news-simulation.local.json'
if ($Current) {
    if (Test-Path -LiteralPath $configurationPath) { Remove-Item -LiteralPath $configurationPath }
    Write-Host 'Normal data restored on port 3000. Reload open LANES pages.'
    return
}

$listener = Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue
$previousConfiguration = if (Test-Path -LiteralPath $configurationPath) { [System.IO.File]::ReadAllText($configurationPath) } else { $null }
if ($listener) {
    # Verify this checkout's server before reusing it; never select another port.
    try {
        [System.IO.File]::WriteAllText($configurationPath, '{"mode":"persisted","port":"3000"}')
        $existing = Invoke-RestMethod -Uri 'http://localhost:3000/news-simulation.local.json' -TimeoutSec 20
        if ($existing.mode -ne 'persisted' -or $existing.port -ne '3000') { throw 'Unexpected local configuration' }
    } catch {
        if ($null -ne $previousConfiguration) { [System.IO.File]::WriteAllText($configurationPath, $previousConfiguration) }
        else { Remove-Item -LiteralPath $configurationPath }
        throw 'Port 3000 is occupied by another server. Stop it before starting LANES reconstruction.'
    }
    Write-Host 'Reconstruction enabled on the existing port 3000 server. Reload open LANES pages.'
    return
}

# Explicit mode survives task completion. Use Current to restore normal data.
[System.IO.File]::WriteAllText($configurationPath, '{"mode":"persisted","port":"3000"}')
$previousDistDir = $env:NEWS_SIMULATION_DIST_DIR
try {
    $env:NEWS_SIMULATION_DIST_DIR = '.next-news-simulation'
    & node .\node_modules\@dotenvx\dotenvx\src\cli\dotenvx.js run -f .env.local -- node .\node_modules\next\dist\bin\next dev --webpack -H 0.0.0.0 -p 3000
    if ($LASTEXITCODE -ne 0) { throw 'Reconstruction frontend exited with an error' }
} finally {
    $env:NEWS_SIMULATION_DIST_DIR = $previousDistDir
}
