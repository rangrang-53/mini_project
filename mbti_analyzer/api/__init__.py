"""
API 라우터

이 패키지는 FastAPI 애플리케이션의 라우터들을 포함합니다.
"""

from .main import app
from .routes import analysis, questions, speech

__all__ = ["app", "analysis", "questions", "speech"] 