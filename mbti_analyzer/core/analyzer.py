"""
T/F 성향 분석 로직

텍스트를 분석하여 MBTI의 T(사고형)/F(감정형) 성향을 판단하는 핵심 로직입니다.
"""

import re
import logging
from typing import Dict, Optional
import google.generativeai as genai
import os
from groq import AsyncGroq

logger = logging.getLogger(__name__)

def analyze_tf_tendency(text: str) -> float:
    """
    텍스트를 분석하여 T/F 성향 점수를 반환합니다.
    0에 가까울수록 T, 100에 가까울수록 F 성향입니다.
    """
    text = text.lower()
    logger.info(f"🔍 Fallback 분석 시작: {text[:50]}...")

    # 사고형(T) 강한 무심/단정/객관적 표현 패턴 (확실한 사고형)
    t_strong_patterns = [
        r"어쩌라고", r"상관없어", r"알아서 해", r"내 알 바 아냐", r"그게 나랑 무슨 상관이야",
        r"네 마음대로 해", r"내가 뭘", r"그건 네 문제야", r"그건 중요하지 않아"
    ]
    t_strong_count = sum(len(re.findall(pattern, text)) for pattern in t_strong_patterns)
    if t_strong_count > 0:
        score = max(15, 30 - (t_strong_count - 1) * 5)
        return float(score)

    # 싸가지 없는(공감 없는 퉁명/무심) 패턴 (살짝 T)
    t_rude_patterns = [
        r"몰라", r"딱히", r"별 생각 없어", r"신경 안 써", r"관심 없어", r"그냥 그래", r"글쎄", r"음[.\.\,\!\?…]*$", r"별로야"
    ]
    t_rude_count = sum(len(re.findall(pattern, text)) for pattern in t_rude_patterns)
    if t_rude_count > 0:
        # 퉁명/무심 패턴이 감지되면 35~45점(살짝 T)
        score = max(35, 45 - (t_rude_count - 1) * 3)
        return float(score)

    # 1. 키워드(핵심/약한) 및 가중치
    t_keywords_strong = [
        '논리', '분석', '판단', '효율', '객관', '사실', '증거', '합리', '이성', '체계',
        '정확', '명확', '일관', '데이터', '통계', '측정',
        '맞다', '틀렸다', '정답', '확실', '명백', '분명', '확인',
        '검토', '평가', '기준', '조건', '해결', '개선',
        '최적', '효과', '결정', '선택', '우선순위', '중요도',
        '불가능', '문제', '해답', '답', '반드시', '무조건', '체크', '실용적', '계산'
    ]
    t_keywords_weak = [
        '계획', '전략', '목표', '성과', '방법', '해야', '해야지', '하자', '됐다', '안 돼', '안 됨',
        '확실히', '분명히', '정확히', '당연히', '바로', '먼저', '우선', '일단', '정리', '효과적', '효율적',
        '간단', '복잡', '가능', '됐다', '우선', '일단', '편해', '편리', '쉽다', '어렵다', '시간', '가격', '비용'
    ]
    f_keywords_strong = [
        '감정', '마음', '공감', '배려', '이해', '조화', '협력', '관계', '소통', '친밀',
        '가치', '의미', '도덕', '윤리', '지원', '격려', '행복', '슬프', '걱정', '미안', '고마', '소중', '사랑',
        '따뜻', '포근', '아늑', '편안', '안심', '든든', '기분', '느낌', '마음가짐', '심정',
        '함께', '같이', '서로', '우리 모두', '친구', '가족', '사람들', '동료들',
        '예뻐', '귀여워', '착해', '멋져', '좋아해', '싫어해'
    ]
    f_keywords_weak = [
        '기뻐', '즐거워', '신나', '행복해', '만족', '뿌듯', '속상', '짜증', '화나', '답답', '불안', '신경 쓰여',
        '우리', '다함께', '함께 하자', '같이 하자', '마음에', '따뜻', '포근', '보고 싶어', '만나고 싶어', '하고 싶어'
    ]

    # 가중치 적용 카운트
    t_count = sum(2 for keyword in t_keywords_strong if keyword in text) + sum(1 for keyword in t_keywords_weak if keyword in text)
    f_count = sum(2 for keyword in f_keywords_strong if keyword in text) + sum(1 for keyword in f_keywords_weak if keyword in text)

    # 패턴/어조/구조 분석
    f_patterns = [
        r'어떻게 생각|어떤 느낌|괜찮을까|어떨까|좋을 것 같|나쁠 것 같',
        r'하면 좋겠|했으면|인 것 같|느낌이|기분이',
        r'함께|같이|서로|우리|모두|다함께',
        r'미안|고마워|사랑|소중|아껴|챙기',
        r'공감|이해|위로|격려|응원',
        r'좋아|싫어|예뻐|귀여워|재밌|지루',
        r'기분 좋|느낌 좋|마음에|따뜻|포근',
        r'하고 싶어|가고 싶어|보고 싶어|만나고 싶어',
        r'같이 하자|함께 하자|우리 모두|다 같이'
    ]
    t_patterns = [
        r'해야 한다|해야지|하자|하면 돼|되면|안 되면',
        r'당연히|정확히|맞다|틀렸다|옳다|그르다|확실히|분명히',
        r'효율적|체계적|논리적|합리적|객관적',
        r'중요한 건|핵심은|문제는|해결책은|방법은',
        r'먼저|우선|차례로|단계별로|계획적으로',
        r'그냥|바로|빨리|즉시|일단|우선',
        r'안 돼|안 됨|되네|됐다|가능|불가능',
        r'쉽다|어렵다|간단|복잡|편해|편리',
        r'계산|비용|가격|시간|효과|실용'
    ]
    f_pattern_count = sum(len(re.findall(pattern, text)) for pattern in f_patterns)
    t_pattern_count = sum(len(re.findall(pattern, text)) for pattern in t_patterns)
    
    soft_tone = len(re.findall(r'것 같아|인 듯|아마|혹시|면 어떨까|하면 좋겠|~인가|~할까|~지 않을까', text))
    firm_tone = len(re.findall(r'반드시|무조건|확실히|당연히|명백히|분명히|해야|하자|된다|안 된다', text))
    question_suggestion = len(re.findall(r'\?|할까|어떨까|좋을까|어때|괜찮을까', text))
    statement_command = len(re.findall(r'다\.|이다\.|하자\.|해야\.|된다\.|안 된다\.', text))
    
    total_keywords = t_count + f_count
    total_patterns = f_pattern_count + t_pattern_count  
    total_tone = soft_tone + firm_tone
    total_structure = question_suggestion + statement_command
    
    # 2. 키워드 점수(가중치 반영)
    if total_keywords == 0:
        keyword_score = 50
    else:
        t_ratio = t_count / total_keywords if total_keywords > 0 else 0
        f_ratio = f_count / total_keywords if total_keywords > 0 else 0
        if t_ratio > f_ratio:
            intensity = min(t_count, 4)
            keyword_score = 25 - (intensity * 7)  # 기존 30에서 25로, 강도별 -7점씩
        elif f_ratio > t_ratio:
            intensity = min(f_count, 4)
            keyword_score = 75 + (intensity * 7)  # 기존 70에서 75로, 강도별 +7점씩
        else:
            keyword_score = 50
    
    # 3. 패턴/어조/구조 점수(동점/애매시 가중치 증가)
    if total_patterns == 0:
        pattern_score = 50
    else:
        t_pattern_ratio = t_pattern_count / total_patterns
        f_pattern_ratio = f_pattern_count / total_patterns
        if t_pattern_ratio > f_pattern_ratio:
            intensity = min(t_pattern_count, 3)
            pattern_score = 30 - (intensity * 5)
        elif f_pattern_ratio > t_pattern_ratio:
            intensity = min(f_pattern_count, 3)
            pattern_score = 70 + (intensity * 5)
        else:
            pattern_score = 50
    
    if total_tone == 0:
        tone_score = 50
    else:
        if firm_tone > soft_tone:
            intensity = min(firm_tone, 2)
            tone_score = 25 - (intensity * 5)
        elif soft_tone > firm_tone:
            intensity = min(soft_tone, 2)
            tone_score = 75 + (intensity * 5)
        else:
            tone_score = 50
    
    if total_structure == 0:
        structure_score = 50
    else:
        if statement_command > question_suggestion:
            structure_score = 30
        elif question_suggestion > statement_command:
            structure_score = 70
        else:
            structure_score = 50
    
    text_length = len(text.replace(' ', ''))
    # 동점/애매할수록 패턴/어조/구조 가중치 증가
    if total_keywords == 0 or abs(t_count - f_count) <= 2:
        keyword_weight = 0.25
        pattern_weight = 0.3
        tone_weight = 0.25
        structure_weight = 0.2
    elif text_length < 15:
        keyword_weight = 0.5
        pattern_weight = 0.2  
        tone_weight = 0.15
        structure_weight = 0.15
    elif text_length < 30:
        keyword_weight = 0.45
        pattern_weight = 0.25
        tone_weight = 0.2
        structure_weight = 0.1
    else:
        keyword_weight = 0.4
        pattern_weight = 0.3
        tone_weight = 0.2
        structure_weight = 0.1
    
    # 4. 최종 점수 계산
    final_score = (
        keyword_score * keyword_weight +
        pattern_score * pattern_weight +
        tone_score * tone_weight +
        structure_score * structure_weight
    )
    
    # 5. 점수 범위 제한 (15~85)
    final_score = max(15, min(85, final_score))
    
    logger.info(f"🔍 Fallback 분석 완료: {final_score}점")
    return float(final_score)

