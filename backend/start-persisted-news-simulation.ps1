$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.env.test.local')) {
    throw 'Missing private database configuration. Follow docs/guides/local-news-replay.md.'
}
# The launcher validates both configured and bound database targets before
# serving API routes. No live publisher/provider or pipeline run on startup.
& node ..\frontend\node_modules\@dotenvx\dotenvx\src\cli\dotenvx.js run -f .env.test.local -f .env -- .\venv\Scripts\python.exe -m scripts.serve_local_news_replay
if ($LASTEXITCODE -ne 0) { throw 'Private simulation backend exited with an error' }
