# MBTI T/F 분석기 서버 시작 스크립트 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MBTI T/F 분석기 서버 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Python 환경 확인
Write-Host "1. Python 환경 확인 중..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 오류: Python이 설치되지 않았습니다." -ForegroundColor Red
    Write-Host "Python을 설치한 후 다시 시도하세요." -ForegroundColor Red
    Read-Host "Enter를 눌러 종료"
    exit 1
}

Write-Host ""

# 2. 필요한 패키지 설치
Write-Host "2. 필요한 패키지 설치 중..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ 패키지 설치 완료" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 경고: 일부 패키지 설치에 실패했습니다." -ForegroundColor Yellow
    Write-Host "계속 진행합니다..." -ForegroundColor Yellow
}

Write-Host ""

# 3. api.py 파일 위치 확인
Write-Host "3. api.py 파일 위치 확인 중..." -ForegroundColor Yellow
$apiPath = $null

if (Test-Path "api.py") {
    Write-Host "✅ api.py를 루트 디렉토리에서 찾았습니다." -ForegroundColor Green
    $apiPath = "api.py"
} elseif (Test-Path "backend\api.py") {
    Write-Host "✅ api.py를 backend 디렉토리에서 찾았습니다." -ForegroundColor Green
    $apiPath = "backend\api.py"
} else {
    Write-Host "❌ api.py 파일을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "다음 위치를 확인해주세요:" -ForegroundColor Red
    Write-Host "  - 루트 디렉토리: api.py" -ForegroundColor Red
    Write-Host "  - backend 디렉토리: backend\api.py" -ForegroundColor Red
    Read-Host "Enter를 눌러 종료"
    exit 1
}

# 4. PYTHONPATH 설정
Write-Host ""
Write-Host "4. PYTHONPATH 설정 중..." -ForegroundColor Yellow
$env:PYTHONPATH = Get-Location
Write-Host "✅ PYTHONPATH 설정 완료: $env:PYTHONPATH" -ForegroundColor Green

# 5. 기존 프로세스 종료
Write-Host ""
Write-Host "5. 기존 프로세스 정리 중..." -ForegroundColor Yellow
try {
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ 기존 Python 프로세스 종료 완료" -ForegroundColor Green
} catch {
    Write-Host "ℹ️ 종료할 Python 프로세스가 없습니다." -ForegroundColor Blue
}

# 포트 8000 사용 중인 프로세스 종료
try {
    $portProcess = netstat -ano | Select-String ":8000" | ForEach-Object {
        ($_ -split '\s+')[4]
    }
    if ($portProcess) {
        Stop-Process -Id $portProcess -Force
        Write-Host "✅ 포트 8000 사용 프로세스 종료 완료" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️ 포트 8000을 사용하는 프로세스가 없습니다." -ForegroundColor Blue
}

# 6. 서버 시작
Write-Host ""
Write-Host "6. 서버 시작 중..." -ForegroundColor Yellow
Write-Host "서버 주소: http://localhost:8000" -ForegroundColor Cyan
Write-Host "브라우저에서 위 주소로 접속하세요." -ForegroundColor Cyan
Write-Host ""
Write-Host "서버를 중지하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ""

try {
    python $apiPath
} catch {
    Write-Host "❌ 서버 시작 중 오류가 발생했습니다: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "서버가 종료되었습니다." -ForegroundColor Yellow
Read-Host "Enter를 눌러 종료" 