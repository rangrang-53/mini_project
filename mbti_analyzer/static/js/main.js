// API 기본 URL 설정
const API_BASE_URL = 'http://localhost:8000';

// 모달 함수들
function showAlertModal(message) {
    const modal = document.getElementById('alert_modal');
    const messageElement = document.getElementById('alert_message');
    
    if (modal && messageElement) {
        messageElement.textContent = message;
        modal.style.display = 'flex';
    }
}

function hideAlertModal() {
    const modal = document.getElementById('alert_modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
        
// 전역 변수
let currentCount = 0;
let maxCount = 0;
let results = [];
let usedQuestions = new Set(); // 사용된 질문들을 추적
let currentQuestionIndex = 0;
let questions = [];
let answers = [];
let totalQuestions = 0;

// DOM 로드 완료 후 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('start_button');
    
    // 시작 버튼 클릭 함수
    function handleStart() {
        // 체크박스 선택 여부 확인
        const countCheckboxes = document.querySelectorAll('input[name="question_count"]:checked');
        const typeCheckboxes = document.querySelectorAll('input[name="meme"]:checked, input[name="aiSettings"]:checked');
        
        if (countCheckboxes.length === 0) {
            showAlertModal('문제 개수를 선택해주세요!');
            return;
        }
        
        if (typeCheckboxes.length === 0) {
            showAlertModal('문제 타입을 선택해주세요!');
            return;
        }
        
        // 선택된 문제 개수 값 가져오기
        const selectedCount = parseInt(countCheckboxes[0].value);
        
        // 선택된 문제 타입 확인
        const selectedType = typeCheckboxes[0].name; // 'meme' 또는 'aiSettings'
        
        maxCount = selectedCount;
        currentCount = 0;
        results = [];
        usedQuestions.clear();
        
        // question.html로 이동 (선택된 개수와 타입을 URL 파라미터로 전달)
        window.location.href = `/question?count=${selectedCount}&type=${selectedType}`;
    }
    
    // 클릭 이벤트
    if (startButton) {
        startButton.addEventListener('click', handleStart);
    }
    
    // Enter 키 이벤트
    document.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            handleStart();
        }
    });

    // 체크박스 단일 선택 로직 - 문제 개수
    const countCheckboxes = document.querySelectorAll('input[name="question_count"]');
    countCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                countCheckboxes.forEach(cb => {
                    if (cb !== this) cb.checked = false;
                });
            }
        });
    });

    // 체크박스 단일 선택 로직 - 문제 타입
    const typeCheckboxes = document.querySelectorAll('input[name="meme"], input[name="aiSettings"]');
    typeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                typeCheckboxes.forEach(cb => {
                    if (cb !== this) cb.checked = false;
                });
            }
        });
    });

    // AI 설정 표시/숨김 토글 (향후 AI 설정 기능 추가 시 사용)
    function toggleAISettings() {
        const aiCheckbox = document.querySelector('input[name="aiSettings"]');
        const aiSettingsDiv = document.getElementById('aiSettings');
        
        if (aiSettingsDiv) {
            if (aiCheckbox && aiCheckbox.checked) {
                aiSettingsDiv.style.display = 'block';
            } else {
                aiSettingsDiv.style.display = 'none';
            }
        }
    }

    // AI 설정 체크박스에 이벤트 리스너 추가
    const aiCheckbox = document.querySelector('input[name="aiSettings"]');
    if (aiCheckbox) {
        aiCheckbox.addEventListener('change', toggleAISettings);
    }

    // 모달 백그라운드 클릭 시 닫기
    const alertModal = document.getElementById('alert_modal');
    if (alertModal) {
        alertModal.addEventListener('click', function(event) {
            if (event.target === alertModal) {
                hideAlertModal();
            }
        });
    }

    var sampleBtn = document.getElementById('sample_review_btn');
    var sampleModal = document.getElementById('sample_review_modal');
    if (sampleBtn && sampleModal) {
        sampleBtn.addEventListener('click', function() {
            sampleModal.style.display = 'flex';
        });
    }

    // 리뷰모달 샘플 스피커(TTS) 버튼 기능
    var ttsBtn = document.getElementById('sample_review_tts');
    if (ttsBtn) {
        ttsBtn.addEventListener('click', async function() {
            // 실천팁/대안답변 텍스트 추출 (정적 샘플)
            var tip = '감정을 솔직하게 표현해보는 연습을 해보세요.';
            var alt = '가끔은 내 생각을 말로 표현하는 게 어려워.';
            var ttsText = '실천팁: ' + tip + ' 대안답변: ' + alt;
            try {
                const response = await fetch('/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: ttsText, lang: 'ko-KR' })
                });
                if (!response.ok) throw new Error('TTS 변환 실패');
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                audio.play();
            } catch (e) {
                alert('음성 변환에 실패했습니다.');
            }
        });
    }
});

