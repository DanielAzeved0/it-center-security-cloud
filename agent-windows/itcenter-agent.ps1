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

function Get-AgentFirewallEnabled {
    param(
        [scriptblock]$FirewallProfileReader = {
            if (Get-Command -Name Get-NetFirewallProfile -ErrorAction SilentlyContinue) {
                Get-NetFirewallProfile -ErrorAction SilentlyContinue
            }
        }
    )

    $profiles = @(& $FirewallProfileReader | Where-Object { $null -ne $_ })

    if ($profiles.Count -eq 0) {
        return $false
    }

    $disabledProfiles = @($profiles | Where-Object { $_.Enabled -ne $true })
    $disabledProfiles.Count -eq 0
}

function Get-AgentDefenderEnabled {
    param(
        [scriptblock]$DefenderStatusReader = {
            if (Get-Command -Name Get-MpComputerStatus -ErrorAction SilentlyContinue) {
                Get-MpComputerStatus -ErrorAction SilentlyContinue
            }
        }
    )

    $status = & $DefenderStatusReader

    if ($null -eq $status) {
        return $false
    }

    $serviceEnabled = $status.AMServiceEnabled -eq $true
    $antispywareEnabled = $status.AntispywareEnabled -eq $true
    $realtimeEnabled = $status.RealTimeProtectionEnabled -eq $true

    $serviceEnabled -and $antispywareEnabled -and $realtimeEnabled
}

function Get-AgentRdpEnabled {
    param(
        [scriptblock]$RegistryReader = {
            param($Path)
            Get-ItemProperty -Path $Path -ErrorAction SilentlyContinue
        }
    )

    $terminalServer = & $RegistryReader "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"

    if ($null -eq $terminalServer -or $null -eq $terminalServer.fDenyTSConnections) {
        return $false
    }

    [int]$terminalServer.fDenyTSConnections -eq 0
}

function Get-AgentLocalAdmins {
    param(
        [scriptblock]$LocalAdminReader = {
            $hasLocalGroup = $null -ne (Get-Command -Name Get-LocalGroup -ErrorAction SilentlyContinue)
            $hasLocalGroupMember = $null -ne (Get-Command -Name Get-LocalGroupMember -ErrorAction SilentlyContinue)

            if ($hasLocalGroup -and $hasLocalGroupMember) {
                $adminGroup = Get-LocalGroup -SID "S-1-5-32-544" -ErrorAction SilentlyContinue

                if ($null -ne $adminGroup) {
                    Get-LocalGroupMember -Group $adminGroup.Name -ErrorAction SilentlyContinue
                }
            }
        }
    )

    $admins = @(& $LocalAdminReader | Where-Object { $null -ne $_ })

    $admins |
        ForEach-Object {
            if (-not [string]::IsNullOrWhiteSpace($_.Name)) {
                [string]$_.Name
            }
            elseif (-not [string]::IsNullOrWhiteSpace($_)) {
                [string]$_
            }
        } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { $_.Trim() } |
        Sort-Object -Unique
}

function Get-AgentUsbDevices {
    param(
        [scriptblock]$UsbDeviceReader = {
            Get-CimInstance -ClassName Win32_DiskDrive -ErrorAction SilentlyContinue |
                Where-Object { $_.InterfaceType -eq "USB" }
        }
    )

    $devices = @(& $UsbDeviceReader | Where-Object { $null -ne $_ })

    $devices |
        ForEach-Object {
            [ordered]@{
                name = if ([string]::IsNullOrWhiteSpace($_.Model)) { "USB storage device" } else { [string]$_.Model.Trim() }
                manufacturer = if ([string]::IsNullOrWhiteSpace($_.Manufacturer)) { $null } else { [string]$_.Manufacturer.Trim() }
                serial_number = if ([string]::IsNullOrWhiteSpace($_.SerialNumber)) { $null } else { [string]$_.SerialNumber.Trim() }
            }
        }
}

function Get-AgentFailedLoginsLastHour {
    param(
        [scriptblock]$FailedLoginReader = {
            Get-WinEvent -FilterHashtable @{
                LogName = "Security"
                Id = 4625
                StartTime = (Get-Date).AddHours(-1)
            } -ErrorAction SilentlyContinue
        }
    )

    try {
        $events = @(& $FailedLoginReader | Where-Object { $null -ne $_ })
        return $events.Count
    }
    catch {
        return 0
    }
}

