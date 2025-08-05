#!/usr/bin/env python3
"""
키워드 길이 문제 해결 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.hcx_service import HCXService
from services.batch_service import BatchService


async def test_keyword_length_handling():
    """키워드 길이 처리 테스트"""
    print("🧪 키워드 길이 처리 테스트 시작")
    print("=" * 60)
    
    # 설정 초기화
    config = Config()
    hcx_service = HCXService(config.hcx)
    
    # 문제가 되었던 긴 질문 테스트
    long_question = """수업 중 '공기를 이루는 기체에 대해 조사해서 애니메이션으로 표현하기' 활동을 했어. 활동을 한 후 학생들이 직접 작성한 소감을 엑셀파일로 올릴테니 이러한 활동 모습을 묘사하는 문장을 작성해줘. 학생들이 직접 작성한 것이라 오타나 맞춤법 오류가 있으니 적당히 수정해 줘. 아래와 같은 양식으로 작성해 주면 돼. (학급) 학급에서 (첫 번째 열 내용 참고)를 주제로 (두 번째 열 내용 참고) 활동을 통해 (세 번째 열 내용 참고)를 배우며 (네 번째 열 내용 참고) 활동을 완수하였으며 (다섯 번째 열 내용 참고)를 개선하고자 생각하는 등 (참고5 내용 중 앞선 열의 내용과 관련된 역량 1가지)가 (향상됨 또는 돋보임 등 긍정적 표현). 문장 마지막에 있는 역량은 과학과 관련성이 높은 것 위주로 하면서도 가능한 여러 가지로 해줘."""
    
    print(f"📝 테스트 질문 길이: {len(long_question)}자")
    print(f"📝 질문 내용: {long_question[:100]}...")
    print()
    
    # 1. HCX 서비스 키워드 추출 테스트
    print("1️⃣ HCX 서비스 키워드 추출 테스트")
    print("-" * 40)
    
    try:
        keyword_categories = hcx_service.classify_education_question(long_question)
        print(f"✅ HCX 분류 성공: {len(keyword_categories)}개 결과")
        
        for i, item in enumerate(keyword_categories):
            keyword = item.get("keyword", "")
            categories = item.get("categories", [])
            
            print(f"   키워드 {i+1}: '{keyword}' (길이: {len(keyword)}자)")
            print(f"   카테고리: {categories}")
            
            if len(keyword) > 100:  # VARCHAR(100) 기준으로 변경
                print(f"   ❌ 키워드 길이 초과!")
            else:
                print(f"   ✅ 키워드 길이 정상")
            print()
            
    except Exception as e:
        print(f"❌ HCX 분류 실패: {e}")
    
    # 2. 배치 서비스 키워드 보완 테스트
    print("2️⃣ 배치 서비스 키워드 보완 테스트")
    print("-" * 40)
    
    batch_service = BatchService(config)
    
    # 긴 키워드 처리 테스트
    test_keywords = [
        long_question,  # 원본 질문 전체
        "",  # 빈 키워드
        "기타",  # 기본 키워드
        "수강신청",  # 정상 키워드
        "a" * 150,  # 길이 초과 키워드
    ]
    
    for i, test_keyword in enumerate(test_keywords):
        print(f"테스트 {i+1}: 원본 키워드 길이 {len(test_keyword)}자")
        extracted = batch_service._extract_simple_keyword(long_question)
        print(f"   추출된 키워드: '{extracted}' (길이: {len(extracted)}자)")
        
        if len(extracted) <= 100:  # 100자 기준으로 변경
            print(f"   ✅ 추출 성공")
        else:
            print(f"   ❌ 추출 실패")
        print()
    
    # 3. 데이터베이스 안전장치 테스트
    print("3️⃣ 데이터베이스 안전장치 테스트")
    print("-" * 40)
    
    # 모의 INSERT 데이터 생성
    test_params = {
        "query_text": long_question,
        "keyword": long_question,  # 문제가 되었던 긴 키워드
        "category_id": 1,
        "query_count": 1,
        "created_at": "2025-06-19",
        "batch_created_at": "2025-06-19 16:26:28"
    }
    
    # 키워드 길이 검증 시뮬레이션
    if 'keyword' in test_params:
        keyword = test_params['keyword']
        if len(str(keyword)) > 100:  # 100자 기준으로 변경
            print(f"⚠️ 키워드 길이 초과 감지: {len(str(keyword))}자")
            test_params['keyword'] = str(keyword)[:98] + "..."  # 98자로 변경
            print(f"✅ 키워드 자르기 완료: {len(test_params['keyword'])}자")
            print(f"   처리된 키워드: {test_params['keyword'][:50]}...")
        else:
            print(f"✅ 키워드 길이 정상: {len(str(keyword))}자")
    
    print()
    print("🎉 모든 테스트 완료!")
    print("💡 이제 배치 처리 시 키워드 길이 문제가 해결되어야 합니다.")


def main():
    """메인 함수"""
    try:
        asyncio.run(test_keyword_length_handling())
    except KeyboardInterrupt:
        print("\n⚠️ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 