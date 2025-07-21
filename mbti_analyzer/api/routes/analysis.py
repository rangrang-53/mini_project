"""
분석 관련 API 엔드포인트

T/F 성향 분석과 관련된 API 엔드포인트들을 정의합니다.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging

from mbti_analyzer.core.analyzer import analyze_text

logger = logging.getLogger(__name__)

router = APIRouter()

class TextRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    score: float
    detailed_analysis: Optional[str] = None
    reasoning: Optional[str] = None
    suggestions: Optional[list] = None
    alternative_response: Optional[str] = None

class FinalAnalysisRequest(BaseModel):
    results: List[Dict]  # [{question, answer, score}, ...]

class FinalAnalysisResponse(BaseModel):
    overall_tendency: str
    personality_analysis: str
    communication_strategy: str
    strengths: List[str]
    growth_areas: List[str]
    keyword_analysis: Dict[str, Dict[str, int]]  # 카테고리별 키워드 사용 횟수

@router.post("/analyze")
@router.post("/api/v1/analyze")
async def analyze_text_endpoint(request: TextRequest):
    """텍스트를 분석하여 T/F 성향 점수를 반환합니다."""
    try:
        logger.info(f"🔍 텍스트 분석 요청 처리 중... (텍스트 길이: {len(request.text)})")
        
        # 텍스트 분석 수행
        result = await analyze_text(request.text)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="분석에 실패했습니다.")
        
        score = result["score"]
        method = result["method"]
        
        # 점수에 따른 상세 분석
        detailed_analysis = generate_detailed_analysis(score)
        reasoning = generate_reasoning(score, method)
        suggestions = generate_suggestions(score)
        alternative_response = generate_alternative_response(score)
        
        return AnalysisResponse(
            score=score,
            detailed_analysis=detailed_analysis,
            reasoning=reasoning,
            suggestions=suggestions,
            alternative_response=alternative_response
        )
        
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/final_analyze")
@router.post("/api/v1/final_analyze")
async def final_analyze_endpoint(request: FinalAnalysisRequest):
    """최종 분석 결과를 생성합니다."""
    try:
        logger.info(f"🔍 최종 분석 요청 처리 중... (결과 개수: {len(request.results)})")
        
        if not request.results:
            raise HTTPException(status_code=400, detail="분석 결과가 없습니다.")
        
        # 평균 점수 계산
        scores = [result["score"] for result in request.results]
        average_score = sum(scores) / len(scores)
        
        # 전체 성향 판단
        if average_score < 40:
            overall_tendency = "T (사고형)"
        elif average_score > 60:
            overall_tendency = "F (감정형)"
        else:
            overall_tendency = "균형형"
        
        # 성격 분석
        personality_analysis = generate_personality_analysis(average_score)
        
        # 소통 전략
        communication_strategy = generate_communication_strategy(average_score)
        
        # 강점과 성장 영역
        strengths, growth_areas = generate_strengths_and_growth(average_score)
        
        # 키워드 분석
        keyword_analysis = analyze_keywords(request.results)
        
        logger.info("✅ 최종 분석 완료")
        
        return FinalAnalysisResponse(
            overall_tendency=overall_tendency,
            personality_analysis=personality_analysis,
            communication_strategy=communication_strategy,
            strengths=strengths,
            growth_areas=growth_areas,
            keyword_analysis=keyword_analysis
        )
        
    except Exception as e:
        logger.error(f"최종 분석 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_detailed_analysis(score: float) -> str:
    """점수에 따른 상세 분석을 생성합니다."""
    if score < 30:
        return "강한 사고형(T) 성향을 보입니다. 논리적이고 객관적인 판단을 선호하며, 효율성과 정확성을 중시합니다."
    elif score < 45:
        return "사고형(T) 성향이 우세합니다. 체계적이고 분석적인 접근을 선호하며, 사실과 근거를 바탕으로 판단합니다."
    elif score < 55:
        return "균형잡힌 성향을 보입니다. 논리적 사고와 감정적 공감 능력이 균형을 이루고 있습니다."
    elif score < 70:
        return "감정형(F) 성향이 우세합니다. 관계와 조화를 중시하며, 공감과 배려를 바탕으로 소통합니다."
    else:
        return "강한 감정형(F) 성향을 보입니다. 감정적 공감 능력이 뛰어나며, 관계와 가치를 최우선으로 여깁니다."

def generate_reasoning(score: float, method: str) -> str:
    """분석 근거를 생성합니다."""
    method_text = {
        "gemini": "Gemini AI",
        "groq": "Groq AI",
        "fallback": "규칙 기반 분석"
    }.get(method, "AI 분석")
    
    return f"{method_text}를 통해 분석한 결과, T/F 성향 점수는 {score:.1f}점입니다."

def generate_suggestions(score: float) -> List[str]:
    """점수에 따른 제안사항을 생성합니다."""
    suggestions = []
    
    if score < 40:
        suggestions.extend([
            "상대방의 감정을 더 고려해보세요.",
            "논리적 설명 전에 공감의 말을 건네보세요.",
            "상대방의 입장에서 한 번 더 생각해보세요."
        ])
    elif score > 60:
        suggestions.extend([
            "객관적 사실도 함께 제시해보세요.",
            "논리적 근거를 더 명확히 설명해보세요.",
            "효율성과 정확성도 고려해보세요."
        ])
    else:
        suggestions.extend([
            "상황에 따라 적절한 접근 방식을 선택하세요.",
            "논리와 감정의 균형을 유지해보세요."
        ])
    
    return suggestions

def generate_alternative_response(score: float) -> str:
    """대안 답변을 생성합니다."""
    if score < 40:
        return "상대방의 기분을 먼저 물어보고 대화를 시작해보세요."
    elif score > 60:
        return "함께 해결책을 찾아보는 건 어떨까요?"
    else:
        return "상대방의 의견을 먼저 듣고 반응해보세요."

def generate_personality_analysis(score: float) -> str:
    """성격 분석을 생성합니다."""
    if score < 30:
        return "당신의 강점은 논리적 사고, 객관적 판단, 효율성 중시 입니다."
    elif score < 45:
        return "논리적 사고를 선호하지만 감정도 고려하는 균형잡힌 성향입니다."
    elif score < 55:
        return "논리와 감정의 균형을 잘 맞추는 성향입니다."
    elif score < 70:
        return "공감 능력이 뛰어나고 관계를 중시하는 성향입니다."
    else:
        return "감정적 공감 능력이 뛰어나고 사람과의 관계를 최우선으로 여깁니다."

def generate_communication_strategy(score: float) -> str:
    """소통 전략을 생성합니다."""
    if score < 40:
        return "T 성향 상대와 소통할 때는 논리적이고 객관적인 설명을 선호합니다."
    elif score > 60:
        return "F 성향 상대와 소통할 때는 감정적 공감을 먼저 표현하고 관계를 중시합니다."
    else:
        return "상대방의 성향에 따라 유연하게 소통 방식을 조정하세요."

def generate_strengths_and_growth(score: float) -> tuple:
    """강점과 성장 영역을 생성합니다."""
    if score < 40:
        strengths = ["논리적 사고", "객관적 판단", "효율성 중시"]
        growth_areas = ["감정적 공감", "관계 중시", "부드러운 표현"]
    elif score > 60:
        strengths = ["감정적 공감", "관계 중시", "따뜻한 표현"]
        growth_areas = ["논리적 사고", "객관적 판단", "효율성 중시"]
    else:
        strengths = ["균형잡힌 사고", "유연한 소통", "상황 적응"]
        growth_areas = ["더 나은 균형 유지"]
    
    return strengths, growth_areas

def analyze_keywords(results: List[Dict]) -> Dict[str, Dict[str, int]]:
    """키워드 분석을 수행합니다."""
    keyword_analysis = {
        "T_keywords": {},
        "F_keywords": {},
        "neutral_keywords": {}
    }
    
    # 간단한 키워드 카운팅 (실제로는 더 정교한 분석 필요)
    for result in results:
        text = result.get("answer", "").lower()
        
        # T 키워드
        t_keywords = ["논리", "분석", "효율", "객관", "사실", "확실", "해야"]
        for keyword in t_keywords:
            if keyword in text:
                keyword_analysis["T_keywords"][keyword] = keyword_analysis["T_keywords"].get(keyword, 0) + 1
        
        # F 키워드
        f_keywords = ["감정", "공감", "배려", "관계", "마음", "사랑", "따뜻"]
        for keyword in f_keywords:
            if keyword in text:
                keyword_analysis["F_keywords"][keyword] = keyword_analysis["F_keywords"].get(keyword, 0) + 1
    
    return keyword_analysis 