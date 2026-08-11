param(
    [Parameter(Mandatory = $true)]
    [string]$ServerUrl,

    [Parameter(Mandatory = $true)]
    [string]$AgentApiKey,

    [int]$CheckinIntervalMinutes = 5,

    [string]$InstallPath = "C:\Program Files\ITCenterAgent",

    [string]$TaskName = "ITCenterAgent",

    [switch]$SkipConnectivityCheck,

    [switch]$SkipSignatureCheck,

    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-InstallInput {
    if (-not (Test-IsAdministrator)) {
        throw "Run this installer from an elevated PowerShell session."
    }

    if ([string]::IsNullOrWhiteSpace($ServerUrl)) {
        throw "ServerUrl is required."
    }

    $serverUri = $null
    if (-not [System.Uri]::TryCreate($ServerUrl, [System.UriKind]::Absolute, [ref]$serverUri)) {
        throw "ServerUrl must be an absolute URL."
    }

    $isLocalHttp = $serverUri.Scheme -eq "http" -and @("localhost", "127.0.0.1", "::1") -contains $serverUri.Host
    if ($serverUri.Scheme -ne "https" -and -not $isLocalHttp) {
        throw "ServerUrl must use HTTPS outside local development."
    }

    if ([string]::IsNullOrWhiteSpace($AgentApiKey)) {
        throw "AgentApiKey is required."
    }

    if ($CheckinIntervalMinutes -lt 1) {
        throw "CheckinIntervalMinutes must be greater than or equal to 1."
    }

    $serverUri
}

function Test-AgentServerConnectivity {
    param(
        [Parameter(Mandatory = $true)]
        [uri]$ServerUri
    )

    $hostName = $ServerUri.Host
    try {
        $addresses = [System.Net.Dns]::GetHostAddresses($hostName) |
            Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork } |
            ForEach-Object { $_.IPAddressToString }
    }
    catch {
        throw "ServerUrl host could not be resolved: $hostName. Configure DNS on this network before installing the agent."
    }

    if ($null -eq $addresses -or @($addresses).Count -eq 0) {
        throw "ServerUrl host resolved no IPv4 address: $hostName. Configure DNS on this network before installing the agent."
    }

    Write-Output "ServerUrl DNS resolved: $hostName -> $(@($addresses) -join ', ')"

    $port = if ($ServerUri.IsDefaultPort) {
        if ($ServerUri.Scheme -eq "https") { 443 } elseif ($ServerUri.Scheme -eq "http") { 80 } else { $ServerUri.Port }
    }
    else {
        $ServerUri.Port
    }

    $tcpClient = [System.Net.Sockets.TcpClient]::new()
    try {
        $connectTask = $tcpClient.ConnectAsync($hostName, $port)
        if (-not $connectTask.Wait(5000) -or -not $tcpClient.Connected) {
            throw "ServerUrl TCP connection failed: $hostName`:$port. Check firewall, DNS, or internet access before installing the agent."
        }

        Write-Output "ServerUrl TCP reachable: $hostName`:$port"
    }
    finally {
        $tcpClient.Dispose()
    }

    $baseUrl = $ServerUri.AbsoluteUri.TrimEnd("/")
    $healthUrl = if ($baseUrl -match "/api/v1$") {
        "$baseUrl/health"
    }
    else {
        "$baseUrl/healthz"
    }

    try {
        Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 10 -ErrorAction Stop | Out-Null
        Write-Output "ServerUrl health check passed: $healthUrl"
    }
    catch {
        throw "ServerUrl health check failed: $healthUrl. The agent endpoint must be reachable before installation. Details: $($_.Exception.Message)"
    }
}

function Get-AgentScheduledTaskExecutionPolicy {
    param(
        [switch]$SkipSignatureCheck
    )

    if ($SkipSignatureCheck) {
        return "Bypass"
    }

    return "AllSigned"
}

function Assert-AgentScriptSignature {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $signature = Get-AuthenticodeSignature -FilePath $Path
    if ($signature.Status -ne "Valid") {
        throw "Agent script is not signed with a valid certificate: $Path (status: $($signature.Status)). Run scripts\Sign-AgentScripts.ps1 before installing, or pass -SkipSignatureCheck for a local/dev install without code-signing enforcement (ADR-031)."
    }
}

