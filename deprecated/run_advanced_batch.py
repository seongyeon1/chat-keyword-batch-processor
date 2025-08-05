#!/usr/bin/env python3
"""
통합 배치 처리 스크립트
- 기본 배치 처리
- 누락 데이터 확인 및 처리
- 새로운 쿼리 모듈 기반
"""

import asyncio
import sys
import os
from datetime import datetime
import argparse

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.batch_service import BatchService
from queries.batch_queries import BatchQueries
from core.exceptions import BatchProcessError


async def run_basic_batch_processing(start_date: str, end_date: str):
    """기본 배치 처리 실행"""
    print("🚀 기본 배치 처리 시작")
    print("=" * 60)
    print(f"📅 처리 기간: {start_date} ~ {end_date}")
    print()
    
    try:
        config = Config()
        batch_service = BatchService(config)
        
        # 기간별 배치 처리 실행
        result = await batch_service.run_batch_range(start_date, end_date)
        
        print(f"\n🎉 기본 배치 처리 완료!")
        print("=" * 60)
        print(f"📊 처리 결과:")
        print(f"   - 상태: {result.get('status', 'UNKNOWN')}")
        print(f"   - 전체 데이터: {result.get('total_rows', 0)}개")
        print(f"   - 처리된 데이터: {result.get('processed_count', 0)}개")
        print(f"   - 스킵된 데이터: {result.get('skipped_count', 0)}개")
        print(f"   - 처리 시간: {result.get('duration', 'N/A')}")
        
        # 날짜별 세부 정보
        if result.get('details'):
            print(f"\n📅 날짜별 처리 결과:")
            for detail in result['details']:
                print(f"   - {detail['date']}: {detail['processed']}개 처리, {detail['skipped']}개 스킵")
        
        return result
        
    except Exception as e:
        print(f"❌ 기본 배치 처리 실패: {e}")
        raise


async def run_missing_data_check(start_date: str, end_date: str):
    """누락 데이터 확인"""
    print("🔍 누락 데이터 확인")
    print("=" * 60)
    print(f"📅 확인 기간: {start_date} ~ {end_date}")
    print()
    
    try:
        config = Config()
        batch_service = BatchService(config)
        
        result = await batch_service.check_missing_data(start_date, end_date)
        
        print(f"\n✅ 누락 데이터 확인 완료!")
        print("=" * 60)
        
        stats = result.get('stats', {})
        print(f"📊 통계 정보:")
        print(f"   - 전체 고유 질문: {stats.get('total_unique_questions', 0)}개")
        print(f"   - 기존 처리된 질문: {stats.get('total_processed_questions', 0)}개")
        print(f"   - 누락된 질문: {stats.get('total_missing_questions', 0)}개")
        print(f"   - 처리율: {stats.get('processing_rate', 0)}%")
        
        # 날짜별 누락 정보
        missing_summary = result.get('missing_summary', {})
        if missing_summary:
            print(f"\n📅 날짜별 누락 데이터:")
            for date, info in missing_summary.items():
                print(f"   - {date}: {info.get('missing_questions', 0)}개")
        
        return result
        
    except Exception as e:
        print(f"❌ 누락 데이터 확인 실패: {e}")
        raise


