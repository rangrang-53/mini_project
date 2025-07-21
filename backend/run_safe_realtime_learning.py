#!/usr/bin/env python3
"""
안전장치가 포함된 실시간 학습 시스템 실행 스크립트
- 1주일 단위 프롬프트 백업
- 성능 모니터링 및 롤백 기능
- 사용자 평가 기반 안전장치
"""

import asyncio
import uvicorn
import sys
import os
from pathlib import Path

def main():
    """안전장치가 포함된 실시간 학습 시스템 실행"""
    print("🛡️ MBTI T/F 분석기 - 안전한 실시간 학습 시스템 시작")
    print("=" * 70)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 작업 디렉토리: {current_dir}")
    
    # 필요한 파일들 확인
    required_files = [
        "api.py",
        "common.css",
        "safe_index_with_learning.html"
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
    
    # 안전장치 정보
    print("\n🛡️ 안전장치 기능:")
    print("   - 1주일 단위 자동 백업")
    print("   - 실시간 성능 모니터링")
    print("   - 자동 롤백 기능")
    print("   - 위험도 평가 시스템")
    print("   - 성능 트렌드 분석")
    
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
    print("   - 롤백 조건: 성능 10% 이상 저하")
    
    print("\n🛡️ 안전장치 기준:")
    print("   - 백업 주기: 1주일")
    print("   - 위험도 계산: 오차율, 트렌드, 백업 지연")
    print("   - 자동 롤백: 15% 이상 성능 저하 시")
    print("   - 수동 롤백: 높은 위험도 시 사용자 확인")
    
    print("\n🌐 웹 인터페이스:")
    print("   - 메인 페이지: http://localhost:8000/safe_index_with_learning.html")
    print("   - API 상태: http://localhost:8000/api/v1/learning/status")
    print("   - 안전성 지표: http://localhost:8000/api/v1/safety/metrics")
    print("   - 백업 목록: http://localhost:8000/api/v1/safety/backups")
    
    print("\n⚙️  API 엔드포인트:")
    print("   - 분석: POST /api/v1/analyze")
    print("   - 안전 분석: POST /api/v1/analyze_with_safety")
    print("   - 학습 피드백: POST /api/v1/learning/feedback")
    print("   - 학습 상태: GET /api/v1/learning/status")
    print("   - 안전성 지표: GET /api/v1/safety/metrics")
    print("   - 롤백 수행: POST /api/v1/safety/rollback")
    print("   - 백업 생성: POST /api/v1/safety/backup")
    
    print("\n💡 사용 방법:")
    print("   1. 웹 브라우저에서 http://localhost:8000/safe_index_with_learning.html 접속")
    print("   2. 텍스트를 입력하고 분석 수행")
    print("   3. 분석 결과에 대한 피드백 제출 (예상 점수 입력)")
    print("   4. 시스템이 자동으로 학습하여 성능 개선")
    print("   5. 안전성 지표 및 백업 정보 확인")
    print("   6. 필요시 롤백 기능 사용")
    
    print("\n🔧 시스템 설정:")
    print("   - 데이터베이스: safe_learning_data.db (자동 생성)")
    print("   - 백업 디렉토리: prompt_backups/ (자동 생성)")
    print("   - 프롬프트 버전 관리: 자동 버전 업데이트")
    print("   - 성능 모니터링: 실시간 대시보드")
    print("   - 안전성 검사: 30초마다 자동 실행")
    
    print("\n⚠️  주의사항:")
    print("   - 정확한 예상 점수 입력이 중요합니다")
    print("   - 높은 위험도 시 자동 롤백이 실행될 수 있습니다")
    print("   - 백업은 1주일마다 자동으로 생성됩니다")
    print("   - 성능 저하 시 수동 롤백을 고려하세요")
    
    print("\n🛡️ 안전장치 작동 방식:")
    print("   1. 실시간 성능 모니터링")
    print("   2. 백업과 현재 성능 비교")
    print("   3. 위험도 계산 (오차율, 트렌드, 백업 지연)")
    print("   4. 높은 위험도 시 자동 롤백 고려")
    print("   5. 사용자에게 위험도 알림")
    
    print("\n📊 성능 지표:")
    print("   - 현재 오차율 vs 백업 오차율")
    print("   - 성능 트렌드 (개선/안정/저하)")
    print("   - 백업 경과일")
    print("   - 위험도 레벨 (낮음/중간/높음)")
    
    print("\n" + "=" * 70)
    print("🚀 안전한 실시간 학습 시스템을 시작합니다...")
    print("Ctrl+C를 눌러 서버를 중지할 수 있습니다.")
    print("=" * 70)
    
    try:
        # uvicorn 서버 시작
        uvicorn.run(
            "api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
        print("안전한 실시간 학습 시스템을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 중 오류가 발생했습니다: {e}")
        print("API 파일과 의존성을 확인해주세요.")

if __name__ == "__main__":
    main() 