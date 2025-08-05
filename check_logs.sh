#!/bin/bash

# 🔍 배치 로그 확인 유틸리티 스크립트

echo "=== 🔍 배치 로그 확인 유틸리티 ==="
echo "실행 시간: $(date)"
echo ""

# 날짜 파라미터 (기본값: 오늘)
TARGET_DATE=${1:-$(date +%Y%m%d)}
echo "📅 확인 대상 날짜: $TARGET_DATE"
echo ""

# 1. Cron 작업 로그 확인
echo "=== 📋 Cron 작업 로그 (batch_cron_${TARGET_DATE}.log) ==="
if [ -f "/app/logs/batch_cron_${TARGET_DATE}.log" ]; then
    echo "📄 파일 크기: $(du -h /app/logs/batch_cron_${TARGET_DATE}.log | cut -f1)"
    echo "🕒 마지막 수정: $(stat -c %y /app/logs/batch_cron_${TARGET_DATE}.log)"
    echo ""
    echo "📝 최근 20줄:"
    tail -20 "/app/logs/batch_cron_${TARGET_DATE}.log"
    echo ""
    
    # 성공/실패 요약
    echo "📊 작업 결과 요약:"
    grep -c "🎉.*완료" "/app/logs/batch_cron_${TARGET_DATE}.log" 2>/dev/null && echo "  ✅ 완료된 작업" || echo "  ✅ 완료된 작업: 0개"
    grep -c "❌.*실패" "/app/logs/batch_cron_${TARGET_DATE}.log" 2>/dev/null && echo "  ❌ 실패한 작업" || echo "  ❌ 실패한 작업: 0개"
    
else
    echo "⚠️ Cron 작업 로그 파일이 없습니다."
fi
echo ""

# 2. 시스템 Cron 로그 확인
echo "=== 🖥️ 시스템 Cron 로그 ==="
if [ -f "/var/log/cron.log" ]; then
    echo "📝 오늘 cron 실행 기록:"
    grep "$(date +%Y-%m-%d)" /var/log/cron.log | grep "run_batch.sh" | tail -5
else
    echo "⚠️ 시스템 cron 로그가 없습니다."
fi
echo ""

# 3. 일반 배치 로그 확인
echo "=== 📊 일반 배치 로그 (batch_${TARGET_DATE}.log) ==="
if [ -f "/app/logs/batch_${TARGET_DATE}.log" ]; then
    echo "📄 파일 크기: $(du -h /app/logs/batch_${TARGET_DATE}.log | cut -f1)"
    echo "📝 최근 10줄:"
    tail -10 "/app/logs/batch_${TARGET_DATE}.log"
else
    echo "ℹ️ 일반 배치 로그 파일이 없습니다."
fi
echo ""

# 4. 사용 가능한 로그 파일 목록
echo "=== 📁 사용 가능한 로그 파일들 ==="
ls -la /app/logs/*.log 2>/dev/null | head -10
echo ""

# 5. Cron 서비스 상태
echo "=== ⚙️ Cron 서비스 상태 ==="
service cron status 2>/dev/null || echo "Cron 서비스 상태를 확인할 수 없습니다."
echo ""

# 6. 사용법 안내
echo "=== 💡 사용법 ==="
echo "특정 날짜 로그 확인: $0 20240620"
echo "실시간 로그 모니터링: tail -f /app/logs/batch_cron_\$(date +%Y%m%d).log"
echo "모든 로그 동시 확인: tail -f /app/logs/*.log /var/log/cron.log" 