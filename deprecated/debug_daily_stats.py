#!/usr/bin/env python3
"""
일별 통계 비교 디버그 스크립트
"""

import pandas as pd
import sys
import asyncio
sys.path.append('/app')

from core.database import DatabaseManager
from core.config import Config
from queries.batch_queries import BatchQueries

async def check_daily_stats():
    config = Config()
    db_manager = DatabaseManager(config.database)
    
    try:
        print('=== 원본 채팅 데이터 일별 통계 ===')
        # 원본 채팅 데이터 일별 통계
        query = BatchQueries.get_total_chattings_by_date('2025-06-11', '2025-06-20')
        rows = await db_manager.execute_query(query)
        
        original_stats = {}
        for row in rows:
            date_str = str(row[0])
            unique_questions = row[1]
            total_messages = row[2]
            original_stats[date_str] = {'unique': unique_questions, 'total': total_messages}
            print(f'{date_str}: 고유질문 {unique_questions:,}개, 총메시지 {total_messages:,}개')
        
        print('\n=== 분류된 키워드 데이터 일별 통계 ===')
        # 분류된 데이터 일별 통계
        classify_query = BatchQueries.classify_chat_keywords_by_date('2025-06-11', '2025-06-20')
        classified_rows = await db_manager.execute_query(classify_query)
        
        print(f'분류된 데이터 총 {len(classified_rows):,}개 레코드')
        
        # DataFrame으로 변환하여 일별 통계 계산
        df = pd.DataFrame(classified_rows, columns=['category_name', 'query_text', 'keyword', 'created_at', 'query_count'])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # 일별 통계
        daily_stats = df.groupby('date').agg({
            'query_text': 'count',          # 분류된 레코드 수
            'query_count': 'sum'            # 총 질문 횟수
        }).reset_index()
        
        # 고유 질문 수 계산
        unique_daily = df.groupby('date')['query_text'].nunique().reset_index()
        unique_daily.columns = ['date', 'unique_questions']
        
        # 병합
        daily_final = daily_stats.merge(unique_daily, on='date')
        
        classified_stats = {}
        for _, row in daily_final.iterrows():
            date_str = str(row['date'])
            classified_stats[date_str] = {
                'records': row['query_text'],
                'unique': row['unique_questions'], 
                'total_count': row['query_count']
            }
            print(f'{date_str}: 분류레코드 {row["query_text"]:,}개, 고유질문 {row["unique_questions"]:,}개, 총질문횟수 {row["query_count"]:,}회')
        
        print('\n=== 비교 결과 ===')
        all_dates = set(original_stats.keys()) | set(classified_stats.keys())
        for date_str in sorted(all_dates):
            orig = original_stats.get(date_str, {})
            classified = classified_stats.get(date_str, {})
            
            print(f'\n📅 {date_str}:')
            print(f'  원본 고유질문: {orig.get("unique", 0):,}개')
            print(f'  분류 고유질문: {classified.get("unique", 0):,}개')
            print(f'  분류 레코드수: {classified.get("records", 0):,}개')
            
            if orig.get("unique", 0) != classified.get("unique", 0):
                missing = orig.get("unique", 0) - classified.get("unique", 0)
                print(f'  ⚠️ 차이: {missing:,}개 질문이 누락됨')
        
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_daily_stats()) 