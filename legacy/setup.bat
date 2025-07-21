@echo off
echo ========================================
echo MBTI Analyzer 프로젝트 초기 설정
echo ========================================
echo.

echo 1. Python 가상환경 확인...
python --version

echo.
echo 2. 필요한 패키지 설치 중...
pip install -r requirements.txt
pip install groq google-cloud-texttospeech

echo.
echo 3. 설정 완료!
echo 이제 run_server.bat 또는 start.bat를 실행하세요.
echo.

pause 