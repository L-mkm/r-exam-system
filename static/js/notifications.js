/**
 * 统一的通知和确认对话框系统
 * 用于替代原生的alert和confirm，提供更一致的用户体验
 */

// 初始化通知系统
const NotificationSystem = (function() {
    // 通知容器
    let container = null;

    // 创建通知容器
    function createContainer() {
        if (container) return container;

        container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 9999; max-width: 350px;';
        document.body.appendChild(container);

        return container;
    }

    // 创建通知元素
    function createNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} fade-in`;
        notification.style.cssText = `
            background-color: #fff;
            box-shadow: 0 .125rem .25rem rgba(0,0,0,.075);
            border-radius: .375rem;
            padding: 1rem;
            margin-bottom: 0.75rem;
            position: relative;
            border-left: 4px solid;
            opacity: 0;
            transform: translateX(20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
        `;

        // 设置边框颜色
        switch (type) {
            case 'success':
                notification.style.borderLeftColor = '#28a745';
                break;
            case 'warning':
                notification.style.borderLeftColor = '#ffc107';
                break;
            case 'error':
                notification.style.borderLeftColor = '#dc3545';
                break;
            default:
                notification.style.borderLeftColor = '#17a2b8';
        }

        // 通知内容
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" style="position: absolute; top: 0.5rem; right: 0.5rem; border: none; background: none; cursor: pointer; font-size: 1.25rem;">&times;</button>
        `;

        // 关闭按钮事件
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            closeNotification(notification);
        });

        // 返回创建的通知
        return notification;
    }

    // 关闭通知
    function closeNotification(notification) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(20px)';

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    // 显示通知
    function showNotification(message, type = 'info', duration = 3000) {
        const cont = createContainer();
        const notification = createNotification(message, type, duration);

        cont.appendChild(notification);

        // 显示动画
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);

        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                closeNotification(notification);
            }, duration);
        }

        return notification;
    }

    // 创建确认对话框
    function createConfirmDialog(options = {}) {
        return new Promise((resolve) => {
            const defaults = {
                title: '确认操作',
                message: '您确定要执行此操作吗？',
                confirmText: '确定',
                cancelText: '取消',
                type: 'primary', // primary, danger, warning, success
                dialogClass: ''
            };

            const settings = {...defaults, ...options};

            // 创建模态框
            const modal = document.createElement('div');
            modal.className = `modal confirm-modal fade ${settings.dialogClass}`;
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-hidden', 'true');

            const buttonTypeClass = settings.type === 'danger' ? 'btn-danger' : (
                settings.type === 'warning' ? 'btn-warning' : (
                    settings.type === 'success' ? 'btn-success' : 'btn-primary'
                )
            );

            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${settings.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>${settings.message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary cancel-btn" data-bs-dismiss="modal">${settings.cancelText}</button>
                            <button type="button" class="btn ${buttonTypeClass} confirm-btn">${settings.confirmText}</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // 初始化模态框
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();

            // 确认按钮事件
            const confirmBtn = modal.querySelector('.confirm-btn');
            confirmBtn.addEventListener('click', () => {
                modalInstance.hide();
                resolve(true);

                // 移除模态框
                modal.addEventListener('hidden.bs.modal', () => {
                    document.body.removeChild(modal);
                });
            });

            // 取消按钮事件
            const cancelBtn = modal.querySelector('.cancel-btn');
            cancelBtn.addEventListener('click', () => {
                resolve(false);
            });

            // 关闭按钮事件
            const closeBtn = modal.querySelector('.btn-close');
            closeBtn.addEventListener('click', () => {
                resolve(false);
            });

            // 关闭后移除模态框
            modal.addEventListener('hidden.bs.modal', () => {
                setTimeout(() => {
                    if (document.body.contains(modal)) {
                        document.body.removeChild(modal);
                    }
                }, 300);
            });
        });
    }

    // 返回公共API
    return {
        success: (message, duration) => showNotification(message, 'success', duration),
        info: (message, duration) => showNotification(message, 'info', duration),
        warning: (message, duration) => showNotification(message, 'warning', duration),
        error: (message, duration) => showNotification(message, 'error', duration),
        confirm: createConfirmDialog
    };
})();

// 导出到全局作用域
window.Notify = NotificationSystem;