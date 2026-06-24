#Requires -Version 5.1
<#
.SYNOPSIS
    Hard-resets the repository, pulls the latest changes, re-runs the downloader,
    and rewrites the .DbLib connection string.
#>

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw "Not inside a git repository!" }
$repoRoot = $repoRoot.Trim()

Push-Location $repoRoot
try {
    Write-Host "Discarding local changes..."
    git reset --hard
    if ($LASTEXITCODE -ne 0) { throw "git reset failed!" }

    Write-Host "Pulling latest changes from remote..."
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw "git pull failed!" }
} finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot "download_files.ps1") @args

$dblibPath = Join-Path $repoRoot "Altium-Library.DbLib"
$dbPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "Altium-Library.db"))

if (-not (Test-Path -LiteralPath $dblibPath)) { throw "DbLib not found: $dblibPath" }

Write-Host "Patching .DbLib database path -> $dbPath"
$content = [System.IO.File]::ReadAllText($dblibPath)
$pattern = 'Database=[^;"]*Altium-Library\.db'
if ($content -notmatch $pattern) { throw "Could not find database path in $dblibPath" }
$content = [regex]::Replace($content, $pattern, { "Database=$dbPath" })

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($dblibPath, $content, $utf8NoBom)
