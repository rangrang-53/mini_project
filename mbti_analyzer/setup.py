"""
MBTI T/F 성향 분석기 패키지 설정

이 파일은 모듈화된 MBTI 분석기를 패키지로 설치하기 위한 설정입니다.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mbti-analyzer",
    version="1.0.0",
    author="MBTI Analyzer Team",
    author_email="team@mbti-analyzer.com",
    description="MBTI T/F 성향 분석기",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/mbti-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mbti-analyzer=mbti_analyzer.run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mbti_analyzer": ["static/**/*", "*.md", "*.txt"],
    },
) 