# PowerShell 배치 처리 백그라운드 실행 및 로그 확인 스크립트 (Windows 서버용)

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Action,
    
    [Parameter(Position=1)]
    [string]$StartDate,
    
    [Parameter(Position=2)]
    [string]$EndDate
)

# 색상 함수
function Write-ColorText {
    param([string]$Text, [string]$Color = "White")
    
    $colors = @{
        "Red" = "Red"
        "Green" = "Green" 
        "Yellow" = "Yellow"
        "Blue" = "Blue"
        "White" = "White"
    }
    
    Write-Host $Text -ForegroundColor $colors[$Color]
}

# 환경 감지 함수
function Get-Environment {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        return "docker_host"
    } elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        return "docker_available"
    } else {
        return "no_docker"
    }
}

$envType = Get-Environment

# 사용법 출력 함수
function Show-Usage {
    Write-ColorText "=== 채팅 키워드 배치 처리 도구 (Windows 서버용) ===" "Blue"
    Write-ColorText "환경: $envType" "Blue"
    Write-Host ""
    Write-ColorText "사용법:" "Blue"
    Write-Host "  .\run_batch_background.ps1 run <start-date> <end-date>    # 기간별 배치 실행"
    Write-Host "  .\run_batch_background.ps1 run <target-date>             # 단일 날짜 배치 실행"
    Write-Host "  .\run_batch_background.ps1 logs                          # 실시간 로그 확인"
    Write-Host "  .\run_batch_background.ps1 status                        # 컨테이너 상태 확인"
    Write-Host "  .\run_batch_background.ps1 stop                          # 실행 중인 배치 중지"
    Write-Host "  .\run_batch_background.ps1 cleanup                       # 오래된 로그 파일 정리"
    Write-Host ""
    Write-ColorText "예제:" "Blue"
    Write-Host "  .\run_batch_background.ps1 run 2025-06-11 2025-06-15     # 2025-06-11부터 2025-06-15까지 처리"
    Write-Host "  .\run_batch_background.ps1 run 2025-06-15                # 2025-06-15만 처리"
    Write-Host "  .\run_batch_background.ps1 logs                          # 로그 실시간 확인"
}

# Docker 명령어 생성 함수
function Get-DockerCommand {
    param([string]$CmdArgs)
    
    switch ($envType) {
        "docker_host" {
            if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
                return "docker-compose exec -T keyword-batch python chat_keyword_batch.py $CmdArgs"
            } else {
                return "docker exec -i keyword-batch python chat_keyword_batch.py $CmdArgs"
            }
        }
        "docker_available" {
            return "docker exec -i keyword-batch python chat_keyword_batch.py $CmdArgs"
        }
        default {
            Write-ColorText "❌ Docker 환경을 찾을 수 없습니다." "Red"
            exit 1
        }
    }
}

