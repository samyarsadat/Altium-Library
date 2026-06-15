#Requires -Version 5.1
<#
.SYNOPSIS
    Sets up the database virtual environment for local development.
.NOTES
    If script execution is blocked, run via:
        powershell -ExecutionPolicy Bypass -File .\setup_dev.ps1
#>

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "setup_venv.ps1") -ProjectDir "database"
Write-Host "Done."
