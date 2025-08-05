#!/bin/bash

# 🔧 환경변수 안전하게 로드
set -a
if [ -f /app/.env ]; then
    # .env 파일에서 주석과 빈 줄 제거하고 안전하게 로드
    source <(grep -v '^#' /app/.env | grep -v '^$' | sed 's/^/export /')
fi
if [ -f ./.env ]; then
    source <(grep -v '^#' ./.env | grep -v '^$' | sed 's/^/export /')
fi
set +a

# 🐍 Python 경로 설정 (Docker 환경)
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="/app:${PYTHONPATH}"

# 📁 작업 디렉토리 설정
if [ ! -f "./cli.py" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
fi

# 🔍 Python 명령어 확인
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Python을 찾을 수 없습니다. PATH: $PATH"
    exit 1
fi

echo "🐍 사용할 Python: $PYTHON_CMD ($(which $PYTHON_CMD))"
echo "📁 작업 디렉토리: $(pwd)"
echo "🕒 실행 시간: $(date)"

# CLI 기반 배치 처리
case "$1" in
  "batch")
    echo "🚀 배치 처리 실행: $2 ~ $3"
    $PYTHON_CMD cli.py batch -s "$2" -e "$3" --email
    ;;
  "missing")
    echo "🔍 누락 데이터 처리: $2 ~ $3"
    $PYTHON_CMD cli.py missing auto -s "$2" -e "$3" --email
    ;;
  "report")
    echo "📊 보고서 생성: $2 ~ $3"
    $PYTHON_CMD cli.py report -s "$2" -e "$3" --email
    ;;
  "daily")
    echo "📅 일일 작업: 배치 + 보고서"
    $PYTHON_CMD cli.py batch --email
    $PYTHON_CMD cli.py report -d yesterday --email
    ;;
  "complete")
    echo "🎯 완전한 일일 작업: $2 날짜"
    if [ -n "$2" ]; then
      $PYTHON_CMD cli.py batch -d "$2" --email
      $PYTHON_CMD cli.py report -d "$2" --email
    else
      $PYTHON_CMD cli.py batch --email
      $PYTHON_CMD cli.py report -d yesterday --email
    fi
    ;;
  "status")
    echo "📊 시스템 상태 확인"
    $PYTHON_CMD cli.py status
    ;;
  *)
    echo "사용법: $0 {batch|missing|report|daily|complete|status} [start_date] [end_date]"
    echo "예시:"
    echo "  $0 batch 2024-03-01 2024-03-31"
    echo "  $0 missing 2024-03-01 2024-03-31"
    echo "  $0 report 2024-03-01 2024-03-31"
    echo "  $0 daily"
    echo "  $0 complete 2024-03-15"
    echo "  $0 status"
    exit 1
    ;;
esac 