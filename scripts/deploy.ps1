[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$AccountId,
    [Parameter(Mandatory = $true)][string]$Region,
    [string]$Profile,
    [switch]$SkipBootstrap,
    [int]$MaxVcpus = 16
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$InfraRoot = Join-Path $ProjectRoot "infra"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Run scripts\prepare.ps1 first."
}
if (-not (Test-Path -LiteralPath (Join-Path $InfraRoot "node_modules\.bin\cdk.cmd"))) {
    throw "CDK CLI is missing. Run scripts\prepare.ps1 first."
}
if ($MaxVcpus -lt 1 -or $MaxVcpus -gt 256) {
    throw "MaxVcpus must be between 1 and 256."
}

$AwsArgs = @()
if ($Profile) {
    $AwsArgs += @("--profile", $Profile)
}
aws sts get-caller-identity @AwsArgs | Out-Null

$Cdk = Join-Path $InfraRoot "node_modules\.bin\cdk.cmd"
$CdkArgs = @("--app", "`"$VenvPython`" app.py", "--context", "maxVcpus=$MaxVcpus")
$ProfileArgs = @()
if ($Profile) {
    $CdkArgs += @("--profile", $Profile)
    $ProfileArgs += @("--profile", $Profile)
}

Push-Location $InfraRoot
try {
    if (-not $SkipBootstrap) {
        & $Cdk bootstrap "aws://$AccountId/$Region" @ProfileArgs
    }
    & $Cdk synth --strict @CdkArgs
    & $Cdk diff @CdkArgs

    $Answer = Read-Host "Deploy the resources shown above? Type DEPLOY to continue"
    if ($Answer -cne "DEPLOY") {
        throw "Deployment cancelled."
    }
    & $Cdk deploy "PixelOpticsBatchStack" --require-approval broadening @CdkArgs
} finally {
    Pop-Location
}

Write-Output "Infrastructure deployed. Run scripts\submit.ps1 to upload cases and submit the array job."

