"""
엑셀 서비스 모듈 - 엑셀 보고서 생성과 관리를 담당합니다.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime

from core.config import ReportConfig, DatabaseConfig
from core.database import DatabaseManager
from core.exceptions import ExcelError, DatabaseError


class ExcelService:
    """엑셀 보고서 생성 서비스 클래스"""
    
    def __init__(self, report_config: ReportConfig, db_manager: DatabaseManager):
        self.report_config = report_config
        self.db_manager = db_manager
    
    async def generate_report(self, start_date: str, end_date: str) -> Tuple[str, Dict[str, Any]]:
        """
        채팅 키워드 분류 보고서를 생성합니다.
        
        Args:
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            Tuple[str, Dict[str, Any]]: (파일 경로, 요약 통계)
        """
        try:
            # 날짜 유효성 검사
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                raise ExcelError("시작일이 종료일보다 늦을 수 없습니다.")
            
            # 출력 디렉토리 생성
            os.makedirs(self.report_config.output_dir, exist_ok=True)
            
            # 데이터 조회
            print("🔍 데이터베이스에서 분류 데이터 조회 중...")
            # rows = await self.db_manager.call_procedure(
            #     "classify_chat_keywords_by_date",
            #     {"start_date": start_date, "end_date": end_date}
            # )
            query=f"""SELECT 
  t.category_name AS category_name, 
  c.query_text, 
  c.keyword, 
  c.created_at, 
  c.query_count 
FROM admin_chat_keywords AS c
LEFT JOIN admin_categories t
  ON t.category_id = c.category_id
