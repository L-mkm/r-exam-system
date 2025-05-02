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
        if (this.isSaving) return;

        const answerData = getAnswerDataCallback();
        if (!answerData) return;

        this.isSaving = true;

        if (this.statusElement) {
            this.statusElement.textContent = '正在保存...';
        }

        fetch(this.saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(answerData),
        })
        .then(response => response.json())
        .then(data => {
            this.isSaving = false;

            if (data.success) {
                this.lastSaveTime = data.saved_at;

                if (this.statusElement) {
                    this.statusElement.textContent = `上次保存: ${this.lastSaveTime}`;
                }

                this.onSaveSuccess(data);
            } else {
                if (this.statusElement) {
                    this.statusElement.textContent = '保存失败，请重试';
                }

                this.onSaveError(data);
            }
        })
        .catch(error => {
            this.isSaving = false;

            if (this.statusElement) {
                this.statusElement.textContent = '保存失败，请重试';
            }

            this.onSaveError({ error: error.message });
        });
    }

    getLastSaveTime() {
        return this.lastSaveTime;
    }
}