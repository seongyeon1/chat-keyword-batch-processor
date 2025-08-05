"""
데이터베이스 관리 모듈 - 데이터베이스 연결과 쿼리 실행을 담당합니다.
"""

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .exceptions import DatabaseError
from .config import DatabaseConfig


class DatabaseManager:
    """데이터베이스 연결 및 쿼리 실행을 관리하는 클래스"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
    
    @property
    def engine(self):
        """데이터베이스 엔진을 생성합니다."""
        if self._engine is None:
            try:
                self._engine = sqlalchemy.create_engine(self.config.engine_url, echo=False)
            except Exception as e:
                raise DatabaseError(f"데이터베이스 엔진 생성 실패: {e}")
        return self._engine
    
    @contextmanager
    def get_session(self):
        """데이터베이스 세션을 안전하게 관리합니다."""
        session = Session(self.engine)
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"데이터베이스 세션 오류: {e}")
        finally:
            session.close()
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[tuple]:
        """SELECT 쿼리를 실행하고 결과를 반환합니다."""
        try:
            with self.get_session() as session:
                if params is None:
                    params = {}
                result = session.execute(text(query), params).all()
                return result
        except Exception as e:
            raise DatabaseError(f"쿼리 실행 실패: {e}", query=query)
    
    async def execute_insert(self, query: str, params: Dict[str, Any] = None) -> bool:
        """INSERT/UPDATE/DELETE 쿼리를 실행합니다."""
        try:
            with self.get_session() as session:
                if params is None:
                    params = {}
                session.execute(text(query), params)
                session.commit()
                return True
        except Exception as e:
            raise DatabaseError(f"INSERT 쿼리 실행 실패: {e}", query=query)
    
    async def execute_batch_insert(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """배치 INSERT 쿼리를 실행합니다."""
        from utils.logger import log_info, log_warning, log_error
        
        success_count = 0
        failed_count = 0
        
        try:
            with self.get_session() as session:
                for i, original_params in enumerate(params_list):
                    try:
                        # 🔧 원본 파라미터를 복사하여 변조 방지
                        params = original_params.copy()
                        
                        # 🔧 키워드 길이 추가 검증 (안전장치)
                        if 'keyword' in params:
                            keyword = params['keyword']
                            if len(str(keyword)) > 100:
                                log_warning(f"키워드 길이 초과, 자르기: {len(str(keyword))}자 -> 100자")
                                params['keyword'] = str(keyword)[:98] + "..."
                        
                        session.execute(text(query), params)
                        success_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        log_warning(f"개별 INSERT 실패 (#{i+1}): {e}")
                        
                        # 상세 정보 출력 (디버깅용)
                        if 'keyword' in original_params:
                            log_info(f"   - 키워드: '{str(original_params['keyword'])[:50]}{'...' if len(str(original_params['keyword'])) > 50 else ''}'")
                            log_info(f"   - 키워드 길이: {len(str(original_params['keyword']))}자")
                        
                        # 🔧 심각한 DB 오류인 경우 배치 전체 중단
                        error_str = str(e).lower()
                        if any(critical_error in error_str for critical_error in [
                            'connection', 'timeout', 'server has gone away', 'lost connection'
                        ]):
                            log_error(f"심각한 DB 오류 감지, 배치 처리 중단: {e}")
                            session.rollback()
                            raise DatabaseError(f"심각한 DB 오류로 배치 처리 중단: {e}")
                
                # 🔧 트랜잭션 커밋 전 상태 확인
                if success_count > 0:
                    session.commit()
                    log_info(f"배치 INSERT 완료: {success_count}개 성공")
                else:
                    session.rollback()
                    log_warning("배치 INSERT: 성공한 레코드가 없어 롤백")
                
                if failed_count > 0:
                    log_warning(f"📊 배치 INSERT 결과: {success_count}개 성공, {failed_count}개 실패")
                
                return success_count
                
        except Exception as e:
            log_error(f"배치 INSERT 실행 실패: {e}")
            raise DatabaseError(f"배치 INSERT 실행 실패: {e}", query=query)
    
    async def call_procedure(self, procedure_name: str, params: Dict[str, Any] = None) -> List[tuple]:
        """저장 프로시저를 호출합니다."""
        if params is None:
            params = {}
        
        # 파라미터를 프로시저 호출 형식으로 변환
        param_placeholders = ', '.join([f":{key}" for key in params.keys()])
        query = f"CALL {procedure_name}({param_placeholders});"
        
        return await self.execute_query(query, params)
    
    async def get_table_schema(self, table_name: str) -> List[tuple]:
        """테이블 스키마 정보를 조회합니다."""
        query = f"DESCRIBE {table_name}"
        return await self.execute_query(query)
    
    async def check_connection(self) -> bool:
        """데이터베이스 연결 상태를 확인합니다."""
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception:
            return False


# 하위 호환성을 위한 기존 함수들
async def get_selection_from_db_text_(stm: str, params: Dict[str, Any]) -> List[tuple]:
    """기존 함수와의 호환성을 위한 래퍼 함수"""
    from .config import Config
    
    config = Config()
    db_manager = DatabaseManager(config.database)
    return await db_manager.execute_query(stm, params)


async def insert_data_to_db_text(stm: str, params: Dict[str, Any] = None) -> bool:
    """기존 함수와의 호환성을 위한 래퍼 함수"""
    from .config import Config
    
    config = Config()
    db_manager = DatabaseManager(config.database)
    return await db_manager.execute_insert(stm, params) 