"""
FastAPI 메인 애플리케이션

MBTI 분석기의 메인 FastAPI 애플리케이션을 정의합니다.
"""

import sys
import os
from pathlib import Path
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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# 정적 파일 서빙 - 동적 경로 사용
try:
    # 기본 정적 파일
    if settings.static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    
    # 이미지 파일들
    if settings.images_dir.exists():
        app.mount("/images", StaticFiles(directory=str(settings.images_dir)), name="images")
    if settings.final_dir.exists():
        app.mount("/Final", StaticFiles(directory=str(settings.final_dir)), name="final")
    if settings.question_pg_dir.exists():
        app.mount("/Question_pg", StaticFiles(directory=str(settings.question_pg_dir)), name="questionpg")
    if settings.main_pg_dir.exists():
        app.mount("/Main_pg", StaticFiles(directory=str(settings.main_pg_dir)), name="mainpg")
    
    # 폰트 파일들
    if settings.fonts_dir.exists():
        app.mount("/fonts", StaticFiles(directory=str(settings.fonts_dir)), name="fonts")
    
    # 질문 파일들
    if settings.question_dir.exists():
        app.mount("/question", StaticFiles(directory=str(settings.question_dir)), name="question")
    
    logger.info("✅ 정적 파일 마운트 완료")
    logger.info(f"프로젝트 루트: {settings.project_root}")
except Exception as e:
    logger.warning(f"정적 파일 마운트 실패: {e}")

# 기본 라우트들
@app.get("/")
async def read_index():
    """메인 페이지"""
    try:
        index_path = settings.project_root / "index1.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")
    except Exception as e:
        logger.error(f"index1.html 로드 실패: {e}")
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index1.html")
async def read_index1():
    """index1.html 페이지"""
    try:
        index_path = settings.project_root / "index1.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")
    except Exception as e:
        logger.error(f"index1.html 로드 실패: {e}")
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index1.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index2.html")
async def read_index2():
    """index2.html 페이지"""
    try:
        index_path = settings.project_root / "index2.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index2.html 파일을 찾을 수 없습니다.</p>")
    except Exception as e:
        logger.error(f"index2.html 로드 실패: {e}")
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index2.html 파일을 찾을 수 없습니다.</p>")

@app.get("/index3.html")
async def read_index3():
    """index3.html 페이지"""
    try:
        index_path = settings.project_root / "index3.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index3.html 파일을 찾을 수 없습니다.</p>")
    except Exception as e:
        logger.error(f"index3.html 로드 실패: {e}")
        return HTMLResponse(content="<h1>MBTI T/F Analyzer</h1><p>index3.html 파일을 찾을 수 없습니다.</p>")

@app.get("/common.css")
async def read_css():
    """common.css 파일"""
    try:
        css_path = settings.project_root / "common.css"
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), media_type="text/css")
        else:
            return HTMLResponse(content="/* CSS 파일을 찾을 수 없습니다 */", media_type="text/css")
    except Exception as e:
        logger.error(f"common.css 로드 실패: {e}")
        return HTMLResponse(content="/* CSS 파일을 찾을 수 없습니다 */", media_type="text/css")

@app.get("/favicon.ico")
async def get_favicon():
    """파비콘"""
    try:
        favicon_path = settings.project_root / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        else:
            raise HTTPException(status_code=404, detail="Favicon not found")
    except Exception as e:
        logger.error(f"favicon.ico 로드 실패: {e}")
        raise HTTPException(status_code=404, detail="Favicon not found")

# 추가 정적 파일 라우트들
@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    """정적 파일 서빙"""
    try:
        # 프로젝트 루트에서 파일 찾기
        file_path = settings.project_root / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"정적 파일 서빙 오류: {e}")
        raise HTTPException(status_code=404, detail="File not found")

def check_module_connections():
    """모듈 연결 상태 확인"""
    try:
        from mbti_analyzer.core.analyzer import analyze_tf_tendency
        from mbti_analyzer.core.question_generator import generate_ai_questions
        from mbti_analyzer.core.final_analyzer import generate_final_analysis
        from mbti_analyzer.modules.stt_module import transcribe_audio_file
        from mbti_analyzer.modules.tts_module import text_to_speech
        
        logger.info("✅ 모든 모듈 연결 완료")
        return True
    except ImportError as e:
        logger.error(f"모듈 연결 실패: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("=== MBTI T/F Analyzer 서버 시작 ===")
    logger.info(f"프로젝트 루트: {settings.project_root}")
    logger.info(f"서버 주소: http://{settings.host}:{settings.port}")
    
    # 모듈 연결 상태 확인
    if not check_module_connections():
        logger.error("❌ 모듈 연결 실패")
    else:
        logger.info("✅ 모든 모듈 연결 완료")

if __name__ == "__main__":
    uvicorn.run(
        "mbti_analyzer.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 