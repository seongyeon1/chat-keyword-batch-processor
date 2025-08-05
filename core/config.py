"""
설정 관리 모듈 - 환경변수와 기본 설정을 관리합니다.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

# 환경변수 로딩을 위한 dotenv 지원
try:
    from dotenv import load_dotenv
    # .env 파일이 존재하면 로드
    if os.path.exists('.env'):
        load_dotenv('.env')
    elif os.path.exists('/app/.env'):
        load_dotenv('/app/.env')
except ImportError:
    # dotenv가 없어도 계속 진행
    pass


@dataclass
class ParallelConfig:
    """병렬 처리 설정"""
    max_workers: int = 2  # 최대 워커 수
    chunk_size: int = 100  # 배치당 처리 크기
    concurrent_dates: int = 3  # 동시 처리 날짜 수
    async_batch_size: int = 25  # 비동기 배치 크기
    enable_parallel_dates: bool = True  # 날짜별 병렬 처리 활성화
    enable_parallel_chunks: bool = True  # 청크별 병렬 처리 활성화
    
    def __post_init__(self):
        # 환경변수에서 설정 읽기
        self.max_workers = int(os.getenv("PARALLEL_MAX_WORKERS", self.max_workers))
        self.chunk_size = int(os.getenv("PARALLEL_CHUNK_SIZE", self.chunk_size))
        self.concurrent_dates = int(os.getenv("PARALLEL_CONCURRENT_DATES", self.concurrent_dates))
        self.async_batch_size = int(os.getenv("PARALLEL_ASYNC_BATCH_SIZE", self.async_batch_size))
        self.enable_parallel_dates = os.getenv("PARALLEL_ENABLE_DATES", "true").lower() == "true"
        self.enable_parallel_chunks = os.getenv("PARALLEL_ENABLE_CHUNKS", "true").lower() == "true"


@dataclass
class BatchConfig:
    """배치 처리 설정"""
    batch_size: int = 25
    classification_batch_size: int = 5
    default_target_date: str = None
    max_retry_attempts: int = 3
    retry_delay: int = 1
    timeout_seconds: int = 300
    
    # 🆕 카테고리 설정 - 환경변수로 설정 가능
    default_category_id: int = 11  # 기본 카테고리 ID (미분류)
    exclude_category_ids: List[int] = None  # 제외할 카테고리 ID 목록
    
    def __post_init__(self):
        if self.default_target_date is None:
            self.default_target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 환경변수에서 설정 읽기
        self.batch_size = int(os.getenv("BATCH_SIZE", self.batch_size))
        self.classification_batch_size = int(os.getenv("CLASSIFICATION_BATCH_SIZE", self.classification_batch_size))
        self.max_retry_attempts = int(os.getenv("BATCH_MAX_RETRY", self.max_retry_attempts))
        self.retry_delay = int(os.getenv("BATCH_RETRY_DELAY", self.retry_delay))
        self.timeout_seconds = int(os.getenv("BATCH_TIMEOUT", self.timeout_seconds))
        
        # 🆕 카테고리 설정을 환경변수에서 읽기
        self.default_category_id = int(os.getenv("BATCH_DEFAULT_CATEGORY_ID", self.default_category_id))
        
        # 제외할 카테고리 ID 목록
        exclude_ids_str = os.getenv("BATCH_EXCLUDE_CATEGORY_IDS", "")
        if exclude_ids_str:
            self.exclude_category_ids = [int(x.strip()) for x in exclude_ids_str.split(",") if x.strip()]
        else:
            self.exclude_category_ids = []


@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    engine_url: str = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # 🆕 스키마 설정 - 테이블명과 컬럼명을 환경변수로 설정 가능
    table_chattings: str = "chattings"
    table_chat_keywords: str = "admin_chat_keywords"
    table_categories: str = "admin_categories"
    
    column_input_text: str = "input_text"
    column_chatting_pk: str = "chatting_pk"
    column_created_at: str = "created_at"
    column_query_text: str = "query_text"
    column_keyword: str = "keyword"
    column_category_id: str = "category_id"
    column_query_count: str = "query_count"
    column_batch_created_at: str = "batch_created_at"
    column_category_name: str = "category_name"
    
    def __post_init__(self):
        # 환경변수에서 데이터베이스 URL 읽기
        if not self.engine_url:
            self.engine_url = os.getenv("ENGINE_FOR_SQLALCHEMY")
        
        # 여전히 설정되지 않은 경우 기본값 설정 (개발용)
        if not self.engine_url:
            # 개발 환경용 기본 설정 - 실제 운영에서는 환경변수 필수
            print("⚠️ ENGINE_FOR_SQLALCHEMY 환경변수가 설정되지 않았습니다.")
            print("💡 개발 환경용 기본 데이터베이스 설정을 사용합니다.")
            # 충남교육청 특정 값 제거하고 일반적인 설정으로 변경
            self.engine_url = "mysql+pymysql://user:password@localhost:3306/database"
        
        # 환경변수에서 추가 설정 읽기
        self.pool_size = int(os.getenv("DB_POOL_SIZE", self.pool_size))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", self.max_overflow))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", self.pool_timeout))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", self.pool_recycle))
        
        # 🆕 스키마 설정을 환경변수에서 읽기
        self.table_chattings = os.getenv("DB_TABLE_CHATTINGS", self.table_chattings)
        self.table_chat_keywords = os.getenv("DB_TABLE_CHAT_KEYWORDS", self.table_chat_keywords)
        self.table_categories = os.getenv("DB_TABLE_CATEGORIES", self.table_categories)
        
        self.column_input_text = os.getenv("DB_COLUMN_INPUT_TEXT", self.column_input_text)
        self.column_chatting_pk = os.getenv("DB_COLUMN_CHATTING_PK", self.column_chatting_pk)
        self.column_created_at = os.getenv("DB_COLUMN_CREATED_AT", self.column_created_at)
        self.column_query_text = os.getenv("DB_COLUMN_QUERY_TEXT", self.column_query_text)
        self.column_keyword = os.getenv("DB_COLUMN_KEYWORD", self.column_keyword)
        self.column_category_id = os.getenv("DB_COLUMN_CATEGORY_ID", self.column_category_id)
        self.column_query_count = os.getenv("DB_COLUMN_QUERY_COUNT", self.column_query_count)
        self.column_batch_created_at = os.getenv("DB_COLUMN_BATCH_CREATED_AT", self.column_batch_created_at)
        self.column_category_name = os.getenv("DB_COLUMN_CATEGORY_NAME", self.column_category_name)
        
        # 설정 검증
        if not self.engine_url or not self.engine_url.startswith(("mysql", "postgresql", "sqlite")):
            raise ValueError(f"올바르지 않은 데이터베이스 URL입니다: {self.engine_url}")


@dataclass
class HCXConfig:
    """HCX API 설정"""
    api_key: str = None
    model: str = "HCX-005"
    app_type: str = "serviceapp"
    max_tokens: int = 1000
    temperature: float = 0.1
    max_retries: int = 3
    timeout: int = 30
    
    # 🚀 Rate Limiting 설정
    max_requests_per_minute: int = 30  # 분당 최대 요청 수
    min_request_interval: float = 1.0  # 최소 요청 간격 (초)
    base_delay: float = 2.0  # 기본 지연 시간 (초)
    max_delay: float = 60.0  # 최대 지연 시간 (초)
    
    def __post_init__(self):
        # 환경변수에서 설정 읽기
        self.api_key = os.getenv("HCX_CHAT_API_KEY", self.api_key)
        self.model = os.getenv("HCX_MODEL", self.model)
        self.app_type = os.getenv("HCX_APP_TYPE", self.app_type)
        self.max_tokens = int(os.getenv("HCX_MAX_TOKENS", self.max_tokens))
        self.temperature = float(os.getenv("HCX_TEMPERATURE", self.temperature))
        self.max_retries = int(os.getenv("HCX_MAX_RETRIES", self.max_retries))
        self.timeout = int(os.getenv("HCX_TIMEOUT", self.timeout))
        
        # Rate Limiting 환경변수
        self.max_requests_per_minute = int(os.getenv("HCX_MAX_REQUESTS_PER_MINUTE", self.max_requests_per_minute))
        self.min_request_interval = float(os.getenv("HCX_MIN_REQUEST_INTERVAL", self.min_request_interval))
        self.base_delay = float(os.getenv("HCX_BASE_DELAY", self.base_delay))
        self.max_delay = float(os.getenv("HCX_MAX_DELAY", self.max_delay))
        
        if not self.api_key:
            print("⚠️ HCX_CHAT_API_KEY 환경변수가 설정되지 않았습니다.")
            print("💡 HCX API 기능이 제한될 수 있습니다.")
            # API 키가 없어도 일단 진행하도록 수정
            return
        
        if not self.api_key.startswith("nv-"):
            print(f"⚠️ API 키 형식 주의: 'nv-'로 시작해야 합니다. 현재: {self.api_key[:10]}...")


@dataclass
class EmailConfig:
    """이메일 설정"""
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_emails: List[str]
    enable_email: bool = True
    email_timeout: int = 30
    max_attachment_size_mb: int = 10
    
    def __post_init__(self):
        if not all([self.smtp_server, self.smtp_port, self.sender_email, self.sender_password]):
            self.enable_email = False
            print("⚠️ 이메일 설정이 불완전하여 이메일 기능이 비활성화됩니다.")
        
        # 환경변수에서 추가 설정 읽기
        self.enable_email = os.getenv("EMAIL_ENABLED", "true").lower() == "true" and self.enable_email
        self.email_timeout = int(os.getenv("EMAIL_TIMEOUT", self.email_timeout))
        self.max_attachment_size_mb = int(os.getenv("EMAIL_MAX_ATTACHMENT_MB", self.max_attachment_size_mb))


@dataclass
class ReportConfig:
    """보고서 설정"""
    output_dir: str = "reports"
    excel_engine: str = "openpyxl"
    auto_cleanup_days: int = 30
    enable_auto_cleanup: bool = True
    
    def __post_init__(self):
        # 환경변수에서 설정 읽기
        self.output_dir = os.getenv("REPORT_OUTPUT_DIR", self.output_dir)
        self.excel_engine = os.getenv("EXCEL_ENGINE", self.excel_engine)
        self.auto_cleanup_days = int(os.getenv("REPORT_CLEANUP_DAYS", self.auto_cleanup_days))
        self.enable_auto_cleanup = os.getenv("REPORT_AUTO_CLEANUP", "true").lower() == "true"


@dataclass
class DockerConfig:
    """도커 환경 설정"""
    is_docker: bool = False
    container_name: str = "keyword-batch"
    log_level: str = "INFO"
    healthcheck_interval: int = 30
    
    def __post_init__(self):
        # 도커 환경 감지
        self.is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER", "false").lower() == "true"
        self.container_name = os.getenv("CONTAINER_NAME", self.container_name)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.healthcheck_interval = int(os.getenv("HEALTHCHECK_INTERVAL", self.healthcheck_interval))


@dataclass
class LogConfig:
    """로깅 설정"""
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "batch_keywords.log"
    max_log_size_mb: int = 100  # 로그 파일 최대 크기 (MB)
    backup_count: int = 5  # 백업 파일 개수
    console_log: bool = True  # 콘솔 출력 여부
    file_log: bool = True  # 파일 출력 여부
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    def __post_init__(self):
        # 환경변수에서 설정 읽기
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()
        self.log_dir = os.getenv("LOG_DIR", self.log_dir)
        self.log_file = os.getenv("LOG_FILE", self.log_file)
        self.max_log_size_mb = int(os.getenv("MAX_LOG_SIZE_MB", self.max_log_size_mb))
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", self.backup_count))
        self.console_log = os.getenv("CONSOLE_LOG", "true").lower() == "true"
        self.file_log = os.getenv("FILE_LOG", "true").lower() == "true"
        
        # 로그 디렉토리 생성
        if self.file_log:
            os.makedirs(self.log_dir, exist_ok=True)
    
    @property
    def log_file_path(self) -> str:
        """전체 로그 파일 경로를 반환합니다."""
        return os.path.join(self.log_dir, self.log_file)


@dataclass
class OrganizationConfig:
    """조직 설정"""
    name: str = "Default Organization"
    code: str = "DEFAULT"
    timezone: str = "Asia/Seoul"
    language: str = "ko"
    
    def __post_init__(self):
        # 환경변수에서 설정 읽기
        self.name = os.getenv("ORG_NAME", self.name)
        self.code = os.getenv("ORG_CODE", self.code)
        self.timezone = os.getenv("ORG_TIMEZONE", self.timezone)
        self.language = os.getenv("ORG_LANGUAGE", self.language)


class Config:
    """통합 설정 관리 클래스"""
    
    def __init__(self):
        self._parallel = None
        self._batch = None
        self._database = None
        self._hcx = None
        self._email = None
        self._report = None
        self._docker = None
        self._log = None
        self._organization = None
    
    @property
    def parallel(self) -> ParallelConfig:
        """병렬 처리 설정"""
        if self._parallel is None:
            self._parallel = ParallelConfig()
        return self._parallel
    
    @property
    def batch(self) -> BatchConfig:
        """배치 처리 설정"""
        if self._batch is None:
            self._batch = BatchConfig()
        return self._batch
    
    @property
    def database(self) -> DatabaseConfig:
        """데이터베이스 설정"""
        if self._database is None:
            self._database = DatabaseConfig()
        return self._database
    
    @property
    def hcx(self) -> HCXConfig:
        """HCX API 설정"""
        if self._hcx is None:
            self._hcx = HCXConfig()
        return self._hcx
    
    @property
    def email(self) -> EmailConfig:
        """이메일 설정"""
        if self._email is None:
            recipient_emails_str = os.getenv("RECIPIENT_EMAILS", "")
            recipient_emails = [email.strip() for email in recipient_emails_str.split(",") if email.strip()]
            
            self._email = EmailConfig(
                smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                sender_email=os.getenv("SENDER_EMAIL"),
                sender_password=os.getenv("SENDER_PASSWORD"),
                recipient_emails=recipient_emails
            )
        return self._email
    
    @property
    def report(self) -> ReportConfig:
        """보고서 설정"""
        if self._report is None:
            self._report = ReportConfig()
        return self._report
    
    @property
    def docker(self) -> DockerConfig:
        """도커 환경 설정"""
        if self._docker is None:
            self._docker = DockerConfig()
        return self._docker
    
    @property
    def log(self) -> LogConfig:
        """로깅 설정"""
        if self._log is None:
            self._log = LogConfig()
        return self._log

    @property
    def organization(self) -> OrganizationConfig:
        """조직 설정"""
        if self._organization is None:
            self._organization = OrganizationConfig()
        return self._organization

    def validate_all(self) -> bool:
        """모든 설정의 유효성을 검사합니다."""
        try:
            # 데이터베이스 설정 검증 (필수)
            db_config = self.database
            print(f"✅ 데이터베이스 설정 확인: {db_config.engine_url[:50]}...")
            
            # HCX API 설정 검증 (경고만)
            hcx_config = self.hcx
            if not hcx_config.api_key:
                print("⚠️ HCX API 키가 설정되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
            else:
                print(f"✅ HCX API 설정 확인: {hcx_config.api_key[:10]}...")
            
            # 이메일 설정 검증 (선택적)
            if not self.email.enable_email:
                print("⚠️ 이메일 설정이 불완전합니다. 이메일 기능이 비활성화됩니다.")
            else:
                print(f"✅ 이메일 설정 확인: {len(self.email.recipient_emails)}명의 수신자")
            
            return True
        except Exception as e:
            print(f"❌ 설정 유효성 검사 실패: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """현재 설정 요약을 반환합니다."""
        return {
            "parallel": {
                "max_workers": self.parallel.max_workers,
                "concurrent_dates": self.parallel.concurrent_dates,
                "enable_parallel_dates": self.parallel.enable_parallel_dates,
                "enable_parallel_chunks": self.parallel.enable_parallel_chunks
            },
            "batch": {
                "batch_size": self.batch.batch_size,
                "classification_batch_size": self.batch.classification_batch_size,
                "timeout_seconds": self.batch.timeout_seconds
            },
            "email": {
                "enabled": self.email.enable_email,
                "recipients": len(self.email.recipient_emails)
            },
            "docker": {
                "is_docker": self.docker.is_docker,
                "container_name": self.docker.container_name,
                "log_level": self.docker.log_level
            }
        } 