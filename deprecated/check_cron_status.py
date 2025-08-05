#!/usr/bin/env python3
"""
Cron 실행 상태 체크 스크립트
"""

import os
import subprocess
import datetime
from pathlib import Path


def run_command(cmd):
    """Shell 명령어 실행"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def check_cron_status():
    """Cron 실행 상태 체크"""
    print("=" * 60)
    print("🕐 CRON 실행 상태 체크")
    print("=" * 60)
    
    # 1. Cron 프로세스 확인
    print("\n1. 📋 Cron 프로세스 상태")
    print("-" * 40)
    
    success, output, error = run_command("pidof cron")
    if success and output:
        print(f"✅ Cron 데몬 실행 중 (PID: {output})")
    else:
        print("❌ Cron 데몬이 실행되지 않고 있습니다!")
        return False
    
    success, output, error = run_command("service cron status")
    if success:
        print(f"✅ Cron 서비스 상태: 정상")
    else:
        print(f"⚠️ Cron 서비스 상태 확인 실패: {error}")
    
    # 2. Crontab 설정 확인
    print("\n2. ⚙️ Crontab 설정")
    print("-" * 40)
    
    success, output, error = run_command("crontab -l")
    if success and output:
        print("✅ Crontab 설정이 존재합니다:")
        for line in output.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"   📋 {line}")
    else:
        print("❌ Crontab 설정이 없습니다!")
        return False
    
    # 3. 현재 시간과 다음 실행 시간
    print("\n3. 🕒 시간 정보")
    print("-" * 40)
    
    now = datetime.datetime.now()
    print(f"⏰ 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Cron은 매일 01:00에 실행되도록 설정됨
    next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)
    if now.hour >= 1:  # 오늘 이미 01:00이 지났다면 내일
        next_run += datetime.timedelta(days=1)
    
    print(f"⏭️ 다음 실행 예정: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    time_diff = next_run - now
    hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    print(f"⌛ 남은 시간: {hours}시간 {minutes}분")
    
    # 4. 로그 파일 확인
    print("\n4. 📁 로그 파일 상태")
    print("-" * 40)
    
    log_dir = Path("/app/logs")
    if log_dir.exists():
        print(f"✅ 로그 디렉토리 존재: {log_dir}")
        
        # 최근 로그 파일들 확인
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print(f"📄 발견된 로그 파일 수: {len(log_files)}")
            for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                size_mb = log_file.stat().st_size / (1024 * 1024)
                print(f"   📋 {log_file.name} - {mtime.strftime('%Y-%m-%d %H:%M')} ({size_mb:.2f}MB)")
        else:
            print("⚠️ 로그 파일이 없습니다.")
    else:
        print(f"❌ 로그 디렉토리가 없습니다: {log_dir}")
    
    # 5. Cron 로그 확인
    print("\n5. 📋 Cron 시스템 로그")
    print("-" * 40)
    
    cron_log = Path("/var/log/cron.log")
    if cron_log.exists():
        file_size = cron_log.stat().st_size
        if file_size > 0:
            print(f"✅ Cron 로그 존재: {cron_log} ({file_size} bytes)")
            
            # 최근 몇 줄 확인
            success, output, error = run_command(f"tail -5 {cron_log}")
            if success and output:
                print("📋 최근 Cron 로그:")
                for line in output.split('\n'):
                    if line.strip():
                        print(f"   {line}")
            else:
                print("⚠️ Cron 로그 내용을 읽을 수 없습니다.")
        else:
            print(f"⚠️ Cron 로그 파일이 비어있습니다: {cron_log}")
    else:
        print("❌ Cron 로그 파일이 없습니다!")
    
    # 6. 오늘 예상 배치 로그 파일
    print("\n6. 🎯 오늘 배치 로그 예상 경로")
    print("-" * 40)
    
    today = datetime.datetime.now().strftime('%Y%m%d')
    expected_log = f"/app/logs/batch_{today}.log"
    
    print(f"📋 예상 로그 파일: {expected_log}")
    
    if Path(expected_log).exists():
        file_size = Path(expected_log).stat().st_size
        mtime = datetime.datetime.fromtimestamp(Path(expected_log).stat().st_mtime)
        print(f"✅ 오늘 배치 로그 존재 ({file_size} bytes, 최종 수정: {mtime.strftime('%H:%M:%S')})")
    else:
        print("⚠️ 오늘 배치 로그가 아직 생성되지 않았습니다 (정상 - 01:00에 생성됨)")
    
    # 7. 권한 확인
    print("\n7. 🔐 권한 확인")
    print("-" * 40)
    
    success, output, error = run_command("whoami")
    if success:
        print(f"👤 현재 사용자: {output}")
    
    success, output, error = run_command("ls -la /etc/cron.d/")
    if success and 'batch' in output:
        print("✅ Cron 작업 파일이 /etc/cron.d/에 존재합니다")
    else:
        print("⚠️ /etc/cron.d/에 batch 관련 파일을 찾을 수 없습니다")
    
    print("\n" + "=" * 60)
    print("✅ Cron 상태 체크 완료!")
    print("=" * 60)
    
    return True


def main():
    """메인 함수"""
    try:
        check_cron_status()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    return True


if __name__ == "__main__":
    main() 