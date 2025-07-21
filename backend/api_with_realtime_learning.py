import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import threading
import queue
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 기존 API 코드와 통합
from api import app, TextRequest, AnalysisResponse

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

class RealtimeLearningManager:
    def __init__(self):
        self.user_inputs_queue = queue.Queue()
        self.current_prompt_version = "v1.0"
        self.prompt_history = []
        self.performance_threshold = 0.6  # 60% 허용 오차 달성 시 개선
        self.min_inputs_for_tuning = 10   # 튜닝을 위한 최소 입력 수
        self.db_path = "learning_data.db"
        self.init_database()
        self.learning_enabled = True
        
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
        
        # 프롬프트 업데이트 (실제로는 API 재시작 필요)
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

# 새로운 API 엔드포인트들
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

# 기존 analyze 엔드포인트 수정 (학습 통합)
@app.post("/api/v1/analyze_with_learning")
async def analyze_with_learning(request: TextRequest, expected_score: Optional[float] = None):
    """학습이 통합된 분석 엔드포인트"""
    # 기존 분석 수행
    analysis_result = await analyze_text(request)
    
    # 예상 점수가 제공된 경우 학습 처리
    if expected_score is not None and learning_manager.learning_enabled:
        await learning_manager.process_user_input(
            question="사용자 입력",  # 실제로는 질문 정보가 필요
            answer=request.text,
            expected_score=expected_score,
            actual_score=analysis_result.score
        )
    
    return analysis_result

# 기존 analyze_text 함수 (api.py에서 가져옴)
async def analyze_text(request: TextRequest) -> AnalysisResponse:
    """기존 분석 함수 (api.py에서 복사)"""
    # 여기에 기존 api.py의 analyze_text 함수 내용을 복사
    # 실제 구현에서는 api.py의 함수를 import하거나 복사
    pass 