# Integrated Batch System v2.0 Deployment Script (English Version)

Write-Host "=== Integrated Batch System v2.0 Deployment Started ===" -ForegroundColor Green
Write-Host "Deployment Time: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# 1. Backup existing files
Write-Host "Step 1: Backing up existing files..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (Test-Path "requirements.txt") {
    Copy-Item "requirements.txt" "requirements_backup_$timestamp.txt"
    Write-Host "  [OK] requirements.txt backed up"
} else {
    Write-Host "  [INFO] No existing requirements.txt found"
}

if (Test-Path "Dockerfile") {
    Copy-Item "Dockerfile" "Dockerfile_backup_$timestamp"
    Write-Host "  [OK] Dockerfile backed up"
} else {
    Write-Host "  [INFO] No existing Dockerfile found"
}

# 2. Replace with new files
Write-Host ""
Write-Host "Step 2: Replacing with new files..." -ForegroundColor Cyan

if (Test-Path "requirements_step3.txt") {
    Copy-Item "requirements_step3.txt" "requirements.txt"
    Write-Host "  [OK] requirements.txt <- requirements_step3.txt"
} else {
    Write-Host "  [ERROR] requirements_step3.txt not found!" -ForegroundColor Red
    exit 1
}

if (Test-Path "Dockerfile.production") {
    Copy-Item "Dockerfile.production" "Dockerfile"
    Write-Host "  [OK] Dockerfile <- Dockerfile.production"
} else {
    Write-Host "  [ERROR] Dockerfile.production not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[SUCCESS] File replacement completed" -ForegroundColor Green
Write-Host ""

# 3. Docker build
Write-Host "Step 3: Building Docker image..." -ForegroundColor Cyan
$buildResult = docker build --no-cache -t batch-keywords:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Docker build completed!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4. Stop and remove existing containers
Write-Host "Step 4: Cleaning up existing containers..." -ForegroundColor Cyan

# Stop container
$stopResult = docker stop batch-keywords 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Existing container stopped"
} else {
    Write-Host "  [INFO] No running container found"
}

# Remove container
$removeResult = docker rm batch-keywords 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Existing container removed"
} else {
    Write-Host "  [INFO] No container to remove"
}

# 5. Run new container
Write-Host ""
Write-Host "Step 5: Starting new container..." -ForegroundColor Cyan

$currentPath = (Get-Location).Path
$runResult = docker run -d `
    --name batch-keywords `
    --restart unless-stopped `
    -v "${currentPath}/.env:/app/.env:ro" `
    -v "${currentPath}/logs:/app/logs" `
    -v "${currentPath}/reports:/app/reports" `
    batch-keywords:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Container started successfully!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Container startup failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 6. System validation
Write-Host "Step 6: Validating system..." -ForegroundColor Cyan
Start-Sleep -Seconds 5  # Wait for container startup

docker exec batch-keywords /app/validate.sh

Write-Host ""

# 7. Usage guide
Write-Host "Deployment Complete! Available Commands:" -ForegroundColor Green
Write-Host ""
Write-Host "System Status Check:" -ForegroundColor Yellow
Write-Host "  docker logs batch-keywords"
Write-Host "  docker exec batch-keywords /app/validate.sh"
Write-Host ""
Write-Host "Batch Processing:" -ForegroundColor Yellow
Write-Host "  # Basic batch processing"
Write-Host "  docker exec batch-keywords /app/run_batch.sh basic 2025-01-15 2025-01-15"
Write-Host ""
Write-Host "  # Check missing data"
Write-Host "  docker exec batch-keywords /app/run_batch.sh check 2025-01-10 2025-01-15"
Write-Host ""
Write-Host "  # Process missing data"
Write-Host "  docker exec batch-keywords /app/run_batch.sh missing 2025-01-10 2025-01-15"
Write-Host ""
Write-Host "  # Complete processing (Recommended)"
Write-Host "  docker exec batch-keywords /app/run_batch.sh complete 2025-01-10 2025-01-15"
Write-Host ""
Write-Host "Logs and Reports:" -ForegroundColor Yellow
Write-Host "  - Logs: ./logs/"
Write-Host "  - Reports: ./reports/"
Write-Host ""
Write-Host "Auto Schedule: Daily at 1:00 AM (Previous day data)" -ForegroundColor Yellow
Write-Host ""
Write-Host "=== Deployment Completed! ===" -ForegroundColor Green 