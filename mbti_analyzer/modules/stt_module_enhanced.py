import whisper
import os
import logging
import numpy as np
from typing import Optional, Dict, List
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whisper 모델 로딩 (최초 1회)
try:
    # medium 모델로 변경하여 정확도 개선 (한국어 인식 향상)
    whisper_model = whisper.load_model("medium")
    logger.info("Whisper medium 모델 로딩 완료 (정확도 개선)")
except Exception as e:
    logger.error(f"Whisper medium 모델 로딩 실패, base 모델로 대체: {e}")
    try:
        whisper_model = whisper.load_model("base")
        logger.info("Whisper base 모델 로딩 완료 (대체)")
    except Exception as e2:
        logger.error(f"Whisper base 모델 로딩도 실패: {e2}")
        whisper_model = None


def transcribe_audio_file_enhanced(audio_path: str, language: str = 'ko', task: str = 'transcribe') -> Dict:
    """
    향상된 STT 기능 - 여러 모델과 후처리를 통한 정확도 향상
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File not found: {audio_path}")
    
    if whisper_model is None:
        raise RuntimeError("Whisper 모델이 로드되지 않았습니다.")
    
    try:
        logger.info(f"향상된 STT 처리 시작: {audio_path}")
        logger.info(f"파일 크기: {os.path.getsize(audio_path)} bytes")
        
        # 1단계: 기본 STT
        basic_result = whisper_model.transcribe(
            audio_path, 
            language=language,
            task=task,
            fp16=False,
            temperature=0.0
        )
        basic_text = basic_result.get("text", "").strip()
        
        # 2단계: 향상된 후처리
        enhanced_text = enhance_text_quality(basic_text)
        
        # 3단계: 신뢰도 점수 계산
        confidence_score = calculate_confidence(basic_result)
        
        # 4단계: 대안 제안 (신뢰도가 낮은 경우)
        alternatives = []
        if confidence_score < 0.7:
            alternatives = generate_alternatives(basic_text)
        
        logger.info(f"향상된 STT 결과: '{enhanced_text}' (신뢰도: {confidence_score:.2f})")
        
        return {
            "text": enhanced_text,
            "original_text": basic_text,
            "confidence": confidence_score,
            "alternatives": alternatives,
            "has_alternatives": len(alternatives) > 0
        }
        
    except Exception as e:
        logger.error(f"향상된 STT 처리 중 오류: {e}")
        raise


def enhance_text_quality(text: str) -> str:
    """
    텍스트 품질을 향상시키는 후처리 함수
    """
    if not text:
        return text
    
    # 1. 기본 정리
    text = text.strip()
    text = ' '.join(text.split())  # 불필요한 공백 제거
    
    # 2. 한국어 특화 정리
    # 자주 발생하는 오인식 패턴 수정
    common_corrections = {
        # 숫자 관련
        '일': '1', '이': '2', '삼': '3', '사': '4', '오': '5',
        '육': '6', '칠': '7', '팔': '8', '구': '9', '십': '10',
        
        # 조사 관련
        '은': '은', '는': '는', '이': '이', '가': '가',
        '을': '을', '를': '를', '의': '의', '에': '에',
        
        # 연결어 관련
        '그리고': '그리고', '그런데': '그런데', '그렇지만': '그렇지만',
        '그러니까': '그러니까', '그러면': '그러면', '그래서': '그래서',
        
        # 감정 표현 관련
        '좋아': '좋아', '싫어': '싫어', '재미있어': '재미있어',
        '어려워': '어려워', '쉬워': '쉬워', '힘들어': '힘들어',
    }
    
    for mistake, correction in common_corrections.items():
        text = text.replace(mistake, correction)
    
    # 3. 문장 구조 개선
    # 불완전한 문장 완성
    if text and not text.endswith(('.', '!', '?', '~', '다', '까', '네', '요', '어', '아')):
        # 문맥에 따라 적절한 종결어미 추가
        if any(word in text for word in ['좋', '싫', '재미', '어려', '쉬', '힘들']):
            text += '어.'
        elif any(word in text for word in ['생각', '느낌', '기분']):
            text += '이야.'
        else:
            text += '.'
    
    # 4. 중복 단어 제거
    words = text.split()
    cleaned_words = []
    for i, word in enumerate(words):
        if i == 0 or word != words[i-1]:
            cleaned_words.append(word)
    text = ' '.join(cleaned_words)
    
    return text


def calculate_confidence(result: Dict) -> float:
    """
    STT 결과의 신뢰도를 계산합니다.
    """
    try:
        # Whisper의 로그 확률을 사용한 신뢰도 계산
        if 'segments' in result and result['segments']:
            total_logprob = 0
            total_tokens = 0
            
            for segment in result['segments']:
                if 'avg_logprob' in segment:
                    total_logprob += segment['avg_logprob'] * len(segment.get('tokens', []))
                    total_tokens += len(segment.get('tokens', []))
            
            if total_tokens > 0:
                avg_logprob = total_logprob / total_tokens
                # 로그 확률을 0-1 범위의 신뢰도로 변환
                confidence = max(0.0, min(1.0, (avg_logprob + 2.0) / 4.0))
                return confidence
        
        # 기본 신뢰도 (텍스트 길이 기반)
        text_length = len(result.get('text', ''))
        if text_length < 5:
            return 0.3
        elif text_length < 10:
            return 0.6
        else:
            return 0.8
            
    except Exception as e:
        logger.error(f"신뢰도 계산 중 오류: {e}")
        return 0.5


def generate_alternatives(original_text: str) -> List[str]:
    """
    원본 텍스트에 대한 대안을 생성합니다.
    """
    alternatives = []
    
    if not original_text:
        return alternatives
    
    # 1. 유사한 발음 패턴 대안
    pronunciation_alternatives = {
        '그리고': ['그리고', '그러고', '그래서'],
        '그런데': ['그런데', '그렇지만', '하지만'],
        '생각': ['생각', '생각해', '생각이'],
        '느낌': ['느낌', '느껴', '느낌이'],
        '좋아': ['좋아', '좋은', '좋은 것'],
        '싫어': ['싫어', '싫은', '싫은 것'],
    }
    
    for pattern, alts in pronunciation_alternatives.items():
        if pattern in original_text:
            for alt in alts:
                alt_text = original_text.replace(pattern, alt)
                if alt_text != original_text:
                    alternatives.append(alt_text)
    
    # 2. 문장 구조 변형
    if original_text.endswith('.'):
        base_text = original_text[:-1]
        alternatives.extend([
            f"{base_text}이야.",
            f"{base_text}이에요.",
            f"{base_text}입니다.",
        ])
    
    # 3. 중복 제거
    alternatives = list(set(alternatives))
    
    return alternatives[:3]  # 최대 3개까지만 반환


def validate_audio_quality(audio_path: str) -> Dict:
    """
    오디오 품질을 검증하고 개선 제안을 제공합니다.
    """
    try:
        import librosa
        
        # 오디오 파일 로드
        y, sr = librosa.load(audio_path, sr=None)
        
        # 기본 정보
        duration = len(y) / sr
        rms_energy = np.sqrt(np.mean(y**2))
        
        # 품질 지표
        quality_score = 1.0
        issues = []
        suggestions = []
        
        # 1. 길이 검증
        if duration < 0.5:
            quality_score *= 0.5
            issues.append("음성이 너무 짧습니다")
            suggestions.append("1초 이상 말씀해주세요")
        elif duration > 30:
            quality_score *= 0.8
            issues.append("음성이 너무 깁니다")
            suggestions.append("30초 이내로 말씀해주세요")
        
        # 2. 볼륨 검증
        if rms_energy < 0.01:
            quality_score *= 0.3
            issues.append("음성이 너무 작습니다")
            suggestions.append("마이크에 더 가까이 말씀해주세요")
        elif rms_energy > 0.5:
            quality_score *= 0.7
            issues.append("음성이 너무 큽니다")
            suggestions.append("마이크에서 조금 떨어져 말씀해주세요")
        
        # 3. 노이즈 검증 (간단한 방법)
        # 고주파 성분이 많으면 노이즈로 간주
        fft = np.fft.fft(y)
        high_freq_energy = np.sum(np.abs(fft[len(fft)//2:])) / len(fft)
        
        if high_freq_energy > 0.1:
            quality_score *= 0.6
            issues.append("배경 소음이 감지됩니다")
            suggestions.append("조용한 환경에서 말씀해주세요")
        
        return {
            "quality_score": float(quality_score),
            "duration": float(duration),
            "rms_energy": float(rms_energy),
            "issues": issues,
            "suggestions": suggestions,
            "is_good": quality_score > 0.7
        }
        
    except ImportError:
        logger.warning("librosa가 설치되지 않아 오디오 품질 검증을 건너뜁니다.")
        return {
            "quality_score": 0.5,
            "duration": 0,
            "rms_energy": 0,
            "issues": ["오디오 품질 검증을 사용할 수 없습니다"],
            "suggestions": ["librosa 라이브러리를 설치해주세요"],
            "is_good": False
        }
    except Exception as e:
        logger.error(f"오디오 품질 검증 중 오류: {e}")
        return {
            "quality_score": 0.5,
            "duration": 0,
            "rms_energy": 0,
            "issues": [f"오디오 품질 검증 중 오류: {e}"],
            "suggestions": ["다시 시도해주세요"],
            "is_good": False
        } 