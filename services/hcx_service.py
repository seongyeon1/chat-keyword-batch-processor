"""
HCX API 서비스 모듈 - HCX API를 통한 질문 분류 처리를 담당합니다.
"""

import json
import requests
import asyncio
import time
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.config import HCXConfig
from utils.logger import get_logger, log_info, log_warning, log_error, log_debug

# HCX API 예외 클래스들
class HCXError(Exception):
    """HCX API 기본 예외"""
    pass

class HCXAPIError(HCXError):
    """HCX API 오류"""
    pass

class HCXTooManyRequestError(HCXError):
    """HCX API 요청 한도 초과"""
    pass

class HCXService:
    """HCX API 서비스 클래스"""
    
    def __init__(self, config: HCXConfig):
        self.config = config
        self.base_url = f"https://clovastudio.stream.ntruss.com/{config.app_type}/v3/chat-completions/{config.model}"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        self.tools = self._get_classification_tools()
        
        # 🚀 Rate Limiting 설정
        self.last_request_time = 0
        self.min_request_interval = config.min_request_interval  # 설정에서 가져오기
        self.request_count = 0
        self.request_window_start = time.time()
        self.max_requests_per_minute = config.max_requests_per_minute  # 설정에서 가져오기
        
        # 🔄 재시도 설정
        self.max_retries = config.max_retries  # 설정에서 가져오기
        self.base_delay = config.base_delay  # 설정에서 가져오기
        self.max_delay = config.max_delay  # 설정에서 가져오기
    
    def _get_classification_tools(self) -> List[Dict[str, Any]]:
        """분류를 위한 도구 정의를 반환합니다."""
        return [{
            "type": "function",
            "function": {
                "name": "classify_education_question",
                "description": "교육 관련 질문을 키워드 기준으로 분석하고 관련된 11가지 카테고리 중 하나 이상으로 분류합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "사용자가 입력한 원본 질문"
                        },
                        "keywords": {
                            "type": "array",
                            "description": "사용자가 입력한 원본 질문에서 구문 및 키워드 추출"
                        },
                        "keywords_with_categories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "keyword": {
                                        "type": "string",
                                        "description": "질문 내에서 감지된 주요 키워드"
                                    },
                                    "categories": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "학교폭력",
                                                "교권보호 (교육활동 보호)",
                                                "학생 생활",
                                                "평가(성적) 관련",
                                                "전학, 편입",
                                                "입학 관련",
                                                "검정고시",
                                                "교원 임용고시 관련",
                                                "제 증명 관련",
                                                "정보공개",
                                                "기타"
                                            ]
                                        },
                                        "description": "해당 키워드와 연관된 카테고리 목록"
                                    }
                                },
                                "required": ["keyword", "categories"]
                            },
                            "description": "질문 내에서 추출된 키워드와 해당 키워드별 분류된 카테고리 목록"
                        }
                    },
                    "required": ["question", "keywords", "keywords_with_categories"]
                }
            }
        }]
    
    async def _rate_limit_check(self):
        """Rate limiting 체크 및 대기"""
        current_time = time.time()
        
        # 🕐 분 단위 요청 수 체크
        if current_time - self.request_window_start >= 60:
            # 새로운 분 시작
            self.request_count = 0
            self.request_window_start = current_time
        
        # 요청 한도 체크
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.request_window_start)
            if wait_time > 0:
                log_info(f"⏰ Rate limit 도달, {wait_time:.1f}초 대기 중...")
                await asyncio.sleep(wait_time)
                # 대기 후 카운터 리셋
                self.request_count = 0
                self.request_window_start = time.time()
        
        # 🚦 최소 요청 간격 체크
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            log_info(f"⏱️ 요청 간격 조절: {wait_time:.1f}초 대기")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type(HCXTooManyRequestError)
    )
    async def chat_completion(self, messages: List[Dict], maxTokens: int = None, temperature: float = None) -> Dict[str, Any]:
        """HCX API 채팅 완료 호출 - Rate limiting 적용"""
        await self._rate_limit_check()
        
        data = {
            "messages": messages,
            "maxTokens": maxTokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "topP": 0.8,
            "topK": 0,
            "repeatPenalty": 1.0
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                log_info(f"📈 API 요청 한도 초과 감지, 재시도 대기 중...")
                raise HCXTooManyRequestError("API 요청 한도 초과")
            else:
                raise HCXError(f"API 호출 실패: {response.text}", response.status_code)
                
        except requests.exceptions.RequestException as e:
            raise HCXError(f"네트워크 오류: {e}")
    
    def fn_calling(self, query: str) -> Dict[str, Any]:
        """Function calling을 사용한 질문 분류 - Rate limiting 적용"""
        import os
        import requests
        
        # API 키 확인
        API_KEY = os.getenv("HCX_CHAT_API_KEY")
        if not API_KEY:
            raise HCXAPIError("HCX_CHAT_API_KEY 환경변수가 설정되지 않았습니다.")
        
        if not API_KEY.startswith("nv-"):
            log_warning(f"⚠️ API 키 형식 주의: 'nv-'로 시작해야 합니다. 현재: {API_KEY[:10]}...")
        
        # 🚦 동기 버전 Rate limiting
        current_time = time.time()
        
        # 분 단위 요청 수 체크
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # 요청 한도 체크
        if self.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.request_window_start)
            if wait_time > 0:
                log_info(f"⏰ Rate limit 도달, {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = time.time()
        
        # 최소 요청 간격 체크
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            log_info(f"⏱️ 요청 간격 조절: {wait_time:.1f}초 대기")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        url = f"https://clovastudio.stream.ntruss.com/{self.config.app_type}/v3/chat-completions/{self.config.model}"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "messages": [
                {"role": "user", "content": query}
            ],
            "tools": self.tools,
            "toolChoice": "auto"
        }
        
        # 🔄 수동 재시도 로직 (tenacity 대신)
        for attempt in range(self.max_retries):
            try:
                log_info(f"🔄 API 호출 시도 {attempt + 1}/{self.max_retries}")
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                log_info(f"📡 HTTP 응답: 상태 코드 {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    log_info(f"✅ API 호출 성공")
                    return result
                    
                elif response.status_code == 401:
                    log_info(f"🔑 API 키 인증 실패!")
                    log_info(f"   - 현재 API 키: {API_KEY}")
                    log_info(f"   - 응답 메시지: {response.text}")
                    raise HCXAPIError(f"API 키 인증 실패: {response.text}")
                
                elif response.status_code == 429:
                    # 🚨 Rate limit 처리
                    retry_after = response.headers.get('Retry-After', self.base_delay * (2 ** attempt))
                    try:
                        retry_after = float(retry_after)
                    except:
                        retry_after = self.base_delay * (2 ** attempt)
                    
                    retry_after = min(retry_after, self.max_delay)
                    
                    if attempt < self.max_retries - 1:
                        log_info(f"📈 요청 한도 초과 (시도 {attempt + 1}/{self.max_retries})")
                        log_info(f"⏰ {retry_after:.1f}초 후 재시도...")
                        time.sleep(retry_after)
                        continue
                    else:
                        log_info(f"❌ 최대 재시도 횟수 초과")
                        raise HCXTooManyRequestError("API 요청 한도 초과 - 최대 재시도 초과")
                
                else:
                    log_info(f"❌ HTTP 오류: {response.status_code}")
                    log_info(f"   - 응답 내용: {response.text}")
                    if attempt < self.max_retries - 1:
                        wait_time = self.base_delay * (2 ** attempt)
                        log_info(f"⏰ {wait_time:.1f}초 후 재시도...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise HCXAPIError(f"HTTP {response.status_code}: {response.text}")
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    log_info(f"⏰ 타임아웃, {wait_time:.1f}초 후 재시도...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HCXAPIError("요청 타임아웃 - 최대 재시도 초과")
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    log_info(f"🌐 네트워크 오류, {wait_time:.1f}초 후 재시도: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HCXAPIError(f"네트워크 오류: {e}")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)
                    log_info(f"💥 예상치 못한 오류, {wait_time:.1f}초 후 재시도: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HCXAPIError(f"예상치 못한 오류: {e}")
        
        # 모든 재시도 실패
        raise HCXAPIError("모든 재시도 실패")
    
    def classify_education_question(self, query: str) -> List[Dict[str, Any]]:
        """
        교육 관련 질문을 분류하여 키워드-카테고리 매핑을 반환합니다.
        
        Args:
            query (str): 분류할 질문
            
        Returns:
            List[Dict[str, Any]]: 키워드-카테고리 매핑 리스트
        """
        try:
            # 먼저 Function Calling 시도
            result = self.fn_calling(query)
            
            # 응답 처리 로직은 기존과 동일
            tool_calls = result.get("result", {}).get("message", {}).get("toolCalls", [])
            
            if not tool_calls:
                log_warning(f"⚠️ Function calling 응답 없음, 일반 분류로 전환: {query}")
                return self._fallback_classification(query)
            
            log_info(f"✅ Function calling 성공, tool_calls 개수: {len(tool_calls)}")
            
            arguments = tool_calls[0]["function"]["arguments"]
            
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as e:
                    log_warning(f"⚠️ JSON 파싱 실패: {e}, 일반 분류 시도: {query}")
                    return self._fallback_classification(query)
            
            keyword_category_list = arguments.get("keywords_with_categories", [])
            
            if not keyword_category_list:
                log_warning(f"⚠️ 키워드 카테고리 없음, 일반 분류 시도: {query}")
                return self._fallback_classification(query)
            
            # 데이터 정제
            cleaned_list = []
            for item in keyword_category_list:
                if not isinstance(item, dict):
                    continue
                
                keyword = item.get("keyword", "").strip()
                categories = item.get("categories", [])
                
                if not keyword:
                    continue
                
                # 키워드 길이 및 품질 검증
                keyword = self._clean_and_validate_keyword(keyword, query)
                
                # categories 정규화
                if isinstance(categories, str):
                    categories = [categories]
                elif not isinstance(categories, list):
                    categories = ["기타"]
                
                # 빈 카테고리 필터링
                categories = [cat.strip() for cat in categories if cat and cat.strip()]
                if not categories:
                    categories = ["기타"]
                
                cleaned_list.append({
                    "keyword": keyword,
                    "categories": categories
                })
            
            if not cleaned_list:
                log_warning(f"⚠️ 정제 후 유효한 키워드 없음, 일반 분류 시도: {query}")
                return self._fallback_classification(query)
            
            log_info(f"✅ 최종 분류 결과: {len(cleaned_list)}개 키워드-카테고리")
            return cleaned_list
            
        except Exception as e:
            log_error(f"❌ HCX 분류 실패: {e}")
            log_info(f"🔄 기본 분류로 전환: {query}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> List[Dict[str, Any]]:
        """Function calling 실패 시 사용하는 기본 분류 방법"""
        log_info(f"🔄 키워드 기반 fallback 분류 시작: {query}")
        
        # 간단한 키워드 기반 분류 (확장)
        keyword_mapping = {
            "전학": "전학, 편입",
            "편입": "전학, 편입", 
            "전입": "전학, 편입",
            "성적": "평가(성적) 관련",
            "평가": "평가(성적) 관련",
            "시험": "평가(성적) 관련",
            "점수": "평가(성적) 관련",
            "입학": "입학 관련",
            "모집": "입학 관련",
            "지원": "입학 관련",
            "학교폭력": "학교폭력",
            "괴롭힘": "학교폭력",
            "왕따": "학교폭력",
            "폭행": "학교폭력",
            "교권": "교권보호 (교육활동 보호)",
            "교사": "교권보호 (교육활동 보호)",
            "선생님": "교권보호 (교육활동 보호)",
            "검정고시": "검정고시",
            "임용": "교원 임용고시 관련",
            "임용고시": "교원 임용고시 관련",
            "증명": "제 증명 관련",
            "서류": "제 증명 관련",
            "증명서": "제 증명 관련",
            "공개": "정보공개",
            "정보": "정보공개",
            "공개청구": "정보공개",
            "생활": "학생 생활",
            "학생": "학생 생활",
            "규정": "학생 생활",
            "수강신청": "학생 생활",
            "수업": "학생 생활",
            "강의": "학생 생활",
            "과제": "학생 생활",
            "숙제": "학생 생활",
            "수강": "학생 생활",
            "학점": "평가(성적) 관련",
            "성취도": "평가(성적) 관련",
            "졸업": "학생 생활",
            "휴학": "학생 생활",
            "복학": "학생 생활",
            "장학금": "학생 생활",
            "등록금": "학생 생활",
            "학비": "학생 생활",
            "기숙사": "학생 생활",
            "기계": "기타",
            "프로그램": "기타",
            "애니메이션": "기타",
            "활동": "기타",
            "조사": "기타",
            "표현": "기타"
        }
        
        query_lower = query.lower()
        detected_category = "기타"
        matched_keyword = None
        
        # 🔧 키워드 추출 개선: 문장이 긴 경우 핵심 키워드만 추출
        best_keyword = self._extract_meaningful_keyword(query, keyword_mapping)
        
        for keyword, category in keyword_mapping.items():
            if keyword in query_lower:
                detected_category = category
                matched_keyword = keyword
                break
        
        # 키워드가 너무 길면 핵심 키워드만 사용
        final_keyword = best_keyword if len(best_keyword) <= 50 else matched_keyword or "기타"
        
        result = [{"keyword": final_keyword, "categories": [detected_category]}]
        
        log_info(f"✅ Fallback 분류 완료:")
        log_info(f"   - 매칭된 키워드: {matched_keyword or '없음'}")
        log_info(f"   - 추출된 키워드: {best_keyword}")
        log_info(f"   - 최종 키워드: {final_keyword}")
        log_info(f"   - 분류된 카테고리: {detected_category}")
        log_info(f"   - 결과: {result}")
        
        return result

    def _extract_meaningful_keyword(self, query: str, keyword_mapping: dict) -> str:
        """문장에서 의미있는 키워드를 추출합니다."""
        # 1. 매핑된 키워드 중 가장 긴 것 우선
        found_keywords = []
        for keyword in keyword_mapping.keys():
            if keyword in query:
                found_keywords.append(keyword)
        
        if found_keywords:
            # 가장 긴 키워드 선택 (더 구체적)
            return max(found_keywords, key=len)
        
        # 2. 일반적인 교육 키워드 추출
        words = query.split()
        meaningful_words = []
        
        # 의미있는 단어들 필터링
        for word in words:
            # 너무 짧거나 일반적인 단어 제외
            if len(word) >= 2 and word not in ['을', '를', '은', '는', '이', '가', '의', '에', '에서', '로', '와', '과', '도', '만', '라서', '니까', '어요', '습니다', '해요', '이다', '있다', '없다']:
                meaningful_words.append(word)
        
        # 3. 첫 번째 의미있는 단어 반환 (최대 20자)
        if meaningful_words:
            return meaningful_words[0][:20]
        
        # 4. 모든 방법이 실패하면 질문의 처음 10자
        return query[:10].strip()

    def _clean_and_validate_keyword(self, keyword: str, query: str) -> str:
        """키워드 길이 및 품질 검증"""
        # 🔧 키워드가 원본 질문과 동일하거나 너무 긴 경우 처리
        if len(keyword) > 100:  # VARCHAR(100) 가정 - 사용자 변경 반영
            log_warning(f"⚠️ 키워드 길이 초과 ({len(keyword)}자): {keyword[:50]}...")
            # 원본 질문에서 의미있는 키워드 추출
            extracted = self._extract_meaningful_keyword(query, {})
            return extracted[:50] if extracted else "기타"
        
        # 키워드가 원본 질문과 거의 동일한 경우 (90% 이상 유사)
        if len(keyword) > 50 and keyword.strip() == query.strip():
            log_warning(f"⚠️ 키워드가 원본 질문과 동일함, 핵심 키워드 추출: {query[:30]}...")
            extracted = self._extract_meaningful_keyword(query, {})
            return extracted[:50] if extracted else "기타"
        
        if len(keyword) < 2:
            log_warning(f"⚠️ 짧은 키워드 건너뜀: {keyword}")
            return "기타"
        
        if keyword.isdigit():
            log_warning(f"⚠️ 숫자만 포함된 키워드 건너뜀: {keyword}")
            return "기타"
        
        # 키워드 정리 (앞뒤 공백 및 특수문자 제거)
        cleaned_keyword = keyword.strip().strip('.,!?;:"()[]{}')
        
        if len(cleaned_keyword) < 2:
            return "기타"
        
        log_info(f"✅ 키워드 유효성 통과: {cleaned_keyword}")
        return cleaned_keyword


# 하위 호환성을 위한 기존 함수
def classify_education_question(query: str) -> Dict[str, Any]:
    """기존 함수와의 호환성을 위한 래퍼 함수"""
    from core.config import Config
    
    config = Config()
    hcx_service = HCXService(config.hcx)
    
    # 기존 반환 형식에 맞춰 변환
    keyword_categories = hcx_service.classify_education_question(query)
    
    return {
        "result": {
            "message": {
                "toolCalls": [{
                    "function": {
                        "arguments": {
                            "keywords_with_categories": keyword_categories
                        }
                    }
                }]
            }
        }
    } 