"""
로깅 유틸리티 모듈 - 통합 로깅 시스템을 제공합니다.
"""

import logging
import logging.handlers
import sys
from typing import Optional
from core.config import Config, LogConfig


class Logger:
    """통합 로깅 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config = None
            self.logger = None
            self._initialized = True
    
    def setup(self, config: Optional[LogConfig] = None):
        """로깅 시스템을 설정합니다."""
        if config is None:
            config = Config().log
        
        self.config = config
        
        # 기본 로거 설정
        self.logger = logging.getLogger("batch_keywords")
        self.logger.setLevel(getattr(logging, config.log_level))
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 포매터 설정
        formatter = logging.Formatter(
            fmt=config.log_format,
            datefmt=config.date_format
        )
        
        # 🖥️ 콘솔 핸들러 설정
        if config.console_log:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.log_level))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 📁 파일 핸들러 설정 (회전 로그)
        if config.file_log:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=config.log_file_path,
                maxBytes=config.max_log_size_mb * 1024 * 1024,  # MB to bytes
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, config.log_level))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 루트 로거 전파 방지 (중복 출력 방지)
        self.logger.propagate = False
        
        self.info("🚀 로깅 시스템 초기화 완료")
        self.info(f"📊 로그 레벨: {config.log_level}")
        self.info(f"📁 로그 파일: {config.log_file_path}")
        self.info(f"🖥️ 콘솔 출력: {config.console_log}")
        self.info(f"📄 파일 출력: {config.file_log}")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """특정 이름의 로거를 반환합니다."""
        if name:
            return logging.getLogger(f"batch_keywords.{name}")
        return self.logger
    
    def debug(self, message: str):
        """디버그 로그"""
        if self.logger:
            self.logger.debug(message)
    
    def info(self, message: str):
        """정보 로그"""
        if self.logger:
            self.logger.info(message)
    
    def warning(self, message: str):
        """경고 로그"""
        if self.logger:
            self.logger.warning(message)
    
    def error(self, message: str):
        """오류 로그"""
        if self.logger:
            self.logger.error(message)
    
    def critical(self, message: str):
        """치명적 오류 로그"""
        if self.logger:
            self.logger.critical(message)


# 전역 로거 인스턴스
logger = Logger()


def setup_logging(config: Optional[LogConfig] = None):
    """로깅 시스템을 설정합니다."""
    logger.setup(config)


def get_logger(name: str = None) -> logging.Logger:
    """로거를 반환합니다."""
    return logger.get_logger(name)


# 편의 함수들
def log_info(message: str):
    """정보 로그 출력"""
    logger.info(message)


def log_warning(message: str):
    """경고 로그 출력"""
    logger.warning(message)


def log_error(message: str):
    """오류 로그 출력"""
    logger.error(message)


def log_debug(message: str):
    """디버그 로그 출력"""
    logger.debug(message)


def log_critical(message: str):
    """치명적 오류 로그 출력"""
    logger.critical(message) 