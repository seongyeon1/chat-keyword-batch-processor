# 통합 배치 시스템 v2.0 사용법

프로시저 없이 쿼리 모듈을 사용하는 새로운 배치 처리 시스템입니다.

## 🚀 빠른 시작

### 1. 배포 (한 번만 실행)

```bash
# 배포 스크립트 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

### 2. Docker Compose 사용 (권장)

```bash
# 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f batch-keywords

# 중지
docker-compose down
```

## 📋 주요 명령어

### 기본 배치 처리

```bash
# 오늘 날짜 처리
docker exec batch-keywords /app/run_batch.sh basic $(date +%Y-%m-%d) $(date +%Y-%m-%d)

# 특정 날짜 처리
docker exec batch-keywords /app/run_batch.sh basic 2025-01-15 2025-01-15

# 기간별 처리
docker exec batch-keywords /app/run_batch.sh basic 2025-01-10 2025-01-15
```

### 누락 데이터 처리

```bash
# 누락 데이터 확인만
docker exec batch-keywords /app/run_batch.sh check 2025-01-10 2025-01-15

# 누락 데이터 처리만
docker exec batch-keywords /app/run_batch.sh missing 2025-01-10 2025-01-15

# 완전한 처리 (기본 + 누락) - 권장
docker exec batch-keywords /app/run_batch.sh complete 2025-01-10 2025-01-15
```

### 시스템 관리

```bash
# 시스템 상태 확인
docker exec batch-keywords /app/validate.sh

# 로그 확인
docker logs batch-keywords

# 컨테이너 재시작
docker restart batch-keywords
```

## 📊 모니터링

### 로그 파일 위치

- **배치 로그**: `./logs/`
- **크론 로그**: `docker logs batch-keywords`
- **보고서**: `./reports/`

### 실시간 로그 모니터링

```bash
# Docker 로그
docker logs -f batch-keywords

# 배치 로그 파일
tail -f logs/*.log

# 특정 날짜 로그
tail -f logs/batch_$(date +%Y%m%d).log
```

## ⚙️ 설정

### 환경변수 (.env 파일)

```bash
# 데이터베이스
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:pass@host:port/db

# HCX API
HCX_CHAT_API_KEY=your-api-key
HCX_MODEL=HCX-005

# 이메일 (선택사항)
SMTP_SERVER=smtp.gmail.com
SENDER_EMAIL=your-email@domain.com
RECIPIENT_EMAILS=user1@domain.com,user2@domain.com
```

### 크론 스케줄 변경

```bash
# docker-compose.yml에서 수정
environment:
  - CRON_SCHEDULE=0 2 * * *  # 매일 새벽 2시로 변경
```

## 🔧 문제 해결

### 일반적인 문제

1. **컨테이너가 시작되지 않음**
   ```bash
   docker logs batch-keywords
   docker exec batch-keywords /app/validate.sh
   ```

2. **데이터베이스 연결 실패**
   ```bash
   # .env 파일의 DATABASE_URL 확인
   docker exec batch-keywords python -c "from core.config import Config; print('DB 연결 테스트')"
   ```

3. **HCX API 오류**
   ```bash
   # API 키 확인
   docker exec batch-keywords python -c "from services.hcx_service import HCXService; print('HCX 연결 테스트')"
   ```

### 성능 최적화

```bash
# 메모리 사용량 확인
docker stats batch-keywords

# 디스크 공간 확인
docker exec batch-keywords df -h

# 오래된 로그 정리
find logs/ -name "*.log" -mtime +30 -delete
find reports/ -name "*.xlsx" -mtime +30 -delete
```

## 📈 사용 예시

### 일일 배치 처리

```bash
# 어제 데이터 완전 처리
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
docker exec batch-keywords /app/run_batch.sh complete $YESTERDAY $YESTERDAY
```

### 주간 누락 데이터 정리

```bash
# 지난 주 누락 데이터 처리
WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
docker exec batch-keywords /app/run_batch.sh missing $WEEK_AGO $YESTERDAY
```

### 월간 보고서 생성

```bash
# 지난 달 전체 데이터 확인
LAST_MONTH_START=$(date -d "last month" +%Y-%m-01)
LAST_MONTH_END=$(date -d "$(date +%Y-%m-01) - 1 day" +%Y-%m-%d)
docker exec batch-keywords /app/run_batch.sh check $LAST_MONTH_START $LAST_MONTH_END
```

## 🆘 지원

문제가 발생하면 다음 정보를 수집해서 문의하세요:

```bash
# 시스템 정보 수집
echo "=== 시스템 상태 ===" > debug_info.txt
docker exec batch-keywords /app/validate.sh >> debug_info.txt
echo "" >> debug_info.txt
echo "=== 최근 로그 ===" >> debug_info.txt
docker logs --tail=50 batch-keywords >> debug_info.txt
echo "" >> debug_info.txt
echo "=== 리소스 사용량 ===" >> debug_info.txt
docker stats --no-stream batch-keywords >> debug_info.txt
```

## 📋 사용법 가이드

## 🚀 빠른 시작

### 📦 필수 환경 설정

## ⚠️ 문제 해결

### EOF 오류 ("EOF when reading a line")

**증상**: `❓ 31개의 누락 데이터를 처리하시겠습니까? (y/N): ❌ 누락 데이터 처리 실패: EOF when reading a line`

**원인**: 
- 비대화형 환경(Docker, CI/CD, 백그라운드)에서 실행
- 터미널이 연결되지 않은 상태
- 입력 스트림 리다이렉션 사용

**해결 방법**:
1. **자동 처리 모드 사용 (권장)**:
   ```bash
   # 기본적으로 이제 자동 확인 모드로 실행됩니다
   python run_advanced_batch.py missing 2025-06-11 2025-06-19
   ```

2. **대화형 터미널에서 실행**:
   ```bash
   # Windows PowerShell, CMD, 또는 WSL에서 직접 실행
   python run_advanced_batch.py missing 2025-06-11 2025-06-19
   ```

3. **Docker 컨테이너에서 실행 시**:
   ```bash
   # -it 옵션 추가
   docker run -it your-container python run_advanced_batch.py missing 2025-06-11 2025-06-19
   ```

**참고**: 최신 버전에서는 사용자 입력을 받을 수 없는 환경을 자동으로 감지하여 처리를 계속 진행합니다.

이 가이드로 새로운 통합 배치 시스템을 효율적으로 사용할 수 있습니다! 