#Requires -Version 5.1
<#
.SYNOPSIS
    Pulls the latest changes, re-runs the downloader,
    and writes the local .DbLib with an absolute database path.
#>

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $changes = git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "git status failed!" }
    if ($changes) { throw "Local changes found. Commit or stash them before updating." }

    Write-Host "Pulling latest changes from remote..."
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw "git pull failed!" }
} finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot "download_files.ps1") @args

$dblibPath = Join-Path $repoRoot "Altium-Library.DbLib"
$localDblibPath = Join-Path $repoRoot "Altium-Library.local.DbLib"
$dbPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "Altium-Library.db"))

if (-not (Test-Path -LiteralPath $dblibPath)) { throw "DbLib not found: $dblibPath" }

Write-Host "Writing local .DbLib database path -> $dbPath"
$content = [System.IO.File]::ReadAllText($dblibPath)
$pattern = 'Database=[^;"]*Altium-Library\.db'
if ($content -notmatch $pattern) { throw "Could not find database path in $dblibPath" }
$content = [regex]::Replace($content, $pattern, { "Database=$dbPath" })

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($localDblibPath, $content, $utf8NoBom)
