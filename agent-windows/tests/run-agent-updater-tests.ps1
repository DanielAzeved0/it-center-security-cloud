param(
    [string]$UpdaterScriptPath = (Join-Path $PSScriptRoot "..\itcenter-agent-updater.ps1")
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

. $UpdaterScriptPath

function New-AgentUpdaterTestInstall {
    param(
        [Parameter(Mandatory = $true)]
        [string]$InstallPath,
        [string]$InstalledVersion = "1.0.0"
    )

    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $InstallPath "config.json") -Encoding UTF8 -Value (
        [ordered]@{
            server_url = "http://127.0.0.1:8000/api/v1"
            agent_api_key = "test-key"
        } | ConvertTo-Json
    )
    Set-Content -LiteralPath (Join-Path $InstallPath "itcenter-agent.ps1") -Encoding UTF8 -Value (
        "param()`n`$script:AgentVersion = `"$InstalledVersion`"`n"
    )
}

function Invoke-TestManifest {
    param($RequestParams)
    $script:capturedManifestRequest = $RequestParams
    [pscustomobject]@{ version = $script:mockManifestVersion; sha256 = $script:mockManifestSha256; target_agent_version = $script:mockManifestTargetVersion }
}

function Invoke-TestDownload {
    param($RequestParams)
    $script:capturedDownloadRequest = $RequestParams
    [System.IO.File]::WriteAllBytes($RequestParams.OutFile, $script:mockDownloadBytes)
}

function Invoke-ValidSignature {
    param($Path)
    [pscustomobject]@{ Status = "Valid" }
}

function Invoke-InvalidSignature {
    param($Path)
    [pscustomobject]@{ Status = "NotSigned" }
}

# --- Get-AgentInstalledVersion -------------------------------------------------------------

$versionTestDir = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-updater-version-$([guid]::NewGuid().ToString('N'))"
New-AgentUpdaterTestInstall -InstallPath $versionTestDir -InstalledVersion "2.3.4"
try {
    $installedVersion = Get-AgentInstalledVersion -AgentScriptPath (Join-Path $versionTestDir "itcenter-agent.ps1")
    Assert-True -Condition ($installedVersion -eq "2.3.4") -Message "Get-AgentInstalledVersion must parse `$script:AgentVersion from the installed script."
}
finally {
    Remove-Item -LiteralPath $versionTestDir -Recurse -Force
}

# --- Test-AgentUpdaterReleaseValid ----------------------------------------------------------

$validationTestDir = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-updater-validation-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $validationTestDir | Out-Null
try {
    $sampleFile = Join-Path $validationTestDir "sample.ps1"
    Set-Content -LiteralPath $sampleFile -Encoding UTF8 -Value "Write-Output 'hello'"
    $realHash = (Get-FileHash -LiteralPath $sampleFile -Algorithm SHA256).Hash

    $invalidSignatureResult = Test-AgentUpdaterReleaseValid -FilePath $sampleFile -ExpectedSha256 $realHash -SignatureInvoker ${function:Invoke-InvalidSignature}
    Assert-True -Condition (-not $invalidSignatureResult.IsValid) -Message "Test-AgentUpdaterReleaseValid must reject an invalid signature."
    Assert-True -Condition ($invalidSignatureResult.Reason -like "*signature*") -Message "Rejection reason must mention the signature."

    $hashMismatchResult = Test-AgentUpdaterReleaseValid -FilePath $sampleFile -ExpectedSha256 ("0" * 64) -SignatureInvoker ${function:Invoke-ValidSignature}
    Assert-True -Condition (-not $hashMismatchResult.IsValid) -Message "Test-AgentUpdaterReleaseValid must reject a hash mismatch."
    Assert-True -Condition ($hashMismatchResult.Reason -like "*hash*") -Message "Rejection reason must mention the hash."

    $validResult = Test-AgentUpdaterReleaseValid -FilePath $sampleFile -ExpectedSha256 $realHash -SignatureInvoker ${function:Invoke-ValidSignature}
    Assert-True -Condition $validResult.IsValid -Message "Test-AgentUpdaterReleaseValid must accept a valid signature with a matching hash."
}
finally {
    Remove-Item -LiteralPath $validationTestDir -Recurse -Force
}

# --- Start-ItCenterAgentUpdate: end-to-end scenarios ---------------------------------------

