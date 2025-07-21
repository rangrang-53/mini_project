@echo off
echo MBTI Analyzer 서버 시작...
echo http://localhost:8000
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload 