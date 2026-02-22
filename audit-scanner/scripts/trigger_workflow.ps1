<#
Trigger a GitHub Actions workflow dispatch using the REST API.

Usage:
  $env:GITHUB_TOKEN = '<your-token>'
  .\trigger_workflow.ps1 -Repo 'owner/repo' -WorkflowFile 'docker_build_and_publish.yml' -Ref 'main'

Minimum requirements:
- A GitHub Personal Access Token with `repo` and `workflow` scope set in `GITHUB_TOKEN` env var (recommended) or passed via `-Token`.
#>

param(
    [string]$Repo = $env:GITHUB_REPO,
    [string]$WorkflowFile = 'docker_build_and_publish.yml',
    [string]$Ref = 'main',
    [string]$Token = $env:GITHUB_TOKEN
)

function Get-GitHubRepoFromOrigin {
    try {
        $url = git remote get-url origin 2>$null
        if (-not $url) { return $null }
        # normalize SSH or HTTPS URL formats
        if ($url -match 'git@github.com:(.+)\.git') { return $matches[1] }
        if ($url -match 'https?://github.com/(.+)\.git') { return $matches[1] }
        return $null
    } catch {
        return $null
    }
}

if (-not $Repo) {
    $Repo = Get-GitHubRepoFromOrigin
}

if (-not $Repo) {
    Write-Error "Repository not specified. Set -Repo 'owner/repo' or configure git origin."
    exit 2
}

if (-not $Token) {
    Write-Error "GITHUB_TOKEN not set. Export it as an env var or pass -Token <pat>."
    exit 3
}

$uri = "https://api.github.com/repos/$Repo/actions/workflows/$WorkflowFile/dispatches"
$body = @{ ref = $Ref } | ConvertTo-Json

Write-Host "Triggering workflow '$WorkflowFile' on '$Repo' (ref=$Ref)"
try {
    $resp = Invoke-RestMethod -Uri $uri -Method Post -Headers @{ Authorization = "token $Token"; Accept = 'application/vnd.github.v3+json' } -Body $body -ContentType 'application/json'
    Write-Host "Workflow dispatch request sent. Verify on GitHub Actions UI for run status."
} catch {
    Write-Error "Failed to dispatch workflow: $_"
    exit 4
}
