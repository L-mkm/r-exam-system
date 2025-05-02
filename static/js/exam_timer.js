/**
 * 考试计时器JavaScript
 */
class ExamTimer {
    constructor(elementId, remainingSeconds, onTimeUp) {
        this.element = document.getElementById(elementId);
        this.remainingSeconds = remainingSeconds;
        this.onTimeUp = onTimeUp || function() {};
        this.interval = null;
    }

    start() {
        this.updateDisplay();

        this.interval = setInterval(() => {
            this.remainingSeconds--;

            if (this.remainingSeconds <= 0) {
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
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    updateDisplay() {
        const hours = Math.floor(this.remainingSeconds / 3600);
        const minutes = Math.floor((this.remainingSeconds % 3600) / 60);
        const seconds = this.remainingSeconds % 60;

        this.element.innerHTML = `
            <span id="hours">${String(hours).padStart(2, '0')}</span>:
            <span id="minutes">${String(minutes).padStart(2, '0')}</span>:
            <span id="seconds">${String(seconds).padStart(2, '0')}</span>
        `;
    }

    getRemainingSeconds() {
        return this.remainingSeconds;
    }
}