async def run_missing_data_processing(start_date: str, end_date: str, limit: int = None, auto_confirm: bool = True):
    """누락 데이터 처리"""
    limit_text = f" (최대 {limit}개 제한)" if limit else ""
    print("🔧 누락 데이터 처리")
    print("=" * 60)
    print(f"📅 처리 기간: {start_date} ~ {end_date}{limit_text}")
    print()
    
    try:
        config = Config()
        batch_service = BatchService(config)
        queries = BatchQueries()
        
        # 1. 누락 데이터 현황 확인
        print("1️⃣ 누락 데이터 현황 확인 중...")
        
        missing_status_query = queries.get_missing_data_status(start_date, end_date)
        missing_status = await batch_service.db_manager.execute_query(missing_status_query)
        
        if not missing_status:
            print("   ✅ 누락된 데이터가 없습니다!")
            return {"status": "SUCCESS", "message": "누락 데이터 없음"}
        
        print("   📊 날짜별 누락 데이터 현황:")
        total_missing = 0
        for row in missing_status:
            missing_date = row[0]
            count = row[1]
            total_missing += count
            print(f"     - {missing_date}: {count}개")
        
        if limit and total_missing > limit:
            print(f"   📋 전체 누락 데이터: {total_missing}개 (처리 제한: {limit}개)")
            print(f"   ⚠️ {total_missing - limit}개는 이후에 처리됩니다.")
        else:
            print(f"   📋 총 누락 데이터: {total_missing}개")
        
        if total_missing == 0:
            print("   ✅ 처리할 누락 데이터가 없습니다!")
            return {"status": "SUCCESS", "message": "처리할 누락 데이터 없음"}
        
        # 실제 처리할 데이터 수 계산
        actual_process_count = min(total_missing, limit) if limit else total_missing
        
        # 2. 사용자 확인 (auto_confirm이 False인 경우)
        if not auto_confirm:
            print(f"\n❓ {actual_process_count}개의 누락 데이터를 처리하시겠습니까? (y/N): ", end="")
            try:
                response = input().strip().lower()
                if response not in ['y', 'yes']:
                    print("   ❌ 사용자가 처리를 취소했습니다.")
                    return {"status": "CANCELLED", "message": "사용자 취소"}
            except KeyboardInterrupt:
                print("\n   ❌ 사용자가 처리를 중단했습니다.")
                return {"status": "CANCELLED", "message": "사용자 중단"}
            except EOFError:
                print("\n   ⚠️ 사용자 입력을 받을 수 없는 환경입니다. 자동으로 처리를 진행합니다.")
                print("   💡 수동 확인이 필요한 경우 대화형 터미널에서 실행해주세요.")
        
        # 3. 누락 데이터 처리 실행
        print("\n2️⃣ 누락 데이터 처리 실행 중...")
        start_time = datetime.now()
        
        result = await batch_service.process_missing_data(start_date, end_date, limit=limit)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 4. 결과 출력
        limit_info = f" (제한: {limit}개)" if limit else ""
        print(f"\n🎉 누락 데이터 처리 완료{limit_info}!")
        print("=" * 60)
        print(f"📊 처리 결과:")
        print(f"   - 기간: {result.get('period', 'N/A')}")
        print(f"   - 발견된 누락 데이터: {result.get('total_missing_questions', 0)}개")
        print(f"   - 처리된 데이터: {result.get('processed_count', 0)}개")
        print(f"   - 스킵된 데이터: {result.get('skipped_count', 0)}개")
        print(f"   - 처리 시간: {duration.total_seconds():.1f}초")
        
        # 제한 관련 정보 출력
        if limit:
            print(f"   - 적용된 제한: {limit}개")
            if result.get('limit_reached'):
                print(f"   ⚠️ 제한에 도달했습니다. 추가 데이터가 있을 수 있습니다.")
        
        # 5. 검증 결과 출력
        if 'verification' in result:
            verification = result['verification']
            print(f"\n🔍 처리 후 검증:")
            if verification.get('verification_success', False):
                print("   ✅ 처리된 모든 데이터가 성공적으로 저장되었습니다!")
            else:
                remaining_count = verification.get('remaining_missing_count', 0)
                if limit and result.get('limit_reached'):
                    print(f"   ℹ️ 제한으로 인해 {remaining_count}개의 데이터가 여전히 누락되어 있습니다.")
                    print(f"   💡 나머지 데이터 처리를 위해 다시 실행하거나 제한을 늘려주세요.")
                else:
                    print(f"   ⚠️ {remaining_count}개의 데이터가 여전히 누락되어 있습니다.")
                
                if 'remaining_by_date' in verification:
                    print("   📅 날짜별 잔여 누락 데이터:")
                    for date, count in verification['remaining_by_date'].items():
                        print(f"     - {date}: {count}개")
        
        # 6. 최종 상태 확인
        print(f"\n3️⃣ 최종 상태 확인...")
        final_check_query = queries.get_final_missing_count(
            start_date, end_date, datetime.now().strftime('%Y-%m-%d')
        )
        
        final_result = await batch_service.db_manager.execute_query(final_check_query)
        final_missing_count = final_result[0][0] if final_result else 0
        print(f"   📊 최종 누락 데이터: {final_missing_count}개")
        
        if final_missing_count == 0:
            print("   🎉 완벽! 모든 데이터가 처리되었습니다!")
        else:
            if limit and final_missing_count > 0:
                print(f"   ℹ️ 제한({limit}개)으로 인해 {final_missing_count}개의 데이터가 남아있습니다.")
                print(f"   💡 나머지 처리 명령어:")
                print(f"       python run_advanced_batch.py missing {start_date} {end_date} --limit {final_missing_count}")
            else:
                print(f"   ⚠️ 여전히 {final_missing_count}개의 데이터가 누락되어 있습니다.")
                print("   💡 다시 실행하거나 수동으로 확인이 필요할 수 있습니다.")
        
        return result
        
    except Exception as e:
        print(f"❌ 누락 데이터 처리 실패: {e}")
        raise


