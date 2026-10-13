param(
    [Parameter(Mandatory=$true)][string]$DatabaseUrl,
    [Parameter(Mandatory=$true)][string]$ScenarioFile
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:DATABASE_URL = $DatabaseUrl
$env:ENVIRONMENT = 'development'
$env:LANES_NEWS_SCENARIO_FILE = $ScenarioFile
$env:LANES_NEWS_AUDITOR_PROVIDER = 'source_rules'
$env:LANES_NEWS_AUDITOR_MODEL = 'source-rules-v1'
$env:LANES_NEWS_AUDITOR_CONFIG_REVISION = 'source-rules-defense-20261013'
$env:VALHALLA_URL = 'http://127.0.0.1:8002'
& dotenvx run -f .env -- .venv/Scripts/python.exe -m scripts.run_news_source_demo --historical-replay
if ($LASTEXITCODE -ne 0) { throw 'Private historical demonstration failed; see the error above.' }
& dotenvx run -f .env -- .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
if ($LASTEXITCODE -ne 0) { throw 'Local source-validation backend exited with an error.' }
