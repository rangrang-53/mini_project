# MBTI T/F 성향 분석기 (모듈화 버전)

이 프로젝트는 사용자의 텍스트 응답을 분석하여 MBTI의 T(사고형)/F(감정형) 성향을 판단하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **텍스트 기반 T/F 성향 분석**: 사용자의 답변을 분석하여 T/F 성향 점수 제공
- **실시간 감정 분석**: 키워드, 패턴, 어조를 종합적으로 분석
- **음성 인식 (STT)**: 음성 파일을 텍스트로 변환
- **음성 합성 (TTS)**: 텍스트를 음성으로 변환
- **AI 기반 질문 생성**: Gemini API를 활용한 동적 질문 생성
- **다중 질문 분석**: 1회, 3회, 5회 질문 지원
- **종합 분석 리포트**: 전체 결과를 바탕으로 한 상세 분석

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
│       ├── analysis.py     # 분석 관련
│       ├── questions.py    # 질문 관련
│       └── speech.py       # 음성 관련
├── config/                  # 설정 관리
│   └── settings.py         # 애플리케이션 설정
├── utils/                   # 유틸리티
│   └── helpers.py          # 헬퍼 함수들
├── static/                  # 프론트엔드
│   ├── html/               # HTML 파일들
│   ├── css/                # 스타일시트
│   ├── js/                 # 자바스크립트
│   └── images/             # 이미지 파일들
├── requirements.txt         # 의존성 패키지
└── README.md               # 프로젝트 문서
```

## 🛠️ 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Gemini AI API 키 (선택사항)
GEMINI_API_KEY=your_gemini_api_key_here

# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. 서버 실행

```bash
# 개발 모드
uvicorn mbti_analyzer.api.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn mbti_analyzer.api.main:app --host 0.0.0.0 --port 8000
```

### 4. 웹 브라우저에서 접속

```
http://localhost:8000
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 주요 API 엔드포인트

### 분석 관련
- `POST /api/v1/analyze`: 텍스트 T/F 성향 분석
- `POST /api/v1/final_analyze`: 종합 분석

### 질문 관련
- `POST /api/v1/generate_questions`: AI 질문 생성
- `GET /api/v1/questions`: 질문 조회

### 음성 관련
- `POST /api/v1/stt`: 음성 인식 (STT)
- `POST /api/v1/tts`: 음성 합성 (TTS)

## 🎯 사용 예시

### 텍스트 분석

```python
import requests

# 텍스트 분석 요청
response = requests.post("http://localhost:8000/api/v1/analyze", 
                        json={"text": "논리적으로 생각해보면 이 방법이 가장 효율적입니다."})

result = response.json()
print(f"T/F 점수: {result['score']}")
print(f"분석 결과: {result['detailed_analysis']}")
```

### AI 질문 생성

```python
# AI 질문 생성 요청
response = requests.post("http://localhost:8000/api/v1/generate_questions",
                        json={"count": 5, "difficulty": "medium"})

questions = response.json()
print("생성된 질문들:", questions['questions'])
```

## 🔒 보안 고려사항

- 입력 텍스트의 XSS 방지를 위한 sanitization 적용
- 파일 업로드 크기 제한 (10MB)
- 지원 오디오 형식 검증
- API 키는 환경변수로 관리

## 🚀 배포

### Docker를 사용한 배포

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

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 