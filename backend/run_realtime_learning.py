#!/usr/bin/env python3
"""
실시간 학습 시스템 실행 스크립트
매 순간 사용자 데이터가 입력될 때마다 자동으로 테스트 및 튜닝이 진행됩니다.
"""

import asyncio
import uvicorn
import sys
import os
from pathlib import Path

def main():
    """실시간 학습 시스템 실행"""
    print("🚀 MBTI T/F 분석기 - 실시간 학습 시스템 시작")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 작업 디렉토리: {current_dir}")
    
    # 필요한 파일들 확인
    required_files = [
        "api.py",
        "common.css",
        "index_with_learning.html"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 필요한 파일이 없습니다: {missing_files}")
        print("현재 디렉토리에 필요한 파일들을 확인해주세요.")
        return
    
    print("✅ 모든 필요한 파일이 확인되었습니다.")
    
    # 실시간 학습 시스템 정보
    print("\n📋 실시간 학습 시스템 기능:")
    print("   - 사용자 입력마다 자동 성능 평가")
    print("   - 성능 기준 미달 시 자동 프롬프트 튜닝")
    print("   - 학습 데이터베이스 자동 관리")
    print("   - 실시간 성능 모니터링")
    print("   - 사용자 피드백 수집 및 반영")
    
    print("\n🎯 학습 기준:")
    print("   - 최소 입력 수: 10개")
    print("   - 허용 오차 비율: 60% 이상")
    print("   - 자동 튜닝 조건: 허용 비율 60% 미만")
    
    print("\n🌐 웹 인터페이스:")
    print("   - 메인 페이지: http://localhost:8001/index_with_learning.html")
    print("   - API 상태: http://localhost:8001/api/v1/learning/status")
    print("   - 학습 히스토리: http://localhost:8001/api/v1/learning/history")
    
    print("\n⚙️  API 엔드포인트:")
    print("   - 분석: POST /api/v1/analyze")
    print("   - 학습 피드백: POST /api/v1/learning/feedback")
    print("   - 학습 상태: GET /api/v1/learning/status")
    print("   - 학습 토글: POST /api/v1/learning/toggle")
    print("   - 학습 히스토리: GET /api/v1/learning/history")
    
    print("\n💡 사용 방법:")
    print("   1. 웹 브라우저에서 http://localhost:8001/index_with_learning.html 접속")
    print("   2. 텍스트를 입력하고 분석 수행")
    print("   3. 분석 결과에 대한 피드백 제출 (예상 점수 입력)")
    print("   4. 시스템이 자동으로 학습하여 성능 개선")
    print("   5. 실시간 학습 상태 및 히스토리 확인")
    
    print("\n🔧 시스템 설정:")
    print("   - 데이터베이스: learning_data.db (자동 생성)")
    print("   - 프롬프트 버전 관리: 자동 버전 업데이트")
    print("   - 성능 모니터링: 실시간 대시보드")
    
    print("\n" + "=" * 60)
    print("🚀 서버를 시작합니다...")
    print("Ctrl+C를 눌러 서버를 중지할 수 있습니다.")
    print("=" * 60)
    
    try:
        # uvicorn 서버 시작
        uvicorn.run(
            "api:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
        print("실시간 학습 시스템을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류가 발생했습니다: {e}")
        print("API 파일과 의존성을 확인해주세요.")

if __name__ == "__main__":
    main() 