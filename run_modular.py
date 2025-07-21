#!/usr/bin/env python3
"""
MBTI T/F Analyzer - 모듈화된 버전
"""

import sys
import os
import uvicorn
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

def main():
    """메인 실행 함수"""
    try:
        logger.info("=== MBTI T/F Analyzer 모듈화 버전 시작 ===")
        
        # 모듈화된 앱 임포트
        from mbti_analyzer.api.main import app
        
        # 서버 설정
        host = "0.0.0.0"
        port = 8000
        reload = True
        
        logger.info(f"서버 시작: http://{host}:{port}")
        logger.info("모듈화된 구조로 실행 중...")
        
        # uvicorn으로 서버 실행
        uvicorn.run(
            "mbti_analyzer.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"모듈 임포트 실패: {e}")
        logger.error("모듈화된 구조를 사용할 수 없습니다. 기존 api.py를 사용하세요.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 