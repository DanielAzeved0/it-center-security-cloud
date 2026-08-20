param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot "config.json")
)

$ErrorActionPreference = "Stop"

# ADR-032: thresholds for the rollback/confirm decision below. Not read from config.json - kept
# as script constants, same treatment as any other fixed policy value in this script.
$script:UpdaterRollbackFailureThreshold = 5
$script:UpdaterConfirmSuccessThreshold = 3

function Get-AgentUpdaterInstallPath {
    Split-Path -Path $ConfigPath -Parent
}

function Get-AgentUpdaterConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config file not found: $Path"
    }

    $rawConfig = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json

    $serverUrl = [string]$rawConfig.server_url
    if ([string]::IsNullOrWhiteSpace($serverUrl)) {
        throw "Server URL not configured."
    }

    $apiKey = if (-not [string]::IsNullOrWhiteSpace($rawConfig.agent_api_key)) {
        [string]$rawConfig.agent_api_key
    }
    else {
        [string]$rawConfig.api_key
    }

    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw "Agent API key not configured."
    }

    [pscustomobject]@{
        server_url = $serverUrl.TrimEnd("/")
        agent_api_key = $apiKey
        log_path = [string]$rawConfig.log_path
    }
}

function Get-AgentUpdaterLogDirectory {
    param(
        [object]$Config
    )

    if ($null -ne $Config -and -not [string]::IsNullOrWhiteSpace($Config.log_path)) {
        return $Config.log_path
    }

    Join-Path (Get-AgentUpdaterInstallPath) "logs"
}

# Separate log file from itcenter-agent.log by design: the collector and the updater are two
# independent scheduled processes, and sharing one file would risk both rotating it at once.
function Write-AgentUpdaterLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [object]$Config = $null
    )

    $logsPath = Get-AgentUpdaterLogDirectory -Config $Config
    if (-not (Test-Path -LiteralPath $logsPath)) {
        New-Item -ItemType Directory -Path $logsPath | Out-Null
    }

    $logFile = Join-Path $logsPath "itcenter-agent-updater.log"

    if ((Test-Path -LiteralPath $logFile) -and (Get-Item -LiteralPath $logFile).Length -ge 5MB) {
        $rotated = "$logFile.1"
        if (Test-Path -LiteralPath $rotated) {
            Remove-Item -LiteralPath $rotated -Force
        }
        Move-Item -LiteralPath $logFile -Destination $rotated -Force
    }

    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -LiteralPath $logFile -Value "[$timestamp] [$Level] $Message"
}

function Get-AgentUpdaterHostname {
    $hostname = [System.Net.Dns]::GetHostName()

    if ([string]::IsNullOrWhiteSpace($hostname)) {
        $hostname = $env:COMPUTERNAME
    }

    $hostname.Trim().ToUpperInvariant()
}

function Get-AgentUpdaterManifest {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        [scriptblock]$RequestInvoker = {
            param($RequestParams)
            Invoke-RestMethod @RequestParams
        }
    )

    $baseUrl = $Config.server_url
    if ($baseUrl -notmatch "/api/v1$") {
        $baseUrl = "$baseUrl/api/v1"
    }

    $hostname = Get-AgentUpdaterHostname
    $requestParams = @{
        Uri = "$baseUrl/agent/manifest?hostname=$([uri]::EscapeDataString($hostname))"
        Method = "Get"
        Headers = @{
            "X-Agent-Api-Key" = $Config.agent_api_key
        }
        ErrorAction = "Stop"
    }

    & $RequestInvoker $requestParams
}

function Save-AgentUpdaterReleaseToFile {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath,
        [scriptblock]$RequestInvoker = {
            param($RequestParams)
            Invoke-WebRequest @RequestParams | Out-Null
        }
    )

    $baseUrl = $Config.server_url
    if ($baseUrl -notmatch "/api/v1$") {
        $baseUrl = "$baseUrl/api/v1"
    }

    $requestParams = @{
        Uri = "$baseUrl/agent/download"
        Method = "Get"
        Headers = @{
            "X-Agent-Api-Key" = $Config.agent_api_key
        }
        OutFile = $DestinationPath
        ErrorAction = "Stop"
    }

    & $RequestInvoker $requestParams
}

