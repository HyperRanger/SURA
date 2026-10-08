#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Push-Location -Path (Split-Path -Parent $PSScriptRoot)

try {
	Write-Host "Running Alembic upgrade head"
	python -m alembic -c alembic.ini upgrade head
}
finally {
	Pop-Location
}
