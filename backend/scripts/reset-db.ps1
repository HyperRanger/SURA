#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Write-Host "Recreating local Postgres via docker-compose and running migrations"
docker compose -f backend/docker-compose.yml down -v
docker compose -f backend/docker-compose.yml up -d
Start-Sleep -Seconds 5
.
Write-Host "Running migrations"
pwsh -NoProfile -Command "./backend/scripts/migrate.ps1"
