#!/usr/bin/env python3
"""
메인 배치 처리 스크립트 (리팩토링 버전)
- 재사용 가능한 서비스 기반 아키텍처
- 통합 설정 관리
- 향상된 오류 처리
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from core.exceptions import BatchProcessError
from services.batch_service import BatchService


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='채팅 키워드 배치 처리 (리팩토링 버전)')
    parser.add_argument('--start-index', type=int, default=0, help='시작 인덱스 (기본값: 0)')
    parser.add_argument('--target-date', type=str, help='처리할 날짜 (YYYY-MM-DD 형식)')
    parser.add_argument('--start-date', type=str, help='처리할 시작 날짜 (YYYY-MM-DD 형식)')
    parser.add_argument('--end-date', type=str, help='처리할 종료 날짜 (YYYY-MM-DD 형식)')
    parser.add_argument('--validate-config', action='store_true', help='설정 유효성 검사만 실행')
    parser.add_argument('--check-missing', action='store_true', help='누락된 데이터 확인만 실행')
    parser.add_argument('--process-missing', action='store_true', help='누락된 데이터 처리 실행')
    parser.add_argument('--missing-only', action='store_true', help='누락된 데이터 확인 및 처리 통합 실행')
    parser.add_argument('--email', action='store_true', help='처리 완료 후 이메일 발송')
    
    args = parser.parse_args()
    
    try:
        # 설정 초기화 및 유효성 검사
        print("🔧 설정 초기화 중...")
        config = Config()
        
        if not config.validate_all():
            print("❌ 설정 유효성 검사 실패")
            sys.exit(1)
        
        if args.validate_config:
            print("✅ 설정 유효성 검사 완료")
            return
        
        print("✅ 설정 초기화 완료")
        
        # 배치 서비스 초기화
        batch_service = BatchService(config)
        
        # 이메일 발송 예정 알림
        if args.email:
            print("📧 처리 완료 후 이메일 발송 예정")
        
        # 누락 데이터 처리 모드
        if args.check_missing or args.process_missing or args.missing_only:
            if not (args.start_date and args.end_date):
                print("❌ 오류: 누락 데이터 처리에는 --start-date와 --end-date가 필요합니다.")
                print("사용법:")
                print("  python main_batch.py --check-missing --start-date 2025-06-11 --end-date 2025-06-19")
                print("  python main_batch.py --process-missing --start-date 2025-06-11 --end-date 2025-06-19")
                print("  python main_batch.py --missing-only --start-date 2025-06-11 --end-date 2025-06-19 --email")
                sys.exit(1)
            
            if args.check_missing:
                print(f"🔍 누락 데이터 확인 모드: {args.start_date} ~ {args.end_date}")
                result = await batch_service.check_missing_data(args.start_date, args.end_date)
                
                print(f"\n📋 누락 데이터 확인 결과:")
                print(f"  - 기간: {result.get('period', 'N/A')}")
                print(f"  - 처리된 데이터: {result.get('total_processed', 0):,}개")
                print(f"  - 누락된 데이터: {result.get('total_missing', 0):,}개")
                
                if result.get('missing_summary'):
                    print(f"\n  📅 일별 누락 현황:")
                    for date, count in result['missing_summary'].items():
                        print(f"    - {date}: {count:,}개")
                
                return result
            
            elif args.process_missing:
                print(f"🔧 누락 데이터 처리 모드: {args.start_date} ~ {args.end_date}")
                result = await batch_service.process_missing_data(
                    args.start_date, args.end_date, args.start_index
                )
                
                print(f"\n📋 누락 데이터 처리 결과:")
                print(f"  - 상태: {result.get('status', 'UNKNOWN')}")
                print(f"  - 고유 누락 질문: {result.get('total_missing_questions', 0):,}개")
                print(f"  - 처리 완료: {result.get('processed_count', 0):,}개")
                print(f"  - 중복 스킵: {result.get('skipped_count', 0):,}개")
                print(f"  - 소요 시간: {result.get('duration', 'N/A')}")
                
                # 이메일 발송
                if args.email:
                    await _send_email_notification(
                        batch_service, 
                        f"{args.start_date}~{args.end_date}",
                        result.get('status', 'UNKNOWN'),
                        result,
                        mode="누락 데이터 처리"
                    )
                
                return result
            
            elif args.missing_only:
                print(f"🚀 누락 데이터 통합 처리 모드: {args.start_date} ~ {args.end_date}")
                result = await batch_service.run_missing_data_batch(
                    args.start_date, args.end_date, args.start_index
                )
                
                print(f"\n📋 누락 데이터 통합 처리 결과:")
                print(f"  - 최종 상태: {result.get('final_status', 'UNKNOWN')}")
                print(f"  - 기간: {result.get('period', 'N/A')}")
                print(f"  - 처리된 데이터: {result.get('total_processed', 0):,}개")
                print(f"  - 누락된 데이터: {result.get('total_missing', 0):,}개")
                
                if result.get('processing_result'):
                    processing = result['processing_result']
                    print(f"  - 처리 완료: {processing.get('processed_count', 0):,}개")
                    print(f"  - 중복 스킵: {processing.get('skipped_count', 0):,}개")
                    print(f"  - 소요 시간: {processing.get('duration', 'N/A')}")
                
                # 이메일 발송
                if args.email:
                    await _send_email_notification(
                        batch_service, 
                        f"{args.start_date}~{args.end_date}",
                        result.get('final_status', 'UNKNOWN'),
                        result,
                        mode="누락 데이터 통합 처리"
                    )
                
                return result
        
        # 실행 모드 결정
        if args.start_date and args.end_date:
            # 기간 처리
            print(f"📅 기간별 처리 모드: {args.start_date} ~ {args.end_date}")
            
            result = await batch_service.run_batch_range(
                start_date=args.start_date,
                end_date=args.end_date,
                start_index=args.start_index
            )
            
            # 이메일 발송
            if args.email:
                await _send_email_notification(
                    batch_service, 
                    f"{args.start_date}~{args.end_date}",
                    result.get('status', 'UNKNOWN'),
                    result,
                    mode="기간별 처리"
                )
            
        elif args.start_date or args.end_date:
            # 시작일 또는 종료일 중 하나만 지정된 경우 오류
            print("❌ 오류: --start-date와 --end-date는 함께 사용해야 합니다.")
            print("사용법:")
            print("  단일 날짜: python main_batch.py --target-date 2024-03-15 --email")
            print("  기간 처리: python main_batch.py --start-date 2024-03-01 --end-date 2024-03-31 --email")
            print("  누락 확인: python main_batch.py --check-missing --start-date 2025-06-11 --end-date 2025-06-19")
            print("  누락 처리: python main_batch.py --process-missing --start-date 2025-06-11 --end-date 2025-06-19 --email")
            print("  누락 통합: python main_batch.py --missing-only --start-date 2025-06-11 --end-date 2025-06-19 --email")
            sys.exit(1)
            
        else:
            # 단일 날짜 처리
            target_date = args.target_date
            print(f"📋 단일 날짜 처리 모드: {target_date or '어제 날짜'}")
            
            result = await batch_service.run_single_batch(
                target_date=target_date,
                start_index=args.start_index
            )
            
            # 이메일 발송
            if args.email:
                await _send_email_notification(
                    batch_service, 
                    target_date or "어제 날짜",
                    result.get('status', 'UNKNOWN'),
                    result,
                    mode="단일 날짜 처리"
                )
        
        # 결과 출력
        print(f"\n🎉 배치 처리 완료!")
        print(f"📊 처리 결과:")
        print(f"  - 상태: {result.get('status', 'UNKNOWN')}")
        print(f"  - 전체 레코드: {result.get('total_rows', 0):,}개")
        print(f"  - 처리 완료: {result.get('processed_count', 0):,}개")
        print(f"  - 중복 스킵: {result.get('skipped_count', 0):,}개")
        print(f"  - 소요 시간: {result.get('duration', 'N/A')}")
        
    except BatchProcessError as e:
        print(f"❌ 배치 처리 오류: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")
        sys.exit(1)


async def _send_email_notification(batch_service, target_date: str, status: str, result: dict, mode: str = "배치 처리"):
    """이메일 알림을 발송합니다."""
    try:
        print(f"\n📧 이메일 발송 중...")
        
        # 상태 변환
        email_status = "SUCCESS" if status in ["SUCCESS", "COMPLETED"] else "FAILED"
        
        # 통계 정보 준비
        stats = {
            'start_time': result.get('start_time', 'N/A'),
            'end_time': result.get('end_time', 'N/A'),
            'duration': result.get('duration', 'N/A'),
            'total_rows': result.get('total_rows', 0),
            'processed_count': result.get('processed_count', 0),
            'skipped_count': result.get('skipped_count', 0),
            'category_distribution': result.get('category_distribution', {}),
            'mode': mode
        }
        
        # 이메일 발송
        await batch_service._send_notification(
            target_date=target_date,
            status=email_status,
            stats=stats,
            error_message=result.get('error_message') if email_status == "FAILED" else None,
            attach_excel=True if email_status == "SUCCESS" else False
        )
        
        print(f"📧 이메일 발송 완료!")
        
    except Exception as e:
        print(f"📧 이메일 발송 실패: {e}")
        # 이메일 발송 실패는 전체 프로세스를 중단시키지 않음


if __name__ == "__main__":
    asyncio.run(main()) 