async def analyze_with_gemini(text: str) -> Optional[float]:
    """Gemini AI를 사용하여 T/F 성향 분석"""
    try:
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            from mbti_analyzer.config.settings import settings
            gemini_key = settings.gemini_api_key
        
        if not gemini_key:
            logger.warning("Gemini API 키가 설정되지 않았습니다.")
            return None
        
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
다음 한국어 텍스트를 분석하여 MBTI의 T(사고형)/F(감정형) 성향을 평가해주세요.

평가 기준:
- T(사고형): 논리적, 객관적, 분석적, 효율성 중시
- F(감정형): 감정적, 공감적, 관계 중시, 가치 기반

텍스트: "{text}"

다음 형식으로만 응답해주세요:
<TENDENCY>점수</TENDENCY>
<REASONING>분석 근거</REASONING>

점수는 0-100 사이의 숫자로, 0에 가까울수록 T 성향, 100에 가까울수록 F 성향입니다.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # 점수 추출
        import re
        tendency_match = re.search(r'<TENDENCY>(\d+(?:\.\d+)?)</TENDENCY>', response_text)
        if tendency_match:
            score = float(tendency_match.group(1))
            return score
        
        return None
        
    except Exception as e:
        logger.error(f"Gemini AI 분석 실패: {e}")
        return None

