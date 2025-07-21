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

async def analyze_with_gemini(text: str) -> Optional[Dict]:
    """Gemini AI를 사용하여 T/F 성향 분석 (ver02 스타일 상세 분석)"""
    logger.info("🔍 Gemini AI 분석 시작")
    logger.info(f"📝 입력 텍스트: {text}")
    
    try:
        # 1. API 키 확인
        logger.info("🔑 Gemini API 키 확인 중...")
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            from mbti_analyzer.config.settings import settings
            gemini_key = settings.gemini_api_key
            logger.info("환경변수에서 API 키를 찾지 못해 설정 파일에서 확인")
        
        if not gemini_key:
            logger.error("❌ Gemini API 키가 설정되지 않았습니다.")
            logger.error("GEMINI_API_KEY 환경변수 또는 settings.gemini_api_key를 확인하세요.")
            return None
        
        logger.info("✅ Gemini API 키 확인 완료")
        
        # 2. Gemini AI 모델 초기화
        logger.info("🤖 Gemini AI 모델 초기화 중...")
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini AI 모델 초기화 완료")
        
        # 3. 프롬프트 생성 (ver02 스타일 상세 분석)
        logger.info("📝 분석 프롬프트 생성 중...")
        prompt = f"""
MBTI T/F 성향 분석 전문가입니다. 답변을 분석하여 T/F 성향을 평가하세요.

[분석 기준]
- T(Thinking): 논리적, 객관적, 분석적 사고, 원인 분석, 체계적 접근, 효율성 중시, 문제 해결 지향
- F(Feeling): 감정적, 공감적, 관계 중심적 사고, 기분 고려, 공감 표현, 관계 중시, 감정적 지지
- 점수: 0(매우 강한 T) ~ 100(매우 강한 F), 50=균형

[핵심 분석 원칙]
1. 답변의 주요 의도와 핵심 메시지에 집중
2. T 성향 강한 표현: "분석", "원인", "논리", "체계", "효율", "방지", "파악", "결과", "해결", "접근", "단계별", "체계적"
3. F 성향 강한 표현: "기분", "마음", "공감", "힘들", "안타깝", "궁금", "도와", "함께", "지지", "위로", "걱정", "안타깝"
4. 혼합 답변 분석: 
   - T+F 혼합 답변의 경우: 핵심 메시지의 방향성에 따라 판단
   - "분석하자" + "자책하지 마" → T 성향이 우선 (40-60점)
   - "함께 생각해보자" → F 성향이 우선 (60-80점)
5. 맥락별 점수 가이드:
   - 순수 T 성향 (논리적 해결): 20-40점
   - T+F 혼합 (분석+공감): 40-70점  
   - 순수 F 성향 (감정적 지지): 70-90점

[출력 형식]
[분석] 답변자의 T/F 성향 분석 (성향 강도와 주요 특징 명시)
[근거] 분석 근거 (구체적 키워드와 표현 방식, 의도 파악)
[제안] 개선 제안 3가지
[대안] 대안 답변
점수: X

답변: {text}
"""
        logger.info("✅ 분석 프롬프트 생성 완료")
        logger.info(f"📋 프롬프트 길이: {len(prompt)} 문자")
        
        # 4. Gemini AI API 호출
        logger.info("🚀 Gemini AI API 호출 시작...")
        response = model.generate_content(prompt)
        logger.info("✅ Gemini AI API 호출 완료")
        
        # 5. 응답 검증
        logger.info("🔍 Gemini AI 응답 검증 중...")
        if not response:
            logger.error("❌ Gemini AI 응답이 None입니다.")
            return None
            
        if not response.text:
            logger.error("❌ Gemini AI 응답 텍스트가 비어있습니다.")
            return None
        
        response_text = response.text.strip()
        logger.info(f"📄 응답 텍스트 길이: {len(response_text)} 문자")
        logger.info(f"📄 응답 텍스트 미리보기: {response_text[:200]}...")
        
        # 6. 점수 추출 (ver02 스타일 개선된 파싱)
        logger.info("🔢 점수 추출 중...")
        import re
        
        # 점수 파싱 정규식 개선: 다양한 띄어쓰기/콜론/한글자 오타 허용
        score_match = re.search(r"점\s*수\s*[:：=\-]?\s*(\d{1,3})", response_text)
        if score_match:
            score = float(score_match.group(1))
            logger.info(f"✅ 점수 추출 성공: {score}")
            
            # 상세분석 파싱 (ver02 스타일)
            def extract(tag):
                m = re.search(rf"\[{tag}\](.*?)(?=\[|$)", response_text, re.DOTALL)
                return m.group(1).strip() if m else ""
            
            detailed_analysis = extract("분석")
            reasoning = extract("근거")
            suggestions_raw = extract("제안")
            suggestions = [s.strip() for s in suggestions_raw.split("\n") if s.strip()] if suggestions_raw else []
            alternative_response = extract("대안")
            
            logger.info(f"✅ 상세분석 파싱 완료:")
            logger.info(f"📋 상세분석: {detailed_analysis[:50]}...")
            logger.info(f"🔍 분석근거: {reasoning[:50]}...")
            logger.info(f"💡 개선제안 개수: {len(suggestions)}")
            logger.info(f"🔄 대안답변: {alternative_response[:50]}...")
            
            # 상세 분석 결과를 딕셔너리로 반환
            return {
                "score": score,
                "detailed_analysis": detailed_analysis,
                "reasoning": reasoning,
                "suggestions": suggestions,
                "alternative_response": alternative_response
            }
        else:
            logger.error("❌ 점수 추출 실패: 점수 패턴을 찾을 수 없습니다.")
            logger.error(f"📄 전체 응답 텍스트: {response_text}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Gemini AI 분석 실패: {e}")
        logger.error(f"❌ 오류 타입: {type(e).__name__}")
        logger.error(f"❌ 오류 상세: {str(e)}")
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
    logger.info("=" * 50)
    logger.info("🚀 텍스트 분석 시작")
    logger.info(f"📝 입력 텍스트: {text.strip()}")
    logger.info(f"📝 텍스트 길이: {len(text.strip())} 문자")
    
    # 1. Gemini AI 시도
    logger.info("🔍 1단계: Gemini AI 분석 시도 중...")
    try:
        gemini_result = await analyze_with_gemini(text)
        if gemini_result is not None:
            logger.info(f"✅ Gemini AI 분석 성공: {gemini_result}")
            logger.info("🎯 Gemini AI로 분석 완료")
            return {
                "score": gemini_result["score"],
                "method": "gemini",
                "success": True,
                "detailed_analysis": gemini_result.get("detailed_analysis"),
                "reasoning": gemini_result.get("reasoning"),
                "suggestions": gemini_result.get("suggestions"),
                "alternative_response": gemini_result.get("alternative_response")
            }
        else:
            logger.warning("⚠️ Gemini AI 분석 결과가 None입니다.")
            logger.warning("⚠️ 다음 단계(Groq AI)로 진행합니다.")
    except Exception as e:
        logger.error(f"❌ Gemini AI 분석 실패: {e}")
        logger.error(f"❌ 오류 타입: {type(e).__name__}")
        logger.error(f"❌ 오류 상세: {str(e)}")
        logger.warning("⚠️ 다음 단계(Groq AI)로 진행합니다.")
    
    # 2. Groq AI 시도
    logger.info("🔍 2단계: Groq AI 분석 시도 중...")
    try:
        groq_result = await analyze_with_groq(text)
        if groq_result is not None:
            logger.info(f"✅ Groq AI 분석 성공: {groq_result}")
            logger.info("🎯 Groq AI로 분석 완료")
            return {
                "score": groq_result,
                "method": "groq",
                "success": True
            }
        else:
            logger.warning("⚠️ Groq AI 분석 결과가 None입니다.")
            logger.warning("⚠️ 다음 단계(Fallback)로 진행합니다.")
    except Exception as e:
        logger.error(f"❌ Groq AI 분석 실패: {e}")
        logger.warning("⚠️ 다음 단계(Fallback)로 진행합니다.")
    
    # 3. Fallback 분석
    logger.info("🔍 3단계: Fallback 분석 함수 사용 중...")
    try:
        fallback_score = analyze_tf_tendency(text)
        logger.info(f"✅ Fallback 분석 성공: {fallback_score}")
        logger.info("🎯 Fallback으로 분석 완료")
        return {
            "score": fallback_score,
            "method": "fallback",
            "success": True
        }
    except Exception as e:
        logger.error(f"❌ Fallback 분석 실패: {e}")
        logger.error("❌ 모든 분석 방법이 실패했습니다.")
        return {
            "score": 50.0,  # 기본값
            "method": "error",
            "success": False
        } 