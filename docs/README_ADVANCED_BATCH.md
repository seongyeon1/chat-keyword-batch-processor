# 통합 배치 처리 시스템

프로시저 대신 쿼리 모듈을 사용하는 새로운 배치 처리 시스템입니다.

## 주요 특징

- 🚀 **프로시저 제거**: 모든 SQL 쿼리를 `queries/batch_queries.py`에서 관리
- 📊 **다양한 실행 모드**: 기본 배치, 누락 데이터 확인/처리, 통합 처리
- 🔧 **개선된 누락 데이터 처리**: 정확한 누락 데이터 식별 및 처리
- 💾 **메모리 효율적**: 스트리밍 방식으로 대용량 데이터 처리
- 🎯 **처리 제한**: 누락 데이터 처리 시 개수 제한 기능

## 파일 구조

```
batch-keywords/
├── queries/
│   └── batch_queries.py          # 모든 SQL 쿼리 관리
├── services/
│   └── batch_service.py          # 업데이트된 배치 서비스
├── run_advanced_batch.py         # 새로운 통합 실행 스크립트
└── README_ADVANCED_BATCH.md      # 이 파일
```

## 사용법

### 1. 기본 배치 처리만 실행

```bash
python run_advanced_batch.py basic 2025-06-11 2025-06-19
```

### 2. 누락 데이터 확인만 실행

```bash
python run_advanced_batch.py check 2025-06-11 2025-06-19
```

### 3. 누락 데이터 처리만 실행

```bash
# 전체 누락 데이터 처리
python run_advanced_batch.py missing 2025-06-11 2025-06-19

# 처리 개수 제한 (예: 106개만)
python run_advanced_batch.py missing 2025-06-11 2025-06-19 --limit 106
```

### 4. 완전한 통합 처리 (권장)

```bash
# 기본 배치 + 누락 데이터 처리 전체 실행
python run_advanced_batch.py complete 2025-06-11 2025-06-19

# 누락 데이터 처리 개수 제한
python run_advanced_batch.py complete 2025-06-11 2025-06-19 --limit 500
```

## 실행 모드 설명

### `basic` 모드
- 기본 배치 처리만 실행
- 새로운 채팅 데이터를 HCX API로 분류하여 키워드 추출
- 날짜별 병렬 처리로 빠른 성능

### `check` 모드
- 누락된 데이터만 확인하고 처리하지 않음
- 전체 채팅 데이터 대비 처리된 데이터 통계 제공
- 날짜별 누락 현황 상세 보고

### `missing` 모드
- 누락된 데이터만 처리
- `--limit` 옵션으로 처리 개수 제한 가능
- 처리 후 자동 검증 수행

### `complete` 모드 (권장)
- 기본 배치 → 누락 확인 → 누락 처리의 전체 워크플로우
- 완전한 데이터 처리를 위한 원스톱 솔루션
- 자동으로 각 단계 진행 (사용자 확인 생략)

## 주요 개선사항

### 1. 프로시저 제거
기존의 MySQL 프로시저 대신 Python에서 직접 쿼리 관리:

```python
# 기존 (프로시저 호출)
await self.db_manager.call_procedure("get_unique_chattings_by_date", params)

# 개선 (쿼리 모듈 사용)
query = self.queries.get_unique_chattings_by_date(start_date, end_date)
result = await self.db_manager.execute_query(query)
```

### 2. 제공된 쿼리 적용
사용자가 제공한 CTE 쿼리를 `BatchQueries.get_unique_chattings_by_date()`에 적용:

```sql
WITH counted_chats AS (
    SELECT 
        chatting_pk,
        input_text,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY input_text ORDER BY created_at DESC) AS rn,
        COUNT(*) OVER (PARTITION BY input_text) AS total_count
    FROM chattings
    WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
)
SELECT 
    input_text,
    total_count,
    DATE(created_at) AS created_at
FROM counted_chats
WHERE rn = 1
ORDER BY total_count DESC, created_at ASC
```

### 3. 정확한 누락 데이터 처리
기존 `admin_chat_keywords` 테이블과 실시간 비교하여 정확한 누락 데이터 식별:

```sql
SELECT 
    DATE(c.created_at) AS missing_date,
    c.input_text,
    COUNT(*) AS missing_count
FROM chattings c
LEFT JOIN (
    SELECT DISTINCT query_text, DATE(created_at) AS dt
    FROM admin_chat_keywords
    WHERE DATE(created_at) BETWEEN '{start_date}' AND '{end_date}'
) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
WHERE t.query_text IS NULL
  AND c.created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
```

