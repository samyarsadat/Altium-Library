#Requires -Version 5.1
<#
.SYNOPSIS
    Creates (if needed) a Python virtual environment for a project directory and
    installs its dependencies.
#>

param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectDir
)

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw "Not inside a git repository." }
$repoRoot = $repoRoot.Trim()

$projectPath = Join-Path $repoRoot $ProjectDir
if (-not (Test-Path $projectPath)) { throw "Project directory not found: $projectPath" }

$venvDir    = Join-Path $projectPath ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in $venvDir..."
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
}

Write-Host "Installing dependencies from $ProjectDir\requirements.txt..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }
& $venvPython -m pip install -r (Join-Path $projectPath "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }
