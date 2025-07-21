"""
질문 관련 API 엔드포인트

질문 생성과 관련된 API 엔드포인트들을 정의합니다.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class QuestionGenerationRequest(BaseModel):
    count: Optional[int] = 5  # 생성할 질문 개수
    difficulty: Optional[str] = "medium"  # easy, medium, hard

def load_questions_from_file(file_path: str) -> List[str]:
    """파일에서 질문 목록을 로드합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            else:
                return []
    except Exception as e:
        logger.error(f"질문 파일 로드 실패: {e}")
        return []

def generate_fallback_questions(count: int = 5) -> List[str]:
    """기본 질문 목록을 반환합니다."""
    questions = [
        "나 또 헛소리했어?",
        "왜 화장품을 질렀을까?",
        "그냥 기분이 좋아진다",
        "우울하니까 구석에 찌그러져있는다",
        "너답지 않게 왜 겸손이냐",
        "역시 그게 너야",
        "그날이냐?",
        "이번 실수를 잘 고치고 다음 번에 조심합니다",
        "네, 화장품을 바르시겠어요?",
        "우울해서 모든 게 힘들다"
    ]
    return questions[:count]

@router.post("/generate_questions")
@router.post("/api/v1/generate_questions")
async def generate_questions_endpoint(request: QuestionGenerationRequest):
    """AI를 사용하여 질문을 생성합니다."""
    try:
        # 현재는 기본 질문 목록을 반환
        questions = generate_fallback_questions(request.count)
        
        return {
            "questions": questions,
            "count": len(questions),
            "method": "fallback"
        }
        
    except Exception as e:
        logger.error(f"질문 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/questions")
@router.get("/api/v1/questions")
async def get_questions_endpoint(count: int = 5, use_ai: bool = False):
    """질문 목록을 반환합니다."""
    try:
        logger.info(f"🔍 질문 로드 요청 처리 중... (count: {count})")
        
        # 질문 파일 경로들
        question_files = [
            "question/question2.json",
            "question/questions.json",
            "question/questions_fine_tuned.json"
        ]
        
        questions = []
        
        # 파일에서 질문 로드 시도
        for file_path in question_files:
            if os.path.exists(file_path):
                file_questions = load_questions_from_file(file_path)
                if file_questions:
                    questions.extend(file_questions)
                    break
        
        # 파일에서 로드하지 못한 경우 기본 질문 사용
        if not questions:
            questions = generate_fallback_questions(count)
        
        # 요청된 개수만큼 반환
        questions = questions[:count]
        
        return {
            "questions": questions,
            "count": len(questions),
            "source": "file" if questions != generate_fallback_questions(count) else "fallback"
        }
        
    except Exception as e:
        logger.error(f"질문 로드 오류: {e}")
        # 오류 시 기본 질문 반환
        fallback_questions = generate_fallback_questions(count)
        return {
            "questions": fallback_questions,
            "count": len(fallback_questions),
            "source": "fallback"
        } 