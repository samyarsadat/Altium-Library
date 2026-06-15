#Requires -Version 5.1
<#
.SYNOPSIS
    Hard-resets the repository, pulls the latest changes, and re-runs the downloader.
.NOTES
    If script execution is blocked, run via:
        powershell -ExecutionPolicy Bypass -File .\update_lib.ps1
#>

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw "Not inside a git repository." }
$repoRoot = $repoRoot.Trim()

Push-Location $repoRoot
try {
    Write-Host "Discarding local changes (git reset --hard) ..."
    git reset --hard
    if ($LASTEXITCODE -ne 0) { throw "git reset failed." }

    Write-Host "Pulling latest changes from remote ..."
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw "git pull failed." }
} finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot "download_files.ps1") @args