function Test-AgentUpdaterReleaseValid {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedSha256,
        [scriptblock]$SignatureInvoker = {
            param($Path)
            Get-AuthenticodeSignature -FilePath $Path
        }
    )

    $signature = & $SignatureInvoker $FilePath
    if ($signature.Status -ne "Valid") {
        return [pscustomobject]@{
            IsValid = $false
            Reason = "invalid signature (status: $($signature.Status))"
        }
    }

    $actualHash = (Get-FileHash -LiteralPath $FilePath -Algorithm SHA256).Hash
    if ($actualHash -ne $ExpectedSha256.ToUpperInvariant()) {
        return [pscustomobject]@{
            IsValid = $false
            Reason = "hash mismatch (expected $ExpectedSha256, got $actualHash)"
        }
    }

    [pscustomobject]@{
        IsValid = $true
        Reason = $null
    }
}

# Parses the same "$script:AgentVersion = "..."" line itcenter-agent.ps1 declares at its top -
# reading the file as text (not dot-sourcing it) so the updater never executes the collector.
function Get-AgentInstalledVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AgentScriptPath
    )

    if (-not (Test-Path -LiteralPath $AgentScriptPath)) {
        throw "Installed agent script not found: $AgentScriptPath"
    }

    $content = Get-Content -LiteralPath $AgentScriptPath -Raw
    if ($content -match '\$script:AgentVersion\s*=\s*"([^"]+)"') {
        return $Matches[1]
    }

    throw "Unable to determine installed agent version (missing `$script:AgentVersion in $AgentScriptPath)."
}

function Get-AgentUpdaterStateFilePath {
    Join-Path (Get-AgentUpdaterInstallPath) "update-state.json"
}

function Get-AgentUpdaterState {
    $path = Get-AgentUpdaterStateFilePath
    if (-not (Test-Path -LiteralPath $path)) {
        return $null
    }

    try {
        Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    }
    catch {
        Write-AgentUpdaterLog -Message "Update state file is corrupted, treating as no pending update: $($_.Exception.Message)" -Level "WARN"
        $null
    }
}

function Set-AgentUpdaterState {
    param(
        [Parameter(Mandatory = $true)]
        [object]$State
    )

    $State | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Get-AgentUpdaterStateFilePath) -Encoding UTF8
}

function New-AgentUpdaterAppliedState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AppliedVersion,
        [Parameter(Mandatory = $true)]
        [string]$PreviousVersion
    )

    [pscustomobject]@{
        applied_version = $AppliedVersion
        previous_version = $PreviousVersion
        updated_at = (Get-Date).ToUniversalTime().ToString("o")
        consecutive_checkin_failures = 0
        consecutive_checkin_successes = 0
        confirmed = $false
    }
}

# Resolves a pending update (FR-010/011/012) before checking for a new one: rolls back on
# repeated post-update check-in failures, or marks the update confirmed after enough successes.
# A state with no applied_version, or already confirmed, is returned unchanged (nothing pending).
function Resolve-AgentUpdaterPendingState {
    param(
        [Parameter(Mandatory = $true)]
        [object]$State,
        [Parameter(Mandatory = $true)]
        [string]$AgentScriptPath,
        [Parameter(Mandatory = $true)]
        [string]$PreviousScriptPath,
        [object]$Config = $null,
        [scriptblock]$SignatureInvoker = {
            param($Path)
            Get-AuthenticodeSignature -FilePath $Path
        }
    )

    if ([string]::IsNullOrWhiteSpace($State.applied_version) -or $State.confirmed -eq $true) {
        return $State
    }

    $failures = [int]$State.consecutive_checkin_failures
    $successes = [int]$State.consecutive_checkin_successes

    if ($failures -ge $script:UpdaterRollbackFailureThreshold) {
        if (-not (Test-Path -LiteralPath $PreviousScriptPath)) {
            Write-AgentUpdaterLog -Message "Rollback needed ($failures consecutive check-in failures) but no .previous backup was found - cannot roll back automatically." -Level "ERROR" -Config $Config
            return $State
        }

        $previousSignature = & $SignatureInvoker $PreviousScriptPath
        if ($previousSignature.Status -ne "Valid") {
            Write-AgentUpdaterLog -Message "Rollback aborted: .previous backup signature is not valid (status: $($previousSignature.Status))." -Level "ERROR" -Config $Config
            return $State
        }

        Move-Item -LiteralPath $PreviousScriptPath -Destination $AgentScriptPath -Force
        Write-AgentUpdaterLog -Message "Rollback applied: reverted from version $($State.applied_version) to $($State.previous_version) after $failures consecutive check-in failures." -Level "ERROR" -Config $Config

        return [pscustomobject]@{
            applied_version = $null
            previous_version = $null
            updated_at = $null
            consecutive_checkin_failures = 0
            consecutive_checkin_successes = 0
            confirmed = $false
        }
    }

    if ($successes -ge $script:UpdaterConfirmSuccessThreshold) {
        Write-AgentUpdaterLog -Message "Update to version $($State.applied_version) confirmed after $successes consecutive successful check-ins." -Config $Config
        $State.confirmed = $true
    }

    return $State
}

