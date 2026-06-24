#Requires -Version 5.1
<#
.SYNOPSIS
    Runs the GitHub file downloader script.
#>

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "setup_venv.ps1") -ProjectDir "gh_download"

$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw "Not inside a git repository!" }
$repoRoot = $repoRoot.Trim()

$downloadDir = Join-Path $repoRoot "gh_download"
$venvPython  = Join-Path $downloadDir ".venv\Scripts\python.exe"

Push-Location $downloadDir
try {
    Write-Host "Running downloader..."
    & $venvPython "downloader.py" @args
    if ($LASTEXITCODE -ne 0) { throw "Downloader script failed!" }
} finally {
    Pop-Location
}

Write-Host "Done."
