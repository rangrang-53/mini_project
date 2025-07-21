"""
Pydantic 모델 정의

MBTI 분석기에서 사용하는 모든 데이터 모델들을 정의합니다.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class TextRequest(BaseModel):
    """텍스트 분석 요청 모델"""
    text: str


class DetailedAnalysisRequest(BaseModel):
    """상세 분석 요청 모델"""
    question: str
    answer: str
    score: float


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    score: float
    detailed_analysis: Optional[str] = None
    reasoning: Optional[str] = None
    suggestions: Optional[list] = None
    alternative_response: Optional[str] = None


class FinalAnalysisRequest(BaseModel):
    """최종 분석 요청 모델"""
    results: List[Dict]  # [{question, answer, score}, ...]


class FinalAnalysisResponse(BaseModel):
    """최종 분석 응답 모델"""
    overall_tendency: str
    personality_analysis: str
    communication_strategy: str
    strengths: List[str]
    growth_areas: List[str]
    keyword_analysis: Dict[str, Dict[str, int]]  # 카테고리별 키워드 사용 횟수


class QuestionGenerationRequest(BaseModel):
    """질문 생성 요청 모델"""
    count: Optional[int] = 5  # 생성할 질문 개수
    difficulty: Optional[str] = "medium"  # easy, medium, hard


class TTSRequest(BaseModel):
    """TTS 요청 모델"""
    text: str
    lang: str = 'ko' 