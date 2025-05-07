// exam_create.js - 考试创建页面脚本
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM已加载完成，初始化考试创建页面...");

    // 获取表单元素
    const examForm = document.getElementById('examForm');
    const toggleRandomQuestions = document.getElementById('toggleRandomQuestions');
    const randomQuestionsSettings = document.getElementById('randomQuestionsSettings');
    const useDurationCheckbox = document.getElementById('use_duration');
    const durationContainer = document.getElementById('duration_container');
    const examDurationInput = document.getElementById('exam_duration');
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');

    // 获取按钮元素
    const saveDraftBtn = document.getElementById('save_draft_btn');
    const createExamBtn = document.getElementById('create_exam_btn');
    const confirmCreateBtn = document.getElementById('confirm_create_btn');
    const manageQuestionsBtn = document.getElementById('manage_questions_btn');
    const cancelBtn = document.getElementById('cancel_btn');

    // 获取状态和统计元素
    const saveStatus = document.getElementById('save_status');
    const questionCountElement = document.getElementById('question_count');
    const totalScoreElement = document.getElementById('total_score');
    const noQuestionsWarning = document.getElementById('no_questions_warning');

    // 获取题目统计相关元素
    const choiceCountInput = document.getElementById('choice_count');
    const choiceScoreInput = document.getElementById('choice_score');
    const fillBlankCountInput = document.getElementById('fill_blank_count');
    const fillBlankScoreInput = document.getElementById('fill_blank_score');
    const programmingCountInput = document.getElementById('programming_count');
    const programmingScoreInput = document.getElementById('programming_score');

    // 表单是否有未保存更改
    let hasUnsavedChanges = false;

    // ===== 初始化页面 =====
    init();

    // 初始化函数
    function init() {
        console.log("初始化页面");

        // 初始显示状态
        if (toggleRandomQuestions && toggleRandomQuestions.checked) {
            randomQuestionsSettings.style.display = 'block';
        }

        // 更新题目统计
        updateQuestionStats();

        // 添加事件监听器
        setupEventListeners();

        // 设置自动保存
        setupAutoSave();
    }

    // 设置事件监听器
    function setupEventListeners() {
        console.log("设置事件监听器");


        // 考试时长设置
        if (useDurationCheckbox) {
            useDurationCheckbox.addEventListener('change', function() {
                console.log("使用考试时长变更:", this.checked);
                if (this.checked) {
                    durationContainer.style.display = 'block';
                    calculateEndTime();
                    endTimeInput.disabled = true;
                } else {
                    durationContainer.style.display = 'none';
                    endTimeInput.disabled = false;
                }
                markUnsaved();
            });
        }

        // 当开始时间改变时，如果启用了考试时长，就重新计算结束时间
        if (startTimeInput) {
            startTimeInput.addEventListener('change', function() {
                console.log("开始时间变更:", this.value);
                if (useDurationCheckbox && useDurationCheckbox.checked) {
                    calculateEndTime();
                }
                markUnsaved();
            });
        }

        // 当考试时长改变时，重新计算结束时间
        if (examDurationInput) {
            examDurationInput.addEventListener('input', function() {
                console.log("考试时长变更:", this.value);
                if (useDurationCheckbox && useDurationCheckbox.checked) {
                    calculateEndTime();
                }
                markUnsaved();
            });
        }

        // 结束时间变化
        if (endTimeInput) {
            endTimeInput.addEventListener('change', function() {
                markUnsaved();
            });
        }


        // 保存草稿按钮
        if (saveDraftBtn) {
            saveDraftBtn.addEventListener('click', function() {
                console.log("保存草稿按钮点击");
                saveDraft();
            });
        }

        // 创建考试按钮
        if (createExamBtn) {
            createExamBtn.addEventListener('click', function() {
                console.log("创建考试按钮点击");
                showCreateExamModal();
            });
        }

        // 确认创建按钮
        if (confirmCreateBtn) {
            confirmCreateBtn.addEventListener('click', function() {
                console.log("确认创建按钮点击");
                submitForm();
            });
        }

        // 管理题目按钮
        const manageQuestionsBtn = document.getElementById('manage_questions_btn');
            if (manageQuestionsBtn) {
                manageQuestionsBtn.addEventListener('click', function() {
                    console.log("管理题目按钮点击");
                    // 保存当前表单数据
                    saveDraft(function(data) {
                        console.log("saveDraft回调", data);

                        if (data && data.success && data.exam_id) {
                            // 保存成功后跳转到题目管理页面
                            console.log("保存成功，跳转到题目管理页面");
                            window.location.href = `/exams/${data.exam_id}/questions`;
                        } else {
                            const errorMessage = data && data.message ? data.message : '未知错误';
                            console.error("保存失败:", errorMessage);
                            alert('保存失败: ' + errorMessage);
                        }
                    });
                });
            }

        // 取消按钮
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function(e) {
                console.log("取消按钮点击, 有未保存更改:", hasUnsavedChanges);
                if (hasUnsavedChanges) {
                    e.preventDefault();
                    // 使用Bootstrap 5方式显示模态框
                    const cancelModal = new bootstrap.Modal(document.getElementById('cancelModal'));
                    cancelModal.show();
                }
                // 如果没有未保存的更改，则直接导航到列表页面
            });
        }

        // 标记表单中的其他输入变化
        if (examForm) {
            examForm.addEventListener('input', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                    markUnsaved();
                }
            });
        }

        // 页面关闭前提示
        window.addEventListener('beforeunload', function(e) {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '您有未保存的更改，确定要离开此页面吗？';
                return e.returnValue;
            }
        });
    }

    // 根据开始时间和考试时长计算结束时间
    function calculateEndTime() {
        console.log("计算结束时间");
        if (!startTimeInput || !startTimeInput.value) return;

        const startTime = new Date(startTimeInput.value);
        const durationMinutes = parseInt(examDurationInput.value) || 120;

        if (!isNaN(startTime.getTime())) {
            const endTime = new Date(startTime.getTime() + durationMinutes * 60000);

            // 格式化为datetime-local格式: YYYY-MM-DDTHH:MM
            const year = endTime.getFullYear();
            const month = String(endTime.getMonth() + 1).padStart(2, '0');
            const day = String(endTime.getDate()).padStart(2, '0');
            const hours = String(endTime.getHours()).padStart(2, '0');
            const minutes = String(endTime.getMinutes()).padStart(2, '0');

            const formattedEndTime = `${year}-${month}-${day}T${hours}:${minutes}`;
            endTimeInput.value = formattedEndTime;
            console.log("结束时间已设置为:", formattedEndTime);

            // 禁用结束时间输入
            endTimeInput.disabled = true;
        }
    }

    // 更新题目统计信息
    function updateQuestionStats() {
        if (!questionCountElement || !totalScoreElement || !noQuestionsWarning) return;

        // 直接显示统计信息，不再考虑随机抽题
        // 由于我们已经从页面移除随机抽题功能，这里只显示固定值
        // 实际数据将在题目管理页面处理
        questionCountElement.textContent = '0';
        totalScoreElement.textContent = '0';
        noQuestionsWarning.style.display = 'block';

        console.log("统计信息已更新");
    }


    // 标记有未保存的更改
    function markUnsaved() {
        hasUnsavedChanges = true;
        if (saveStatus) saveStatus.style.display = 'none';
    }

    // 标记为已保存
    function markSaved() {
        hasUnsavedChanges = false;
        if (!saveStatus) return;

        saveStatus.textContent = '已自动保存草稿';
        saveStatus.style.display = 'inline';

        // 3秒后隐藏保存状态
        setTimeout(function() {
            saveStatus.style.display = 'none';
        }, 3000);
    }

    // 设置自动保存
    function setupAutoSave() {
        // 每30秒自动保存一次
        setInterval(function() {
            if (hasUnsavedChanges) {
                console.log("自动保存触发");
                saveDraft();
            }
        }, 30000);
    }

    // 保存草稿
    function saveDraft(callback) {
        // 检查是否所有必需元素都存在
        if (!document.querySelector('input[name="title"]')) {
          console.error("找不到标题输入框");
          if (typeof callback === 'function') {
            callback({success: false, message: "找不到标题输入框"});
          }
          return;
        }

        // 收集表单数据
        const formData = {
            title: document.querySelector('input[name="title"]').value || '',
            description: document.querySelector('textarea[name="description"]').value || '',
            start_time: document.getElementById('start_time').value || '',
            end_time: document.getElementById('end_time').value || '',
            is_published: document.querySelector('input[name="is_published"]').checked || false,
            use_duration: document.getElementById('use_duration').checked || false,
            exam_duration: document.getElementById('exam_duration').value || '120'
        };

        // 如果有考试ID，添加到数据中
        const examIdInput = document.querySelector('input[name="exam_id"]');
        if (examIdInput && examIdInput.value) {
            formData.exam_id = examIdInput.value;
        }

        console.log("保存草稿数据:", formData);

        // 发送AJAX请求
        fetch('/exams/save_draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN // 使用前面定义的全局变量
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("保存草稿响应:", data);

            if (data.success) {
                // 如果返回了考试ID，添加到表单中
                if (data.exam_id && !document.querySelector('input[name="exam_id"]')) {
                    const idInput = document.createElement('input');
                    idInput.type = 'hidden';
                    idInput.name = 'exam_id';
                    idInput.value = data.exam_id;
                    document.getElementById('examForm').appendChild(idInput);
                }

                markSaved();

                // 执行回调
                if (typeof callback === 'function') {
                    callback(data);
                }
            } else {
                console.error("保存失败:", data.message);
                if (typeof callback === 'function') {
                    callback(data); // 即使失败也传递数据
                } else {
                    alert("保存失败: " + (data.message || "未知错误"));
                }
            }
        })
        .catch(error => {
            console.error("请求错误:", error);
            if (typeof callback === 'function') {
                callback({success: false, message: "请求错误: " + error.message}); // 传递错误数据
            } else {
                alert("保存请求出错，请重试");
            }
        });
    }

    // 显示创建考试确认对话框
    function showCreateExamModal() {
        console.log("显示创建考试确认对话框");
        if (!document.getElementById('exam_summary')) return;

        // 准备考试概要信息
        const title = document.querySelector('input[name="title"]')?.value || '(无标题)';
        const startTime = startTimeInput?.value ? new Date(startTimeInput.value).toLocaleString() : '(未设置)';
        const endTime = endTimeInput?.value ? new Date(endTimeInput.value).toLocaleString() : '(未设置)';
        const isPublished = document.querySelector('input[name="is_published"]')?.checked ? '是' : '否';

        const totalCount = parseInt(questionCountElement?.textContent) || 0;
        const totalScore = parseFloat(totalScoreElement?.textContent) || 0;

        // 填充确认对话框中的信息
        const summary = document.getElementById('exam_summary');
        summary.innerHTML = `
            <p><strong>考试标题:</strong> ${title}</p>
            <p><strong>开始时间:</strong> ${startTime}</p>
            <p><strong>结束时间:</strong> ${endTime}</p>
            <p><strong>立即发布:</strong> ${isPublished}</p>
            <p><strong>题目数量:</strong> ${totalCount}</p>
            <p><strong>总分值:</strong> ${totalScore.toFixed(1)}</p>
        `;

        // 如果没有题目，显示警告
        const confirmWarning = document.getElementById('confirm_warning');
        if (confirmWarning) {
            if (totalCount === 0) {
                confirmWarning.style.display = 'block';
            } else {
                confirmWarning.style.display = 'none';
            }
        }

        // 使用Bootstrap 5方式显示模态框
        try {
            const createExamModal = document.getElementById('createExamModal');
            if (createExamModal) {
                const modal = new bootstrap.Modal(createExamModal);
                modal.show();
                console.log("模态框显示成功");
            } else {
                throw new Error("未找到模态框元素");
            }
        } catch (error) {
            console.error("模态框显示失败:", error);
            // 备用方案：使用原生确认框
            if (confirm("确认创建考试吗？")) {
                submitForm();
            }
        }
    }

    // 提交表单
    function submitForm() {
        console.log("提交表单");
        // 确保结束时间输入可用
        if (endTimeInput) endTimeInput.disabled = false;

        // 提交表单
        if (examForm) examForm.submit();
    }

    console.log("脚本初始化完成");
});