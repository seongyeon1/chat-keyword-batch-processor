#!/bin/bash
set -e

# .env 파일에서 환경변수 로드
if [ -f /app/.env ]; then
    echo "🔧 환경변수 로딩 중..."
    # 주석과 빈 줄을 제외하고 환경변수 export
    while IFS= read -r line; do
        # 주석 및 빈 줄 스킵
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        # = 포함된 라인만 처리
        if [[ "$line" =~ = ]]; then
            export "$line"
        fi
    done < /app/.env
    
    echo "✅ 환경변수 로딩 완료"
    echo "🔍 DB 연결 설정: ${ENGINE_FOR_SQLALCHEMY:0:50}..."
else
    echo "❌ .env 파일을 찾을 수 없습니다."
    exit 1
fi

# Python 경로 설정
export PYTHONPATH=/app

# 스크립트 실행
echo "🚀 배치 스크립트 실행: $@"
python /app/run_advanced_batch.py "$@" 