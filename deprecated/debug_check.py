#!/usr/bin/env python3
"""
데이터베이스 적재 상황 디버그 스크립트
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.database_manager import DatabaseManager

async def debug_data_status():
    """데이터 적재 상황 상세 확인"""
    config = Config()
    db = DatabaseManager(config)
    
    start_date = "2025-06-11"
    end_date = "2025-06-19"
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("🔍 데이터베이스 적재 상황 디버그")
    print("=" * 60)
    print(f"📅 확인 기간: {start_date} ~ {end_date}")
    print(f"📅 오늘 날짜: {today}")
    print()
    
    # 1. 전체 채팅 데이터 확인
    chattings_query = f"""
        SELECT 
            DATE(created_at) as date,
            COUNT(DISTINCT input_text) as unique_questions,
            COUNT(*) as total_messages
        FROM chattings
        WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    
    chattings_result = await db.execute_query(chattings_query)
    print("1️⃣ 채팅 데이터 (chattings 테이블):")
    chattings_total = 0
    for row in chattings_result:
        print(f"   {row[0]}: {row[1]}개 고유 질문, {row[2]}개 총 메시지")
        chattings_total += row[1]
    print(f"   📊 전체 고유 질문: {chattings_total}개")
    
    print()
    
    # 2. 처리된 키워드 데이터 확인
    keywords_query = f"""
        SELECT 
            DATE(created_at) as date,
            COUNT(DISTINCT query_text) as unique_queries,
            COUNT(*) as total_records
        FROM admin_chat_keywords
        WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    
    keywords_result = await db.execute_query(keywords_query)
    print("2️⃣ 처리된 키워드 데이터 (admin_chat_keywords 테이블):")
    keywords_total = 0
    for row in keywords_result:
        print(f"   {row[0]}: {row[1]}개 고유 질문, {row[2]}개 총 레코드")
        keywords_total += row[1]
    print(f"   📊 전체 처리된 고유 질문: {keywords_total}개")
    
    print()
    
    # 3. 오늘 배치로 처리된 데이터 확인
    today_batch_query = f"""
        SELECT 
            DATE(created_at) as original_date,
            COUNT(DISTINCT query_text) as unique_queries,
            COUNT(*) as total_records
        FROM admin_chat_keywords
        WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
          AND DATE(batch_created_at) = '{today}'
        GROUP BY DATE(created_at)
        ORDER BY original_date
    """
    
    today_result = await db.execute_query(today_batch_query)
    print("3️⃣ 오늘 배치로 처리된 데이터:")
    today_total = 0
    if today_result:
        for row in today_result:
            print(f"   {row[0]}: {row[1]}개 고유 질문, {row[2]}개 총 레코드")
            today_total += row[1]
        print(f"   📊 오늘 처리된 고유 질문: {today_total}개")
    else:
        print("   ❌ 오늘 처리된 데이터가 없습니다.")
    
    print()
    
    # 4. 실제 누락 데이터 확인 (상세 쿼리)
    missing_query = f"""
        SELECT 
            DATE(c.created_at) as missing_date,
            COUNT(DISTINCT c.input_text) as missing_count
        FROM chattings c
        LEFT JOIN (
            SELECT DISTINCT query_text, DATE(created_at) as dt
            FROM admin_chat_keywords
            WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        ) k ON c.input_text = k.query_text AND DATE(c.created_at) = k.dt
        WHERE k.query_text IS NULL
          AND c.created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        GROUP BY DATE(c.created_at)
        ORDER BY missing_date
    """
    
    missing_result = await db.execute_query(missing_query)
    print("4️⃣ 실제 누락 데이터:")
    missing_total = 0
    if missing_result:
        for row in missing_result:
            print(f"   {row[0]}: {row[1]}개 누락")
            missing_total += row[1]
        print(f"   📊 총 누락: {missing_total}개")
    else:
        print("   ✅ 누락된 데이터가 없습니다.")
    
    print()
    
    # 5. 요약
    print("📊 요약:")
    print(f"   - 전체 고유 질문: {chattings_total}개")
    print(f"   - 처리된 고유 질문: {keywords_total}개")
    print(f"   - 오늘 처리된 질문: {today_total}개")
    print(f"   - 누락된 질문: {missing_total}개")
    print(f"   - 처리율: {(keywords_total/chattings_total*100):.1f}%")
    
    # 6. 사용자가 말하는 '적재되지 않음' 확인
    if missing_total == 0 and today_total > 0:
        print("\n✅ 결론: 데이터가 정상적으로 적재되었습니다!")
        print(f"   오늘 {today_total}개의 질문이 추가로 처리되었습니다.")
    elif missing_total == 0 and today_total == 0:
        print("\n❓ 상황: 누락 데이터는 없지만 오늘 처리된 데이터도 없습니다.")
        print("   이미 모든 데이터가 처리되어 있거나, 다른 날짜에 처리되었을 수 있습니다.")
    else:
        print(f"\n❌ 문제: {missing_total}개의 질문이 여전히 누락되어 있습니다.")

if __name__ == "__main__":
    asyncio.run(debug_data_status()) 