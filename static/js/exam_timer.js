/**
 * 考试计时器JavaScript
 */
class ExamTimer {
    constructor(options) {
        // 配置选项
        this.options = Object.assign({
            // 默认值
            timerElementId: 'timer-display',      // 显示时间的元素ID
            hoursElementId: 'hours',              // 显示小时的元素ID
            minutesElementId: 'minutes',          // 显示分钟的元素ID
            secondsElementId: 'seconds',          // 显示秒数的元素ID
            warningElementId: 'exam-timer-warning', // 警告元素ID
            warningThreshold: 300,                // 警告阈值(秒)，默认5分钟
            dangerThreshold: 60,                  // 危险阈值(秒)，默认1分钟
            timeUpCallback: null,                 // 时间到回调函数
            warningCallback: null,                // 警告回调函数
            updateCallback: null,                 // 更新回调函数
            checkServerTime: false,               // 是否检查服务器时间
            serverTimeCheckInterval: 60,          // 服务器时间检查间隔(秒)
            serverTimeUrl: '/check-time',         // 服务器时间检查URL
            examId: null,                         // 考试ID
            autoSubmitUrl: null                   // 自动提交URL
        }, options);

        // 初始化元素引用
        this.timerElement = document.getElementById(this.options.timerElementId);
        this.hoursElement = document.getElementById(this.options.hoursElementId);
        this.minutesElement = document.getElementById(this.options.minutesElementId);
        this.secondsElement = document.getElementById(this.options.secondsElementId);
        this.warningElement = document.getElementById(this.options.warningElementId);

        // 初始化状态
        this.remainingSeconds = this.options.remainingSeconds || 0;
        this.isRunning = false;
        this.timerInterval = null;
        this.serverCheckInterval = null;
        this.hasWarned = false;
        this.hasDanger = false;

        // 记录上一次同步时间
        this.lastSyncTime = Date.now();

        // 初始日志
        console.log(`计时器初始化完成，剩余时间：${this.formatTime(this.remainingSeconds)}`);
    }

    /**
     * 开始计时器
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;

        // 立即更新显示
        this.updateDisplay();

        // 设置计时器
        this.timerInterval = setInterval(() => this.tick(), 1000);

        // 如果需要定期检查服务器时间
        if (this.options.checkServerTime && this.options.examId) {
            this.serverCheckInterval = setInterval(() => {
                this.syncWithServerTime();
            }, this.options.serverTimeCheckInterval * 1000);
        }

        console.log(`计时器已启动，剩余时间：${this.formatTime(this.remainingSeconds)}`);
    }

    /**
     * 停止计时器
     */
    stop() {
        if (!this.isRunning) return;

        clearInterval(this.timerInterval);
        if (this.serverCheckInterval) {
            clearInterval(this.serverCheckInterval);
        }

        this.timerInterval = null;
        this.serverCheckInterval = null;
        this.isRunning = false;

        console.log(`计时器已停止，剩余时间：${this.formatTime(this.remainingSeconds)}`);
    }

    /**
     * 计时器滴答
     */
    tick() {
        // 计算实际流逝的时间（避免因浏览器休眠等导致的计时不准）
        const now = Date.now();
        const elapsed = Math.floor((now - this.lastSyncTime) / 1000);
        this.lastSyncTime = now;

        // 减少剩余时间（至少减1秒，即使实际流逝时间小于1秒）
        this.remainingSeconds -= Math.max(1, elapsed);

        // 确保不为负
        if (this.remainingSeconds <= 0) {
            this.remainingSeconds = 0;
            this.timeUp();
            return;
        }

        // 更新显示
        this.updateDisplay();

        // 检查是否需要显示警告
        this.checkWarnings();

        // 调用更新回调
        if (typeof this.options.updateCallback === 'function') {
            this.options.updateCallback(this.remainingSeconds);
        }
    }

    /**
     * 更新显示
     */
    updateDisplay() {
        if (!this.hoursElement || !this.minutesElement || !this.secondsElement) return;

        const { hours, minutes, seconds } = this.getTimeComponents(this.remainingSeconds);

        this.hoursElement.textContent = this.padZero(hours);
        this.minutesElement.textContent = this.padZero(minutes);
        this.secondsElement.textContent = this.padZero(seconds);
    }