function Start-ItCenterAgentUpdate {
    param(
        [scriptblock]$ManifestInvoker = {
            param($RequestParams)
            Invoke-RestMethod @RequestParams
        },
        [scriptblock]$DownloadInvoker = {
            param($RequestParams)
            Invoke-WebRequest @RequestParams | Out-Null
        },
        [scriptblock]$SignatureInvoker = {
            param($Path)
            Get-AuthenticodeSignature -FilePath $Path
        }
    )

    $installPath = Get-AgentUpdaterInstallPath
    $agentScriptPath = Join-Path $installPath "itcenter-agent.ps1"
    $previousScriptPath = "$agentScriptPath.previous"

    try {
        $config = Get-AgentUpdaterConfig -Path $ConfigPath
    }
    catch {
        Write-AgentUpdaterLog -Message "Updater failed to read configuration: $($_.Exception.Message)" -Level "ERROR"
        throw
    }

    $state = Get-AgentUpdaterState
    if ($null -ne $state) {
        $state = Resolve-AgentUpdaterPendingState -State $state -AgentScriptPath $agentScriptPath -PreviousScriptPath $previousScriptPath -Config $config -SignatureInvoker $SignatureInvoker
        Set-AgentUpdaterState -State $state
    }

    try {
        $manifest = Get-AgentUpdaterManifest -Config $config -RequestInvoker $ManifestInvoker
    }
    catch {
        Write-AgentUpdaterLog -Message "Failed to fetch agent manifest: $($_.Exception.Message)" -Level "WARN" -Config $config
        return
    }

    try {
        $installedVersion = Get-AgentInstalledVersion -AgentScriptPath $agentScriptPath
    }
    catch {
        Write-AgentUpdaterLog -Message $_.Exception.Message -Level "ERROR" -Config $config
        return
    }

    if ($installedVersion -eq $manifest.version) {
        Write-AgentUpdaterLog -Message "Agent already up to date (version $installedVersion)." -Config $config
        return
    }

    if (-not [string]::IsNullOrWhiteSpace($manifest.target_agent_version) -and $manifest.target_agent_version -ne $manifest.version) {
        Write-AgentUpdaterLog -Message "Update to $($manifest.version) held back: target_agent_version is pinned to $($manifest.target_agent_version)." -Config $config
        return
    }

    $tempPath = "$agentScriptPath.download"
    try {
        Save-AgentUpdaterReleaseToFile -Config $config -DestinationPath $tempPath -RequestInvoker $DownloadInvoker
    }
    catch {
        Write-AgentUpdaterLog -Message "Failed to download agent release $($manifest.version): $($_.Exception.Message)" -Level "WARN" -Config $config
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
        return
    }

    $validation = Test-AgentUpdaterReleaseValid -FilePath $tempPath -ExpectedSha256 $manifest.sha256 -SignatureInvoker $SignatureInvoker
    if (-not $validation.IsValid) {
        Write-AgentUpdaterLog -Message "Downloaded agent release $($manifest.version) rejected: $($validation.Reason)." -Level "ERROR" -Config $config
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
        return
    }

    Copy-Item -LiteralPath $agentScriptPath -Destination $previousScriptPath -Force
    Move-Item -LiteralPath $tempPath -Destination $agentScriptPath -Force

    Set-AgentUpdaterState -State (New-AgentUpdaterAppliedState -AppliedVersion $manifest.version -PreviousVersion $installedVersion)
    Write-AgentUpdaterLog -Message "Agent updated from version $installedVersion to $($manifest.version)." -Config $config
}

if ($MyInvocation.InvocationName -ne ".") {
    Start-ItCenterAgentUpdate
}