function Get-AgentSecurityPayload {
    [ordered]@{
        firewall_enabled = Get-AgentFirewallEnabled
        defender_enabled = Get-AgentDefenderEnabled
        rdp_enabled = Get-AgentRdpEnabled
        local_admins = @(Get-AgentLocalAdmins)
        usb_devices = @(Get-AgentUsbDevices)
        failed_logins_last_hour = Get-AgentFailedLoginsLastHour
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
    $securityPayload = Get-AgentSecurityPayload

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
        security = $securityPayload
    }
}

function ConvertTo-AgentCheckinJson {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Payload
    )

    $Payload | ConvertTo-Json -Depth 8
}

function Get-AgentCacheDirectory {
    Join-Path $PSScriptRoot "cache"
}

function Save-AgentOfflinePayload {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Payload,
        [string]$CacheDirectory = (Get-AgentCacheDirectory)
    )

    if (-not (Test-Path -LiteralPath $CacheDirectory)) {
        New-Item -ItemType Directory -Path $CacheDirectory | Out-Null
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmssfff")
    $fileName = "checkin-$timestamp-$([guid]::NewGuid().ToString('N')).json"
    $cacheFile = Join-Path $CacheDirectory $fileName

    ConvertTo-AgentCheckinJson -Payload $Payload | Set-Content -LiteralPath $cacheFile -Encoding UTF8

    $cacheFile
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
    $jsonBody = ConvertTo-AgentCheckinJson -Payload $Payload
    $utf8Body = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)

    $requestParams = @{
        Uri = "$baseUrl/agent/checkin"
        Method = "Post"
        Headers = @{
            "X-Agent-Api-Key" = $Config.api_key
        }
        ContentType = "application/json"
        Body = $utf8Body
        ErrorAction = "Stop"
    }

    & $RequestInvoker $requestParams
}

function Send-PendingAgentCheckins {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        [string]$CacheDirectory = (Get-AgentCacheDirectory),
        [scriptblock]$RequestInvoker = {
            param($RequestParams)
            Invoke-RestMethod @RequestParams
        }
    )

    if (-not (Test-Path -LiteralPath $CacheDirectory)) {
        return 0
    }

    $sentCount = 0
    $pendingFiles = @(Get-ChildItem -LiteralPath $CacheDirectory -Filter "checkin-*.json" -File | Sort-Object LastWriteTimeUtc, Name)

    foreach ($pendingFile in $pendingFiles) {
        try {
            $pendingPayload = Get-Content -LiteralPath $pendingFile.FullName -Raw | ConvertFrom-Json
            Send-AgentCheckin -Config $Config -Payload $pendingPayload -RequestInvoker $RequestInvoker | Out-Null
            Remove-Item -LiteralPath $pendingFile.FullName
            $sentCount++
        }
        catch {
            Write-AgentLog -Message "Failed to resend cached check-in $($pendingFile.Name): $($_.Exception.Message)" -Level "WARN"
            break
        }
    }

    $sentCount
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
    Write-AgentLog -Message "Security posture collected. Firewall: $($payload.security.firewall_enabled), Defender: $($payload.security.defender_enabled), RDP: $($payload.security.rdp_enabled)"
    Write-AgentLog -Message "Check-in JSON generated."

    try {
        $resentCount = Send-PendingAgentCheckins -Config $config
        if ($resentCount -gt 0) {
            Write-AgentLog -Message "Cached check-ins resent: $resentCount"
        }
    }
    catch {
        Write-AgentLog -Message "Pending cached check-ins were not fully resent: $($_.Exception.Message)" -Level "WARN"
    }

    try {
        $response = Send-AgentCheckin -Config $config -Payload $payload
        Write-AgentLog -Message "Check-in sent successfully."
        Write-Output ($response | ConvertTo-Json -Depth 8)
    }
    catch {
        Write-AgentLog -Message "Failed to send check-in: $($_.Exception.Message)" -Level "WARN"
        $cacheFile = Save-AgentOfflinePayload -Payload $payload
        Write-AgentLog -Message "Check-in cached locally: $cacheFile" -Level "WARN"
        Write-Output (ConvertTo-AgentCheckinJson -Payload $payload)
    }
}

if ($MyInvocation.InvocationName -ne ".") {
    Start-ItCenterAgent
}