    /**
     * 检查警告条件
     */
    checkWarnings() {
        // 警告阈值检查
        if (this.remainingSeconds <= this.options.warningThreshold && !this.hasWarned) {
            this.hasWarned = true;
            if (this.warningElement) {
                this.warningElement.style.display = 'block';
            }
            if (this.timerElement) {
                this.timerElement.classList.remove('alert-info');
                this.timerElement.classList.add('alert-warning');
            }
            if (typeof this.options.warningCallback === 'function') {
                this.options.warningCallback(this.remainingSeconds);
            }
            console.log(`警告：考试剩余时间不足${Math.floor(this.options.warningThreshold / 60)}分钟！`);
        }

        // 危险阈值检查
        if (this.remainingSeconds <= this.options.dangerThreshold && !this.hasDanger) {
            this.hasDanger = true;
            if (this.timerElement) {
                this.timerElement.classList.remove('alert-warning');
                this.timerElement.classList.add('alert-danger');
            }
            console.log(`警告：考试剩余时间不足${Math.floor(this.options.dangerThreshold / 60)}分钟！`);
        }
    }

    /**
     * 时间到处理
     */
    timeUp() {
        this.stop();

        if (this.timerElement) {
            this.timerElement.classList.remove('alert-warning', 'alert-info');
            this.timerElement.classList.add('alert-danger');
        }

        // 更新显示为00:00:00
        if (this.hoursElement && this.minutesElement && this.secondsElement) {
            this.hoursElement.textContent = '00';
            this.minutesElement.textContent = '00';
            this.secondsElement.textContent = '00';
        }

        console.log('考试时间结束！');

        // 调用时间到回调
        if (typeof this.options.timeUpCallback === 'function') {
            this.options.timeUpCallback();
        }

        // 如果配置了自动提交
        if (this.options.autoSubmitUrl && this.options.examId) {
            this.autoSubmitExam();
        }
    }

    /**
     * 自动提交考试
     */
    autoSubmitExam() {
        if (!this.options.autoSubmitUrl || !this.options.examId) return;

        console.log('正在自动提交考试...');

        // 显示提交中提示
        const submitMessageElement = document.createElement('div');
        submitMessageElement.className = 'alert alert-warning mt-3';
        submitMessageElement.innerHTML = '<strong>注意：</strong> 考试时间已结束，系统正在自动提交您的答案...';
        document.body.appendChild(submitMessageElement);

        // 创建表单并提交
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = this.options.autoSubmitUrl.replace(':id', this.options.examId);

        // 添加CSRF令牌（如果有）
        const csrfElement = document.querySelector('meta[name="csrf-token"]');
        if (csrfElement) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrf_token';
            csrfInput.value = csrfElement.getAttribute('content');
            form.appendChild(csrfInput);
        }

        document.body.appendChild(form);
        form.submit();
    }

    /**
     * 与服务器时间同步
     */
    syncWithServerTime() {
        if (!this.options.checkServerTime || !this.options.examId) return;

        fetch(`${this.options.serverTimeUrl}/${this.options.examId}`)
            .then(response => response.json())
            .then(data => {
                if (data.remaining_seconds !== undefined) {
                    // 记录时间差异
                    const diff = Math.abs(this.remainingSeconds - data.remaining_seconds);
                    console.log(`服务器时间同步：本地剩余${this.remainingSeconds}秒，服务器剩余${data.remaining_seconds}秒，差异${diff}秒`);

                    // 如果差异超过30秒，更新本地时间
                    if (diff > 30) {
                        this.remainingSeconds = data.remaining_seconds;
                        this.updateDisplay();
                    }

                    // 如果考试已结束，强制结束计时
                    if (data.status === 'ended') {
                        this.timeUp();
                    }
                }
            })
            .catch(error => {
                console.error('服务器时间同步失败:', error);
            });
    }

    /**
     * 获取时间组件（小时、分钟、秒）
     */
    getTimeComponents(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        return { hours, minutes, seconds };
    }

    /**
     * 格式化时间
     */
    formatTime(totalSeconds) {
        const { hours, minutes, seconds } = this.getTimeComponents(totalSeconds);
        return `${this.padZero(hours)}:${this.padZero(minutes)}:${this.padZero(seconds)}`;
    }

    /**
     * 数字前补零
     */
    padZero(num) {
        return num.toString().padStart(2, '0');
    }

    /**
     * 获取剩余时间（秒）
     */
    getRemainingSeconds() {
        return this.remainingSeconds;
    }

    /**
     * 设置剩余时间（秒）
     */
    setRemainingSeconds(seconds) {
        const newSeconds = parseInt(seconds, 10);
        if (isNaN(newSeconds) || newSeconds < 0) {
            console.error(`无效的剩余时间: ${seconds}`);
            return false;
        }

        this.remainingSeconds = newSeconds;
        this.updateDisplay();

        // 重置警告状态
        if (newSeconds > this.options.warningThreshold) {
            this.hasWarned = false;
            if (this.warningElement) {
                this.warningElement.style.display = 'none';
            }
        }

        if (newSeconds > this.options.dangerThreshold) {
            this.hasDanger = false;
        }

        if (this.timerElement) {
            this.timerElement.className = 'alert alert-info';
        }

        return true;
    }
}