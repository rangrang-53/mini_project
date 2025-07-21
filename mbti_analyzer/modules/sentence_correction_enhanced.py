import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CorrectionResult:
    """문장 교정 결과"""
    original_text: str
    corrected_text: str
    confidence: float
    corrections_made: List[str]
    suggestions: List[str]
    context_aware: bool


class EnhancedSentenceCorrector:
    """
    향상된 문장 교정 시스템
    """
    
    def __init__(self):
        # 한국어 특화 교정 규칙
        self.korean_corrections = {
            # 조사 오류
            '은/는': {'은': '은', '는': '는'},
            '이/가': {'이': '이', '가': '가'},
            '을/를': {'을': '을', '를': '를'},
            '의/에': {'의': '의', '에': '에'},
            
            # 연결어 오류
            '그리고': '그리고',
            '그런데': '그런데',
            '그렇지만': '그렇지만',
            '그러니까': '그러니까',
            '그러면': '그러면',
            '그래서': '그래서',
            
            # 감정 표현
            '좋아': '좋아',
            '싫어': '싫어',
            '재미있어': '재미있어',
            '어려워': '어려워',
            '쉬워': '쉬워',
            '힘들어': '힘들어',
            
            # MBTI 관련 용어
            '생각': '생각',
            '느낌': '느낌',
            '감정': '감정',
            '논리': '논리',
            '사실': '사실',
            '객관': '객관',
            '주관': '주관',
        }
        
        # 문맥별 교정 규칙
        self.context_rules = {
            'mbti_question': {
                'keywords': ['생각', '느낌', '감정', '논리', '사실'],
                'corrections': {
                    '생각해': '생각해',
                    '느껴': '느껴',
                    '감정적': '감정적',
                    '논리적': '논리적',
                }
            },
            'emotion_expression': {
                'keywords': ['좋', '싫', '재미', '어려', '쉬', '힘들'],
                'corrections': {
                    '좋아': '좋아',
                    '싫어': '싫어',
                    '재미있어': '재미있어',
                }
            }
        }
    
    def correct_sentence_enhanced(self, text: str, context: str = 'general') -> CorrectionResult:
        """
        향상된 문장 교정 수행
        """
        if not text:
            return CorrectionResult(
                original_text=text,
                corrected_text=text,
                confidence=0.0,
                corrections_made=[],
                suggestions=[],
                context_aware=False
            )
        
        original_text = text
        corrected_text = text
        corrections_made = []
        suggestions = []
        
        # 1단계: 기본 정리
        corrected_text = self._basic_cleanup(corrected_text)
        
        # 2단계: 한국어 특화 교정
        corrected_text, basic_corrections = self._korean_specific_corrections(corrected_text)
        corrections_made.extend(basic_corrections)
        
        # 3단계: 문맥별 교정
        corrected_text, context_corrections = self._context_aware_corrections(corrected_text, context)
        corrections_made.extend(context_corrections)
        
        # 4단계: 문장 구조 개선
        corrected_text, structure_corrections = self._improve_sentence_structure(corrected_text)
        corrections_made.extend(structure_corrections)
        
        # 5단계: 신뢰도 계산
        confidence = self._calculate_correction_confidence(original_text, corrected_text)
        
        # 6단계: 추가 제안 생성
        suggestions = self._generate_suggestions(corrected_text, context)
        
        return CorrectionResult(
            original_text=original_text,
            corrected_text=corrected_text,
            confidence=confidence,
            corrections_made=corrections_made,
            suggestions=suggestions,
            context_aware=len(context_corrections) > 0
        )
    
    def _basic_cleanup(self, text: str) -> str:
        """기본 텍스트 정리"""
        # 불필요한 공백 제거
        text = ' '.join(text.split())
        
        # 특수문자 정리
        text = re.sub(r'[^\w\s가-힣.,!?~]', '', text)
        
        return text.strip()
    
    def _korean_specific_corrections(self, text: str) -> tuple[str, List[str]]:
        """한국어 특화 교정"""
        corrections_made = []
        
        for pattern, correction in self.korean_corrections.items():
            if isinstance(correction, dict):
                # 조사별 교정
                for wrong, right in correction.items():
                    if wrong in text:
                        text = text.replace(wrong, right)
                        corrections_made.append(f"조사 교정: {wrong} → {right}")
            else:
                # 일반 교정
                if pattern in text:
                    text = text.replace(pattern, correction)
                    corrections_made.append(f"단어 교정: {pattern} → {correction}")
        
        return text, corrections_made
    
    def _context_aware_corrections(self, text: str, context: str) -> tuple[str, List[str]]:
        """문맥별 교정"""
        corrections_made = []
        
        if context in self.context_rules:
            rule = self.context_rules[context]
            
            # 키워드 기반 문맥 확인
            context_keywords = rule['keywords']
            found_keywords = [kw for kw in context_keywords if kw in text]
            
            if found_keywords:
                # 문맥별 교정 적용
                for pattern, correction in rule['corrections'].items():
                    if pattern in text:
                        text = text.replace(pattern, correction)
                        corrections_made.append(f"문맥 교정: {pattern} → {correction}")
        
        return text, corrections_made
    
    def _improve_sentence_structure(self, text: str) -> tuple[str, List[str]]:
        """문장 구조 개선"""
        corrections_made = []
        
        # 1. 불완전한 문장 완성
        if text and not text.endswith(('.', '!', '?', '~', '다', '까', '네', '요', '어', '아')):
            # 문맥에 따른 종결어미 추가
            if any(word in text for word in ['좋', '싫', '재미', '어려', '쉬', '힘들']):
                text += '어.'
                corrections_made.append("종결어미 추가: 어.")
            elif any(word in text for word in ['생각', '느낌', '기분']):
                text += '이야.'
                corrections_made.append("종결어미 추가: 이야.")
            else:
                text += '.'
                corrections_made.append("종결어미 추가: .")
        
        # 2. 중복 단어 제거
        words = text.split()
        cleaned_words = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                cleaned_words.append(word)
        
        if len(cleaned_words) < len(words):
            text = ' '.join(cleaned_words)
            corrections_made.append("중복 단어 제거")
        
        # 3. 문장 길이 최적화
        if len(text) > 100:
            # 긴 문장을 여러 문장으로 분할
            sentences = re.split(r'[.!?]', text)
            if len(sentences) > 1:
                text = '. '.join([s.strip() for s in sentences if s.strip()]) + '.'
                corrections_made.append("긴 문장 분할")
        
        return text, corrections_made
    
    def _calculate_correction_confidence(self, original: str, corrected: str) -> float:
        """교정 신뢰도 계산"""
        if not original or not corrected:
            return 0.0
        
        # 1. 기본 신뢰도 (원본과의 유사도)
        similarity = self._calculate_similarity(original, corrected)
        
        # 2. 문장 품질 점수
        quality_score = self._calculate_quality_score(corrected)
        
        # 3. 최종 신뢰도 (가중 평균)
        confidence = (similarity * 0.6) + (quality_score * 0.4)
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        if not text1 or not text2:
            return 0.0
        
        # 간단한 유사도 계산 (공통 단어 비율)
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_quality_score(self, text: str) -> float:
        """문장 품질 점수 계산"""
        if not text:
            return 0.0
        
        score = 1.0
        
        # 1. 길이 점수
        if len(text) < 5:
            score *= 0.5
        elif len(text) > 200:
            score *= 0.8
        
        # 2. 문장 끝 점수
        if not text.endswith(('.', '!', '?', '~')):
            score *= 0.7
        
        # 3. 중복 단어 점수
        words = text.split()
        unique_words = set(words)
        if len(words) > 0:
            uniqueness = len(unique_words) / len(words)
            score *= (0.5 + uniqueness * 0.5)
        
        return score
    
    def _generate_suggestions(self, text: str, context: str) -> List[str]:
        """추가 제안 생성"""
        suggestions = []
        
        # 1. 문장 길이 제안
        if len(text) < 10:
            suggestions.append("더 자세한 답변을 해주시면 분석이 정확해집니다.")
        elif len(text) > 100:
            suggestions.append("답변을 간단히 요약해주시면 더 정확한 분석이 가능합니다.")
        
        # 2. 문맥별 제안
        if context == 'mbti_question':
            if '생각' in text or '느낌' in text:
                suggestions.append("구체적인 예시를 들어주시면 더 정확한 분석이 가능합니다.")
        
        # 3. 감정 표현 제안
        emotion_words = ['좋', '싫', '재미', '어려', '쉬', '힘들']
        if any(word in text for word in emotion_words):
            suggestions.append("감정의 강도나 이유를 추가로 설명해주시면 좋겠습니다.")
        
        return suggestions