## 실행 예시

### 단계별 실행 (개발/테스트용)

```bash
# 1단계: 기본 배치 처리
python run_advanced_batch.py basic 2025-06-11 2025-06-14

# 2단계: 누락 데이터 확인
python run_advanced_batch.py check 2025-06-11 2025-06-14

# 3단계: 누락 데이터 처리 (100개 제한)
python run_advanced_batch.py missing 2025-06-11 2025-06-14 --limit 100
```

### 원스톱 실행 (운영용 권장)

```bash
# 모든 과정을 자동으로 처리
python run_advanced_batch.py complete 2025-06-11 2025-06-14
```

## 출력 예시

### 완전한 통합 처리 실행 시:

```
🚀 완전한 배치 처리 시작
================================================================================
📅 처리 기간: 2025-06-11 ~ 2025-06-14

STEP 1: 기본 배치 처리
----------------------------------------
📅 기간별 배치 처리 시작: 2025-06-11 ~ 2025-06-14
📋 처리할 날짜: 4일
🚀 날짜별 병렬 처리 시작: 4개 날짜
✅ 2025-06-11 완료: 145개 처리
✅ 2025-06-12 완료: 167개 처리
✅ 2025-06-13 완료: 134개 처리
✅ 2025-06-14 완료: 98개 처리

================================================================================

STEP 2: 누락 데이터 확인
----------------------------------------
🔍 누락 데이터 확인 중: 2025-06-11 ~ 2025-06-14
📊 통계 정보:
   - 전체 고유 질문: 620개
   - 기존 처리된 질문: 544개
   - 누락된 질문: 76개
   - 처리율: 87.7%

================================================================================

STEP 3: 누락 데이터 처리
----------------------------------------
🔧 누락 데이터 처리 시작: 2025-06-11 ~ 2025-06-14
📊 처리 결과: 76개 처리, 0개 중복 스킵
✅ 검증 완료: 모든 누락 데이터가 처리되었습니다.

================================================================================
🎉 완전한 배치 처리 완료!
================================================================================
📊 최종 요약:
   [기본 배치]
   - 처리된 데이터: 544개
   - 스킵된 데이터: 12개
   - 처리 시간: 8분 23초

   [누락 데이터]
   - 발견된 누락 데이터: 76개
   - 처리된 누락 데이터: 76개
   - 스킵된 누락 데이터: 0개

   [전체 합계]
   - 총 처리된 데이터: 620개
```

## 주의사항

1. **데이터베이스 연결**: `.env` 파일의 데이터베이스 설정이 올바른지 확인
2. **HCX API 키**: HCX API 키가 유효한지 확인
3. **처리 시간**: 대용량 데이터의 경우 처리 시간이 오래 걸릴 수 있음
4. **메모리 사용량**: 스트리밍 방식으로 메모리 효율적이지만 동시 처리 수를 조절할 수 있음

## 트러블슈팅

### 자주 발생하는 문제

1. **프로시저 오류**: 이제 프로시저를 사용하지 않으므로 관련 오류 없음
2. **메모리 부족**: 배치 크기를 줄이거나 `--limit` 옵션 사용
3. **네트워크 시간 초과**: HCX API 호출 시 재시도 로직 내장
4. **중복 데이터**: 자동 중복 체크로 중복 삽입 방지

### 로그 확인

상세한 로그는 콘솔에 실시간으로 출력되며, 각 단계별 진행 상황을 확인할 수 있습니다.

---

## 기존 코드와의 차이점

| 항목 | 기존 코드 | 새로운 코드 |
|------|-----------|-------------|
| SQL 관리 | 프로시저 호출 | 쿼리 모듈 (`BatchQueries`) |
| 누락 데이터 처리 | 별도 스크립트 | 통합 모드 지원 |
| 쿼리 방식 | 사용자 제공 쿼리 미적용 | 사용자 제공 CTE 쿼리 적용 |
| 실행 방식 | 단일 기능 스크립트들 | 다중 모드 통합 스크립트 |
| 메모리 관리 | 일괄 로딩 | 스트리밍 처리 |

이제 더 효율적이고 유지보수가 쉬운 배치 처리 시스템을 사용할 수 있습니다! 