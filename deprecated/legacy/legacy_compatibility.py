"""
기존 코드와의 호환성을 위한 래퍼 모듈
- 기존 함수들을 새로운 서비스 기반으로 리다이렉트
- 하위 호환성 보장
"""

# 기존 database.py 함수들 호환성
from core.database import get_selection_from_db_text_, insert_data_to_db_text

# 기존 hcx_client.py 함수들 호환성  
from services.hcx_service import classify_education_question

# 기존 email_notifier.py 클래스 호환성
from services.email_service import EmailService as EmailNotifier

__all__ = [
    'get_selection_from_db_text_',
    'insert_data_to_db_text', 
    'classify_education_question',
    'EmailNotifier'
] 