#!/bin/bash
# 통합 배치 시스템 배포 스크립트

echo "=== 🚀 통합 배치 시스템 v2.0 배포 시작 ==="
echo "배포 시간: $(date)"
echo ""

# 1. 기존 파일 백업
echo "1️⃣ 기존 파일 백업 중..."
cp requirements.txt requirements_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "기존 requirements.txt 없음"
cp Dockerfile Dockerfile_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "기존 Dockerfile 없음"

# 2. 새로운 파일로 교체
echo "2️⃣ 새로운 파일로 교체 중..."
cp requirements_step3.txt requirements.txt
cp Dockerfile.production Dockerfile

echo "✅ 파일 교체 완료"
echo "  - requirements.txt ← requirements_step3.txt"
echo "  - Dockerfile ← Dockerfile.production"
echo ""

# 3. Docker 빌드
echo "3️⃣ Docker 이미지 빌드 중..."
docker build --no-cache -t batch-keywords:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker 빌드 성공!"
else
    echo "❌ Docker 빌드 실패!"
    exit 1
fi

echo ""

# 4. 기존 컨테이너 중지 및 제거 (있다면)
echo "4️⃣ 기존 컨테이너 정리 중..."
docker stop batch-keywords 2>/dev/null || echo "실행 중인 컨테이너 없음"
docker rm batch-keywords 2>/dev/null || echo "제거할 컨테이너 없음"

# 5. 새로운 컨테이너 실행
echo "5️⃣ 새로운 컨테이너 실행 중..."
docker run -d \
    --name batch-keywords \
    --restart unless-stopped \
    -v $(pwd)/.env:/app/.env:ro \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/reports:/app/reports \
    batch-keywords:latest

if [ $? -eq 0 ]; then
    echo "✅ 컨테이너 실행 성공!"
else
    echo "❌ 컨테이너 실행 실패!"
    exit 1
fi

echo ""

# 6. 시스템 검증
echo "6️⃣ 시스템 검증 중..."
sleep 5  # 컨테이너 시작 대기

docker exec batch-keywords /app/validate.sh

echo ""

# 7. 사용법 안내
echo "🎯 배포 완료! 사용 가능한 명령어:"
echo ""
echo "📊 시스템 상태 확인:"
echo "  docker logs batch-keywords"
echo "  docker exec batch-keywords /app/validate.sh"
echo ""
echo "🚀 배치 작업 실행:"
echo "  # 기본 배치 처리"
echo "  docker exec batch-keywords /app/run_batch.sh basic 2025-01-15 2025-01-15"
echo ""
echo "  # 누락 데이터 확인"
echo "  docker exec batch-keywords /app/run_batch.sh check 2025-01-10 2025-01-15"
echo ""
echo "  # 누락 데이터 처리"
echo "  docker exec batch-keywords /app/run_batch.sh missing 2025-01-10 2025-01-15"
echo ""
echo "  # 완전한 처리 (권장)"
echo "  docker exec batch-keywords /app/run_batch.sh complete 2025-01-10 2025-01-15"
echo ""
echo "📁 로그 및 보고서:"
echo "  - 로그: ./logs/"
echo "  - 보고서: ./reports/"
echo ""
echo "🔄 자동 스케줄: 매일 새벽 1시 (전날 데이터 처리)"
echo ""
echo "=== 🎉 배포 완료! ===" 