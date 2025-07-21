"""
애플리케이션 설정

MBTI 분석기의 모든 설정을 관리합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings:
    # API Keys
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    groq_api_key: str = os.getenv('GROQ_API_KEY', '')
    google_application_credentials: str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "debug.log"
    
    # AI 모델 설정
    whisper_model: str = "base"
    tts_voice: str = "ko-KR-Chirp3-HD-Leda"
    tts_gender: str = "FEMALE"
    
    # 데이터베이스 설정
    database_url: str = "learning_data.db"
    
    # 파일 경로 설정
    static_dir: str = "static"
    templates_dir: str = "templates"
    upload_dir: str = "uploads"
    
    # 보안 설정
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

# 전역 설정 인스턴스
settings = Settings() 