// 질문 페이지 표시
function showQuestionPage() {
    // 질문 페이지 HTML 생성
    const questionPageHTML = `
        <div id="question_page" style="display: block;">
            <div id="character">
                <div id="characterFace" class="face face-neutral"></div>
            </div>
            <div id="question_container">
                <div id="question">질문을 로드하는 중...</div>
                <div id="answer_container">
                    <input type="text" id="answerInput" placeholder="답변을 입력하세요...">
                    <button id="submitButton" class="submit-button">제출</button>
                    <button id="nextButton" style="display: none;">다음</button>
                </div>
                <div id="resultGraph" style="display: none;"></div>
                <div id="reviewIcon" style="display: none;"></div>
            </div>
        </div>
    `;
    
    // 메인 컨테이너에 질문 페이지 추가
    const main = document.querySelector('main');
    main.innerHTML = questionPageHTML;
    
    // 이벤트 리스너 추가
    document.getElementById('submitButton').addEventListener('click', submitAnswer);
    document.getElementById('nextButton').addEventListener('click', nextQuestion);
    document.getElementById('answerInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            submitAnswer();
        }
    });
    
    // 질문 데이터 로드
    loadQuestions();
}

// 질문 데이터 로드
async function loadQuestions() {
    try {
        const url = `${API_BASE_URL}/questions?count=5`;
        
        const response = await fetch(url);
        console.log('서버 응답:', response);
        const data = await response.json();
        console.log('받은 데이터:', data);
        questions = data.questions;
        totalQuestions = questions.length;
        
        console.log(`질문 로드 완료: ${data.source} 소스에서 ${questions.length}개 질문`);
        
        showNextQuestion();
    } catch (error) {
        console.error('질문을 불러오는데 실패했습니다:', error);
        document.getElementById('question').textContent = '질문을 불러오는데 실패했습니다. 서버가 실행 중인지 확인해주세요.';
    }
}

// 랜덤 질문 선택
function getRandomQuestion() {
    const availableQuestions = questions.filter((_, index) => !usedQuestions.has(index));
    if (availableQuestions.length === 0) {
        usedQuestions.clear();
        return questions[Math.floor(Math.random() * questions.length)];
    }
    const randomIndex = Math.floor(Math.random() * availableQuestions.length);
    const questionIndex = questions.findIndex(q => q === availableQuestions[randomIndex]);
    usedQuestions.add(questionIndex);
    return availableQuestions[randomIndex];
}

// AI 질문 생성 기능 (현재 사용하지 않음)
// async function generateNewQuestions() {
//     const difficulty = 'medium'; // 기본값
//     const count = 5; // 기본값
//     
//     try {
//         const response = await fetch(`${API_BASE_URL}/generate_questions`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({
//                 count: count,
//                 difficulty: difficulty
//             })
//         });
//         
//         if (!response.ok) {
//             throw new Error('AI 질문 생성 실패');
//         }
//         
//         const data = await response.json();
//         questions = data.questions;
//         
//         showAlertModal(`새로운 ${difficulty} 난이도의 ${count}개 질문이 생성되었습니다!`);
//         
//     } catch (error) {
//         console.error('Error generating questions:', error);
//         showAlertModal('AI 질문 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
//     }
// }

// 다음 질문 표시
function showNextQuestion() {
    if (currentCount >= maxCount) {
        showFinalResult();
        return;
    }

    const question = getRandomQuestion();
    document.getElementById('question').textContent = question;
    document.getElementById('answerInput').value = '';
    document.getElementById('answerInput').disabled = false;
    document.getElementById('resultGraph').style.display = 'none';
    document.getElementById('reviewIcon').style.display = 'none';
    
    // 버튼 상태 초기화
    document.getElementById('submitButton').disabled = false;
    document.getElementById('submitButton').style.opacity = '1';
    document.getElementById('nextButton').style.display = 'none';
}

