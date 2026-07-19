param(
    [string]$ContainerName = "hazel-memory-test-postgres"
)

$ErrorActionPreference = "Stop"
$modelRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $modelRoot
$existing = docker ps -a --filter "name=^/$ContainerName$" --format "{{.Names}}"

if ($existing) {
    throw "Docker container already exists: $ContainerName"
}

$created = $false
try {
    docker run --detach --name $ContainerName --publish 55433:5432 `
        --env POSTGRES_DB=hazel_test `
        --env POSTGRES_USER=hazel_test `
        --env POSTGRES_PASSWORD=hazel_test `
        pgvector/pgvector:pg16 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start PostgreSQL test container"
    }
    $created = $true

    $ready = $false
    foreach ($attempt in 1..30) {
        docker exec $ContainerName pg_isready -U hazel_test -d hazel_test | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) {
        throw "PostgreSQL test container did not become ready"
    }

    $env:POSTGRES_DSN = "postgresql+psycopg://hazel_test:hazel_test@127.0.0.1:55433/hazel_test"
    & uv run --directory "$repoRoot\database-server" alembic -c alembic.ini upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Memory database migration failed"
    }

    $env:POSTGRES_DSN = "postgresql+asyncpg://hazel_test:hazel_test@127.0.0.1:55433/hazel_test"
    $env:PYTHONPATH = $modelRoot
    & uv run --package hazel-model-server python -m unittest discover -s "$modelRoot\tests" -p "test_*.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Memory integration tests failed"
    }
}
finally {
    if ($created) {
        docker rm --force $ContainerName | Out-Null
    }
}
