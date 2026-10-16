[CmdletBinding()]
param(
    [string]$Profile,
    [string]$Region
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Arguments = @(
    (Join-Path $PSScriptRoot "aws_status.py"),
    "--manifest", (Join-Path $ProjectRoot "deployment\last-run.json")
)
if ($Profile) { $Arguments += @("--profile", $Profile) }
if ($Region) { $Arguments += @("--region", $Region) }

& $Python @Arguments

