"""
날짜 유틸리티 모듈 - 날짜 관련 공통 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Tuple


class DateUtils:
    """날짜 관련 유틸리티 클래스"""
    
    @staticmethod
    def generate_date_range(start_date: str, end_date: str) -> List[str]:
        """
        시작일부터 종료일까지의 날짜 리스트를 생성합니다.
        
        Args:
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            List[str]: 날짜 문자열 리스트
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start > end:
            raise ValueError("시작일이 종료일보다 늦을 수 없습니다.")
        
        date_list = []
        current = start
        while current <= end:
            date_list.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return date_list
    
    @staticmethod
    def parse_date_shortcut(date_str: str) -> Tuple[str, str]:
        """
        날짜 단축어를 실제 날짜로 변환합니다.
        
        Args:
            date_str (str): 날짜 단축어 또는 날짜 문자열
            
        Returns:
            Tuple[str, str]: (시작 날짜, 종료 날짜)
        """
        today = datetime.now()
        
        shortcuts = {
            "today": lambda: (today, today),
            "yesterday": lambda: (today - timedelta(days=1), today - timedelta(days=1)),
            "this-week": lambda: DateUtils._get_week_range(today, 0),
            "last-week": lambda: DateUtils._get_week_range(today, -1),
            "this-month": lambda: DateUtils._get_month_range(today, 0),
            "last-month": lambda: DateUtils._get_month_range(today, -1),
        }
        
        if date_str in shortcuts:
            start, end = shortcuts[date_str]()
            return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
        else:
            # 일반 날짜 문자열
            return date_str, date_str
    
    @staticmethod
    def _get_week_range(reference_date: datetime, week_offset: int) -> Tuple[datetime, datetime]:
        """주간 범위를 계산합니다."""
        # 해당 주의 월요일 계산
        start = reference_date - timedelta(days=reference_date.weekday()) + timedelta(weeks=week_offset)
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_month_range(reference_date: datetime, month_offset: int) -> Tuple[datetime, datetime]:
        """월간 범위를 계산합니다."""
        if month_offset == 0:
            # 이번 달
            start = reference_date.replace(day=1)
            if reference_date.month == 12:
                next_month = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
            else:
                next_month = reference_date.replace(month=reference_date.month + 1, day=1)
            end = next_month - timedelta(days=1)
        else:
            # 지난 달
            first_this_month = reference_date.replace(day=1)
            end = first_this_month - timedelta(days=1)
            start = end.replace(day=1)
        
        return start, end
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        날짜 형식을 검증합니다.
        
        Args:
            date_str (str): 검증할 날짜 문자열
            
        Returns:
            bool: 유효한 형식인지 여부
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_yesterday() -> str:
        """어제 날짜를 반환합니다."""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    @staticmethod
    def format_duration(start_time: datetime, end_time: datetime) -> str:
        """
        시작 시간과 종료 시간을 받아 소요 시간을 포맷팅합니다.
        
        Args:
            start_time (datetime): 시작 시간
            end_time (datetime): 종료 시간
            
        Returns:
            str: 포맷팅된 소요 시간
        """
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초" 