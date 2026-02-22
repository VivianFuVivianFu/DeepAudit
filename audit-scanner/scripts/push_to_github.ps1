<#
Push the current repository to GitHub, using `GITHUB_TOKEN` for authentication.

Usage:
  $env:GITHUB_TOKEN = '<PERSONAL_ACCESS_TOKEN>'
  .\push_to_github.ps1 -Repo 'owner/repo' -Branch 'main'

Notes:
- The script will initialize a git repo if one is not present, create an initial commit,
  add the remote using the token for HTTPS authentication, and push the branch.
- For security, prefer creating a deploy token with minimal scopes and unset the env var after use.
#>

param(
    [Parameter(Mandatory=$true)] [string]$Repo,
    [string]$Branch = 'main',
    [string]$CommitMessage = 'Initial commit: enterprise upgrade'
)

$Token = $env:GITHUB_TOKEN
if (-not $Token) {
    Write-Error "GITHUB_TOKEN environment variable is not set. Export a PAT with repo+workflow scopes and retry."
    exit 2
}

function Run-Git([string]$args) {
    Write-Host "> git $args"
    $res = git $args
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git $args failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..."
    Run-Git "init"
}

Run-Git "add -A"

try {
    Run-Git "commit -m \"$CommitMessage\""
} catch {
    Write-Host "No changes to commit or commit failed; continuing..."
}

$remoteUrl = "https://$($Token)@github.com/$Repo.git"

try {
    git remote remove origin 2>$null
} catch {}

Run-Git "remote add origin $remoteUrl"
Run-Git "branch -M $Branch"
Run-Git "push -u origin $Branch"

Write-Host "Push complete. Please remove the token from environment for security: Remove-Item Env:\GITHUB_TOKEN"
