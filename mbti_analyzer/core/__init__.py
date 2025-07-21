"""
핵심 분석 로직

이 패키지는 MBTI T/F 분석의 핵심 로직들을 포함합니다.
"""

# 상대 임포트 대신 절대 임포트 사용
try:
    from mbti_analyzer.core.analyzer import analyze_tf_tendency
    from mbti_analyzer.core.question_generator import generate_ai_questions, generate_fallback_questions
    from mbti_analyzer.core.final_analyzer import generate_final_analysis
except ImportError:
    # 로컬 테스트를 위한 대체 임포트
    from .analyzer import analyze_tf_tendency
    from .question_generator import generate_ai_questions, generate_fallback_questions
    from .final_analyzer import generate_final_analysis

__all__ = [
    "analyze_tf_tendency",
    "generate_ai_questions",
    "generate_fallback_questions", 
    "generate_final_analysis"
] 