# push-to-github.ps1
# One-shot: make this folder a git repo and push it to GitHub.
# Run it with:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\push-to-github.ps1
#
# It installs Git for Windows if git is missing, initialises the repo,
# commits everything that is not listed in .gitignore, and pushes to main.

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$remoteUrl = 'https://github.com/p88437868-boop/TEXT-TO-IMAGE.git'
$commitMsg = 'TextPic Studio 1.0.3 source'

function Write-Step($text) {
    Write-Host ""
    Write-Host "==> $text" -ForegroundColor Cyan
}

# ---------------------------------------------------------------- 1. git
Write-Step 'Looking for git'
$git = Get-Command git -ErrorAction SilentlyContinue

if (-not $git) {
    Write-Host 'git not found - installing Git for Windows with winget...' -ForegroundColor Yellow
    winget install --id Git.Git --exact --source winget `
        --accept-package-agreements --accept-source-agreements

    # winget updates the machine/user PATH, but this process still has the old one.
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User') + ';' +
                "$env:ProgramFiles\Git\cmd"

    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        throw 'Git was installed but is still not on PATH. Close this window, open a new one, and run this script again.'
    }
}
Write-Host ("Using " + (& git --version))

# ---------------------------------------------------------------- 2. repo
Write-Step 'Initialising repository'
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git'))) {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed.' }
} else {
    Write-Host 'Already a git repository - reusing it.'
}

# Identity is only set locally, and only if you have none configured yet.
if (-not (& git config user.email)) {
    & git config user.email 'p88437868-boop@users.noreply.github.com'
}
if (-not (& git config user.name)) {
    & git config user.name 'p88437868-boop'
}

# ---------------------------------------------------------------- 3. remote
Write-Step 'Pointing origin at GitHub'
& git remote remove origin 2>$null
& git remote add origin $remoteUrl
if ($LASTEXITCODE -ne 0) { throw 'Could not add the origin remote.' }

# ---------------------------------------------------------------- 4. stage
Write-Step 'Staging files (build output, .venv and caches are skipped by .gitignore)'
& git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }

$staged = & git diff --cached --name-only
if (-not $staged) {
    Write-Host 'Nothing new to stage.' -ForegroundColor Yellow
} else {
    Write-Host ("Staged " + ($staged | Measure-Object).Count + " files.")
}

# ---------------------------------------------------------------- 5. commit
Write-Step 'Committing'
& git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Nothing to commit (already committed) - continuing.' -ForegroundColor Yellow
}

# ---------------------------------------------------------------- 6. push
Write-Step 'Pushing to GitHub'
Write-Host 'A browser window may open so you can sign in to GitHub.' -ForegroundColor Yellow
& git push -u origin main
if ($LASTEXITCODE -ne 0) {
    throw 'Push failed. Check the sign-in prompt / token, then run: git push -u origin main'
}

Write-Host ""
Write-Host 'Done: https://github.com/p88437868-boop/TEXT-TO-IMAGE' -ForegroundColor Green
