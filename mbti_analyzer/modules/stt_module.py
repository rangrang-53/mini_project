import os
import tempfile
import logging
import whisper
import librosa
import numpy as np
from typing import Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whisper 모델 로드
try:
    model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully!")
except Exception as e:
    logger.error(f"Whisper 모델 로드 실패: {e}")
    model = None

def transcribe_audio_file(audio_file_path: str) -> str:
    """음성 파일을 텍스트로 변환합니다."""
    if model is None:
        return "음성 인식 모델을 로드할 수 없습니다."
    
    try:
        result = model.transcribe(audio_file_path)
        return result["text"].strip()
    except Exception as e:
        logger.error(f"음성 인식 오류: {e}")
        return f"음성 인식 오류: {str(e)}"

def transcribe_audio_file_enhanced(audio_file_path: str) -> Dict:
    """향상된 음성 인식 기능"""
    try:
        # 기본 STT 수행
        text = transcribe_audio_file(audio_file_path)
        
        # 신뢰도 계산 (간단한 휴리스틱)
        confidence = 0.8
        if len(text.strip()) < 3:
            confidence = 0.5
        elif len(text.strip()) > 50:
            confidence = 0.9
        
        # 대안 텍스트 생성
        alternatives = []
        if text.strip():
            # 조사 변형
            text_variations = [
                text.replace("입니다", "이에요"),
                text.replace("이에요", "입니다"),
                text.replace("습니다", "어요"),
                text.replace("어요", "습니다")
            ]
            alternatives.extend([t for t in text_variations if t != text])
            
            # 띄어쓰기 변형
            words = text.split()
            if len(words) > 1:
                # 일부 단어들을 붙여서 변형
                for i in range(len(words) - 1):
                    new_text = " ".join(words[:i]) + " " + words[i] + words[i+1] + " " + " ".join(words[i+2:])
                    alternatives.append(new_text.strip())
        
        return {
            "text": text,
            "original_text": text,
            "confidence": confidence,
            "alternatives": alternatives[:3],  # 최대 3개 대안
            "has_alternatives": len(alternatives) > 0
        }
    except Exception as e:
        return {
            "text": f"음성 인식 오류: {str(e)}",
            "original_text": "",
            "confidence": 0.0,
            "alternatives": [],
            "has_alternatives": False
        }

def validate_audio_quality(audio_file_path: str) -> Dict:
    """오디오 품질을 검증합니다."""
    try:
        # 오디오 파일 로드
        y, sr = librosa.load(audio_file_path, sr=None)
        duration = len(y) / sr
        
        # 기본 품질 검증
        is_good = True
        suggestions = []
        
        # 길이 검증
        if duration < 0.5:
            is_good = False
            suggestions.append("음성이 너무 짧습니다. 1초 이상 말씀해주세요.")
        elif duration > 30:
            is_good = False
            suggestions.append("음성이 너무 깁니다. 30초 이내로 말씀해주세요.")
        
        # 볼륨 검증
        rms = np.sqrt(np.mean(y**2))
        if rms < 0.01:
            is_good = False
            suggestions.append("음성이 너무 작습니다. 더 크게 말씀해주세요.")
        elif rms > 0.5:
            is_good = False
            suggestions.append("음성이 너무 큽니다. 조금만 작게 말씀해주세요.")
        
        # 샘플링 레이트 검증
        if sr < 8000:
            suggestions.append("음성 품질이 낮습니다. 더 좋은 마이크를 사용해보세요.")
        
        return {
            "valid": True,
            "is_good": is_good,
            "duration": duration,
            "sample_rate": sr,
            "channels": 1,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"오디오 품질 검증 오류: {e}")
        return {
            "valid": False,
            "is_good": False,
            "duration": 0,
            "sample_rate": 0,
            "channels": 0,
            "suggestions": ["오디오 파일을 분석할 수 없습니다."]
        } 