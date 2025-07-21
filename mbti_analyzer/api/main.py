"""
FastAPI 메인 애플리케이션

MBTI 분석기의 메인 FastAPI 애플리케이션을 정의합니다.
"""

import sys
import os
sys.path.append('.')

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from mbti_analyzer.api.routes import analysis, speech, questions
from mbti_analyzer.config.settings import settings

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="MBTI T/F Analyzer",
    description="MBTI T/F 성향 분석 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# 라우터 등록
app.include_router(analysis.router, tags=["analysis"])
app.include_router(speech.router, tags=["speech"])
app.include_router(questions.router, tags=["questions"])

# 정적 파일 서빙 - 모든 필요한 디렉토리 마운트
try:
    # 기본 정적 파일
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # 이미지 파일들
    app.mount("/images", StaticFiles(directory="images"), name="images")
    app.mount("/Final", StaticFiles(directory="Final"), name="final")
    app.mount("/Question_pg", StaticFiles(directory="Question_pg"), name="questionpg")
    app.mount("/Main_pg", StaticFiles(directory="Main_pg"), name="mainpg")
    
    # 폰트 파일들
    app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
    
    # 질문 파일들
    app.mount("/question", StaticFiles(directory="question"), name="question")
    
    logger.info("✅ 정적 파일 마운트 완료")
except Exception as e:
    logger.warning(f"정적 파일 마운트 실패: {e}")

# 기본 라우트들
@app.get("/")
async def read_index():
    """메인 페이지"""
    try:
        with open("index1.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index1.html")
async def read_index1():
    """index1.html 페이지"""
    try:
        with open("index1.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index2.html")
async def read_index2():
    """index2.html 페이지"""
    try:
        with open("index2.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index2.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index3.html")
async def read_index3():
    """index3.html 페이지"""
    try:
        with open("index3.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index3.html 파일을 찾을 수 없습니다.</p>")

@app.get("/common.css")
async def read_css():
    """공통 CSS 파일"""
    try:
        with open("common.css", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="text/css")
    except FileNotFoundError:
        return HTMLResponse(content="/* CSS 파일을 찾을 수 없습니다 */", media_type="text/css")

@app.get("/favicon.ico")
async def get_favicon():
    """파비콘"""
    try:
        return FileResponse("favicon.ico")
    except FileNotFoundError:
        return None

# 추가 정적 파일 라우트들
@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    """정적 파일 서빙"""
    try:
        # 파일이 존재하는지 확인
        if os.path.exists(filename):
            return FileResponse(filename)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"정적 파일 서빙 오류: {e}")
        raise HTTPException(status_code=404, detail="File not found")

# 모듈 연결 상태 확인
def check_module_connections():
    """모듈 연결 상태를 확인합니다."""
    logger.info("=== MBTI T/F Analyzer 모듈 연결 상태 확인 ===")
    
    modules = [
        ("분석기 모듈", "mbti_analyzer.core.analyzer"),
        ("질문 생성기 모듈", "mbti_analyzer.core.question_generator"),
        ("최종 분석기 모듈", "mbti_analyzer.core.final_analyzer"),
        ("STT 모듈", "mbti_analyzer.modules.stt_module"),
        ("TTS 모듈", "mbti_analyzer.modules.tts_module"),
    ]
    
    for name, module_path in modules:
        try:
            __import__(module_path)
            logger.info(f"✅ {name} ({module_path}) - 연결됨")
        except ImportError as e:
            logger.error(f"❌ {name} ({module_path}) - 연결 실패: {e}")
    
    logger.info("=== 모든 모듈 연결 완료 ===")

# 앱 시작 시 모듈 연결 확인
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행되는 이벤트"""
    logger.info("Starting MBTI T/F Analyzer...")
    check_module_connections()
    
    # AI 모델 초기화 확인
    try:
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            logger.info("✅ Gemini AI 모델 초기화 완료 (1순위)")
        else:
            logger.warning("⚠️ Gemini API 키가 설정되지 않았습니다.")
    except Exception as e:
        logger.error(f"❌ Gemini AI 모델 초기화 실패: {e}")
    
    try:
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            logger.info("✅ Groq AI 모델 초기화 완료 (2순위)")
        else:
            logger.warning("⚠️ Groq API 키가 설정되지 않았습니다.")
    except Exception as e:
        logger.error(f"❌ Groq AI 모델 초기화 실패: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "mbti_analyzer.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 