import re
import logging
import google.generativeai as genai
import os
from typing import Dict

logger = logging.getLogger(__name__)

def correct_sentence_with_ai_enhanced(text: str) -> Dict:
    """AI를 사용하여 문장을 교정합니다."""
    try:
        # 문장 교정 프롬프트 생성
        prompt = f"""
다음 음성 인식 결과를 자연스럽고 문법적으로 올바른 한국어 문장으로 교정해주세요.

교정 규칙:
1. 오타나 잘못된 단어를 올바른 단어로 수정
2. 문법 오류를 수정 (조사, 어미 등)
3. 불완전한 문장을 완성
4. 원래 의미는 반드시 유지
5. 교정된 문장만 출력 (설명 없이)

음성 인식 결과: "{text}"

교정된 문장:
"""
        
        # Gemini AI 사용
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            from mbti_analyzer.config.settings import settings
            gemini_key = settings.gemini_api_key
        
        if not gemini_key:
            return {
                "success": True,
                "corrected_text": text,
                "method_used": "fallback"
            }
        
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(prompt)
        corrected_text = response.text.strip()
        
        # 불필요한 텍스트 제거
        corrected_text = re.sub(r'^교정된 문장:\s*', '', corrected_text)
        corrected_text = re.sub(r'^결과:\s*', '', corrected_text)
        corrected_text = corrected_text.strip()
        
        if not corrected_text:
            corrected_text = text
        
        return {
            "success": True,
            "corrected_text": corrected_text,
            "method_used": "ai"
        }
        
    except Exception as e:
        logger.error(f"AI 문장 교정 실패: {e}")
        return {
            "success": True,
            "corrected_text": text,
            "method_used": "fallback"
        }

def correct_sentence_simple(text: str) -> str:
    """간단한 문장 교정 (규칙 기반)"""
    corrected = text
    
    # 기본적인 교정 규칙들
    corrections = {
        '이번 실수를 잘 구독하고': '이번 실수를 잘 고치고',
        '구속도 끌어져': '구석에 찌그러져',
        '화장품을 칠하실까': '화장품을 바르시겠어요',
        'diesel': '디젤',
        '녹음 테스트 중입니다': '녹음 테스트 중입니다.'
    }
    
    for wrong, correct in corrections.items():
        corrected = corrected.replace(wrong, correct)
    
    # 문장 끝 처리
    if corrected and not corrected.endswith(('.', '!', '?')):
        corrected += '.'
    
    return corrected 