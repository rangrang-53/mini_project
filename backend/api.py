import sys
sys.path.append('.')

import os
import json
import logging
import asyncio
import sqlite3
import queue
import re
import random
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from groq import AsyncGroq
from dotenv import load_dotenv
import whisper
from gtts import gTTS
import tempfile

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 모듈화된 구조 import
from mbti_analyzer.core.analyzer import analyze_tf_tendency, generate_f_friendly_response, get_f_friendly_alternatives, get_t_strong_ment, get_t_mild_ment
from mbti_analyzer.core.question_generator import generate_ai_questions_real, generate_fallback_questions, generate_ai_questions
from mbti_analyzer.core.final_analyzer import generate_final_analysis
from mbti_analyzer.modules.stt_module import transcribe_audio_file
from mbti_analyzer.modules.tts_module import text_to_speech
from mbti_analyzer.modules.stt_module_enhanced import transcribe_audio_file_enhanced, validate_audio_quality
from mbti_analyzer.modules.sentence_correction_enhanced import correct_sentence_with_ai_enhanced

# 실시간 학습 시스템을 위한 데이터 클래스들
@dataclass
class UserInput:
    """사용자 입력 데이터"""
    question: str
    answer: str
    expected_score: float
    actual_score: float
    timestamp: datetime
    error: float
    is_acceptable: bool

@dataclass
class PromptVersion:
    """프롬프트 버전 정보"""
    version: str
    prompt: str
    performance: Dict
    created_at: datetime

class LearningFeedbackRequest(BaseModel):
    question: str
    answer: str
    expected_score: float
    actual_score: float

class LearningStatusResponse(BaseModel):
    enabled: bool
    total_inputs: int
    acceptable_rate: float
    average_error: float
    current_version: str

