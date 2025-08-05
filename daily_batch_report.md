# 🤖 채팅 키워드 배치 처리 시스템 - 일일 작업 보고서

## 📅 작업 일자
- **작업 대상 날짜**: 전날 (yesterday)
- **실행 시간**: 매일 새벽 1시 (00:00 KST)
- **작업 유형**: 완전한 일일 작업 (배치 처리 + 보고서 생성)

## 🕐 Crontab 설정

### 현재 설정된 Cron 명령어
```bash
# Docker Compose 환경에서 설정
CRON_SCHEDULE=0 1 * * *  # 매일 새벽 1시

# 실제 실행 명령어
/app/run_batch.sh complete >> /app/logs/batch_cron_$(date +%Y%m%d).log 2>&1
```

### 실행되는 배치 작업
1. **배치 처리**: `python cli.py batch --email`
   - 전날 채팅 데이터의 키워드 분류 처리
   - HCX API를 통한 AI 기반 분류
   - 처리 완료 후 이메일 알림 발송

2. **보고서 생성**: `python cli.py report -d yesterday --email`
   - 전날 처리된 데이터의 Excel 보고서 생성
   - 분석 결과 요약 및 통계
   - 보고서 완료 후 이메일 발송

## 🔄 배치 작업 흐름

### 1단계: 배치 처리 (`python cli.py batch --email`)
- **데이터 수집**: 전날 채팅 데이터 추출
- **키워드 분류**: HCX API를 통한 AI 기반 분류
- **데이터 저장**: 분류 결과 데이터베이스 저장
- **이메일 알림**: 배치 처리 완료 알림

### 2단계: 보고서 생성 (`python cli.py report -d yesterday --email`)
- **데이터 분석**: 처리된 데이터 통계 분석
- **Excel 생성**: 상세 분석 보고서 작성
- **파일 저장**: `/app/reports/` 디렉토리에 저장
- **이메일 발송**: 보고서 첨부하여 발송

## 📊 모니터링 및 로그

### 로그 파일 위치
- **Cron 로그**: `/var/log/cron.log`
- **배치 로그**: `/app/logs/batch_cron_YYYYMMDD.log`
- **일반 배치 로그**: `/app/logs/batch_YYYYMMDD.log`
- **보고서**: `/app/reports/`

### 상태 확인 명령어
```bash
# Docker 환경에서 로그 확인
docker-compose exec batch-keywords tail -f /var/log/cron.log
docker-compose exec batch-keywords tail -f /app/logs/batch_$(date +%Y%m%d).log

# 시스템 상태 확인
docker-compose exec batch-keywords python cli.py status

# Crontab 설정 확인
docker-compose exec batch-keywords crontab -l
```

## 🎯 주요 기능

### AI 기반 키워드 분류
- **HCX API 활용**: 지능형 키워드 분류
- **모델**: HCX-005
- **처리 방식**: 비동기 병렬 처리

### 자동화된 보고서 생성
- **Excel 형식**: 상세 분석 데이터
- **통계 요약**: 키워드별 분류 결과
- **시각화**: 차트 및 그래프 포함

### 이메일 알림 시스템
- **처리 완료 알림**: 배치 작업 완료 시
- **보고서 첨부**: Excel 파일 자동 첨부
- **오류 알림**: 실패 시 오류 내용 포함

## 🔧 설정 관리

### 환경변수 (.env)
```env
# 데이터베이스 연결
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:pass@host:port/db

# HCX API 설정
HCX_CHAT_API_KEY=your-api-key
HCX_MODEL=HCX-005

# 이메일 설정
SMTP_SERVER=smtp.gmail.com
SENDER_EMAIL=your-email@domain.com
RECIPIENT_EMAILS=user1@domain.com,user2@domain.com

# Cron 설정
CRON_SCHEDULE=0 1 * * *
CRON_EMAIL=true
```

### Docker Compose 설정
```yaml
environment:
  - CRON_SCHEDULE=0 1 * * *  # 매일 새벽 1시
  - CRON_EMAIL=true          # 이메일 발송 활성화
  - TZ=Asia/Seoul            # 한국 시간대
```

## 🚨 문제 해결

### 일반적인 문제점과 해결방법

1. **Cron 작업이 실행되지 않는 경우**
   ```bash
   # Cron 서비스 재시작
   docker-compose exec batch-keywords service cron restart
   
   # Cron 설정 재적용
   docker-compose exec batch-keywords /app/setup_cron.sh
   ```

2. **데이터베이스 연결 실패**
   ```bash
   # 연결 테스트
   docker-compose exec batch-keywords python cli.py config validate
   ```

3. **HCX API 오류**
   ```bash
   # API 키 확인
   docker-compose exec batch-keywords env | grep HCX
   ```

### 수동 실행 명령어
```bash
# 전날 데이터 완전 처리 (배치 + 보고서)
docker-compose exec batch-keywords /app/run_batch.sh complete

# 특정 날짜 처리
docker-compose exec batch-keywords /app/run_batch.sh complete 2024-03-15

# 배치만 실행
docker-compose exec batch-keywords python cli.py batch --email

# 보고서만 생성
docker-compose exec batch-keywords python cli.py report -d yesterday --email
```

## 📈 성능 및 리소스

### 시스템 리소스
- **메모리 제한**: 2GB
- **메모리 예약**: 512MB
- **로그 로테이션**: 최대 10MB, 3개 파일

### 처리 성능
- **비동기 처리**: asyncio 기반 고성능
- **병렬 처리**: 날짜별/청크별 병렬 처리
- **자동 재시도**: 오류 시 자동 복구

## 💡 권장사항

### 일일 운영
1. **로그 모니터링**: 매일 새벽 작업 후 로그 확인
2. **보고서 검토**: 생성된 Excel 보고서 내용 확인
3. **시스템 상태**: 주기적인 상태 점검

### 주간 유지보수
1. **누락 데이터 확인**: 일주일 단위 누락 데이터 점검
2. **로그 정리**: 오래된 로그 파일 정리
3. **성능 모니터링**: 리소스 사용량 확인

### 월간 점검
1. **전체 데이터 검증**: 월별 데이터 완성도 확인
2. **보고서 아카이브**: 월별 보고서 백업
3. **시스템 업데이트**: 필요 시 시스템 업데이트

---

## 📞 문의 및 지원

문제 발생 시 다음 정보를 수집하여 문의:

```bash
# 시스템 정보 수집
echo "=== 시스템 상태 ===" > debug_info.txt
docker-compose exec batch-keywords python cli.py status >> debug_info.txt
echo "" >> debug_info.txt
echo "=== 최근 로그 ===" >> debug_info.txt
docker-compose exec batch-keywords tail -50 /app/logs/batch_$(date +%Y%m%d).log >> debug_info.txt
```

**작성일**: $(date '+%Y-%m-%d %H:%M:%S KST')  
**시스템**: 채팅 키워드 배치 처리 시스템 v2.0  
**환경**: Docker Compose + Cron 자동화 