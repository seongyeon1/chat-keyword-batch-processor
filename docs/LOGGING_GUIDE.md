# 📁 로깅 시스템 가이드

> **통합 로깅 시스템으로 모든 배치 처리 과정을 체계적으로 기록하고 모니터링하세요.**

---

## 📋 목차

1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [설정 방법](#설정-방법)
4. [사용법](#사용법)
5. [로그 파일 관리](#로그-파일-관리)
6. [모니터링](#모니터링)
7. [문제 해결](#문제-해결)
8. [고급 설정](#고급-설정)

---

## 🚀 개요

배치 키워드 시스템은 통합 로깅 시스템을 통해 모든 처리 과정을 체계적으로 기록합니다. 기존의 `print` 문을 완전히 대체하여 파일과 콘솔 모두에 로그를 출력하며, 회전 로그를 통해 디스크 공간을 효율적으로 관리합니다.

### ✨ 주요 특징

- **🖥️ 콘솔 + 📁 파일** 동시 출력
- **🔄 자동 로그 회전** (크기 기반)
- **🎚️ 레벨별 필터링** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **🌏 UTF-8 지원** (한글 완벽 지원)
- **⚙️ 환경변수 제어** (운영 환경별 설정)
- **📊 실시간 모니터링** 지원

---

## 🔧 주요 기능

### 📝 로그 레벨

| 레벨 | 설명 | 용도 |
|------|------|------|
| `DEBUG` | 디버깅 정보 | 개발 및 문제 해결 |
| `INFO` | 일반 정보 | 정상 처리 과정 |
| `WARNING` | 경고 메시지 | 주의가 필요한 상황 |
| `ERROR` | 오류 메시지 | 처리 실패 및 예외 |
| `CRITICAL` | 치명적 오류 | 시스템 중단 상황 |

### 📁 로그 파일 구조

```
batch-keywords/
├── logs/
│   ├── batch_keywords.log      # 현재 로그 파일
│   ├── batch_keywords.log.1    # 백업 파일 1
│   ├── batch_keywords.log.2    # 백업 파일 2
│   ├── batch_keywords.log.3    # 백업 파일 3
│   ├── batch_keywords.log.4    # 백업 파일 4
│   └── batch_keywords.log.5    # 백업 파일 5 (최대)
```

### 🎯 로그 포맷

```
2024-03-15 14:30:25 - batch_keywords.batch_service - INFO - 📅 기간별 배치 처리 시작: 2024-03-01 ~ 2024-03-15
│                   │ │                              │ │    │
│                   │ │                              │ │    └─ 메시지
│                   │ │                              │ └─ 레벨
│                   │ │                              └─ 로거 이름
│                   │ └─ 모듈명
│                   └─ 타임스탬프
```

---

## ⚙️ 설정 방법

### 1. 환경변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# ===========================================
# 📁 로깅 시스템 설정
# ===========================================

# 기본 설정
LOG_LEVEL=INFO                  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_DIR=logs                    # 로그 디렉토리 경로
LOG_FILE=batch_keywords.log     # 로그 파일명

# 파일 관리
MAX_LOG_SIZE_MB=100            # 로그 파일 최대 크기 (MB)
LOG_BACKUP_COUNT=5             # 백업 파일 개수

# 출력 제어
CONSOLE_LOG=true               # 콘솔 출력 활성화 (true/false)
FILE_LOG=true                  # 파일 출력 활성화 (true/false)
```

### 2. 기본값 설정

환경변수를 설정하지 않으면 다음 기본값이 사용됩니다:

```python
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=batch_keywords.log
MAX_LOG_SIZE_MB=100
LOG_BACKUP_COUNT=5
CONSOLE_LOG=true
FILE_LOG=true
```

### 3. 코드에서 로깅 초기화

```python
from utils.logger import setup_logging, log_info, log_error

# 로깅 시스템 초기화 (자동으로 config에서 설정 읽음)
setup_logging()

# 로그 출력
log_info("✅ 시스템 시작")
log_error("❌ 오류 발생")
```

---

## 🎯 사용법

### 1. 기본 사용

```bash
# 기본 설정으로 실행 (INFO 레벨, 콘솔 + 파일 출력)
python cli.py batch -d 2024-03-15

# 로그 파일 확인
cat logs/batch_keywords.log
```

### 2. 로그 레벨 변경

```bash
# 디버그 모드 (더 상세한 로그)
LOG_LEVEL=DEBUG python cli.py batch -d 2024-03-15

# 오류만 로그 (간소한 로그)
LOG_LEVEL=ERROR python cli.py batch -d 2024-03-15

# 경고 이상만 로그
LOG_LEVEL=WARNING python cli.py batch -d 2024-03-15
```

### 3. 출력 제어

```bash
# 파일에만 로그 저장 (콘솔 출력 비활성화)
CONSOLE_LOG=false python cli.py batch -d 2024-03-15

# 콘솔에만 출력 (파일 저장 비활성화)
FILE_LOG=false python cli.py batch -d 2024-03-15

# 로그 완전 비활성화 (권장하지 않음)
CONSOLE_LOG=false FILE_LOG=false python cli.py batch -d 2024-03-15
```

### 4. 커스텀 로그 디렉토리

```bash
# 다른 디렉토리에 로그 저장
LOG_DIR=/var/log/batch-keywords python cli.py batch -d 2024-03-15

# 다른 파일명으로 로그 저장
LOG_FILE=custom_batch.log python cli.py batch -d 2024-03-15
```

---

## 📂 로그 파일 관리

### 1. 자동 회전

로그 파일이 설정된 크기(기본 100MB)를 초과하면 자동으로 백업됩니다:

```
batch_keywords.log      → batch_keywords.log.1
batch_keywords.log.1    → batch_keywords.log.2
batch_keywords.log.2    → batch_keywords.log.3
...
batch_keywords.log.5    → 삭제됨
```

### 2. 수동 관리

```bash
# 현재 로그 파일 크기 확인
ls -lh logs/batch_keywords.log

# 오래된 로그 파일 삭제 (30일 이전)
find logs/ -name "*.log*" -mtime +30 -delete

# 로그 파일 압축
gzip logs/batch_keywords.log.1
gzip logs/batch_keywords.log.2

# 로그 파일 아카이브
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/*.log.*
```

### 3. 디스크 공간 모니터링

```bash
# 로그 디렉토리 전체 크기 확인
du -sh logs/

# 로그 파일별 크기 확인
ls -lh logs/

# 디스크 사용량 확인
df -h .
```

---

## 📊 모니터링

### 1. 실시간 로그 추적

```bash
# 로그 실시간 추적
tail -f logs/batch_keywords.log

# 마지막 100줄 확인
tail -n 100 logs/batch_keywords.log

# 처음 100줄 확인
head -n 100 logs/batch_keywords.log
```

### 2. 로그 필터링

```bash
# 오류만 확인
grep "ERROR" logs/batch_keywords.log

# 경고 이상만 확인
grep -E "(WARNING|ERROR|CRITICAL)" logs/batch_keywords.log

# 특정 날짜 로그 확인
grep "2024-03-15" logs/batch_keywords.log

# 특정 모듈 로그 확인
grep "batch_service" logs/batch_keywords.log
grep "hcx_service" logs/batch_keywords.log

# HCX API 관련 로그
grep "API 호출" logs/batch_keywords.log
```

### 3. 로그 통계

```bash
# 일별 로그 라인 수
grep -o "^[0-9-]*" logs/batch_keywords.log | sort | uniq -c

# 레벨별 로그 수
grep -o " [A-Z]* " logs/batch_keywords.log | sort | uniq -c

# 오류 발생 빈도
grep "ERROR" logs/batch_keywords.log | wc -l

# API 호출 성공/실패 통계
grep "API 호출 성공" logs/batch_keywords.log | wc -l
grep "API 호출 실패" logs/batch_keywords.log | wc -l
```

### 4. 실시간 모니터링 스크립트

```bash
#!/bin/bash
# monitor_logs.sh

echo "📊 배치 키워드 로그 모니터링"
echo "=============================="

while true; do
    clear
    echo "🕒 $(date)"
    echo ""
    
    echo "📈 최근 로그 (마지막 10줄):"
    tail -n 10 logs/batch_keywords.log
    echo ""
    
    echo "⚠️ 최근 오류 (마지막 5개):"
    grep "ERROR" logs/batch_keywords.log | tail -n 5
    echo ""
    
    echo "📊 오늘 통계:"
    TODAY=$(date +%Y-%m-%d)
    echo "  - 총 로그: $(grep "$TODAY" logs/batch_keywords.log | wc -l)개"
    echo "  - 오류: $(grep "$TODAY" logs/batch_keywords.log | grep "ERROR" | wc -l)개"
    echo "  - 경고: $(grep "$TODAY" logs/batch_keywords.log | grep "WARNING" | wc -l)개"
    
    sleep 30
done
```

---

## 🔍 문제 해결

### 1. 일반적인 문제

#### 로그 파일이 생성되지 않음

```bash
# 로그 디렉토리 권한 확인
ls -ld logs/

# 디렉토리 생성 및 권한 설정
mkdir -p logs
chmod 755 logs

# 환경변수 확인
echo $LOG_DIR
echo $LOG_FILE
echo $FILE_LOG
```

#### 콘솔에 로그가 출력되지 않음

```bash
# 콘솔 로그 활성화 확인
export CONSOLE_LOG=true

# 로그 레벨 확인 (DEBUG가 가장 상세함)
export LOG_LEVEL=DEBUG
```

#### 로그 파일이 너무 큼

```bash
# 로그 파일 크기 제한 설정
export MAX_LOG_SIZE_MB=50

# 백업 파일 개수 줄이기
export LOG_BACKUP_COUNT=3

# 로그 레벨 높이기 (INFO → WARNING)
export LOG_LEVEL=WARNING
```

### 2. 성능 관련

#### 로그 출력이 느림

```bash
# 파일 로그만 사용 (콘솔 출력 비활성화)
export CONSOLE_LOG=false

# 로그 레벨 높이기
export LOG_LEVEL=WARNING

# 로그 버퍼링 활성화 (환경에 따라)
export PYTHONUNBUFFERED=0
```

#### 디스크 공간 부족

```bash
# 로그 파일 크기 줄이기
export MAX_LOG_SIZE_MB=20
export LOG_BACKUP_COUNT=2

# 오래된 로그 자동 삭제 스크립트
find logs/ -name "*.log.*" -mtime +7 -delete
```

### 3. 디버깅

#### 상세한 디버그 로그 활성화

```bash
# 모든 디버그 정보 출력
LOG_LEVEL=DEBUG python cli.py batch -d 2024-03-15

# 특정 모듈만 디버그
LOG_LEVEL=DEBUG python cli.py batch -d 2024-03-15 2>&1 | grep "hcx_service"
```

#### 로그 포맷 확인

```python
# 커스텀 로그 포맷 테스트
from utils.logger import setup_logging, log_info

# 간단한 포맷으로 테스트
import os
os.environ['LOG_FORMAT'] = '%(asctime)s - %(levelname)s - %(message)s'

setup_logging()
log_info("테스트 메시지")
```

---

## 🔧 고급 설정

### 1. 커스텀 로그 포맷

```bash
# 환경변수로 포맷 변경 (개발 시)
export LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
export DATE_FORMAT="%Y-%m-%d %H:%M:%S"
```

### 2. 다중 로그 파일

서로 다른 모듈의 로그를 분리하려면:

```python
from utils.logger import get_logger

# 모듈별 로거 생성
batch_logger = get_logger("batch_service")
hcx_logger = get_logger("hcx_service")
email_logger = get_logger("email_service")

# 각각 다른 파일에 로그 출력 (고급 설정 필요)
```

### 3. 원격 로그 전송

```python
# Syslog 서버로 로그 전송 (선택사항)
import logging.handlers

syslog_handler = logging.handlers.SysLogHandler(address=('log-server', 514))
logger.addHandler(syslog_handler)
```

### 4. 로그 분석 도구 연동

```bash
# ELK Stack 연동 예시
# Filebeat 설정으로 Elasticsearch에 로그 전송

# Logstash 패턴
%{TIMESTAMP_ISO8601:timestamp} - %{DATA:logger_name} - %{LOGLEVEL:level} - %{GREEDYDATA:message}
```

### 5. 성능 모니터링

```python
# 로그 성능 측정
import time
from utils.logger import log_info

start_time = time.time()
log_info("성능 테스트 시작")
# ... 작업 수행 ...
duration = time.time() - start_time
log_info(f"작업 완료: {duration:.2f}초 소요")
```

---

## 📚 추가 리소스

### 관련 문서

- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 전체 설정 가이드
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 배포 가이드
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 문제 해결 가이드

### 유용한 명령어 모음

```bash
# 로그 모니터링 원라이너들
alias log-tail="tail -f logs/batch_keywords.log"
alias log-errors="grep ERROR logs/batch_keywords.log"
alias log-today="grep $(date +%Y-%m-%d) logs/batch_keywords.log"
alias log-size="du -sh logs/"

# 로그 분석 함수
function log-stats() {
    echo "📊 로그 통계 (오늘):"
    local today=$(date +%Y-%m-%d)
    echo "  총 로그: $(grep "$today" logs/batch_keywords.log | wc -l)"
    echo "  INFO: $(grep "$today" logs/batch_keywords.log | grep "INFO" | wc -l)"
    echo "  WARNING: $(grep "$today" logs/batch_keywords.log | grep "WARNING" | wc -l)"
    echo "  ERROR: $(grep "$today" logs/batch_keywords.log | grep "ERROR" | wc -l)"
}
```

---

## 🎯 마무리

이 로깅 시스템을 통해 배치 처리 과정을 체계적으로 모니터링하고 문제를 신속하게 해결할 수 있습니다. 

**핵심 포인트:**
- 📁 모든 로그는 `logs/batch_keywords.log`에 저장
- 🎚️ `LOG_LEVEL` 환경변수로 상세도 조절
- 🔄 100MB 초과 시 자동 백업 (최대 5개)
- 📊 `tail -f logs/batch_keywords.log`로 실시간 모니터링
- 🔍 `grep` 명령어로 특정 로그 필터링

문제가 발생하면 먼저 로그를 확인하고, 필요시 `LOG_LEVEL=DEBUG`로 상세 정보를 확인하세요! 🚀 