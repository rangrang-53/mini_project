"""
애플리케이션 설정

MBTI 분석기의 모든 설정을 관리합니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings:
    # 프로젝트 루트 경로 계산
    @property
    def project_root(self) -> Path:
        """프로젝트 루트 경로를 동적으로 계산"""
        # 현재 파일 위치에서 프로젝트 루트 찾기
        current_file = Path(__file__)
        
        # mbti_analyzer/config/settings.py에서 시작해서
        # 프로젝트 루트(requirements.txt가 있는 위치)까지 올라가기
        for parent in [current_file.parent.parent.parent, current_file.parent.parent]:
            if (parent / "requirements.txt").exists():
                return parent
        
        # 찾지 못한 경우 현재 작업 디렉토리 사용
        return Path.cwd()
    
    @property
    def static_dir(self) -> Path:
        """정적 파일 디렉토리 경로"""
        return self.project_root / "static"
    
    @property
    def images_dir(self) -> Path:
        """이미지 디렉토리 경로"""
        return self.project_root / "images"
    
    @property
    def fonts_dir(self) -> Path:
        """폰트 디렉토리 경로"""
        return self.project_root / "fonts"
    
    @property
    def question_dir(self) -> Path:
        """질문 디렉토리 경로"""
        return self.project_root / "question"
    
    @property
    def final_dir(self) -> Path:
        """Final 디렉토리 경로"""
        return self.project_root / "Final"
    
    @property
    def question_pg_dir(self) -> Path:
        """Question_pg 디렉토리 경로"""
        return self.project_root / "Question_pg"
    
    @property
    def main_pg_dir(self) -> Path:
        """Main_pg 디렉토리 경로"""
        return self.project_root / "Main_pg"
    
    # API Keys
    gemini_api_key: str = os.getenv('GEMINI_API_KEY', '')
    groq_api_key: str = os.getenv('GROQ_API_KEY', '')
    google_application_credentials: str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False  # reload 모드 비활성화
    
    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "debug.log"
    
    # AI 모델 설정
    whisper_model: str = "base"
    tts_voice: str = "ko-KR-Chirp3-HD-Leda"
    tts_gender: str = "FEMALE"
    
    # 데이터베이스 설정
    database_url: str = "learning_data.db"
    
    # 보안 설정
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

# 전역 설정 인스턴스
settings = Settings() 