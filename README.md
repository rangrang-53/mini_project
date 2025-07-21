# MBTI T/F 분석기 - AI 기반 성향 분석 시스템

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## 📋 프로젝트 개요

MBTI의 Thinking/Feeling 성향을 AI 기반으로 분석하는 웹 애플리케이션입니다. 사용자의 답변을 분석하여 T/F 성향을 점수화하고, 상세한 분석 결과와 개선 제안을 제공합니다.

### 🌟 주요 특징

- **🤖 AI 기반 분석**: Gemini AI와 Groq AI를 활용한 정확한 성향 분석
- **🎤 음성 인식**: STT(Speech-to-Text) 기능으로 음성 입력 지원
- **🔊 음성 합성**: TTS(Text-to-Speech) 기능으로 결과 음성 출력
- **📚 고정 질문 시스템**: 50개의 검증된 질문으로 안정적인 분석
- **🔄 실시간 학습**: 사용자 피드백을 통한 시스템 성능 자동 개선
- **🛡️ 안전장치**: 자동 백업 및 롤백 기능으로 시스템 안정성 보장
- **📱 반응형 디자인**: 모든 디바이스에서 최적화된 사용자 경험

## 🚀 빠른 시작

### 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Windows 10/11 (권장)
- **메모리**: 최소 4GB RAM
- **인터넷**: AI 모델 사용을 위한 연결 필요

### 설치 및 실행

#### 1. 저장소 클론
```bash
git clone [repository-url]
cd minipjt01
```

#### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 3. 서버 실행

**방법 1: PowerShell 스크립트 (권장)**
```powershell
.\run_server.ps1
```

**방법 2: 수동 실행**
```bash
python backend/api.py
```

#### 4. 브라우저에서 접속
```
http://localhost:8000
```

## 📁 프로젝트 구조

```
minipjt01/
├── 📄 index1.html              # 메인 페이지
├── 📄 index2.html              # 질문 페이지 (음성인식 포함)
├── 📄 index3.html              # 결과 페이지
├── 📁 backend/                 # 백엔드 서버
│   ├── 📄 api.py              # 메인 API 서버
│   ├── 📄 safe_api_endpoints.py # 안전장치 포함 API
│   ├── 📄 realtime_learning_system.py # 실시간 학습 시스템
│   └── 📄 learning_data.db    # 학습 데이터베이스
├── 📁 mbti_analyzer/          # 핵심 분석 모듈
│   ├── 📁 core/               # 분석 엔진
│   ├── 📁 modules/            # STT/TTS 모듈
│   └── 📁 api/                # API 라우터
├── 📁 docs/                   # 문서
│   ├── 📄 고정질문시스템_사용법.md
│   ├── 📄 실시간학습시스템_사용법.md
│   └── 📄 안전장치_사용법.md
├── 📁 question/               # 질문 데이터
├── 📁 static/                 # 정적 파일
└── 📄 requirements.txt        # Python 의존성
```

## 🔧 주요 기능

### 1. AI 기반 성향 분석
- **Gemini AI**: 1순위 분석 엔진
- **Groq AI**: 2순위 백업 엔진
- **정확도**: 10% 허용 오차 내 분석
- **응답 시간**: 평균 2-3초

### 2. 고정 질문 시스템
- **총 질문 수**: 50개
- **카테고리**: 8개 (일상, 직장, 감정, 갈등 등)
- **난이도**: Easy, Medium, Hard
- **장점**: 안정성, 빠른 응답, 일관된 품질

### 3. 음성 인식 (STT)
- **지원 형식**: WebM, MP4, WAV
- **음성 품질**: 8kHz, 모노
- **브라우저**: Chrome, Firefox, Safari 지원
- **모바일**: iOS, Android 지원

### 4. 음성 합성 (TTS)
- **엔진**: Google TTS
- **언어**: 한국어
- **품질**: 자연스러운 발음
- **용도**: 분석 결과 음성 출력

### 5. 실시간 학습 시스템
- **자동 튜닝**: 성능 기준 미달 시 자동 개선
- **피드백 수집**: 사용자 예상 점수와 실제 점수 비교
- **성능 모니터링**: 실시간 지표 확인
- **데이터베이스**: SQLite 기반 학습 데이터 저장

### 6. 안전장치 시스템
- **자동 백업**: 1주일 단위 백업
- **롤백 기능**: 성능 저하 시 이전 버전으로 복원
- **위험도 평가**: 실시간 시스템 상태 모니터링
- **성능 지표**: 오차율, 허용 비율, 트렌드 분석

## 📊 분석 결과

### 점수 체계
- **0-20**: 확실한 T 성향
- **21-40**: T 성향이 강함
- **41-59**: T/F 균형
- **60-79**: F 성향이 강함
- **80-100**: 확실한 F 성향

