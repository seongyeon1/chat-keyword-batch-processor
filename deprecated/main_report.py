#!/usr/bin/env python3
"""
메인 보고서 생성 스크립트 (리팩토링 버전)
- 서비스 기반 아키텍처
- 통합 설정 관리
- 간편 사용법 지원
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from core.database import DatabaseManager
from core.exceptions import ExcelError, EmailError
from services.excel_service import ExcelService
from services.email_service import EmailService


def parse_date_shortcut(date_str: str) -> tuple:
    """날짜 단축어를 실제 날짜로 변환합니다."""
    today = datetime.now()
    
    if date_str == "today":
        date = today.strftime('%Y-%m-%d')
        return date, date
    
    elif date_str == "yesterday":
        date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        return date, date
    
    elif date_str == "this-week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    elif date_str == "last-week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    elif date_str == "this-month":
        start = today.replace(day=1)
        next_month = start.replace(month=start.month + 1) if start.month < 12 else start.replace(year=start.year + 1, month=1)
        end = next_month - timedelta(days=1)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    elif date_str == "last-month":
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    else:
        # 일반 날짜 문자열
        return date_str, date_str


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='채팅 키워드 분류 보고서 생성 (리팩토링 버전)')
    parser.add_argument('start_date', nargs='?', help='시작 날짜 또는 단축어 (today, yesterday, this-week, last-week, this-month, last-month)')
    parser.add_argument('end_date', nargs='?', help='종료 날짜 (선택사항)')
    parser.add_argument('--output-dir', default='reports', help='출력 디렉토리 (기본값: reports)')
    parser.add_argument('--email', '--send-email', action='store_true', help='이메일로 보고서 발송')
    parser.add_argument('--validate-config', action='store_true', help='설정 유효성 검사만 실행')
    
    args = parser.parse_args()
    
    try:
        # 설정 초기화
        print("🔧 설정 초기화 중...")
        config = Config()
        
        if not config.validate_all():
            print("❌ 설정 유효성 검사 실패")
            sys.exit(1)
        
        if args.validate_config:
            print("✅ 설정 유효성 검사 완료")
            return
        
        # 출력 디렉토리 설정 적용
        config.report.output_dir = args.output_dir
        
        print("✅ 설정 초기화 완료")
        
        # 날짜 처리
        if not args.start_date:
            print("❌ 시작 날짜를 입력하세요.")
            print("사용법:")
            print("  python main_report.py 2024-03-01 2024-03-31")
            print("  python main_report.py today")
            print("  python main_report.py last-month --email")
            sys.exit(1)
        
        # 날짜 파싱
        if args.end_date:
            start_date = args.start_date
            end_date = args.end_date
        else:
            start_date, end_date = parse_date_shortcut(args.start_date)
        
        print(f"📅 보고서 생성 기간: {start_date} ~ {end_date}")
        
        # 서비스 초기화
        db_manager = DatabaseManager(config.database)
        excel_service = ExcelService(config.report, db_manager)
        
        # 보고서 생성
        excel_filename, summary_stats = await excel_service.generate_report(start_date, end_date)
        
        # 요약 출력
        excel_service.print_summary_report(summary_stats, excel_filename)
        
        # 이메일 발송
        if args.email:
            print(f"\n📧 이메일 발송 준비 중...")
            try:
                email_service = EmailService(config.email)
                report_period = f"{start_date} ~ {end_date}" if start_date != end_date else start_date
                
                success = email_service.send_excel_report(excel_filename, report_period)
                if success:
                    print(f"📧 이메일 발송 완료!")
                else:
                    print(f"📧 이메일 발송 실패!")
                    
            except EmailError as e:
                print(f"📧 이메일 발송 오류: {e}")
            except Exception as e:
                print(f"📧 이메일 발송 중 예상치 못한 오류: {e}")
        
        print(f"\n🎉 보고서 생성 완료!")
        print(f"📄 파일 경로: {excel_filename}")
        
        # 파일 정보
        file_info = excel_service.get_file_size_info(excel_filename)
        if file_info.get("exists"):
            print(f"📊 파일 크기: {file_info['size_mb']} MB")
            print(f"🕒 생성 시간: {file_info['created_time']}")
        
    except ExcelError as e:
        print(f"❌ 보고서 생성 오류: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 