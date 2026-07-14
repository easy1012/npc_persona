param([string]$EnvFile = ".env")

$ErrorActionPreference = "Stop"
$TimeoutSeconds = 600
$MaxAttempts = 3
$Services = @("postgres", "neo4j")
$env:COMPOSE_ENV_FILES = $EnvFile
$LogDirectory = Join-Path $PSScriptRoot "..\logs"
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

function Save-Diagnostics([int]$Attempt) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logPath = Join-Path $LogDirectory "startup-$stamp-attempt-$Attempt.log"
    docker compose logs --no-color *> $logPath
    docker compose ps -a | Out-File -Append -Encoding utf8 $logPath
    return $logPath
}

function Test-Healthy {
    foreach ($service in $Services) {
        $containerId = docker compose ps -q $service
        if (-not $containerId) { return $false }
        $health = docker inspect --format "{{.State.Health.Status}}" $containerId
        if ($health -ne "healthy") { return $false }
    }
    return $true
}

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    docker compose up -d postgres neo4j
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Healthy) {
            $receipt = Save-Diagnostics $attempt
            Write-Host "Storage services healthy. Log: $receipt"
            exit 0
        }
        Start-Sleep -Seconds 5
    }
    $receipt = Save-Diagnostics $attempt
    Write-Warning "Attempt $attempt timed out after $TimeoutSeconds seconds. Log: $receipt"
    docker compose stop postgres neo4j
}

throw "Storage services failed after $MaxAttempts attempts. Review logs in $LogDirectory."
