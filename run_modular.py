#!/usr/bin/env python3
"""
MBTI T/F Analyzer - 모듈화된 버전

외부 환경에서도 안정적으로 작동하도록 경로 문제를 해결합니다.
"""

import sys
import os
import uvicorn
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_project_structure():
    """프로젝트 구조 확인"""
    logger.info("🔍 프로젝트 구조 확인 중...")
    
    # 필수 파일들 확인
    required_files = [
        "requirements.txt",
        "index1.html",
        "mbti_analyzer/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"❌ 필수 파일이 없습니다: {missing_files}")
        return False
    
    logger.info("✅ 프로젝트 구조 확인 완료")
    return True

def check_dependencies():
    """의존성 확인"""
    logger.info("🔍 의존성 확인 중...")
    
    try:
        import fastapi
        import uvicorn
        import pydantic
        import requests
        
        logger.info("✅ 핵심 의존성 확인 완료")
        return True
    except ImportError as e:
        logger.error(f"❌ 핵심 의존성 확인 실패: {e}")
        logger.error("pip install -r requirements.txt를 실행해주세요.")
        return False

def main():
    """메인 실행 함수"""
    try:
        logger.info("=== MBTI T/F Analyzer 모듈화 버전 시작 ===")
        logger.info(f"📁 작업 디렉토리: {current_dir}")
        
        # debug.log 파일 초기화
        try:
            with open("debug.log", "w", encoding="utf-8") as f:
                f.write("[DEBUG] 서버가 실행되었습니다!\n")
                f.write(f"[DEBUG] 실행 중인 파일: {os.path.abspath(__file__)}\n")
                f.write(f"[DEBUG] 작업 디렉토리: {current_dir}\n")
                f.write(f"[DEBUG] 시작 시간: {datetime.now()}\n")
            logger.info("✅ debug.log 파일 초기화 완료")
        except Exception as e:
            logger.warning(f"debug.log 초기화 실패: {e}")
        
        # 프로젝트 구조 확인
        if not check_project_structure():
            logger.error("프로젝트 구조가 올바르지 않습니다.")
            sys.exit(1)
        
        # 의존성 확인
        if not check_dependencies():
            logger.error("의존성 설치가 필요합니다.")
            sys.exit(1)
        
        # 모듈화된 앱 임포트
        try:
            from mbti_analyzer.api.main import app
            from mbti_analyzer.config.settings import settings
            logger.info("✅ 모듈화된 앱 임포트 완료")
        except ImportError as e:
            logger.error(f"❌ 모듈화된 앱 임포트 실패: {e}")
            logger.error("기존 api.py를 사용하세요.")
            sys.exit(1)
        
        # 서버 설정
        host = settings.host
        port = settings.port
        reload = settings.debug
        
        logger.info(f"🚀 서버 시작: http://{host}:{port}")
        logger.info(f"📁 프로젝트 루트: {settings.project_root}")
        logger.info("모듈화된 구조로 실행 중...")
        
        # uvicorn으로 서버 실행
        uvicorn.run(
            "mbti_analyzer.api.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=["mbti_analyzer"] if reload else None,  # 감시할 디렉토리 제한
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("서버가 사용자에 의해 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 