function Install-AgentSigningCertificate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CerPath
    )

    if (-not (Test-Path -LiteralPath $CerPath)) {
        throw "Signing certificate not found: $CerPath. Run scripts\New-AgentSigningCertificate.ps1 and scripts\Sign-AgentScripts.ps1 first, or pass -SkipSignatureCheck for a local/dev install without code-signing enforcement (ADR-031)."
    }

    # certutil.exe is used instead of the X509Store .NET API because X509Store.Add() on the
    # Root store can hang waiting on a Windows security prompt even when called programmatically -
    # unacceptable for a silent, unattended install on a monitored machine.
    foreach ($storeName in @("Root", "TrustedPublisher")) {
        & certutil.exe -addstore -f $storeName $CerPath | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "certutil -addstore $storeName failed with exit code $LASTEXITCODE"
        }
    }
}

function Protect-AgentConfigFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $acl = Get-Acl -Path $Path
    $acl.SetAccessRuleProtection($true, $false)

    foreach ($existingRule in @($acl.Access)) {
        $acl.RemoveAccessRule($existingRule) | Out-Null
    }

    foreach ($identity in @("NT AUTHORITY\SYSTEM", "BUILTIN\Administrators")) {
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $identity,
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            [System.Security.AccessControl.AccessControlType]::Allow
        )
        $acl.AddAccessRule($rule)
    }

    Set-Acl -Path $Path -AclObject $acl
}

$serverUri = Assert-InstallInput

if ($SkipConnectivityCheck) {
    Write-Output "ServerUrl connectivity check skipped."
}
else {
    Test-AgentServerConnectivity -ServerUri $serverUri
}

$agentSource = Join-Path $PSScriptRoot "itcenter-agent.ps1"
if (-not (Test-Path -LiteralPath $agentSource)) {
    throw "Agent script not found: $agentSource"
}

$installerSource = Join-Path $PSScriptRoot "install-agent.ps1"
$uninstallerSource = Join-Path $PSScriptRoot "uninstall-agent.ps1"
$signingCertPath = Join-Path $PSScriptRoot "itcenter-agent-signing.cer"
$logsPath = Join-Path $InstallPath "logs"
$cachePath = Join-Path $InstallPath "cache"
$configPath = Join-Path $InstallPath "config.json"
$agentTarget = Join-Path $InstallPath "itcenter-agent.ps1"

if ((Test-Path -LiteralPath $InstallPath) -and -not $Force) {
    throw "InstallPath already exists. Re-run with -Force to update files: $InstallPath"
}

if ($SkipSignatureCheck) {
    Write-Output "Code-signing enforcement skipped (-SkipSignatureCheck). Scheduled task will use ExecutionPolicy Bypass (ADR-031)."
}
else {
    # Import the certificate before validating signatures: on a first-time install, the
    # certificate chain is not yet trusted on this machine, so Get-AuthenticodeSignature
    # would report NotTrusted even for a legitimately signed script.
    Install-AgentSigningCertificate -CerPath $signingCertPath
    Write-Output "Signing certificate imported into LocalMachine Root and TrustedPublisher."

    Assert-AgentScriptSignature -Path $agentSource
    Assert-AgentScriptSignature -Path $installerSource
    Assert-AgentScriptSignature -Path $uninstallerSource
}

New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
New-Item -ItemType Directory -Path $cachePath -Force | Out-Null

Copy-Item -LiteralPath $agentSource -Destination $agentTarget -Force
Copy-Item -LiteralPath $installerSource -Destination (Join-Path $InstallPath "install-agent.ps1") -Force
Copy-Item -LiteralPath $uninstallerSource -Destination (Join-Path $InstallPath "uninstall-agent.ps1") -Force

$config = [ordered]@{
    server_url = $ServerUrl.TrimEnd("/")
    agent_api_key = $AgentApiKey
    checkin_interval_minutes = $CheckinIntervalMinutes
    retry_max_attempts = 3
    retry_initial_delay_seconds = 2
    retry_max_delay_seconds = 15
    log_path = $logsPath
    cache_path = $cachePath
    log_max_size_kb = 5120
    log_max_backups = 3
    cache_retention_days = 30
    collect_inventory = $true
    collect_metrics = $true
    collect_security = $true
}

$config | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding UTF8

try {
    Protect-AgentConfigFile -Path $configPath
    Write-Output "config.json ACL restricted to SYSTEM and Administrators."
}
catch {
    Write-Output "Warning: failed to restrict config.json ACL: $($_.Exception.Message)"
}

$executionPolicy = Get-AgentScheduledTaskExecutionPolicy -SkipSignatureCheck:$SkipSignatureCheck

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy $executionPolicy -File `"$agentTarget`" -ConfigPath `"$configPath`""

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $CheckinIntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

Write-Output "IT Center Agent installed."
Write-Output "InstallPath: $InstallPath"
Write-Output "ConfigPath: $configPath"
Write-Output "TaskName: $TaskName"
Write-Output "ExecutionPolicy: $executionPolicy"
