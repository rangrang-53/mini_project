#!/usr/bin/env python3
"""
간단한 모듈 테스트

기본적인 모듈 임포트와 기능 테스트를 수행합니다.
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_basic_imports():
    """기본 임포트 테스트"""
    try:
        print("🔍 기본 임포트 테스트...")
        
        # 직접 임포트 테스트
        sys.path.insert(0, current_dir)
        
        # 코어 모듈 직접 테스트
        from core.analyzer import analyze_tf_tendency
        print("   ✅ 코어 분석기 임포트 성공")
        
        # 기능 테스트
        test_text = "논리적으로 생각해보면 이 방법이 가장 효율적입니다."
        score = analyze_tf_tendency(test_text)
        print(f"   ✅ T/F 분석 성공: 점수={score}")
        
        # 질문 생성 테스트
        from core.question_generator import generate_fallback_questions
        questions = generate_fallback_questions(2)
        print(f"   ✅ 질문 생성 성공: {len(questions)}개")
        
        print("\n🎉 기본 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    sys.exit(0 if success else 1) 