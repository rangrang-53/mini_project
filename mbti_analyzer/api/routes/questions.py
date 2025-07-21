"""
질문 관련 API 라우터

질문 생성, 로드, 관리 기능을 제공합니다.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mbti_analyzer.core.question_generator import generate_ai_questions, generate_fallback_questions
from mbti_analyzer.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class QuestionRequest(BaseModel):
    count: int = 5
    use_ai: bool = False
    category: Optional[str] = None

class QuestionResponse(BaseModel):
    questions: List[Dict[str, Any]]
    count: int
    source: str

def load_questions_from_file(file_path: str) -> List[Dict[str, Any]]:
    """파일에서 질문 로드"""
    try:
        # 동적 경로 사용
        full_path = settings.project_root / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'questions' in data:
                    return data['questions']
                else:
                    logger.warning(f"질문 파일 형식이 올바르지 않습니다: {file_path}")
                    return []
        else:
            logger.warning(f"질문 파일을 찾을 수 없습니다: {file_path}")
            return []
    except Exception as e:
        logger.error(f"질문 파일 로드 실패 {file_path}: {e}")
        return []

@router.get("/questions")
@router.get("/api/v1/questions")
async def get_questions_endpoint(count: int = 5, use_ai: bool = False):
    """질문 목록을 반환합니다."""
    try:
        logger.info(f"🔍 질문 로드 요청 처리 중... (count: {count})")
        
        # 질문 파일 경로들 (동적 경로 사용)
        question_files = [
            "question/question2.json",
            "question/questions.json",
            "question/questions_fine_tuned.json"
        ]
        
        questions = []
        
        # 파일에서 질문 로드 시도
        for file_path in question_files:
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

@router.post("/generate_questions")
@router.post("/api/v1/generate_questions")
async def generate_questions_endpoint(request: QuestionRequest):
    """AI를 사용하여 질문을 생성합니다."""
    try:
        logger.info(f"🤖 AI 질문 생성 요청 처리 중... (count: {request.count})")
        
        if request.use_ai:
            questions = generate_ai_questions(request.count)
            source = "ai"
        else:
            questions = generate_fallback_questions(request.count)
            source = "fallback"
        
        return {
            "questions": questions,
            "count": len(questions),
            "source": source
        }
        
    except Exception as e:
        logger.error(f"AI 질문 생성 오류: {e}")
        # 오류 시 기본 질문 반환
        fallback_questions = generate_fallback_questions(request.count)
        return {
            "questions": fallback_questions,
            "count": len(fallback_questions),
            "source": "fallback"
        }

@router.get("/question_files")
@router.get("/api/v1/question_files")
async def get_question_files():
    """사용 가능한 질문 파일 목록을 반환합니다."""
    try:
        question_dir = settings.question_dir
        available_files = []
        
        if question_dir.exists():
            for file_path in question_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        question_count = len(data) if isinstance(data, list) else len(data.get('questions', []))
                        available_files.append({
                            "filename": file_path.name,
                            "path": str(file_path.relative_to(settings.project_root)),
                            "question_count": question_count
                        })
                except Exception as e:
                    logger.warning(f"질문 파일 정보 읽기 실패 {file_path}: {e}")
        
        return {
            "available_files": available_files,
            "total_files": len(available_files)
        }
        
    except Exception as e:
        logger.error(f"질문 파일 목록 조회 오류: {e}")
        return {
            "available_files": [],
            "total_files": 0
        } 