### 제공 정보
- **T/F 점수**: 0-100 점수
- **상세 분석**: 답변에 대한 구체적인 분석
- **분석 근거**: 점수 산정 근거 설명
- **개선 제안**: F 성향을 위한 대안 답변
- **시각화**: 그래프와 이모지로 직관적 표현

## 🛡️ 안전 기능

### 자동 백업 시스템
- **주기**: 1주일 단위
- **저장소**: 로컬 데이터베이스
- **복원**: 언제든지 이전 버전으로 롤백 가능

### 실시간 모니터링
- **성능 지표**: 오차율, 허용 비율, 트렌드
- **위험도 평가**: Low, Medium, High
- **자동 알림**: 성능 저하 시 경고

### 롤백 시스템
- **조건**: 현재 오차율이 백업 대비 10% 이상 증가
- **방법**: 웹 인터페이스에서 원클릭 롤백
- **안전성**: 데이터 손실 없이 안전한 복원

## 📱 사용자 인터페이스

### 반응형 디자인
- **데스크톱**: 1200px 이상 최적화
- **태블릿**: 768px-1199px 최적화
- **모바일**: 320px-767px 최적화
- **세로 화면**: iPhone 12 Pro 등 특정 기기 최적화

### 접근성
- **키보드 네비게이션**: Tab 키로 모든 요소 접근 가능
- **스크린 리더**: ARIA 라벨 및 시맨틱 HTML
- **고대비**: 색상 대비 WCAG 2.1 AA 준수
- **터치 친화적**: 44px 최소 터치 영역

## 🔧 API 문서

### 분석 API
```http
POST /api/v1/analyze
Content-Type: application/json

{
  "text": "분석할 텍스트"
}
```

### 질문 API
```http
GET /api/v1/questions?count=5&difficulty=medium&category=직장/팀워크
```

### 음성 인식 API
```http
POST /api/v1/stt
Content-Type: multipart/form-data

audio_file: [음성 파일]
```

### 음성 합성 API
```http
POST /api/v1/tts
Content-Type: application/json

{
  "text": "음성으로 변환할 텍스트"
}
```

### 학습 피드백 API
```http
POST /api/v1/learning/feedback
Content-Type: application/json

{
  "question": "질문",
  "answer": "답변",
  "expected_score": 65,
  "actual_score": 70
}
```

## 🛠️ 개발 가이드

### 환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 서버 실행 옵션
```bash
# 개발 모드 (자동 재시작)
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 데이터베이스 관리
```bash
# 학습 데이터 확인
sqlite3 backend/learning_data.db ".tables"

# 백업 생성
cp backend/learning_data.db backup_$(date +%Y%m%d).db
```

## 📈 성능 지표

### 시스템 성능
- **응답 시간**: 평균 2-3초
- **동시 사용자**: 100명까지 안정적 처리
- **메모리 사용량**: 평균 500MB
- **CPU 사용률**: 평균 30%

### 분석 정확도
- **전체 정확도**: 85% 이상
- **허용 오차**: 10% 이내
- **학습 효과**: 사용자 피드백 후 5-10% 정확도 향상

## 🔍 문제 해결

### 일반적인 문제

#### 서버가 시작되지 않는 경우
```bash
# 1. 포트 확인
netstat -an | findstr :8000

# 2. 기존 프로세스 종료
taskkill /F /IM python.exe

# 3. 다시 시작
python backend/api.py
```

#### 음성 인식이 작동하지 않는 경우
1. 브라우저에서 마이크 권한 허용
2. HTTPS 환경에서 테스트 (로컬에서는 HTTP도 가능)
3. 브라우저 업데이트 확인

#### AI 분석이 느린 경우
1. 인터넷 연결 상태 확인
2. AI 서비스 상태 확인
3. 서버 재시작

### 로그 확인
```bash
# 실시간 로그 확인
tail -f debug.log

# 에러 로그 필터링
grep "ERROR" debug.log
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

- **이슈 리포트**: GitHub Issues
- **문서**: `/docs` 폴더 참조
- **이메일**: [your-email@example.com]

## 🔄 업데이트 로그

### v2.0 (2024-07-20)
- ✅ 고정 질문 시스템 도입
- ✅ 실시간 학습 시스템 개선
- ✅ 안전장치 시스템 강화
- ✅ 음성 인식/합성 기능 추가
- ✅ 반응형 디자인 완전 개선
- ✅ 불필요한 테스트 파일 정리

### v1.5 (2024-07-15)
- ✅ AI 모델 통합 (Gemini + Groq)
- ✅ 기본 분석 기능 구현
- ✅ 웹 인터페이스 구축

---

**MBTI T/F 분석기** - AI로 더 정확하고 개인화된 성향 분석을 경험하세요! 🚀 