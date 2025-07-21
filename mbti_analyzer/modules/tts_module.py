import os
import tempfile
import logging
from typing import Optional
from gtts import gTTS
import google.cloud.texttospeech as tts
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

def text_to_speech(
    text: str, 
    output_path: str, 
    voice_name: str = 'ko-KR-Chirp3-HD-Leda', 
    gender: str = 'FEMALE', 
    speaking_rate: float = 1.1, 
    pitch: float = 0.0
) -> bool:
    """텍스트를 음성으로 변환합니다."""
    try:
        # Google Cloud TTS 시도
        if try_google_cloud_tts(text, output_path, voice_name, gender, speaking_rate, pitch):
            return True
        
        # gTTS fallback
        return try_gtts_fallback(text, output_path)
        
    except Exception as e:
        logger.error(f"TTS 오류: {e}")
        return False

def try_google_cloud_tts(
    text: str, 
    output_path: str, 
    voice_name: str, 
    gender: str, 
    speaking_rate: float, 
    pitch: float
) -> bool:
    """Google Cloud TTS를 시도합니다."""
    try:
        # Google Cloud 인증 확인
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path or not os.path.exists(credentials_path):
            logger.warning("Google Cloud 인증 파일이 없습니다.")
            return False
        
        logger.info(f"🔍 Google Cloud TTS 시도 중... (음성: {voice_name}, 성별: {gender})")
        
        client = texttospeech.TextToSpeechClient()
        
        # 음성 설정
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name=voice_name,
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, gender)
        )
        
        # 오디오 설정
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        # 합성 요청
        logger.info("🔍 Google Cloud TTS 요청 중...")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # 파일 저장
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        logger.info("✅ Google Cloud TTS 성공!")
        return True
        
    except Exception as e:
        logger.error(f"Google Cloud TTS 실패: {e}")
        return False

def try_gtts_fallback(text: str, output_path: str) -> bool:
    """gTTS를 fallback으로 사용합니다."""
    try:
        logger.info("🔍 gTTS fallback 사용 중...")
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(output_path)
        logger.info("✅ gTTS 성공!")
        return True
    except Exception as e:
        logger.error(f"gTTS 실패: {e}")
        return False

def get_available_voices() -> list:
    """사용 가능한 음성 목록을 반환합니다."""
    try:
        client = texttospeech.TextToSpeechClient()
        request = texttospeech.ListVoicesRequest()
        response = client.list_voices(request=request)
        
        korean_voices = []
        for voice in response.voices:
            if voice.language_codes[0].startswith('ko'):
                korean_voices.append({
                    'name': voice.name,
                    'language_code': voice.language_codes[0],
                    'ssml_gender': voice.ssml_gender.name
                })
        
        return korean_voices
    except Exception as e:
        logger.error(f"음성 목록 조회 실패: {e}")
        return [] 