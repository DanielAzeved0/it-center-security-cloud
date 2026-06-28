param(
    [string]$AgentScriptPath = (Join-Path $PSScriptRoot "..\itcenter-agent.ps1")
)

$ErrorActionPreference = "Stop"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Assert-Percent {
    param(
        [double]$Value,
        [string]$Name
    )

    Assert-True -Condition ($Value -ge 0) -Message "$Name must be greater than or equal to 0."
    Assert-True -Condition ($Value -le 100) -Message "$Name must be less than or equal to 100."
}

. $AgentScriptPath

$cpuUsage = Get-AgentCpuUsage
$ramUsage = Get-AgentRamUsage
$diskUsage = Get-AgentDiskUsage
$payload = New-AgentCheckinPayload
$json = ConvertTo-AgentCheckinJson -Payload $payload
$jsonPayload = $json | ConvertFrom-Json
$capturedRequest = $null
$resendRequestCount = 0
$capturedResendRequests = @()
$mockOsRegistry = [pscustomobject]@{
    ProductName = "Windows 11 Pro"
    DisplayVersion = "23H2"
}

$mockProgramRegistry = @(
    [pscustomobject]@{
        DisplayName = "Google Chrome"
        DisplayVersion = "126.0"
        Publisher = "Google"
    },
    [pscustomobject]@{
        DisplayName = "Google Chrome"
        DisplayVersion = "126.0"
        Publisher = "Google"
    },
    [pscustomobject]@{
        DisplayName = "AnyDesk"
        DisplayVersion = "8.0"
        Publisher = "AnyDesk Software GmbH"
    }
)

$mockFirewallProfilesEnabled = @(
    [pscustomobject]@{ Name = "Domain"; Enabled = $true },
    [pscustomobject]@{ Name = "Private"; Enabled = $true },
    [pscustomobject]@{ Name = "Public"; Enabled = $true }
)

$mockFirewallProfilesDisabled = @(
    [pscustomobject]@{ Name = "Domain"; Enabled = $true },
    [pscustomobject]@{ Name = "Private"; Enabled = $false },
    [pscustomobject]@{ Name = "Public"; Enabled = $true }
)

$mockDefenderEnabled = [pscustomobject]@{
    AMServiceEnabled = $true
    AntispywareEnabled = $true
    RealTimeProtectionEnabled = $true
}

$mockDefenderDisabled = [pscustomobject]@{
    AMServiceEnabled = $true
    AntispywareEnabled = $true
    RealTimeProtectionEnabled = $false
}

$mockRdpDisabledRegistry = [pscustomobject]@{
    fDenyTSConnections = 1
}

$mockRdpEnabledRegistry = [pscustomobject]@{
    fDenyTSConnections = 0
}

$mockLocalAdmins = @(
    [pscustomobject]@{ Name = "DESKTOP\Administrator" },
    [pscustomobject]@{ Name = "DOMAIN\Daniel" },
    [pscustomobject]@{ Name = "DOMAIN\Daniel" }
)

$mockUsbDevices = @(
    [pscustomobject]@{
        Model = "Kingston DataTraveler"
        Manufacturer = "Kingston"
        SerialNumber = "USB123"
    }
)

$mockFailedLogins = @(
    [pscustomobject]@{ Id = 4625 },
    [pscustomobject]@{ Id = 4625 }
)

$validatedNewConfig = ConvertTo-AgentValidatedConfig -RawConfig ([pscustomobject]@{
    server_url = "https://itcenter-daniel.chickenkiller.com"
    agent_api_key = "new-key"
    checkin_interval_minutes = 5
    log_path = "C:\Program Files\ITCenterAgent\logs"
    cache_path = "C:\Program Files\ITCenterAgent\cache"
})

$validatedLegacyConfig = ConvertTo-AgentValidatedConfig -RawConfig ([pscustomobject]@{
    server_url = "http://127.0.0.1:8000/api/v1"
    api_key = "legacy-key"
    interval_minutes = 10
})

function Invoke-TestRequest {
    param($RequestParams)

    $script:capturedRequest = $RequestParams

    [pscustomobject]@{
        status = "success"
        message = "Check-in received"
        machine_id = 1
    }
}

