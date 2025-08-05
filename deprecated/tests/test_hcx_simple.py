#!/usr/bin/env python3
"""
HCX API 간단 테스트 스크립트
"""

import os
import json
import requests

# 환경변수 로드
HCX_API_KEY = "nv-2f7914583cba44499c808641385ad86e4HwM"

def test_hcx_with_different_configs():
    """다양한 설정으로 HCX API 테스트"""
    
    configs = [
        {"app_type": "testapp", "model": "HCX-003"},
        {"app_type": "testapp", "model": "HCX-005"},
        {"app_type": "serviceapp", "model": "HCX-003"},
        {"app_type": "serviceapp", "model": "HCX-005"},
    ]
    
    tools = [{
        "type": "function",
        "function": {
            "name": "classify_education_question",
            "description": "교육 관련 질문을 키워드 기준으로 분석하고 관련된 11가지 카테고리 중 하나 이상으로 분류합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "사용자가 입력한 원본 질문"
                    },
                    "keywords": {
                        "type": "array",
                        "description": "사용자가 입력한 원본 질문에서 구문 및 키워드 추출"
                    },
                    "keywords_with_categories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword": {
                                    "type": "string",
                                    "description": "질문 내에서 감지된 주요 키워드"
                                },
                                "categories": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": [
                                            "학교폭력",
                                            "교권보호 (교육활동 보호)",
                                            "학생 생활",
                                            "평가(성적) 관련",
                                            "전학, 편입",
                                            "입학 관련",
                                            "검정고시",
                                            "교원 임용고시 관련",
                                            "제 증명 관련",
                                            "정보공개",
                                            "기타"
                                        ]
                                    },
                                    "description": "해당 키워드와 연관된 카테고리 목록"
                                }
                            },
                            "required": ["keyword", "categories"]
                        },
                        "description": "질문 내에서 추출된 키워드와 해당 키워드별 분류된 카테고리 목록"
                    }
                },
                "required": ["question", "keywords", "keywords_with_categories"]
            }
        }
    }]
    
    test_query = "전학을 신청하려면 어떤 서류가 필요한가요?"
    
    for config in configs:
        print(f"\n{'='*60}")
        print(f"🧪 테스트 설정: {config['app_type']} / {config['model']}")
        print(f"{'='*60}")
        
        url = f"https://clovastudio.stream.ntruss.com/{config['app_type']}/v3/chat-completions/{config['model']}"
        headers = {
            "Authorization": f"Bearer {HCX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [
                {"role": "user", "content": test_query}
            ],
            "tools": tools,
            "toolChoice": "auto"
        }
        
        try:
            print(f"📡 API 호출 중: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 성공!")
                
                # 응답 구조 분석
                if "result" in result:
                    message = result.get("result", {}).get("message", {})
                    tool_calls = message.get("toolCalls", [])
                    
                    if tool_calls:
                        print(f"🔧 Tool calls 개수: {len(tool_calls)}")
                        arguments = tool_calls[0]["function"]["arguments"]
                        print(f"🎯 Arguments: {arguments}")
                    else:
                        print(f"⚠️ Tool calls 없음")
                        print(f"📝 전체 응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    print(f"📝 전체 응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                print(f"✅ 이 설정은 정상 작동합니다!")
                return config  # 첫 번째 성공한 설정 반환
                
            else:
                print(f"❌ 실패: {response.status_code}")
                response_text = response.text
                print(f"📄 응답 내용: {response_text}")
                
                # 응답 분석
                try:
                    error_json = response.json()
                    status = error_json.get("status", {})
                    error_code = status.get("code", "알 수 없음")
                    error_message = status.get("message", "알 수 없는 오류")
                    
                    print(f"🔍 오류 코드: {error_code}")
                    print(f"🔍 오류 메시지: {error_message}")
                    
                    if error_code == "40009":
                        print("💡 이 설정에서는 Function Calling이 지원되지 않습니다.")
                    elif error_code == "40100":
                        print("💡 인증 오류입니다. API 키를 확인해주세요.")
                    elif error_code.startswith("4"):
                        print("💡 클라이언트 오류입니다.")
                    elif error_code.startswith("5"):
                        print("💡 서버 오류입니다.")
                        
                except json.JSONDecodeError:
                    print("💡 JSON이 아닌 응답입니다.")
                    
        except requests.exceptions.Timeout:
            print("⏰ 요청 타임아웃")
        except requests.exceptions.RequestException as e:
            print(f"🌐 네트워크 오류: {e}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
    
    print(f"\n{'='*60}")
    print("❌ 모든 설정에서 실패했습니다.")
    return None

def test_simple_chat():
    """Function calling 없이 간단한 채팅 테스트"""
    print(f"\n{'='*60}")
    print(f"🧪 간단한 채팅 테스트 (Function calling 없음)")
    print(f"{'='*60}")
    
    configs = [
        {"app_type": "testapp", "model": "HCX-003"},
        {"app_type": "serviceapp", "model": "HCX-005"},
    ]
    
    for config in configs:
        url = f"https://clovastudio.stream.ntruss.com/{config['app_type']}/v3/chat-completions/{config['model']}"
        headers = {
            "Authorization": f"Bearer {HCX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [
                {"role": "user", "content": "안녕하세요"}
            ],
            "maxTokens": 100,
            "temperature": 0.3
        }
        
        try:
            print(f"📡 채팅 테스트: {config['app_type']} / {config['model']}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("result", {}).get("message", {}).get("content", "")
                print(f"✅ 채팅 성공: {message[:100]}")
                return config
            else:
                print(f"❌ 채팅 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 채팅 오류: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 HCX API 테스트 시작")
    
    # Function calling 테스트
    working_config = test_hcx_with_different_configs()
    
    if not working_config:
        # 간단한 채팅 테스트
        working_config = test_simple_chat()
    
    if working_config:
        print(f"\n✅ 권장 설정: {working_config}")
        print(f"환경변수 설정:")
        print(f"HCX_MODEL={working_config['model']}")
        print(f"HCX_APP_TYPE={working_config['app_type']}")
    else:
        print(f"\n❌ 모든 테스트가 실패했습니다. API 키를 확인해주세요.") 