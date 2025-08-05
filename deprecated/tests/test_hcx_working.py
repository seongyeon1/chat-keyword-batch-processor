#!/usr/bin/env python3
"""
HCX API 정상 작동 확인 테스트
"""

import json
import requests

# 성공한 설정
HCX_API_KEY = "nv-2f7914583cba44499c808641385ad86e4HwM"
APP_TYPE = "testapp"
MODEL = "HCX-005"

def test_working_config():
    """정상 작동하는 설정으로 테스트"""
    
    url = f"https://clovastudio.stream.ntruss.com/{APP_TYPE}/v3/chat-completions/{MODEL}"
    headers = {
        "Authorization": f"Bearer {HCX_API_KEY}",
        "Content-Type": "application/json"
    }
    
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
    
    test_questions = [
        "전학을 신청하려면 어떤 서류가 필요한가요?",
        "성적표는 어떻게 발급받나요?",
        "학교폭력 신고는 어디에 하나요?",
        "검정고시 접수 기간이 언제인가요?",
        "교사 임용고시 일정을 알려주세요"
    ]
    
    print(f"🧪 HCX API 정상 작동 테스트")
    print(f"📝 설정: {APP_TYPE} / {MODEL}")
    print(f"{'='*60}")
    
    success_count = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. 질문: {question}")
        
        data = {
            "messages": [
                {"role": "user", "content": question}
            ],
            "tools": tools,
            "toolChoice": "auto"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # 응답 분석
                tool_calls = result.get("result", {}).get("message", {}).get("toolCalls", [])
                
                if tool_calls:
                    arguments = tool_calls[0]["function"]["arguments"]
                    
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            pass
                    
                    keywords_with_categories = arguments.get("keywords_with_categories", [])
                    
                    print(f"   ✅ 성공!")
                    print(f"   📊 분류 결과:")
                    for item in keywords_with_categories:
                        keyword = item.get("keyword", "")
                        categories = item.get("categories", [])
                        print(f"      - 키워드: '{keyword}' → 카테고리: {categories}")
                    
                    success_count += 1
                else:
                    print(f"   ⚠️ Tool calls 없음")
                    print(f"   📝 응답: {result}")
            else:
                print(f"   ❌ 실패: {response.status_code}")
                print(f"   📄 응답: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 테스트 결과: {success_count}/{len(test_questions)} 성공")
    
    if success_count == len(test_questions):
        print(f"🎉 모든 테스트 통과! HCX API가 정상 작동합니다.")
        return True
    elif success_count > 0:
        print(f"⚠️ 일부 테스트 통과. HCX API가 대부분 정상 작동합니다.")
        return True
    else:
        print(f"❌ 모든 테스트 실패. HCX API에 문제가 있습니다.")
        return False

if __name__ == "__main__":
    test_working_config() 