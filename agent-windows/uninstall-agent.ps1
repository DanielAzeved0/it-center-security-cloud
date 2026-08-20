param(
    [string]$InstallPath = "C:\Program Files\ITCenterAgent",

    [string]$TaskName = "ITCenterAgent",

    [string]$UpdaterTaskName = "ITCenterAgentUpdater",

    [switch]$RemoveFiles,

    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    throw "Run this uninstaller from an elevated PowerShell session."
}

foreach ($scheduledTaskName in @($TaskName, $UpdaterTaskName)) {
    $task = Get-ScheduledTask -TaskName $scheduledTaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $scheduledTaskName -Confirm:$false
        Write-Output "Scheduled task removed: $scheduledTaskName"
    }
    else {
        Write-Output "Scheduled task not found: $scheduledTaskName"
    }
}

if ($RemoveFiles) {
    $agentScript = Join-Path $InstallPath "itcenter-agent.ps1"
    $agentScriptPrevious = Join-Path $InstallPath "itcenter-agent.ps1.previous"
    $updaterScript = Join-Path $InstallPath "itcenter-agent-updater.ps1"
    $installer = Join-Path $InstallPath "install-agent.ps1"
    $uninstaller = Join-Path $InstallPath "uninstall-agent.ps1"
    $config = Join-Path $InstallPath "config.json"
    $updateState = Join-Path $InstallPath "update-state.json"

    foreach ($file in @($agentScript, $agentScriptPrevious, $updaterScript, $installer, $uninstaller, $config, $updateState)) {
        if (Test-Path -LiteralPath $file) {
            Remove-Item -LiteralPath $file -Force
        }
    }

    Write-Output "Agent executable files removed from: $InstallPath"

    # certutil.exe -delstore is used instead of X509Store.Remove() because X509Store.Add() on
    # the Root store is known to hang waiting on a Windows security prompt even when called
    # programmatically (see install-agent.ps1); -delstore does not have that issue, but the
    # thumbprint lookup itself (read-only) still uses the .NET certificate store APIs.
    $signingCertSubject = "CN=IT Center Security Cloud Agent"
    foreach ($storeName in @("Root", "TrustedPublisher")) {
        $matchingCerts = @(Get-ChildItem "Cert:\LocalMachine\$storeName" | Where-Object { $_.Subject -eq $signingCertSubject })
        foreach ($cert in $matchingCerts) {
            & certutil.exe -delstore $storeName $cert.Thumbprint | Out-Null
        }
    }

    Write-Output "Agent signing certificate removed from LocalMachine Root and TrustedPublisher (if present)."
}

if ($RemoveData) {
    foreach ($directoryName in @("logs", "cache")) {
        $directory = Join-Path $InstallPath $directoryName
        if (Test-Path -LiteralPath $directory) {
            Remove-Item -LiteralPath $directory -Recurse -Force
        }
    }

    Write-Output "Agent logs and cache removed from: $InstallPath"
}

if ((Test-Path -LiteralPath $InstallPath) -and $RemoveFiles -and $RemoveData) {
    $remainingItems = @(Get-ChildItem -LiteralPath $InstallPath -Force -ErrorAction SilentlyContinue)
    if ($remainingItems.Count -eq 0) {
        Remove-Item -LiteralPath $InstallPath -Force
        Write-Output "Install directory removed: $InstallPath"
    }
}

Write-Output "IT Center Agent uninstall completed."
