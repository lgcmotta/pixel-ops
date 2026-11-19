#requires -Version 7.0
<#
.SYNOPSIS
Registers current-user interactive tasks. Run this yourself; -WhatIf previews it.
.EXAMPLE
./tools/windows/Register-PixelOpsTasks.ps1 -WhatIf
.EXAMPLE
./tools/windows/Register-PixelOpsTasks.ps1
.EXAMPLE
./tools/windows/Register-PixelOpsTasks.ps1 -StudioAtLogon
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$StudioAtLogon,
    [switch]$Uninstall,
    [ValidatePattern('^[a-zA-Z0-9 _-]+$')]
    [string]$TaskPrefix = 'Pixel OPs'
)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'Scheduled tasks require Windows.' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$launcher = Join-Path $PSScriptRoot 'PixelOps.ps1'
$pwshPath = (Get-Command pwsh -CommandType Application | Select-Object -First 1).Source
$userId = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$definitions = @(
    @{ Name = "$TaskPrefix - Desktop"; Action = 'RunDesktop'; AtLogon = $true },
    @{ Name = "$TaskPrefix - Config Studio"; Action = 'RunStudio'; AtLogon = [bool]$StudioAtLogon }
)
foreach ($definition in $definitions) {
    $existing = Get-ScheduledTask -TaskName $definition.Name -ErrorAction SilentlyContinue
    if ($existing -and -not ($existing.Actions.Arguments -like "*`"$launcher`"*")) {
        throw "Task '$($definition.Name)' belongs to another launcher. Choose another -TaskPrefix."
    }
    if ($Uninstall) {
        if ($existing -and $PSCmdlet.ShouldProcess($definition.Name, 'Unregister scheduled task')) {
            Unregister-ScheduledTask -InputObject $existing -Confirm:$false
        }
        continue
    }
    $arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$launcher`" -Action $($definition.Action)"
    $action = New-ScheduledTaskAction -Execute $pwshPath -Argument $arguments -WorkingDirectory $repoRoot
    $taskParameters = @{ Action = $action; Principal = $principal; Settings = $settings; Description = "Pixel OPs per-user desktop control for $repoRoot" }
    if ($definition.AtLogon) { $taskParameters.Trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId }
    $task = New-ScheduledTask @taskParameters
    if ($PSCmdlet.ShouldProcess("$($definition.Name) ($userId; at logon: $($definition.AtLogon))", 'Register scheduled task')) {
        Register-ScheduledTask -TaskName $definition.Name -InputObject $task -Force | Out-Null
    }
}
if (-not $Uninstall -and -not $WhatIfPreference) {
    $stateDir = Join-Path $repoRoot 'pixel_ops/cache/desktop'
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    @{ prefix = $TaskPrefix } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDir 'tasks.json') -Encoding utf8
    Write-Output 'Tasks registered. Use PixelOps.ps1 -Action Start to start the tray, or sign in again.'
}
