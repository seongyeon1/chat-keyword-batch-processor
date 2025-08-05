#!/usr/bin/env python3
"""
사용자 쿼리와 시스템 쿼리의 차이를 확인하는 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.batch_service import BatchService


async def check_query_difference():
    """사용자 쿼리와 시스템 쿼리의 차이를 확인합니다."""
    
    config = Config()
    batch_service = BatchService(config)
    
    start_date = '2025-06-11'
    end_date = '2025-06-19'
    
    print("🔍 사용자 쿼리와 시스템 쿼리 비교 분석")
    print("=" * 60)
    
    # 1. 사용자가 제공한 쿼리
    print("1️⃣ 사용자 제공 쿼리로 확인 중...")
    user_query = """
    SELECT 
        DATE(c.created_at) AS missing_date,
        c.input_text,
        COUNT(*) AS missing_count
    FROM chattings c
    LEFT JOIN (
        SELECT query_text, DATE(created_at) AS dt
        FROM temp_classified
    ) t
      ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
    WHERE t.query_text IS NULL  
      AND c.created_at BETWEEN :start_date AND :end_date
    GROUP BY DATE(c.created_at), c.input_text
    ORDER BY missing_date
    """
    
    user_result = await batch_service.db_manager.execute_query(
        user_query,
        {"start_date": start_date, "end_date": end_date}
    )
    
    print(f"   📋 사용자 쿼리 결과: {len(user_result)}개")
    
    # 2. 시스템에서 사용하는 쿼리
    print("\n2️⃣ 시스템 쿼리로 확인 중...")
    system_query = """
    SELECT 
        c.input_text,
        COUNT(*) AS query_count,
        MIN(c.created_at) AS created_at,
        DATE(c.created_at) AS missing_date
    FROM chattings c
    LEFT JOIN (
        SELECT query_text, DATE(created_at) AS dt
        FROM temp_classified
    ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
    WHERE t.query_text IS NULL
      AND c.created_at BETWEEN :start_date AND :end_date
    GROUP BY DATE(c.created_at), c.input_text
    ORDER BY missing_date, query_count DESC
    """
    
    system_result = await batch_service.db_manager.execute_query(
        system_query,
        {"start_date": start_date, "end_date": end_date}
    )
    
    print(f"   📋 시스템 쿼리 결과: {len(system_result)}개")
    
    # 3. 차이 분석
    difference = len(system_result) - len(user_result)
    print(f"\n📊 결과 분석:")
    print(f"   - 사용자 쿼리: {len(user_result)}개")
    print(f"   - 시스템 쿼리: {len(system_result)}개")
    print(f"   - 차이: {difference}개")
    
    if difference == 0:
        print("   ✅ 두 쿼리의 결과가 동일합니다!")
    else:
        print(f"   ⚠️ 시스템 쿼리가 {difference}개 더 많이 나옵니다.")
        
        # 4. 상세 비교
        print(f"\n3️⃣ 상세 차이 분석...")
        
        # 사용자 쿼리 결과를 set으로 변환 (input_text 기준)
        user_texts = {(row[1], str(row[0])) for row in user_result}  # (input_text, missing_date)
        system_texts = {(row[0], str(row[3])) for row in system_result}  # (input_text, missing_date)
        
        only_in_system = system_texts - user_texts
        only_in_user = user_texts - system_texts
        
        if only_in_system:
            print(f"   🔍 시스템에만 있는 데이터 ({len(only_in_system)}개):")
            for i, (text, date) in enumerate(list(only_in_system)[:5]):
                print(f"     {i+1}. [{date}] {text[:50]}...")
            if len(only_in_system) > 5:
                print(f"     ... (나머지 {len(only_in_system) - 5}개)")
        
        if only_in_user:
            print(f"   🔍 사용자 쿼리에만 있는 데이터 ({len(only_in_user)}개):")
            for i, (text, date) in enumerate(list(only_in_user)[:5]):
                print(f"     {i+1}. [{date}] {text[:50]}...")
            if len(only_in_user) > 5:
                print(f"     ... (나머지 {len(only_in_user) - 5}개)")
    
    # 5. temp_classified 데이터 확인
    print(f"\n4️⃣ temp_classified 테이블 상태 확인...")
    temp_query = """
    SELECT 
        DATE(created_at) AS date,
        COUNT(DISTINCT query_text) AS unique_queries,
        SUM(query_count) AS total_count
    FROM temp_classified
    WHERE DATE(created_at) BETWEEN :start_date AND :end_date
    GROUP BY DATE(created_at)
    ORDER BY date
    """
    
    temp_result = await batch_service.db_manager.execute_query(
        temp_query,
        {"start_date": start_date, "end_date": end_date}
    )
    
    print(f"   📅 temp_classified 처리 현황:")
    for row in temp_result:
        print(f"     - {row[0]}: {row[1]}개 고유 질문, {row[2]}건 총계")


if __name__ == "__main__":
    try:
        asyncio.run(check_query_difference())
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}") 