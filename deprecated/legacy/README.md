# 레거시 파일들

이 폴더에는 v2.0 리팩토링 이전의 레거시 파일들이 보관되어 있습니다.

## 📁 파일 목록

### 스크립트 파일들
- `run_missing_check.py` - 누락 데이터 확인 (구버전)
- `run_missing_data_advanced.py` - 고급 누락 데이터 처리 (구버전)
- `manual_run.sh` - 수동 실행 스크립트 (구버전)
- `run_batch_background.sh` - 백그라운드 배치 실행 (구버전)
- `run_batch_background.ps1` - PowerShell 배치 실행 (구버전)
- `legacy_compatibility.py` - 레거시 호환성 모듈

## ⚠️ 주의사항

- 이 파일들은 **더 이상 사용되지 않습니다**
- v2.0의 새로운 CLI 인터페이스를 사용하세요
- 참고용으로만 보관되며, 삭제해도 무방합니다

## 🆕 새로운 방법

대신 다음과 같이 사용하세요:

```bash
# 새로운 CLI 사용
python run.py cli batch --parallel --email
python run.py cli missing auto -s 2024-03-01 -e 2024-03-31
python run.py status

# 또는 직접 CLI 사용
python cli.py batch --workers 8 --email
python cli.py missing check -s 2024-03-01 -e 2024-03-31
``` 