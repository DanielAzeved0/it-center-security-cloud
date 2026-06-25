param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot "config.json")
)

$ErrorActionPreference = "Stop"

function Get-AgentConfig {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config file not found: $Path"
    }

    Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Write-AgentLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $logsPath = Join-Path $PSScriptRoot "logs"
    if (-not (Test-Path -LiteralPath $logsPath)) {
        New-Item -ItemType Directory -Path $logsPath | Out-Null
    }

    $logFile = Join-Path $logsPath "itcenter-agent.log"
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -LiteralPath $logFile -Value "[$timestamp] [$Level] $Message"
}

function Initialize-AgentWorkspace {
    $requiredDirectories = @(
        (Join-Path $PSScriptRoot "cache"),
        (Join-Path $PSScriptRoot "logs")
    )

    foreach ($directory in $requiredDirectories) {
        if (-not (Test-Path -LiteralPath $directory)) {
            New-Item -ItemType Directory -Path $directory | Out-Null
        }
    }
}

function ConvertTo-AgentPercent {
    param(
        [double]$Value
    )

    if ($Value -lt 0) {
        return 0
    }

    if ($Value -gt 100) {
        return 100
    }

    [math]::Round($Value, 2)
}

function Get-AgentHostname {
    $hostname = [System.Net.Dns]::GetHostName()

    if ([string]::IsNullOrWhiteSpace($hostname)) {
        $hostname = $env:COMPUTERNAME
    }

    if ([string]::IsNullOrWhiteSpace($hostname)) {
        throw "Unable to collect hostname."
    }

    $hostname.Trim().ToUpperInvariant()
}

function Get-AgentUsername {
    $username = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

    if ([string]::IsNullOrWhiteSpace($username)) {
        $username = $env:USERNAME
    }

    if ([string]::IsNullOrWhiteSpace($username)) {
        throw "Unable to collect username."
    }

    $username.Trim()
}

function Get-AgentIpAddress {
    $ipAddress = $null

    if (Get-Command -Name Get-NetIPAddress -ErrorAction SilentlyContinue) {
        $ipAddress = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object {
                $_.IPAddress -ne "127.0.0.1" -and
                $_.IPAddress -notlike "169.254.*" -and
                $_.PrefixOrigin -ne "WellKnown"
            } |
            Sort-Object -Property InterfaceMetric, InterfaceIndex |
            Select-Object -ExpandProperty IPAddress -First 1
    }

    if ([string]::IsNullOrWhiteSpace($ipAddress)) {
        $ipAddress = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -ErrorAction SilentlyContinue |
            Where-Object { $_.IPEnabled -eq $true -and $_.IPAddress } |
            ForEach-Object { $_.IPAddress } |
            Where-Object {
                $_ -match "^\d{1,3}(\.\d{1,3}){3}$" -and
                $_ -ne "127.0.0.1" -and
                $_ -notlike "169.254.*"
            } |
            Select-Object -First 1
    }

    if ([string]::IsNullOrWhiteSpace($ipAddress)) {
        $hostname = Get-AgentHostname
        $ipAddress = [System.Net.Dns]::GetHostAddresses($hostname) |
            Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork } |
            ForEach-Object { $_.IPAddressToString } |
            Where-Object {
                $_ -ne "127.0.0.1" -and
                $_ -notlike "169.254.*"
            } |
            Select-Object -First 1
    }

    if ([string]::IsNullOrWhiteSpace($ipAddress)) {
        return $null
    }

    $ipAddress.Trim()
}

function Get-AgentCpuUsage {
    $processors = Get-CimInstance -ClassName Win32_Processor -ErrorAction SilentlyContinue
    $cpuSamples = @($processors | Where-Object { $null -ne $_.LoadPercentage } | ForEach-Object { [double]$_.LoadPercentage })

    if ($cpuSamples.Count -eq 0) {
        return 0
    }

    $averageCpu = ($cpuSamples | Measure-Object -Average).Average
    ConvertTo-AgentPercent -Value $averageCpu
}

