#!/bin/bash

echo "=== 수동 배치 실행 스크립트 (리팩토링 버전) ==="
echo "실행 시간: $(date)"
echo ""

# 도움말 출력
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "사용법:"
    echo "  $0                              # 어제 날짜로 배치 실행"
    echo "  $0 2024-03-15                   # 특정 날짜로 배치 실행"
    echo "  $0 --range 2024-03-01 2024-03-31  # 기간별 배치 실행"
    echo "  $0 --validate                   # 설정 유효성 검사만 실행"
    echo "  $0 --check-missing 2025-06-11 2025-06-19  # 누락 데이터 확인"
    echo "  $0 --process-missing 2025-06-11 2025-06-19 # 누락 데이터 처리"
    echo "  $0 --missing-only 2025-06-11 2025-06-19   # 누락 데이터 통합 처리"
    echo "  $0 --help                       # 도움말 출력"
    echo ""
    echo "이메일 옵션:"
    echo "  --email                         # 처리 완료 후 이메일 발송"
    echo ""
    echo "Docker 컨테이너에서 실행하려면:"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh 2024-03-15"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh --range 2024-03-01 2024-03-31"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh --check-missing 2025-06-11 2025-06-19"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh --process-missing 2025-06-11 2025-06-19"
    echo "  docker-compose exec keyword-batch /app/manual_run.sh --missing-only 2025-06-11 2025-06-19 --email"
    echo ""
    echo "보고서 생성은 다음 명령어 사용:"
    echo "  docker-compose exec keyword-batch /app/run_report.sh yesterday"
    echo "  docker-compose exec keyword-batch /app/run_report.sh last-month --email"
    exit 0
fi

# 환경변수 로드
set -a
source /app/.env
set +a

# Python 경로 설정
export PYTHONPATH=/app

# 이메일 옵션 확인 함수
check_email_option() {
    for arg in "$@"; do
        if [ "$arg" = "--email" ]; then
            return 0  # --email 옵션이 있음
        fi
    done
    return 1  # --email 옵션이 없음
}

# 매개변수에 따른 실행
if [ "$1" = "--validate" ]; then
    echo "🔧 설정 유효성 검사 실행 중..."
    python /app/main_batch.py --validate-config
elif [ "$1" = "--range" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 오류: 기간별 실행에는 시작날짜와 종료날짜가 필요합니다."
        echo "사용법: $0 --range 2024-03-01 2024-03-31 [--email]"
        exit 1
    fi
    echo "📅 기간별 배치 실행 중: $2 ~ $3"
    if check_email_option "$@"; then
        python /app/main_batch.py --start-date "$2" --end-date "$3" --email
    else
        python /app/main_batch.py --start-date "$2" --end-date "$3"
    fi
elif [ "$1" = "--check-missing" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 오류: 누락 데이터 확인에는 시작날짜와 종료날짜가 필요합니다."
        echo "사용법: $0 --check-missing 2025-06-11 2025-06-19"
        exit 1
    fi
    echo "🔍 누락 데이터 확인 중: $2 ~ $3"
    python /app/main_batch.py --check-missing --start-date "$2" --end-date "$3"
elif [ "$1" = "--process-missing" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 오류: 누락 데이터 처리에는 시작날짜와 종료날짜가 필요합니다."
        echo "사용법: $0 --process-missing 2025-06-11 2025-06-19 [--email]"
        exit 1
    fi
    echo "🔧 누락 데이터 처리 중: $2 ~ $3"
    if check_email_option "$@"; then
        python /app/main_batch.py --process-missing --start-date "$2" --end-date "$3" --email
    else
        python /app/main_batch.py --process-missing --start-date "$2" --end-date "$3"
    fi
elif [ "$1" = "--missing-only" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "❌ 오류: 누락 데이터 통합 처리에는 시작날짜와 종료날짜가 필요합니다."
        echo "사용법: $0 --missing-only 2025-06-11 2025-06-19 [--email]"
        exit 1
    fi
    echo "🚀 누락 데이터 통합 처리 중: $2 ~ $3"
    if check_email_option "$@"; then
        echo "📧 처리 완료 후 이메일 발송 예정"
        python /app/main_batch.py --missing-only --start-date "$2" --end-date "$3" --email
    else
        python /app/main_batch.py --missing-only --start-date "$2" --end-date "$3"
    fi
elif [ -z "$1" ]; then
    echo "📋 어제 날짜로 배치 실행 중..."
    if check_email_option "$@"; then
        python /app/main_batch.py --email
    else
        python /app/main_batch.py
    fi
else
    echo "📋 날짜 $1 으로 배치 실행 중..."
    if check_email_option "$@"; then
        python /app/main_batch.py --target-date "$1" --email
    else
        python /app/main_batch.py --target-date "$1"
    fi
fi

echo ""
echo "✅ 배치 실행 완료: $(date)" 