# 채팅 키워드 배치 처리 시스템용 Dockerfile v2.0
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV TZ=Asia/Seoul
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (최소한으로)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    cron \
    locales \
    tzdata \
    && echo "ko_KR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN pip install --upgrade pip

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# Python 경로 및 환경 변수 설정
ENV PYTHONPATH=/app
ENV DOCKER=true

# 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs /app/reports /app/temp && \
    chmod 755 /app/logs /app/reports /app/temp

# 📝 run_batch.sh 권한 설정 (호스트에서 복사된 파일 사용)
RUN chmod +x /app/run_batch.sh

# 설정 검증 스크립트 (CLI 기반)
RUN echo '#!/bin/bash\n\
set -a\n\
[ -f /app/.env ] && source /app/.env\n\
set +a\n\
export PYTHONPATH=/app\n\
echo "=== 🔧 CLI 기반 배치 시스템 검증 ==="\n\
echo "Python 버전: $(python --version)"\n\
echo "작업 디렉토리: $(pwd)"\n\
echo "Python 경로: $PYTHONPATH"\n\
echo "환경 파일: $([ -f /app/.env ] && echo \"✅ 존재\" || echo \"⚠️ 없음\")"\n\
echo ""\n\
echo "=== 📦 핵심 패키지 확인 ==="\n\
python -c "import requests; print(\"✅ requests\")" 2>/dev/null || echo "❌ requests"\n\
python -c "import pymysql; print(\"✅ pymysql\")" 2>/dev/null || echo "❌ pymysql"\n\
python -c "import sqlalchemy; print(\"✅ sqlalchemy\")" 2>/dev/null || echo "❌ sqlalchemy"\n\
python -c "import httpx; print(\"✅ httpx\")" 2>/dev/null || echo "❌ httpx"\n\
python -c "import pandas; print(\"✅ pandas\")" 2>/dev/null || echo "❌ pandas"\n\
python -c "import openpyxl; print(\"✅ openpyxl\")" 2>/dev/null || echo "❌ openpyxl"\n\
echo ""\n\
echo "=== 🚀 CLI 시스템 모듈 확인 ==="\n\
python -c "from core.config import Config; print(\"✅ Config\")" 2>/dev/null || echo "❌ Config 로드 실패"\n\
python -c "from services.batch_service import BatchService; print(\"✅ BatchService\")" 2>/dev/null || echo "❌ BatchService 로드 실패"\n\
python -c "from services.email_service import EmailService; print(\"✅ EmailService\")" 2>/dev/null || echo "❌ EmailService 로드 실패"\n\
python -c "from services.excel_service import ExcelService; print(\"✅ ExcelService\")" 2>/dev/null || echo "❌ ExcelService 로드 실패"\n\
echo ""\n\
echo "=== 🎯 CLI 명령어 테스트 ==="\n\
python cli.py config validate > /dev/null 2>&1 && echo "✅ CLI config 명령어" || echo "❌ CLI config 명령어 실패"\n\
echo ""\n\
echo "✅ 시스템 검증 완료!"' > /app/validate.sh && \
    chmod +x /app/validate.sh

# 크론 설정 스크립트 (CLI 기반)
RUN echo '#!/bin/bash\n\
echo "🕐 크론 설정: ${CRON_SCHEDULE:-0 1 * * *}"\n\
\n\
# Python 경로 설정\n\
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"\n\
export PYTHONPATH="/app"\n\
\n\
# CLI 기반 일일 배치 작업 (complete 명령어 사용)\n\
CRON_CMD="/app/run_batch.sh complete"\n\
\n\
if [ "${CRON_EMAIL:-true}" = "true" ]; then\n\
    echo "📧 이메일 발송 활성화"\n\
else\n\
    echo "📧 이메일 발송 비활성화"\n\
fi\n\
\n\
# PATH 환경변수를 포함한 cron 설정\n\
echo "PATH=/usr/local/bin:/usr/bin:/bin" > /etc/cron.d/batch\n\
echo "PYTHONPATH=/app" >> /etc/cron.d/batch\n\
echo "${CRON_SCHEDULE:-0 1 * * *} root cd /app && $CRON_CMD >> /app/logs/batch_cron_\\$(date +\\%Y\\%m\\%d).log 2>&1" >> /etc/cron.d/batch\n\
chmod 0644 /etc/cron.d/batch\n\
crontab /etc/cron.d/batch\n\
\n\
echo "✅ 크론 설정 완료"\n\
echo "📅 예약된 작업:"\n\
crontab -l' > /app/setup_cron.sh && \
    chmod +x /app/setup_cron.sh

