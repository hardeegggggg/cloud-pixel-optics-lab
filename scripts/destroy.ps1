[CmdletBinding()]
param(
    [string]$Profile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InfraRoot = Join-Path $ProjectRoot "infra"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Cdk = Join-Path $InfraRoot "node_modules\.bin\cdk.cmd"

$Answer = Read-Host "This deletes the stack and, by default, its S3 results. Type DESTROY to continue"
if ($Answer -cne "DESTROY") {
    throw "Destroy cancelled."
}

$CdkArgs = @("--app", "`"$Python`" app.py")
if ($Profile) { $CdkArgs += @("--profile", $Profile) }

Push-Location $InfraRoot
try {
    & $Cdk destroy "PixelOpticsBatchStack" --force @CdkArgs
} finally {
    Pop-Location
}