function Invoke-TestRootUrlRequest {
    param($RequestParams)

    $script:capturedRequest = $RequestParams

    [pscustomobject]@{
        status = "success"
        message = "Check-in received"
        machine_id = 2
    }
}

function Invoke-TestResendRequest {
    param($RequestParams)

    $script:resendRequestCount++
    $script:capturedResendRequests += $RequestParams

    [pscustomobject]@{
        status = "success"
        message = "Check-in received"
        machine_id = $script:resendRequestCount
    }
}

function Invoke-MockOsRegistry {
    param($Path)

    $script:mockOsRegistry
}

function Invoke-MockProgramRegistry {
    param($Path)

    if ($Path -like "*Uninstall*") {
        return $script:mockProgramRegistry
    }

    @()
}

function Invoke-MockFirewallEnabled {
    $script:mockFirewallProfilesEnabled
}

function Invoke-MockFirewallDisabled {
    $script:mockFirewallProfilesDisabled
}

function Invoke-MockDefenderEnabled {
    $script:mockDefenderEnabled
}

function Invoke-MockDefenderDisabled {
    $script:mockDefenderDisabled
}

function Invoke-MockRdpDisabledRegistry {
    param($Path)

    $script:mockRdpDisabledRegistry
}

function Invoke-MockRdpEnabledRegistry {
    param($Path)

    $script:mockRdpEnabledRegistry
}

function Invoke-MockLocalAdmins {
    $script:mockLocalAdmins
}

function Invoke-MockUsbDevices {
    $script:mockUsbDevices
}

function Invoke-MockFailedLogins {
    $script:mockFailedLogins
}

Assert-True -Condition ($validatedNewConfig.server_url -eq "https://itcenter-daniel.chickenkiller.com") -Message "New config server_url must be preserved without trailing slash."
Assert-True -Condition ($validatedNewConfig.api_key -eq "new-key") -Message "New config must normalize agent_api_key to api_key."
Assert-True -Condition ($validatedNewConfig.checkin_interval_minutes -eq 5) -Message "New config interval must be normalized."
Assert-True -Condition ($validatedLegacyConfig.api_key -eq "legacy-key") -Message "Legacy config must keep api_key."
Assert-True -Condition ($validatedLegacyConfig.checkin_interval_minutes -eq 10) -Message "Legacy config interval must be normalized."

Assert-Percent -Value $cpuUsage -Name "CPU usage"
Assert-Percent -Value $ramUsage -Name "RAM usage"
Assert-Percent -Value $diskUsage -Name "Disk usage"

Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($payload.hostname)) -Message "Payload hostname is required."
Assert-True -Condition ($payload.cpu_usage -ge 0 -and $payload.cpu_usage -le 100) -Message "Payload CPU usage must be between 0 and 100."
Assert-True -Condition ($payload.ram_usage -ge 0 -and $payload.ram_usage -le 100) -Message "Payload RAM usage must be between 0 and 100."
Assert-True -Condition ($payload.disk_usage -ge 0 -and $payload.disk_usage -le 100) -Message "Payload disk usage must be between 0 and 100."
Assert-True -Condition ($payload.uptime_seconds -ge 0) -Message "Payload uptime must be greater than or equal to 0."

Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($json)) -Message "JSON output is required."
Assert-True -Condition ($jsonPayload.hostname -eq $payload.hostname) -Message "JSON hostname must match payload hostname."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "cpu_usage") -Message "JSON must contain cpu_usage."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "ram_usage") -Message "JSON must contain ram_usage."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "disk_usage") -Message "JSON must contain disk_usage."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "uptime_seconds") -Message "JSON must contain uptime_seconds."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "installed_programs") -Message "JSON must contain installed_programs."
Assert-True -Condition ($jsonPayload.PSObject.Properties.Name -contains "security") -Message "JSON must contain security."
Assert-True -Condition ([double]$jsonPayload.cpu_usage -eq [double]$payload.cpu_usage) -Message "JSON CPU usage must match payload CPU usage."
Assert-True -Condition ([double]$jsonPayload.ram_usage -eq [double]$payload.ram_usage) -Message "JSON RAM usage must match payload RAM usage."
Assert-True -Condition ([double]$jsonPayload.disk_usage -eq [double]$payload.disk_usage) -Message "JSON disk usage must match payload disk usage."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "firewall_enabled") -Message "JSON security must contain firewall_enabled."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "defender_enabled") -Message "JSON security must contain defender_enabled."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "rdp_enabled") -Message "JSON security must contain rdp_enabled."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "local_admins") -Message "JSON security must contain local_admins."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "usb_devices") -Message "JSON security must contain usb_devices."
Assert-True -Condition ($jsonPayload.security.PSObject.Properties.Name -contains "failed_logins_last_hour") -Message "JSON security must contain failed_logins_last_hour."

