// exam_app.js
document.addEventListener('DOMContentLoaded', function() {
    // 使用从HTML传递的全局变量
    const examId = EXAM_ID;
    const scoreId = SCORE_ID;
    let currentQuestionId = null;
    const examQuestions = EXAM_QUESTIONS;
    const csrfToken = CSRF_TOKEN;

    // 题目状态跟踪
    const questionStatus = {};

    // 初始化页面
    initializePage();

    // 显示剩余时间
    updateRemainingTime(REMAINING_SECONDS);

    // 加载第一道题
    if(examQuestions.length > 0) {
        loadQuestion(examQuestions[0].id);
    }

    // 题目导航点击事件
    document.querySelectorAll('.question-nav-btn').forEach(button => {
        button.addEventListener('click', function() {
            const questionId = parseInt(this.getAttribute('data-question-id'));
            loadQuestion(questionId);
        });
    });

    // 上一题按钮点击事件
    document.getElementById('prev-question-btn').addEventListener('click', function() {
        if(currentQuestionId) {
            const currentIndex = examQuestions.findIndex(q => q.id === currentQuestionId);
            if(currentIndex > 0) {
                loadQuestion(examQuestions[currentIndex - 1].id);
            }
        }
    });

    // 下一题按钮点击事件
    document.getElementById('next-question-btn').addEventListener('click', function() {
        if(currentQuestionId) {
            const currentIndex = examQuestions.findIndex(q => q.id === currentQuestionId);
            if(currentIndex < examQuestions.length - 1) {
                loadQuestion(examQuestions[currentIndex + 1].id);
            }
        }
    });

    // 保存答案按钮点击事件
    document.getElementById('save-answer-btn').addEventListener('click', function() {
        saveAnswer();
    });

    // 初始化页面函数
    function initializePage() {
        // 初始化题目状态
        examQuestions.forEach(question => {
            questionStatus[question.id] = false;
        });

        // 初始化自动保存
        setupAutoSave();

        // 全局保存按钮
        const globalSaveButton = document.getElementById('global-save-button');
        if (globalSaveButton) {
            globalSaveButton.addEventListener('click', function() {
                // 直接内联保存逻辑
                if (currentQuestionId) {
                    saveAnswer();

                    // 更新保存状态
                    const saveStatus = document.getElementById('save-status');
                    if (saveStatus) {
                        saveStatus.textContent = '已保存所有答案';
                        saveStatus.style.display = 'inline';
                        setTimeout(() => {
                            saveStatus.style.display = 'none';
                        }, 3000);
                    }

                    // 更新全局保存状态
                    const lastSaveTime = document.getElementById('last-save-time');
                    if (lastSaveTime) {
                        const now = new Date();
                        lastSaveTime.textContent = '上次保存: ' + now.toLocaleTimeString();
                    }
                } else {
                    alert('请先选择一道题目！');
                }
            });
        }
    }

    // 加载题目函数
    function loadQuestion(questionId) {
        // 保存当前题目答案（如果有）
        if (currentQuestionId) {
            // 根据当前题目类型决定如何保存
            const questionTypeElement = document.getElementById('question-type-badge');
            if (questionTypeElement) {
                const questionType = questionTypeElement.textContent.trim();

                if (questionType === '选择题') {
                    saveChoiceAnswer();
                } else {
                    saveAnswer();
                }
            }
        }


        // 发起请求获取题目详情
        fetch(`/exams/student/get_question/${examId}/${questionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if(data.error) {
                    alert(data.message);
                    return;
                }

                displayQuestion(data);
                currentQuestionId = questionId;
                updateNavigationButtons();
            })
            .catch(error => {
                console.error('获取题目失败:', error);
                alert('获取题目失败，请刷新页面重试');
            });
    }

    // 显示题目函数
    function displayQuestion(question) {
        // 更新题目标题和标签
        document.getElementById('question-title').textContent = `题目 ${getQuestionOrderById(question.id)}`;

        const typeText = getQuestionTypeText(question.question_type);
        document.getElementById('question-type-badge').textContent = typeText;
        document.getElementById('question-score-badge').textContent = `${question.score} 分`;

        // 更新题目内容
        const contentContainer = document.getElementById('question-content-container');
        contentContainer.innerHTML = `
            <h5>${question.title}</h5>
            <div class="question-content">${question.content}</div>
        `;

        // 高亮当前题目导航按钮
        document.querySelectorAll('.question-nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const navBtn = document.getElementById(`nav-question-${question.id}`);
        if(navBtn) {
            navBtn.classList.add('active');
        }

        // 根据题目类型显示不同的答题区域
        if(question.question_type === 'choice') {
            displayChoiceQuestion(question);
        } else {
            displayTextQuestion(question);
        }

        // 填充已保存的答案（如果有）
        if(question.saved_answer) {
            fillSavedAnswer(question);
        }

        // 设置表单字段
        document.getElementById('question_id').value = question.id;
    }

    // 显示选择题函数
    function displayChoiceQuestion(question) {
        document.getElementById('options-container').style.display = 'block';
        document.getElementById('answer-container').style.display = 'none';

        const optionsList = document.getElementById('options-list');
        optionsList.innerHTML = '';

        if(question.options && question.options.length > 0) {
            question.options.forEach(option => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'form-check mb-2';

                const input = document.createElement('input');
                input.type = 'checkbox';
                input.className = 'form-check-input option-checkbox';
                input.id = `option-${option.id}`;
                input.name = 'selected_options';
                input.value = option.id;
                input.dataset.questionId = question.id;
                input.addEventListener('change', function() {
                    saveChoiceAnswer();
                });

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `option-${option.id}`;
                label.innerHTML = option.content;

                optionDiv.appendChild(input);
                optionDiv.appendChild(label);
                optionsList.appendChild(optionDiv);
            });
        } else {
            optionsList.innerHTML = '<p class="text-danger">此题选项加载失败</p>';
        }
    }

    // 显示填空题或编程题函数
    function displayTextQuestion(question) {
        document.getElementById('options-container').style.display = 'none';
        document.getElementById('answer-container').style.display = 'block';

        const textarea = document.getElementById('answer_content');
        textarea.value = '';

        // 显示保存按钮
        document.getElementById('save-answer-btn').style.display = 'block';
        document.getElementById('save-status').style.display = 'none';
    }

    // 填充已保存的答案
    function fillSavedAnswer(question) {
        if(question.question_type === 'choice') {
            try {
                const selectedOptions = JSON.parse(question.saved_answer);
                selectedOptions.forEach(optionId => {
                    const checkbox = document.getElementById(`option-${optionId}`);
                    if(checkbox) {
                        checkbox.checked = true;
                    }
                });
            } catch(e) {
                console.error('解析已保存的选择题答案失败:', e);
            }
        } else {
            // 对于填空题和编程题
            const textarea = document.getElementById('answer_content');
            if (question.saved_answer && question.saved_answer.trim() !== '') {
                // 如果有已保存的答案，使用它
                textarea.value = question.saved_answer;
            }

        }
    }

    // 保存选择题答案
    function saveChoiceAnswer() {
        const selectedOptions = [];
        document.querySelectorAll('.option-checkbox:checked').forEach(checkbox => {
            selectedOptions.push(parseInt(checkbox.value));
        });

        const questionId = currentQuestionId;
        // 确保转换为JSON字符串
        const answerContent = JSON.stringify(selectedOptions);

        // 增加日志检查数据
        console.log('选择题答案数据:', {
            selectedOptions: selectedOptions,
            answerContent: answerContent
        });

        saveAnswerToServer(questionId, answerContent);
    }

    // 填充已保存的答案函数修改
    function fillSavedAnswer(question) {
        if(question.question_type === 'choice') {
            try {
                // 确保我们传入的是有效的JSON字符串
                let selectedOptions;
                if (typeof question.saved_answer === 'string') {
                    selectedOptions = JSON.parse(question.saved_answer);
                } else {
                    // 如果已经是对象，尝试直接使用
                    selectedOptions = question.saved_answer || [];
                }

                // 检查解析后的内容是否为数组
                if (!Array.isArray(selectedOptions)) {
                    console.error('解析后的选择题答案不是数组:', selectedOptions);
                    selectedOptions = [];
                }

                console.log('解析选择题答案:', selectedOptions);

                // 使用解析后的数组设置checkbox状态
                selectedOptions.forEach(optionId => {
                    const checkbox = document.getElementById(`option-${optionId}`);
                    if(checkbox) {
                        checkbox.checked = true;
                    } else {
                        console.warn(`未找到选项ID为${optionId}的选择框`);
                    }
                });
            } catch(e) {
                console.error('解析已保存的选择题答案失败:', e);
                console.error('原始答案内容:', question.saved_answer);
            }
        } else {
            // 对于填空题和编程题
            const textarea = document.getElementById('answer_content');
            if (question.saved_answer && question.saved_answer.trim() !== '') {
                // 如果有已保存的答案，使用它
                textarea.value = question.saved_answer;
            }
        }
    }

    // 保存填空题或编程题答案
    function saveAnswer(callback) {
        const questionId = currentQuestionId;
        const answerContent = document.getElementById('answer_content').value;

        saveAnswerToServer(questionId, answerContent, callback);
    }

    // 向服务器保存答案
    function saveAnswerToServer(questionId, answerContent, callback) {
        // 调试信息
        console.log('发送答案数据:', {
            score_id: scoreId,
            question_id: questionId,
            answer_content: answerContent
        });

        fetch('/exams/student/save_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken  // 添加CSRF令牌到请求头
            },
            body: JSON.stringify({
                score_id: scoreId,
                question_id: questionId,
                answer_content: answerContent
            })
        })
        .then(response => {
            console.log('响应状态:', response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('错误响应:', text);
                    throw new Error('保存失败: ' + response.status + ' - ' + text);
                });
            }
            return response.json();
        })
        .then(data => {
            if(data.success) {
                // 更新保存状态
                const saveStatus = document.getElementById('save-status');
                saveStatus.textContent = `已保存 (${data.saved_at})`;
                saveStatus.style.display = 'inline';
                setTimeout(() => {
                    saveStatus.style.display = 'none';
                }, 3000);

                // 更新全局保存状态
                const lastSaveTime = document.getElementById('last-save-time');
                if (lastSaveTime) {
                    lastSaveTime.textContent = '上次保存: ' + data.saved_at;
                }

                // 更新题目状态
                questionStatus[questionId] = true;
                updateQuestionNavStatus(questionId, true);

                // 标记为已保存
                if (window.markSaved) window.markSaved();

                // 执行回调函数
                if (typeof callback === 'function') {
                    callback(data);
                }
            } else {
                console.error('保存失败:', data);
                alert('保存答案失败: ' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('保存答案失败:', error);
            alert('保存答案失败: ' + error.message);
        });
    }

    // 更新题目导航状态
    function updateQuestionNavStatus(questionId, answered) {
        const navBtn = document.getElementById(`nav-question-${questionId}`);
        if(navBtn) {
            if(answered) {
                navBtn.classList.remove('btn-outline-secondary');
                navBtn.classList.add('btn-success');
            } else {
                navBtn.classList.remove('btn-success');
                navBtn.classList.add('btn-outline-secondary');
            }
        }
    }

    // 更新导航按钮状态
    function updateNavigationButtons() {
        const currentIndex = examQuestions.findIndex(q => q.id === currentQuestionId);

        // 更新上一题按钮
        const prevButton = document.getElementById('prev-question-btn');
        if(currentIndex > 0) {
            prevButton.disabled = false;
        } else {
            prevButton.disabled = true;
        }

        // 更新下一题按钮
        const nextButton = document.getElementById('next-question-btn');
        if(currentIndex < examQuestions.length - 1) {
            nextButton.disabled = false;
        } else {
            nextButton.disabled = true;
        }
    }

    // 更新剩余时间
    function updateRemainingTime(seconds) {
        const timerElement = document.getElementById('remaining-time');

        if(seconds <= 0) {
            timerElement.textContent = '考试已结束';
            document.getElementById('exam-timer').classList.remove('alert-info');
            document.getElementById('exam-timer').classList.add('alert-danger');
            return;
        }

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        timerElement.textContent = `${padZero(hours)}:${padZero(minutes)}:${padZero(secs)}`;
    }

    // 数字前补零
    function padZero(num) {
        return num.toString().padStart(2, '0');
    }

    // 获取题目类型文本
    function getQuestionTypeText(type) {
        switch(type) {
            case 'choice': return '选择题';
            case 'fill_blank': return '填空题';
            case 'programming': return '编程题';
            default: return '未知题型';
        }
    }

    // 根据ID获取题目序号
    function getQuestionOrderById(id) {
        const question = examQuestions.find(q => q.id === id);
        return question ? question.order : '?';
    }

    // 设置自动保存
    function setupAutoSave() {
        // 添加文本区域输入事件监听器
        const textarea = document.getElementById('answer_content');
        if (textarea) {
            textarea.addEventListener('input', function() {
                // 标记为未保存状态
                if (window.markUnsaved) window.markUnsaved();

                // 使用防抖进行自动保存
                if (window.autoSaveDebounce) clearTimeout(window.autoSaveDebounce);
                window.autoSaveDebounce = setTimeout(function() {
                    if (currentQuestionId) {
                        saveAnswer();
                        console.log('自动保存填空/编程题答案');
                    }
                }, 2000); // 输入后2秒保存
            });
        }

        // 更新保存状态显示
        document.getElementById('save-status-indicator').textContent = '自动保存: 已启用';
    }

    // 获取当前题目的答案数据
    window.getCurrentQuestionData = function() {
        if (!currentQuestionId) return null;

        let answerContent = '';

        // 根据题目类型获取答案内容
        const questionTypeElement = document.getElementById('question-type-badge');
        if (!questionTypeElement) return null;

        const questionType = questionTypeElement.textContent.trim();

        if (questionType === '选择题') {
            // 获取选中的选项ID
            const selectedOptions = [];
            document.querySelectorAll('.option-checkbox:checked').forEach(checkbox => {
                selectedOptions.push(parseInt(checkbox.value));
            });
            answerContent = JSON.stringify(selectedOptions);
        } else {
            // 填空题或编程题
            const textarea = document.getElementById('answer_content');
            if (textarea) {
                answerContent = textarea.value;
            }
        }

        return {
            score_id: scoreId,
            question_id: currentQuestionId,
            answer_content: answerContent
        };
    };

    // 添加文本区域输入事件监听器
    document.addEventListener('input', function(event) {
        if (event.target.id === 'answer_content') {
            // 使用防抖进行自动保存
            if (window.autoSaveDebounce) clearTimeout(window.autoSaveDebounce);
            window.autoSaveDebounce = setTimeout(function() {
                if (currentQuestionId) {
                    saveAnswer();
                    console.log('自动保存填空/编程题答案');
                }
            }, 2000); // 输入后2秒保存
        }
    });
});