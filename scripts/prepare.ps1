[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

foreach ($CommandName in @("python", "node", "npm", "docker", "aws")) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $CommandName"
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install -e "$ProjectRoot[dev]"
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "infra\requirements.txt")

Push-Location (Join-Path $ProjectRoot "infra")
try {
    npm install
} finally {
    Pop-Location
}

& (Join-Path $ProjectRoot ".venv\Scripts\pixelcloud-generate.exe") `
    --output (Join-Path $ProjectRoot "data\cases.jsonl")
& $VenvPython -m pytest $ProjectRoot

Write-Output "Preparation complete. No AWS resources were created."