$operatingSystem = Get-AgentOperatingSystem -RegistryReader ${function:Invoke-MockOsRegistry} -SystemInfoReader { $null }
Assert-True -Condition ($operatingSystem.operating_system -eq "Windows 11 Pro") -Message "Operating system must come from registry."
Assert-True -Condition ($operatingSystem.os_version -eq "23H2") -Message "OS version must come from registry."

$programs = @(Get-InstalledPrograms -RegistryReader ${function:Invoke-MockProgramRegistry})
Assert-True -Condition ($programs.Count -eq 2) -Message "Installed programs must be de-duplicated."
Assert-True -Condition ($programs[0].name -eq "AnyDesk" -or $programs[1].name -eq "AnyDesk") -Message "Installed programs must include AnyDesk."
Assert-True -Condition ($programs[0].name -eq "Google Chrome" -or $programs[1].name -eq "Google Chrome") -Message "Installed programs must include Google Chrome."

Assert-True -Condition (Get-AgentFirewallEnabled -FirewallProfileReader ${function:Invoke-MockFirewallEnabled}) -Message "Firewall must be enabled when all profiles are enabled."
Assert-True -Condition (-not (Get-AgentFirewallEnabled -FirewallProfileReader ${function:Invoke-MockFirewallDisabled})) -Message "Firewall must be disabled when any profile is disabled."
Assert-True -Condition (Get-AgentDefenderEnabled -DefenderStatusReader ${function:Invoke-MockDefenderEnabled}) -Message "Defender must be enabled when service, antispyware and realtime protection are enabled."
Assert-True -Condition (-not (Get-AgentDefenderEnabled -DefenderStatusReader ${function:Invoke-MockDefenderDisabled})) -Message "Defender must be disabled when realtime protection is disabled."
Assert-True -Condition (-not (Get-AgentRdpEnabled -RegistryReader ${function:Invoke-MockRdpDisabledRegistry})) -Message "RDP must be disabled when fDenyTSConnections is 1."
Assert-True -Condition (Get-AgentRdpEnabled -RegistryReader ${function:Invoke-MockRdpEnabledRegistry}) -Message "RDP must be enabled when fDenyTSConnections is 0."

$localAdmins = @(Get-AgentLocalAdmins -LocalAdminReader ${function:Invoke-MockLocalAdmins})
Assert-True -Condition ($localAdmins.Count -eq 2) -Message "Local admins must be de-duplicated."
Assert-True -Condition ($localAdmins -contains "DESKTOP\Administrator") -Message "Local admins must include local Administrator."
Assert-True -Condition ($localAdmins -contains "DOMAIN\Daniel") -Message "Local admins must include domain admin."

$usbDevices = @(Get-AgentUsbDevices -UsbDeviceReader ${function:Invoke-MockUsbDevices})
Assert-True -Condition ($usbDevices.Count -eq 1) -Message "USB devices must be collected."
Assert-True -Condition ($usbDevices[0].name -eq "Kingston DataTraveler") -Message "USB device model must be collected."
Assert-True -Condition ($usbDevices[0].serial_number -eq "USB123") -Message "USB device serial number must be collected."

$failedLogins = Get-AgentFailedLoginsLastHour -FailedLoginReader ${function:Invoke-MockFailedLogins}
Assert-True -Condition ($failedLogins -eq 2) -Message "Failed login count must match mocked events."

$mockPayload = [pscustomobject]@{
    hostname = $payload.hostname
    username = $payload.username
    ip_address = $payload.ip_address
    operating_system = $operatingSystem.operating_system
    os_version = $operatingSystem.os_version
    cpu_usage = $payload.cpu_usage
    ram_usage = $payload.ram_usage
    disk_usage = $payload.disk_usage
    uptime_seconds = $payload.uptime_seconds
    installed_programs = $programs
    security = $payload.security
}

