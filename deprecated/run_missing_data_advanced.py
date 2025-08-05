#!/usr/bin/env python3
"""
고급 누락 데이터 처리 스크립트
사용자 제공 SQL 쿼리 방식을 기반으로 정확한 누락 데이터 처리
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
from core.exceptions import BatchProcessError


async def run_advanced_missing_data_processing(start_date: str, end_date: str, limit: int = None):
    """고급 누락 데이터 처리 실행"""
    limit_text = f" (최대 {limit}개 제한)" if limit else ""
    print("🚀 고급 누락 데이터 처리 시작")
    print("=" * 60)
    print(f"📅 처리 기간: {start_date} ~ {end_date}{limit_text}")
    print()
    
    try:
        # 설정 초기화
        config = Config()
        batch_service = BatchService(config)
        
        # 1. 프로시저 실행 상태 확인
        print("1️⃣ classify_chat_keywords_by_date 프로시저 실행 중...")

        
        classified_result = await batch_service.db_manager.call_procedure(
            "classify_chat_keywords_by_date",
            {"from_date": start_date, "to_date": end_date}
        )
        print(f"   ✅ 프로시저 완료: {len(classified_result)}개 레코드 처리됨")
        
        # 2. 정확한 누락 데이터 현황 확인
        print("\n2️⃣ 정확한 누락 데이터 현황 확인 중...")
        
        # 🔧 temp_classified 대신 admin_chat_keywords 사용 (프로시저 실행 전에도 작동)
        missing_status_query = f"""
            SELECT 
                missing_date,
                COUNT(*) AS total_missing_count
            FROM (
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
            ) AS missing_data
            GROUP BY missing_date
            ORDER BY missing_date
        """
        
        missing_status = await batch_service.db_manager.execute_query(
            missing_status_query,
            {"start_date": start_date, "end_date": end_date}
        )
        
        if not missing_status:
            print("   ✅ 누락된 데이터가 없습니다!")
            return
        
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
            return
        
        # 실제 처리할 데이터 수 계산
        actual_process_count = min(total_missing, limit) if limit else total_missing
        
        # 3. 사용자 확인
        print(f"\n❓ {actual_process_count}개의 누락 데이터를 처리하시겠습니까? (y/N): ", end="")
        try:
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                print("   ❌ 사용자가 처리를 취소했습니다.")
                return
        except KeyboardInterrupt:
            print("\n   ❌ 사용자가 처리를 중단했습니다.")
            return
        except EOFError:
            print("\n   ⚠️ 사용자 입력을 받을 수 없는 환경입니다. 자동으로 처리를 진행합니다.")
            print("   💡 수동 확인이 필요한 경우 대화형 터미널에서 실행해주세요.")
        
        # 4. 누락 데이터 처리 실행
        print("\n3️⃣ 누락 데이터 처리 실행 중...")
        start_time = datetime.now()
        
        result = await batch_service.process_missing_data(start_date, end_date, limit=limit)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 5. 결과 출력
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
        
        # 6. 검증 결과 출력
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
        
        # 7. 최종 상태 확인
        print(f"\n4️⃣ 최종 상태 확인...")
        final_check_query = """
            SELECT 
                COUNT(DISTINCT c.input_text) AS final_missing_count
            FROM chattings c
            LEFT JOIN (
                SELECT query_text, DATE(created_at) AS dt
                FROM temp_classified
                UNION
                SELECT query_text, DATE(created_at) AS dt  
                FROM admin_chat_keywords
                WHERE batch_created_at >= :today
            ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
            WHERE t.query_text IS NULL
              AND c.created_at BETWEEN :start_date AND :end_date
        """
        
        today = datetime.now().strftime('%Y-%m-%d')
        final_result = await batch_service.db_manager.execute_query(
            final_check_query,
            {
                "start_date": start_date, 
                "end_date": end_date,
                "today": today
            }
        )
        
        final_missing_count = final_result[0][0] if final_result else 0
        print(f"   📊 최종 누락 데이터: {final_missing_count}개")
        
        if final_missing_count == 0:
            print("   🎉 완벽! 모든 데이터가 처리되었습니다!")
        else:
            if limit and final_missing_count > 0:
                print(f"   ℹ️ 제한({limit}개)으로 인해 {final_missing_count}개의 데이터가 남아있습니다.")
                print(f"   💡 나머지 처리 명령어:")
                print(f"       python run_missing_data_advanced.py {start_date} {end_date} --limit {final_missing_count}")
            else:
                print(f"   ⚠️ 여전히 {final_missing_count}개의 데이터가 누락되어 있습니다.")
                print("   💡 다시 실행하거나 수동으로 확인이 필요할 수 있습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        raise


async def show_missing_data_summary(start_date: str, end_date: str):
    """누락 데이터 요약 정보만 표시"""
    print("📊 누락 데이터 요약 정보")
    print("=" * 60)
    
    try:
        config = Config()
        batch_service = BatchService(config)
        
        # 1. 프로시저 처리 현황
        print("1️⃣ 프로시저 처리 현황 확인 중...")
        processed_query = """
            SELECT DATE(created_at) AS date, SUM(query_count) AS total
            FROM temp_classified
            WHERE DATE(created_at) BETWEEN :start_date AND :end_date
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        processed_result = await batch_service.db_manager.execute_query(
            processed_query,
            {"start_date": start_date, "end_date": end_date}
        )
        
        print("   📅 프로시저 처리 현황:")
        for row in processed_result:
            print(f"     - {row[0]}: {row[1]}개")
        
        # 2. 누락 데이터 현황
        print("\n2️⃣ 누락 데이터 현황 확인 중...")
        missing_query = """
            SELECT 
                missing_date,
                SUM(missing_count) AS total_missing_count
            FROM (
                SELECT 
                    DATE(c.created_at) AS missing_date,
                    c.input_text,
                    COUNT(*) AS missing_count
                FROM chattings c
                LEFT JOIN (
                    SELECT query_text, DATE(created_at) AS dt
                    FROM temp_classified
                ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
                WHERE t.query_text IS NULL
                  AND c.created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE(c.created_at), c.input_text
            ) AS missing_data
            GROUP BY missing_date
            ORDER BY missing_date
        """
        
        missing_result = await batch_service.db_manager.execute_query(
            missing_query,
            {"start_date": start_date, "end_date": end_date}
        )
        
        print("   📅 누락 데이터 현황:")
        total_missing = 0
        for row in missing_result:
            count = row[1]
            total_missing += count
            print(f"     - {row[0]}: {count}개")
        
        print(f"\n📋 총 누락 데이터: {total_missing}개")
        
        if total_missing > 0:
            print(f"\n💡 처리 명령어:")
            print(f"   python run_missing_data_advanced.py {start_date} {end_date}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='고급 누락 데이터 처리 스크립트')
    parser.add_argument('start_date', help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('end_date', help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--summary', action='store_true', help='요약 정보만 표시')
    parser.add_argument('--limit', type=int, help='처리할 최대 데이터 수 (예: --limit 106)')
    
    # argparse가 실패할 경우를 대비한 기존 방식
    if len(sys.argv) < 3:
        print("❌ 사용법: python run_missing_data_advanced.py <start_date> <end_date> [옵션]")
        print("   기본: python run_missing_data_advanced.py 2025-06-11 2025-06-19")
        print("   요약: python run_missing_data_advanced.py 2025-06-11 2025-06-19 --summary")
        print("   제한: python run_missing_data_advanced.py 2025-06-11 2025-06-19 --limit 106")
        sys.exit(1)
    
    try:
        args = parser.parse_args()
        start_date = args.start_date
        end_date = args.end_date
        summary_only = args.summary
        limit = args.limit
        
        if limit:
            print(f"🎯 처리 제한: {limit}개 데이터만 처리합니다.")
        
        if summary_only:
            asyncio.run(show_missing_data_summary(start_date, end_date))
        else:
            asyncio.run(run_advanced_missing_data_processing(start_date, end_date, limit=limit))
            
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