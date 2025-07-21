import os
import sys

try:
    from transformers import pipeline
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'transformers'])
    from transformers import pipeline

# 사전 학습된 요약 모델 로드 (최초 1회)
summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

def summarize_text(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """
    입력된 텍스트를 요약하여 반환합니다.
    """
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

# 사용 예시
if __name__ == "__main__":
    sample_text = """
    인공지능(AI)은 컴퓨터 시스템이 인간과 유사한 지능을 갖추도록 하는 기술입니다. AI는 머신러닝, 딥러닝, 자연어 처리 등 다양한 분야에서 활용되며, 최근에는 챗봇, 자율주행, 의료 진단 등 실생활에 널리 적용되고 있습니다. 앞으로 AI 기술의 발전은 우리의 삶을 더욱 편리하고 풍요롭게 만들어줄 것으로 기대됩니다.
    """
    print("요약 결과:", summarize_text(sample_text)) 