"""
배치 처리용 SQL 쿼리 모음
프로시저 대신 직접 쿼리를 관리합니다.

🚀 성능 최적화 권장사항:
1. chattings.created_at 인덱스 필수
2. admin_chat_keywords.created_at 인덱스 필수  
3. admin_chat_keywords.batch_created_at 인덱스 권장

📅 날짜 형식 표준:
- 모든 쿼리에서 'YYYY-MM-DD HH:MM:SS' 형식 사용
- start_date: 'YYYY-MM-DD 00:00:00'
- end_date: 'YYYY-MM-DD 23:59:59'
"""

from core.config import Config


class BatchQueries:
    """배치 처리용 SQL 쿼리 클래스"""
    
    def __init__(self, config: Config = None):
        self.config = config
    
    def _get_table_name(self, table_type: str) -> str:
        """테이블명을 설정에서 가져옵니다."""
        if not self.config:
            # 기본값 반환
            table_map = {
                'chattings': 'chattings',
                'chat_keywords': 'admin_chat_keywords',
                'categories': 'admin_categories'
            }
            return table_map.get(table_type, table_type)
        
        table_map = {
            'chattings': self.config.database.table_chattings,
            'chat_keywords': self.config.database.table_chat_keywords,
            'categories': self.config.database.table_categories
        }
        return table_map.get(table_type, table_type)
    
    def _get_column_name(self, column_type: str) -> str:
        """컬럼명을 설정에서 가져옵니다."""
        if not self.config:
            # 기본값 반환
            column_map = {
                'input_text': 'input_text',
                'chatting_pk': 'chatting_pk',
                'created_at': 'created_at',
                'query_text': 'query_text',
                'keyword': 'keyword',
                'category_id': 'category_id',
                'query_count': 'query_count',
                'batch_created_at': 'batch_created_at',
                'category_name': 'category_name'
            }
            return column_map.get(column_type, column_type)
        
        column_map = {
            'input_text': self.config.database.column_input_text,
            'chatting_pk': self.config.database.column_chatting_pk,
            'created_at': self.config.database.column_created_at,
            'query_text': self.config.database.column_query_text,
            'keyword': self.config.database.column_keyword,
            'category_id': self.config.database.column_category_id,
            'query_count': self.config.database.column_query_count,
            'batch_created_at': self.config.database.column_batch_created_at,
            'category_name': self.config.database.column_category_name
        }
        return column_map.get(column_type, column_type)
    
    def get_unique_chattings_by_date(self, start_date: str, end_date: str) -> str:
        """고유 채팅 데이터 조회 쿼리 (기존 프로시저 대체)"""
        chattings_table = self._get_table_name('chattings')
        input_text_col = self._get_column_name('input_text')
        chatting_pk_col = self._get_column_name('chatting_pk')
        created_at_col = self._get_column_name('created_at')
        
        return f"""
            WITH counted_chats AS (
                SELECT 
                    {chatting_pk_col},
                    {input_text_col},
                    {created_at_col},
                    ROW_NUMBER() OVER (PARTITION BY {input_text_col} ORDER BY {created_at_col} DESC) AS rn,
                    COUNT(*) OVER (PARTITION BY {input_text_col}) AS total_count
                FROM {chattings_table}
                WHERE {created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            )
            SELECT 
                {input_text_col},
                total_count,
                DATE({created_at_col}) AS created_at
            FROM counted_chats
            WHERE rn = 1
            ORDER BY total_count DESC, created_at ASC
        """
    
    def classify_chat_keywords_by_date(self, start_date: str, end_date: str) -> str:
        """채팅 키워드 분류 쿼리 (기존 프로시저 대체)"""
        chat_keywords_table = self._get_table_name('chat_keywords')
        categories_table = self._get_table_name('categories')
        query_text_col = self._get_column_name('query_text')
        created_at_col = self._get_column_name('created_at')
        query_count_col = self._get_column_name('query_count')
        keyword_col = self._get_column_name('keyword')
        category_id_col = self._get_column_name('category_id')
        category_name_col = self._get_column_name('category_name')
        
        # 기본 카테고리 ID (미분류)
        default_category_id = 11
        if self.config:
            default_category_id = self.config.batch.default_category_id
        
        return f"""WITH base AS (
            SELECT *
            FROM {chat_keywords_table}
            WHERE {created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        ),
        first_occurrence AS (
            SELECT 
                {query_text_col},
                {created_at_col},
                {query_count_col},
                ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY {created_at_col} ASC) AS rn
            FROM base
        ),
        keyword_ranked AS (
            SELECT 
                {query_text_col}, 
                {keyword_col},
                ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY {created_at_col} ASC) AS rn
            FROM base
        ),
        category_ranked AS (
            SELECT 
                {query_text_col}, 
                {category_id_col},
                ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY MIN({created_at_col}) ASC) AS rn
            FROM base
            WHERE {category_id_col} != {default_category_id}
            GROUP BY {query_text_col}, {category_id_col}
        ),
        final_agg AS (
            SELECT 
                fo.{query_text_col},
                fo.{created_at_col},
                fo.{query_count_col},
                CASE
                    WHEN SUM(CASE WHEN b.{category_id_col} = {default_category_id} THEN 1 ELSE 0 END) = COUNT(*) THEN {default_category_id}
                    ELSE cr.{category_id_col}
                END AS final_category
            FROM first_occurrence fo
            JOIN base b ON fo.{query_text_col} = b.{query_text_col}
            LEFT JOIN category_ranked cr 
                ON fo.{query_text_col} = cr.{query_text_col} AND cr.rn = 1
            WHERE fo.rn = 1
            GROUP BY fo.{query_text_col}
        ),
        final_result AS (
            SELECT 
                fa.{query_text_col},
                fa.{created_at_col},
                fa.{query_count_col},
                fa.final_category,
                kr.{keyword_col}
            FROM final_agg fa
            LEFT JOIN keyword_ranked kr 
                ON fa.{query_text_col} = kr.{query_text_col} AND kr.rn = 1
        )
        SELECT 
            c.{category_name_col},
            fr.{query_text_col},
            fr.{keyword_col},
            fr.{created_at_col},
            fr.{query_count_col}
        FROM final_result fr
        LEFT JOIN {categories_table} c 
            ON fr.final_category = c.{category_id_col};
        """
    
    def get_total_chattings_by_date(self, start_date: str, end_date: str) -> str:
        """날짜별 전체 채팅 통계 조회"""
        chattings_table = self._get_table_name('chattings')
        input_text_col = self._get_column_name('input_text')
        created_at_col = self._get_column_name('created_at')
        
        return f"""
            SELECT 
                DATE({created_at_col}) AS date,
                COUNT(DISTINCT {input_text_col}) AS unique_questions,
                COUNT(*) AS total_messages
            FROM {chattings_table} 
            WHERE {created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            GROUP BY DATE({created_at_col})
            ORDER BY date
        """
    
    def get_all_unique_questions_by_date(self, start_date: str, end_date: str) -> str:
        """날짜별 고유 질문 조회"""
        chattings_table = self._get_table_name('chattings')
        input_text_col = self._get_column_name('input_text')
        created_at_col = self._get_column_name('created_at')
        
        return f"""
            SELECT DISTINCT 
                {input_text_col},
                DATE({created_at_col}) AS date
            FROM {chattings_table} 
            WHERE {created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            ORDER BY date, {input_text_col}
        """
    
    def get_missing_data(self, start_date: str, end_date: str) -> str:
        """누락된 데이터 조회"""
        chattings_table = self._get_table_name('chattings')
        chat_keywords_table = self._get_table_name('chat_keywords')
        input_text_col = self._get_column_name('input_text')
        created_at_col = self._get_column_name('created_at')
        query_text_col = self._get_column_name('query_text')
        query_count_col = self._get_column_name('query_count')
        category_id_col = self._get_column_name('category_id')
        
        # 기본 카테고리 ID (미분류)
        default_category_id = 11
        if self.config:
            default_category_id = self.config.batch.default_category_id
        
        return f"""
        WITH base AS (
        SELECT *
        FROM {chat_keywords_table}
        WHERE {created_at_col} >= '{start_date} 00:00:00' AND {created_at_col} <= '{end_date} 23:59:59'
    ),
    first_occurrence AS (
        SELECT 
            {query_text_col},
            {created_at_col},
            {query_count_col},
            ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY {created_at_col} ASC) AS rn
        FROM base
    ),
    category_ranked AS (
        SELECT 
            {query_text_col}, 
            {category_id_col},
            ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY MIN({created_at_col}) ASC) AS rn
        FROM base
        WHERE {category_id_col} != {default_category_id}
        GROUP BY {query_text_col}, {category_id_col}
    ),
    final_agg AS (
        SELECT 
            fo.{query_text_col},
            fo.{created_at_col},
            fo.{query_count_col},
            CASE
                WHEN SUM(CASE WHEN b.{category_id_col} = {default_category_id} THEN 1 ELSE 0 END) = COUNT(*) THEN {default_category_id}
                ELSE cr.{category_id_col}
            END AS final_category
        FROM first_occurrence fo
        JOIN base b ON fo.{query_text_col} = b.{query_text_col}
        LEFT JOIN category_ranked cr 
            ON fo.{query_text_col} = cr.{query_text_col} AND cr.rn = 1
        WHERE fo.rn = 1
        GROUP BY fo.{query_text_col}
    )
    SELECT 
        DATE(c.{created_at_col}) AS missing_date,
        c.{input_text_col},
        COUNT(*) AS missing_count
    FROM {chattings_table} c
    LEFT JOIN (
        SELECT {query_text_col}, DATE({created_at_col}) AS dt
        FROM final_agg
    ) t ON c.{input_text_col} = t.{query_text_col} AND DATE(c.{created_at_col}) = t.dt
    WHERE t.{query_text_col} IS NULL
    AND c.{created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
    GROUP BY DATE(c.{created_at_col}), c.{input_text_col}
    ORDER BY missing_date;
    """
    
    def get_missing_data_status(self, start_date: str, end_date: str) -> str:
        """누락 데이터 현황 조회"""
        chattings_table = self._get_table_name('chattings')
        chat_keywords_table = self._get_table_name('chat_keywords')
        input_text_col = self._get_column_name('input_text')
        created_at_col = self._get_column_name('created_at')
        query_text_col = self._get_column_name('query_text')
        query_count_col = self._get_column_name('query_count')
        category_id_col = self._get_column_name('category_id')
        
        # 기본 카테고리 ID (미분류)
        default_category_id = 11
        if self.config:
            default_category_id = self.config.batch.default_category_id
        
        return f"""SELECT m.missing_date, SUM(m.missing_count) as missing_total
FROM (WITH base AS (
    SELECT *
    FROM {chat_keywords_table}
    WHERE {created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
),
first_occurrence AS (
    SELECT 
        {query_text_col},
        {created_at_col},
        {query_count_col},
        ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY {created_at_col} ASC) AS rn
    FROM base
),
category_ranked AS (
    SELECT 
        {query_text_col}, 
        {category_id_col},
        ROW_NUMBER() OVER (PARTITION BY {query_text_col} ORDER BY MIN({created_at_col}) ASC) AS rn
    FROM base
    WHERE {category_id_col} != {default_category_id}
    GROUP BY {query_text_col}, {category_id_col}
),
final_agg AS (
    SELECT 
        fo.{query_text_col},
        fo.{created_at_col},
        fo.{query_count_col},
        CASE
            WHEN SUM(CASE WHEN b.{category_id_col} = {default_category_id} THEN 1 ELSE 0 END) = COUNT(*) THEN {default_category_id}
            ELSE cr.{category_id_col}
        END AS final_category
    FROM first_occurrence fo
    JOIN base b ON fo.{query_text_col} = b.{query_text_col}
    LEFT JOIN category_ranked cr 
        ON fo.{query_text_col} = cr.{query_text_col} AND cr.rn = 1
    WHERE fo.rn = 1
    GROUP BY fo.{query_text_col}
)
SELECT 
    DATE(c.{created_at_col}) AS missing_date,
    c.{input_text_col},
    COUNT(*) AS missing_count
FROM {chattings_table} c
LEFT JOIN (
    SELECT {query_text_col}, DATE({created_at_col}) AS dt
    FROM final_agg
) t ON c.{input_text_col} = t.{query_text_col} AND DATE(c.{created_at_col}) = t.dt
WHERE t.{query_text_col} IS NULL
  AND c.{created_at_col} BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
GROUP BY DATE(c.{created_at_col}), c.{input_text_col}
) as m
GROUP BY m.missing_date
ORDER BY m.missing_date
"""
    
    @staticmethod
    def get_existing_keywords_cache(start_date: str, end_date: str) -> str:
        """기존 키워드 중복 체크용 캐시 조회 - 개선된 버전
        
        ⚠️ 중요: 키워드는 HCX API에 따라 달라질 수 있으므로 
        중복 체크는 query_text + created_at 기준으로만 수행합니다.
        """
        return f"""
            SELECT DISTINCT CONCAT(query_text, '|', DATE(created_at)) as unique_key
            FROM admin_chat_keywords
            WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        """
    
    @staticmethod
    def verify_missing_data_processing(start_date: str, end_date: str) -> str:
        """누락 데이터 처리 후 검증 쿼리"""
        return f"""
            SELECT 
                DATE(c.created_at) AS missing_date,
                COUNT(DISTINCT c.input_text) AS remaining_missing_count
            FROM chattings c
            LEFT JOIN (
                SELECT DISTINCT query_text, DATE(created_at) AS dt
                FROM admin_chat_keywords
                WHERE created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
            WHERE t.query_text IS NULL
              AND c.created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            GROUP BY DATE(c.created_at)
            ORDER BY missing_date
        """
    
    @staticmethod
    def get_final_missing_count(start_date: str, end_date: str, today: str) -> str:
        """최종 누락 데이터 개수 확인"""
        return f"""
            SELECT 
                COUNT(DISTINCT c.input_text) AS final_missing_count
            FROM chattings c
            LEFT JOIN (
                SELECT DISTINCT query_text, DATE(created_at) AS dt  
                FROM admin_chat_keywords
                WHERE DATE(batch_created_at) >= '{today}'
                  AND created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
            ) t ON c.input_text = t.query_text AND DATE(c.created_at) = t.dt
            WHERE t.query_text IS NULL
              AND c.created_at BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
        """
    
    @staticmethod
    def get_categories() -> str:
        """카테고리 정보 조회"""
        return "SELECT category_id, category_name FROM admin_categories"
    
    @staticmethod
    def get_table_schema(table_name: str) -> str:
        """테이블 스키마 조회"""
        return f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}' 
            ORDER BY ORDINAL_POSITION
        """
    
    @staticmethod
    def insert_chat_keywords(query_column: str) -> str:
        """채팅 키워드 INSERT 쿼리"""
        return f"""
            INSERT INTO admin_chat_keywords ({query_column}, keyword, category_id, query_count, created_at, batch_created_at)
            VALUES (:{query_column}, :keyword, :category_id, :query_count, :created_at, :batch_created_at)
        """ 