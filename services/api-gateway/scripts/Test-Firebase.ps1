$ErrorActionPreference = 'Stop'
if (-not $env:FIREBASE_PROJECT_ID -or -not (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS)) { throw 'Configuração Firebase ausente' }
go test ./... -count=1
if ($LASTEXITCODE -ne 0) { throw 'Testes falharam' }
go vet ./...
if ($LASTEXITCODE -ne 0) { throw 'Vet falhou' }
go build ./...
if ($LASTEXITCODE -ne 0) { throw 'Build falhou' }
