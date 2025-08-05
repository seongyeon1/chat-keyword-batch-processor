# Deprecated Files

이 폴더는 새로운 `cli.py` 기반 시스템에서 더 이상 사용하지 않는 레거시 파일들을 모아둔 곳입니다.

## 📁 이동된 파일들

### 레거시 메인 스크립트
- `main_batch.py` - 기존 배치 처리 메인 스크립트 (→ `cli.py batch` 로 대체)
- `main_report.py` - 기존 보고서 생성 스크립트 (→ `cli.py report` 로 대체)

### 레거시 고급 스크립트들
- `run_advanced_batch.py` - 고급 배치 처리 스크립트 (→ `cli.py` 통합 기능으로 대체)
- `run_missing_data_advanced.py` - 누락 데이터 처리 스크립트 (→ `cli.py missing` 로 대체)

### 디버그 및 모니터링 스크립트들
- `debug_check.py` - 데이터베이스 적재 상황 디버그 스크립트
- `debug_daily_stats.py` - 일별 통계 비교 디버그 스크립트
- `check_cron_status.py` - 크론 작업 상태 확인 스크립트

### 배포 및 실행 스크립트들
- `run_batch.sh` - 쉘 배치 실행 스크립트
- `deploy.sh` - 배포 스크립트
- `deploy_en.ps1` - PowerShell 배포 스크립트

### 요구사항 파일들
- `requirements_step3.txt` - 구버전 요구사항 파일
- `requirements_fixed.txt` - 수정된 요구사항 파일 (→ `requirements.txt` 사용)

### 폴더들
- `tests/` - 기존 테스트 파일들
- `legacy/` - 기존 레거시 코드들

## 🚀 새로운 CLI 시스템 사용법

기존 레거시 파일들 대신 다음과 같이 사용하세요:

### 기본 배치 처리
```bash
# 기존: python main_batch.py
python cli.py batch

# 기존: python main_batch.py --target-date 2024-03-15
python cli.py batch -d 2024-03-15

# 기존: python run_advanced_batch.py --start-date 2024-03-01 --end-date 2024-03-31
python cli.py batch -s 2024-03-01 -e 2024-03-31 --parallel
```

### 누락 데이터 처리
```bash
# 기존: python run_missing_data_advanced.py
python cli.py missing auto -s 2024-03-01 -e 2024-03-31

# 누락 데이터 확인만
python cli.py missing check -s 2024-03-01 -e 2024-03-31
```

### 보고서 생성
```bash
# 기존: python main_report.py yesterday
python cli.py report -d yesterday --email

# 기간별 보고서
python cli.py report -s 2024-03-01 -e 2024-03-31
```

### 시스템 상태 확인
```bash
# 기존: python debug_check.py (부분적으로)
python cli.py status

# 설정 검증
python cli.py config validate
```

## ⚠️ 주의사항

1. **이 폴더의 파일들은 더 이상 유지보수되지 않습니다.**
2. **새로운 기능은 `cli.py`에서만 추가됩니다.**
3. **기존 파일들을 사용하려면 개별적으로 의존성을 확인해야 합니다.**

## 🗑️ 삭제 예정

이 폴더의 파일들은 충분한 테스트 기간 후 삭제될 예정입니다. 
필요한 기능이 있다면 `cli.py`에 통합하거나 별도로 백업하시기 바랍니다. 