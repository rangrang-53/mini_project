"""
MBTI T/F 성향 분석기

이 패키지는 사용자의 텍스트 응답을 분석하여 MBTI의 T(사고형)/F(감정형) 성향을 판단하는 
웹 애플리케이션입니다.

주요 기능:
- 텍스트 기반 T/F 성향 분석
- 실시간 감정 분석
- 음성 인식 (STT) 및 음성 합성 (TTS)
- AI 기반 질문 생성
- 다중 질문 분석 지원
"""

__version__ = "1.0.0"
__author__ = "MBTI Analyzer Team"
__description__ = "MBTI T/F 성향 분석기"

from .core.analyzer import analyze_tf_tendency
from .core.question_generator import generate_ai_questions
from .core.final_analyzer import generate_final_analysis

__all__ = [
    "analyze_tf_tendency",
    "generate_ai_questions", 
    "generate_final_analysis"
] 