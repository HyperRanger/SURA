#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Push-Location -Path (Split-Path -Parent $PSScriptRoot)

try {
	Write-Host "Recreating local Postgres via docker-compose and running migrations"
	docker compose -f docker-compose.yml down -v
	docker compose -f docker-compose.yml up -d --wait db

	Write-Host "Running migrations"
	& (Join-Path $PSScriptRoot "migrate.ps1")
}
finally {
	Pop-Location
}
