#!/usr/bin/env python3
"""
간편한 실행 스크립트 - 모든 기능에 쉽게 접근할 수 있는 통합 인터페이스
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def main():
    """메인 실행 함수"""
    
    # 인수가 없으면 도움말 표시
    if len(sys.argv) == 1:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['help', '--help', '-h']:
        print_help()
    elif command in ['cli', 'new']:
        # 새로운 CLI 인터페이스 실행
        run_cli()
    elif command in ['batch', 'legacy']:
        # 레거시 배치 처리 실행
        run_legacy_batch()
    elif command in ['report']:
        # 보고서 생성 실행
        run_report()
    elif command in ['status', 'check']:
        # 시스템 상태 확인
        run_status_check()
    elif command in ['config', 'validate']:
        # 설정 검증
        run_config_validation()
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("사용법: python run.py help")

def print_help():
    """도움말을 출력합니다."""
    print("""
🚀 개선된 채팅 키워드 배치 처리 시스템

== 사용법 ==
python run.py <명령어> [옵션...]

== 사용 가능한 명령어 ==
cli, new        - 새로운 CLI 인터페이스 사용 (권장)
batch, legacy   - 레거시 배치 처리 인터페이스
report          - 보고서 생성
status, check   - 시스템 상태 확인
config, validate - 설정 검증
help            - 이 도움말 표시

== 새로운 CLI 사용 예시 ==
python run.py cli batch                                  # 어제 날짜 처리
python run.py cli batch -d 2024-03-15 --email          # 특정 날짜 + 이메일
python run.py cli batch -s 2024-03-01 -e 2024-03-31 --parallel  # 기간별 병렬 처리
python run.py cli missing check -s 2024-03-01 -e 2024-03-31     # 누락 데이터 확인
python run.py cli report -d yesterday --email           # 어제 보고서 + 이메일
python run.py cli report -s 2024-03-01 -e 2024-03-31   # 기간별 보고서
python run.py cli config validate                       # 설정 검증
python run.py cli status                                # 시스템 상태

== 레거시 사용 예시 ==
python run.py batch                                     # 어제 날짜 처리
python run.py batch --target-date 2024-03-15 --email   # 특정 날짜 + 이메일
python run.py report yesterday                          # 어제 보고서
python run.py report last-month --email                # 지난달 보고서 + 이메일

== 빠른 상태 확인 ==
python run.py status                                    # 시스템 전체 상태
python run.py config                                    # 설정만 검증

== 도커 환경에서 ==
docker-compose exec keyword-batch python run.py cli batch --parallel --email
docker-compose exec keyword-batch python run.py cli report -d yesterday --email
docker-compose exec keyword-batch python run.py status
    """)

def run_cli():
    """새로운 CLI 인터페이스를 실행합니다."""
    try:
        # cli.py의 명령어 실행
        import subprocess
        
        # 인수에서 'cli' 제거하고 나머지를 cli.py에 전달
        cli_args = sys.argv[2:] if len(sys.argv) > 2 else []
        
        cmd = [sys.executable, str(project_root / 'cli.py')] + cli_args
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"❌ CLI 실행 오류: {e}")
        sys.exit(1)

def run_legacy_batch():
    """레거시 배치 처리를 실행합니다."""
    try:
        import subprocess
        
        # 인수에서 'batch' 제거하고 나머지를 main_batch.py에 전달
        batch_args = sys.argv[2:] if len(sys.argv) > 2 else []
        
        cmd = [sys.executable, str(project_root / 'main_batch.py')] + batch_args
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"❌ 레거시 배치 실행 오류: {e}")
        sys.exit(1)

def run_report():
    """보고서 생성을 실행합니다."""
    try:
        import subprocess
        
        # 인수에서 'report' 제거하고 나머지를 main_report.py에 전달
        report_args = sys.argv[2:] if len(sys.argv) > 2 else []
        
        cmd = [sys.executable, str(project_root / 'main_report.py')] + report_args
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"❌ 보고서 생성 오류: {e}")
        sys.exit(1)

def run_status_check():
    """시스템 상태를 확인합니다."""
    try:
        # 새로운 CLI의 status 명령 사용
        import subprocess
        
        cmd = [sys.executable, str(project_root / 'cli.py'), 'status']
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"❌ 상태 확인 오류: {e}")
        sys.exit(1)

def run_config_validation():
    """설정 검증을 실행합니다."""
    try:
        # 새로운 CLI의 config validate 명령 사용
        import subprocess
        
        cmd = [sys.executable, str(project_root / 'cli.py'), 'config', 'validate']
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"❌ 설정 검증 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 