# 배치 실행 함수
function Start-Batch {
    param([string]$StartDate, [string]$EndDate)
    
    if (-not $StartDate) {
        Write-ColorText "❌ 오류: 날짜를 입력해주세요" "Red"
        Show-Usage
        exit 1
    }
    
    # 로그 파일명 생성
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logFile = ""
    $cmdArgs = ""
    
    if ($EndDate) {
        # 기간별 처리
        $logFile = "logs\batch_range_${StartDate}_to_${EndDate}_${timestamp}.log"
        $cmdArgs = "--start-date $StartDate --end-date $EndDate"
        Write-ColorText "🚀 기간별 배치 시작: $StartDate ~ $EndDate" "Green"
    } else {
        # 단일 날짜 처리
        $logFile = "logs\batch_single_${StartDate}_${timestamp}.log"
        $cmdArgs = "--target-date $StartDate"
        Write-ColorText "🚀 단일 날짜 배치 시작: $StartDate" "Green"
    }
    
    # 로그 디렉토리 생성
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
    }
    
    # Docker 컨테이너 상태 확인
    Write-ColorText "🔍 Docker 컨테이너 상태 확인..." "Blue"
    
    try {
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            $containerStatus = docker-compose ps keyword-batch 2>$null
            if (-not ($containerStatus -match "Up")) {
                Write-ColorText "⚠️ keyword-batch 컨테이너가 실행되지 않았습니다. 시작합니다..." "Yellow"
                docker-compose up -d keyword-batch
                Start-Sleep -Seconds 5
            }
        } else {
            $containerStatus = docker ps --filter name=keyword-batch 2>$null
            if (-not ($containerStatus -match "keyword-batch")) {
                Write-ColorText "❌ keyword-batch 컨테이너를 찾을 수 없습니다." "Red"
                Write-Host "수동으로 컨테이너를 시작하거나 docker-compose를 사용해주세요."
                exit 1
            }
        }
    } catch {
        Write-ColorText "❌ Docker 상태 확인 실패: $_" "Red"
        exit 1
    }
    
    # 실행 명령어 생성
    $dockerCmd = Get-DockerCommand $cmdArgs
    
    # 백그라운드에서 배치 실행
    Write-ColorText "📝 로그 파일: $logFile" "Blue"
    Write-ColorText "🔧 실행 명령: $dockerCmd" "Blue"
    
    try {
        # PowerShell Job으로 백그라운드 실행
        $job = Start-Job -ScriptBlock {
            param($cmd, $log)
            Invoke-Expression "$cmd" *> $log
        } -ArgumentList $dockerCmd, $logFile
        
        $jobId = $job.Id
        
        Write-ColorText "✅ 배치가 백그라운드에서 시작되었습니다 (Job ID: $jobId)" "Green"
        Write-ColorText "📊 Job ID를 기록합니다..." "Blue"
        "$jobId" | Out-File "logs\batch_${timestamp}.job" -Encoding UTF8
        
        # 잠시 대기 후 초기 로그 출력
        Start-Sleep -Seconds 3
        Write-ColorText "📋 초기 로그:" "Yellow"
        if (Test-Path $logFile) {
            Get-Content $logFile -Tail 15
        } else {
            Write-Host "로그 파일이 아직 생성되지 않았습니다. 잠시 후 다시 확인해주세요."
        }
        
        Write-Host ""
        Write-ColorText "💡 유용한 명령어:" "Green"
        Write-Host "  실시간 로그 확인: .\run_batch_background.ps1 logs"
        Write-Host "  또는: Get-Content $logFile -Wait"
        Write-Host "  배치 중지: .\run_batch_background.ps1 stop"
        Write-Host "  상태 확인: .\run_batch_background.ps1 status"
        
    } catch {
        Write-ColorText "❌ 배치 실행 실패: $_" "Red"
        exit 1
    }
}

# 로그 확인 함수
function Show-Logs {
    Write-ColorText "📋 사용 가능한 로그 파일들:" "Blue"
    
    if (-not (Test-Path "logs")) {
        Write-ColorText "❌ logs 디렉토리가 없습니다." "Red"
        exit 1
    }
    
    # 최근 로그 파일들 목록 출력
    $logFiles = Get-ChildItem "logs\batch_*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10
    
    if (-not $logFiles) {
        Write-ColorText "⚠️ 로그 파일이 없습니다." "Yellow"
        Write-Host "먼저 배치를 실행해주세요: .\run_batch_background.ps1 run <날짜>"
        exit 1
    }
    
    Write-ColorText "최근 로그 파일들:" "Yellow"
    for ($i = 0; $i -lt $logFiles.Count; $i++) {
        $file = $logFiles[$i]
        $size = [math]::Round($file.Length / 1KB, 2)
        $modified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "  $($i+1). $($file.Name) (크기: ${size}KB, 수정: $modified)"
    }
    
    # 가장 최근 로그 파일 자동 선택
    $latestLog = $logFiles[0].FullName
    Write-Host ""
    Write-ColorText "📖 가장 최근 로그 파일을 실시간으로 보여줍니다: $($logFiles[0].Name)" "Green"
    Write-ColorText "🔄 실시간 로그 (Ctrl+C로 중지):" "Blue"
    Write-Host "----------------------------------------"
    
    # 실시간 로그 출력
    Get-Content $latestLog -Wait
}

