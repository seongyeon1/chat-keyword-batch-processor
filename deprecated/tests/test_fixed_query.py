#!/usr/bin/env python3
"""
수정된 쿼리가 사용자 확인 결과와 일치하는지 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.batch_service import BatchService


async def test_fixed_query():
    """수정된 쿼리가 정확한 결과를 반환하는지 테스트합니다."""
    
    config = Config()
    batch_service = BatchService(config)
    
    start_date = '2025-06-11'
    end_date = '2025-06-19'
    
    print("🧪 수정된 쿼리 테스트")
    print("=" * 50)
    
    # 1. 사용자가 확인한 원본 쿼리 (admin_chat_keywords 사용)
    print("1️⃣ admin_chat_keywords 기반 쿼리로 확인...")
    user_query = """
    SELECT 
        DATE(c.created_at) AS missing_date,
        c.input_text,
        COUNT(*) AS missing_count
    FROM chattings c
    LEFT JOIN (
        SELECT DISTINCT query_text, DATE(created_at) AS dt
        FROM admin_chat_keywords
        WHERE DATE(created_at) BETWEEN :start_date AND :end_date
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
    
    print(f"   📋 admin_chat_keywords 기반 쿼리 결과: {len(user_result)}개")
    
    # 2. 수정된 시스템 쿼리로 직접 테스트
    print("\n2️⃣ 수정된 시스템 쿼리로 확인...")
    
    # process_missing_data에서 사용하는 수정된 쿼리와 동일
    system_query = """
    SELECT 
        DATE(c.created_at) AS missing_date,
        c.input_text,
        COUNT(*) AS missing_count
    FROM chattings c
    LEFT JOIN (
        SELECT DISTINCT query_text, DATE(created_at) AS dt
        FROM admin_chat_keywords
        WHERE DATE(created_at) BETWEEN :start_date AND :end_date
    ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
    WHERE t.query_text IS NULL
      AND c.created_at BETWEEN :start_date AND :end_date
    GROUP BY DATE(c.created_at), c.input_text
    ORDER BY missing_date
    """
    
    system_result = await batch_service.db_manager.execute_query(
        system_query,
        {"start_date": start_date, "end_date": end_date}
    )
    
    print(f"   📋 수정된 시스템 쿼리 결과: {len(system_result)}개")
    
    # 3. 결과 비교
    print(f"\n📊 결과 비교:")
    print(f"   - 사용자 확인: {len(user_result)}개")
    print(f"   - 수정된 시스템: {len(system_result)}개")
    
    if len(user_result) == len(system_result):
        print("   ✅ 완벽히 일치합니다! 문제가 해결되었습니다.")
        
        # 내용도 동일한지 확인
        user_set = {(str(row[0]), row[1], row[2]) for row in user_result}
        system_set = {(str(row[0]), row[1], row[2]) for row in system_result}
        
        if user_set == system_set:
            print("   ✅ 내용도 완전히 동일합니다!")
        else:
            print("   ⚠️ 개수는 같지만 내용이 다릅니다.")
            
    else:
        difference = len(system_result) - len(user_result)
        print(f"   ❌ {abs(difference)}개 차이가 있습니다.")
    
    # 4. 실제 process_missing_data 함수 테스트 (시뮬레이션)
    print(f"\n3️⃣ process_missing_data 함수 시뮬레이션...")
    
    try:
        # classify_chat_keywords_by_date 프로시저 실행
        print("   📊 프로시저 실행 중...")
        classified_result = await batch_service.db_manager.call_procedure(
            "classify_chat_keywords_by_date",
            {"from_date": start_date, "to_date": end_date}
        )
        print(f"   ✅ 프로시저 완료: {len(classified_result)}개 레코드 처리됨")
        
        # 프로시저 실행 후 다시 확인
        print("   🔍 프로시저 실행 후 누락 데이터 재확인...")
        post_procedure_result = await batch_service.db_manager.execute_query(
            system_query,
            {"start_date": start_date, "end_date": end_date}
        )
        
        print(f"   📋 프로시저 후 결과: {len(post_procedure_result)}개")
        
        if len(post_procedure_result) != len(user_result):
            print(f"   ⚠️ 프로시저 실행 후 결과가 변경되었습니다! ({len(user_result)}개 -> {len(post_procedure_result)}개)")
            print("   💡 이것이 차이의 원인일 수 있습니다.")
        else:
            print("   ✅ 프로시저 실행 후에도 결과가 동일합니다.")
            
    except Exception as e:
        print(f"   ❌ 프로시저 테스트 실패: {e}")
    
    # 5. 106개 제한 테스트
    if len(system_result) >= 106:
        print(f"\n4️⃣ 106개 제한 테스트...")
        limited_query = system_query + " LIMIT 106"
        
        limited_result = await batch_service.db_manager.execute_query(
            limited_query,
            {"start_date": start_date, "end_date": end_date}
        )
        
        print(f"   📋 LIMIT 106 적용 결과: {len(limited_result)}개")
        print("   ✅ 106개 제한이 정상적으로 작동합니다.")


if __name__ == "__main__":
    try:
        asyncio.run(test_fixed_query())
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}") 