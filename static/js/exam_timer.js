/**
 * 考试计时器JavaScript
 */
class ExamTimer {
    constructor(elementId, remainingSeconds, onTimeUp) {
        this.element = document.getElementById(elementId);
        if (!this.element) {
            console.error(`计时器元素不存在: ${elementId}`);
            return;
        }

        // 确保剩余时间是有效的数字
        this.remainingSeconds = parseInt(remainingSeconds);
        if (isNaN(this.remainingSeconds) || this.remainingSeconds < 0) {
            console.error(`无效的剩余时间: ${remainingSeconds}`);
            this.remainingSeconds = 7200; // 默认2小时
        }

        this.onTimeUp = onTimeUp || function() {};
        this.interval = null;

        console.log(`计时器初始化完成, 剩余时间: ${this.remainingSeconds}秒`);
    }

    start() {
        // 确保不会重复启动
        this.stop();

        // 立即更新显示
        this.updateDisplay();

        console.log(`计时器启动, 剩余时间: ${this.remainingSeconds}秒`);

        // 设置定时器
        this.interval = setInterval(() => {
            this.remainingSeconds--;

            if (this.remainingSeconds <= 0) {
                console.log('计时器结束，时间到！');
                this.stop();
                this.onTimeUp();
                return;
            }

            this.updateDisplay();

            // 时间小于15分钟，显示警告颜色
            if (this.remainingSeconds < 900) {
                this.element.classList.add('timer-warning');
            }

            // 时间小于5分钟，显示危险颜色
            if (this.remainingSeconds < 300) {
                this.element.classList.remove('timer-warning');
                this.element.classList.add('timer-danger');
            }
        }, 1000);
    }

    stop() {
        if (this.interval) {
            console.log('停止计时器');
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    updateDisplay() {
        if (!this.element) return;

        const hours = Math.floor(this.remainingSeconds / 3600);
        const minutes = Math.floor((this.remainingSeconds % 3600) / 60);
        const seconds = this.remainingSeconds % 60;

        // 使用更安全的方式更新HTML内容
        try {
            this.element.innerHTML = `
                <span id="hours">${String(hours).padStart(2, '0')}</span>:
                <span id="minutes">${String(minutes).padStart(2, '0')}</span>:
                <span id="seconds">${String(seconds).padStart(2, '0')}</span>
            `;
        } catch (e) {
            console.error('更新计时器显示时出错:', e);
        }
    }

    getRemainingSeconds() {
        return this.remainingSeconds;
    }

    // 添加重设时间的方法
    setRemainingSeconds(seconds) {
        this.remainingSeconds = parseInt(seconds);
        if (isNaN(this.remainingSeconds) || this.remainingSeconds < 0) {
            console.error(`无效的剩余时间: ${seconds}`);
            return false;
        }
        this.updateDisplay();
        return true;
    }
}