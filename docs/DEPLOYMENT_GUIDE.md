# 🚀 배포 및 실행 가이드

Chat Keyword Batch Processor (리팩토링 버전) 배포 및 실행 방법을 설명합니다.

## 📋 사전 준비

### 1. 시스템 요구사항
- Docker 20.0+ 
- Docker Compose 2.0+
- Git

### 2. 환경 설정 파일 준비

`.env` 파일을 생성하고 다음 환경변수들을 설정하세요:

```bash
# 데이터베이스 연결 정보
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://username:password@host:port/database

# HCX API 설정
HCX_CHAT_API_KEY=your-hcx-api-key
HCX_MODEL=HCX-005

# 이메일 알림 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAILS=admin@example.com,manager@example.com

# 보고서 설정 (선택사항)
REPORT_OUTPUT_DIR=reports
```

## 🐳 Docker 배포

### 1. 저장소 클론
```bash
git clone https://github.com/clabi-lab/batch-keywords.git
cd batch-keywords
git checkout refactored-v2
```

### 2. 환경 설정
```bash
# .env 파일 생성 (.env.example 참고)
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 3. 컨테이너 빌드 및 시작
```bash
# 컨테이너 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 4. 설정 검증
```bash
# 설정이 올바른지 확인
docker-compose exec keyword-batch /app/validate_config.sh
```

## 🎯 실행 방법

### 1. 배치 처리 실행

#### 기본 실행 (어제 데이터)
```bash
docker-compose exec keyword-batch /app/run_batch.sh
```

#### 특정 날짜 처리
```bash
docker-compose exec keyword-batch /app/run_batch.sh --target-date 2024-03-15
```

#### 기간별 처리
```bash
docker-compose exec keyword-batch /app/run_batch.sh --start-date 2024-03-01 --end-date 2024-03-31
```

#### 중간부터 재시작 (장애 복구)
```bash
docker-compose exec keyword-batch /app/run_batch.sh --start-date 2024-03-01 --end-date 2024-03-31 --start-index 500
```

### 2. 보고서 생성

#### 날짜 단축어 사용
```bash
# 어제 보고서
docker-compose exec keyword-batch /app/run_report.sh yesterday

# 지난달 보고서
docker-compose exec keyword-batch /app/run_report.sh last-month

# 이번 주 보고서
docker-compose exec keyword-batch /app/run_report.sh this-week

# 오늘 보고서
docker-compose exec keyword-batch /app/run_report.sh today
```

#### 기간별 보고서
```bash
# 특정 기간 보고서
docker-compose exec keyword-batch /app/run_report.sh 2024-03-01 2024-03-31

# 단일 날짜 보고서
docker-compose exec keyword-batch /app/run_report.sh 2024-03-15 2024-03-15
```

#### 이메일 발송 포함
```bash
# 보고서 생성 + 이메일 발송
docker-compose exec keyword-batch /app/run_report.sh last-month --email
docker-compose exec keyword-batch /app/run_report.sh today --email
```

### 3. 수동 실행 스크립트

#### 기본 사용법
```bash
# 어제 데이터 처리
docker-compose exec keyword-batch /app/manual_run.sh

# 특정 날짜 처리
docker-compose exec keyword-batch /app/manual_run.sh 2024-03-15

# 기간별 처리
docker-compose exec keyword-batch /app/manual_run.sh --range 2024-03-01 2024-03-31

# 설정 검증만 실행
docker-compose exec keyword-batch /app/manual_run.sh --validate

# 도움말
docker-compose exec keyword-batch /app/manual_run.sh --help
```

## 📊 모니터링 및 관리

### 1. 상태 확인
```bash
# 컨테이너 상태 확인
docker-compose ps

# 헬스체크 상태 확인
docker inspect keyword-batch-refactored | grep -A 10 Health

# 수동 헬스체크 실행
docker-compose exec keyword-batch /app/healthcheck.sh
```

### 2. 로그 모니터링
```bash
# 실시간 로그 확인
docker-compose logs -f

# 배치 처리 로그만 확인
docker-compose logs -f keyword-batch

# 특정 날짜 cron 로그 확인
docker-compose exec keyword-batch cat /app/logs/cron_20240322_010000.log
```

### 3. 파일 관리
```bash
# 생성된 보고서 확인
docker-compose exec keyword-batch ls -la /app/reports/

# 로그 파일 확인
docker-compose exec keyword-batch ls -la /app/logs/

# 호스트로 파일 복사
docker cp keyword-batch-refactored:/app/reports/report.xlsx ./local-reports/
```

## 🔧 고급 사용법

### 1. 개발 모드 실행
```bash
# 컨테이너 내부 접속
docker-compose exec keyword-batch bash

# Python REPL에서 테스트
docker-compose exec keyword-batch python
>>> from core.config import Config
>>> config = Config()
>>> config.validate_all()
```

### 2. 설정 커스터마이징
```bash
# 환경변수 확인
docker-compose exec keyword-batch env | grep -E "(ENGINE|HCX|SENDER)"

# cron 스케줄 변경 (docker-compose.yml 수정 후)
docker-compose restart
```

### 3. 성능 튜닝
```bash
# 메모리 사용량 확인
docker stats keyword-batch-refactored

# 배치 크기 조정 (환경변수 추가)
# BATCH_SIZE=50
# PARALLEL_WORKERS=5
```

## 🚨 장애 대응

### 1. 일반적인 문제 해결
```bash
# 설정 문제 진단
docker-compose exec keyword-batch /app/validate_config.sh

# 컨테이너 재시작
docker-compose restart

# 이미지 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. 로그 분석
```bash
# 최근 오류 로그 확인
docker-compose logs --tail=100 keyword-batch | grep -i error

# 특정 시간대 로그 확인
docker-compose logs --since="2024-03-22T01:00:00" keyword-batch
```

### 3. 데이터베이스 연결 문제
```bash
# 연결 테스트
docker-compose exec keyword-batch python -c "
from core.config import Config
from core.database import DatabaseManager
config = Config()
db = DatabaseManager(config.database)
import asyncio
print('DB 연결:', asyncio.run(db.check_connection()))
"
```

## 🔄 자동 스케줄링

### 1. Cron 설정 확인
```bash
# 현재 cron 스케줄 확인
docker-compose exec keyword-batch crontab -l

# cron 데몬 상태 확인
docker-compose exec keyword-batch pgrep cron
```

### 2. 스케줄 변경
`docker-compose.yml`에서 `CRON_SCHEDULE` 환경변수 수정:
```yaml
environment:
  - CRON_SCHEDULE=0 2 * * *  # 매일 새벽 2시로 변경
```

### 3. 수동 cron 실행 테스트
```bash
# cron 작업 수동 실행
docker-compose exec keyword-batch /app/run_batch.sh
```

## 📈 백업 및 복구

### 1. 설정 백업
```bash
# 설정 파일 백업
cp .env .env.backup.$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup
```

### 2. 데이터 백업
```bash
# 로그 및 보고서 백업
tar -czf backup_$(date +%Y%m%d).tar.gz logs/ reports/
```

### 3. 복구
```bash
# 설정 복구
cp .env.backup.20240322 .env

# 컨테이너 재시작
docker-compose restart
```

## 📞 지원 및 문의

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **문서**: README.md 참고
- **레거시 호환성**: 기존 스크립트들도 계속 사용 가능

---

**마지막 업데이트**: 2024년 12월 22일  
**버전**: 2.0 (리팩토링된 버전)  
**브랜치**: refactored-v2 