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

function Invoke-TestRequest {
    param($RequestParams)

    $script:capturedRequest = $RequestParams

    [pscustomobject]@{
        status = "success"
        message = "Check-in received"
        machine_id = 1
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

$sentPayload = $capturedRequest.Body | ConvertFrom-Json
Assert-True -Condition ($sentPayload.hostname -eq $payload.hostname) -Message "Sent payload hostname must match."
Assert-True -Condition ($sentPayload.cpu_usage -eq $payload.cpu_usage) -Message "Sent payload CPU usage must match."
Assert-True -Condition ($response.status -eq "success") -Message "Send-AgentCheckin should return API response."

Write-Output "Agent tests passed."
