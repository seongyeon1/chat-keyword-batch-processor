#!/usr/bin/env python3
"""
개선된 CLI 인터페이스 - 사용하기 쉬운 명령어로 배치 처리를 관리합니다.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.config import Config
from core.exceptions import BatchProcessError
from services.batch_service import BatchService
from services.email_service import EmailService
from services.excel_service import ExcelService
from utils.date_utils import DateUtils
from utils.logger import setup_logging, log_info, log_warning, log_error


class CLI:
    """개선된 CLI 인터페이스"""
    
    def __init__(self):
        self.config = Config()
        self.batch_service = None
    
    async def init_services(self):
        """서비스들을 초기화합니다."""
        self.config = Config()
        
        # 🚀 로깅 시스템 초기화
        setup_logging(self.config.log)
        log_info("🚀 CLI 시스템 시작")
        
        # 설정 검증
        if not self.config.validate_all():
            log_error("❌ 설정 검증 실패")
            sys.exit(1)
        
        self.batch_service = BatchService(self.config)
        self.email_service = EmailService(self.config.email)
        self.excel_service = ExcelService(self.config.report, self.batch_service.db_manager)
        
        log_info("✅ 모든 서비스 초기화 완료")
    
    def create_parser(self) -> argparse.ArgumentParser:
        """명령어 파서를 생성합니다."""
        parser = argparse.ArgumentParser(
            description='개선된 채팅 키워드 배치 처리 시스템',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
사용 예시:

  # 기본 배치 처리
  python cli.py batch                                    # 어제 날짜 처리
  python cli.py batch -d 2024-03-15                     # 특정 날짜 처리
  python cli.py batch -s 2024-03-01 -e 2024-03-31     # 기간 처리
  python cli.py batch -d yesterday --email             # 어제 + 이메일 발송
  
  # 병렬 처리 옵션
  python cli.py batch -s 2024-03-01 -e 2024-03-31 --parallel      # 날짜별 병렬 처리
  python cli.py batch -d 2024-03-15 --workers 8                   # 워커 수 지정
  
  # 누락 데이터 처리
  python cli.py missing check -s 2024-03-01 -e 2024-03-31        # 누락 확인
  python cli.py missing process -s 2024-03-01 -e 2024-03-31      # 누락 처리
  python cli.py missing auto -s 2024-03-01 -e 2024-03-31 --email # 누락 자동 처리
  
  # 보고서 생성
  python cli.py report -d yesterday --email                       # 어제 보고서 + 이메일
  python cli.py report -s 2024-03-01 -e 2024-03-31               # 기간 보고서
  
  # 설정 및 유틸리티
  python cli.py config validate                                   # 설정 검증
  python cli.py config show                                       # 설정 요약
  python cli.py status                                            # 시스템 상태
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
        
        # batch 명령어
        self._add_batch_parser(subparsers)
        
        # missing 명령어
        self._add_missing_parser(subparsers)
        
        # report 명령어
        self._add_report_parser(subparsers)
        
        # config 명령어
        self._add_config_parser(subparsers)
        
        # status 명령어
        self._add_status_parser(subparsers)
        
        return parser
    
    def _add_batch_parser(self, subparsers):
        """batch 명령어 파서를 추가합니다."""
        batch_parser = subparsers.add_parser('batch', help='배치 처리 실행')
        
        # 날짜 관련 옵션
        date_group = batch_parser.add_mutually_exclusive_group()
        date_group.add_argument('-d', '--date', type=str, 
                               help='처리할 날짜 (YYYY-MM-DD 또는 yesterday, today)')
        
        # 기간 관련 옵션
        batch_parser.add_argument('-s', '--start-date', type=str, 
                                 help='시작 날짜 (YYYY-MM-DD)')
        batch_parser.add_argument('-e', '--end-date', type=str,
                                 help='종료 날짜 (YYYY-MM-DD)')
        
        # 처리 옵션
        batch_parser.add_argument('--start-index', type=int, default=0,
                                 help='시작 인덱스 (기본값: 0)')
        
        # 병렬 처리 옵션
        batch_parser.add_argument('--parallel', action='store_true',
                                 help='병렬 처리 활성화')
        batch_parser.add_argument('--workers', type=int,
                                 help='병렬 워커 수')
        batch_parser.add_argument('--chunk-size', type=int,
                                 help='청크 크기')
        
        # 이메일 옵션
        batch_parser.add_argument('--email', action='store_true',
                                 help='완료 후 이메일 발송')
        
        # 기타 옵션
        batch_parser.add_argument('--dry-run', action='store_true',
                                 help='실제 처리 없이 계획만 출력')
    
    def _add_missing_parser(self, subparsers):
        """missing 명령어 파서를 추가합니다."""
        missing_parser = subparsers.add_parser('missing', help='누락 데이터 처리')
        missing_subparsers = missing_parser.add_subparsers(dest='missing_action', help='누락 데이터 작업')
        
        # check 서브명령어
        check_parser = missing_subparsers.add_parser('check', help='누락 데이터 확인')
        check_parser.add_argument('-s', '--start-date', type=str, required=True, help='시작 날짜')
        check_parser.add_argument('-e', '--end-date', type=str, required=True, help='종료 날짜')
        
        # process 서브명령어
        process_parser = missing_subparsers.add_parser('process', help='누락 데이터 처리')
        process_parser.add_argument('-s', '--start-date', type=str, required=True, help='시작 날짜')
        process_parser.add_argument('-e', '--end-date', type=str, required=True, help='종료 날짜')
        process_parser.add_argument('--start-index', type=int, default=0, help='시작 인덱스')
        process_parser.add_argument('--email', action='store_true', help='완료 후 이메일 발송')
        
        # auto 서브명령어 (확인 + 처리 통합)
        auto_parser = missing_subparsers.add_parser('auto', help='누락 데이터 자동 처리')
        auto_parser.add_argument('-s', '--start-date', type=str, required=True, help='시작 날짜')
        auto_parser.add_argument('-e', '--end-date', type=str, required=True, help='종료 날짜')
        auto_parser.add_argument('--start-index', type=int, default=0, help='시작 인덱스')
        auto_parser.add_argument('--email', action='store_true', help='완료 후 이메일 발송')
    
    def _add_report_parser(self, subparsers):
        """report 명령어 파서를 추가합니다."""
        report_parser = subparsers.add_parser('report', help='보고서 생성')
        
        # 날짜 관련 옵션
        date_group = report_parser.add_mutually_exclusive_group()
        date_group.add_argument('-d', '--date', type=str,
                               help='보고서 날짜 (YYYY-MM-DD 또는 yesterday, today)')
        
        # 기간 관련 옵션
        report_parser.add_argument('-s', '--start-date', type=str, help='시작 날짜')
        report_parser.add_argument('-e', '--end-date', type=str, help='종료 날짜')
        
        # 이메일 옵션
        report_parser.add_argument('--email', action='store_true', help='보고서 이메일 발송')
        
        # 출력 옵션
        report_parser.add_argument('-o', '--output', type=str, help='출력 파일 경로')
    
    def _add_config_parser(self, subparsers):
        """config 명령어 파서를 추가합니다."""
        config_parser = subparsers.add_parser('config', help='설정 관리')
        config_subparsers = config_parser.add_subparsers(dest='config_action', help='설정 작업')
        
        config_subparsers.add_parser('validate', help='설정 유효성 검사')
        config_subparsers.add_parser('show', help='현재 설정 표시')
    
    def _add_status_parser(self, subparsers):
        """status 명령어 파서를 추가합니다."""
        subparsers.add_parser('status', help='시스템 상태 확인')
    
    async def handle_batch(self, args) -> Dict[str, Any]:
        """배치 처리 명령을 처리합니다."""
        # 날짜 처리
        if args.date:
            if args.date in ['yesterday', 'today']:
                target_date, _ = DateUtils.parse_date_shortcut(args.date)
            else:
                target_date = args.date
            
            log_info(f"📅 단일 날짜 배치 처리: {target_date}")
            result = await self.batch_service.run_single_batch(
                target_date=target_date,
                start_index=args.start_index
            )
            
        elif args.start_date and args.end_date:
            log_info(f"📅 기간별 배치 처리: {args.start_date} ~ {args.end_date}")
            
            # 병렬 처리 설정 적용
            if args.parallel or args.workers or args.chunk_size:
                if args.workers:
                    self.config.parallel.max_workers = args.workers
                if args.chunk_size:
                    self.config.parallel.chunk_size = args.chunk_size
                if args.parallel:
                    self.config.parallel.enable_parallel_dates = True
                
                log_info(f"🚀 병렬 처리 설정:")
                log_info(f"   - 최대 워커: {self.config.parallel.max_workers}")
                log_info(f"   - 청크 크기: {self.config.parallel.chunk_size}")
                log_info(f"   - 날짜별 병렬: {self.config.parallel.enable_parallel_dates}")
            
            result = await self.batch_service.run_batch_range(
                start_date=args.start_date,
                end_date=args.end_date,
                start_index=args.start_index
            )
            
        else:
            # 기본값: 어제 날짜
            target_date = DateUtils.get_yesterday()
            log_info(f"📅 기본 배치 처리 (어제): {target_date}")
            result = await self.batch_service.run_single_batch(
                target_date=target_date,
                start_index=args.start_index
            )
        
        # 이메일 발송
        if args.email:
            await self._send_batch_email(result, args)
        
        return result
    
    async def handle_missing(self, args) -> Dict[str, Any]:
        """누락 데이터 처리 명령을 처리합니다."""
        if args.missing_action == 'check':
            log_info(f"🔍 누락 데이터 확인: {args.start_date} ~ {args.end_date}")
            result = await self.batch_service.check_missing_data(args.start_date, args.end_date)
            
            log_info(f"\n📋 누락 데이터 확인 결과:")
            log_info(f"  - 기간: {result.get('period', 'N/A')}")
            log_info(f"  - 처리된 데이터: {result.get('total_processed', 0):,}개")
            log_info(f"  - 누락된 데이터: {result.get('total_missing', 0):,}개")
            
            if result.get('missing_summary'):
                log_info(f"\n📅 일별 누락 현황:")
                for date, count in result['missing_summary'].items():
                    log_info(f"    - {date}: {count:,}개")
            
            return result
            
        elif args.missing_action == 'process':
            log_info(f"🔧 누락 데이터 처리: {args.start_date} ~ {args.end_date}")
            result = await self.batch_service.process_missing_data(
                args.start_date, args.end_date, args.start_index
            )
            
            if args.email and self.config.email.enable_email:
                await self._send_missing_email(result, args, "처리")
            
            return result
            
        elif args.missing_action == 'auto':
            log_info(f"🚀 누락 데이터 자동 처리: {args.start_date} ~ {args.end_date}")
            result = await self.batch_service.run_missing_data_batch(
                args.start_date, args.end_date, args.start_index
            )
            
            if args.email and self.config.email.enable_email:
                await self._send_missing_email(result, args, "자동 처리")
            
            return result
    
    async def handle_report(self, args) -> Dict[str, Any]:
        """보고서 생성 명령을 처리합니다."""
        try:
            from services.excel_service import ExcelService
            from services.email_service import EmailService
            from core.database import DatabaseManager
            from utils.date_utils import DateUtils
            
            # 날짜 처리
            if args.date:
                if args.date in ['yesterday', 'today', 'this-week', 'last-week', 'this-month', 'last-month']:
                    start_date, end_date = DateUtils.parse_date_shortcut(args.date)
                else:
                    start_date = end_date = args.date
            elif args.start_date and args.end_date:
                start_date = args.start_date
                end_date = args.end_date
            elif args.start_date:
                start_date = end_date = args.start_date
            else:
                # 기본값: 어제
                start_date, end_date = DateUtils.parse_date_shortcut('yesterday')
            
            log_info(f"📊 보고서 생성 중: {start_date} ~ {end_date}")
            
            # 서비스 초기화
            db_manager = DatabaseManager(self.config.database)
            excel_service = ExcelService(self.config.report, db_manager)
            
            # 보고서 생성
            excel_filename, summary_stats = await excel_service.generate_report(start_date, end_date)
            
            # 요약 출력
            excel_service.print_summary_report(summary_stats, excel_filename)
            
            result = {
                "status": "SUCCESS",
                "start_date": start_date,
                "end_date": end_date,
                "excel_filename": excel_filename,
                "summary_stats": summary_stats,
                "file_size": excel_service.get_file_size_info(excel_filename)
            }
            
            # 이메일 발송
            if args.email and self.config.email.enable_email:
                await self._send_report_email(result, args)
            
            log_info(f"\n🎉 보고서 생성 완료!")
            log_info(f"📄 파일 경로: {excel_filename}")
            
            # 파일 정보 출력
            file_info = result["file_size"]
            if file_info.get("exists"):
                log_info(f"📊 파일 크기: {file_info['size_mb']} MB")
                log_info(f"🕒 생성 시간: {file_info['created_time']}")
            
            return result
            
        except Exception as e:
            log_error(f"❌ 보고서 생성 실패: {e}")
            import traceback
            log_error(f"상세 오류:\n{traceback.format_exc()}")
            return {"status": "FAILED", "error": str(e)}
    
    def handle_config(self, args) -> Dict[str, Any]:
        """설정 관리 명령을 처리합니다."""
        if args.config_action == 'validate':
            log_info("🔧 설정 유효성 검사 중...")
            is_valid = self.config.validate_all()
            
            if is_valid:
                log_info("✅ 모든 설정이 유효합니다.")
                return {"status": "SUCCESS", "valid": True}
            else:
                log_info("❌ 설정 유효성 검사 실패")
                return {"status": "FAILED", "valid": False}
                
        elif args.config_action == 'show':
            log_info("🔧 현재 설정 요약:")
            summary = self.config.get_summary()
            
            for category, settings in summary.items():
                log_info(f"\n📋 {category.upper()}:")
                for key, value in settings.items():
                    log_info(f"  - {key}: {value}")
            
            return {"status": "SUCCESS", "summary": summary}
    
    async def handle_status(self, args) -> Dict[str, Any]:
        """시스템 상태 확인 명령을 처리합니다."""
        log_info("📊 시스템 상태 확인 중...")
        
        status = {
            "config": self.config.validate_all(),
            "database": False,
            "hcx_api": False,
            "email": self.config.email.enable_email,
            "docker": self.config.docker.is_docker,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 데이터베이스 연결 확인
            await self.batch_service.db_manager.check_connection()
            status["database"] = True
        except Exception as e:
            log_error(f"❌ 데이터베이스 연결 실패: {e}")
        
        # 상태 출력
        log_info(f"\n📋 시스템 상태:")
        log_info(f"  - 설정: {'✅' if status['config'] else '❌'}")
        log_info(f"  - 데이터베이스: {'✅' if status['database'] else '❌'}")
        log_info(f"  - 이메일: {'✅' if status['email'] else '⚠️'}")
        log_info(f"  - 도커: {'✅' if status['docker'] else '❌'}")
        log_info(f"  - 확인 시간: {status['timestamp']}")
        
        return status
    
    async def _send_batch_email(self, result: Dict[str, Any], args):
        """배치 처리 결과 이메일을 발송합니다."""
        try:
            log_info(f"\n📧 배치 처리 결과 이메일 발송 중...")
            
            target_date = args.date or f"{args.start_date}~{args.end_date}" if args.start_date else DateUtils.get_yesterday()
            status = "SUCCESS" if result.get('status') == 'SUCCESS' else "FAILED"
            
            stats = {
                'start_time': result.get('start_time', 'N/A'),
                'end_time': result.get('end_time', 'N/A'),
                'duration': result.get('duration', 'N/A'),
                'total_rows': result.get('total_rows', 0),
                'processed_count': result.get('processed_count', 0),
                'skipped_count': result.get('skipped_count', 0),
                'mode': '배치 처리'
            }
            
            # 엑셀 파일 생성 (성공한 경우)
            excel_file_path = None
            if status == "SUCCESS":
                try:
                    # 날짜 범위 처리
                    start_date = target_date
                    end_date = target_date
                    if "~" in target_date:
                        date_parts = target_date.split("~")
                        if len(date_parts) == 2:
                            start_date = date_parts[0].strip()
                            end_date = date_parts[1].strip()
                    
                    log_info(f"📊 배치 처리 결과 엑셀 보고서 생성 중: {start_date} ~ {end_date}")
                    excel_file_path, summary_stats = await self.excel_service.generate_report(start_date, end_date)
                    log_info(f"✅ 엑셀 보고서 생성 완료: {excel_file_path}")
                    
                except Exception as excel_error:
                    log_warning(f"⚠️ 엑셀 보고서 생성 실패, 첨부 없이 이메일 발송: {excel_error}")
            
            # 이메일 발송
            success = self.email_service.send_batch_notification(
                target_date=target_date,
                status=status,
                stats=stats,
                error_message=result.get('error_message') if status == "FAILED" else None,
                excel_file_path=excel_file_path
            )
            
            if success:
                log_info(f"📧 이메일 발송 완료!")
            else:
                log_error(f"📧 이메일 발송 실패!")
            
        except Exception as e:
            log_error(f"📧 이메일 발송 실패: {e}")
    
    async def _send_missing_email(self, result: Dict[str, Any], args, mode: str):
        """누락 데이터 처리 결과 이메일을 발송합니다."""
        try:
            log_info(f"\n📧 누락 데이터 {mode} 결과 이메일 발송 중...")
            
            target_date = f"{args.start_date}~{args.end_date}"
            status = "SUCCESS" if result.get('status') in ['SUCCESS', 'COMPLETED'] else "FAILED"
            
            stats = {
                'start_time': result.get('start_time', 'N/A'),
                'end_time': result.get('end_time', 'N/A'),
                'duration': result.get('duration', 'N/A'),
                'total_rows': result.get('total_rows', 0),
                'processed_count': result.get('processed_count', 0),
                'skipped_count': result.get('skipped_count', 0),
                'mode': f'누락 데이터 {mode}'
            }
            
            # 엑셀 파일 생성 (성공한 경우)
            excel_file_path = None
            if status == "SUCCESS":
                try:
                    log_info(f"📊 누락 데이터 처리 결과 엑셀 보고서 생성 중: {args.start_date} ~ {args.end_date}")
                    excel_file_path, summary_stats = await self.excel_service.generate_report(args.start_date, args.end_date)
                    log_info(f"✅ 엑셀 보고서 생성 완료: {excel_file_path}")
                    
                except Exception as excel_error:
                    log_warning(f"⚠️ 엑셀 보고서 생성 실패, 첨부 없이 이메일 발송: {excel_error}")
            
            # 이메일 발송
            success = self.email_service.send_batch_notification(
                target_date=target_date,
                status=status,
                stats=stats,
                error_message=result.get('error_message') if status == "FAILED" else None,
                excel_file_path=excel_file_path
            )
            
            if success:
                log_info(f"📧 이메일 발송 완료!")
            else:
                log_error(f"📧 이메일 발송 실패!")
            
        except Exception as e:
            log_error(f"📧 이메일 발송 실패: {e}")

    async def _send_report_email(self, result: Dict[str, Any], args):
        """보고서 생성 결과 이메일을 발송합니다."""
        try:
            from services.email_service import EmailService
            
            log_info(f"\n📧 보고서 이메일 발송 중...")
            
            email_service = EmailService(self.config.email)
            start_date = result.get('start_date')
            end_date = result.get('end_date')
            
            # 보고서 기간 설정
            if start_date == end_date:
                report_period = start_date
            else:
                report_period = f"{start_date} ~ {end_date}"
            
            # 이메일 발송
            success = email_service.send_excel_report(
                result.get('excel_filename'),
                report_period
            )
            
            if success:
                log_info(f"📧 보고서 이메일 발송 완료!")
            else:
                log_info(f"📧 보고서 이메일 발송 실패!")
                
        except Exception as e:
            log_error(f"📧 보고서 이메일 발송 실패: {e}")


async def main():
    """메인 실행 함수"""
    cli = CLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # 서비스 초기화
        await cli.init_services()
        
        # 명령 처리
        if args.command == 'batch':
            if args.dry_run:
                log_info("DRY RUN: 실제 처리 없이 계획만 출력합니다.")
                log_info(f"  - 날짜: {args.date or f'{args.start_date}~{args.end_date}' if args.start_date else DateUtils.get_yesterday()}")
                log_info(f"  - 병렬 처리: {args.parallel}")
                log_info(f"  - 이메일 발송: {args.email}")
                return
            
            result = await cli.handle_batch(args)
            
        elif args.command == 'missing':
            result = await cli.handle_missing(args)
            
        elif args.command == 'report':
            result = await cli.handle_report(args)
            
        elif args.command == 'config':
            result = cli.handle_config(args)
            
        elif args.command == 'status':
            result = await cli.handle_status(args)
        
        # 결과 출력
        if result.get('status') == 'SUCCESS':
            log_info(f"\n🎉 작업 완료!")
        elif result.get('status') == 'FAILED':
            log_info(f"\n❌ 작업 실패!")
            if result.get('error'):
                log_error(f"오류: {result['error']}")
        
    except BatchProcessError as e:
        log_error(f"❌ 배치 처리 오류: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log_warning("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        log_error(f"❌ 예상치 못한 오류: {e}")
        import traceback
        log_error(f"상세 오류:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 