# Quick smoke tests for compiler v2 + agent doctor
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=== plan ===" -ForegroundColor Cyan
py -3 agent/agent.py plan

Write-Host "`n=== doctor ===" -ForegroundColor Cyan
py -3 agent/agent.py doctor
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== compile-v2 ===" -ForegroundColor Cyan
py -3 knit.py compile-v2 examples/hello.knit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=== compile v1 (src scaffold) ===" -ForegroundColor Cyan
py -3 knit.py compile examples/hello.knit
Write-Host "v1 exit (expect 1 until spec implemented): $LASTEXITCODE"

Write-Host "`n=== config test command ===" -ForegroundColor Cyan
py -3 -c "import sys; sys.path.insert(0,'agent'); from config_loader import load_config; print(load_config()['public_test_command'])"

Write-Host "`nSmoke tests done." -ForegroundColor Green
