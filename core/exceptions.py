"""
커스텀 예외 클래스들 - 프로젝트 전용 예외 정의
"""


class BatchProcessError(Exception):
    """배치 처리 관련 예외"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class DatabaseError(Exception):
    """데이터베이스 관련 예외"""
    def __init__(self, message: str, query: str = None):
        super().__init__(message)
        self.query = query


class HCXError(Exception):
    """HCX API 관련 예외"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class HCXTooManyRequestError(HCXError):
    """HCX API 요청 한도 초과 예외"""
    pass


class EmailError(Exception):
    """이메일 발송 관련 예외"""
    def __init__(self, message: str, smtp_code: int = None):
        super().__init__(message)
        self.smtp_code = smtp_code


class ExcelError(Exception):
    """엑셀 파일 처리 관련 예외"""
    pass


class ValidationError(Exception):
    """데이터 유효성 검증 예외"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field 