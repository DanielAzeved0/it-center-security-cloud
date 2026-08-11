param(
    [Parameter(Mandatory = $true)]
    [string]$PfxPath,

    [Parameter(Mandatory = $true)]
    [string]$CerPath,

    [Parameter(Mandatory = $true)]
    [System.Security.SecureString]$PfxPassword,

    [string]$Subject = "CN=IT Center Security Cloud Agent",

    [int]$ValidityYears = 10
)

$ErrorActionPreference = "Stop"

if (Test-Path -LiteralPath $PfxPath) {
    throw "PfxPath already exists, refusing to overwrite: $PfxPath"
}

if (Test-Path -LiteralPath $CerPath) {
    throw "CerPath already exists, refusing to overwrite: $CerPath"
}

$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -NotAfter (Get-Date).AddYears($ValidityYears) `
    -KeyExportPolicy Exportable `
    -KeyUsage DigitalSignature `
    -KeyAlgorithm RSA `
    -KeyLength 2048

Export-PfxCertificate -Cert $cert -FilePath $PfxPath -Password $PfxPassword | Out-Null
Export-Certificate -Cert $cert -FilePath $CerPath | Out-Null

# Trust the certificate on this machine so Sign-AgentScripts.ps1 (run here, by the
# maintainer) can produce a "Valid" Authenticode signature. Without this, Set-AuthenticodeSignature
# reports UnknownError because the root of a freshly generated self-signed certificate
# is not yet trusted anywhere. Monitored machines trust it separately via install-agent.ps1
# (LocalMachine\Root/TrustedPublisher, imported from the .cer at install time).
# certutil.exe is used instead of the X509Store .NET API because X509Store.Add() on the
# Root store can hang waiting on a Windows security prompt even when called programmatically.
& certutil.exe -user -addstore -f Root $CerPath | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "certutil -addstore Root failed with exit code $LASTEXITCODE"
}

Write-Output "Signing certificate created."
Write-Output "Subject: $Subject"
Write-Output "Thumbprint: $($cert.Thumbprint)"
Write-Output "Valid until: $($cert.NotAfter)"
Write-Output "PfxPath (private key): $PfxPath"
Write-Output "CerPath (public key): $CerPath"
Write-Output ""
Write-Output "IMPORTANT:"
Write-Output "- Store $PfxPath outside this repository, protected by a strong password."
Write-Output "- Never commit the .pfx file and never use it in CI/GitHub Actions."
Write-Output "- Copy the .cer file to agent-windows\itcenter-agent-signing.cer and commit only that file (public key, safe to distribute)."
Write-Output "- Run Sign-AgentScripts.ps1 with this .pfx before packaging any agent release."
