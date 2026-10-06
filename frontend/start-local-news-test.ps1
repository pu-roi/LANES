$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\node_modules\.bin\dotenvx.cmd run -f .env.local -- .\node_modules\.bin\next.cmd dev --webpack -H 127.0.0.1
exit $LASTEXITCODE
