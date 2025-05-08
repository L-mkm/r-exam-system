// manage_questions.js - 考试题目管理页面脚本
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM已加载完成，初始化题目管理页面...");

    // 全局变量
    let hasUnsavedChanges = false;
    let currentPage = 1;
    let isLoadingMore = false;
    let noMoreQuestions = false;
    const ITEMS_PER_PAGE = 20;

    // DOM元素引用
    const sortableQuestions = document.getElementById('sortable_questions');
    const toggleRandomQuestions = document.getElementById('toggleRandomQuestions');
    const randomQuestionsSettings = document.getElementById('randomQuestionsSettings');
    const backBtn = document.getElementById('back_btn');
    const saveBtn = document.getElementById('save_btn');
    const cancelBtn = document.getElementById('cancel_btn');
    const saveStatus = document.getElementById('save_status');
    const removeSelectedBtn = document.getElementById('remove_selected_btn');
    const addSelectedBtn = document.getElementById('add_selected_btn');
    const loadMoreBtn = document.getElementById('load_more_btn');
    const selectAllAdded = document.getElementById('select_all_added');
    const selectAllAvailable = document.getElementById('select_all_available');
    const searchInput = document.getElementById('search_questions');
    const filterType = document.getElementById('filter_type');
    const filterDifficulty = document.getElementById('filter_difficulty');
    const filterCategory = document.getElementById('filter_category');
    const previewRandomBtn = document.getElementById('preview_random_btn');
    const applyRandomBtn = document.getElementById('apply_random_btn');

    // 初始化页面
    initPage();

    // 初始化排序功能
    initSortable();

    // 设置事件监听器
    setupEventListeners();

    // 更新统计信息
    updateStats();

    // 页面初始化
    function initPage() {
        console.log("初始化页面");

        // 触发一次筛选，确保可见题目正确
        filterAvailableQuestions();
    }

    // 初始化可拖拽排序
    function initSortable() {
        if (sortableQuestions) {
            new Sortable(sortableQuestions, {
                animation: 150,
                ghostClass: 'bg-light',
                handle: '.question-order',
                onEnd: function() {
                    // 更新序号显示
                    updateOrderNumbers();
                    // 保存新的排序
                    saveQuestionOrder();
                    // 标记有未保存的更改
                    markUnsaved();
                }
            });
        }
    }

    // 设置事件监听器
    function setupEventListeners() {
        // 随机抽题设置显示/隐藏
        if (toggleRandomQuestions) {
            toggleRandomQuestions.addEventListener('change', function() {
                if (this.checked) {
                    randomQuestionsSettings.style.display = 'block';
                } else {
                    randomQuestionsSettings.style.display = 'none';
                }
            });
        }

        // 分值变更自动保存
        document.querySelectorAll('.score-input').forEach(input => {
            input.addEventListener('change', function() {
                const questionId = this.getAttribute('data-question-id');
                const newScore = parseFloat(this.value);

                if (isNaN(newScore) || newScore < 0) {
                    alert('请输入有效的分值');
                    return;
                }

                updateQuestionScore(questionId, newScore);
            });
        });

        // 单个题目添加/移除按钮
        document.querySelectorAll('.add-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const questionId = this.getAttribute('data-question-id');
                addQuestion(questionId);
            });
        });

        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const questionId = this.getAttribute('data-question-id');
                removeQuestion(questionId);
            });
        });

        // 查看题目详情
        // document.querySelectorAll('.view-btn').forEach(btn => {
           // btn.addEventListener('click', function() {
                // const questionId = this.getAttribute('data-question-id');
                // viewQuestionDetail(questionId);
            // });
        // });

        // +题目标题点击事件
        document.querySelectorAll('.question-title-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const questionId = this.getAttribute('data-question-id');
                viewQuestionDetail(questionId);
            });
        });


        // 批量选择
        if (selectAllAdded) {
            selectAllAdded.addEventListener('change', function() {
                const isChecked = this.checked;
                document.querySelectorAll('.question-check').forEach(check => {
                    check.checked = isChecked;
                });
                updateRemoveSelectedButton();
            });
        }

        if (selectAllAvailable) {
            selectAllAvailable.addEventListener('change', function() {
                const isChecked = this.checked;
                document.querySelectorAll('.available-check:not(:disabled)').forEach(check => {
                    check.checked = isChecked;
                });
                updateAddSelectedButton();
            });
        }

        // 单个题目选择状态变化
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('question-check')) {
                updateRemoveSelectedButton();
            } else if (e.target.classList.contains('available-check')) {
                updateAddSelectedButton();
            }
        });

        // 批量添加/移除按钮
        if (addSelectedBtn) {
            addSelectedBtn.addEventListener('click', function() {
                addSelectedQuestions();
            });
        }

        if (removeSelectedBtn) {
            removeSelectedBtn.addEventListener('click', function() {
                removeSelectedQuestions();
            });
        }

        // 搜索和筛选
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                filterAvailableQuestions();
            });
        }

        if (filterType) {
            filterType.addEventListener('change', function() {
                filterAvailableQuestions();
            });
        }

        if (filterDifficulty) {
            filterDifficulty.addEventListener('change', function() {
                filterAvailableQuestions();
            });
        }

        if (filterCategory) {
            filterCategory.addEventListener('change', function() {
                filterAvailableQuestions();
            });
        }

        // 加载更多题目
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function() {
                loadMoreQuestions();
            });
        }

        // 随机抽题预览和应用
        if (previewRandomBtn) {
            previewRandomBtn.addEventListener('click', function() {
                previewRandomQuestions();
            });
        }

        if (applyRandomBtn) {
            applyRandomBtn.addEventListener('click', function() {
                applyRandomQuestions();
            });
        }

        // 保存和取消按钮
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                saveAll();
            });
        }

        // 取消按钮
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                if (hasUnsavedChanges) {
                    const cancelModal = new bootstrap.Modal(document.getElementById('cancelConfirmModal'));
                    cancelModal.show();
                } else {
                    // 无更改时直接返回
                    redirectBasedOnStatus();
                }
            });
        }

        // 确认放弃按钮点击事件
        const confirmDiscardBtn = document.getElementById('confirm_discard_btn');
        if (confirmDiscardBtn) {
            confirmDiscardBtn.addEventListener('click', function() {
                console.log("确认放弃更改按钮点击");

                // 禁用自动保存
                window.disableAutoSave = true;
                hasUnsavedChanges = false;

                // 重新加载页面，放弃所有未保存的更改
                window.location.reload();
            });
        }

        // 根据考试状态重定向
        function redirectBasedOnStatus() {
            fetch(`/exams/${EXAM_ID}/check_status`)
                .then(response => response.json())
                .then(data => {
                    if (data.is_draft) {
                        window.location.replace(`/exams/${EXAM_ID}/continue_create`);
                    } else {
                        window.location.replace(`/exams/${EXAM_ID}/edit`);
                    }
                })
                .catch(error => {
                    console.error('获取考试状态失败:', error);
                    window.location.replace(`/exams/${EXAM_ID}/edit`);
                });
        }

        // 修改返回按钮
        if (backBtn) {
            backBtn.textContent = '返回考试设置'; // 更改按钮文本以更清晰
            backBtn.addEventListener('click', function() {
                if (hasUnsavedChanges) {
                    const cancelModal = new bootstrap.Modal(document.getElementById('cancelConfirmModal'));
                    cancelModal.show();
                } else {
                    // 检查考试状态决定返回的页面
                    fetch(`/exams/${EXAM_ID}/check_status`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.is_draft) {
                                window.location.href = `/exams/${EXAM_ID}/continue_create`;
                            } else {
                                window.location.href = `/exams/${EXAM_ID}/edit`;
                            }
                        })
                        .catch(error => {
                            console.error('获取考试状态失败:', error);
                            // 默认返回编辑页面
                            window.location.href = `/exams/${EXAM_ID}/edit`;
                        });
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

    // 更新序号显示
    function updateOrderNumbers() {
        document.querySelectorAll('#sortable_questions tr').forEach((row, index) => {
            row.querySelector('.question-order').textContent = index + 1;
        });
    }

    // 保存题目排序
    function saveQuestionOrder() {
        const orderData = {};
        document.querySelectorAll('#sortable_questions tr').forEach((row, index) => {
            const questionId = row.getAttribute('data-question-id');
            orderData[questionId] = index + 1;
        });

        fetch(`/exams/${EXAM_ID}/reorder_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSaveStatus('排序已保存');
            } else {
                console.error('保存排序失败:', data.message);
            }
        })
        .catch(error => {
            console.error('保存排序请求失败:', error);
        });
    }

    // 更新题目分值
    function updateQuestionScore(questionId, newScore) {
        fetch(`/exams/${EXAM_ID}/update_question_score/${questionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ score: newScore })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSaveStatus('分值已保存');
                // 更新统计信息
                updateStats();
            } else {
                console.error('更新分值失败:', data.message);
                alert('更新分值失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('更新分值请求失败:', error);
            alert('更新分值请求失败，请重试');
        });

        // 标记有未保存的更改
        markUnsaved();
    }

    // 添加题目
    function addQuestion(questionId) {
        fetch(`/exams/${EXAM_ID}/add_question/${questionId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 显示成功消息
                showSaveStatus('题目已添加');

                // 重要：在刷新页面前重置未保存标记
                hasUnsavedChanges = false;

                // 立即刷新页面，确保看到最新状态
                window.location.reload();
            } else {
                console.error('添加题目失败:', data.message);
                alert('添加题目失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('添加题目请求失败:', error);
            alert('添加题目请求失败，请重试');
        });

        // 注释掉这行，不在这里标记未保存的更改
        // markUnsaved();
    }

    // 移除题目
        function removeQuestion(questionId) {
            if (!confirm('确定要移除此题目吗？')) {
                return;
            }

            fetch(`/exams/${EXAM_ID}/remove_question/${questionId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                // 确保检查响应状态
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                // 检查响应的内容类型，确保是JSON
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    return response.json();
                } else {
                    // 如果响应不是JSON，可能是错误页面
                    throw new Error("服务器返回了非JSON响应");
                }
            })
            .then(data => {
                if (data.success) {
                    // 显示成功消息
                    showSaveStatus('题目已移除');

                    // 从DOM中移除题目行
                    const row = document.querySelector(`tr[data-question-id="${questionId}"]`);
                    if (row) {
                        row.remove();
                    }

                    // 更新序号
                    updateOrderNumbers();

                    // 更新统计信息
                    updateStats();
                } else {
                    console.error('移除题目失败:', data.message);
                    alert('移除题目失败: ' + data.message);
                    // 错误时也重置未保存标记并刷新
                    hasUnsavedChanges = false;
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('移除题目请求失败:', error);
                // 不显示警告，直接重置未保存标记并刷新
                hasUnsavedChanges = false;
                window.location.reload();
            });

            // 不要调用 markUnsaved()
        }

    // 查看题目详情
    function viewQuestionDetail(questionId) {
        const detailContent = document.getElementById('question_detail_content');
        if (!detailContent) return;

        // 显示加载中
        detailContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('questionDetailModal'));
        modal.show();

        // 加载题目详情
        fetch(`/questions/api/detail/${questionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 根据题目类型显示不同内容
                    let content = `
                        <h4>${data.question.title}</h4>
                        <div class="mb-3">
                            <span class="badge ${getBadgeClass(data.question.question_type)}">${getTypeText(data.question.question_type)}</span>
                            <span class="badge bg-secondary">难度: ${data.question.difficulty}</span>
                        </div>
                        <div class="question-content mb-3">${data.question.content}</div>
                    `;

                    // 选择题选项
                    if (data.question.question_type === 'choice' && data.options && data.options.length > 0) {
                        content += '<h5>选项</h5><div class="list-group">';
                        data.options.forEach(option => {
                            content += `
                                <div class="list-group-item ${option.is_correct ? 'list-group-item-success' : ''}">
                                    ${option.is_correct ? '<span class="badge bg-success me-2">正确</span>' : ''}
                                    ${option.content}
                                </div>
                            `;
                        });
                        content += '</div>';
                    }

                    // 填空题和编程题答案
                    if (data.question.standard_answer) {
                        content += `
                            <h5 class="mt-3">标准答案</h5>
                            <div class="card">
                                <div class="card-body">
                                    <pre>${data.question.standard_answer}</pre>
                                </div>
                            </div>
                        `;
                    }

                    // 解析说明
                    if (data.question.explanation) {
                        content += `
                            <h5 class="mt-3">解析</h5>
                            <div class="card">
                                <div class="card-body">
                                    ${data.question.explanation}
                                </div>
                            </div>
                        `;
                    }

                    detailContent.innerHTML = content;
                } else {
                    detailContent.innerHTML = `<div class="alert alert-danger">加载题目详情失败: ${data.message}</div>`;
                }
            })
            .catch(error => {
                console.error('加载题目详情失败:', error);
                detailContent.innerHTML = '<div class="alert alert-danger">加载题目详情失败，请重试</div>';
            });
    }

    // 获取题型徽章样式
    function getBadgeClass(type) {
        switch(type) {
            case 'choice': return 'bg-primary';
            case 'fill_blank': return 'bg-success';
            case 'programming': return 'bg-warning';
            default: return 'bg-secondary';
        }
    }

    // 获取题型文本
    function getTypeText(type) {
        switch(type) {
            case 'choice': return '选择题';
            case 'fill_blank': return '填空题';
            case 'programming': return '编程题';
            default: return '未知题型';
        }
    }

    // 批量添加选中题目
    function addSelectedQuestions() {
        const selectedIds = [];
        document.querySelectorAll('.available-check:checked').forEach(checkbox => {
            const row = checkbox.closest('tr');
            if (row) {
                const questionId = row.getAttribute('data-question-id');
                if (questionId) {
                    selectedIds.push(questionId);
                }
            }
        });

        if (selectedIds.length === 0) {
            alert('请先选择要添加的题目');
            return;
        }

        // 发送批量添加请求
        fetch(`/exams/${EXAM_ID}/batch_add_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ question_ids: selectedIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSaveStatus(`已添加 ${data.added_count} 道题目`);
                hasUnsavedChanges = false;
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                console.error('批量添加题目失败:', data.message);
                alert('批量添加题目失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('批量添加题目请求失败:', error);
            alert('批量添加题目请求失败，请重试');
        });

        // 标记有未保存的更改
        markUnsaved();
    }

    // 批量移除选中题目
    function removeSelectedQuestions() {
        const selectedIds = [];
        document.querySelectorAll('.question-check:checked').forEach(checkbox => {
            const row = checkbox.closest('tr');
            if (row) {
                const questionId = row.getAttribute('data-question-id');
                if (questionId) {
                    selectedIds.push(questionId);
                }
            }
        });

        if (selectedIds.length === 0) {
            alert('请先选择要移除的题目');
            return;
        }

        if (!confirm(`确定要移除选中的 ${selectedIds.length} 道题目吗？`)) {
            return;
        }

        // 发送批量移除请求
        fetch(`/exams/${EXAM_ID}/batch_remove_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ question_ids: selectedIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 从DOM中移除题目行
                selectedIds.forEach(id => {
                    const row = document.querySelector(`tr[data-question-id="${id}"]`);
                    if (row) {
                        row.remove();
                    }
                });

                // 更新序号
                updateOrderNumbers();

                // 更新统计信息
                updateStats();

                showSaveStatus(`已移除 ${data.removed_count} 道题目`);

                // 添加：如果移除了所有题目，或者移除数量较多，刷新页面确保UI状态一致
                const remainingRows = document.querySelectorAll('#sortable_questions tr').length;
                if (remainingRows === 0 || selectedIds.length > 3) {
                    // 重置未保存标记，防止刷新警告
                    hasUnsavedChanges = false;
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                console.error('批量移除题目失败:', data.message);
                alert('批量移除题目失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('批量移除题目请求失败:', error);
            alert('批量移除题目请求失败，请重试');

            // 在发生错误时也重置未保存标记并刷新页面
            hasUnsavedChanges = false;
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        });

        // markUnsaved() 注释掉
    }

    // 更新批量移除按钮状态
    function updateRemoveSelectedButton() {
        const selectedCount = document.querySelectorAll('.question-check:checked').length;
        if (removeSelectedBtn) {
            removeSelectedBtn.disabled = selectedCount === 0;
            removeSelectedBtn.textContent = selectedCount > 0 ?
                `移除选中题目 (${selectedCount})` : '移除选中题目';
        }
    }

    // 更新批量添加按钮状态
    function updateAddSelectedButton() {
        const selectedCount = document.querySelectorAll('.available-check:checked').length;
        if (addSelectedBtn) {
            addSelectedBtn.disabled = selectedCount === 0;
            addSelectedBtn.textContent = selectedCount > 0 ?
                `添加选中题目 (${selectedCount})` : '添加选中题目';
        }
    }

    // 筛选可选题目
    function filterAvailableQuestions() {
        const searchText = searchInput ? searchInput.value.toLowerCase() : '';
        const typeFilter = filterType ? filterType.value : '';
        const difficultyFilter = filterDifficulty ? parseInt(filterDifficulty.value) : 0;
        const categoryFilter = filterCategory ? parseInt(filterCategory.value) : 0;

        document.querySelectorAll('.available-question-row').forEach(row => {
            const title = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            const type = row.getAttribute('data-type');
            const difficulty = parseInt(row.getAttribute('data-difficulty'));
            const category = parseInt(row.getAttribute('data-category'));

            // 应用筛选条件
            const matchesSearch = title.includes(searchText);
            const matchesType = !typeFilter || type === typeFilter;
            const matchesDifficulty = !difficultyFilter || difficulty === difficultyFilter;
            const matchesCategory = !categoryFilter || category === categoryFilter;

            // 显示或隐藏行
            if (matchesSearch && matchesType && matchesDifficulty && matchesCategory) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // 加载更多题目
    function loadMoreQuestions() {
        if (isLoadingMore || noMoreQuestions) return;

        isLoadingMore = true;
        currentPage++;

        // 更新按钮状态
        loadMoreBtn.textContent = '加载中...';
        loadMoreBtn.disabled = true;

        // 获取筛选条件
        const searchText = searchInput ? searchInput.value : '';
        const typeFilter = filterType ? filterType.value : '';
        const difficultyFilter = filterDifficulty ? filterDifficulty.value : '';
        const categoryFilter = filterCategory ? filterCategory.value : '';

        // 发送请求加载更多题目
        fetch(`/exams/${EXAM_ID}/available_questions?page=${currentPage}&limit=${ITEMS_PER_PAGE}&search=${searchText}&type=${typeFilter}&difficulty=${difficultyFilter}&category=${categoryFilter}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.questions.length === 0) {
                        noMoreQuestions = true;
                        loadMoreBtn.textContent = '没有更多题目';
                        loadMoreBtn.disabled = true;
                    } else {
                        // 添加新题目到列表
                        const availableQuestions = document.getElementById('available_questions');
                        data.questions.forEach(question => {
                            const row = createQuestionRow(question);
                            availableQuestions.appendChild(row);
                        });

                        // 恢复按钮状态
                        loadMoreBtn.textContent = '加载更多题目';
                        loadMoreBtn.disabled = false;

                        // 为新添加的行绑定事件
                        document.querySelectorAll('.available-question-row:not(.initialized)').forEach(row => {
                            const addBtn = row.querySelector('.add-btn');
                            if (addBtn) {
                                addBtn.addEventListener('click', function() {
                                    const questionId = this.getAttribute('data-question-id');
                                    addQuestion(questionId);
                                });
                            }

                            // 标记为已初始化
                            row.classList.add('initialized');
                        });

                        // 应用当前筛选条件
                        filterAvailableQuestions();
                    }
                } else {
                    console.error('加载更多题目失败:', data.message);
                    loadMoreBtn.textContent = '加载失败，点击重试';
                    loadMoreBtn.disabled = false;
                }

                isLoadingMore = false;
            })
            .catch(error => {
                console.error('加载更多题目请求失败:', error);
                loadMoreBtn.textContent = '加载失败，点击重试';
                loadMoreBtn.disabled = false;
                isLoadingMore = false;
            });
    }

    // 创建题目行
    function createQuestionRow(question) {
        const row = document.createElement('tr');
        row.className = 'available-question-row';
        row.setAttribute('data-question-id', question.id);
        row.setAttribute('data-type', question.question_type);
        row.setAttribute('data-difficulty', question.difficulty);
        row.setAttribute('data-category', question.category_id || 0);

        // 设置行内容
        row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input available-check">
            </td>
            <td>
                <span class="badge ${getBadgeClass(question.question_type)}">${getTypeText(question.question_type)}</span>
            </td>
            <td>
                <a href="javascript:void(0);" class="question-title-link" data-question-id="${question.id}">
                    ${truncateText(question.title, 30)}
                </a>
            </td>
            <td>${question.difficulty}</td>
            <td>
                <button class="btn btn-sm btn-success add-btn" data-question-id="${question.id}">添加</button>
            </td>
        `;

        // 为新创建的行中的题目标题添加点击事件
        const titleLink = row.querySelector('.question-title-link');
        if (titleLink) {
            titleLink.addEventListener('click', function(e) {
                e.preventDefault();
                const questionId = this.getAttribute('data-question-id');
                viewQuestionDetail(questionId);
            });
        }


        return row;
    }

    // 截断文本
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // 预览随机题目
    function previewRandomQuestions() {
        // 获取随机抽题设置
        const settings = getRandomSettings();

        if (!validateRandomSettings(settings)) {
            return;
        }

        // 发送请求预览随机题目
        fetch(`/exams/${EXAM_ID}/preview_random_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`预计将随机抽取 ${data.total_count} 道题目，总分值 ${data.total_score} 分。\n\n包含：\n选择题: ${data.choice_count} 道\n填空题: ${data.fill_blank_count} 道\n编程题: ${data.programming_count} 道`);
            } else {
                console.error('预览随机题目失败:', data.message);
                alert('预览随机题目失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('预览随机题目请求失败:', error);
            alert('预览随机题目请求失败，请重试');
        });
    }

    // 应用随机抽题
    function applyRandomQuestions() {
        // 获取随机抽题设置
        const settings = getRandomSettings();

        if (!validateRandomSettings(settings)) {
            return;
        }

        if (!confirm('应用随机抽题将清除当前已添加的所有题目，确定继续吗？')) {
            return;
        }

        // 发送请求应用随机题目
        fetch(`/exams/${EXAM_ID}/apply_random_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSaveStatus(`已随机抽取 ${data.total_count} 道题目`);
                hasUnsavedChanges = false;
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                console.error('应用随机题目失败:', data.message);
                alert('应用随机题目失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('应用随机题目请求失败:', error);
            alert('应用随机题目请求失败，请重试');
        });

        // 标记有未保存的更改
        markUnsaved();
    }

    // 获取随机抽题设置
    function getRandomSettings() {
        return {
            category_id: document.getElementById('category_id').value,
            choice_count: parseInt(document.getElementById('choice_count').value) || 0,
            choice_difficulty_min: parseInt(document.getElementById('choice_difficulty_min').value) || 0,
            choice_difficulty_max: parseInt(document.getElementById('choice_difficulty_max').value) || 0,
            choice_score: parseFloat(document.getElementById('choice_score').value) || 0,
            fill_blank_count: parseInt(document.getElementById('fill_blank_count').value) || 0,
            fill_blank_difficulty_min: parseInt(document.getElementById('fill_blank_difficulty_min').value) || 0,
            fill_blank_difficulty_max: parseInt(document.getElementById('fill_blank_difficulty_max').value) || 0,
            fill_blank_score: parseFloat(document.getElementById('fill_blank_score').value) || 0,
            programming_count: parseInt(document.getElementById('programming_count').value) || 0,
            programming_difficulty_min: parseInt(document.getElementById('programming_difficulty_min').value) || 0,
            programming_difficulty_max: parseInt(document.getElementById('programming_difficulty_max').value) || 0,
            programming_score: parseFloat(document.getElementById('programming_score').value) || 0
        };
    }

    // 验证随机抽题设置
    function validateRandomSettings(settings) {
        const totalCount = settings.choice_count + settings.fill_blank_count + settings.programming_count;

        if (totalCount === 0) {
            alert('请至少设置一种题型的数量');
            return false;
        }

        if (settings.choice_count > 0 && settings.choice_score <= 0) {
            alert('选择题分值必须大于0');
            return false;
        }

        if (settings.fill_blank_count > 0 && settings.fill_blank_score <= 0) {
            alert('填空题分值必须大于0');
            return false;
        }

        if (settings.programming_count > 0 && settings.programming_score <= 0) {
            alert('编程题分值必须大于0');
            return false;
        }

        // 验证难度范围
        if (settings.choice_count > 0 &&
            settings.choice_difficulty_min > 0 &&
            settings.choice_difficulty_max > 0 &&
            settings.choice_difficulty_min > settings.choice_difficulty_max) {
            alert('选择题最低难度不能大于最高难度');
            return false;
        }

        if (settings.fill_blank_count > 0 &&
            settings.fill_blank_difficulty_min > 0 &&
            settings.fill_blank_difficulty_max > 0 &&
            settings.fill_blank_difficulty_min > settings.fill_blank_difficulty_max) {
            alert('填空题最低难度不能大于最高难度');
            return false;
        }

        if (settings.programming_count > 0 &&
            settings.programming_difficulty_min > 0 &&
            settings.programming_difficulty_max > 0 &&
            settings.programming_difficulty_min > settings.programming_difficulty_max) {
            alert('编程题最低难度不能大于最高难度');
            return false;
        }

        return true;
    }

    // 更新统计信息
    function updateStats() {
        // 计算题目总数
        const totalCount = document.querySelectorAll('#sortable_questions tr').length;
        document.getElementById('added_questions_count').textContent = totalCount;
        document.getElementById('total_questions_count').textContent = totalCount;

        // 计算各类型题目数量
        const choiceCount = document.querySelectorAll('#sortable_questions tr td:nth-child(3) .badge-primary, #sortable_questions tr td:nth-child(3) .bg-primary').length;
        const fillBlankCount = document.querySelectorAll('#sortable_questions tr td:nth-child(3) .badge-success, #sortable_questions tr td:nth-child(3) .bg-success').length;
        const programmingCount = document.querySelectorAll('#sortable_questions tr td:nth-child(3) .badge-warning, #sortable_questions tr td:nth-child(3) .bg-warning').length;

        document.getElementById('choice_questions_count').textContent = choiceCount;
        document.getElementById('fill_blank_questions_count').textContent = fillBlankCount;
        document.getElementById('programming_questions_count').textContent = programmingCount;

        // 计算总分值
        let totalScore = 0;
        document.querySelectorAll('.score-input').forEach(input => {
            totalScore += parseFloat(input.value) || 0;
        });

        document.getElementById('total_score').textContent = totalScore.toFixed(1);
    }

    // 显示保存状态
    function showSaveStatus(message) {
        if (!saveStatus) return;

        saveStatus.textContent = message;
        saveStatus.style.display = 'inline';

        setTimeout(() => {
            saveStatus.style.display = 'none';
        }, 3000);
    }

    // 保存所有更改
    function saveAll() {
        // 发送请求保存所有更改
        fetch(`/exams/${EXAM_ID}/save_all`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 清除未保存标记
                hasUnsavedChanges = false;

                showSaveStatus('所有更改已保存');

                // 使用服务器返回的重定向URL
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                }
            } else {
                console.error('保存失败:', data.message);
                alert('保存失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('保存请求失败:', error);
            alert('保存请求失败，请重试');
        });
    }

    // 标记有未保存的更改
    function markUnsaved() {
        hasUnsavedChanges = true;
    }
});