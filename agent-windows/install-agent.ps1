param(
    [Parameter(Mandatory = $true)]
    [string]$ServerUrl,

    [Parameter(Mandatory = $true)]
    [string]$AgentApiKey,

    [int]$CheckinIntervalMinutes = 5,

    [string]$InstallPath = "C:\Program Files\ITCenterAgent",

    [string]$TaskName = "ITCenterAgent",

    [switch]$SkipConnectivityCheck,

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
$logsPath = Join-Path $InstallPath "logs"
$cachePath = Join-Path $InstallPath "cache"
$configPath = Join-Path $InstallPath "config.json"
$agentTarget = Join-Path $InstallPath "itcenter-agent.ps1"

if ((Test-Path -LiteralPath $InstallPath) -and -not $Force) {
    throw "InstallPath already exists. Re-run with -Force to update files: $InstallPath"
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
    log_path = $logsPath
    cache_path = $cachePath
    collect_inventory = $true
    collect_metrics = $true
    collect_security = $true
}

$config | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding UTF8

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$agentTarget`" -ConfigPath `"$configPath`""

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
