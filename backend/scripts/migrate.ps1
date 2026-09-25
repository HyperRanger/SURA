#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Push-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)
Push-Location ..

Write-Host "Running Alembic upgrade head"
python -m alembic -c backend/alembic.ini upgrade head

Pop-Location
Pop-Location
