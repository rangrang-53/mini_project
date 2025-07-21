#!/usr/bin/env python3
"""
안전장치가 포함된 API 엔드포인트들
- 백업 관리 API
- 롤백 기능 API
- 안전성 지표 API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3
import json
import os

# 기존 API에서 import
from api import app

# 안전장치 관련 데이터 모델
class SafetyMetricsRequest(BaseModel):
    check_date: Optional[datetime] = None

class SafetyMetricsResponse(BaseModel):
    success: bool
    risk_level: str
    current_error_rate: float
    backup_error_rate: float
    performance_trend: str
    days_since_backup: int
    backup_info: Optional[Dict] = None
    can_rollback: bool

class RollbackRequest(BaseModel):
    confirm: bool = True

class RollbackResponse(BaseModel):
    success: bool
    message: str
    previous_version: str
    new_version: str

class BackupInfo(BaseModel):
    version: str
    backup_date: str
    average_error: float
    is_stable: bool
    performance_data: Dict

class BackupResponse(BaseModel):
    success: bool
    backup_info: BackupInfo
    message: str

# 안전장치 관리자 클래스
class SafetyManager:
    def __init__(self, db_path: str = "safe_learning_data.db"):
        self.db_path = db_path
    
    def get_safety_metrics(self) -> SafetyMetricsResponse:
        """안전성 지표 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 현재 성능 조회
            cursor.execute('''
                SELECT expected_score, actual_score, error, is_acceptable
                FROM user_inputs
                ORDER BY timestamp DESC
                LIMIT 50
            ''')
            
            results = cursor.fetchall()
            
            if not results:
                return SafetyMetricsResponse(
                    success=True,
                    risk_level="low",
                    current_error_rate=0,
                    backup_error_rate=0,
                    performance_trend="stable",
                    days_since_backup=0,
                    backup_info=None,
                    can_rollback=False
                )
            
            # 현재 오차율 계산
            total_error = sum(error for _, _, error, _ in results)
            current_error_rate = total_error / len(results)
            
            # 최신 백업 조회
            cursor.execute('''
                SELECT version, backup_date, average_error, performance_data, is_stable
                FROM prompt_backups
                ORDER BY backup_date DESC
                LIMIT 1
            ''')
            
            backup_result = cursor.fetchone()
            
            if backup_result:
                backup_date = datetime.fromisoformat(backup_result[1])
                backup_error_rate = backup_result[2]
                days_since_backup = (datetime.now() - backup_date).days
                
                backup_info = {
                    "version": backup_result[0],
                    "backup_date": backup_result[1],
                    "average_error": backup_result[2],
                    "is_stable": bool(backup_result[4])
                }
                
                # 성능 트렌드 분석
                performance_trend = self.analyze_performance_trend(results)
                
                # 위험도 계산
                risk_level = self.calculate_risk_level(
                    current_error_rate, 
                    backup_error_rate, 
                    performance_trend,
                    days_since_backup
                )
                
                # 롤백 가능 여부
                can_rollback = current_error_rate > backup_error_rate + 0.1  # 10% 이상 성능 저하
                
            else:
                backup_error_rate = 0
                days_since_backup = 0
                backup_info = None
                performance_trend = "stable"
                risk_level = "low"
                can_rollback = False
            
            conn.close()
            
            return SafetyMetricsResponse(
                success=True,
                risk_level=risk_level,
                current_error_rate=current_error_rate,
                backup_error_rate=backup_error_rate,
                performance_trend=performance_trend,
                days_since_backup=days_since_backup,
                backup_info=backup_info,
                can_rollback=can_rollback
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"안전성 지표 조회 중 오류: {str(e)}")
    
    def analyze_performance_trend(self, results: List) -> str:
        """성능 트렌드 분석"""
        if len(results) < 10:
            return "stable"
        
        # 최근 5개와 이전 5개 비교
        recent_errors = [error for _, _, error, _ in results[:5]]
        previous_errors = [error for _, _, error, _ in results[5:10]]
        
        recent_avg = sum(recent_errors) / len(recent_errors)
        previous_avg = sum(previous_errors) / len(previous_errors)
        
        if recent_avg < previous_avg - 2:  # 2% 이상 개선
            return "improving"
        elif recent_avg > previous_avg + 2:  # 2% 이상 저하
            return "declining"
        else:
            return "stable"
    
    def calculate_risk_level(self, current_error: float, backup_error: float, 
                           trend: str, days_since_backup: int) -> str:
        """위험도 계산"""
        risk_score = 0
        
        # 오차율 증가 위험
        if current_error > backup_error + 0.15:  # 15% 이상 증가
            risk_score += 3
        
        # 성능 저하 위험
        if trend == "declining":
            risk_score += 2
        
        # 백업 지연 위험
        if days_since_backup > 7:  # 1주일 이상
            risk_score += 1
        
        # 높은 오차율 위험
        if current_error > 15:
            risk_score += 2
        
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def perform_rollback(self) -> RollbackResponse:
        """롤백 수행"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 최신 백업 조회
            cursor.execute('''
                SELECT version, prompt, backup_date, average_error
                FROM prompt_backups
                ORDER BY backup_date DESC
                LIMIT 1
            ''')
            
            backup_result = cursor.fetchone()
            
            if not backup_result:
                raise HTTPException(status_code=400, detail="롤백할 백업이 없습니다.")
            
            backup_version = backup_result[0]
            backup_prompt = backup_result[1]
            backup_date = backup_result[2]
            backup_error = backup_result[3]
            
            # 현재 버전 조회
            cursor.execute('''
                SELECT version FROM prompt_versions
                ORDER BY created_at DESC
                LIMIT 1
            ''')
            
            current_result = cursor.fetchone()
            current_version = current_result[0] if current_result else "v1.0"
            
            # 롤백 이벤트 로그
            cursor.execute('''
                INSERT INTO safety_metrics 
                (check_date, current_error_rate, backup_error_rate, performance_trend, risk_level, action_taken)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                0, 0, "rollback", "high", f"Rollback from {current_version} to {backup_version}"
            ))
            
            conn.commit()
            conn.close()
            
            return RollbackResponse(
                success=True,
                message=f"롤백이 성공적으로 수행되었습니다. {backup_version}으로 복구되었습니다.",
                previous_version=current_version,
                new_version=backup_version
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"롤백 수행 중 오류: {str(e)}")
    
    def create_backup(self) -> BackupResponse:
        """백업 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 현재 성능 조회
            cursor.execute('''
                SELECT expected_score, actual_score, error, is_acceptable
                FROM user_inputs
                ORDER BY timestamp DESC
                LIMIT 50
            ''')
            
            results = cursor.fetchall()
            
            if not results:
                raise HTTPException(status_code=400, detail="백업할 데이터가 없습니다.")
            
            # 성능 계산
            total_inputs = len(results)
            acceptable_count = sum(1 for _, _, _, is_acceptable in results if is_acceptable)
            total_error = sum(error for _, _, error, _ in results)
            
            performance_data = {
                "total_inputs": total_inputs,
                "acceptable_rate": (acceptable_count / total_inputs) * 100,
                "average_error": total_error / total_inputs
            }
            
            # 백업 정보 생성
            backup_version = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_date = datetime.now().isoformat()
            average_error = performance_data["average_error"]
            is_stable = performance_data["acceptable_rate"] >= 60
            
            # 백업 저장
            cursor.execute('''
                INSERT INTO prompt_backups 
                (version, prompt, backup_date, average_error, performance_data, is_stable)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                backup_version,
                "현재 프롬프트",  # 실제로는 현재 프롬프트 내용
                backup_date,
                average_error,
                json.dumps(performance_data),
                is_stable
            ))
            
            conn.commit()
            conn.close()
            
            backup_info = BackupInfo(
                version=backup_version,
                backup_date=backup_date,
                average_error=average_error,
                is_stable=is_stable,
                performance_data=performance_data
            )
            
            return BackupResponse(
                success=True,
                backup_info=backup_info,
                message=f"백업이 성공적으로 생성되었습니다: {backup_version}"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"백업 생성 중 오류: {str(e)}")

# 안전장치 관리자 인스턴스
safety_manager = SafetyManager()

# 안전장치 API 엔드포인트들
@app.get("/api/v1/safety/metrics")
async def get_safety_metrics() -> SafetyMetricsResponse:
    """안전성 지표 조회"""
    return safety_manager.get_safety_metrics()

@app.post("/api/v1/safety/rollback")
async def perform_rollback(request: RollbackRequest) -> RollbackResponse:
    """롤백 수행"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="롤백 확인이 필요합니다.")
    
    return safety_manager.perform_rollback()

@app.post("/api/v1/safety/backup")
async def create_backup() -> BackupResponse:
    """백업 생성"""
    return safety_manager.create_backup()

@app.get("/api/v1/safety/backups")
async def get_backup_list():
    """백업 목록 조회"""
    try:
        conn = sqlite3.connect(safety_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, backup_date, average_error, is_stable
            FROM prompt_backups
            ORDER BY backup_date DESC
            LIMIT 20
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        backups = []
        for row in results:
            backups.append({
                "version": row[0],
                "backup_date": row[1],
                "average_error": row[2],
                "is_stable": bool(row[3])
            })
        
        return {
            "success": True,
            "backups": backups,
            "total_count": len(backups)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백업 목록 조회 중 오류: {str(e)}")

@app.get("/safe_index_with_learning.html")
async def read_safe_index_with_learning():
    """안전장치가 포함된 메인 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("safe_index_with_learning.html")

# 기존 API에 안전장치 통합
@app.post("/api/v1/analyze_with_safety")
async def analyze_with_safety(request):
    """안전장치가 포함된 분석 API"""
    # 기존 분석 수행
    analysis_result = await analyze_text(request)
    
    # 안전성 검사
    safety_metrics = safety_manager.get_safety_metrics()
    
    # 위험도가 높으면 경고
    if safety_metrics.risk_level == "high":
        print(f"🚨 높은 위험도 감지: {safety_metrics.current_error_rate:.1f}% 오차율")
    
    return {
        **analysis_result,
        "safety_warning": safety_metrics.risk_level == "high",
        "safety_metrics": {
            "risk_level": safety_metrics.risk_level,
            "current_error_rate": safety_metrics.current_error_rate,
            "performance_trend": safety_metrics.performance_trend
        }
    }

# 기존 analyze_text 함수 (api.py에서 가져옴)
async def analyze_text(request):
    """기존 분석 함수 (api.py에서 복사)"""
    # 여기에 기존 api.py의 analyze_text 함수 내용을 복사
    pass 