# 상태 확인 함수
function Check-Status {
    Write-ColorText "📊 환경 정보: $envType" "Blue"
    
    Write-ColorText "🐳 Docker 컨테이너 상태:" "Blue"
    try {
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            docker-compose ps keyword-batch 2>$null
        } else {
            docker ps --filter name=keyword-batch 2>$null
        }
    } catch {
        Write-Host "Docker 컨테이너 상태 확인 실패"
    }
    
    Write-Host ""
    Write-ColorText "🔍 실행 중인 배치 프로세스:" "Blue"
    
    # 실행 중인 Job 파일들 확인
    if (Test-Path "logs") {
        $jobFiles = Get-ChildItem "logs\batch_*.job" -ErrorAction SilentlyContinue
        
        if (-not $jobFiles) {
            Write-ColorText "⚠️ 실행 중인 배치가 없습니다." "Yellow"
        } else {
            foreach ($jobFile in $jobFiles) {
                $jobId = Get-Content $jobFile.FullName -ErrorAction SilentlyContinue
                if ($jobId) {
                    $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
                    if ($job) {
                        if ($job.State -eq "Running") {
                            Write-ColorText "✅ 실행 중: Job ID $jobId ($($jobFile.Name))" "Green"
                        } else {
                            Write-ColorText "❌ 종료됨: Job ID $jobId ($($jobFile.Name)) - 상태: $($job.State)" "Red"
                            Remove-Item $jobFile.FullName -Force -ErrorAction SilentlyContinue
                        }
                    } else {
                        Write-ColorText "❌ 종료됨: Job ID $jobId ($($jobFile.Name))" "Red"
                        Remove-Item $jobFile.FullName -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    }
    
    Write-Host ""
    Write-ColorText "📈 최근 로그 파일들:" "Blue"
    if (Test-Path "logs") {
        Get-ChildItem "logs\batch_*.log" -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object {
            $size = [math]::Round($_.Length / 1KB, 2)
            Write-Host "  $($_.Name) (크기: ${size}KB)"
        }
    } else {
        Write-ColorText "⚠️ logs 디렉토리가 없습니다." "Yellow"
    }
}

# 배치 중지 함수
function Stop-Batch {
    Write-ColorText "🛑 실행 중인 배치 프로세스를 중지합니다..." "Yellow"
    
    $stoppedCount = 0
    
    if (Test-Path "logs") {
        $jobFiles = Get-ChildItem "logs\batch_*.job" -ErrorAction SilentlyContinue
        
        if (-not $jobFiles) {
            Write-ColorText "⚠️ 실행 중인 배치가 없습니다." "Yellow"
        } else {
            foreach ($jobFile in $jobFiles) {
                $jobId = Get-Content $jobFile.FullName -ErrorAction SilentlyContinue
                if ($jobId) {
                    $job = Get-Job -Id $jobId -ErrorAction SilentlyContinue
                    if ($job -and $job.State -eq "Running") {
                        Write-ColorText "🛑 Job 종료: ID $jobId" "Red"
                        Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                        Remove-Job -Id $jobId -Force -ErrorAction SilentlyContinue
                        $stoppedCount++
                    }
                    Remove-Item $jobFile.FullName -Force -ErrorAction SilentlyContinue
                }
            }
            
            if ($stoppedCount -gt 0) {
                Write-ColorText "✅ $stoppedCount개 배치 프로세스가 중지되었습니다." "Green"
            }
        }
    }
    
    # Docker 컨테이너 내부의 Python 프로세스도 확인
    Write-ColorText "🔍 Docker 컨테이너 내부 프로세스 확인..." "Blue"
    try {
        if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            docker-compose exec -T keyword-batch pkill -f "chat_keyword_batch.py" 2>$null
        } else {
            docker exec keyword-batch pkill -f "chat_keyword_batch.py" 2>$null
        }
    } catch {
        # 무시 (프로세스가 없을 수 있음)
    }
}

# 로그 정리 함수
function Clear-Logs {
    Write-ColorText "🧹 로그 파일 정리 시작..." "Yellow"
    
    if (-not (Test-Path "logs")) {
        Write-ColorText "⚠️ logs 디렉토리가 없습니다." "Yellow"
        return
    }
    
    # 7일 이전 로그 파일 삭제
    $cutoffDate = (Get-Date).AddDays(-7)
    $oldLogs = Get-ChildItem "logs\batch_*.log" | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    foreach ($oldLog in $oldLogs) {
        Write-Host "  🗑️ 삭제: $($oldLog.Name)"
        Remove-Item $oldLog.FullName -Force
    }
    
    # 오래된 Job 파일 정리
    $cutoffDate = (Get-Date).AddDays(-1)
    $oldJobs = Get-ChildItem "logs\batch_*.job" | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    foreach ($oldJob in $oldJobs) {
        Remove-Item $oldJob.FullName -Force
    }
    
    Write-ColorText "✅ 로그 정리 완료" "Green"
}

# 메인 로직
switch ($Action.ToLower()) {
    "run" {
        if ($EndDate) {
            Start-Batch -StartDate $StartDate -EndDate $EndDate
        } else {
            Start-Batch -StartDate $StartDate
        }
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Check-Status
    }
    "stop" {
        Stop-Batch
    }
    "cleanup" {
        Clear-Logs
    }
    default {
        Write-ColorText "❌ 알 수 없는 명령어: $Action" "Red"
        Write-Host ""
        Show-Usage
        exit 1
    }
} 