#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Start', 'RunDesktop', 'Exit', 'Status', 'StartDisplay', 'StopDisplay', 'RestartDisplay', 'OpenStudio', 'StartStudio', 'RunStudio', 'StopStudio')]
    [string]$Action = 'Status'
)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'Pixel OPs desktop controls require Windows.' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw "Python environment is missing: $python" }
$prefix = 'Pixel OPs'
$settingsPath = Join-Path $repoRoot 'pixel_ops/cache/desktop/tasks.json'
if (Test-Path -LiteralPath $settingsPath) { $prefix = (Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json).prefix }

function Invoke-Controller([string]$Command) {
    & $python -m pixel_ops.desktop $Command
    if ($LASTEXITCODE -ne 0) { throw "Pixel OPs action '$Command' failed. See pixel_ops/output/desktop.log." }
}

Push-Location -LiteralPath $repoRoot
try {
    switch ($Action) {
        'Start' {
            $task = Get-ScheduledTask -TaskName "$prefix - Desktop" -ErrorAction SilentlyContinue
            if ($task) { Start-ScheduledTask -InputObject $task }
            else { Invoke-Controller 'start-desktop' }
        }
        'RunDesktop' { Invoke-Controller 'run-desktop' }
        'RunStudio' { Invoke-Controller 'run-studio' }
        'OpenStudio' {
            $status = & $python -m pixel_ops.desktop status | ConvertFrom-Json
            if ($LASTEXITCODE -ne 0) { throw 'Cannot read Pixel OPs process status.' }
            if (-not $status.studio.running) {
                $task = Get-ScheduledTask -TaskName "$prefix - Config Studio" -ErrorAction SilentlyContinue
                if ($task) { Start-ScheduledTask -InputObject $task }
                else { Invoke-Controller 'start-studio' }
            }
            Invoke-Controller 'wait-studio'
            Invoke-Controller 'open-browser'
        }
        'Status' { Invoke-Controller 'status' }
        'Exit' { Invoke-Controller 'exit' }
        'StartStudio' { Invoke-Controller 'start-studio' }
        'StopStudio' { Invoke-Controller 'stop-studio' }
        'StartDisplay' { Invoke-Controller 'start-display' }
        'StopDisplay' { Invoke-Controller 'stop-display' }
        'RestartDisplay' { Invoke-Controller 'restart-display' }
    }
}
finally { Pop-Location }