async def analyze_with_groq(text: str) -> Optional[float]:
    """Groq AI를 사용하여 T/F 성향 분석"""
    try:
        groq_key = os.getenv('GROQ_API_KEY')
        if not groq_key:
            from mbti_analyzer.config.settings import settings
            groq_key = settings.groq_api_key
        
        if not groq_key:
            logger.warning("Groq API 키가 설정되지 않았습니다.")
            return None
        
        client = AsyncGroq(api_key=groq_key)
        
        prompt = f"""
다음 한국어 텍스트를 분석하여 MBTI의 T(사고형)/F(감정형) 성향을 평가해주세요.

평가 기준:
- T(사고형): 논리적, 객관적, 분석적, 효율성 중시
- F(감정형): 감정적, 공감적, 관계 중시, 가치 기반

텍스트: "{text}"

다음 형식으로만 응답해주세요:
<TENDENCY>점수</TENDENCY>
<REASONING>분석 근거</REASONING>

점수는 0-100 사이의 숫자로, 0에 가까울수록 T 성향, 100에 가까울수록 F 성향입니다.
"""
        
        response = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # 점수 추출
        import re
        tendency_match = re.search(r'<TENDENCY>(\d+(?:\.\d+)?)</TENDENCY>', response_text)
        if tendency_match:
            score = float(tendency_match.group(1))
            return score
        
        return None
        
    except Exception as e:
        logger.error(f"Groq AI 분석 실패: {e}")
        return None

async def analyze_text(text: str) -> Dict:
    """텍스트를 분석하여 T/F 성향 점수를 반환합니다."""
    logger.info(f"🔍 입력 텍스트: {text.strip()}")
    
    # 1. Gemini AI 시도
    logger.info("🔍 Gemini AI 분석 시도 중...")
    try:
        gemini_result = await analyze_with_gemini(text)
        if gemini_result is not None:
            return {
                "score": gemini_result,
                "method": "gemini",
                "success": True
            }
    except Exception as e:
        logger.info(f"❌ Gemini AI 분석 실패: {e}")
    
    # 2. Groq AI 시도
    logger.info("🔍 Groq AI 분석 시도 중...")
    try:
        groq_result = await analyze_with_groq(text)
        if groq_result is not None:
            return {
                "score": groq_result,
                "method": "groq",
                "success": True
            }
    except Exception as e:
        logger.info(f"❌ Groq AI 분석 실패: {e}")
    
    # 3. Fallback 분석
    logger.info("🔍 Fallback 분석 함수 사용 중...")
    fallback_score = analyze_tf_tendency(text)
    
    return {
        "score": fallback_score,
        "method": "fallback",
        "success": True
    } 