/**
 * 答案自动保存JavaScript
 */
class AnswerAutoSave {
    constructor(options) {
        this.saveUrl = options.saveUrl || '/student/save_answer';
        this.saveInterval = options.saveInterval || 30000; // 默认30秒
        this.statusElement = options.statusElement ? document.getElementById(options.statusElement) : null;
        this.onSaveSuccess = options.onSaveSuccess || function() {};
        this.onSaveError = options.onSaveError || function() {};

        this.timer = null;
        this.lastSaveTime = null;
        this.isSaving = false;
    }

    startAutoSave(getAnswerDataCallback) {
        this.stopAutoSave();

        this.timer = setInterval(() => {
            this.saveAnswer(getAnswerDataCallback);
        }, this.saveInterval);
    }

    stopAutoSave() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

saveAnswer(getAnswerDataCallback) {
    if (this.isSaving) {
        console.log('答案正在保存中，跳过本次保存请求');
        return;
    }

    // 获取答案数据
    let answerData = null;
    try {
        answerData = getAnswerDataCallback();
    } catch (e) {
        console.error('获取答案数据时出错:', e);
        if (this.statusElement) {
            this.statusElement.textContent = `获取答案数据出错: ${e.message}`;
        }
        this.onSaveError({ error: e.message });
        return;
    }

    // 检查答案数据是否有效
    if (!answerData) {
        console.warn('答案数据为空，跳过保存');
        return;
    }

    // 标记正在保存状态
    this.isSaving = true;

    // 更新状态元素
    if (this.statusElement) {
        this.statusElement.textContent = '正在保存...';
    }

    console.log(`正在保存答案: URL=${this.saveUrl}, 数据=`, answerData);

    // 使用fetch API发送请求
    fetch(this.saveUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // 添加CSRF令牌（如果页面中存在）
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(answerData),
        credentials: 'same-origin' // 包含cookies
    })
    .then(response => {
        // 检查HTTP状态码
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        this.isSaving = false;
        console.log('保存答案响应:', data);

        if (data.success) {
            this.lastSaveTime = data.saved_at;

            if (this.statusElement) {
                this.statusElement.textContent = `上次保存: ${this.lastSaveTime}`;
            }

            this.onSaveSuccess(data);
        } else {
            if (this.statusElement) {
                this.statusElement.textContent = `保存失败: ${data.message || '未知错误'}`;
            }

            this.onSaveError(data);
        }
    })
    .catch(error => {
        this.isSaving = false;
        console.error('保存答案时发生错误:', error);

        if (this.statusElement) {
            this.statusElement.textContent = `保存失败: ${error.message}`;
        }

        this.onSaveError({ error: error.message });
    });
}

    getLastSaveTime() {
        return this.lastSaveTime;
    }
}