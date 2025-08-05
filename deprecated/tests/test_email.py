#!/usr/bin/env python3
"""
이메일 발송 테스트 스크립트
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from services.email_service import EmailService
from core.exceptions import EmailError


async def test_email_basic():
    """기본 이메일 발송 테스트"""
    print("📧 기본 이메일 발송 테스트")
    print("=" * 50)
    
    try:
        config = Config()
        email_service = EmailService(config.email)
        
        # 테스트 이메일 발송
        subject = "🧪 배치 시스템 이메일 테스트"
        body = f"""
안녕하세요!

이 메일은 배치 시스템의 이메일 발송 기능 테스트입니다.

테스트 정보:
- 발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 발송자: 배치 처리 시스템
- 상태: 정상 작동

---
채팅 키워드 배치 처리 시스템
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #28a745; text-align: center;">🧪 이메일 테스트</h2>
        
        <p>안녕하세요!</p>
        
        <p>이 메일은 배치 시스템의 이메일 발송 기능 테스트입니다.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">📋 테스트 정보</h3>
            <ul style="list-style: none; padding: 0;">
                <li><strong>발송 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li><strong>발송자:</strong> 배치 처리 시스템</li>
                <li><strong>상태:</strong> <span style="color: #28a745;">정상 작동</span></li>
            </ul>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p style="text-align: center; color: #6c757d; font-size: 12px;">
            채팅 키워드 배치 처리 시스템
        </p>
    </div>
</body>
</html>
        """
        
        success = email_service.send_email(subject, body, html_body=html_body)
        
        if success:
            print("✅ 이메일 발송 성공!")
            print(f"📤 수신자: {', '.join(config.email.recipient_emails)}")
        else:
            print("❌ 이메일 발송 실패!")
            
    except EmailError as e:
        print(f"❌ 이메일 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


async def test_batch_notification():
    """배치 완료 알림 이메일 테스트"""
    print("\n📧 배치 완료 알림 이메일 테스트")
    print("=" * 50)
    
    try:
        config = Config()
        email_service = EmailService(config.email)
        
        # 테스트 통계 데이터
        test_stats = {
            'start_time': '2025-01-16 10:00:00',
            'end_time': '2025-01-16 10:05:00',
            'duration': '5분 30초',
            'total_rows': 1500,
            'processed_count': 1450,
            'skipped_count': 50,
            'category_distribution': {
                '학습지원': 850,
                '학사정보': 400,
                '기타': 200
            }
        }
        
        # 성공 알림 테스트
        success = email_service.send_batch_notification(
            target_date="2025-01-16 (테스트)",
            status="SUCCESS",
            stats=test_stats
        )
        
        if success:
            print("✅ 배치 완료 알림 이메일 발송 성공!")
        else:
            print("❌ 배치 완료 알림 이메일 발송 실패!")
            
    except EmailError as e:
        print(f"❌ 이메일 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


async def test_email_config():
    """이메일 설정 확인"""
    print("\n🔧 이메일 설정 확인")
    print("=" * 50)
    
    try:
        config = Config()
        
        print(f"📧 SMTP 서버: {config.email.smtp_server}")
        print(f"🔌 SMTP 포트: {config.email.smtp_port}")
        print(f"👤 발송자: {config.email.sender_email}")
        print(f"📥 수신자: {', '.join(config.email.recipient_emails)}")
        
        if not config.email.sender_email:
            print("⚠️ 경고: SENDER_EMAIL이 설정되지 않았습니다.")
        
        if not config.email.sender_password:
            print("⚠️ 경고: SENDER_PASSWORD가 설정되지 않았습니다.")
        
        if not config.email.recipient_emails:
            print("⚠️ 경고: RECIPIENT_EMAILS가 설정되지 않았습니다.")
        
        if all([config.email.sender_email, config.email.sender_password, config.email.recipient_emails]):
            print("✅ 이메일 설정이 완료되었습니다.")
        else:
            print("❌ 이메일 설정이 불완전합니다.")
            
    except Exception as e:
        print(f"❌ 설정 확인 오류: {e}")


async def main():
    """메인 실행 함수"""
    print("📧 이메일 기능 테스트 시작")
    print("=" * 60)
    
    # 설정 확인
    await test_email_config()
    
    # 입력 대기
    print("\n" + "=" * 60)
    response = input("📧 이메일 발송 테스트를 계속하시겠습니까? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        # 기본 이메일 테스트
        await test_email_basic()
        
        # 배치 알림 테스트
        await test_batch_notification()
        
        print("\n" + "=" * 60)
        print("🎉 이메일 테스트 완료!")
        print("\n💡 참고사항:")
        print("  - Gmail 사용 시 앱 비밀번호를 사용하세요")
        print("  - 환경변수 설정을 확인하세요:")
        print("    * SENDER_EMAIL")
        print("    * SENDER_PASSWORD") 
        print("    * RECIPIENT_EMAILS")
    else:
        print("📧 이메일 발송 테스트를 건너뜁니다.")


if __name__ == "__main__":
    asyncio.run(main()) 