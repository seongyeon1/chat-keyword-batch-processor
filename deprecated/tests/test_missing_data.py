#!/usr/bin/env python3
"""
누락 데이터 처리 기능 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from services.batch_service import BatchService


async def test_missing_data_features():
    """누락 데이터 처리 기능들을 테스트합니다."""
    
    print("🚀 누락 데이터 처리 기능 테스트 시작")
    print("=" * 50)
    
    try:
        # 설정 초기화
        print("🔧 설정 초기화 중...")
        config = Config()
        
        if not config.validate_all():
            print("❌ 설정 유효성 검사 실패")
            return
        
        print("✅ 설정 초기화 완료")
        
        # 배치 서비스 초기화
        batch_service = BatchService(config)
        
        # 테스트할 날짜 범위 (사용자 제공)
        start_date = "2025-06-11"
        end_date = "2025-06-19"
        
        print(f"\n📅 테스트 기간: {start_date} ~ {end_date}")
        
        # 누락 데이터 확인
        print("\n" + "="*60)
        print("🔍 누락 데이터 확인 테스트")
        print("="*60)
        
        try:
            result = await batch_service.check_missing_data(start_date, end_date)
            
            print(f"✅ 누락 데이터 확인 성공!")
            print(f"📊 기간: {result['period']}")
            print(f"📈 전체 고유 질문: {result['stats']['total_unique_questions']}개")
            print(f"✅ 처리된 질문: {result['stats']['total_processed_questions']}개")
            print(f"🚫 누락된 질문: {result['stats']['total_missing_questions']}개")
            print(f"📊 처리율: {result['stats']['processing_rate']}%")
            
            # 일별 상세 정보
            print(f"\n📋 일별 상세 정보:")
            for date_str, data in result['total_summary'].items():
                processed = result['processed_summary'].get(date_str, {'processed_questions': 0})
                missing = result['missing_summary'].get(date_str, {'missing_questions': 0})
                
                print(f"  📅 {date_str}: "
                      f"전체 {data['unique_questions']}개, "
                      f"처리 {processed['processed_questions']}개, "
                      f"누락 {missing['missing_questions']}개")
            
            # 누락 데이터 처리 테스트
            if result['stats']['total_missing_questions'] > 0:
                print(f"\n🔧 누락 데이터 처리 테스트 시작...")
                process_result = await batch_service.process_missing_data(start_date, end_date)
                
                print(f"✅ 누락 데이터 처리 완료!")
                print(f"📊 처리 결과: {process_result['processed_count']}개 처리, {process_result['skipped_count']}개 건너뜀")
                print(f"⏱️ 소요 시간: {process_result['duration']}")
            else:
                print(f"ℹ️ 처리할 누락 데이터가 없습니다.")
            
        except Exception as e:
            print(f"❌ 누락 데이터 확인 실패: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. 통합 처리 테스트 (실제로는 실행하지 않고 설명만)
        print(f"\n🚀 3. 통합 처리 기능 안내")
        print("-" * 30)
        print("통합 처리는 다음 명령으로 실행 가능합니다:")
        print(f"  python main_batch.py --missing-only --start-date {start_date} --end-date {end_date}")
        print("또는:")
        print(f"  docker-compose exec keyword-batch /app/manual_run.sh --missing-only {start_date} {end_date}")
        
        print(f"\n🎉 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")


async def show_usage_examples():
    """사용법 예시를 출력합니다."""
    
    print("\n📚 누락 데이터 처리 사용법 예시")
    print("=" * 50)
    
    examples = [
        {
            "title": "1. 누락 데이터 확인만",
            "command": "python main_batch.py --check-missing --start-date 2025-06-11 --end-date 2025-06-19",
            "description": "누락된 데이터의 현황만 확인하고 처리하지 않습니다."
        },
        {
            "title": "2. 누락 데이터 처리만",
            "command": "python main_batch.py --process-missing --start-date 2025-06-11 --end-date 2025-06-19",
            "description": "누락된 데이터를 HCX API로 분류하여 데이터베이스에 저장합니다."
        },
        {
            "title": "3. 통합 처리 (확인 + 처리)",
            "command": "python main_batch.py --missing-only --start-date 2025-06-11 --end-date 2025-06-19",
            "description": "누락 데이터 확인과 처리를 한 번에 실행합니다."
        },
        {
            "title": "4. Docker 환경에서 실행",
            "command": "docker-compose exec keyword-batch /app/manual_run.sh --missing-only 2025-06-11 2025-06-19",
            "description": "Docker 컨테이너 내에서 누락 데이터 통합 처리를 실행합니다."
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}")
        print(f"명령어: {example['command']}")
        print(f"설명: {example['description']}")


if __name__ == "__main__":
    print("🧪 누락 데이터 처리 기능 테스트 및 예시")
    print("실제 데이터를 사용하여 테스트하려면 'test' 옵션을")
    print("사용법 예시만 보려면 'examples' 옵션을 선택하세요.")
    print()
    
    choice = input("선택하세요 (test/examples/both): ").strip().lower()
    
    if choice in ['test', 'both']:
        asyncio.run(test_missing_data_features())
    
    if choice in ['examples', 'both']:
        asyncio.run(show_usage_examples())
    
    if choice not in ['test', 'examples', 'both']:
        print("유효하지 않은 선택입니다. 'test', 'examples', 또는 'both'를 입력하세요.") 