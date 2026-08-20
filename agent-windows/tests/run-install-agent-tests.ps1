param(
    [string]$InstallerScriptPath = (Join-Path $PSScriptRoot "..\install-agent.ps1")
)

$ErrorActionPreference = "Stop"

function Assert-Equal {
    param(
        $Expected,
        $Actual,
        [string]$Message
    )

    if ($Expected -ne $Actual) {
        throw "$Message (expected: '$Expected', actual: '$Actual')"
    }
}

$tokens = $null
$parseErrors = $null
$installerAst = [System.Management.Automation.Language.Parser]::ParseFile($InstallerScriptPath, [ref]$tokens, [ref]$parseErrors)

if ($parseErrors.Count -gt 0) {
    throw "Failed to parse $InstallerScriptPath : $($parseErrors -join '; ')"
}

$functionAst = $installerAst.FindAll(
    { param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq "Get-AgentScheduledTaskExecutionPolicy" },
    $true
) | Select-Object -First 1

if ($null -eq $functionAst) {
    throw "Function not found in $InstallerScriptPath : Get-AgentScheduledTaskExecutionPolicy"
}

# Dot-source at script scope (not inside a function) so the function stays available below.
. ([scriptblock]::Create($functionAst.Extent.Text))

$defaultPolicy = Get-AgentScheduledTaskExecutionPolicy
Assert-Equal -Expected "AllSigned" -Actual $defaultPolicy -Message "Default execution policy must be AllSigned (ADR-031)"

$skipPolicy = Get-AgentScheduledTaskExecutionPolicy -SkipSignatureCheck
Assert-Equal -Expected "Bypass" -Actual $skipPolicy -Message "SkipSignatureCheck must fall back to Bypass"

$scheduledTaskArgumentPattern = 'New-ScheduledTaskAction[\s\S]*?-Argument\s+"[^"]*-ExecutionPolicy\s+\$executionPolicy'
$installerContent = Get-Content -LiteralPath $InstallerScriptPath -Raw
Assert-Equal -Expected $true -Actual ([regex]::IsMatch($installerContent, $scheduledTaskArgumentPattern)) `
    -Message "Scheduled task action must use the `$executionPolicy variable, not a hardcoded ExecutionPolicy value"

Write-Output "install-agent.ps1 execution policy tests passed."

# EPIC 22 (ADR-032): the updater must be registered as its own scheduled task, signed and
# validated the same way as the other 3 agent scripts, never with a hardcoded execution policy.
Assert-Equal -Expected $true -Actual ($installerContent -match 'Assert-AgentScriptSignature\s+-Path\s+\$updaterSource') `
    -Message "install-agent.ps1 must validate the updater script signature (Assert-AgentScriptSignature)"

Assert-Equal -Expected $true -Actual ($installerContent -match 'Register-ScheduledTask\s+-TaskName\s+\$UpdaterTaskName') `
    -Message "install-agent.ps1 must register the ITCenterAgentUpdater scheduled task"

# Both the collector's and the updater's New-ScheduledTaskAction must reference $executionPolicy
# (never a hardcoded value) - one match per scheduled task, so exactly 2 across the file.
$scheduledTaskArgumentMatches = [regex]::Matches($installerContent, $scheduledTaskArgumentPattern)
Assert-Equal -Expected 2 -Actual $scheduledTaskArgumentMatches.Count `
    -Message "Both the collector and updater scheduled task actions must use the `$executionPolicy variable"

Write-Output "install-agent.ps1 updater scheduled task tests passed."
