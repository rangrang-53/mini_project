"""
유틸리티 헬퍼 함수들

애플리케이션에서 사용하는 다양한 유틸리티 함수들을 정의합니다.
"""

import logging
from typing import Any, Dict, List, Optional
import json


def log_debug(msg: str) -> None:
    """디버그 로그 출력"""
    print(f"[DEBUG] {msg}", flush=True)


def validate_audio_file(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """오디오 파일 유효성 검사"""
    if allowed_extensions is None:
        allowed_extensions = [".wav", ".mp3", ".m4a", ".flac"]
    
    if not filename:
        return False
    
    file_extension = filename.lower()
    return any(file_extension.endswith(ext) for ext in allowed_extensions)


def format_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """응답 데이터 포맷팅"""
    return {
        "success": True,
        "data": data,
        "timestamp": "2024-01-01T00:00:00Z"  # 실제로는 현재 시간 사용
    }


def parse_json_safely(json_str: str, default: Any = None) -> Any:
    """안전한 JSON 파싱"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def sanitize_text(text: str) -> str:
    """텍스트 정리 (XSS 방지 등)"""
    if not text:
        return ""
    
    # 기본적인 HTML 태그 제거
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # 특수 문자 이스케이프
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text.strip()


def truncate_text(text: str, max_length: int = 1000) -> str:
    """텍스트 길이 제한"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..." 