# 실시간 학습 시스템 초기화
class RealtimeLearningManager:
    def __init__(self):
        self.user_inputs_queue = queue.Queue()
        self.current_prompt_version = "v1.0"
        self.prompt_history = []
        self.performance_threshold = 0.6  # 60% 허용 오차 달성 시 개선
        self.min_inputs_for_tuning = 10   # 튜닝을 위한 최소 입력 수
        self.db_path = "learning_data.db"
        self.learning_enabled = True
        self.init_database()
        
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 사용자 입력 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                expected_score REAL,
                actual_score REAL,
                error REAL,
                is_acceptable BOOLEAN,
                timestamp DATETIME,
                prompt_version TEXT
            )
        ''')
        
        # 프롬프트 버전 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT,
                prompt TEXT,
                performance_data TEXT,
                created_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_error(self, expected: float, actual: float) -> float:
        """오차 계산"""
        return abs(expected - actual)
    
    def is_acceptable_error(self, error: float) -> bool:
        """오차가 허용 범위(10%) 내인지 확인"""
        return error <= 10.0
    
    async def process_user_input(self, question: str, answer: str, expected_score: float, actual_score: float) -> Dict:
        """사용자 입력 처리 및 학습"""
        if not self.learning_enabled:
            return {"success": True, "learning_disabled": True}
        
        print(f"🔄 실시간 학습: 사용자 입력 처리 중...")
        print(f"질문: {question}")
        print(f"답변: {answer}")
        print(f"예상: {expected_score}%, 실제: {actual_score}%")
        
        error = self.calculate_error(expected_score, actual_score)
        is_acceptable = self.is_acceptable_error(error)
        
        # 사용자 입력 저장
        user_input = UserInput(
            question=question,
            answer=answer,
            expected_score=expected_score,
            actual_score=actual_score,
            timestamp=datetime.now(),
            error=error,
            is_acceptable=is_acceptable
        )
        
        # 데이터베이스에 저장
        self.save_user_input(user_input)
        
        # 큐에 추가
        self.user_inputs_queue.put(user_input)
        
        # 성능 평가 및 필요시 튜닝
        await self.evaluate_and_tune_if_needed()
        
        status_emoji = "✅" if is_acceptable else "❌"
        print(f"{status_emoji} 학습 결과: 오차 {error:.1f}%")
        
        return {
            "success": True,
            "error": error,
            "is_acceptable": is_acceptable,
            "prompt_version": self.current_prompt_version
        }
    
    def save_user_input(self, user_input: UserInput):
        """사용자 입력을 데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_inputs 
            (question, answer, expected_score, actual_score, error, is_acceptable, timestamp, prompt_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_input.question,
            user_input.answer,
            user_input.expected_score,
            user_input.actual_score,
            user_input.error,
            user_input.is_acceptable,
            user_input.timestamp.isoformat(),
            self.current_prompt_version
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_performance(self, limit: int = 50) -> Dict:
        """최근 성능 데이터 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT expected_score, actual_score, error, is_acceptable
            FROM user_inputs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {
                "total_inputs": 0,
                "acceptable_rate": 0,
                "average_error": 0
            }
        
        total_inputs = len(results)
        acceptable_count = sum(1 for _, _, _, is_acceptable in results if is_acceptable)
        total_error = sum(error for _, _, error, _ in results)
        
        return {
            "total_inputs": total_inputs,
            "acceptable_rate": (acceptable_count / total_inputs) * 100,
            "average_error": total_error / total_inputs
        }
    
    async def evaluate_and_tune_if_needed(self):
        """성능 평가 및 필요시 튜닝"""
        performance = self.get_recent_performance()
        
        print(f"📊 현재 성능:")
        print(f"   - 총 입력: {performance['total_inputs']}개")
        print(f"   - 허용 비율: {performance['acceptable_rate']:.1f}%")
        print(f"   - 평균 오차: {performance['average_error']:.1f}%")
        
        # 튜닝 조건 확인
        if (performance['total_inputs'] >= self.min_inputs_for_tuning and 
            performance['acceptable_rate'] < self.performance_threshold * 100):
            
            print(f"⚠️  성능 개선 필요! 자동 튜닝 시작...")
            await self.auto_tune_prompt()
    
    async def auto_tune_prompt(self):
        """자동 프롬프트 튜닝"""
        print(f"🔧 프롬프트 자동 튜닝 중...")
        
        # 최근 입력 데이터 분석
        recent_inputs = self.get_recent_user_inputs(20)
        
        # 오차 패턴 분석
        error_patterns = self.analyze_error_patterns(recent_inputs)
        
        # 프롬프트 개선
        improved_prompt = self.generate_improved_prompt(error_patterns)
        
        # 새 버전 저장
        new_version = f"v{len(self.prompt_history) + 1}.0"
        self.save_prompt_version(new_version, improved_prompt)
        
        print(f"✅ 프롬프트 업데이트 완료: {new_version}")
        
        self.current_prompt_version = new_version
    
    def get_recent_user_inputs(self, limit: int = 20) -> List[UserInput]:
        """최근 사용자 입력 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, answer, expected_score, actual_score, error, is_acceptable, timestamp
            FROM user_inputs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            UserInput(
                question=row[0],
                answer=row[1],
                expected_score=row[2],
                actual_score=row[3],
                timestamp=datetime.fromisoformat(row[6]),
                error=row[4],
                is_acceptable=bool(row[5])
            )
            for row in results
        ]
    
    def analyze_error_patterns(self, inputs: List[UserInput]) -> Dict:
        """오차 패턴 분석"""
        high_errors = [i for i in inputs if i.error > 10]
        medium_errors = [i for i in inputs if 5 < i.error <= 10]
        low_errors = [i for i in inputs if i.error <= 5]
        
        # T 성향 과소 평가 패턴
        t_underestimated = [i for i in high_errors if i.actual_score < i.expected_score - 10]
        
        # F 성향 과소 평가 패턴
        f_underestimated = [i for i in high_errors if i.actual_score > i.expected_score + 10]
        
        return {
            "high_errors": high_errors,
            "medium_errors": medium_errors,
            "low_errors": low_errors,
            "t_underestimated": t_underestimated,
            "f_underestimated": f_underestimated
        }
    
    def generate_improved_prompt(self, error_patterns: Dict) -> str:
        """오차 패턴을 바탕으로 개선된 프롬프트 생성"""
        base_prompt = """
        MBTI T/F 성향 분석 전문가입니다. 답변을 분석하여 T/F 성향을 평가하세요.

        [분석 기준]
        - T(Thinking): 논리적, 객관적, 분석적 사고, 원인 분석, 체계적 접근, 효율성 중시, 문제 해결 지향
        - F(Feeling): 감정적, 공감적, 관계 중심적 사고, 기분 고려, 공감 표현, 관계 중시, 감정적 지지
        - 점수: 0(매우 강한 T) ~ 100(매우 강한 F), 50=균형

        [핵심 분석 원칙]
        1. 답변의 주요 의도와 핵심 메시지에 집중
        2. T 성향 강한 표현: "분석", "원인", "논리", "체계", "효율", "방지", "파악", "결과", "해결", "접근", "단계별", "체계적"
        3. F 성향 강한 표현: "기분", "마음", "공감", "힘들", "안타깝", "궁금", "도와", "함께", "지지", "위로", "걱정", "안타깝"
        4. 혼합 답변 분석: 
           - T+F 혼합 답변의 경우: 핵심 메시지의 방향성에 따라 판단
           - "분석하자" + "자책하지 마" → T 성향이 우선 (40-60점)
           - "함께 생각해보자" → F 성향이 우선 (60-80점)
        5. 맥락별 점수 가이드:
           - 순수 T 성향 (논리적 해결): 20-40점
           - T+F 혼합 (분석+공감): 40-70점  
           - 순수 F 성향 (감정적 지지): 70-90점

        [출력 형식]
        [분석] 답변자의 T/F 성향 분석 (성향 강도와 주요 특징 명시)
        [근거] 분석 근거 (구체적 키워드와 표현 방식, 의도 파악)
        [제안] 개선 제안 3가지
        [대안] 대안 답변
        점수: X

        답변: {text}
        """
        
        # 오차 패턴에 따른 개선사항 추가
        improvements = []
        
        if error_patterns["t_underestimated"]:
            improvements.append("⚠️ T 성향 과소 평가 문제 발견 - T 성향 분석 강화 필요")
            base_prompt += "\n[특별 주의사항]\n- T 성향 표현이 있는 경우 과소 평가하지 말 것\n- '논리적', '체계적', '분석적' 표현 시 T 점수 높게 부여"
        
        if error_patterns["f_underestimated"]:
            improvements.append("⚠️ F 성향 과소 평가 문제 발견 - F 성향 분석 강화 필요")
            base_prompt += "\n- F 성향 표현이 있는 경우 과소 평가하지 말 것\n- '공감', '지지', '위로' 표현 시 F 점수 높게 부여"
        
        return base_prompt
    
    def save_prompt_version(self, version: str, prompt: str):
        """프롬프트 버전 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        performance = self.get_recent_performance()
        
        cursor.execute('''
            INSERT INTO prompt_versions 
            (version, prompt, performance_data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            version,
            prompt,
            json.dumps(performance),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        self.prompt_history.append(PromptVersion(
            version=version,
            prompt=prompt,
            performance=performance,
            created_at=datetime.now()
        ))

# 전역 학습 매니저 인스턴스
learning_manager = RealtimeLearningManager()

# 모듈 연결 상태 로깅
print("=== MBTI T/F Analyzer 모듈 연결 상태 확인 ===")
logger.info("=== MBTI T/F Analyzer 모듈 연결 상태 확인 ===")
print("✅ 분석기 모듈 (mbti_analyzer.core.analyzer) - 연결됨")
logger.info("✅ 분석기 모듈 (mbti_analyzer.core.analyzer) - 연결됨")
print("✅ 질문 생성기 모듈 (mbti_analyzer.core.question_generator) - 연결됨")
logger.info("✅ 질문 생성기 모듈 (mbti_analyzer.core.question_generator) - 연결됨")
print("✅ 최종 분석기 모듈 (mbti_analyzer.core.final_analyzer) - 연결됨")
logger.info("✅ 최종 분석기 모듈 (mbti_analyzer.core.final_analyzer) - 연결됨")
print("✅ STT 모듈 (mbti_analyzer.modules.stt_module) - 연결됨")
logger.info("✅ STT 모듈 (mbti_analyzer.modules.stt_module) - 연결됨")
print("✅ TTS 모듈 (mbti_analyzer.modules.tts_module) - 연결됨")
logger.info("✅ TTS 모듈 (mbti_analyzer.modules.tts_module) - 연결됨")
print("=== 모든 모듈 연결 완료 ===")
logger.info("=== 모든 모듈 연결 완료 ===")

# 환경변수 로드
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 모델 초기화
print("Starting MBTI T/F Analyzer...")

# AI 모델 초기화 (Gemini 1순위, Groq 2순위)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Gemini 초기화
if GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-pro-latest')
    print("✅ Gemini AI 모델 초기화 완료 (1순위)", flush=True)
else:
    GEMINI_MODEL = None
    print("⚠️ GEMINI_API_KEY가 설정되지 않음.", flush=True)

# Groq 초기화 (백업용)
if GROQ_API_KEY:
    AI_CLIENT = AsyncGroq(api_key=GROQ_API_KEY)
    print("✅ Groq AI 모델 초기화 완료 (2순위)", flush=True)
else:
    AI_CLIENT = None
    print("⚠️ GROQ_API_KEY가 설정되지 않음.", flush=True)

# STT 모델 초기화
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded successfully!")

# 정적 파일들을 서비스
app.mount("/static", StaticFiles(directory="."), name="static")
app.mount("/Main_pg", StaticFiles(directory="Main_pg"), name="mainpg")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/Final", StaticFiles(directory="Final"), name="final")
app.mount("/Question_pg", StaticFiles(directory="Question_pg"), name="questionpg")

# 루트 경로에서 HTML 파일들 제공
from fastapi.responses import FileResponse

@app.get("/")
async def read_index():
    logger.info("🔍 루트 페이지 요청 처리 중...")
    try:
        response = FileResponse("index1.html")
        logger.info("✅ 루트 페이지 성공적으로 로드됨")
        return response
    except Exception as e:
        logger.error(f"❌ 루트 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/index1.html")
async def read_index1():
    return FileResponse("index1.html")

@app.get("/index2.html")
async def read_index2():
    return FileResponse("index2.html")

@app.get("/index3.html")
async def read_index3():
    return FileResponse("index3.html")

@app.get("/answer.html")
async def read_answer():
    return FileResponse("answer.html")

@app.get("/common.css")
async def read_css():
    return FileResponse("common.css")

@app.get("/favicon.ico")
async def get_favicon():
    """
    브라우저가 자동으로 요청하는 favicon.ico에 대한 응답
    """
    return Response(content="", media_type="image/x-icon")

class TextRequest(BaseModel):
    text: str

class SentenceCorrectionRequest(BaseModel):
    text: str

class DetailedAnalysisRequest(BaseModel):
    question: str
    answer: str
    score: float

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

class QuestionGenerationRequest(BaseModel):
    count: Optional[int] = 5  # 생성할 질문 개수
    difficulty: Optional[str] = "medium"  # easy, medium, hard

# generate_ai_questions_real, generate_fallback_questions, generate_ai_questions 함수는 mbti_analyzer.core.question_generator에서 import하여 사용

# analyze_tf_tendency 함수는 mbti_analyzer.core.analyzer에서 import하여 사용

# generate_f_friendly_response와 get_f_friendly_alternatives 함수는 mbti_analyzer.core.analyzer에서 import하여 사용

# generate_final_analysis 함수는 mbti_analyzer.core.final_analyzer에서 import하여 사용

def log_debug(msg):
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

@app.post("/analyze")
@app.post("/api/v1/analyze")
async def analyze_text(request: TextRequest):
    logger.info(f"🔍 텍스트 분석 요청 처리 중... (텍스트 길이: {len(request.text)})")
    with open("debug.log", "a", encoding="utf-8") as f:
        f.write("[DEBUG] analyze_text 함수 진입!\n")
    log_debug(f"[DEBUG] /analyze 요청 도착, AI_CLIENT: {AI_CLIENT}")
    log_debug(f"[DEBUG] 입력 텍스트: {request.text.strip()}")
    try:
        # Gemini 1순위 시도
        if GEMINI_MODEL:
            log_debug("[DEBUG] Gemini AI 분석 분기 진입 (1순위)")
            log_debug("[DEBUG] Gemini AI 모델 상태: 정상")
            try:
                prompt = f"""
                MBTI T/F 성향 분석 전문가입니다. 답변을 분석하여 T/F 성향을 평가하세요.

                [분석 기준]
                - T(Thinking): 논리적, 객관적, 분석적 사고, 원인 분석, 체계적 접근, 효율성 중시, 문제 해결 지향
                - F(Feeling): 감정적, 공감적, 관계 중심적 사고, 기분 고려, 공감 표현, 관계 중시, 감정적 지지
                - 점수: 0(매우 강한 T) ~ 100(매우 강한 F), 50=균형

                [핵심 분석 원칙]
                1. 답변의 주요 의도와 핵심 메시지에 집중
                2. T 성향 강한 표현: "분석", "원인", "논리", "체계", "효율", "방지", "파악", "결과", "해결", "접근", "단계별", "체계적"
                3. F 성향 강한 표현: "기분", "마음", "공감", "힘들", "안타깝", "궁금", "도와", "함께", "지지", "위로", "걱정", "안타깝"
                4. 혼합 답변 분석: 
                   - T+F 혼합 답변의 경우: 핵심 메시지의 방향성에 따라 판단
                   - "분석하자" + "자책하지 마" → T 성향이 우선 (40-60점)
                   - "함께 생각해보자" → F 성향이 우선 (60-80점)
                5. 맥락별 점수 가이드:
                   - 순수 T 성향 (논리적 해결): 20-40점
                   - T+F 혼합 (분석+공감): 40-70점  
                   - 순수 F 성향 (감정적 지지): 70-90점

                [출력 형식]
                [분석] 답변자의 T/F 성향 분석 (성향 강도와 주요 특징 명시)
                [근거] 분석 근거 (구체적 키워드와 표현 방식, 의도 파악)
                [제안] 개선 제안 3가지
                [대안] 대안 답변
                점수: X

                답변: {request.text.strip()}
                """
                
                log_debug("[DEBUG] Gemini AI에 분석 요청 전송 중...")
                import asyncio
                import re
                response = await asyncio.to_thread(GEMINI_MODEL.generate_content, prompt)
                result = response.text.strip()
                log_debug(f"[Gemini AI 원본 응답]: {result}")
                log_debug(f"[DEBUG] Gemini AI 응답 길이: {len(result)} 문자")
                
                # 점수 파싱 정규식 개선: 다양한 띄어쓰기/콜론/한글자 오타 허용
                score_match = re.search(r"점\s*수\s*[:：=\-]?\s*(\d{1,3})", result)
                if score_match:
                    tf_score = float(score_match.group(1))
                    log_debug(f"[DEBUG] Gemini AI 점수 파싱 성공: {tf_score}")
                elif (not result) or ("429" in result) or ("QUOTA" in result) or ("ERROR" in result):
                    log_debug("[Gemini 응답 비정상, Groq로 시도]")
                    raise Exception("Gemini 응답 비정상")
                else:
                    log_debug("[DEBUG] Gemini AI 점수 파싱 실패, 키워드 기반 점수 추정")
                    if 'T' in result and 'F' not in result:
                        tf_score = 20
                    elif 'F' in result and 'T' not in result:
                        tf_score = 80
                    elif any(k in result for k in ['B', '균형', '중립', '밸런스']):
                        tf_score = 50
                    elif 'T' in result and 'F' in result:
                        tf_score = 50
                    else:
                        log_debug(f"[Gemini AI 예외: 예상치 못한 응답] {result}")
                        raise Exception("Gemini 예상치 못한 응답")
                    log_debug(f"[DEBUG] 키워드 기반 추정 점수: {tf_score}")
                    log_debug("[분석 로직: gemini]")
                
                # 상세분석 파싱
                def extract(tag):
                    m = re.search(rf"\[{tag}\](.*?)(?=\[|$)", result, re.DOTALL)
                    return m.group(1).strip() if m else ""
                
                detailed_analysis = extract("분석")
                reasoning = extract("근거")
                suggestions_raw = extract("제안")
                suggestions = [s.strip() for s in suggestions_raw.split("\n") if s.strip()] if suggestions_raw else []
                alternative_response = extract("대안")
                tip = extract("실천팁")
                
                log_debug(f"[DEBUG] Gemini AI 분석 결과:")
                log_debug(f"[DEBUG] - 상세분석: {detailed_analysis[:100]}...")
                log_debug(f"[DEBUG] - 근거: {reasoning[:100]}...")
                log_debug(f"[DEBUG] - 제안 개수: {len(suggestions)}")
                log_debug(f"[DEBUG] - 대안: {alternative_response[:100]}...")
                log_debug(f"[DEBUG] - 실천팁: {tip[:100]}...")
                
                # 대안답변이 없거나 fallback일 때 랜덤 문구 추가 (F용, T강/약 구분)
                if (not alternative_response or alternative_response.strip() == "Gemini 분석 결과를 받아오지 못했습니다.") and (not tip or tip.strip() == ""):
                    log_debug("[DEBUG] Gemini AI 대안 답변 부족, 랜덤 문구 추가")
                    if tf_score <= 20:
                        one_liner = random.choice(get_t_strong_ment())
                    elif tf_score <= 40:
                        one_liner = random.choice(get_t_mild_ment())
                    else:
                        one_liner = random.choice(get_f_friendly_alternatives())
                    # Gemini 대안 제안이 있으면 그 아래에 추가
                    gemini_tip = tip
                    gemini_alt = extract("대안")
                    merged = []
                    if gemini_tip and gemini_tip.strip() != "Gemini 분석 결과를 받아오지 못했습니다.":
                        merged.append(gemini_tip.strip())
                    if gemini_alt and gemini_alt.strip() != "Gemini 분석 결과를 받아오지 못했습니다.":
                        merged.append(gemini_alt.strip())
                    if merged:
                        alternative_response = one_liner + "\n" + "\n".join(merged)
                else:
                    # 실천팁+대안이 있으면 합쳐서 반환
                    merged = []
                    if tip and tip.strip() != "Gemini 분석 결과를 받아오지 못했습니다.":
                        merged.append(tip.strip())
                    if alternative_response and alternative_response.strip() != "Gemini 분석 결과를 받아오지 못했습니다.":
                        merged.append(alternative_response.strip())
                    if merged:
                        alternative_response = "\n".join(merged)
                
                # --- 자연어 성향 파싱 및 점수 보정 ---
                def parse_tendency_score(text):
                    text = text.replace(" ", "")
                    # 강도 우선순위: 매우강한 > 강한 > 약한 > 균형/중립/밸런스
                    if re.search(r"매우강(한)?T성향", text):
                        return 5
                    if re.search(r"강(한)?T성향", text):
                        return 15
                    if re.search(r"약(한)?T성향", text):
                        return 35
                    if re.search(r"T와F의균형|논리와감정의균형|중립|밸런스", text):
                        return 50
                    if re.search(r"약(한)?F성향", text):
                        return 65
                    if re.search(r"강(한)?F성향", text):
                        return 85
                    if re.search(r"매우강(한)?F성향", text):
                        return 95
                    if re.search(r"T성향", text):
                        return 40
                    if re.search(r"F성향", text):
                        return 60
                    return None
                
                # 자연어 성향 점수 추출
                tendency_score = parse_tendency_score(detailed_analysis)
                log_debug(f"[DEBUG] 자연어 성향 점수: {tendency_score}")
                # 점수와 자연어가 불일치하면 자연어 기준으로 보정
                if tendency_score is not None and abs(tf_score - tendency_score) >= 10:
                    log_debug(f"[점수/자연어 불일치: Gemini 점수={tf_score}, 자연어 점수={tendency_score}, 자연어로 보정]")
                    tf_score = tendency_score
                
                log_debug(f"[DEBUG] Gemini AI 최종 분석 완료: 점수={tf_score}")
                return AnalysisResponse(
                    score=tf_score,
                    detailed_analysis=detailed_analysis,
                    reasoning=reasoning,
                    suggestions=suggestions,
                    alternative_response=alternative_response
                )
            except Exception as e:
                log_debug(f"[Gemini AI 예외 발생, Groq로 시도]: {e}")
                # Gemini 실패 시 Groq로 시도
                if AI_CLIENT:
                    try:
                        log_debug("[DEBUG] Groq AI 분석 분기 진입 (2순위)")
                        prompt = f"""
                        아래 답변은 T(사고형)인 내가 F(감정형)인 상대에게 한 말이야.
                        - F(감정형) 성향의 상대가 이 답변을 들었을 때 어떤 느낌일지, 그리고 F에게 더 효과적으로 소통하려면 어떻게 바꾸면 좋을지 분석해줘.
                        - 분석 결과(자연어)에는 반드시 '매우 강한 T 성향', '강한 F 성향', '약한 T 성향', 'T와 F의 균형', '중립', '밸런스' 등과 같이 '성향이 OOO하다'라는 문구를 명확하게 포함해서 작성해줘.
                        - 마지막에는 반드시 "점수: X" 형식으로 0~100 사이의 점수를 명시해줘. (0=매우 강한 T, 50=균형, 100=매우 강한 F)
                        - 분석 결과를 다음 형식으로 작성해줘:
                        [분석]
                        성향 분석 및 F 입장에서의 반응

                        [근거]
                        분석의 근거

                        [제안]
                        1. F가 공감할 수 있는 개선 제안 1
                        2. F가 공감할 수 있는 개선 제안 2
                        3. F가 공감할 수 있는 개선 제안 3

                        [실천팁]
                        F 성향 상대를 위한 한 줄 실천 팁

                        [대안]
                        F 성향 상대를 위한 대안 답변

                        점수: X (0=매우 강한 T, 50=균형, 100=매우 강한 F)

                        *** 중요: 모든 응답은 반드시 한국어로 작성해주세요. 영어는 절대 사용하지 마세요. ***

                        답변: {request.text.strip()}
                        """
                        response = await AI_CLIENT.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama3-8b-8192",
                        )
                        result = response.choices[0].message.content
                        if result is not None:
                            result = result.strip().upper()
                        else:
                            result = ""
                        log_debug(f"[Groq AI 원본 응답]: {result}")
                        
                        # 점수 파싱 정규식 개선: 다양한 띄어쓰기/콜론/한글자 오타 허용
                        score_match = re.search(r"점\s*수\s*[:：=\-]?\s*(\d{1,3})", result)
                        if score_match:
                            tf_score = float(score_match.group(1))
                        elif (not result) or ("429" in result) or ("QUOTA" in result) or ("ERROR" in result):
                            log_debug("[Groq 응답 비정상, fallback으로 자체 분석 수행]")
                            tf_score = analyze_tf_tendency(request.text)
                            log_debug("[분석 로직: fallback]")
                        else:
                            if 'T' in result and 'F' not in result:
                                tf_score = 20
                            elif 'F' in result and 'T' not in result:
                                tf_score = 80
                            elif any(k in result for k in ['B', '균형', '중립', '밸런스']):
                                tf_score = 50
                            elif 'T' in result and 'F' in result:
                                tf_score = 50
                            else:
                                log_debug(f"[Groq AI 예외: 예상치 못한 응답] {result}")
                                tf_score = analyze_tf_tendency(request.text)
                                log_debug("[분석 로직: fallback]")
                            log_debug("[분석 로직: groq]")
                        
                        # 상세분석 파싱
                        def extract(tag):
                            content = response.choices[0].message.content
                            if content is None:
                                return ""
                            m = re.search(rf"\[{tag}\](.*?)(?=\[|$)", content, re.DOTALL)
                            return m.group(1).strip() if m else ""
                        
                        detailed_analysis = extract("분석")
                        reasoning = extract("근거")
                        suggestions_raw = extract("제안")
                        suggestions = [s.strip() for s in suggestions_raw.split("\n") if s.strip()] if suggestions_raw else []
                        alternative_response = extract("대안")
                        tip = extract("실천팁")
                        
                        # 대안답변이 없거나 fallback일 때 랜덤 문구 추가 (F용, T강/약 구분)
                        if (not alternative_response or alternative_response.strip() == "Groq 분석 결과를 받아오지 못했습니다.") and (not tip or tip.strip() == ""):
                            if tf_score <= 20:
                                one_liner = random.choice(get_t_strong_ment())
                            elif tf_score <= 40:
                                one_liner = random.choice(get_t_mild_ment())
                            else:
                                one_liner = random.choice(get_f_friendly_alternatives())
                            # Groq 대안 제안이 있으면 그 아래에 추가
                            groq_tip = tip
                            groq_alt = extract("대안")
                            merged = []
                            if groq_tip and groq_tip.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                                merged.append(groq_tip.strip())
                            if groq_alt and groq_alt.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                                merged.append(groq_alt.strip())
                            if merged:
                                alternative_response = one_liner + "\n" + "\n".join(merged)
                            else:
                                alternative_response = one_liner
                        else:
                            # 실천팁+대안이 있으면 합쳐서 반환
                            merged = []
                            if tip and tip.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                                merged.append(tip.strip())
                            if alternative_response and alternative_response.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                                merged.append(alternative_response.strip())
                            if merged:
                                alternative_response = "\n".join(merged)
                        
                        # --- 자연어 성향 파싱 및 점수 보정 ---
                        def parse_tendency_score(text):
                            text = text.replace(" ", "")
                            # 강도 우선순위: 매우강한 > 강한 > 약한 > 균형/중립/밸런스
                            if re.search(r"매우강(한)?T성향", text):
                                return 5
                            if re.search(r"강(한)?T성향", text):
                                return 15
                            if re.search(r"약(한)?T성향", text):
                                return 35
                            if re.search(r"T와F의균형|논리와감정의균형|중립|밸런스", text):
                                return 50
                            if re.search(r"약(한)?F성향", text):
                                return 65
                            if re.search(r"강(한)?F성향", text):
                                return 85
                            if re.search(r"매우강(한)?F성향", text):
                                return 95
                            if re.search(r"T성향", text):
                                return 40
                            if re.search(r"F성향", text):
                                return 60
                            return None
                        
                        # 자연어 성향 점수 추출
                        tendency_score = parse_tendency_score(detailed_analysis)
                        # 점수와 자연어가 불일치하면 자연어 기준으로 보정
                        if tendency_score is not None and abs(tf_score - tendency_score) >= 10:
                            log_debug(f"[점수/자연어 불일치: Groq 점수={tf_score}, 자연어 점수={tendency_score}, 자연어로 보정]")
                            tf_score = tendency_score
                        
                        return AnalysisResponse(
                            score=tf_score,
                            detailed_analysis=detailed_analysis,
                            reasoning=reasoning,
                            suggestions=suggestions,
                            alternative_response=alternative_response
                        )
                    except Exception as groq_e:
                        log_debug(f"[Groq AI 예외 발생, fallback으로 자체 분석 수행]: {groq_e}")
                        tf_score = analyze_tf_tendency(request.text)
                        log_debug("[분석 로직: fallback]")
                        return AnalysisResponse(score=tf_score)
                else:
                    # Groq도 없으면 fallback
                    tf_score = analyze_tf_tendency(request.text)
                    log_debug("[분석 로직: fallback]")
                    return AnalysisResponse(score=tf_score)
        # Gemini가 없으면 Groq 시도
        elif AI_CLIENT:
            log_debug("[DEBUG] Groq AI 분석 분기 진입 (1순위)")
            try:
                prompt = f"""
                아래 답변은 T(사고형)인 내가 F(감정형)인 상대에게 한 말이야.
                - F(감정형) 성향의 상대가 이 답변을 들었을 때 어떤 느낌일지, 그리고 F에게 더 효과적으로 소통하려면 어떻게 바꾸면 좋을지 분석해줘.
                - 분석 결과(자연어)에는 반드시 '매우 강한 T 성향', '강한 F 성향', '약한 T 성향', 'T와 F의 균형', '중립', '밸런스' 등과 같이 '성향이 OOO하다'라는 문구를 명확하게 포함해서 작성해줘.
                - 마지막에는 반드시 "점수: X" 형식으로 0~100 사이의 점수를 명시해줘. (0=매우 강한 T, 50=균형, 100=매우 강한 F)
                - 분석 결과를 다음 형식으로 작성해줘:
                [분석]
                성향 분석 및 F 입장에서의 반응

                [근거]
                분석의 근거

                [제안]
                1. F가 공감할 수 있는 개선 제안 1
                2. F가 공감할 수 있는 개선 제안 2
                3. F가 공감할 수 있는 개선 제안 3

                [실천팁]
                F 성향 상대를 위한 한 줄 실천 팁

                [대안]
                F 성향 상대를 위한 대안 답변

                점수: X (0=매우 강한 T, 50=균형, 100=매우 강한 F)

                *** 중요: 모든 응답은 반드시 한국어로 작성해주세요. 영어는 절대 사용하지 마세요. ***

                답변: {request.text.strip()}
                """
                response = await AI_CLIENT.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                )
                result = response.choices[0].message.content
                if result is not None:
                    result = result.strip().upper()
                else:
                    result = ""
                log_debug(f"[Groq AI 원본 응답]: {result}")
                import re
                # 점수 파싱 정규식 개선: 다양한 띄어쓰기/콜론/한글자 오타 허용
                score_match = re.search(r"점\s*수\s*[:：=\-]?\s*(\d{1,3})", result)
                if score_match:
                    tf_score = float(score_match.group(1))
                elif (not result) or ("429" in result) or ("QUOTA" in result) or ("ERROR" in result):
                    log_debug("[Groq 응답 비정상, fallback으로 자체 분석 수행]")
                    tf_score = analyze_tf_tendency(request.text)
                    log_debug("[분석 로직: fallback]")
                else:
                    if 'T' in result and 'F' not in result:
                        tf_score = 20
                    elif 'F' in result and 'T' not in result:
                        tf_score = 80
                    elif any(k in result for k in ['B', '균형', '중립', '밸런스']):
                        tf_score = 50
                    elif 'T' in result and 'F' in result:
                        tf_score = 50
                    else:
                        log_debug(f"[Groq AI 예외: 예상치 못한 응답] {result}")
                        tf_score = analyze_tf_tendency(request.text)
                        log_debug("[분석 로직: fallback]")
                    log_debug("[분석 로직: groq]")
                # 상세분석 파싱
                def extract(tag):
                    content = response.choices[0].message.content
                    if content is None:
                        return ""
                    m = re.search(rf"\[{tag}\](.*?)(?=\[|$)", content, re.DOTALL)
                    return m.group(1).strip() if m else ""
                detailed_analysis = extract("분석")
                reasoning = extract("근거")
                suggestions_raw = extract("제안")
                suggestions = [s.strip() for s in suggestions_raw.split("\n") if s.strip()] if suggestions_raw else []
                alternative_response = extract("대안")
                tip = extract("실천팁")
                # 대안답변이 없거나 fallback일 때 랜덤 문구 추가 (F용, T강/약 구분)
                if (not alternative_response or alternative_response.strip() == "Groq 분석 결과를 받아오지 못했습니다.") and (not tip or tip.strip() == ""):
                    if tf_score <= 20:
                        one_liner = random.choice(get_t_strong_ment())
                    elif tf_score <= 40:
                        one_liner = random.choice(get_t_mild_ment())
                    else:
                        one_liner = random.choice(get_f_friendly_alternatives())
                    # Groq 대안 제안이 있으면 그 아래에 추가
                    groq_tip = tip
                    groq_alt = extract("대안")
                    merged = []
                    if groq_tip and groq_tip.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                        merged.append(groq_tip.strip())
                    if groq_alt and groq_alt.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                        merged.append(groq_alt.strip())
                    if merged:
                        alternative_response = one_liner + "\n" + "\n".join(merged)
                    else:
                        alternative_response = one_liner
                else:
                    # 실천팁+대안이 있으면 합쳐서 반환
                    merged = []
                    if tip and tip.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                        merged.append(tip.strip())
                    if alternative_response and alternative_response.strip() != "Groq 분석 결과를 받아오지 못했습니다.":
                        merged.append(alternative_response.strip())
                    if merged:
                        alternative_response = "\n".join(merged)
                # --- 자연어 성향 파싱 및 점수 보정 ---
                def parse_tendency_score(text):
                    text = text.replace(" ", "")
                    # 강도 우선순위: 매우강한 > 강한 > 약한 > 균형/중립/밸런스
                    if re.search(r"매우강(한)?T성향", text):
                        return 5
                    if re.search(r"강(한)?T성향", text):
                        return 15
                    if re.search(r"약(한)?T성향", text):
                        return 35
                    if re.search(r"T와F의균형|논리와감정의균형|중립|밸런스", text):
                        return 50
                    if re.search(r"약(한)?F성향", text):
                        return 65
                    if re.search(r"강(한)?F성향", text):
                        return 85
                    if re.search(r"매우강(한)?F성향", text):
                        return 95
                    if re.search(r"T성향", text):
                        return 40
                    if re.search(r"F성향", text):
                        return 60
                    return None
                # 자연어 성향 점수 추출
                tendency_score = parse_tendency_score(detailed_analysis)
                # 점수와 자연어가 불일치하면 자연어 기준으로 보정
                if tendency_score is not None and abs(tf_score - tendency_score) >= 10:
                    log_debug(f"[점수/자연어 불일치: Groq 점수={tf_score}, 자연어 점수={tendency_score}, 자연어로 보정]")
                    tf_score = tendency_score
                return AnalysisResponse(
                    score=tf_score,
                    detailed_analysis=detailed_analysis,
                    reasoning=reasoning,
                    suggestions=suggestions,
                    alternative_response=alternative_response
                )
            except Exception as e:
                log_debug(f"[Groq AI 예외 발생, fallback으로 자체 분석 수행]: {e}")
                tf_score = analyze_tf_tendency(request.text)
                log_debug("[분석 로직: fallback]")
                return AnalysisResponse(score=tf_score)
        else:
            log_debug("[DEBUG] Fallback(키워드 분석) 분기 진입")
            tf_score = analyze_tf_tendency(request.text)
            log_debug("[분석 로직: fallback]")
            return AnalysisResponse(score=tf_score)
    except Exception as e:
        log_debug(f"[analyze_text 최상위 예외]: {e}")
        tf_score = analyze_tf_tendency(request.text)
        log_debug("[분석 로직: fallback]")
        return AnalysisResponse(score=tf_score)

