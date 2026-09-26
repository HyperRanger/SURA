#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Push-Location -Path (Split-Path -Parent $PSScriptRoot)

try {
    Write-Host "Running backend tests"
    python -m pytest tests
}
finally {
    Pop-Location
}