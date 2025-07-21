# MBTI T/F 성향 분석기 사용법

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정 (선택사항)
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```env
GEMINI_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. 서버 실행
```bash
# 방법 1: 실행 스크립트 사용
python run.py

# 방법 2: uvicorn 직접 사용
uvicorn mbti_analyzer.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 웹 브라우저에서 접속
```
http://localhost:8000
```

## 📚 API 사용법

### 텍스트 분석
```python
import requests

# T/F 성향 분석
response = requests.post("http://localhost:8000/api/v1/analyze", 
                        json={"text": "논리적으로 생각해보면 이 방법이 가장 효율적입니다."})

result = response.json()
print(f"T/F 점수: {result['score']}")
print(f"분석 결과: {result['detailed_analysis']}")
```

### AI 질문 생성
```python
# AI 질문 생성
response = requests.post("http://localhost:8000/api/v1/generate_questions",
                        json={"count": 5, "difficulty": "medium"})

questions = response.json()
print("생성된 질문들:", questions['questions'])
```

### 음성 인식 (STT)
```python
# 음성 파일을 텍스트로 변환
with open("audio.wav", "rb") as f:
    files = {"audio_file": f}
    response = requests.post("http://localhost:8000/api/v1/stt", files=files)

result = response.json()
print(f"인식된 텍스트: {result['text']}")
```

## 🔧 개발 모드

### 모듈 테스트
```bash
# 기본 기능 테스트
python test_simple.py

# 전체 모듈 테스트
python test_imports.py
```

### 패키지 설치 (개발용)
```bash
# 개발 모드로 설치
pip install -e .
```

## 📁 프로젝트 구조

```
mbti_analyzer/
├── core/                    # 핵심 분석 로직
│   ├── analyzer.py         # T/F 분석 엔진
│   ├── question_generator.py # AI 질문 생성
│   └── final_analyzer.py   # 최종 분석 엔진
├── models/                  # 데이터 모델
│   └── schemas.py          # Pydantic 모델들
├── modules/                 # 기존 모듈들
│   ├── stt_module.py       # 음성 인식
│   ├── tts_module.py       # 음성 합성
│   └── text_summary_module.py # 텍스트 요약
├── api/                     # API 라우터
│   ├── main.py             # FastAPI 앱
│   └── routes/             # API 엔드포인트
├── config/                  # 설정 관리
├── utils/                   # 유틸리티
├── static/                  # 프론트엔드
├── requirements.txt         # 의존성 패키지
├── run.py                   # 실행 스크립트
└── README.md               # 프로젝트 문서
```

## 🎯 주요 기능

### 1. T/F 성향 분석
- 텍스트 기반 MBTI T/F 성향 분석
- 키워드, 패턴, 어조 종합 분석
- 0-100 점수 시스템 (0=T, 100=F)

### 2. AI 질문 생성
- Gemini API 기반 동적 질문 생성
- 난이도별 질문 생성 (easy, medium, hard)
- 폴백 질문 시스템

### 3. 음성 처리
- STT (Speech-to-Text): 음성 파일을 텍스트로 변환
- TTS (Text-to-Speech): 텍스트를 음성으로 변환
- 다양한 오디오 형식 지원

### 4. 종합 분석
- 다중 질문 결과 종합 분석
- 성향별 소통 전략 제시
- 키워드 분석 및 성장 영역 제안

## 🔒 보안 고려사항

- 입력 텍스트 sanitization 적용
- 파일 업로드 크기 제한 (10MB)
- 지원 오디오 형식 검증
- API 키 환경변수 관리

## 🚀 배포

### Docker 배포
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "mbti_analyzer.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 환경변수 설정
```bash
export GEMINI_API_KEY=your_api_key_here
export HOST=0.0.0.0
export PORT=8000
```

## 📞 문제 해결

### 일반적인 문제들

1. **모듈 임포트 오류**
   ```bash
   # Python 경로 확인
   python -c "import sys; print(sys.path)"
   
   # 패키지 설치
   pip install -e .
   ```

2. **API 키 오류**
   ```bash
   # 환경변수 확인
   echo $GEMINI_API_KEY
   
   # .env 파일 생성
   echo "GEMINI_API_KEY=your_key_here" > .env
   ```

3. **포트 충돌**
   ```bash
   # 다른 포트 사용
   python run.py --port 8001
   ```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 