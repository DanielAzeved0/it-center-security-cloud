param(
    [Parameter(Mandatory = $true)]
    [string]$PfxPath,

    [Parameter(Mandatory = $true)]
    [System.Security.SecureString]$PfxPassword,

    [string]$AgentDirectory = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,

    [string]$TimestampServer
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PfxPath)) {
    throw "Certificate file not found: $PfxPath"
}

$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
    $PfxPath,
    $PfxPassword,
    [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable
)

$scriptsToSign = @(
    "itcenter-agent.ps1",
    "install-agent.ps1",
    "uninstall-agent.ps1"
)

foreach ($scriptName in $scriptsToSign) {
    $scriptPath = Join-Path $AgentDirectory $scriptName
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        throw "Agent script not found: $scriptPath"
    }

    $signParams = @{
        FilePath    = $scriptPath
        Certificate = $cert
    }
    if ($TimestampServer) {
        $signParams["TimestampServer"] = $TimestampServer
    }

    $result = Set-AuthenticodeSignature @signParams

    if ($result.Status -ne "Valid") {
        throw "Signing failed for $scriptPath. Status: $($result.Status) - $($result.StatusMessage)"
    }

    Write-Output "Signed: $scriptPath (Status: $($result.Status))"
}

Write-Output ""
Write-Output "All agent scripts signed successfully."
Write-Output "Re-run this script after any edit to $AgentDirectory before packaging a release."
Write-Output "Remember to also copy the matching .cer to agent-windows\itcenter-agent-signing.cer if the certificate changed."