@app.post("/final_analyze")
@app.post("/api/v1/final_analyze")
async def final_analyze(request: FinalAnalysisRequest):
    logger.info(f"🔍 최종 분석 요청 처리 중... (결과 개수: {len(request.results)})")
    try:
        final_result = generate_final_analysis(request.results)
        logger.info("✅ 최종 분석 완료")
        return final_result
    except Exception as e:
        logger.error(f"❌ 최종 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_questions")
@app.post("/api/v1/generate_questions")
async def generate_questions(request: QuestionGenerationRequest):
    """
    AI 기반으로 새로운 질문들을 생성합니다.
    """
    try:
        questions = await generate_ai_questions_real(count=request.count or 5, difficulty=request.difficulty or "medium")
        return {
            "questions": questions,
            "count": len(questions),
            "difficulty": request.difficulty,
            "generated_by": "AI"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 생성 중 오류가 발생했습니다: {str(e)}")

@app.get("/questions")
@app.get("/api/v1/questions")
async def get_questions(count: int = 5):
    """
    questions.json 파일에서 질문들을 반환합니다.
    """
    logger.info(f"🔍 질문 로드 요청 처리 중... (count: {count})")
    try:
        # questions.json 파일 사용
        questions_file = Path("question/questions.json")
        if not questions_file.exists():
            raise HTTPException(status_code=404, detail="질문 파일을 찾을 수 없습니다.")
        
        with open(questions_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        
        questions_list = questions_data.get("questions", [])
        
        # 요청된 개수만큼 랜덤 선택 (Fisher-Yates 셔플 알고리즘 사용)
        import random
        if len(questions_list) > count:
            # 전체 리스트를 셔플한 후 앞에서부터 선택
            shuffled = questions_list.copy()
            random.shuffle(shuffled)
            selected_questions = shuffled[:count]
        else:
            # 전체 리스트가 요청 개수보다 적으면 전체를 셔플해서 반환
            selected_questions = questions_list.copy()
            random.shuffle(selected_questions)
        
        return {
            "questions": selected_questions,
            "source": "questions.json",
            "count": len(selected_questions),
            "total_available": len(questions_list)
        }
            
    except json.JSONDecodeError:
        # JSON 파일 오류 시 기본 질문 사용
        return {
            "questions": ["질문을 불러올 수 없습니다. 서버를 확인해주세요."],
            "source": "error_fallback",
            "count": 1,
            "difficulty": "medium"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset_log")
async def reset_log():
    try:
        with open("debug.log", "w", encoding="utf-8") as f:
            f.write("[DEBUG] 로그가 초기화되었습니다!\n")
            f.write(f"[DEBUG] 초기화 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("[DEBUG] UTF-8 인코딩으로 정상 초기화됨\n")
        logger.info("✅ 로그 파일 초기화 완료")
        return Response(content="로그 초기화 완료", media_type="text/plain")
    except Exception as e:
        logger.error(f"❌ 로그 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"로그 초기화 실패: {str(e)}")

def get_t_strong_ment():
    return [
        "뼈 맞았어…",
        "어디보자 데스노트가...",
        "복수한다…",
        "넌 진짜 감정이란 게 있니?",
        "넌 D졌다",
        "조만간 순살만들어준다",
        "로봇이냐..?",
        "유 스틸 마이 데스노트 넘버원~",
        "우리 헤어져",
        "저리가 ㅠㅠ"
    ]

def get_t_mild_ment():
    return [
        "계산기냐?",
        "님 배려좀...",
        "로봇이냐?",
        "살살해주세요..",
        "니 말도 맞는데.. 살살좀 ㅠ",
        "내 기분 존중좀 ㅠ",
        "말 대신 결과?",
        "감정도 좀 챙기라구!",
        "네 논리 따라가다 머리 터져 죽겠어",
        "팩트부터 정리해라? 내 마음은 누가 정리해줘?"
    ]

@app.post("/stt")
@app.post("/api/v1/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Speech to text endpoint that accepts audio file uploads
    """
    logger.info(f"🔍 STT 요청 처리 중... (파일명: {audio_file.filename})")
    try:
        if not audio_file:
            logger.error("❌ 오디오 파일이 제공되지 않음")
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # 파일 확장자 검사
        allowed_extensions = ['.wav', '.mp3', '.ogg', '.m4a']
        filename = audio_file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        # 임시 파일로 저장
        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_audio:
                temp_audio_path = temp_audio.name
                content = await audio_file.read()
                temp_audio.write(content)
                temp_audio.flush()
                os.fsync(temp_audio.fileno())
            
            print(f"Processing audio file: {temp_audio_path}")
            # 모듈화된 STT 함수 사용
            text = transcribe_audio_file(temp_audio_path)
            print(f"STT result: {text}")
            return {"text": text}
            
        finally:
            # 임시 파일 삭제
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except Exception as e:
                    print(f"Failed to delete temp file: {e}")
    except Exception as e:
        print(f"STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt_enhanced")
@app.post("/api/v1/stt_enhanced")
async def speech_to_text_enhanced(audio_file: UploadFile = File(...)):
    """
    향상된 STT 기능 - 더 정확한 음성 인식과 품질 검증
    """
    logger.info(f"🔍 향상된 STT 요청 처리 중... (파일명: {audio_file.filename})")
    
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f"Processing audio file: {temp_file_path}")
        
        try:
            # 1단계: 오디오 품질 검증
            quality_result = validate_audio_quality(temp_file_path)
            
            # numpy 타입을 Python 기본 타입으로 변환
            if isinstance(quality_result, dict):
                for key, value in quality_result.items():
                    if hasattr(value, 'item'):  # numpy 타입인 경우
                        quality_result[key] = float(value)
                    elif isinstance(value, (list, dict)):
                        # 리스트나 딕셔너리 내부의 numpy 타입도 변환
                        if isinstance(value, list):
                            quality_result[key] = [float(v) if hasattr(v, 'item') else v for v in value]
            
            # 2단계: 향상된 STT 처리
            stt_result = transcribe_audio_file_enhanced(temp_file_path)
            
            # 3단계: 결과 정리
            response_data = {
                "text": stt_result["text"],
                "original_text": stt_result["original_text"],
                "confidence": stt_result["confidence"],
                "alternatives": stt_result["alternatives"],
                "has_alternatives": stt_result["has_alternatives"],
                "audio_quality": quality_result,
                "suggestions": []
            }
            
            # 4단계: 품질 기반 제안 추가
            if not quality_result["is_good"]:
                response_data["suggestions"].extend(quality_result["suggestions"])
            
            if stt_result["confidence"] < 0.7:
                response_data["suggestions"].append("음성 인식 정확도가 낮습니다. 더 명확하게 말씀해주세요.")
            
            logger.info(f"향상된 STT 결과: '{stt_result['text']}' (신뢰도: {stt_result['confidence']:.2f})")
            
            return response_data
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"향상된 STT 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"향상된 STT 처리 중 오류 발생: {str(e)}")

@app.post("/correct_sentence")
@app.post("/api/v1/correct_sentence")
async def correct_sentence(request: SentenceCorrectionRequest):
    """
    STT 결과 문장을 교정합니다.
    """
    logger.info(f"🔍 문장 교정 요청 처리 중... (텍스트: {request.text})")
    
    try:
        # 문장 교정 프롬프트 생성 (더 구체적이고 명확한 지시사항)
        prompt = f"""
다음 음성 인식 결과를 자연스럽고 문법적으로 올바른 한국어 문장으로 교정해주세요.

교정 규칙:
1. 오타나 잘못된 단어를 올바른 단어로 수정
2. 문법 오류를 수정 (조사, 어미 등)
3. 불완전한 문장을 완성
4. 원래 의미는 반드시 유지
5. 교정된 문장만 출력 (설명 없이)

음성 인식 결과: "{request.text}"

교정된 문장:
"""
        
        # AI 모델을 사용하여 문장 교정
        try:
            # Gemini AI 직접 사용
            import google.generativeai as genai
            from mbti_analyzer.config.settings import settings
            
            # Gemini AI 설정
            import os
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                # settings에서 확인
                gemini_key = settings.gemini_api_key
                if not gemini_key:
                    raise Exception("Gemini API 키가 설정되지 않았습니다. 환경 변수 GEMINI_API_KEY를 설정해주세요.")
            
            logger.info(f"Gemini API 키 확인: {gemini_key[:10]}...")
            genai.configure(api_key=gemini_key)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # AI 응답 생성
            response = model.generate_content(prompt)
            corrected_text = response.text.strip()
            
            logger.info(f"AI 응답 원본: {corrected_text}")
            
            # 교정 결과 정리
            if corrected_text and isinstance(corrected_text, str):
                # 불필요한 부분 제거
                corrected_text = corrected_text.replace("교정된 문장:", "").strip()
                corrected_text = corrected_text.replace("교정:", "").strip()
                corrected_text = corrected_text.replace("수정된 문장:", "").strip()
                corrected_text = corrected_text.replace("결과:", "").strip()
                corrected_text = corrected_text.replace("답변:", "").strip()
                
                # 줄바꿈 정리
                corrected_text = corrected_text.replace("\n", " ").strip()
                
                # 따옴표 제거
                corrected_text = corrected_text.strip('"').strip("'").strip()
                
                # 빈 문자열 체크
                if not corrected_text:
                    corrected_text = request.text
                
                logger.info(f"정리된 교정 결과: '{corrected_text}'")
                
                # 원본과 동일한 경우 원본 반환
                has_changes = corrected_text != request.text
                
                if not has_changes:
                    logger.info("교정 결과가 원본과 동일함")
                
                return {
                    "success": True,
                    "original_text": request.text,
                    "corrected_text": corrected_text,
                    "has_changes": has_changes,
                    "ai_response": response.text.strip()  # 디버깅용
                }
            else:
                raise Exception("AI 문장 교정 생성 실패")
                
        except Exception as ai_error:
            logger.error(f"AI 문장 교정 실패: {ai_error}")
            # AI 실패 시 원본 텍스트 반환
            return {
                "success": True,
                "original_text": request.text,
                "corrected_text": request.text,
                "has_changes": False,
                "fallback": True,
                "error": str(ai_error),
                "error_type": type(ai_error).__name__
            }
            
    except Exception as e:
        logger.error(f"문장 교정 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문장 교정 처리 중 오류 발생: {str(e)}")

@app.post("/correct_sentence_enhanced")
@app.post("/api/v1/correct_sentence_enhanced")
async def correct_sentence_enhanced(request: SentenceCorrectionRequest):
    """
    향상된 문장 교정 기능 - AI와 규칙 기반 교정을 결합
    """
    logger.info(f"🔍 향상된 문장 교정 요청 처리 중... (텍스트: {request.text})")
    
    try:
        # 문맥 감지 (MBTI 질문인지 확인)
        context = 'general'
        mbti_keywords = ['생각', '느낌', '감정', '논리', '사실', '객관', '주관']
        if any(keyword in request.text for keyword in mbti_keywords):
            context = 'mbti_question'
        
        # 향상된 문장 교정 수행
        result = await correct_sentence_with_ai_enhanced(request.text, context)
        
        if result["success"]:
            logger.info(f"향상된 교정 결과: '{result['corrected_text']}' (방법: {result['method_used']})")
            return result
        else:
            # 실패 시 기존 교정 시스템 사용
            logger.warning("향상된 교정 실패, 기존 시스템으로 대체")
            return await correct_sentence(request)
            
    except Exception as e:
        logger.error(f"향상된 문장 교정 처리 중 오류: {e}")
        # 오류 시 기존 교정 시스템으로 대체
        return await correct_sentence(request)

@app.post("/audio_quality_check")
@app.post("/api/v1/audio_quality_check")
async def check_audio_quality(audio_file: UploadFile = File(...)):
    """
    오디오 품질 검증 및 개선 제안
    """
    logger.info(f"🔍 오디오 품질 검증 요청 처리 중... (파일명: {audio_file.filename})")
    
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 오디오 품질 검증
            quality_result = validate_audio_quality(temp_file_path)
            
            logger.info(f"오디오 품질 검증 완료: 점수 {quality_result['quality_score']:.2f}")
            
            return {
                "success": True,
                "quality_score": quality_result["quality_score"],
                "duration": quality_result["duration"],
                "rms_energy": quality_result["rms_energy"],
                "issues": quality_result["issues"],
                "suggestions": quality_result["suggestions"],
                "is_good": quality_result["is_good"]
            }
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"오디오 품질 검증 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 품질 검증 중 오류 발생: {str(e)}")

@app.get("/stt_enhancement_status")
@app.get("/api/v1/stt_enhancement_status")
async def get_stt_enhancement_status():
    """
    STT 향상 기능 상태 확인
    """
    try:
        # 향상된 모듈 사용 가능 여부 확인
        enhanced_modules_available = True
        missing_modules = []
        
        try:
            from mbti_analyzer.modules.stt_module_enhanced import transcribe_audio_file_enhanced
        except ImportError:
            enhanced_modules_available = False
            missing_modules.append("stt_module_enhanced")
        
        try:
            from mbti_analyzer.modules.sentence_correction_enhanced import correct_sentence_with_ai_enhanced
        except ImportError:
            enhanced_modules_available = False
            missing_modules.append("sentence_correction_enhanced")
        
        return {
            "enhanced_features_available": enhanced_modules_available,
            "missing_modules": missing_modules,
            "available_endpoints": [
                "/stt_enhanced",
                "/correct_sentence_enhanced", 
                "/audio_quality_check"
            ] if enhanced_modules_available else [],
            "recommendations": [
                "향상된 STT 기능을 사용하려면 /stt_enhanced 엔드포인트를 사용하세요",
                "향상된 문장 교정을 사용하려면 /correct_sentence_enhanced 엔드포인트를 사용하세요",
                "오디오 품질을 미리 확인하려면 /audio_quality_check 엔드포인트를 사용하세요"
            ] if enhanced_modules_available else [
                "향상된 모듈이 설치되지 않았습니다. 기본 기능을 사용하세요."
            ]
        }
        
    except Exception as e:
        logger.error(f"STT 향상 기능 상태 확인 중 오류: {e}")
        return {
            "enhanced_features_available": False,
            "error": str(e)
        }

# 실시간 학습 시스템 API 엔드포인트들
@app.post("/api/v1/learning/feedback")
async def submit_learning_feedback(request: LearningFeedbackRequest):
    """학습 피드백 제출"""
    try:
        result = await learning_manager.process_user_input(
            request.question,
            request.answer,
            request.expected_score,
            request.actual_score
        )
        return {
            "success": True,
            "learning_result": result,
            "message": "학습 피드백이 성공적으로 처리되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"학습 처리 중 오류 발생: {str(e)}")

@app.get("/api/v1/learning/status")
async def get_learning_status() -> LearningStatusResponse:
    """학습 상태 조회"""
    performance = learning_manager.get_recent_performance()
    return LearningStatusResponse(
        enabled=learning_manager.learning_enabled,
        total_inputs=performance["total_inputs"],
        acceptable_rate=performance["acceptable_rate"],
        average_error=performance["average_error"],
        current_version=learning_manager.current_prompt_version
    )

@app.post("/api/v1/learning/toggle")
async def toggle_learning(enabled: bool = True):
    """학습 기능 켜기/끄기"""
    learning_manager.learning_enabled = enabled
    return {
        "success": True,
        "enabled": learning_manager.learning_enabled,
        "message": f"실시간 학습이 {'활성화' if enabled else '비활성화'}되었습니다."
    }

@app.get("/api/v1/learning/history")
async def get_learning_history():
    """학습 히스토리 조회"""
    conn = sqlite3.connect(learning_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT question, answer, expected_score, actual_score, error, is_acceptable, timestamp, prompt_version
        FROM user_inputs
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    history = []
    for row in results:
        history.append({
            "question": row[0],
            "answer": row[1],
            "expected_score": row[2],
            "actual_score": row[3],
            "error": row[4],
            "is_acceptable": bool(row[5]),
            "timestamp": row[6],
            "prompt_version": row[7]
        })
    
    return {
        "success": True,
        "history": history,
        "total_count": len(history)
    }

@app.get("/index_with_learning.html")
async def read_index_with_learning():
    """실시간 학습이 통합된 메인 페이지"""
    return FileResponse("index_with_learning.html")

@app.post("/tts")
@app.post("/api/v1/tts")
async def text_to_speech_endpoint(request: TextRequest = None, text: str = Form(None)):
    """
    Text to speech endpoint that converts text to audio
    Supports both JSON and FormData requests
    """
    # 텍스트 추출 (JSON 또는 FormData)
    if request and request.text:
        text_content = request.text
    elif text:
        text_content = text
    else:
        logger.error("❌ 텍스트가 제공되지 않음")
        raise HTTPException(status_code=400, detail="No text provided")
    
    logger.info(f"🔍 TTS 요청 처리 중... (텍스트 길이: {len(text_content)})")
    try:
        # 모듈화된 TTS 함수 사용 (gTTS)
        audio_path = text_to_speech(
            text=text_content,
            lang='ko-KR',
            voice_name='ko-KR-Chirp3-HD-Leda',
            gender='FEMALE',
            speaking_rate=1.1,
            pitch=0.0
        )
        
        # 오디오 파일을 응답으로 반환
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def remove_tts_code():
    pass

@app.post("/correct_sentence")
@app.post("/api/v1/correct_sentence")
async def correct_sentence(request: SentenceCorrectionRequest):
    """
    STT 결과 문장을 교정합니다.
    """
    logger.info(f"🔍 문장 교정 요청 처리 중... (텍스트: {request.text})")
    
    try:
        # 문장 교정 프롬프트 생성 (더 구체적이고 명확한 지시사항)
        prompt = f"""
다음 음성 인식 결과를 자연스럽고 문법적으로 올바른 한국어 문장으로 교정해주세요.

교정 규칙:
1. 오타나 잘못된 단어를 올바른 단어로 수정
2. 문법 오류를 수정 (조사, 어미 등)
3. 불완전한 문장을 완성
4. 원래 의미는 반드시 유지
5. 교정된 문장만 출력 (설명 없이)

음성 인식 결과: "{request.text}"

교정된 문장:
"""
        
        # AI 모델을 사용하여 문장 교정
        try:
            # Gemini AI 직접 사용
            import google.generativeai as genai
            from mbti_analyzer.config.settings import settings
            
            # Gemini AI 설정
            import os
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                # settings에서 확인
                gemini_key = settings.gemini_api_key
                if not gemini_key:
                    raise Exception("Gemini API 키가 설정되지 않았습니다. 환경 변수 GEMINI_API_KEY를 설정해주세요.")
            
            logger.info(f"Gemini API 키 확인: {gemini_key[:10]}...")
            genai.configure(api_key=gemini_key)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # AI 응답 생성
            response = model.generate_content(prompt)
            corrected_text = response.text.strip()
            
            logger.info(f"AI 응답 원본: {corrected_text}")
            
            # 교정 결과 정리
            if corrected_text and isinstance(corrected_text, str):
                # 불필요한 부분 제거
                corrected_text = corrected_text.replace("교정된 문장:", "").strip()
                corrected_text = corrected_text.replace("교정:", "").strip()
                corrected_text = corrected_text.replace("수정된 문장:", "").strip()
                corrected_text = corrected_text.replace("결과:", "").strip()
                corrected_text = corrected_text.replace("답변:", "").strip()
                
                # 줄바꿈 정리
                corrected_text = corrected_text.replace("\n", " ").strip()
                
                # 따옴표 제거
                corrected_text = corrected_text.strip('"').strip("'").strip()
                
                # 빈 문자열 체크
                if not corrected_text:
                    corrected_text = request.text
                
                logger.info(f"정리된 교정 결과: '{corrected_text}'")
                
                # 원본과 동일한 경우 원본 반환
                has_changes = corrected_text != request.text
                
                if not has_changes:
                    logger.info("교정 결과가 원본과 동일함")
                
                return {
                    "success": True,
                    "original_text": request.text,
                    "corrected_text": corrected_text,
                    "has_changes": has_changes,
                    "ai_response": response.text.strip()  # 디버깅용
                }
            else:
                raise Exception("AI 문장 교정 생성 실패")
                
        except Exception as ai_error:
            logger.error(f"AI 문장 교정 실패: {ai_error}")
            # AI 실패 시 원본 텍스트 반환
            return {
                "success": True,
                "original_text": request.text,
                "corrected_text": request.text,
                "has_changes": False,
                "fallback": True,
                "error": str(ai_error),
                "error_type": type(ai_error).__name__
            }
            
    except Exception as e:
        logger.error(f"문장 교정 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문장 교정 처리 중 오류 발생: {str(e)}")

class SummarizeRequest(BaseModel):
    text: str
    type: str  # "detailed_analysis", "reasoning", "suggestions"

@app.post("/api/v1/summarize")
async def summarize_text(request: SummarizeRequest):
    """
    AI를 사용하여 텍스트를 요약합니다.
    """
    logger.info(f"🔍 AI 요약 요청 처리 중... (타입: {request.type}, 텍스트 길이: {len(request.text)})")
    
    try:
        # 요약 프롬프트 생성
        if request.type == "detailed_analysis":
            prompt = f"""
다음 MBTI T/F 분석의 상세 분석 내용을 2-3줄로 요약해주세요:

{request.text}

요약 (2-3줄):
"""
        elif request.type == "reasoning":
            prompt = f"""
다음 MBTI T/F 분석의 분석 근거를 2-3줄로 요약해주세요:

{request.text}

요약 (2-3줄):
"""
        elif request.type == "suggestions":
            prompt = f"""
다음 MBTI T/F 분석의 개선 제안을 2-3줄로 요약해주세요:

{request.text}

요약 (2-3줄):
"""
        else:
            raise HTTPException(status_code=400, detail="Invalid type parameter")

        # AI 모델을 사용하여 요약 생성
        try:
            # Gemini AI 사용 (1순위)
            from mbti_analyzer.core.question_generator import generate_ai_questions_real
            summary = await generate_ai_questions_real(prompt)
            
            # 요약 결과 정리
            if summary and isinstance(summary, str):
                # 불필요한 부분 제거
                summary = summary.replace("요약 (2-3줄):", "").strip()
                summary = summary.replace("요약:", "").strip()
                
                # 줄바꿈 정리
                summary = summary.replace("\n\n", "\n").replace("\n", " ")
                
                return {
                    "success": True,
                    "summary": summary,
                    "type": request.type,
                    "original_length": len(request.text),
                    "summary_length": len(summary)
                }
            else:
                raise Exception("AI 요약 생성 실패")
                
        except Exception as ai_error:
            logger.error(f"AI 요약 실패: {ai_error}")
            # AI 실패 시 간단한 요약으로 대체
            fallback_summary = request.text[:100] + "..." if len(request.text) > 100 else request.text
            return {
                "success": True,
                "summary": fallback_summary,
                "type": request.type,
                "original_length": len(request.text),
                "summary_length": len(fallback_summary),
                "fallback": True
            }
            
    except Exception as e:
        logger.error(f"요약 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"요약 처리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # 서버 시작 시 debug.log 파일 초기화
    with open("debug.log", "w", encoding="utf-8") as f:
        f.write("[DEBUG] 서버가 실행되었습니다!\n")
        f.write(f"[DEBUG] 실행 중인 파일: {os.path.abspath(__file__)}\n")
    
    # Static 파일 마운트
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 