function Invoke-AgentUpdaterScenario {
    param(
        [Parameter(Mandatory = $true)]
        [string]$InstalledVersion,
        [string]$ManifestVersion = "1.1.0",
        [string]$ManifestTargetVersion = $null,
        [scriptblock]$DownloadInvoker = ${function:Invoke-TestDownload},
        [scriptblock]$SignatureInvoker = ${function:Invoke-ValidSignature},
        [string]$DownloadContent = "param()`n`$script:AgentVersion = `"1.1.0`"`n",
        [object]$PreState = $null
    )

    $installDir = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-updater-e2e-$([guid]::NewGuid().ToString('N'))"
    New-AgentUpdaterTestInstall -InstallPath $installDir -InstalledVersion $InstalledVersion

    $script:mockManifestVersion = $ManifestVersion
    $script:mockManifestTargetVersion = $ManifestTargetVersion
    $script:mockDownloadBytes = [System.Text.Encoding]::UTF8.GetBytes($DownloadContent)
    $script:mockManifestSha256 = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new($script:mockDownloadBytes)) -Algorithm SHA256).Hash

    $previousConfigPath = $ConfigPath
    $ConfigPath = Join-Path $installDir "config.json"

    if ($null -ne $PreState) {
        Set-Content -LiteralPath (Join-Path $installDir "update-state.json") -Encoding UTF8 -Value ($PreState | ConvertTo-Json -Depth 5)
    }

    try {
        Start-ItCenterAgentUpdate -ManifestInvoker ${function:Invoke-TestManifest} -DownloadInvoker $DownloadInvoker -SignatureInvoker $SignatureInvoker
        [pscustomobject]@{
            InstallDir = $installDir
            AgentScriptContent = Get-Content -LiteralPath (Join-Path $installDir "itcenter-agent.ps1") -Raw
            PreviousExists = Test-Path -LiteralPath (Join-Path $installDir "itcenter-agent.ps1.previous")
            State = if (Test-Path -LiteralPath (Join-Path $installDir "update-state.json")) { Get-Content -LiteralPath (Join-Path $installDir "update-state.json") -Raw | ConvertFrom-Json } else { $null }
        }
    }
    finally {
        $ConfigPath = $previousConfigPath
        Remove-Item -LiteralPath $installDir -Recurse -Force
    }
}

# Valid update: backup created, script swapped, state recorded.
$validUpdateResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.0.0" -ManifestVersion "1.1.0"
Assert-True -Condition $validUpdateResult.PreviousExists -Message "A valid update must back up the previous script to itcenter-agent.ps1.previous."
Assert-True -Condition ($validUpdateResult.AgentScriptContent -like '*$script:AgentVersion = "1.1.0"*') -Message "A valid update must replace the active script with the new version."
Assert-True -Condition ($validUpdateResult.State.applied_version -eq "1.1.0") -Message "update-state.json must record the applied version."
Assert-True -Condition ($validUpdateResult.State.previous_version -eq "1.0.0") -Message "update-state.json must record the previous version."
Assert-True -Condition ($validUpdateResult.State.confirmed -eq $false) -Message "A freshly applied update must not be marked confirmed yet."

# Invalid signature: nothing replaced.
$invalidSignatureUpdateResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.0.0" -ManifestVersion "1.1.0" -SignatureInvoker ${function:Invoke-InvalidSignature}
Assert-True -Condition (-not $invalidSignatureUpdateResult.PreviousExists) -Message "An update with an invalid signature must not create a .previous backup."
Assert-True -Condition ($invalidSignatureUpdateResult.AgentScriptContent -like '*$script:AgentVersion = "1.0.0"*') -Message "An update with an invalid signature must leave the installed script untouched."
Assert-True -Condition ($null -eq $invalidSignatureUpdateResult.State) -Message "An update with an invalid signature must not create update-state.json."

# Hash mismatch: nothing replaced. Force a mismatch by hashing different content than what is served.
function Invoke-TestDownloadWrongContent {
    param($RequestParams)
    Set-Content -LiteralPath $RequestParams.OutFile -Encoding UTF8 -Value "param()`n`$script:AgentVersion = `"tampered`"`n"
}
$hashMismatchUpdateResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.0.0" -ManifestVersion "1.1.0" -DownloadInvoker ${function:Invoke-TestDownloadWrongContent}
Assert-True -Condition (-not $hashMismatchUpdateResult.PreviousExists) -Message "An update with a hash mismatch must not create a .previous backup."
Assert-True -Condition ($hashMismatchUpdateResult.AgentScriptContent -like '*$script:AgentVersion = "1.0.0"*') -Message "An update with a hash mismatch must leave the installed script untouched."

# Already up to date: no-op.
$upToDateResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.1.0" -ManifestVersion "1.1.0"
Assert-True -Condition (-not $upToDateResult.PreviousExists) -Message "An already up-to-date agent must not be touched."
Assert-True -Condition ($null -eq $upToDateResult.State) -Message "An already up-to-date agent must not gain an update-state.json."