async def correct_sentence_with_ai_enhanced(text: str, context: str = 'general') -> Dict:
    """
    AI와 향상된 교정 시스템을 결합한 문장 교정
    """
    try:
        # 1단계: 향상된 교정 시스템 사용
        corrector = EnhancedSentenceCorrector()
        enhanced_result = corrector.correct_sentence_enhanced(text, context)
        
        # 2단계: AI 교정 (기존 시스템 활용)
        ai_corrected = await correct_sentence_with_ai(text)
        
        # 3단계: 결과 비교 및 최적 선택
        final_result = _select_best_correction(enhanced_result, ai_corrected)
        
        return {
            "success": True,
            "original_text": text,
            "corrected_text": final_result["corrected_text"],
            "confidence": final_result["confidence"],
            "corrections_made": final_result["corrections_made"],
            "suggestions": final_result["suggestions"],
            "enhanced_correction": enhanced_result.corrected_text,
            "ai_correction": ai_corrected.get("corrected_text", text),
            "method_used": final_result["method_used"]
        }
        
    except Exception as e:
        logger.error(f"향상된 문장 교정 중 오류: {e}")
        return {
            "success": False,
            "original_text": text,
            "corrected_text": text,
            "error": str(e)
        }


async def correct_sentence_with_ai(text: str) -> Dict:
    """
    AI를 사용한 문장 교정 (기존 시스템과 호환)
    """
    try:
        # 기존 API 엔드포인트 호출
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:8000/correct_sentence',
                json={'text': text}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"AI 교정 실패: {response.status}")
                    
    except Exception as e:
        logger.error(f"AI 교정 중 오류: {e}")
        return {
            "success": True,
            "corrected_text": text,
            "has_changes": False,
            "fallback": True
        }


def _select_best_correction(enhanced_result: CorrectionResult, ai_result: Dict) -> Dict:
    """
    향상된 교정과 AI 교정 중 더 나은 결과 선택
    """
    enhanced_confidence = enhanced_result.confidence
    ai_confidence = 0.8  # AI 기본 신뢰도
    
    # AI 결과가 있는 경우 신뢰도 조정
    if ai_result.get("success") and ai_result.get("has_changes"):
        ai_confidence = 0.9
    
    # 신뢰도가 높은 방법 선택
    if enhanced_confidence > ai_confidence:
        return {
            "corrected_text": enhanced_result.corrected_text,
            "confidence": enhanced_confidence,
            "corrections_made": enhanced_result.corrections_made,
            "suggestions": enhanced_result.suggestions,
            "method_used": "enhanced"
        }
    else:
        return {
            "corrected_text": ai_result.get("corrected_text", enhanced_result.corrected_text),
            "confidence": ai_confidence,
            "corrections_made": [],
            "suggestions": enhanced_result.suggestions,
            "method_used": "ai"
        } 