// 답변 제출
async function submitAnswer() {
    const answer = document.getElementById('answerInput').value.trim();
    if (!answer) {
        showAlertModal('답변을 입력해주세요.');
        return;
    }

    try {
        // API 호출
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: answer })
        });

        if (!response.ok) {
            throw new Error('API 호출 실패');
        }

        const data = await response.json();
        
        results.push({
            question: document.getElementById('question').textContent,
            answer: answer,
            score: data.score
        });

        showResult(data.score);
        currentCount++;
    } catch (error) {
        console.error('Error:', error);
        showAlertModal('분석 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
}

// 결과 표시
function showResult(score) {
    // 결과 그래프 표시
    const resultGraph = document.getElementById('resultGraph');
    resultGraph.innerHTML = `
        <div style="margin-top: 20px;">
            <div>T/F 성향 점수: ${score.toFixed(1)}</div>
            <div style="background: #eee; height: 20px; width: 100%; margin-top: 10px;">
                <div style="background: #4CAF50; height: 100%; width: ${score}%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                <span>T형</span>
                <span>F형</span>
            </div>
        </div>
    `;
    resultGraph.style.display = 'block';
    
    updateCharacterExpression(score);
    
    // 입력 필드와 버튼 상태 업데이트
    document.getElementById('answerInput').disabled = true;
    document.getElementById('submitButton').style.display = 'none';
    document.getElementById('nextButton').style.display = 'inline-block';
}

// 다음 질문으로 이동
function nextQuestion() {
    if (currentCount >= maxCount) {
        showFinalResult();
        return;
    }

    // 입력 필드 초기화
    document.getElementById('answerInput').value = '';
    document.getElementById('answerInput').disabled = false;
    document.getElementById('resultGraph').style.display = 'none';
    document.getElementById('submitButton').disabled = false;
    document.getElementById('submitButton').style.opacity = '1';
    document.getElementById('submitButton').style.display = 'inline-block';
    document.getElementById('nextButton').style.display = 'none';
    
    // 리뷰 아이콘 숨기기
    document.getElementById('reviewIcon').style.display = 'none';
    
    showNextQuestion();
}

// 최종 결과 표시
function showFinalResult() {
    const averageScore = results.reduce((sum, result) => sum + result.score, 0) / results.length;
    
    const finalResultHTML = `
        <div id="final_result">
            <h2>모든 질문이 완료되었습니다!</h2>
            <div class="final-score">
                <h3>최종 T/F 성향 점수: ${averageScore.toFixed(1)}</h3>
                <div style="background: #eee; height: 30px; width: 100%; margin: 20px 0;">
                    <div style="background: #4CAF50; height: 100%; width: ${averageScore}%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>T형 (논리적)</span>
                    <span>F형 (감정적)</span>
                </div>
            </div>
            <div class="final-results">
                <h3>당신의 답변 기록:</h3>
                ${results.map((result, index) => `
                    <div class="answer-record">
                        <p><strong>Q${index + 1}:</strong> ${result.question}</p>
                        <p><strong>A:</strong> ${result.answer}</p>
                        <p><strong>점수:</strong> ${result.score.toFixed(1)}</p>
                    </div>
                `).join('')}
            </div>
            <button onclick="location.reload()" class="start-button">다시 시작하기</button>
        </div>
    `;
    
    document.querySelector('main').innerHTML = finalResultHTML;
}

// 캐릭터 초기화
function initCharacter() {
    const character = document.getElementById('characterFace');
    if (character) {
        character.className = 'face face-neutral';
    }
}

// 표정 변경
function updateCharacterExpression(score) {
    const face = document.getElementById('characterFace');
    if (face) {
        face.className = 'face'; // 기존 클래스 제거

        if (score < 20) {
            face.classList.add('face-very-angry');
        } else if (score < 40) {
            face.classList.add('face-angry');
        } else if (score < 60) {
            face.classList.add('face-neutral');
        } else if (score < 80) {
            face.classList.add('face-happy');
        } else {
            face.classList.add('face-very-happy');
        }
    }
}