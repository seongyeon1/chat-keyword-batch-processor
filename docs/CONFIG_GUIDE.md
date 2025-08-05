# ⚙️ 설정 가이드 (Configuration Guide)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://docker.com)

> 📋 Chat Keyword Batch Processor의 **완전한 설정 가이드**

---

## 📋 목차

- [🚀 빠른 설정](#-빠른-설정)
- [🔧 환경변수 설정](#-환경변수-설정)
- [🗄️ 데이터베이스 설정](#️-데이터베이스-설정)
- [🤖 HCX API 설정](#-hcx-api-설정)
- [📧 이메일 설정](#-이메일-설정)
- [📊 보고서 설정](#-보고서-설정)
- [🐳 Docker 설정](#-docker-설정)
- [🔍 설정 검증](#-설정-검증)
- [🛠️ 고급 설정](#️-고급-설정)
- [❌ 문제 해결](#-문제-해결)

---

## 🚀 빠른 설정

### 1️⃣ **기본 설정 파일 생성**

```bash
# .env 파일 복사
cp .env.example .env

# 권한 설정 (보안)
chmod 600 .env
```

### 2️⃣ **필수 설정 항목**

다음 항목들은 **반드시** 설정해야 합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| `ENGINE_FOR_SQLALCHEMY` | 데이터베이스 연결 URL | `mysql+pymysql://...` |
| `HCX_CHAT_API_KEY` | HCX API 키 | `hcx_xxxxxxxxxxxx` |
| `SENDER_EMAIL` | 발송자 이메일 | `batch@company.com` |
| `SENDER_PASSWORD` | 이메일 앱 비밀번호 | `app-specific-password` |

### 3️⃣ **설정 검증**

```bash
# 설정 유효성 검사
python main_batch.py --validate-config

# 또는 Docker에서
docker-compose exec keyword-batch python main_batch.py --validate-config
```

---

## 🔧 환경변수 설정

### 📄 **.env 파일 구조**

```bash
# ===========================================
# 🗄️ 데이터베이스 설정
# ===========================================
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://username:password@host:port/database

# ===========================================
# 🤖 HCX API 설정
# ===========================================
HCX_CHAT_API_KEY=your_hcx_api_key_here
HCX_MODEL=HCX-005
HCX_MAX_RETRIES=3
HCX_TIMEOUT=30

# ===========================================
# 📧 이메일 설정
# ===========================================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAILS=admin@company.com,manager@company.com

# ===========================================
# 📊 보고서 설정
# ===========================================
REPORT_OUTPUT_DIR=reports
REPORT_TEMPLATE_PATH=templates

# ===========================================
# ⚡ 배치 처리 설정
# ===========================================
BATCH_SIZE=10
PARALLEL_WORKERS=4
CLASSIFICATION_BATCH_SIZE=5

# ===========================================
# 🔒 보안 설정
# ===========================================
DEBUG=false
LOG_LEVEL=INFO
```

### 🔐 **환경변수 우선순위**

1. **시스템 환경변수** (최우선)
2. **.env 파일**
3. **기본값** (코드 내 설정)

```bash
# 시스템 환경변수로 임시 오버라이드
export HCX_MODEL="HCX-006"
python main_batch.py --validate-config
```

---

## 🗄️ 데이터베이스 설정

### 🔌 **연결 URL 형식**

#### MySQL/MariaDB
```bash
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://username:password@host:port/database?charset=utf8mb4
```

#### PostgreSQL
```bash
ENGINE_FOR_SQLALCHEMY=postgresql://username:password@host:port/database
```

#### SQLite (개발용)
```bash
ENGINE_FOR_SQLALCHEMY=sqlite:///./database.db
```

### ⚙️ **연결 옵션**

<details>
<summary><b>🔽 MySQL 고급 연결 옵션</b></summary>

```bash
# SSL 연결
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:pass@host:port/db?ssl_ca=/path/to/ca.pem&ssl_disabled=false

# 연결 풀 설정
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:pass@host:port/db?pool_size=10&max_overflow=20

# 타임아웃 설정
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:pass@host:port/db?connect_timeout=60&read_timeout=30
```

</details>

### 🧪 **데이터베이스 연결 테스트**

```python
# 연결 테스트 스크립트
from core.config import Config
from core.database import DatabaseManager
import asyncio

async def test_db_connection():
    config = Config()
    db_manager = DatabaseManager(config.database)
    
    try:
        is_connected = await db_manager.check_connection()
        if is_connected:
            print("✅ 데이터베이스 연결 성공")
        else:
            print("❌ 데이터베이스 연결 실패")
    except Exception as e:
        print(f"❌ 연결 오류: {e}")

# 실행
asyncio.run(test_db_connection())
```

---

## 🤖 HCX API 설정

### 🔑 **API 키 획득**

1. **HCX 플랫폼 접속**: https://console.hcx.ai
2. **API 키 생성**: 프로젝트 → API 키 관리
3. **권한 설정**: Chat Completion 권한 필요

### 📝 **HCX 설정 옵션**

| 변수명 | 설명 | 기본값 | 예시 |
|--------|------|--------|------|
| `HCX_CHAT_API_KEY` | API 인증 키 | 필수 | `hcx_xxxxxxxxx` |
| `HCX_MODEL` | 사용할 모델 | `HCX-005` | `HCX-006` |
| `HCX_MAX_RETRIES` | 재시도 횟수 | `3` | `5` |
| `HCX_TIMEOUT` | 요청 타임아웃(초) | `30` | `60` |
| `HCX_BASE_URL` | API 베이스 URL | 기본 HCX URL | 커스텀 URL |

### 🧪 **HCX API 테스트**

```python
# API 테스트 스크립트
from core.config import Config
from services.hcx_service import HCXService

def test_hcx_api():
    config = Config()
    hcx_service = HCXService(config.hcx)
    
    try:
        # 테스트 질문 분류
        result = hcx_service.classify_education_question("수강신청은 언제 하나요?")
        print("✅ HCX API 연결 성공")
        print(f"📊 분류 결과: {result}")
    except Exception as e:
        print(f"❌ HCX API 오류: {e}")

# 실행
test_hcx_api()
```

---

## 📧 이메일 설정

### 📬 **Gmail 설정 (권장)**

#### 1. **앱 비밀번호 생성**
1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 생성 → "배치 처리" 앱 생성
3. 생성된 16자리 비밀번호 사용

#### 2. **환경변수 설정**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=generated-app-password
RECIPIENT_EMAILS=admin@company.com,manager@company.com
```

### 📮 **다른 이메일 서비스**

<details>
<summary><b>🔽 주요 이메일 서비스 설정</b></summary>

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

#### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

#### 사내 Exchange
```bash
SMTP_SERVER=mail.company.com
SMTP_PORT=587
# 또는 포트 25, 465
```

</details>

### 🧪 **이메일 발송 테스트**

```python
# 이메일 테스트 스크립트
from core.config import Config
from services.email_service import EmailService

def test_email():
    config = Config()
    email_service = EmailService(config.email)
    
    try:
        # 테스트 이메일 발송
        success = email_service.send_email(
            subject="🧪 이메일 설정 테스트",
            body="이메일 설정이 정상적으로 작동합니다.",
            to_emails=["test@company.com"]
        )
        
        if success:
            print("✅ 이메일 발송 성공")
        else:
            print("❌ 이메일 발송 실패")
            
    except Exception as e:
        print(f"❌ 이메일 오류: {e}")

# 실행
test_email()
```

---

## 📊 보고서 설정

### 📁 **디렉토리 구조**

```
batch-keywords/
├── reports/                    # 생성된 보고서 저장
│   ├── daily/                 # 일별 보고서
│   ├── monthly/               # 월별 보고서
│   └── custom/                # 커스텀 보고서
├── templates/                 # 보고서 템플릿
│   ├── excel_template.xlsx
│   └── email_template.html
└── logs/                      # 로그 파일
```

### ⚙️ **보고서 설정 옵션**

```bash
# 보고서 출력 디렉토리
REPORT_OUTPUT_DIR=reports

# 템플릿 디렉토리
REPORT_TEMPLATE_PATH=templates

# 자동 정리 설정 (일)
REPORT_RETENTION_DAYS=30

# 파일명 형식
REPORT_FILENAME_FORMAT=keyword_report_{start_date}_{end_date}

# 엑셀 시트명
EXCEL_SHEET_NAMES=Summary,Details,Categories
```

### 📋 **보고서 커스터마이징**

<details>
<summary><b>🔽 엑셀 보고서 커스터마이징</b></summary>

```python
# custom_report_config.py
EXCEL_CONFIG = {
    "sheets": {
        "요약": {
            "columns": ["날짜", "총 키워드", "카테고리 수", "처리율"],
            "chart_type": "line"
        },
        "상세": {
            "columns": ["키워드", "카테고리", "빈도수", "최초등록일"],
            "sort_by": "빈도수"
        },
        "카테고리별": {
            "group_by": "카테고리",
            "chart_type": "pie"
        }
    },
    "formatting": {
        "header_color": "#4472C4",
        "font_name": "맑은 고딕",
        "font_size": 11
    }
}
```

</details>

---

## 🐳 Docker 설정

### 📄 **docker-compose.yml**

```yaml
version: '3.8'

services:
  keyword-batch:
    build: .
    container_name: keyword-batch
    environment:
      # .env 파일에서 자동 로드
      - TZ=Asia/Seoul
    volumes:
      - ./reports:/app/reports          # 보고서 저장
      - ./logs:/app/logs               # 로그 저장
      - ./config:/app/config           # 설정 파일
    networks:
      - batch-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  batch-network:
    driver: bridge
```

### 🔧 **환경별 설정**

<details>
<summary><b>🔽 개발/운영 환경 분리</b></summary>

#### 개발 환경 (docker-compose.dev.yml)
```yaml
version: '3.8'

services:
  keyword-batch:
    extends:
      file: docker-compose.yml
      service: keyword-batch
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - BATCH_SIZE=2
    ports:
      - "8080:8080"  # 디버깅 포트
```

#### 운영 환경 (docker-compose.prod.yml)
```yaml
version: '3.8'

services:
  keyword-batch:
    extends:
      file: docker-compose.yml
      service: keyword-batch
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - BATCH_SIZE=20
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

</details>

---

## 🔍 설정 검증

### ✅ **자동 검증**

```bash
# 모든 설정 검증
python main_batch.py --validate-config

# 특정 설정만 검증
python -c "
from core.config import Config
config = Config()
print('데이터베이스:', config.database.validate())
print('HCX API:', config.hcx.validate())
print('이메일:', config.email.validate())
"
```

### 🔧 **수동 검증 체크리스트**

#### 📋 **필수 검증 항목**

- [ ] **데이터베이스 연결**: 테이블 접근 권한 확인
- [ ] **HCX API**: 키 유효성 및 모델 접근 권한
- [ ] **이메일 SMTP**: 발송 테스트 성공
- [ ] **디렉토리 권한**: 보고서/로그 디렉토리 쓰기 권한
- [ ] **Docker 네트워크**: 컨테이너 간 통신 확인

#### 🛠️ **선택 검증 항목**

- [ ] **SSL/TLS 인증서**: HTTPS 연결 확인
- [ ] **방화벽 설정**: 필요한 포트 오픈 확인
- [ ] **로그 로테이션**: 디스크 용량 관리
- [ ] **백업 설정**: 데이터베이스 백업 스케줄

### 📊 **설정 검증 리포트**

```python
# validate_all.py
import asyncio
from core.config import Config
from core.database import DatabaseManager
from services.hcx_service import HCXService
from services.email_service import EmailService

async def validate_all_settings():
    """모든 설정을 검증하고 리포트 생성"""
    config = Config()
    results = {}
    
    # 데이터베이스 검증
    try:
        db_manager = DatabaseManager(config.database)
        db_connected = await db_manager.check_connection()
        results['database'] = '✅ 연결 성공' if db_connected else '❌ 연결 실패'
    except Exception as e:
        results['database'] = f'❌ 오류: {e}'
    
    # HCX API 검증
    try:
        hcx_service = HCXService(config.hcx)
        test_result = hcx_service.classify_education_question("테스트")
        results['hcx_api'] = '✅ API 정상' if test_result else '❌ API 응답 없음'
    except Exception as e:
        results['hcx_api'] = f'❌ 오류: {e}'
    
    # 이메일 검증
    try:
        email_service = EmailService(config.email)
        email_valid = email_service.validate_smtp_connection()
        results['email'] = '✅ SMTP 연결 성공' if email_valid else '❌ SMTP 연결 실패'
    except Exception as e:
        results['email'] = f'❌ 오류: {e}'
    
    # 리포트 출력
    print("\n" + "="*50)
    print("🔍 설정 검증 리포트")
    print("="*50)
    for service, status in results.items():
        print(f"{service:15}: {status}")
    print("="*50)
    
    return results

# 실행
if __name__ == "__main__":
    asyncio.run(validate_all_settings())
```

---

## 🛠️ 고급 설정

### ⚡ **성능 튜닝**

```bash
# 대용량 처리 최적화
BATCH_SIZE=50                    # 배치 크기 증가
PARALLEL_WORKERS=8               # 워커 수 증가
CLASSIFICATION_BATCH_SIZE=20     # 분류 배치 크기 증가

# 메모리 관리
MAX_MEMORY_USAGE=4096           # 최대 메모리 사용량 (MB)
MEMORY_CHECK_INTERVAL=100       # 메모리 체크 주기

# 데이터베이스 최적화
DB_POOL_SIZE=20                 # 연결 풀 크기
DB_MAX_OVERFLOW=30              # 최대 오버플로우
DB_POOL_TIMEOUT=30              # 연결 타임아웃
```

### 🔒 **보안 강화**

```bash
# API 키 로테이션
HCX_API_KEY_ROTATION_DAYS=90

# 로그 보안
LOG_MASK_SENSITIVE_DATA=true
LOG_RETENTION_DAYS=30

# 네트워크 보안
ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8
USE_SSL_ONLY=true
```

### 📊 **모니터링**

```bash
# 성능 모니터링
ENABLE_PERFORMANCE_MONITORING=true
METRICS_COLLECTION_INTERVAL=60

# 알림 설정
ALERT_ON_FAILURE=true
ALERT_ON_SLOW_PROCESSING=true
SLOW_PROCESSING_THRESHOLD=300   # 5분

# 헬스체크
HEALTHCHECK_ENDPOINT=/health
HEALTHCHECK_INTERVAL=30
```

---

## ❌ 문제 해결

### 🔧 **일반적인 문제들**

#### 1. **데이터베이스 연결 실패**

```bash
# 오류: "Access denied for user"
# 해결방법:
1. 사용자 권한 확인
2. 비밀번호 특수문자 URL 인코딩
3. 방화벽 포트 확인

# URL 인코딩 예시
password="p@ssw0rd!"  # 원본
encoded="p%40ssw0rd%21"  # 인코딩됨
```

#### 2. **HCX API 오류**

```bash
# 오류: "Invalid API Key"
# 해결방법:
1. API 키 재확인
2. 권한 설정 점검
3. 사용량 한도 확인

# 오류: "Model not found"
# 해결방법:
HCX_MODEL=HCX-005  # 지원되는 모델로 변경
```

#### 3. **이메일 발송 실패**

```bash
# 오류: "Authentication failed"
# 해결방법:
1. 앱 비밀번호 사용 (Gmail)
2. 2단계 인증 활성화
3. SMTP 포트 확인 (587, 465)

# 오류: "Connection timeout"
# 해결방법:
SMTP_TIMEOUT=60  # 타임아웃 증가
```

### 🔍 **디버깅 도구**

```bash
# 상세 로그 활성화
export LOG_LEVEL=DEBUG
python main_batch.py --validate-config

# 네트워크 연결 테스트
telnet smtp.gmail.com 587
telnet your-database-host 3306

# 환경변수 확인
env | grep -E "(ENGINE|HCX|SMTP)"
```

### 📞 **추가 지원**

문제가 해결되지 않으면:

1. **로그 파일 확인**: `logs/batch_*.log`
2. **설정 파일 재검토**: `.env` 파일 문법 확인
3. **문의하기**: [ksy9744@clabi.co.kr](mailto:ksy9744@clabi.co.kr)

---

<div align="center">

**📅 마지막 업데이트**: 2025년 6월 19일  
**🔧 설정 버전**: v1.0  
**💡 도움이 필요하시면**: [ksy9744@clabi.co.kr](mailto:ksy9744@clabi.co.kr)

---

*설정이 복잡하더라도 단계별로 차근차근 진행하시면 됩니다! 🚀*

</div> 