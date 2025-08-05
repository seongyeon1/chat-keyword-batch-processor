"""
배치 처리 서비스 모듈 - 배치 처리 로직과 워크플로우를 담당합니다.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

from core.config import Config, BatchConfig
from core.database import DatabaseManager
from core.exceptions import BatchProcessError, DatabaseError
from services.hcx_service import HCXService
from services.email_service import EmailService
from services.excel_service import ExcelService
from utils.date_utils import DateUtils
from utils.logger import setup_logging, get_logger, log_info, log_warning, log_error, log_debug
from queries.batch_queries import BatchQueries


class BatchService:
    """배치 처리 메인 서비스 클래스"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # 🚀 로깅 시스템 초기화
        setup_logging(config.log)
        self.logger = get_logger("batch_service")
        
        self.db_manager = DatabaseManager(config.database)
        self.hcx_service = HCXService(config.hcx)
        self.email_service = EmailService(config.email)
        self.excel_service = ExcelService(config.report, self.db_manager)
        self.batch_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.queries = BatchQueries(config)
        
        log_info("✅ BatchService 초기화 완료")
    
    async def run_batch_range(self, start_date: str, end_date: str, start_index: int = 0) -> Dict[str, Any]:
        """기간별 배치 처리를 실행합니다. (날짜별 병렬처리)"""
        log_info(f"📅 기간별 배치 처리 시작: {start_date} ~ {end_date}")
        
        result = {
            "status": "SUCCESS",
            "start_date": start_date,
            "end_date": end_date,
            "total_rows": 0,
            "processed_count": 0,
            "skipped_count": 0,
            "duration": None,
            "details": []
        }
        
        try:
            start_time = time.time()
            
            # 날짜 범위 생성
            date_range = DateUtils.generate_date_range(start_date, end_date)
            log_info(f"📋 처리할 날짜: {len(date_range)}일")
            
            # 🚀 날짜별 병렬처리 구현
            if len(date_range) > 1:
                log_info(f"🚀 날짜별 병렬 처리 시작: {len(date_range)}개 날짜")
                
                # 병렬 처리 - 동시에 여러 날짜 처리
                date_tasks = [
                    self.run_single_batch(target_date, 0)
                    for target_date in date_range
                ]
                
                # 병렬 실행
                date_results = await asyncio.gather(*date_tasks, return_exceptions=True)
                
                # 결과 처리
                for i, target_date in enumerate(date_range):
                    date_result = date_results[i]
                    
                    if isinstance(date_result, Exception):
                        log_error(f"❌ {target_date} 처리 실패: {date_result}")
                        result["details"].append({
                            "date": target_date,
                            "status": "FAILED",
                            "processed": 0,
                            "skipped": 0,
                            "error": str(date_result)
                        })
                        continue
                    
                    # 성공한 경우 결과 누적
                    result["total_rows"] += date_result.get("total_rows", 0)
                    result["processed_count"] += date_result.get("processed_count", 0)
                    result["skipped_count"] += date_result.get("skipped_count", 0)
                    result["details"].append({
                        "date": target_date,
                        "status": date_result.get("status", "UNKNOWN"),
                        "processed": date_result.get("processed_count", 0),
                        "skipped": date_result.get("skipped_count", 0)
                    })
                    
                    log_info(f"✅ {target_date} 완료: {date_result.get('processed_count', 0)}개 처리")
                
                log_info(f"🎉 날짜별 병렬 처리 완료!")
                
            else:
                # 단일 날짜인 경우 기존 방식
                target_date = date_range[0]
                log_info(f"📅 단일 날짜 처리: {target_date}")
                
                date_result = await self.run_single_batch(target_date, 0)
                
                result["total_rows"] += date_result.get("total_rows", 0)
                result["processed_count"] += date_result.get("processed_count", 0)
                result["skipped_count"] += date_result.get("skipped_count", 0)
                result["details"].append({
                    "date": target_date,
                    "status": date_result.get("status", "UNKNOWN"),
                    "processed": date_result.get("processed_count", 0),
                    "skipped": date_result.get("skipped_count", 0)
                })
                
                log_info(f"✅ {target_date} 완료: {date_result.get('processed_count', 0)}개 처리")
            
            end_time = time.time()
            duration = self._format_duration(end_time - start_time)
            result["duration"] = duration
            
            # 실패한 날짜가 있는지 확인
            failed_dates = [detail["date"] for detail in result["details"] if detail["status"] == "FAILED"]
            if failed_dates:
                result["status"] = "PARTIAL_SUCCESS"
                result["failed_dates"] = failed_dates
                log_warning(f"⚠️ 일부 날짜 처리 실패: {', '.join(failed_dates)}")
            
            log_info(f"🎉 기간별 배치 처리 완료!")
            return result
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            log_error(f"❌ 기간별 배치 처리 실패: {e}")
            raise BatchProcessError(f"기간별 배치 처리 실패: {e}")

    async def check_missing_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """누락된 키워드 데이터를 확인합니다."""
        log_info(f"🔍 누락 데이터 확인 중: {start_date} ~ {end_date}")
        
        try:
            # 1. 기존 처리된 데이터 조회 (classify_chat_keywords_by_date 쿼리 대체)
            log_info("📊 기존 처리된 데이터 조회 중...")
            classified_query = self.queries.classify_chat_keywords_by_date(start_date, end_date)
            classified_result = await self.db_manager.execute_query(classified_query)
            
            # 2. 해당 기간의 전체 채팅 데이터 조회
            log_info("📊 전체 채팅 데이터 조회 중...")
            total_chattings_query = self.queries.get_total_chattings_by_date(start_date, end_date)
            total_result = await self.db_manager.execute_query(total_chattings_query)
            
            # 3. 기존 처리된 데이터 분석
            log_info("📊 기존 처리된 데이터 분석 중...")
            
            # 처리된 질문들 추출
            classified_questions = set()
            classified_by_date = {}
            
            for row in classified_result:
                # 쿼리 결과: category_name, query_text, keyword, created_at, query_count
                query_text = row[1]
                created_at = row[3]
                date_str = created_at.strftime('%Y-%m-%d') if hasattr(created_at, 'strftime') else str(created_at)[:10]
                
                classified_questions.add(query_text)
                
                if date_str not in classified_by_date:
                    classified_by_date[date_str] = set()
                classified_by_date[date_str].add(query_text)
            
            # 4. 전체 채팅에서 고유 질문들 조회
            log_info("🔍 전체 고유 질문 조회 중...")
            all_questions_query = self.queries.get_all_unique_questions_by_date(start_date, end_date)
            all_questions_result = await self.db_manager.execute_query(all_questions_query)
            
            # 5. 누락 데이터 분석
            all_questions_by_date = {}
            missing_questions_by_date = {}
            
            for row in all_questions_result:
                input_text = row[0]
                date_obj = row[1]
                date_str = date_obj.strftime('%Y-%m-%d') if hasattr(date_obj, 'strftime') else str(date_obj)
                
                if date_str not in all_questions_by_date:
                    all_questions_by_date[date_str] = set()
                all_questions_by_date[date_str].add(input_text)
                
                # 누락된 질문 확인
                if input_text not in classified_questions:
                    if date_str not in missing_questions_by_date:
                        missing_questions_by_date[date_str] = set()
                    missing_questions_by_date[date_str].add(input_text)
            
            # 6. 결과 정리
            total_summary = {row[0].strftime('%Y-%m-%d'): {
                'unique_questions': row[1], 
                'total_messages': row[2]
            } for row in total_result}
            
            processed_summary = {}
            for date_str, questions in classified_by_date.items():
                processed_summary[date_str] = {
                    'processed_questions': len(questions)
                }
            
            missing_summary = {}
            for date_str, questions in missing_questions_by_date.items():
                missing_summary[date_str] = {
                    'missing_questions': len(questions)
                }
            
            # 7. 통계 계산
            total_unique_questions = sum(day['unique_questions'] for day in total_summary.values())
            total_processed_questions = len(classified_questions)
            total_missing_questions = sum(len(questions) for questions in missing_questions_by_date.values())
            
            log_info(f"✅ 누락 데이터 확인 완료")
            log_info(f"📊 전체 고유 질문: {total_unique_questions}개")
            log_info(f"✅ 기존 처리된 질문: {total_processed_questions}개")
            log_info(f"🚫 누락된 질문: {total_missing_questions}개")
            log_info(f"📈 처리율: {(total_processed_questions / total_unique_questions * 100):.1f}%" if total_unique_questions > 0 else "처리율: 0%")
            
            return {
                "status": "SUCCESS",
                "period": f"{start_date} ~ {end_date}",
                "total_summary": total_summary,
                "processed_summary": processed_summary,
                "missing_summary": missing_summary,
                "stats": {
                    "total_unique_questions": total_unique_questions,
                    "total_processed_questions": total_processed_questions,
                    "total_missing_questions": total_missing_questions,
                    "processing_rate": round(total_processed_questions / total_unique_questions * 100, 1) if total_unique_questions > 0 else 0
                },
                "classified_result_count": len(classified_result),
                "missing_questions_detail": missing_questions_by_date
            }
            
        except Exception as e:
            raise BatchProcessError(f"누락 데이터 확인 실패: {e}")

    async def process_missing_data(self, start_date: str, end_date: str, start_index: int = 0, limit: int = None) -> Dict[str, Any]:
        """누락된 키워드 데이터를 처리합니다."""
        limit_text = f" (최대 {limit}개 제한)" if limit else ""
        log_info(f"🔧 누락 데이터 처리 시작: {start_date} ~ {end_date}{limit_text}")
        
        try:
            # 1. 정확한 누락 데이터 조회
            log_info("🔍 정확한 누락 데이터 조회 중...")
            
            missing_data_query = self.queries.get_missing_data(start_date, end_date)
            missing_rows = await self.db_manager.execute_query(missing_data_query)
            
            if not missing_rows:
                log_info("✅ 누락된 데이터가 없습니다.")
                return {
                    "status": "SUCCESS",
                    "message": "누락 데이터 없음",
                    "processed_count": 0,
                    "skipped_count": 0,
                    "period": f"{start_date} ~ {end_date}",
                    "limit_applied": limit
                }
            
            actual_count = len(missing_rows)
            limit_applied_text = f" (제한: {limit}개 적용)" if limit and actual_count == limit else ""
            log_info(f"📋 발견된 누락 데이터: {actual_count}개{limit_applied_text}")
            
            if limit and actual_count < limit:
                log_info(f"ℹ️ 실제 누락 데이터가 제한값({limit}개)보다 적습니다.")
            
            # 날짜별 누락 데이터 요약 출력
            missing_by_date = {}
            for row in missing_rows:
                missing_date = str(row[0])
                if missing_date not in missing_by_date:
                    missing_by_date[missing_date] = 0
                missing_by_date[missing_date] += 1
            
            log_info("📅 날짜별 누락 데이터 요약:")
            for date, count in sorted(missing_by_date.items()):
                log_info(f"   - {date}: {count}개")
            
            # 2. 누락된 데이터를 배치 처리 시스템으로 처리
            start_time = time.time()
            
            # 배치 처리를 위한 데이터 형식 변환
            batch_rows = []
            for row in missing_rows:
                missing_date = row[0]
                input_text = row[1]
                missing_count = row[2]
                
                # created_at을 만들기 위해 missing_date 사용
                try:
                    from datetime import datetime
                    if isinstance(missing_date, str):
                        created_at = datetime.strptime(missing_date, '%Y-%m-%d')
                    else:
                        created_at = missing_date
                except:
                    created_at = missing_date
                
                batch_rows.append((input_text, missing_count, created_at))
            
            # stats 딕셔너리 초기화
            stats = {
                'target': f"missing_data_{start_date}_{end_date}",
                'category_distribution': {},
                'processed_count': 0,
                'skipped_count': 0
            }
            
            # 누락 데이터 전용 배치 처리
            processed_count, skipped_count = await self._process_missing_data_parallel(
                batch_rows, 
                start_index, 
                stats, 
                f"missing_{start_date}_{end_date}"
            )
            
            end_time = time.time()
            duration = self._format_duration(end_time - start_time)
            
            result = {
                "status": "SUCCESS",
                "period": f"{start_date} ~ {end_date}",
                "total_missing_questions": actual_count,
                "processed_count": processed_count,
                "skipped_count": skipped_count,
                "duration": duration,
                "missing_by_date": missing_by_date,
                "limit_applied": limit,
                "limit_reached": bool(limit and actual_count == limit)
            }
            
            limit_info = f" (제한: {limit}개)" if limit else ""
            log_info(f"🎉 누락 데이터 처리 완료{limit_info}!")
            log_info(f"📊 처리 결과: {processed_count}개 처리, {skipped_count}개 중복 스킵")
            
            # 3. 처리 후 검증
            log_info("🔍 처리 후 검증 중...")
            verification_result = await self._verify_missing_data_processing(start_date, end_date)
            result["verification"] = verification_result
            
            return result
            
        except Exception as e:
            raise BatchProcessError(f"누락 데이터 처리 실패: {e}")

    async def _process_missing_data_parallel(self, rows: List[tuple], start_index: int, 
                                           stats: Dict[str, Any], target_identifier: str) -> Tuple[int, int]:
        """누락 데이터 전용 병렬 처리 함수 - 진행률 표시 및 스트리밍 방식"""
        log_info(f"🚀 누락 데이터 병렬 처리 시작: {len(rows)}개 항목 (스트리밍 모드)")
        log_info("⚠️ 누락 데이터 처리 모드: 중복 체크 비활성화 (이미 누락 확인된 데이터)")
        
        # 1. 카테고리 캐시 구축
        category_cache = await self._build_category_cache()
        
        # 2. 스키마 확인 (중복 체크 캐시는 생성하지 않음)
        schema_query = self.queries.get_table_schema("admin_chat_keywords")
        schema = await self.db_manager.execute_query(schema_query)
        available_columns = [row[0] for row in schema]
        query_column = self._determine_query_column(available_columns)
        
        # 3. 병렬 처리 설정
        chunk_size = self.config.batch.batch_size
        chunks = [rows[i:i + chunk_size] for i in range(start_index, len(rows), chunk_size)]
        
        total_processed = 0
        total_skipped = 0
        total_chunks = len(chunks)
        total_items = len(rows) - start_index
        
        # 스레드 안전 락
        lock = threading.Lock()
        
        log_info(f"📦 누락 데이터 처리 상세 정보:")
        log_info(f"   📊 총 {total_items:,}개 누락 항목을 {total_chunks}개 청크로 분할")
        log_info(f"   📦 청크당 최대 {chunk_size}개 항목")
        log_info(f"   🏁 시작 인덱스: {start_index}")
        log_info(f"   🔄 중복 체크: 비활성화 (누락 데이터 모드)")
        
        start_time = time.time()
        
        # 4. 청크별 순차 처리 - 즉시 적재 방식
        for chunk_idx, chunk in enumerate(chunks):
            chunk_start_time = time.time()
            
            # 📊 진행률 계산
            progress_percentage = ((chunk_idx) / total_chunks) * 100
            processed_items = chunk_idx * chunk_size
            remaining_items = total_items - processed_items
            
            log_info(f"📈 누락 데이터 진행률: {progress_percentage:.1f}% ({chunk_idx}/{total_chunks} 청크)")
            log_info(f"   🔄 현재 청크 {chunk_idx + 1}/{total_chunks} 처리 중... ({len(chunk)}개 누락 항목)")
            log_info(f"   📋 처리 완료: {processed_items:,}개 / 남은 항목: {remaining_items:,}개")

            try:
                # 청크 처리 (동기 방식) - 중복 체크 없이
                chunk_processed, chunk_skipped, chunk_batch_data = self._process_missing_chunk_sync_no_duplicate_check(
                    chunk, category_cache, query_column, lock, stats
                )
                
                # 🔥 즉시 데이터베이스에 적재 (메모리에 누적하지 않음)
                if chunk_batch_data:
                    log_info(f"   💾 누락 데이터 청크 {chunk_idx + 1} MySQL 즉시 적재: {len(chunk_batch_data)}개 레코드")
                    await self._process_immediate_batch_insert(chunk_batch_data, query_column, chunk_idx + 1, total_chunks)
                    log_info(f"   ✅ 누락 데이터 청크 {chunk_idx + 1} MySQL 적재 완료")
                else:
                    log_info(f"   ⏭️ 누락 데이터 청크 {chunk_idx + 1}: 적재할 데이터 없음")
                
                total_processed += chunk_processed
                total_skipped += chunk_skipped
                
                # 📊 청크 처리 시간 및 예상 시간 계산
                chunk_duration = time.time() - chunk_start_time
                avg_chunk_time = (time.time() - start_time) / (chunk_idx + 1)
                remaining_chunks = total_chunks - (chunk_idx + 1)
                estimated_remaining_time = avg_chunk_time * remaining_chunks
                
                log_info(f"   ✅ 누락 데이터 청크 {chunk_idx + 1} 완료: {chunk_processed}개 처리, {chunk_skipped}개 스킵")
                log_info(f"   ⏱️ 청크 처리 시간: {self._format_duration(chunk_duration)}")
                log_info(f"   📈 누적 처리: {total_processed:,}개 완료, {total_skipped:,}개 스킵")
                
                if remaining_chunks > 0:
                    log_info(f"   🕐 예상 남은 시간: {self._format_duration(estimated_remaining_time)}")
                
                # 청크 간 잠시 대기 (데이터베이스 부하 방지)
                await asyncio.sleep(0.2)
                
            except Exception as e:
                log_error(f"❌ 누락 데이터 청크 {chunk_idx + 1} 처리 실패: {e}")
                continue
        
        # 🎉 최종 완료 통계
        total_duration = time.time() - start_time
        final_progress = 100.0
        
        log_info(f"🎉 누락 데이터 스트리밍 처리 완료!")
        log_info(f"   📈 최종 진행률: {final_progress}% (완료)")
        log_info(f"   📊 누락 데이터 처리 결과:")
        log_info(f"      ✅ 성공: {total_processed:,}개")
        log_info(f"      ⏭️ 스킵: {total_skipped:,}개")
        log_info(f"      📦 총 청크: {total_chunks}개")
        log_info(f"      ⏱️ 총 소요 시간: {self._format_duration(total_duration)}")
        if total_duration > 0:
            log_info(f"      📈 평균 처리 속도: {(total_processed + total_skipped) / total_duration:.1f}개/초")
        
        return total_processed, total_skipped

    def _process_missing_chunk_sync_no_duplicate_check(self, chunk_data: List[tuple], category_cache: Dict[str, int],
                                                       query_column: str, lock: threading.Lock,
                                                       stats: Dict[str, Any]) -> Tuple[int, int, List[Dict[str, Any]]]:
        """누락 데이터 청크 동기 처리 함수 - 중복 체크 없이 바로 처리"""
        chunk_processed = 0
        chunk_skipped = 0
        chunk_batch_data = []
        total_chunk_items = len(chunk_data)
        
        # stats 안전성 확인
        if stats is None:
            stats = {}
        if 'category_distribution' not in stats:
            stats['category_distribution'] = {}
        
        log_info(f"      🔧 청크 내부 처리 시작: {total_chunk_items}개 항목 (중복 체크 비활성화)")
        
        for item_idx, row in enumerate(chunk_data):
            try:
                # 📊 청크 내 진행률 표시 (매 10% 간격 또는 큰 청크의 경우)
                if total_chunk_items > 20 and (item_idx + 1) % max(1, total_chunk_items // 10) == 0:
                    chunk_progress = ((item_idx + 1) / total_chunk_items) * 100
                    log_info(f"         📈 청크 내 진행률: {chunk_progress:.0f}% ({item_idx + 1}/{total_chunk_items})")
                elif total_chunk_items <= 20 and (item_idx + 1) % 5 == 0:
                    log_info(f"         📋 처리 중: {item_idx + 1}/{total_chunk_items} 항목")
                
                input_text = row[0]
                total_count = row[1]
                created_at = row[2]
                
                # HCX 분류 처리 (중복 체크 없이 바로 처리)
                log_info(f"         🤖 HCX API 호출: {input_text[:50]}...")
                keyword_categories = self.hcx_service.classify_education_question(input_text)
                
                # 🚦 API 호출 간 짧은 지연 추가 (Rate Limiting 방지)
                time.sleep(0.1)  # 100ms 지연
                
                # 키워드-카테고리 처리
                question_processed = False  # 이 질문에서 처리된 데이터가 있는지 체크
                
                for item in keyword_categories:
                    keyword = item.get("keyword", "").strip()
                    categories = item.get("categories", ["기타"])
                    
                    if not keyword:
                        continue
                    
                    # 🔧 키워드 길이 제한 (데이터베이스 컬럼 크기 고려)
                    if len(keyword) > 100:  # VARCHAR(100) 가정
                        log_warning(f"         ⚠️ 키워드 길이 초과 ({len(keyword)}자), 요약으로 대체: {keyword[:50]}...")
                        keyword = input_text[:95] + "..." if len(input_text) > 95 else input_text
                        if len(keyword) > 100:
                            keyword = keyword[:97] + "..."
                    
                    # 빈 키워드나 유효하지 않은 키워드 체크
                    if not keyword or keyword.strip() == "" or keyword.strip() == "기타":
                        meaningful_keyword = self._extract_simple_keyword(input_text)
                        keyword = meaningful_keyword if meaningful_keyword else "기타"
                        log_info(f"         🔄 키워드 보완: '{keyword}'")
                    
                    for category_name in categories:
                        category_id = category_cache.get(str(category_name).strip())
                        if not category_id:
                            continue
                        
                        # 중복 체크 없이 바로 데이터 추가
                        chunk_batch_data.append({
                            query_column: input_text,
                            "keyword": keyword,
                            "category_id": category_id,
                            "query_count": total_count,
                            "created_at": created_at,
                            "batch_created_at": self.batch_created_at
                        })
                        
                        chunk_processed += 1
                        question_processed = True
                        log_info(f"         ✅ 데이터 추가 (중복체크 없이): {keyword} - {category_name}")
                        
                        # 통계 업데이트 (안전하게)
                        try:
                            with lock:
                                if 'category_distribution' in stats:
                                    stats['category_distribution'][str(category_name)] = \
                                        stats['category_distribution'].get(str(category_name), 0) + 1
                        except Exception as stats_error:
                            # 통계 업데이트 실패는 무시
                            pass
                
                # 질문에서 처리된 데이터가 없으면 스킵으로 카운트
                if not question_processed:
                    chunk_skipped += 1
                    log_info(f"         ⏭️ 질문 스킵 (분류 결과 없음): {input_text[:30]}...")
                
            except Exception as e:
                chunk_skipped += 1
                log_error(f"         ❌ 청크 내 항목 처리 실패: {input_text} | 오류: {e}")
                continue
        
        log_info(f"      ✅ 청크 내부 처리 완료: {chunk_processed}개 처리, {chunk_skipped}개 스킵 (중복체크 비활성화)")
        return chunk_processed, chunk_skipped, chunk_batch_data

    async def _fetch_data_for_period(self, start_date: str, end_date: str) -> List[tuple]:
        """기간별 데이터를 조회합니다."""
        try:
            query = self.queries.get_unique_chattings_by_date(start_date, end_date)
            return await self.db_manager.execute_query(query)
        except Exception as e:
            raise BatchProcessError(f"데이터 조회 실패: {e}")

    async def _build_category_cache(self) -> Dict[str, int]:
        """카테고리 캐시를 구축합니다."""
        log_info("🔍 카테고리 정보 미리 조회 중...")
        try:
            query = self.queries.get_categories()
            categories = await self.db_manager.execute_query(query)
            cache = {cat[1]: cat[0] for cat in categories}
            log_info(f"✅ {len(cache)}개 카테고리 캐시 완료")
            return cache
        except Exception as e:
            raise BatchProcessError(f"카테고리 캐시 구축 실패: {e}")
    
    async def _verify_missing_data_processing(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """누락 데이터 처리 후 검증을 수행합니다."""
        log_info("🔍 누락 데이터 처리 검증 중...")
        
        try:
            # 처리 후 다시 누락 데이터 확인
            verification_query = self.queries.verify_missing_data_processing(
                start_date, end_date
            )
            
            remaining_result = await self.db_manager.execute_query(verification_query)
            
            total_remaining = sum(row[1] for row in remaining_result)
            
            verification = {
                "remaining_missing_count": total_remaining,
                "remaining_by_date": {str(row[0]): row[1] for row in remaining_result},
                "verification_success": total_remaining == 0
            }
            
            if total_remaining == 0:
                log_info("✅ 검증 완료: 모든 누락 데이터가 처리되었습니다.")
            else:
                log_warning(f"⚠️ 검증 결과: {total_remaining}개의 데이터가 여전히 누락되어 있습니다.")
                for date, count in verification["remaining_by_date"].items():
                    log_info(f"   - {date}: {count}개")
            
            return verification
            
        except Exception as e:
            log_error(f"⚠️ 검증 실패: {e}")
            return {"verification_success": False, "error": str(e)}

    async def _process_large_batch_insert(self, data_list: List[Dict[str, Any]], query_column: str):
        """대용량 배치 INSERT 처리"""
        if not data_list:
            return
        
        log_info(f"💾 대용량 배치 INSERT 시작: {len(data_list)}개 레코드")
        
        # 데이터를 배치 크기로 분할
        batches = [data_list[i:i + self.config.batch.batch_size] 
                   for i in range(0, len(data_list), self.config.batch.batch_size)]
        
        insert_query = self.queries.insert_chat_keywords(query_column)
        
        success_count = 0
        
        for batch_idx, batch in enumerate(batches):
            try:
                log_info(f"📦 배치 {batch_idx + 1}/{len(batches)} 처리 중... ({len(batch)}개)")
                
                batch_success = await self.db_manager.execute_batch_insert(insert_query, batch)
                success_count += batch_success
                
                # 배치 간 잠시 대기
                await asyncio.sleep(0.1)
                
            except Exception as e:
                log_error(f"❌ 배치 {batch_idx + 1} 실패: {e}")
        
        log_info(f"🎯 대용량 배치 INSERT 완료: {success_count}개 성공")

    async def _process_immediate_batch_insert(self, data_list: List[Dict[str, Any]], query_column: str, 
                                            current_chunk: int, total_chunks: int):
        """즉시 배치 INSERT 처리 - 메모리 효율적"""
        if not data_list:
            log_info(f"      💾 청크 {current_chunk}/{total_chunks}: 적재할 데이터 없음")
            return
        
        log_info(f"      💾 청크 {current_chunk}/{total_chunks} MySQL 즉시 INSERT 시작:")
        log_info(f"         📊 적재 대상: {len(data_list)}개 레코드")
        log_info(f"         🗄️ 대상 테이블: admin_chat_keywords")
        log_info(f"         📝 컬럼: {query_column}")
        
        insert_query = self.queries.insert_chat_keywords(query_column)
        
        try:
            insert_start_time = time.time()
            
            # 한 번에 모든 데이터 INSERT (청크 크기가 이미 적당함)
            log_info(f"         🚀 배치 INSERT 실행 중...")
            success_count = await self.db_manager.execute_batch_insert(insert_query, data_list)
            
            insert_duration = time.time() - insert_start_time
            
            log_info(f"         ✅ 배치 INSERT 성공: {success_count}개 레코드")
            log_info(f"         ⏱️ INSERT 소요 시간: {self._format_duration(insert_duration)}")
            log_info(f"         📈 INSERT 속도: {success_count / insert_duration:.1f}개/초")
            
        except Exception as e:
            log_error(f"         ❌ 배치 INSERT 실패, 개별 처리로 전환: {e}")
            log_info(f"         🔄 개별 INSERT 방식으로 재시도...")
            # 실패 시 개별 INSERT로 재시도
            await self._fallback_individual_insert(data_list, insert_query, query_column)

    async def _fallback_individual_insert(self, data_list: List[Dict[str, Any]], insert_query: str, query_column: str):
        """배치 INSERT 실패 시 개별 INSERT로 처리"""
        log_info(f"         🔄 개별 INSERT 시작: {len(data_list)}개 레코드")
        
        success_count = 0
        failed_count = 0
        individual_start_time = time.time()
        
        for idx, params in enumerate(data_list):
            try:
                # 키워드 길이 최종 안전장치
                if 'keyword' in params:
                    keyword = params['keyword']
                    if len(str(keyword)) > 100:
                        log_warning(f"            ⚠️ 개별 INSERT 키워드 길이 초과, 자르기: {len(str(keyword))}자 -> 100자")
                        params['keyword'] = str(keyword)[:98] + "..."
                
                await self.db_manager.execute_insert(insert_query, params)
                success_count += 1
                
                # 진행률 표시 (매 10개마다)
                if (idx + 1) % 10 == 0 or idx == len(data_list) - 1:
                    progress = ((idx + 1) / len(data_list)) * 100
                    log_info(f"            📊 개별 INSERT 진행률: {progress:.0f}% ({idx + 1}/{len(data_list)}) - 성공: {success_count}개")
                
            except Exception as e:
                failed_count += 1
                log_error(f"            ❌ 개별 INSERT 실패 ({idx + 1}): {e}")
                # 키워드만 로깅 (전체 데이터는 너무 길어짐)
                keyword = params.get('keyword', 'Unknown')[:50]
                log_info(f"               실패한 키워드: {keyword}")
        
        individual_duration = time.time() - individual_start_time
        
        log_info(f"         🎯 개별 INSERT 완료:")
        log_info(f"            ✅ 성공: {success_count}개")
        log_info(f"            ❌ 실패: {failed_count}개")
        log_info(f"            ⏱️ 소요 시간: {self._format_duration(individual_duration)}")
        if individual_duration > 0:
            log_info(f"            📈 평균 속도: {(success_count + failed_count) / individual_duration:.1f}개/초")

    def _determine_query_column(self, available_columns: List[str]) -> str:
        """적절한 쿼리 컬럼명을 결정합니다."""
        column_priority = ['query_text', 'content', 'question', 'text']
        
        for col in column_priority:
            if col in available_columns:
                return col
        
        # 기본값
        return available_columns[1] if len(available_columns) > 1 else available_columns[0]

    def _format_duration(self, duration: float) -> str:
        """초를 분으로 변환하여 포맷팅합니다."""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}분 {seconds}초"

    def _extract_simple_keyword(self, text: str) -> str:
        """간단한 키워드 추출 함수"""
        # 교육 관련 핵심 키워드 매핑
        keyword_mapping = {
            "수강신청": "수강신청",
            "전학": "전학",
            "편입": "편입",
            "성적": "성적",
            "평가": "평가",
            "시험": "시험",
            "입학": "입학",
            "졸업": "졸업",
            "휴학": "휴학",
            "복학": "복학",
            "장학금": "장학금",
            "학교폭력": "학교폭력",
            "교권": "교권",
            "검정고시": "검정고시",
            "임용": "임용",
            "증명서": "증명서",
            "수업": "수업",
            "강의": "강의",
            "과제": "과제"
        }
        
        text_lower = text.lower()
        
        # 1. 매핑된 키워드 찾기
        for keyword in keyword_mapping.keys():
            if keyword in text_lower:
                return keyword
        
        # 2. 의미있는 첫 번째 단어 추출
        words = text.split()
        for word in words:
            # 너무 짧거나 일반적인 조사/어미 제외
            if len(word) >= 2 and word not in ['을', '를', '은', '는', '이', '가', '의', '에', '에서', '로', '와', '과', '하는', '있는', '없는', '어떻게', '언제', '어디']:
                return word[:20]  # 최대 20자
        
        # 3. 기본값
        return text[:10].strip() if len(text) > 10 else text.strip()

    async def run_missing_data_batch(self, start_date: str, end_date: str, start_index: int = 0) -> Dict[str, Any]:
        """누락 데이터 확인 및 처리를 통합 실행합니다."""
        log_info(f"🔍 누락 데이터 통합 처리 시작: {start_date} ~ {end_date}")
        
        try:
            # 1. 누락 데이터 확인
            missing_check = await self.check_missing_data(start_date, end_date)
            
            # 2. 누락 데이터가 있으면 처리
            if missing_check["stats"]["total_missing_questions"] > 0:
                process_result = await self.process_missing_data(start_date, end_date, start_index)
                
                return {
                    **missing_check,
                    "processing_result": process_result,
                    "final_status": process_result["status"]
                }
            else:
                log_info("✅ 누락된 데이터가 없습니다.")
                return {
                    **missing_check,
                    "processing_result": {
                        "status": "SUCCESS",
                        "message": "처리할 누락 데이터 없음"
                    },
                    "final_status": "SUCCESS"
                }
                
        except Exception as e:
            raise BatchProcessError(f"누락 데이터 통합 처리 실패: {e}")
    
    async def run_single_batch(self, target_date: str = None, start_index: int = 0) -> Dict[str, Any]:
        """
        단일 날짜 배치 처리를 실행합니다.
        
        Args:
            target_date (str): 대상 날짜
            start_index (int): 시작 인덱스
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        if not target_date:
            target_date = self.config.batch.default_target_date
        
        log_info(f"📋 단일 날짜 배치 처리 시작: {target_date}")
        
        result = {
            "status": "SUCCESS",
            "target_date": target_date,
            "total_rows": 0,
            "processed_count": 0,
            "skipped_count": 0,
            "duration": None
        }
        
        try:
            start_time = time.time()
            
            # 데이터 조회
            rows = await self._fetch_data_for_period(target_date, target_date)
            
            if not rows:
                log_info(f"ℹ️ {target_date}에 대한 데이터가 없습니다.")
                result["total_rows"] = 0
                result["duration"] = self._format_duration(time.time() - start_time)
                return result
            
            result["total_rows"] = len(rows)
            log_info(f"✅ {len(rows)}개 레코드 조회")
            
            # stats 딕셔너리 초기화
            stats = {
                'target_date': target_date,
                'category_distribution': {},
                'processed_count': 0,
                'skipped_count': 0
            }
            
            # 배치 처리 실행
            processed_count, skipped_count = await self._process_batch_data_parallel(
                rows, 
                start_index, 
                stats, 
                target_date,
                target_date,  # start_date
                target_date   # end_date
            )
            
            end_time = time.time()
            duration = self._format_duration(end_time - start_time)
            
            result.update({
                "processed_count": processed_count,
                "skipped_count": skipped_count,
                "duration": duration
            })
            
            log_info(f"✅ {target_date} 배치 처리 완료: {processed_count}개 처리, {skipped_count}개 스킵")
            return result
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            raise BatchProcessError(f"단일 날짜 배치 처리 실패 ({target_date}): {e}")
    
    async def _process_batch_data_parallel(self, rows: List[tuple], start_index: int, 
                                         stats: Dict[str, Any], target_identifier: str, start_date: str, end_date: str) -> Tuple[int, int]:
        """병렬 배치 데이터 처리 - 진행률 표시 및 중간 적재"""
        # 변수 초기화 수정
        total_processed = 0
        total_skipped = 0
        
        # stats가 None이거나 category_distribution이 없으면 초기화
        if stats is None:
            stats = {}
        if 'category_distribution' not in stats:
            stats['category_distribution'] = {}
        
        # 카테고리 캐시 생성
        category_cache = await self._build_category_cache()
        
        # 중복 체크 캐시 생성 - target_identifier를 날짜로 사용
        # target_identifier가 날짜 형식인 경우 해당 날짜를 시작일과 종료일로 사용
        existing_cache, query_column = await self._build_duplicate_cache(start_date, end_date)
        
        # 스레드 안전 락
        lock = threading.Lock()
        
        # 데이터를 청크로 분할
        processing_rows = rows[start_index:]
        chunk_size = self.config.batch.classification_batch_size
        chunks = [processing_rows[i:i + chunk_size] 
                  for i in range(0, len(processing_rows), chunk_size)]
        
        total_chunks = len(chunks)
        total_items = len(processing_rows)
        
        log_info(f"🚀 배치 병렬 처리 시작:")
        log_info(f"   📊 총 {total_items:,}개 항목을 {total_chunks}개 청크로 분할")
        log_info(f"   📦 청크당 최대 {chunk_size}개 항목")
        
        start_time = time.time()
        
        # 🔥 청크별 순차 처리 - 즉시 적재 방식 (메모리 효율적)
        for chunk_idx, chunk in enumerate(chunks):
            chunk_start_time = time.time()
            
            # 📊 진행률 계산
            progress_percentage = ((chunk_idx) / total_chunks) * 100
            processed_items = chunk_idx * chunk_size
            remaining_items = total_items - processed_items
            
            log_info(f"📈 진행률: {progress_percentage:.1f}% ({chunk_idx}/{total_chunks} 청크)")
            log_info(f"   🔄 현재 청크 {chunk_idx + 1}/{total_chunks} 처리 중... ({len(chunk)}개 항목)")
            log_info(f"   📋 처리 완료: {processed_items:,}개 / 남은 항목: {remaining_items:,}개")
            
            try:
                # 청크 처리 (동기 방식)
                chunk_processed, chunk_skipped, chunk_batch_data = self._process_chunk_sync(
                    chunk, category_cache, existing_cache, query_column, lock, stats
                )
                
                # 🔥 즉시 데이터베이스에 적재 (메모리에 누적하지 않음)
                if chunk_batch_data:
                    log_info(f"   💾 청크 {chunk_idx + 1} MySQL 즉시 적재 시작: {len(chunk_batch_data)}개 레코드")
                    await self._process_immediate_batch_insert(chunk_batch_data, query_column, chunk_idx + 1, total_chunks)
                    log_info(f"   ✅ 청크 {chunk_idx + 1} MySQL 적재 완료")
                else:
                    log_info(f"   ⏭️ 청크 {chunk_idx + 1}: 적재할 데이터 없음")
                
                total_processed += chunk_processed
                total_skipped += chunk_skipped
                
                # 📊 청크 처리 시간 및 예상 시간 계산
                chunk_duration = time.time() - chunk_start_time
                avg_chunk_time = (time.time() - start_time) / (chunk_idx + 1)
                remaining_chunks = total_chunks - (chunk_idx + 1)
                estimated_remaining_time = avg_chunk_time * remaining_chunks
                
                log_info(f"   ✅ 청크 {chunk_idx + 1} 완료: {chunk_processed}개 처리, {chunk_skipped}개 스킵")
                log_info(f"   ⏱️ 청크 처리 시간: {self._format_duration(chunk_duration)}")
                log_info(f"   📈 누적 처리: {total_processed:,}개 완료, {total_skipped:,}개 스킵")
                
                if remaining_chunks > 0:
                    log_info(f"   🕐 예상 남은 시간: {self._format_duration(estimated_remaining_time)}")
                
                # 청크 간 잠시 대기 (데이터베이스 부하 방지)
                await asyncio.sleep(0.3)
                
            except Exception as e:
                log_error(f"❌ 청크 {chunk_idx + 1} 처리 실패: {e}")
                continue
        
        # 🎉 최종 완료 통계
        total_duration = time.time() - start_time
        final_progress = 100.0
        
        log_info(f"🎉 배치 병렬 처리 완료!")
        log_info(f"   📈 최종 진행률: {final_progress}% (완료)")
        log_info(f"   📊 처리 결과:")
        log_info(f"      ✅ 성공: {total_processed:,}개")
        log_info(f"      ⏭️ 스킵: {total_skipped:,}개")
        log_info(f"      📦 총 청크: {total_chunks}개")
        log_info(f"      ⏱️ 총 소요 시간: {self._format_duration(total_duration)}")
        if total_duration > 0:
            log_info(f"      📈 평균 처리 속도: {(total_processed + total_skipped) / total_duration:.1f}개/초")
        
        return total_processed, total_skipped
    
    def _process_chunk_sync(self, chunk_data: List[tuple], category_cache: Dict[str, int],
                           existing_cache: set, query_column: str, lock: threading.Lock,
                           stats: Dict[str, Any]) -> Tuple[int, int, List[Dict[str, Any]]]:
        """동기 청크 처리 함수 - 상세 진행률 표시"""
        chunk_processed = 0
        chunk_skipped = 0
        chunk_batch_data = []
        total_chunk_items = len(chunk_data)
        
        # stats 안전성 확인
        if stats is None:
            stats = {}
        if 'category_distribution' not in stats:
            stats['category_distribution'] = {}
        
        log_info(f"      🔧 청크 내부 처리 시작: {total_chunk_items}개 항목")
        
        for item_idx, row in enumerate(chunk_data):
            try:
                # 📊 청크 내 진행률 표시 (매 10% 간격 또는 큰 청크의 경우)
                if total_chunk_items > 20 and (item_idx + 1) % max(1, total_chunk_items // 10) == 0:
                    chunk_progress = ((item_idx + 1) / total_chunk_items) * 100
                    log_info(f"         📈 청크 내 진행률: {chunk_progress:.0f}% ({item_idx + 1}/{total_chunk_items})")
                elif total_chunk_items <= 20 and (item_idx + 1) % 5 == 0:
                    log_info(f"         📋 처리 중: {item_idx + 1}/{total_chunk_items} 항목")
                
                input_text = row[0]
                total_count = row[1]
                created_at = row[2]
                
                # HCX 분류 처리
                log_info(f"         🤖 HCX API 호출: {input_text[:50]}...")
                keyword_categories = self.hcx_service.classify_education_question(input_text)
                
                # 🚦 API 호출 간 짧은 지연 추가 (Rate Limiting 방지)
                time.sleep(0.1)  # 100ms 지연
                
                # 키워드-카테고리 처리
                for item in keyword_categories:
                    keyword = item.get("keyword", "").strip()
                    categories = item.get("categories", ["기타"])
                    
                    if not keyword:
                        continue
                    
                    # 🔧 키워드 길이 제한 (데이터베이스 컬럼 크기 고려)
                    # 키워드가 너무 길면 적절히 줄입니다
                    if len(keyword) > 100:  # VARCHAR(100) 가정 - 사용자 변경 반영
                        log_warning(f"         ⚠️ 키워드 길이 초과 ({len(keyword)}자), 요약으로 대체: {keyword[:50]}...")
                        # 키워드가 너무 길면 원본 질문의 앞부분으로 대체
                        keyword = input_text[:95] + "..." if len(input_text) > 95 else input_text
                        if len(keyword) > 100:
                            keyword = keyword[:97] + "..."
                    
                    # 빈 키워드나 유효하지 않은 키워드 체크
                    if not keyword or keyword.strip() == "" or keyword.strip() == "기타":
                        # 원본 질문에서 의미있는 키워드 추출 시도
                        meaningful_keyword = self._extract_simple_keyword(input_text)
                        keyword = meaningful_keyword if meaningful_keyword else "기타"
                        log_info(f"         🔄 키워드 보완: '{keyword}'")
                    
                    for category_name in categories:
                        category_id = category_cache.get(str(category_name).strip())
                        if not category_id:
                            continue
                        
                        chunk_batch_data.append({
                            query_column: input_text,
                            "keyword": keyword,
                            "category_id": category_id,
                            "query_count": total_count,
                            "created_at": created_at,
                            "batch_created_at": self.batch_created_at
                        })
                        
                        chunk_processed += 1
                        log_info(f"         ✅ 데이터 추가: {keyword} - {category_name}")
                        
                        # 통계 업데이트 (안전하게)
                        try:
                            with lock:
                                if 'category_distribution' in stats:
                                    stats['category_distribution'][str(category_name)] = \
                                        stats['category_distribution'].get(str(category_name), 0) + 1
                        except Exception as stats_error:
                            # 통계 업데이트 실패는 무시 (핵심 기능에 영향 없음)
                            pass
                
            except Exception as e:
                log_error(f"         ❌ 청크 내 항목 처리 실패: {input_text} | 오류: {e}")
                continue
        
        log_info(f"      ✅ 청크 내부 처리 완료: {chunk_processed}개 처리, {chunk_skipped}개 스킵")
        return chunk_processed, chunk_skipped, chunk_batch_data

    async def _build_duplicate_cache(self, start_date: str = None, end_date: str = None) -> Tuple[set, str]:
        """중복 체크 캐시를 구축합니다."""
        log_info("🔍 기존 데이터 중복 체크용 캐시 생성 중...")
        
        try:
            schema_query = self.queries.get_table_schema("admin_chat_keywords")
            schema = await self.db_manager.execute_query(schema_query)
            available_columns = [row[0] for row in schema]
            
            # 컬럼명 매핑
            query_column = self._determine_query_column(available_columns)
            
            # 기존 데이터 조회 - 날짜 범위가 있는 경우에만 조회
            if start_date and end_date:
                existing_data_query = self.queries.get_existing_keywords_cache(start_date, end_date)
                existing_result = await self.db_manager.execute_query(existing_data_query)
                existing_cache = {row[0] for row in existing_result}
                log_info(f"✅ 기존 데이터 {len(existing_cache)}개 캐시 완료 ({start_date} ~ {end_date})")
            else:
                # 날짜 범위가 없는 경우 빈 캐시 사용
                existing_cache = set()
                log_info("ℹ️ 날짜 범위 없음, 빈 캐시로 시작")
            
            return existing_cache, query_column
            
        except Exception as e:
            log_warning(f"⚠️ 기존 데이터 캐시 생성 실패, 빈 캐시로 시작: {e}")
            return set(), "query_text"

    def _normalize_date_for_cache(self, created_at):
        """
        중복 체크를 위한 날짜 정규화 함수
        다양한 날짜 형식을 'YYYY-MM-DD' 형식으로 통일합니다.
        
        Args:
            created_at: datetime, date, str 중 하나의 형식
            
        Returns:
            str: 'YYYY-MM-DD' 형식의 날짜 문자열
        """
        try:
            from datetime import datetime, date
            
            # 1. datetime 객체인 경우
            if isinstance(created_at, datetime):
                return created_at.strftime('%Y-%m-%d')
            
            # 2. date 객체인 경우
            if isinstance(created_at, date):
                return created_at.strftime('%Y-%m-%d')
            
            # 3. 문자열인 경우
            if isinstance(created_at, str):
                # 이미 YYYY-MM-DD 형식인지 확인
                if len(created_at) >= 10 and created_at[:10].count('-') == 2:
                    return created_at[:10]
                
                # 다른 형식 시도
                try:
                    # 'YYYY-MM-DD HH:MM:SS' 형식 시도
                    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass
                
                try:
                    # 'YYYY-MM-DD' 형식 시도
                    dt = datetime.strptime(created_at, '%Y-%m-%d')
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            
            # 4. hasattr를 이용한 기존 방식 (fallback)
            if hasattr(created_at, 'strftime'):
                return created_at.strftime('%Y-%m-%d')
            
            # 5. 최후의 수단: 문자열 변환 후 앞 10자리
            return str(created_at)[:10]
            
        except Exception as e:
            log_warning(f"⚠️ 날짜 정규화 실패: {created_at} -> {e}, 기본값 사용")
            # 에러 발생 시 기본값
            return str(created_at)[:10] if created_at else "1970-01-01" 