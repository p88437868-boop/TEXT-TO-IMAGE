[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipAppBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
Push-Location -LiteralPath $root
try {
    $python = Join-Path $root '.venv\Scripts\python.exe'
    $wix = Join-Path $root '.tools\wix\wix.exe'
    $spec = Join-Path $root 'TextPicStudio.spec'
    $appDir = Join-Path $root 'dist\TextPicStudio'
    $appFiles = Join-Path $root 'installer\AppFiles.wxs'

    if (-not (Test-Path -LiteralPath $python)) {
        throw "Python environment not found at $python. See README.md for setup."
    }
    if (-not (Test-Path -LiteralPath $wix)) {
        throw "WiX not found at $wix. See README.md for installation."
    }

    $versionLine = Select-String -Path (Join-Path $root 'src\textpic\__version__.py') -Pattern '^VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
    if (-not $versionLine) {
        throw 'Could not read VERSION from src\textpic\__version__.py.'
    }
    $version = $versionLine.Matches[0].Groups[1].Value
    $packageText = Get-Content -LiteralPath (Join-Path $root 'installer\Package.wxs') -Raw
    if ($packageText -notmatch ('Version="' + [regex]::Escape($version) + '"')) {
        throw "installer\Package.wxs Version does not match application version $version."
    }

    if (-not $SkipTests) {
        $env:PYTHONPATH = Join-Path $root 'src'
        & $python -m pytest
        if ($LASTEXITCODE -ne 0) {
            throw "Tests failed with exit code $LASTEXITCODE."
        }
    }

    if (-not $SkipAppBuild) {
        $running = Get-Process -Name TextPicStudio -ErrorAction SilentlyContinue
        if ($running) {
            throw 'TextPic Studio is running. Close it before rebuilding the application.'
        }

        & $python -m PyInstaller --noconfirm --clean --log-level WARN $spec
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller failed with exit code $LASTEXITCODE."
        }
    }

    if (-not (Test-Path -LiteralPath $appDir)) {
        throw "Application build not found at $appDir."
    }

    & $python (Join-Path $root 'tools\generate_wix.py') --dist $appDir --out $appFiles
    if ($LASTEXITCODE -ne 0) {
        throw "WiX file generation failed with exit code $LASTEXITCODE."
    }

    $msi = Join-Path $root "dist\TextPicStudio-$version-x64.msi"
    $rootDir = $root.TrimEnd('\') + '\'
    & $wix build (Join-Path $root 'installer\Package.wxs') $appFiles -ext WixToolset.UI.wixext -arch x64 -d "RootDir=$rootDir" -d "DistDir=$appDir" -o $msi -pdbtype none
    if ($LASTEXITCODE -ne 0) {
        throw "WiX build failed with exit code $LASTEXITCODE."
    }

    $hash = (Get-FileHash -LiteralPath $msi -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash *$(Split-Path -Leaf $msi)" | Set-Content -LiteralPath "$msi.sha256" -Encoding ascii

    $item = Get-Item -LiteralPath $msi
    Write-Host ''
    Write-Host "Built: $($item.FullName)"
    Write-Host "Size:  $($item.Length) bytes"
    Write-Host "SHA256: $hash"
}
finally {
    Pop-Location
}