async def run_complete_batch_processing(start_date: str, end_date: str, limit: int = None):
    """완전한 배치 처리 (기본 + 누락 데이터)"""
    print("🚀 완전한 배치 처리 시작")
    print("=" * 80)
    print(f"📅 처리 기간: {start_date} ~ {end_date}")
    if limit:
        print(f"🎯 누락 데이터 처리 제한: {limit}개")
    print()
    
    try:
        # 1. 기본 배치 처리
        print("STEP 1: 기본 배치 처리")
        print("-" * 40)
        basic_result = await run_basic_batch_processing(start_date, end_date)
        
        print("\n" + "=" * 80)
        
        # 2. 누락 데이터 확인
        print("STEP 2: 누락 데이터 확인")
        print("-" * 40)
        missing_check = await run_missing_data_check(start_date, end_date)
        
        # 3. 누락 데이터가 있으면 처리
        total_missing = missing_check.get('stats', {}).get('total_missing_questions', 0)
        if total_missing > 0:
            print("\n" + "=" * 80)
            print("STEP 3: 누락 데이터 처리")
            print("-" * 40)
            missing_result = await run_missing_data_processing(start_date, end_date, limit, auto_confirm=True)
        else:
            print("\n✅ 누락 데이터가 없어 추가 처리를 건너뜁니다.")
            missing_result = {"status": "SUCCESS", "message": "누락 데이터 없음"}
        
        # 4. 최종 결과 요약
        print("\n" + "=" * 80)
        print("🎉 완전한 배치 처리 완료!")
        print("=" * 80)
        
        print(f"📊 최종 요약:")
        print(f"   [기본 배치]")
        print(f"   - 처리된 데이터: {basic_result.get('processed_count', 0)}개")
        print(f"   - 스킵된 데이터: {basic_result.get('skipped_count', 0)}개")
        print(f"   - 처리 시간: {basic_result.get('duration', 'N/A')}")
        
        print(f"   [누락 데이터]")
        print(f"   - 발견된 누락 데이터: {total_missing}개")
        if total_missing > 0:
            print(f"   - 처리된 누락 데이터: {missing_result.get('processed_count', 0)}개")
            print(f"   - 스킵된 누락 데이터: {missing_result.get('skipped_count', 0)}개")
        
        total_processed = basic_result.get('processed_count', 0) + missing_result.get('processed_count', 0)
        print(f"   [전체 합계]")
        print(f"   - 총 처리된 데이터: {total_processed}개")
        
        return {
            "basic_result": basic_result,
            "missing_check": missing_check,
            "missing_result": missing_result,
            "total_processed": total_processed
        }
        
    except Exception as e:
        print(f"❌ 완전한 배치 처리 실패: {e}")
        raise


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 배치 처리 스크립트')
    parser.add_argument('mode', choices=['basic', 'check', 'missing', 'complete'], 
                       help='실행 모드: basic(기본배치), check(누락확인), missing(누락처리), complete(전체)')
    parser.add_argument('start_date', help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('end_date', help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, help='누락 데이터 처리 제한 수 (예: --limit 106)')
    
    # argparse가 실패할 경우를 대비한 기존 방식
    if len(sys.argv) < 4:
        print("❌ 사용법: python run_advanced_batch.py <mode> <start_date> <end_date> [옵션]")
        print("   모드:")
        print("     basic   - 기본 배치 처리만 실행")
        print("     check   - 누락 데이터 확인만 실행")
        print("     missing - 누락 데이터 처리만 실행")
        print("     complete- 기본 배치 + 누락 데이터 처리 전체 실행")
        print()
        print("   예시:")
        print("     python run_advanced_batch.py basic 2025-06-11 2025-06-19")
        print("     python run_advanced_batch.py check 2025-06-11 2025-06-19")
        print("     python run_advanced_batch.py missing 2025-06-11 2025-06-19 --limit 106")
        print("     python run_advanced_batch.py complete 2025-06-11 2025-06-19")
        sys.exit(1)
    
    try:
        args = parser.parse_args()
        mode = args.mode
        start_date = args.start_date
        end_date = args.end_date
        limit = args.limit
        
        if limit:
            print(f"🎯 처리 제한: {limit}개 데이터")
        
        # 모드별 실행
        if mode == 'basic':
            asyncio.run(run_basic_batch_processing(start_date, end_date))
        elif mode == 'check':
            asyncio.run(run_missing_data_check(start_date, end_date))
        elif mode == 'missing':
            asyncio.run(run_missing_data_processing(start_date, end_date, limit))
        elif mode == 'complete':
            asyncio.run(run_complete_batch_processing(start_date, end_date, limit))
            
    except SystemExit:
        # argparse에서 --help 등으로 종료한 경우
        pass
    except KeyboardInterrupt:
        print("\n⚠️ 사용자가 처리를 중단했습니다.")
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 