function Get-AgentRamUsage {
    $operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue

    if ($null -eq $operatingSystem -or $operatingSystem.TotalVisibleMemorySize -le 0) {
        return 0
    }

    $usedMemory = [double]$operatingSystem.TotalVisibleMemorySize - [double]$operatingSystem.FreePhysicalMemory
    $ramUsage = ($usedMemory / [double]$operatingSystem.TotalVisibleMemorySize) * 100

    ConvertTo-AgentPercent -Value $ramUsage
}

function Get-AgentDiskUsage {
    $systemDrive = $env:SystemDrive
    $fixedDisks = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" -ErrorAction SilentlyContinue |
        Where-Object { $_.Size -gt 0 }

    if ($systemDrive) {
        $disk = $fixedDisks | Where-Object { $_.DeviceID -eq $systemDrive } | Select-Object -First 1
    }

    if ($null -eq $disk) {
        $disk = $fixedDisks | Select-Object -First 1
    }

    if ($null -eq $disk -or $disk.Size -le 0) {
        return 0
    }

    $usedDisk = [double]$disk.Size - [double]$disk.FreeSpace
    $diskUsage = ($usedDisk / [double]$disk.Size) * 100

    ConvertTo-AgentPercent -Value $diskUsage
}

function Get-AgentUptimeSeconds {
    $operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue

    if ($null -eq $operatingSystem -or $null -eq $operatingSystem.LastBootUpTime) {
        return 0
    }

    $uptime = (Get-Date) - $operatingSystem.LastBootUpTime
    [math]::Max(0, [int64]$uptime.TotalSeconds)
}

function Get-AgentOperatingSystem {
    param(
        [scriptblock]$RegistryReader = {
            param($Path)
            Get-ItemProperty -Path $Path -ErrorAction SilentlyContinue
        },
        [scriptblock]$SystemInfoReader = {
            Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
        }
    )

    $registry = & $RegistryReader "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    $systemInfo = & $SystemInfoReader

    $operatingSystem = $null
    $osVersion = $null

    if ($null -ne $registry) {
        if (-not [string]::IsNullOrWhiteSpace($registry.ProductName)) {
            $operatingSystem = [string]$registry.ProductName
        }

        if (-not [string]::IsNullOrWhiteSpace($registry.DisplayVersion)) {
            $osVersion = [string]$registry.DisplayVersion
        }
        elseif (-not [string]::IsNullOrWhiteSpace($registry.ReleaseId)) {
            $osVersion = [string]$registry.ReleaseId
        }
    }

    if ([string]::IsNullOrWhiteSpace($operatingSystem) -and $null -ne $systemInfo) {
        if (-not [string]::IsNullOrWhiteSpace($systemInfo.Caption)) {
            $operatingSystem = [string]$systemInfo.Caption
        }
    }

    if ([string]::IsNullOrWhiteSpace($osVersion) -and $null -ne $systemInfo) {
        if (-not [string]::IsNullOrWhiteSpace($systemInfo.Version)) {
            $osVersion = [string]$systemInfo.Version
        }
    }

    [pscustomobject]@{
        operating_system = $operatingSystem
        os_version = $osVersion
    }
}

function Get-InstalledPrograms {
    param(
        [scriptblock]$RegistryReader = {
            param($Path)
            Get-ItemProperty -Path $Path -ErrorAction SilentlyContinue
        }
    )

    $registryPaths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    $programs = foreach ($path in $registryPaths) {
        $items = @(& $RegistryReader $path)

        foreach ($item in $items) {
            if ($null -eq $item) {
                continue
            }

            $name = [string]$item.DisplayName
            if ([string]::IsNullOrWhiteSpace($name)) {
                continue
            }

            [pscustomobject]@{
                name = $name.Trim()
                version = if ([string]::IsNullOrWhiteSpace($item.DisplayVersion)) { $null } else { [string]$item.DisplayVersion.Trim() }
                publisher = if ([string]::IsNullOrWhiteSpace($item.Publisher)) { $null } else { [string]$item.Publisher.Trim() }
            }
        }
    }

    $programs |
        Sort-Object name, version, publisher -Unique |
        ForEach-Object {
            [ordered]@{
                name = $_.name
                version = $_.version
                publisher = $_.publisher
            }
        }
}