WHERE c.created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59';
            """
            rows = await self.db_manager.execute_query(query)
            
            if not rows:
                raise ExcelError(f"해당 기간({start_date} ~ {end_date})에 분류된 데이터가 없습니다.")
            
            print(f"✅ {len(rows)}개 레코드 조회 완료")
            
            # 데이터를 DataFrame으로 변환
            df = self._create_dataframe(rows)
            
            # 요약 통계 생성
            summary_stats = self._generate_summary_statistics(df, start_date, end_date)
            
            # 엑셀 파일 생성
            excel_filename = self._create_excel_file(df, summary_stats, start_date, end_date)
            
            return excel_filename, summary_stats
            
        except Exception as e:
            if isinstance(e, ExcelError):
                raise
            raise ExcelError(f"보고서 생성 중 오류 발생: {e}")
    
    def _create_dataframe(self, rows: List[tuple]) -> pd.DataFrame:
        """데이터를 DataFrame으로 변환합니다."""
        # 프로시저 실제 반환 컬럼: category_name, query_text, keyword, created_at, query_count
        columns = ['category_name', 'query_text', 'keyword', 'created_at','query_count']
        df = pd.DataFrame(rows, columns=columns)
        
        # 데이터 전처리
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date

        # date를 기준으로 query_text 중복 제거
        # 중복제거 방법: 각 query_text 별로 가지고 있는 category_name 중 '기타'를 제외한 최빈 값을 사용, 만약 모두 기타라면 기타로 설정
        def get_most_common_non_etc(x):
            # '기타'를 제외한 카테고리만 필터링
            non_etc = x[x != '기타']
            if len(non_etc) > 0:
                # '기타'가 아닌 카테고리 중 최빈값 반환
                return non_etc.mode()[0]
            # 모두 '기타'인 경우 '기타' 반환
            return '기타'

        # 임시로 category_name 계산
        temp_df = df.groupby(['date', 'query_text'])['category_name'].apply(get_most_common_non_etc).reset_index()
        
        # 원본 데이터에서 해당하는 category_name을 가진 첫 번째 행의 keyword 가져오기
        result = []
        for _, row in temp_df.iterrows():
            date, query_text, category = row['date'], row['query_text'], row['category_name']
            matching_row = df[
                (df['date'] == date) & 
                (df['query_text'] == query_text) & 
                (df['category_name'] == category)
            ].iloc[0]
            
            result.append({
                'date': date,
                'query_text': query_text,
                'category_name': category,
                'query_count': matching_row['query_count'],
                'keyword': matching_row['keyword'],
                'created_at': matching_row['created_at']
            })
            
        df = pd.DataFrame(result)

        return df
    
    def _generate_summary_statistics(self, df: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, Any]:
        """요약 통계 정보를 생성합니다."""
        summary = {
            'period': f"{start_date} ~ {end_date}",
            'total_records': len(df),
            'unique_questions': df['query_text'].nunique(),
            'unique_keywords': df['keyword'].nunique(),
            'total_query_count': df['query_count'].sum(),
        }
        
        # 카테고리별 통계
        category_stats = df.groupby('category_name').agg({
            'query_text': 'count',
            'query_count': 'sum',
            'keyword': 'nunique'
        }).reset_index()
        category_stats.columns = ['category_name', 'record_count', 'total_queries', 'unique_keywords']
        category_stats = category_stats.sort_values('record_count', ascending=False)
        
        summary['category_distribution'] = category_stats.to_dict('records')
        
        # 일별 통계 - 더 상세하게 계산
        daily_stats = df.groupby('date').agg({
            'query_text': ['count', 'nunique'],  # 레코드 수와 고유 질문 수
            'query_count': 'sum',               # 총 질문 횟수
            'keyword': 'nunique'                # 고유 키워드 수
        }).reset_index()
        
        # 컬럼명 평평화
        daily_stats.columns = ['date', 'record_count', 'unique_questions', 'total_queries', 'unique_keywords']
        daily_stats['date'] = daily_stats['date'].astype(str)
        
        summary['daily_distribution'] = daily_stats.to_dict('records')
        
        # 상위 키워드
        keyword_stats = df.groupby('keyword').agg({
            'query_text': 'count',
            'query_count': 'sum'
        }).reset_index()
        keyword_stats.columns = ['keyword', 'record_count', 'total_queries']
        keyword_stats = keyword_stats.sort_values('record_count', ascending=False).head(10)
        
        summary['top_keywords'] = keyword_stats.to_dict('records')
        
        # 상위 질문
        question_stats = df.groupby('query_text').agg({
            'query_count': 'first',
            'keyword': lambda x: ', '.join(x.unique()[:3])  # 최대 3개 키워드만
        }).reset_index()
        question_stats.columns = ['query_text', 'query_count', 'keywords']
        question_stats = question_stats.sort_values('query_count', ascending=False).head(10)
        
        summary['top_questions'] = question_stats.to_dict('records')
        
        return summary
    
    def _create_excel_file(self, df: pd.DataFrame, summary_stats: Dict[str, Any], 
                          start_date: str, end_date: str) -> str:
        """엑셀 보고서 파일을 생성합니다."""
        from utils.logger import log_info, log_warning, log_error
        
        # 🔧 DataFrame 유효성 검사
        if df.empty:
            log_warning("DataFrame이 비어있습니다. 기본 빈 보고서를 생성합니다.")
        
        log_info(f"엑셀 파일 생성 시작: DataFrame 크기 {len(df)}행, 컬럼: {list(df.columns)}")
        
        # 파일명 생성
        if start_date == end_date:
            filename = f"채팅키워드분류보고서_{start_date}.xlsx"
        else:
            filename = f"채팅키워드분류보고서_{start_date}_to_{end_date}.xlsx"
        
        # 먼저 원래 디렉토리에 시도
        filepath = os.path.join(self.report_config.output_dir, filename)
        
        # 권한 문제가 있는 경우를 대비해 여러 경로 시도
        possible_paths = [
            filepath,  # 원래 경로
            os.path.join("/tmp", filename),  # 임시 디렉토리
            os.path.join("/app/temp", filename),  # 앱 임시 디렉토리
            filename  # 현재 디렉토리
        ]
        
        for attempt_path in possible_paths:
            try:
                # 디렉토리 생성 시도
                dir_path = os.path.dirname(attempt_path)
                if dir_path:  # 빈 문자열이 아닌 경우에만
                    os.makedirs(dir_path, exist_ok=True)
                
                log_info(f"📝 엑셀 파일 생성 시도: {attempt_path}")
                
                with pd.ExcelWriter(attempt_path, engine=self.report_config.excel_engine) as writer:
                    # 🔧 항상 최소 하나의 시트는 생성되도록 보장
                    
                    # 1. 전체 분류 데이터 (메인 시트 - 항상 생성)
                    if not df.empty and all(col in df.columns for col in ['query_text', 'keyword', 'category_name', 'query_count', 'created_at']):
                        df_export = df[['query_text', 'keyword', 'category_name', 'query_count', 'created_at']].copy()
                        df_export.columns = ['질문내용', '키워드', '카테고리', '질문횟수', '생성일시']
                        df_export.to_excel(writer, sheet_name='채팅키워드분류', index=False)
                        log_info("✅ '채팅키워드분류' 시트 생성 완료")
                    else:
                        # 빈 데이터인 경우 기본 시트 생성
                        empty_df = pd.DataFrame([['데이터 없음', '', '', 0, start_date]], 
                                              columns=['질문내용', '키워드', '카테고리', '질문횟수', '생성일시'])
                        empty_df.to_excel(writer, sheet_name='채팅키워드분류', index=False)
                        log_warning("⚠️ 빈 데이터로 기본 '채팅키워드분류' 시트 생성")
                    
                    # 2. 카테고리별 통계
                    if 'category_distribution' in summary_stats and summary_stats['category_distribution']:
                        category_df = pd.DataFrame(summary_stats['category_distribution'])
                        if not category_df.empty:
                            category_df.columns = ['카테고리', '레코드수', '총질문횟수', '고유키워드수']
                            category_df.to_excel(writer, sheet_name='카테고리별통계', index=False)
                            log_info("✅ '카테고리별통계' 시트 생성 완료")
                    
                    # 3. 일별 통계
                    if 'daily_distribution' in summary_stats and summary_stats['daily_distribution']:
                        daily_df = pd.DataFrame(summary_stats['daily_distribution'])
                        if not daily_df.empty:
                            daily_df.columns = ['날짜', '레코드수', '고유질문수', '총질문횟수', '고유키워드수']
                            daily_df.to_excel(writer, sheet_name='일별통계', index=False)
                            log_info("✅ '일별통계' 시트 생성 완료")
                    
                    # 4. 상위 키워드
                    if 'top_keywords' in summary_stats and summary_stats['top_keywords']:
                        top_keywords_df = pd.DataFrame(summary_stats['top_keywords'])
                        if not top_keywords_df.empty:
                            top_keywords_df.columns = ['키워드', '레코드수', '총질문횟수']
                            top_keywords_df.to_excel(writer, sheet_name='상위키워드', index=False)
                            log_info("✅ '상위키워드' 시트 생성 완료")
                    
                    # 5. 상위 질문
                    if 'top_questions' in summary_stats and summary_stats['top_questions']:
                        top_questions_df = pd.DataFrame(summary_stats['top_questions'])
                        if not top_questions_df.empty:
                            top_questions_df.columns = ['질문내용', '질문횟수', '관련키워드']
                            # 질문 내용이 너무 길면 자르기
                            top_questions_df['질문내용'] = top_questions_df['질문내용'].apply(
                                lambda x: x[:100] + '...' if len(str(x)) > 100 else x
                            )
                            top_questions_df.to_excel(writer, sheet_name='상위질문', index=False)
                            log_info("✅ '상위질문' 시트 생성 완료")
                    
                    # 6. 요약 정보 (항상 생성)
                    summary_df = pd.DataFrame([
                        ['조회기간', summary_stats.get('period', f"{start_date} ~ {end_date}")],
                        ['총 레코드 수', summary_stats.get('total_records', 0)],
                        ['고유 질문 수', summary_stats.get('unique_questions', 0)],
                        ['고유 키워드 수', summary_stats.get('unique_keywords', 0)],
                        ['총 질문 횟수', summary_stats.get('total_query_count', 0)],
                    ], columns=['항목', '값'])
                    summary_df.to_excel(writer, sheet_name='요약정보', index=False)
                    log_info("✅ '요약정보' 시트 생성 완료")
                
                log_info(f"✅ 엑셀 파일 생성 완료: {attempt_path}")
                
                # 성공했으면 원래 위치로 복사 시도
                if attempt_path != filepath:
                    try:
                        import shutil
                        os.makedirs(self.report_config.output_dir, exist_ok=True)
                        shutil.copy2(attempt_path, filepath)
                        log_info(f"📁 파일 복사 완료: {filepath}")
                        return filepath
                    except Exception as copy_error:
                        log_warning(f"⚠️ 파일 복사 실패 ({copy_error}), 임시 위치 사용: {attempt_path}")
                        return attempt_path
                
                return attempt_path
                
            except PermissionError as e:
                log_warning(f"❌ 권한 오류로 {attempt_path} 생성 실패: {e}")
                continue
            except Exception as e:
                log_error(f"❌ {attempt_path} 생성 실패: {e}")
                continue
        
        # 모든 경로가 실패한 경우
        raise ExcelError(f"모든 경로에서 엑셀 파일 생성 실패. 마지막 시도: {possible_paths[-1]}")
    
    def print_summary_report(self, summary_stats: Dict[str, Any], excel_filename: str):
        """콘솔에 요약 보고서를 출력합니다."""
        print(f"\n📊 채팅 키워드 분류 보고서 요약")
        print("=" * 60)
        print(f"📅 조회 기간: {summary_stats['period']}")
        print(f"📄 출력 파일: {excel_filename}")
        print(f"📈 총 레코드 수: {summary_stats['total_records']:,}개")
        print(f"🗣️ 고유 질문 수: {summary_stats['unique_questions']:,}개")
        print(f"🔑 고유 키워드 수: {summary_stats['unique_keywords']:,}개")
        print(f"💬 총 질문 횟수: {summary_stats['total_query_count']:,}회")
        
        # 카테고리별 분포
        print(f"\n📊 카테고리별 분포:")
        print("-" * 50)
        for cat_info in summary_stats['category_distribution'][:10]:  # 상위 10개만 표시
            print(f"  {cat_info['category_name']}: {cat_info['record_count']:,}개 "
                  f"(질문 {cat_info['total_queries']:,}회, 키워드 {cat_info['unique_keywords']:,}개)")
        
        # 상위 키워드
        print(f"\n🔥 상위 키워드 (레코드 기준):")
        print("-" * 50)
        for i, keyword_info in enumerate(summary_stats['top_keywords'][:10], 1):
            print(f"  {i:2d}. {keyword_info['keyword']}: {keyword_info['record_count']:,}개 "
                  f"(질문 {keyword_info['total_queries']:,}회)")
        
        print("=" * 60)
    
    def get_file_size_info(self, filepath: str) -> Dict[str, Any]:
        """파일 크기 정보를 반환합니다."""
        if not os.path.exists(filepath):
            return {"exists": False}
        
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        return {
            "exists": True,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
            "created_time": datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        } 