$mockJsonPayload = (ConvertTo-AgentCheckinJson -Payload $mockPayload) | ConvertFrom-Json
Assert-True -Condition ($mockJsonPayload.operating_system -eq "Windows 11 Pro") -Message "JSON must include operating system."
Assert-True -Condition ($mockJsonPayload.os_version -eq "23H2") -Message "JSON must include OS version."
Assert-True -Condition ($mockJsonPayload.installed_programs.Count -eq 2) -Message "JSON must include installed programs."

$response = Send-AgentCheckin -Config ([pscustomobject]@{
    server_url = "http://127.0.0.1:8000/api/v1"
    api_key = "test-key"
}) -Payload $payload -RequestInvoker ${function:Invoke-TestRequest}

Assert-True -Condition ($capturedRequest.Uri -eq "http://127.0.0.1:8000/api/v1/agent/checkin") -Message "Request URI must target agent check-in."
Assert-True -Condition ($capturedRequest.Method -eq "Post") -Message "Request method must be POST."
Assert-True -Condition ($capturedRequest.Headers["X-Agent-Api-Key"] -eq "test-key") -Message "Request must include agent API key header."
Assert-True -Condition ($capturedRequest.ContentType -eq "application/json") -Message "Request must send JSON content type."
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($capturedRequest.Body)) -Message "Request body is required."

$sentBody = if ($capturedRequest.Body -is [byte[]]) {
    [System.Text.Encoding]::UTF8.GetString($capturedRequest.Body)
}
else {
    [string]$capturedRequest.Body
}

$sentPayload = $sentBody | ConvertFrom-Json
Assert-True -Condition ($sentPayload.hostname -eq $payload.hostname) -Message "Sent payload hostname must match."
Assert-True -Condition ($sentPayload.cpu_usage -eq $payload.cpu_usage) -Message "Sent payload CPU usage must match."
Assert-True -Condition ($response.status -eq "success") -Message "Send-AgentCheckin should return API response."

$rootUrlResponse = Send-AgentCheckin -Config ([pscustomobject]@{
    server_url = "https://itcenter-daniel.chickenkiller.com"
    api_key = "test-key"
}) -Payload $payload -RequestInvoker ${function:Invoke-TestRootUrlRequest}

Assert-True -Condition ($capturedRequest.Uri -eq "https://itcenter-daniel.chickenkiller.com/api/v1/agent/checkin") -Message "Root server URL must be expanded to /api/v1/agent/checkin."
Assert-True -Condition ($rootUrlResponse.status -eq "success") -Message "Root URL check-in should return API response."

$tempCacheDirectory = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-agent-tests-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tempCacheDirectory | Out-Null

try {
    $cacheFile = Save-AgentOfflinePayload -Payload $payload -CacheDirectory $tempCacheDirectory
    Assert-True -Condition (Test-Path -LiteralPath $cacheFile) -Message "Offline payload must be cached."

    $cachedPayload = Get-Content -LiteralPath $cacheFile -Raw | ConvertFrom-Json
    Assert-True -Condition ($cachedPayload.hostname -eq $payload.hostname) -Message "Cached payload hostname must match."

    $resentCount = Send-PendingAgentCheckins -Config ([pscustomobject]@{
        server_url = "http://127.0.0.1:8000/api/v1"
        api_key = "test-key"
    }) -CacheDirectory $tempCacheDirectory -RequestInvoker ${function:Invoke-TestResendRequest}

    Assert-True -Condition ($resentCount -eq 1) -Message "Pending cache resend count must be 1."
    Assert-True -Condition ($resendRequestCount -eq 1) -Message "Pending cache must invoke one request."
    Assert-True -Condition ($capturedResendRequests[0].Headers["X-Agent-Api-Key"] -eq "test-key") -Message "Pending resend must include agent API key header."
    Assert-True -Condition (-not (Test-Path -LiteralPath $cacheFile)) -Message "Cached payload must be removed after successful resend."
}
finally {
    if (Test-Path -LiteralPath $tempCacheDirectory) {
        Remove-Item -LiteralPath $tempCacheDirectory -Recurse -Force
    }
}

Write-Output "Agent tests passed."
