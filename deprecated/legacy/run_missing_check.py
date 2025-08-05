#!/usr/bin/env python3
"""
누락 데이터 빠른 확인 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from services.batch_service import BatchService


async def quick_missing_check():
    """누락 데이터를 빠르게 확인합니다."""
    
    if len(sys.argv) != 3:
        print("사용법: python run_missing_check.py <시작날짜> <종료날짜>")
        print("예시: python run_missing_check.py 2025-06-11 2025-06-19")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    print(f"🔍 누락 데이터 확인: {start_date} ~ {end_date}")
    print("=" * 50)
    
    try:
        # 설정 초기화
        config = Config()
        if not config.validate_all():
            print("❌ 설정 유효성 검사 실패")
            sys.exit(1)
        
        # 배치 서비스 초기화
        batch_service = BatchService(config)
        
        # 누락 데이터 확인
        result = await batch_service.check_missing_data(start_date, end_date)
        
        print(f"\n📊 확인 결과:")
        print(f"  - 기간: {result['period']}")
        print(f"  - 처리된 데이터: {result['total_processed']:,}개")
        print(f"  - 누락된 데이터: {result['total_missing']:,}개")
        
        if result.get('processed_summary'):
            print(f"\n📅 일별 처리 현황:")
            for date, count in result['processed_summary'].items():
                print(f"    - {date}: {count:,}개 처리됨")
        
        if result.get('missing_summary'):
            print(f"\n🚫 일별 누락 현황:")
            for date, count in result['missing_summary'].items():
                print(f"    - {date}: {count:,}개 누락")
        
        if result['total_missing'] > 0:
            print(f"\n💡 누락 데이터 처리 명령어:")
            print(f"python main_batch.py --process-missing --start-date {start_date} --end-date {end_date}")
            print(f"또는")
            print(f"docker-compose exec keyword-batch /app/manual_run.sh --process-missing {start_date} {end_date}")
        else:
            print(f"\n✅ 누락된 데이터가 없습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(quick_missing_check()) 