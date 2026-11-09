[CmdletBinding()]
param(
    [string]$Msi
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an elevated PowerShell session.'
}

if (-not $Msi) {
    $Msi = Join-Path (Split-Path -Parent $PSScriptRoot) 'dist\TextPicStudio-1.0.3-x64.msi'
}
$Msi = (Resolve-Path -LiteralPath $Msi).Path

$installDir = Join-Path $env:ProgramFiles 'TextPic Studio'
$exe = Join-Path $installDir 'TextPicStudio.exe'
$desktopShortcut = Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) 'TextPic Studio.lnk'
$startMenuShortcut = Join-Path ([Environment]::GetFolderPath('CommonPrograms')) 'TextPic Studio\TextPic Studio.lnk'
$appPathsKey = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths\TextPicStudio.exe'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$appData = Join-Path $env:APPDATA 'TextPicStudio'
$marker = Join-Path $appData 'msi-smoke-marker.txt'
$markerValue = [guid]::NewGuid().ToString()
$report = Join-Path $env:TEMP 'textpic-msi-smoke.txt'
$installLog1 = Join-Path $env:TEMP 'textpic-msi-install-autostart.log'
$installLog2 = Join-Path $env:TEMP 'textpic-msi-install-default.log'
$uninstallLog1 = Join-Path $env:TEMP 'textpic-msi-uninstall-autostart.log'
$uninstallLog2 = Join-Path $env:TEMP 'textpic-msi-uninstall-default.log'
$results = New-Object System.Collections.Generic.List[string]
$failed = $false

function Add-Result([string]$Text) {
    $script:results.Add($Text)
    Write-Host $Text
}

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) {
        throw $Message
    }
}

function Install-TestPackage([string]$Autostart, [string]$LogPath) {
    $arguments = "/i `"$Msi`" /qn /norestart AUTOSTART=$Autostart /l*v `"$LogPath`""
    $process = Start-Process -FilePath msiexec.exe -ArgumentList $arguments -Wait -PassThru
    Assert-True ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) "Install exited with code $($process.ExitCode)."
}

function Uninstall-TestPackage([string]$LogPath) {
    $arguments = "/x `"$Msi`" /qn /norestart /l*v `"$LogPath`""
    $process = Start-Process -FilePath msiexec.exe -ArgumentList $arguments -Wait -PassThru
    Assert-True ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) "Uninstall exited with code $($process.ExitCode)."
}

function Assert-Shortcut([string]$Path) {
    Assert-True (Test-Path -LiteralPath $Path) "Missing shortcut: $Path"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    Assert-True ($shortcut.TargetPath -eq $exe) "Shortcut target mismatch: $Path -> $($shortcut.TargetPath)"
}

function Assert-Autostart([bool]$Expected) {
    $value = $null
    try {
        $value = Get-ItemPropertyValue -Path $runKey -Name TextPicStudio -ErrorAction Stop
    }
    catch {
        $value = $null
    }
    if ($Expected) {
        Assert-True ($null -ne $value) 'Autostart Run value was not created.'
        Assert-True ($value -like "*$exe*") "Autostart Run value points to the wrong executable: $value"
    }
    else {
        Assert-True ($null -eq $value) 'Autostart Run value was not removed.'
    }
}

try {
    Assert-True (-not (Get-Process -Name TextPicStudio -ErrorAction SilentlyContinue)) 'TextPic Studio is running.'
    Assert-True (-not (Test-Path -LiteralPath $installDir)) "Existing installation found at $installDir."
    Assert-True (-not (Test-Path -LiteralPath $appPathsKey)) 'Existing App Paths registration found.'

    New-Item -ItemType Directory -Path $appData -Force | Out-Null
    Set-Content -LiteralPath $marker -Value $markerValue -Encoding ascii

    Add-Result 'Install with AUTOSTART=1'
    Install-TestPackage -Autostart 1 -LogPath $installLog1
    Assert-True (Test-Path -LiteralPath $exe) 'Installed executable is missing.'
    Assert-True (Test-Path -LiteralPath $appPathsKey) 'App Paths registration is missing.'
    Assert-Shortcut $desktopShortcut
    Assert-Shortcut $startMenuShortcut
    Assert-Autostart $true
    $selftest = Start-Process -FilePath $exe -ArgumentList '--selftest' -Wait -PassThru
    Assert-True ($selftest.ExitCode -eq 0) "Installed executable selftest exited with $($selftest.ExitCode)."
    Add-Result 'Autostart install verified'

    Add-Result 'Uninstall autostart install'
    Uninstall-TestPackage -LogPath $uninstallLog1
    Assert-True (-not (Test-Path -LiteralPath $installDir)) 'Install directory still exists after uninstall.'
    Assert-True (-not (Test-Path -LiteralPath $desktopShortcut)) 'Desktop shortcut still exists after uninstall.'
    Assert-True (-not (Test-Path -LiteralPath $startMenuShortcut)) 'Start menu shortcut still exists after uninstall.'
    Assert-True (-not (Test-Path -LiteralPath $appPathsKey)) 'App Paths registration still exists after uninstall.'
    Assert-Autostart $false
    Assert-True ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $markerValue) 'User data was removed during uninstall.'
    Add-Result 'Autostart uninstall verified'

    Add-Result 'Install with default autostart setting'
    Install-TestPackage -Autostart 0 -LogPath $installLog2
    Assert-Autostart $false
    Assert-True (Test-Path -LiteralPath $exe) 'Installed executable is missing on default install.'
    Add-Result 'Default install verified'

    Add-Result 'Uninstall default install'
    Uninstall-TestPackage -LogPath $uninstallLog2
    Assert-True (-not (Test-Path -LiteralPath $installDir)) 'Install directory still exists after default uninstall.'
    Assert-True ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $markerValue) 'User data was removed during default uninstall.'
    Add-Result 'Default uninstall verified'

    Add-Result 'PASS: MSI install, shortcuts, autostart, selftest, uninstall, and data preservation verified.'
}
catch {
    $failed = $true
    Add-Result "FAIL: $($_.Exception.Message)"
    try {
        if (Test-Path -LiteralPath $appPathsKey) {
            Uninstall-TestPackage -LogPath $uninstallLog2
        }
    }
    catch {
        Add-Result "Cleanup failed: $($_.Exception.Message)"
    }
}
finally {
    Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
    $results | Set-Content -LiteralPath $report -Encoding utf8
    Write-Host "Report: $report"
    if ($failed) {
        exit 1
    }
}