# 헬스체크 스크립트 (CLI 기반)
RUN echo '#!/bin/bash\n\
export PYTHONPATH=/app\n\
set -a\n\
[ -f /app/.env ] && source /app/.env\n\
set +a\n\
\n\
if [ ! -f "/app/.env" ]; then\n\
    echo "⚠️ .env 파일 없음"\n\
    exit 1\n\
fi\n\
\n\
# CLI 상태 확인\n\
if ! python cli.py status > /dev/null 2>&1; then\n\
    echo "❌ CLI 상태 확인 실패"\n\
    exit 1\n\
fi\n\
\n\
echo "✅ 헬스체크 통과"\n\
exit 0' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# 시작 스크립트 (CLI 기반)
RUN echo '#!/bin/bash\n\
echo "=== 🚀 CLI 기반 배치 처리 시스템 v2.0 ==="\n\
echo "시작 시간: $(date)"\n\
echo "시간대: $TZ"\n\
echo "Python 경로: $PYTHONPATH"\n\
\n\
# 환경변수 설정\n\
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"\n\
export PYTHONPATH="/app"\n\
\n\
# Python 버전 확인\n\
if command -v python3 >/dev/null 2>&1; then\n\
    PYTHON_CMD="python3"\n\
    echo "🐍 Python 명령어: $PYTHON_CMD ($(python3 --version))"\n\
elif command -v python >/dev/null 2>&1; then\n\
    PYTHON_CMD="python"\n\
    echo "🐍 Python 명령어: $PYTHON_CMD ($(python --version))"\n\
else\n\
    echo "❌ Python을 찾을 수 없습니다!"\n\
    exit 1\n\
fi\n\
\n\
echo "🔧 시스템 검증..."\n\
/app/validate.sh\n\
echo ""\n\
echo "📅 크론 설정..."\n\
/app/setup_cron.sh\n\
echo ""\n\
echo "🚀 크론 데몬 시작..."\n\
service cron start\n\
echo ""\n\
echo "🎯 사용 가능한 CLI 명령어:"\n\
echo "  배치 처리:      $PYTHON_CMD cli.py batch [옵션]"\n\
echo "  누락 데이터:    $PYTHON_CMD cli.py missing [옵션]"\n\
echo "  보고서 생성:    $PYTHON_CMD cli.py report [옵션]"\n\
echo "  시스템 상태:    $PYTHON_CMD cli.py status"\n\
echo "  설정 검증:      $PYTHON_CMD cli.py config validate"\n\
echo ""\n\
echo "🛠️ 배치 스크립트 명령어:"\n\
echo "  일일 작업:      /app/run_batch.sh daily"\n\
echo "  완전한 작업:    /app/run_batch.sh complete [날짜]"\n\
echo "  배치 처리:      /app/run_batch.sh batch YYYY-MM-DD YYYY-MM-DD"\n\
echo "  누락 처리:      /app/run_batch.sh missing YYYY-MM-DD YYYY-MM-DD"\n\
echo "  보고서:         /app/run_batch.sh report YYYY-MM-DD YYYY-MM-DD"\n\
echo "  상태 확인:      /app/run_batch.sh status"\n\
echo ""\n\
echo "📊 로그 모니터링 시작..."\n\
mkdir -p /app/logs\n\
touch /var/log/cron.log\n\
\n\
# 초기 상태 확인\n\
echo "🔍 시스템 상태 확인..."\n\
$PYTHON_CMD cli.py status\n\
echo ""\n\
\n\
# 로그 모니터링 시작\n\
echo "📋 로그 파일 모니터링 중..."\n\
tail -f /var/log/cron.log /app/logs/*.log 2>/dev/null &\n\
\n\
# 무한 대기 (컨테이너 유지)\n\
while true; do\n\
    sleep 3600  # 1시간마다 체크\n\
    if ! service cron status > /dev/null 2>&1; then\n\
        echo "⚠️ cron 서비스 재시작"\n\
        service cron start\n\
    fi\n\
done' > /app/start.sh && \
    chmod +x /app/start.sh

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# 볼륨 설정
VOLUME ["/app/logs", "/app/reports", "/app/temp"]

# 메타데이터
LABEL version="2.0-cli" \
      description="CLI-based Chat Keyword Batch Processing System" \
      maintainer="Chat Keyword Team"

# 기본 명령어
CMD ["/app/start.sh"] 