# Hold-back: target_agent_version differs from manifest version.
$holdBackResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.0.0" -ManifestVersion "1.1.0" -ManifestTargetVersion "1.0.0"
Assert-True -Condition (-not $holdBackResult.PreviousExists) -Message "A machine pinned via target_agent_version must not be updated."
Assert-True -Condition ($holdBackResult.AgentScriptContent -like '*$script:AgentVersion = "1.0.0"*') -Message "A held-back machine must keep its installed version."

# Rollback: enough consecutive failures since the last applied update restores .previous.
$installDirForRollback = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-updater-rollback-$([guid]::NewGuid().ToString('N'))"
New-AgentUpdaterTestInstall -InstallPath $installDirForRollback -InstalledVersion "1.1.0"
Set-Content -LiteralPath (Join-Path $installDirForRollback "itcenter-agent.ps1.previous") -Encoding UTF8 -Value "param()`n`$script:AgentVersion = `"1.0.0`"`n"
Set-Content -LiteralPath (Join-Path $installDirForRollback "update-state.json") -Encoding UTF8 -Value (
    [ordered]@{
        applied_version = "1.1.0"
        previous_version = "1.0.0"
        updated_at = "2026-08-19T00:00:00Z"
        consecutive_checkin_failures = 5
        consecutive_checkin_successes = 0
        confirmed = $false
    } | ConvertTo-Json
)
$script:mockManifestVersion = "1.1.0"
$script:mockManifestTargetVersion = $null
$previousConfigPathForRollback = $ConfigPath
$ConfigPath = Join-Path $installDirForRollback "config.json"
try {
    Start-ItCenterAgentUpdate -ManifestInvoker ${function:Invoke-TestManifest} -SignatureInvoker ${function:Invoke-ValidSignature}
    $rolledBackContent = Get-Content -LiteralPath (Join-Path $installDirForRollback "itcenter-agent.ps1") -Raw
    $rolledBackState = Get-Content -LiteralPath (Join-Path $installDirForRollback "update-state.json") -Raw | ConvertFrom-Json
    Assert-True -Condition ($rolledBackContent -like '*$script:AgentVersion = "1.0.0"*') -Message "5 consecutive check-in failures must trigger a rollback to the previous version."
    Assert-True -Condition ($null -eq $rolledBackState.applied_version) -Message "A rollback must clear the pending update state."
}
finally {
    $ConfigPath = $previousConfigPathForRollback
    Remove-Item -LiteralPath $installDirForRollback -Recurse -Force
}

# Confirm: enough consecutive successes marks the pending update confirmed (no rollback).
$installDirForConfirm = Join-Path ([System.IO.Path]::GetTempPath()) "itcenter-updater-confirm-$([guid]::NewGuid().ToString('N'))"
New-AgentUpdaterTestInstall -InstallPath $installDirForConfirm -InstalledVersion "1.1.0"
Set-Content -LiteralPath (Join-Path $installDirForConfirm "update-state.json") -Encoding UTF8 -Value (
    [ordered]@{
        applied_version = "1.1.0"
        previous_version = "1.0.0"
        updated_at = "2026-08-19T00:00:00Z"
        consecutive_checkin_failures = 0
        consecutive_checkin_successes = 3
        confirmed = $false
    } | ConvertTo-Json
)
$script:mockManifestVersion = "1.1.0"
$script:mockManifestTargetVersion = $null
$previousConfigPathForConfirm = $ConfigPath
$ConfigPath = Join-Path $installDirForConfirm "config.json"
try {
    Start-ItCenterAgentUpdate -ManifestInvoker ${function:Invoke-TestManifest} -SignatureInvoker ${function:Invoke-ValidSignature}
    $confirmedState = Get-Content -LiteralPath (Join-Path $installDirForConfirm "update-state.json") -Raw | ConvertFrom-Json
    Assert-True -Condition ($confirmedState.confirmed -eq $true) -Message "3 consecutive successful check-ins must mark the pending update confirmed."
    Assert-True -Condition (-not (Test-Path -LiteralPath (Join-Path $installDirForConfirm "itcenter-agent.ps1.previous"))) -Message "Confirming an update must not touch the .previous backup."
}
finally {
    $ConfigPath = $previousConfigPathForConfirm
    Remove-Item -LiteralPath $installDirForConfirm -Recurse -Force
}

# No pending state at all: never touches update-state.json, never rolls back/confirms anything.
$noStateResult = Invoke-AgentUpdaterScenario -InstalledVersion "1.1.0" -ManifestVersion "1.1.0"
Assert-True -Condition ($null -eq $noStateResult.State) -Message "A machine with no update-state.json must remain untouched by rollback/confirm logic."

Write-Output "Agent updater tests passed."
