[CmdletBinding()]
param(
    [string]$RunId,
    [string]$Profile,
    [string]$Region
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Arguments = @(
    (Join-Path $PSScriptRoot "aws_submit.py"),
    "--cases", (Join-Path $ProjectRoot "data\cases.jsonl"),
    "--manifest", (Join-Path $ProjectRoot "deployment\last-run.json")
)
if ($RunId) { $Arguments += @("--run-id", $RunId) }
if ($Profile) { $Arguments += @("--profile", $Profile) }
if ($Region) { $Arguments += @("--region", $Region) }

& $Python @Arguments

