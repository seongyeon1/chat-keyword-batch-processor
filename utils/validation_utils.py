"""
유효성 검사 유틸리티 모듈 - 데이터 검증 관련 공통 기능을 제공합니다.
"""

import re
import os
import urllib.parse
from typing import Dict, Any, List


class ValidationUtils:
    """유효성 검사 관련 유틸리티 클래스"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        이메일 주소 형식을 검증합니다.
        
        Args:
            email (str): 검증할 이메일 주소
            
        Returns:
            bool: 유효한 이메일 형식인지 여부
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        파일 경로의 유효성을 검증합니다.
        
        Args:
            file_path (str): 검증할 파일 경로
            
        Returns:
            bool: 유효한 파일 경로인지 여부
        """
        try:
            # 경로가 존재하고 파일인지 확인
            return os.path.isfile(file_path)
        except (OSError, TypeError):
            return False
    
    @staticmethod
    def validate_directory_path(dir_path: str) -> bool:
        """
        디렉토리 경로의 유효성을 검증합니다.
        
        Args:
            dir_path (str): 검증할 디렉토리 경로
            
        Returns:
            bool: 유효한 디렉토리 경로인지 여부
        """
        try:
            return os.path.isdir(dir_path)
        except (OSError, TypeError):
            return False
    
    @staticmethod
    def validate_database_url(db_url: str) -> bool:
        """
        데이터베이스 URL 형식을 검증합니다.
        
        Args:
            db_url (str): 검증할 데이터베이스 URL
            
        Returns:
            bool: 유효한 데이터베이스 URL인지 여부
        """
        try:
            parsed = urllib.parse.urlparse(db_url)
            # 스키마와 호스트가 있는지 확인
            return parsed.scheme and parsed.hostname
        except Exception:
            return False
    
    @staticmethod
    def validate_keyword_category_data(data: List[Dict[str, Any]]) -> bool:
        """
        키워드-카테고리 데이터 구조를 검증합니다.
        
        Args:
            data (List[Dict[str, Any]]): 검증할 키워드-카테고리 데이터
            
        Returns:
            bool: 유효한 데이터 구조인지 여부
        """
        if not isinstance(data, list):
            return False
        
        for item in data:
            if not isinstance(item, dict):
                return False
            
            # 필수 키 존재 확인
            if 'keyword' not in item or 'categories' not in item:
                return False
            
            # keyword는 문자열
            if not isinstance(item['keyword'], str):
                return False
            
            # categories는 리스트
            if not isinstance(item['categories'], list):
                return False
            
            # categories 내의 모든 항목이 문자열인지 확인
            for category in item['categories']:
                if not isinstance(category, str):
                    return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        파일명을 안전하게 만듭니다.
        
        Args:
            filename (str): 원본 파일명
            
        Returns:
            str: 안전한 파일명
        """
        # 위험한 문자들을 제거하거나 대체
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 공백을 언더스코어로 대체
        filename = filename.replace(' ', '_')
        
        # 연속된 언더스코어를 하나로 줄임
        filename = re.sub(r'_+', '_', filename)
        
        # 앞뒤 언더스코어 제거
        filename = filename.strip('_')
        
        return filename
    
    @staticmethod
    def validate_positive_integer(value: Any) -> bool:
        """
        양의 정수인지 검증합니다.
        
        Args:
            value (Any): 검증할 값
            
        Returns:
            bool: 양의 정수인지 여부
        """
        try:
            int_value = int(value)
            return int_value > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_port_number(port: Any) -> bool:
        """
        유효한 포트 번호인지 검증합니다.
        
        Args:
            port (Any): 검증할 포트 번호
            
        Returns:
            bool: 유효한 포트 번호인지 여부
        """
        try:
            port_int = int(port)
            return 1 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_non_empty_string(value: Any) -> bool:
        """
        비어있지 않은 문자열인지 검증합니다.
        
        Args:
            value (Any): 검증할 값
            
        Returns:
            bool: 비어있지 않은 문자열인지 여부
        """
        return isinstance(value, str) and len(value.strip()) > 0
    
    @staticmethod
    def validate_string_list(value: Any) -> bool:
        """
        문자열 리스트인지 검증합니다.
        
        Args:
            value (Any): 검증할 값
            
        Returns:
            bool: 문자열 리스트인지 여부
        """
        if not isinstance(value, list):
            return False
        
        return all(isinstance(item, str) for item in value) 