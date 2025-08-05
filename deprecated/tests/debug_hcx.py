#!/usr/bin/env python3
"""
HCX API 응답 구조 디버깅 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from services.hcx_service import HCXService

def test_hcx_response():
    """HCX API 응답 구조를 테스트합니다."""
    
    print("🔍 HCX API 응답 구조 디버깅")
    print("=" * 50)
    
    try:
        # 설정 초기화
        config = Config()
        hcx_service = HCXService(config.hcx)
        
        # 간단한 테스트 질문
        test_query = "전학을 신청하려면 어떤 서류가 필요한가요?"
        
        print(f"📝 테스트 질문: {test_query}")
        print("-" * 50)
        
        # HCX 분류 실행
        result = hcx_service.classify_education_question(test_query)
        
        print(f"\n✅ 최종 결과:")
        print(f"   - 결과 타입: {type(result)}")
        print(f"   - 결과 길이: {len(result) if result else 0}")
        print(f"   - 결과 내용: {result}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_hcx_response() 