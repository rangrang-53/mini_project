"""
데이터 모델 정의

이 모듈은 MBTI 분석기에서 사용하는 모든 Pydantic 모델들을 정의합니다.
"""

from .schemas import (
    TextRequest,
    DetailedAnalysisRequest,
    AnalysisResponse,
    FinalAnalysisRequest,
    FinalAnalysisResponse,
    QuestionGenerationRequest,
    TTSRequest
)

__all__ = [
    "TextRequest",
    "DetailedAnalysisRequest", 
    "AnalysisResponse",
    "FinalAnalysisRequest",
    "FinalAnalysisResponse",
    "QuestionGenerationRequest",
    "TTSRequest"
] 