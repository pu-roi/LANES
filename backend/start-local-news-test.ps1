$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.env.test.local')) {
    throw 'Missing .env.test.local. Follow docs/guides/local-news-replay.md.'
}
# Load the private test overrides before the encrypted shared configuration.
& dotenvx run -f .env.test.local -f .env -- .\venv\Scripts\python.exe -c 'from app.core.config import settings; from scripts.seed_local_news_replay import require_local_test_database; require_local_test_database(settings.DATABASE_URL); print("Confirmed local news test database")'
if ($LASTEXITCODE -ne 0) { throw 'Local database guard failed' }
& dotenvx run -f .env.test.local -f .env -- .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
exit $LASTEXITCODE
