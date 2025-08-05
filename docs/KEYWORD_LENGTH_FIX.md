# 🔧 키워드 길이 문제 해결 가이드

## 📋 문제 상황

```
⚠️ 개별 INSERT 실패: (pymysql.err.DataError) (1406, "Data too long for column 'keyword' at row 1")
```

**원인**: HCX API에서 반환하는 키워드가 원본 질문 전체(920자 이상)를 그대로 반환하여 데이터베이스의 `keyword` 컬럼 크기(VARCHAR(100))를 초과

---

## ✅ 해결 방법

### 1️⃣ **HCX 서비스 개선** (`services/hcx_service.py`)

#### 🔧 키워드 검증 및 정제
- `_clean_and_validate_keyword()` 함수 추가
- 키워드 길이 100자 초과 시 의미있는 키워드 추출
- 원본 질문과 동일한 경우 핵심 키워드만 추출

#### 🔧 Fallback 분류 개선
- `_extract_meaningful_keyword()` 함수 추가
- 교육 관련 키워드 매핑 확장
- 의미있는 단어 우선 추출

### 2️⃣ **배치 서비스 강화** (`services/batch_service.py`)

#### 🔧 키워드 길이 제한
```python
if len(keyword) > 100:  # VARCHAR(100) 가정
    print(f"⚠️ 키워드 길이 초과 ({len(keyword)}자), 요약으로 대체")
    keyword = input_text[:95] + "..." if len(input_text) > 95 else input_text
    if len(keyword) > 100:
        keyword = keyword[:97] + "..."
```

#### 🔧 키워드 보완 로직
```python
if not keyword or keyword.strip() == "" or keyword.strip() == "기타":
    meaningful_keyword = self._extract_simple_keyword(input_text)
    keyword = meaningful_keyword if meaningful_keyword else "기타"
```

#### 🔧 간단 키워드 추출
- `_extract_simple_keyword()` 함수 추가
- 교육 관련 핵심 키워드 우선 매핑
- 의미있는 첫 번째 단어 추출

### 3️⃣ **데이터베이스 안전장치** (`core/database.py`)

#### 🔧 INSERT 전 최종 검증
```python
if 'keyword' in params:
    keyword = params['keyword']
    if len(str(keyword)) > 100:
        print(f"⚠️ 키워드 길이 초과, 자르기: {len(str(keyword))}자 -> 100자")
        params['keyword'] = str(keyword)[:98] + "..."
```

---

## 🧪 테스트 방법

### 테스트 스크립트 실행
```bash
python test_keyword_length_fix.py
```

### 실제 배치 실행 테스트
```bash
# 문제가 되었던 데이터로 테스트
python main_batch.py --target-date 2025-06-16

# 또는 Docker에서
docker-compose exec keyword-batch python main_batch.py --target-date 2025-06-16
```

---

## 📊 개선 효과

| 이전 | 이후 |
|------|------|
| ❌ 긴 키워드로 INSERT 실패 | ✅ 적절한 길이로 자동 조정 |
| ❌ 원본 질문 전체가 키워드 | ✅ 의미있는 핵심 키워드 추출 |
| ❌ 빈 키워드 처리 불가 | ✅ 자동 키워드 보완 |
| ❌ 오류 시 배치 중단 | ✅ 개별 실패만 기록, 배치 계속 |

---

## 🔍 추가 모니터링

### 로그 확인 포인트
1. **키워드 길이 초과 경고**
   ```
   ⚠️ 키워드 길이 초과 (920자), 요약으로 대체: 수업 중 '공기를...
   ```

2. **키워드 보완 로그**
   ```
   🔄 키워드 보완: '수업'
   ```

3. **최종 안전장치 작동**
   ```
   ⚠️ 키워드 길이 초과, 자르기: 150자 -> 100자
   ```

### 성공 지표
- `📊 배치 INSERT 결과: X개 성공, 0개 실패`
- 더 이상 `Data too long for column 'keyword'` 오류 없음

---

## 🚀 다음 단계

### 1. 데이터베이스 스키마 최적화 고려
```sql
-- 필요 시 키워드 컬럼 크기 확장
ALTER TABLE admin_chat_keywords 
MODIFY COLUMN keyword VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. HCX API 프롬프트 최적화
- HCX API에서 더 적절한 키워드를 추출하도록 프롬프트 개선
- Function calling 스키마에서 키워드 길이 제한 명시

### 3. 정기 모니터링
- 키워드 길이 분포 분석
- 추출 품질 검증
- 성능 영향 모니터링

---

<div align="center">

**✅ 키워드 길이 문제 해결 완료**  
*이제 안전하게 배치 처리를 수행할 수 있습니다.*

</div> 