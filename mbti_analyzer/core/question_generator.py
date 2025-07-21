"""
AI 질문 생성 로직

MBTI T/F 성향 분석을 위한 AI 기반 질문 생성 기능입니다.
"""

import asyncio
import re
import random
import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# AI 모델 초기화
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    AI_MODEL = genai.GenerativeModel('gemini-1.5-pro-latest')
    print("Gemini AI 모델 초기화 완료", flush=True)
else:
    AI_MODEL = None
    print("⚠️ GEMINI_API_KEY가 설정되지 않음. AI 질문 생성이 비활성화됩니다.", flush=True)


async def generate_ai_questions_real(count: int = 5, difficulty: str = "medium") -> List[str]:
    """
    실제 AI를 사용하여 T/F 성향 분석을 위한 질문들을 동적으로 생성합니다.
    """
    if not AI_MODEL:
        print("❌ AI 모델이 초기화되지 않음. 폴백 질문 사용.")
        return generate_fallback_questions(count)
    
    try:
        # 난이도별 프롬프트 설정
        difficulty_prompts = {
            "easy": "일상적이고 가벼운 상황에서",
            "medium": "약간 복잡하고 고민이 필요한 상황에서", 
            "hard": "복잡하고 어려운 딜레마 상황에서"
        }
        
        difficulty_desc = difficulty_prompts.get(difficulty, difficulty_prompts["medium"])
        
        prompt = f"""
        MBTI T/F 성향을 분석하기 위한 상황 질문을 {count}개 생성해줘.

        요구사항:
        1. {difficulty_desc} 어떻게 대응할지 묻는 질문
        2. 관계, 소통, 갈등 해결, 의사결정 상황 중심
        3. T성향(논리적/객관적)과 F성향(감정적/관계중심) 구분이 가능한 상황
        4. 각 질문은 "당신이 어떤 방식으로 어떻게 대응할지 구체적으로 설명해주세요" 형태로 끝나야 함
        5. 실제 일상에서 겪을 수 있는 현실적인 상황들
        6. 한국어로 작성, 존댓말 사용

        예시 형태:
        "친구가 '요즘 너무 힘들어'라고 털어놓았습니다. 당신이 어떤 마음으로 어떻게 대응할지 구체적으로 설명해주세요."

        {count}개의 서로 다른 상황 질문을 생성해줘. 각 질문은 번호 없이 줄바꿈으로 구분해줘.
        """
        
        response = await asyncio.to_thread(AI_MODEL.generate_content, prompt)
        questions_text = response.text.strip()
        
        # 생성된 질문을 리스트로 분할
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        # 빈 질문이나 형식이 맞지 않는 질문 필터링
        valid_questions = []
        for q in questions:
            # 번호나 불필요한 문자 제거
            q = re.sub(r'^\d+[\.\)\-\s]*', '', q)
            q = re.sub(r'^[\-\*\•]\s*', '', q)
            q = q.strip()
            
            if len(q) > 20 and '당신이' in q and ('어떻게' in q or '어떤' in q):
                valid_questions.append(q)
        
        # 요청된 개수만큼 반환
        if len(valid_questions) >= count:
            return valid_questions[:count]
        else:
            # 부족하면 폴백 질문으로 채움
            fallback = generate_fallback_questions(count - len(valid_questions))
            return valid_questions + fallback
            
    except Exception as e:
        print(f"❌ AI 질문 생성 실패: {e}")
        return generate_fallback_questions(count)


def generate_fallback_questions(count: int = 5) -> List[str]:
    """
    AI 실패 시 사용할 폴백 질문들
    """
    fallback_questions = [
        "친구가 갑자기 '요즘 너무 스트레스 받아'라고 털어놓았습니다. 당신이 어떤 방식으로 어떻게 대응할지 구체적으로 설명해주세요.",
        "팀 프로젝트에서 의견이 충돌하고 있습니다. 당신이 어떤 접근방식으로 이 상황을 해결할지 자세히 설명해주세요.",
        "친구가 '나 정말 못생겼지?'라고 진지하게 물어봅니다. 당신이 어떤 방식으로 답변할지 구체적으로 설명해주세요.",
        "약속에 늦은 친구가 변명을 계속합니다. 당신이 어떤 마음으로 어떻게 반응할지 자세히 설명해주세요.",
        "회의에서 내 의견이 무시당한 것 같습니다. 당신이 어떤 방식으로 대처할지 구체적으로 설명해주세요.",
        "동료가 실수로 내 일을 망쳤습니다. 당신이 어떤 마음으로 어떻게 대응할지 구체적으로 설명해주세요.",
        "가족이 내 결정에 반대합니다. 당신이 어떤 방식으로 상황을 해결할지 자세히 설명해주세요.",
        "친구가 내 조언을 무시하고 같은 실수를 반복합니다. 당신이 어떤 마음으로 어떻게 대응할지 구체적으로 설명해주세요.",
        "팀원이 계속 불평만 하고 있습니다. 당신이 어떤 접근방식으로 이 상황을 개선할지 자세히 설명해주세요.",
        "상대방이 내 감정을 이해하지 못합니다. 당신이 어떤 방식으로 소통할지 구체적으로 설명해주세요."
    ]
    
    selected = fallback_questions.copy()
    random.shuffle(selected)
    
    # 요청된 개수만큼 반환 (필요하면 중복 허용)
    if count <= len(selected):
        return selected[:count]
    else:
        result = selected[:]
        while len(result) < count:
            random.shuffle(fallback_questions)
            result.extend(fallback_questions[:count - len(result)])
        return result[:count]


def generate_ai_questions(count: int = 5, difficulty: str = "medium") -> List[str]:
    """
    동기 래퍼 함수 - 기존 호환성 유지
    """
    return asyncio.run(generate_ai_questions_real(count, difficulty)) 