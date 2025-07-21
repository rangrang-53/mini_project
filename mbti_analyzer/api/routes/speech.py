"""
음성 관련 API 엔드포인트

STT(Speech-to-Text)와 TTS(Text-to-Speech) 관련 API 엔드포인트들을 정의합니다.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Optional
import tempfile
import os
import logging

from mbti_analyzer.modules.stt_module import transcribe_audio_file, transcribe_audio_file_enhanced, validate_audio_quality
from mbti_analyzer.modules.tts_module import text_to_speech
from mbti_analyzer.modules.sentence_correction import correct_sentence_with_ai_enhanced

logger = logging.getLogger(__name__)

router = APIRouter()

class SentenceCorrectionRequest(BaseModel):
    text: str

@router.post("/stt")
@router.post("/api/v1/stt")
async def speech_to_text_endpoint(audio_file: UploadFile = File(...)):
    """음성을 텍스트로 변환합니다."""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # STT 수행
        text = transcribe_audio_file(temp_path)
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        return {"text": text}
        
    except Exception as e:
        logger.error(f"STT 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stt_enhanced")
@router.post("/api/v1/stt_enhanced")
async def speech_to_text_enhanced_endpoint(audio_file: UploadFile = File(...)):
    """향상된 음성을 텍스트로 변환합니다."""
    try:
        logger.info(f"🔍 향상된 STT 요청 처리 중... (파일명: {audio_file.filename})")
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 향상된 STT 수행
        result = transcribe_audio_file_enhanced(temp_path)
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        logger.info(f"향상된 STT 결과: '{result['text']}' (신뢰도: {result['confidence']:.2f})")
        
        return result
        
    except Exception as e:
        logger.error(f"향상된 STT 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/correct_sentence")
@router.post("/api/v1/correct_sentence")
async def correct_sentence_endpoint(request: SentenceCorrectionRequest):
    """문장을 교정합니다."""
    try:
        logger.info(f"🔍 문장 교정 요청 처리 중... (텍스트: {request.text})")
        
        # Gemini AI를 사용한 문장 교정
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
다음 음성 인식 결과를 자연스럽고 문법적으로 올바른 한국어 문장으로 교정해주세요.

교정 규칙:
1. 오타나 잘못된 단어를 올바른 단어로 수정
2. 문법 오류를 수정 (조사, 어미 등)
3. 불완전한 문장을 완성
4. 원래 의미는 반드시 유지
5. 교정된 문장만 출력 (설명 없이)

음성 인식 결과: "{request.text}"

교정된 문장:
"""
            
            response = model.generate_content(prompt)
            corrected_text = response.text.strip()
            
            # 불필요한 텍스트 제거
            import re
            corrected_text = re.sub(r'^교정된 문장:\s*', '', corrected_text)
            corrected_text = re.sub(r'^결과:\s*', '', corrected_text)
            corrected_text = corrected_text.strip()
            
            if not corrected_text:
                corrected_text = request.text
            
            logger.info(f"AI 응답 원본: {response.text}")
            logger.info(f"정리된 교정 결과: '{corrected_text}'")
            
            return {"corrected_text": corrected_text, "method": "ai"}
        else:
            # Fallback: 원본 텍스트 반환
            return {"corrected_text": request.text, "method": "fallback"}
            
    except Exception as e:
        logger.error(f"문장 교정 오류: {e}")
        return {"corrected_text": request.text, "method": "fallback"}

@router.post("/correct_sentence_enhanced")
@router.post("/api/v1/correct_sentence_enhanced")
async def correct_sentence_enhanced_endpoint(request: SentenceCorrectionRequest):
    """향상된 문장 교정을 수행합니다."""
    try:
        logger.info(f"🔍 향상된 문장 교정 요청 처리 중... (텍스트: {request.text})")
        
        # 향상된 문장 교정 수행
        result = correct_sentence_with_ai_enhanced(text=request.text)
        
        logger.info(f"향상된 교정 결과: '{result['corrected_text']}' (방법: {result['method_used']})")
        
        return result
        
    except Exception as e:
        logger.error(f"향상된 문장 교정 처리 중 오류: {e}")
        return {
            "success": True,
            "corrected_text": request.text,
            "method_used": "fallback"
        }

@router.post("/audio_quality_check")
@router.post("/api/v1/audio_quality_check")
async def check_audio_quality_endpoint(audio_file: UploadFile = File(...)):
    """오디오 품질을 검증합니다."""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 오디오 품질 검증
        quality_result = validate_audio_quality(temp_path)
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        return quality_result
        
    except Exception as e:
        logger.error(f"오디오 품질 검증 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stt_enhancement_status")
@router.get("/api/v1/stt_enhancement_status")
async def get_stt_enhancement_status():
    """STT 향상 기능 상태를 반환합니다."""
    return {
        "enhanced_stt_available": True,
        "audio_quality_check_available": True,
        "sentence_correction_available": True,
        "confidence_scoring": True,
        "alternative_suggestions": True
    }

@router.post("/tts")
@router.post("/api/v1/tts")
async def text_to_speech_endpoint(
    request: SentenceCorrectionRequest = None, 
    text: str = Form(None),
    voice_name: str = Form('ko-KR-Chirp3-HD-Leda'),
    gender: str = Form('FEMALE'),
    speaking_rate: float = Form(1.1),
    pitch: float = Form(0.0)
):
    """텍스트를 음성으로 변환합니다."""
    try:
        # 텍스트 추출
        if request and request.text:
            text_to_speak = request.text
        elif text:
            text_to_speak = text
        else:
            raise HTTPException(status_code=400, detail="텍스트가 제공되지 않았습니다.")
        
        logger.info(f"🔍 TTS 요청 처리 중... (텍스트 길이: {len(text_to_speak)}, 음성: {voice_name}, 성별: {gender})")
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
        
        # TTS 수행
        success = text_to_speech(
            text=text_to_speak,
            output_path=temp_path,
            voice_name=voice_name,
            gender=gender,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="음성 합성에 실패했습니다.")
        
        # 파일 반환
        from fastapi.responses import FileResponse
        return FileResponse(
            path=temp_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except Exception as e:
        logger.error(f"TTS 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 