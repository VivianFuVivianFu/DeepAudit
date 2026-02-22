param(
    [string]$Tag = "deep-audit:latest"
)

Write-Host "Checking for Docker daemon..."
try {
    docker version --format '{{.Server.Version}}' > $null 2>&1
} catch {
    Write-Error "Docker daemon not available. Start Docker Desktop and re-run this script."
    exit 1
}

Write-Host "Building Docker image $Tag from current directory..."
docker build -t $Tag .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Built image: $Tag"
