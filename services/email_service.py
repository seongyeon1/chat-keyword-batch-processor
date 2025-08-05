"""
이메일 서비스 모듈 - 이메일 발송과 템플릿 관리를 담당합니다.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.config import EmailConfig
from core.exceptions import EmailError


class EmailService:
    """이메일 발송 서비스 클래스"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
    
    def send_email(self, subject: str, body: str, attachments: List[str] = None, html_body: str = None) -> bool:
        """
        이메일을 발송합니다.
        
        Args:
            subject (str): 이메일 제목
            body (str): 이메일 본문 (텍스트)
            attachments (List[str]): 첨부 파일 경로 리스트
            html_body (str): HTML 이메일 본문
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.sender_email
            msg['To'] = ', '.join(self.config.recipient_emails)
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 텍스트 본문 추가
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # HTML 본문 추가
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 첨부 파일 추가
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._attach_file(msg, file_path)
                    else:
                        print(f"⚠️ 첨부 파일을 찾을 수 없습니다: {file_path}")
            
            # SMTP 서버를 통해 이메일 발송
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(self.config.sender_email, self.config.recipient_emails, msg.as_string())
            
            print(f"📧 이메일 발송 완료: {', '.join(self.config.recipient_emails)}")
            return True
            
        except Exception as e:
            print(f"📧 이메일 발송 실패: {e}")
            raise EmailError(f"이메일 발송 실패: {e}")
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """파일을 이메일에 첨부합니다."""
        try:
            filename = os.path.basename(file_path)
            
            # 영어 파일명으로 변환 (한글 인코딩 문제 방지)
            safe_filename = self._get_safe_filename(filename)
            
            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='octet-stream')
                attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=safe_filename
                )
                msg.attach(attachment)
                
        except Exception as e:
            print(f"⚠️ 파일 첨부 실패: {file_path} - {e}")
    
    def _get_safe_filename(self, filename: str) -> str:
        """안전한 영어 파일명을 생성합니다."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if filename.startswith('채팅키워드분류'):
            return f"chat_keywords_report_{timestamp}.xlsx"
        elif '보고서' in filename:
            return f"report_{timestamp}.xlsx"
        else:
            # 기본적으로 영어 파일명 생성
            base_name = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]
            return f"file_{timestamp}{extension}"
    
    def send_batch_notification(self, target_date: str, status: str, stats: Dict[str, Any], 
                              error_message: str = None, excel_file_path: str = None) -> bool:
        """
        배치 처리 결과 알림 이메일을 발송합니다.
        
        Args:
            target_date (str): 대상 날짜
            status (str): 처리 상태 (SUCCESS/FAILED)
            stats (Dict[str, Any]): 통계 정보
            error_message (str): 오류 메시지 (실패 시)
            excel_file_path (str): 엑셀 파일 경로 (성공 시)
            
        Returns:
            bool: 발송 성공 여부
        """
        if status == "SUCCESS":
            subject = f"✅ 채팅 키워드 배치 처리 완료 - {target_date}"
            body = self._create_success_email_body(target_date, stats)
            html_body = self._create_success_html_body(target_date, stats)
            attachments = [excel_file_path] if excel_file_path and os.path.exists(excel_file_path) else []
        else:
            subject = f"❌ 채팅 키워드 배치 처리 실패 - {target_date}"
            body = self._create_failure_email_body(target_date, stats, error_message)
            html_body = self._create_failure_html_body(target_date, stats, error_message)
            attachments = []
        
        return self.send_email(subject, body, attachments, html_body)
    
    def send_excel_report(self, excel_file_path: str, report_period: str = None) -> bool:
        """
        엑셀 보고서를 이메일로 발송합니다.
        
        Args:
            excel_file_path (str): 엑셀 파일 경로
            report_period (str): 보고서 기간
            
        Returns:
            bool: 발송 성공 여부
        """
        if not os.path.exists(excel_file_path):
            raise EmailError(f"엑셀 파일을 찾을 수 없습니다: {excel_file_path}")
        
        period_str = report_period or "특정 기간"
        subject = f"📊 채팅 키워드 분류 보고서 - {period_str}"
        
        body = self._create_report_email_body(report_period, os.path.basename(excel_file_path))
        html_body = self._create_report_html_body(report_period, os.path.basename(excel_file_path))
        
        return self.send_email(subject, body, [excel_file_path], html_body)
    
    def _create_success_email_body(self, target_date: str, stats: Dict[str, Any]) -> str:
        """성공 이메일 텍스트 본문을 생성합니다."""
        return f"""
채팅 키워드 배치 처리가 성공적으로 완료되었습니다.

=== 처리 결과 요약 ===
• 처리 날짜: {target_date}
• 시작 시간: {stats.get('start_time', 'N/A')}
• 종료 시간: {stats.get('end_time', 'N/A')}
• 소요 시간: {stats.get('duration', 'N/A')}
• 전체 데이터: {stats.get('total_rows', 0):,}개
• 처리 완료: {stats.get('processed_count', 0):,}개
• 중복 스킵: {stats.get('skipped_count', 0):,}개

=== 카테고리별 분포 ===
{self._format_category_distribution(stats.get('category_distribution', {}))}

배치 처리 결과가 엑셀 파일로 첨부되어 있습니다.

---
채팅 키워드 배치 처리 시스템
"""
    
    def _create_success_html_body(self, target_date: str, stats: Dict[str, Any]) -> str:
        """성공 이메일 HTML 본문을 생성합니다."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #28a745; text-align: center;">✅ 배치 처리 완료</h2>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📊 처리 결과 요약</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>처리 날짜:</strong> {target_date}</li>
                <li><strong>시작 시간:</strong> {stats.get('start_time', 'N/A')}</li>
                <li><strong>종료 시간:</strong> {stats.get('end_time', 'N/A')}</li>
                <li><strong>소요 시간:</strong> {stats.get('duration', 'N/A')}</li>
                <li><strong>전체 데이터:</strong> {stats.get('total_rows', 0):,}개</li>
                <li><strong>처리 완료:</strong> {stats.get('processed_count', 0):,}개</li>
                <li><strong>중복 스킵:</strong> {stats.get('skipped_count', 0):,}개</li>
            </ul>
        </div>
        
        <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📈 카테고리별 분포</h3>
            {self._format_category_distribution_html(stats.get('category_distribution', {}))}
        </div>
        
        <p style="margin-top: 30px; padding: 10px; background-color: #d4edda; border-radius: 5px;">
            📎 배치 처리 결과가 엑셀 파일로 첨부되어 있습니다.
        </p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="text-align: center; color: #6c757d; font-size: 12px;">
            채팅 키워드 배치 처리 시스템
        </p>
    </div>
</body>
</html>
"""
    
    def _create_failure_email_body(self, target_date: str, stats: Dict[str, Any], error_message: str) -> str:
        """실패 이메일 텍스트 본문을 생성합니다."""
        return f"""
채팅 키워드 배치 처리 중 오류가 발생했습니다.

=== 처리 결과 요약 ===
• 처리 날짜: {target_date}
• 시작 시간: {stats.get('start_time', 'N/A')}
• 종료 시간: {stats.get('end_time', 'N/A')}
• 소요 시간: {stats.get('duration', 'N/A')}
• 전체 데이터: {stats.get('total_rows', 0):,}개
• 처리 완료: {stats.get('processed_count', 0):,}개
• 중복 스킵: {stats.get('skipped_count', 0):,}개

=== 오류 정보 ===
{error_message}

시스템 관리자에게 문의하시기 바랍니다.

---
채팅 키워드 배치 처리 시스템
"""
    
    def _create_failure_html_body(self, target_date: str, stats: Dict[str, Any], error_message: str) -> str:
        """실패 이메일 HTML 본문을 생성합니다."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #dc3545; text-align: center;">❌ 배치 처리 실패</h2>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📊 처리 결과 요약</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>처리 날짜:</strong> {target_date}</li>
                <li><strong>시작 시간:</strong> {stats.get('start_time', 'N/A')}</li>
                <li><strong>종료 시간:</strong> {stats.get('end_time', 'N/A')}</li>
                <li><strong>소요 시간:</strong> {stats.get('duration', 'N/A')}</li>
                <li><strong>전체 데이터:</strong> {stats.get('total_rows', 0):,}개</li>
                <li><strong>처리 완료:</strong> {stats.get('processed_count', 0):,}개</li>
                <li><strong>중복 스킵:</strong> {stats.get('skipped_count', 0):,}개</li>
            </ul>
        </div>
        
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #721c24; margin-top: 0;">⚠️ 오류 정보</h3>
            <pre style="white-space: pre-wrap; font-size: 12px; color: #721c24;">{error_message}</pre>
        </div>
        
        <p style="margin-top: 30px; padding: 10px; background-color: #fff3cd; border-radius: 5px;">
            ⚠️ 시스템 관리자에게 문의하시기 바랍니다.
        </p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="text-align: center; color: #6c757d; font-size: 12px;">
            채팅 키워드 배치 처리 시스템
        </p>
    </div>
</body>
</html>
"""
    
    def _create_report_email_body(self, report_period: str, filename: str) -> str:
        """보고서 이메일 텍스트 본문을 생성합니다."""
        return f"""
채팅 키워드 분류 보고서를 요청하신 대로 생성하여 발송드립니다.

=== 보고서 정보 ===
• 조회 기간: {report_period or "특정 기간"}
• 파일명: {filename}
• 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

보고서는 다음 시트들로 구성되어 있습니다:
1. 채팅키워드분류 - 전체 분류 데이터
2. 카테고리별통계 - 카테고리별 집계
3. 일별통계 - 날짜별 분포
4. 상위키워드 - 인기 키워드 TOP 10
5. 상위질문 - 많이 묻는 질문 TOP 10
6. 요약정보 - 전체 통계 요약

첨부된 엑셀 파일을 확인해주세요.

---
채팅 키워드 배치 처리 시스템
"""
    
    def _create_report_html_body(self, report_period: str, filename: str) -> str:
        """보고서 이메일 HTML 본문을 생성합니다."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #007bff; text-align: center;">📊 채팅 키워드 분류 보고서</h2>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📋 보고서 정보</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>조회 기간:</strong> {report_period or "특정 기간"}</li>
                <li><strong>파일명:</strong> {filename}</li>
                <li><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
        </div>
        
        <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📈 보고서 구성</h3>
            <ol>
                <li><strong>채팅키워드분류</strong> - 전체 분류 데이터</li>
                <li><strong>카테고리별통계</strong> - 카테고리별 집계</li>
                <li><strong>일별통계</strong> - 날짜별 분포</li>
                <li><strong>상위키워드</strong> - 인기 키워드 TOP 10</li>
                <li><strong>상위질문</strong> - 많이 묻는 질문 TOP 10</li>
                <li><strong>요약정보</strong> - 전체 통계 요약</li>
            </ol>
        </div>
        
        <p style="margin-top: 30px; padding: 10px; background-color: #d4edda; border-radius: 5px;">
            📎 첨부된 엑셀 파일을 확인해주세요.
        </p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="text-align: center; color: #6c757d; font-size: 12px;">
            채팅 키워드 배치 처리 시스템
        </p>
    </div>
</body>
</html>
"""
    
    def _format_category_distribution(self, category_dist: Dict[str, int]) -> str:
        """카테고리 분포를 텍스트 형식으로 포맷팅합니다."""
        if not category_dist:
            return "• 분류된 카테고리가 없습니다."
        
        lines = []
        for category, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"• {category}: {count:,}개")
        
        return "\n".join(lines)
    
    def _format_category_distribution_html(self, category_dist: Dict[str, int]) -> str:
        """카테고리 분포를 HTML 형식으로 포맷팅합니다."""
        if not category_dist:
            return "<p>분류된 카테고리가 없습니다.</p>"
        
        lines = ["<ul style='margin: 0; padding-left: 20px;'>"]
        for category, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"<li><strong>{category}:</strong> {count:,}개</li>")
        lines.append("</ul>")
        
        return "\n".join(lines) 