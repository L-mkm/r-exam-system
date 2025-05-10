/**
 * 统一的自动保存和状态管理系统
 * 用于考试创建和编辑页面
 */

// 自动保存系统
const AutosaveSystem = (function() {
    // 配置
    const config = {
        interval: 30000, // 自动保存间隔（毫秒）
        statusShowDuration: 3000, // 状态显示时间（毫秒）
        savingEndpoint: '', // 保存API端点
        entityId: null, // 当前实体ID（考试ID等）
        formSelector: '', // 表单选择器
        statusElementSelector: '', // 状态显示元素选择器
        tokenName: 'csrf_token', // CSRF令牌名称
        onBeforeSave: null, // 保存前回调
        onAfterSave: null, // 保存后回调
        onSaveError: null, // 保存错误回调
    };

    // 状态
    let state = {
        hasUnsavedChanges: false,
        isSaving: false,
        autosaveTimer: null,
        isAutosaveEnabled: true,
        lastSaveTime: null
    };

    // 初始化
    function init(options = {}) {
        // 合并配置
        Object.assign(config, options);

        // 设置表单变更监听
        setupFormChangeListeners();

        // 设置离开页面前提示
        setupBeforeUnloadListener();

        // 启动自动保存定时器
        startAutosaveTimer();

        console.log('自动保存系统已初始化');
    }

    // 设置表单变更监听
    function setupFormChangeListeners() {
        const form = document.querySelector(config.formSelector);
        if (!form) {
            console.error('未找到表单元素');
            return;
        }

        // 监听表单输入变化
        form.addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                markUnsaved();
            }
        });

        // 监听复选框和单选框变化
        form.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox' || e.target.type === 'radio' || e.target.tagName === 'SELECT') {
                markUnsaved();
            }
        });

        console.log('表单变更监听已设置');
    }

    // 设置离开页面前提示
    function setupBeforeUnloadListener() {
        window.addEventListener('beforeunload', (e) => {
            if (state.hasUnsavedChanges && state.isAutosaveEnabled) {
                e.preventDefault();
                e.returnValue = '您有未保存的更改，确定要离开此页面吗？';
                return e.returnValue;
            }
        });

        console.log('离开页面前提示已设置');
    }

    // 启动自动保存定时器
    function startAutosaveTimer() {
        // 清除已有定时器
        if (state.autosaveTimer) {
            clearInterval(state.autosaveTimer);
        }

        // 设置新定时器
        state.autosaveTimer = setInterval(() => {
            if (state.hasUnsavedChanges && state.isAutosaveEnabled && !state.isSaving) {
                console.log('自动保存触发');
                saveForm();
            }
        }, config.interval);

        console.log('自动保存定时器已启动');
    }

    // 停止自动保存
    function stopAutosave() {
        if (state.autosaveTimer) {
            clearInterval(state.autosaveTimer);
            state.autosaveTimer = null;
        }

        state.isAutosaveEnabled = false;
        console.log('自动保存已停止');
    }

    // 恢复自动保存
    function resumeAutosave() {
        state.isAutosaveEnabled = true;
        startAutosaveTimer();
        console.log('自动保存已恢复');
    }

    // 标记有未保存的更改
    function markUnsaved() {
        state.hasUnsavedChanges = true;
        hideStatusElement();
    }

    // 标记为已保存
    function markSaved() {
        state.hasUnsavedChanges = false;
        state.lastSaveTime = new Date();
        showStatusElement('已自动保存');
    }

    // 显示状态元素
    function showStatusElement(message) {
        const statusElement = document.querySelector(config.statusElementSelector);
        if (!statusElement) return;

        statusElement.textContent = message;
        statusElement.classList.add('show');

        // 一段时间后隐藏
        setTimeout(() => {
            hideStatusElement();
        }, config.statusShowDuration);
    }

    // 隐藏状态元素
    function hideStatusElement() {
        const statusElement = document.querySelector(config.statusElementSelector);
        if (!statusElement) return;

        statusElement.classList.remove('show');
    }

    // 收集表单数据
    function collectFormData() {
        const form = document.querySelector(config.formSelector);
        if (!form) return null;

        // 如果有自定义数据收集函数，使用它
        if (typeof config.onBeforeSave === 'function') {
            const customData = config.onBeforeSave();
            if (customData) return customData;
        }

        // 否则使用默认的表单数据收集
        const formData = new FormData(form);
        const data = {};

        for (const [key, value] of formData.entries()) {
            // 处理复选框数组
            if (key.endsWith('[]')) {
                const realKey = key.slice(0, -2);
                if (!data[realKey]) {
                    data[realKey] = [];
                }
                data[realKey].push(value);
            } else {
                data[key] = value;
            }
        }

        // 如果有实体ID，添加它
        if (config.entityId) {
            data.id = config.entityId;
        }

        return data;
    }

    // 保存表单
    function saveForm(callback) {
        if (state.isSaving) return;

        state.isSaving = true;

        // 收集表单数据
        const data = collectFormData();
        if (!data) {
            state.isSaving = false;
            console.error('无法收集表单数据');
            if (typeof callback === 'function') {
                callback({success: false, message: '无法收集表单数据'});
            }
            return;
        }

        // 获取CSRF令牌
        const token = document.querySelector(`input[name="${config.tokenName}"]`)?.value;
        if (!token) {
            console.warn('未找到CSRF令牌');
        }

        console.log('正在保存表单数据:', data);

        // 发送保存请求
        fetch(config.savingEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token || ''
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(responseData => {
            console.log('保存响应:', responseData);

            if (responseData.success) {
                markSaved();

                // 如果有回调，执行它
                if (typeof config.onAfterSave === 'function') {
                    config.onAfterSave(responseData);
                }
            } else {
                console.error('保存失败:', responseData.message);
                showStatusElement('保存失败');

                // 如果有错误回调，执行它
                if (typeof config.onSaveError === 'function') {
                    config.onSaveError(responseData);
                }
            }

            // 执行回调
            if (typeof callback === 'function') {
                callback(responseData);
            }
        })
        .catch(error => {
            console.error('保存请求错误:', error);
            showStatusElement('保存请求失败');

            // 如果有错误回调，执行它
            if (typeof config.onSaveError === 'function') {
                config.onSaveError({success: false, message: error.message});
            }

            // 执行回调
            if (typeof callback === 'function') {
                callback({success: false, message: error.message});
            }
        })
        .finally(() => {
            state.isSaving = false;
        });
    }

    // 手动保存
    function manualSave(callback) {
        saveForm(callback);
    }

    // 检查是否有未保存的更改
    function hasUnsavedChanges() {
        return state.hasUnsavedChanges;
    }

    // 重置状态
    function resetState() {
        state.hasUnsavedChanges = false;
        hideStatusElement();
    }

    // 返回公共API
    return {
        init,
        saveForm: manualSave,
        markUnsaved,
        markSaved,
        hasUnsavedChanges,
        stopAutosave,
        resumeAutosave,
        resetState
    };
})();

// 导出到全局作用域
window.Autosave = AutosaveSystem;