function New-AgentCheckinPayload {
    $hostname = Get-AgentHostname
    $username = Get-AgentUsername
    $ipAddress = Get-AgentIpAddress
    $operatingSystem = Get-AgentOperatingSystem
    $cpuUsage = Get-AgentCpuUsage
    $ramUsage = Get-AgentRamUsage
    $diskUsage = Get-AgentDiskUsage
    $uptimeSeconds = Get-AgentUptimeSeconds
    $installedPrograms = @(Get-InstalledPrograms)

    [ordered]@{
        hostname = $hostname
        username = $username
        ip_address = $ipAddress
        operating_system = $operatingSystem.operating_system
        os_version = $operatingSystem.os_version
        cpu_usage = $cpuUsage
        ram_usage = $ramUsage
        disk_usage = $diskUsage
        uptime_seconds = $uptimeSeconds
        installed_programs = $installedPrograms
        security = [ordered]@{
            firewall_enabled = $true
            defender_enabled = $true
            rdp_enabled = $false
            local_admins = @()
            usb_devices = @()
            failed_logins_last_hour = 0
        }
    }
}

function ConvertTo-AgentCheckinJson {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Payload
    )

    $Payload | ConvertTo-Json -Depth 8
}

function Send-AgentCheckin {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        [Parameter(Mandatory = $true)]
        [object]$Payload,
        [scriptblock]$RequestInvoker = {
            param($RequestParams)
            Invoke-RestMethod @RequestParams
        }
    )

    if ([string]::IsNullOrWhiteSpace($Config.server_url)) {
        throw "Server URL not configured."
    }

    if ([string]::IsNullOrWhiteSpace($Config.api_key)) {
        throw "Agent API key not configured."
    }

    $baseUrl = $Config.server_url.TrimEnd("/")
    $requestParams = @{
        Uri = "$baseUrl/agent/checkin"
        Method = "Post"
        Headers = @{
            "X-Agent-Api-Key" = $Config.api_key
        }
        ContentType = "application/json"
        Body = (ConvertTo-AgentCheckinJson -Payload $Payload)
        ErrorAction = "Stop"
    }

    & $RequestInvoker $requestParams
}

function Start-ItCenterAgent {
    Initialize-AgentWorkspace
    $config = Get-AgentConfig -Path $ConfigPath
    $payload = New-AgentCheckinPayload

    Write-AgentLog -Message "Agent started. Server URL: $($config.server_url)"
    Write-AgentLog -Message "Hostname collected: $($payload.hostname)"
    Write-AgentLog -Message "Username collected: $($payload.username)"
    Write-AgentLog -Message "Operating system collected: $($payload.operating_system) $($payload.os_version)"

    if ([string]::IsNullOrWhiteSpace($payload.ip_address)) {
        Write-AgentLog -Message "IP address not found." -Level "WARN"
    }
    else {
        Write-AgentLog -Message "IP address collected: $($payload.ip_address)"
    }

    Write-AgentLog -Message "CPU usage collected: $($payload.cpu_usage)%"
    Write-AgentLog -Message "RAM usage collected: $($payload.ram_usage)%"
    Write-AgentLog -Message "Disk usage collected: $($payload.disk_usage)%"
    Write-AgentLog -Message "Installed programs collected: $($payload.installed_programs.Count)"
    Write-AgentLog -Message "Check-in JSON generated."

    try {
        $response = Send-AgentCheckin -Config $config -Payload $payload
        Write-AgentLog -Message "Check-in sent successfully."
        Write-Output ($response | ConvertTo-Json -Depth 8)
    }
    catch {
        Write-AgentLog -Message "Failed to send check-in: $($_.Exception.Message)" -Level "WARN"
        Write-Output (ConvertTo-AgentCheckinJson -Payload $payload)
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    Start-ItCenterAgent
}
