/**
 * R语言考试系统 - 通用JavaScript工具函数
 */

// 显示通知提示
function showNotification(message, type = 'info', duration = 3000) {
  // 创建通知元素
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <div class="notification-message">${message}</div>
    </div>
    <button class="notification-close">&times;</button>
  `;

  // 添加到页面
  document.body.appendChild(notification);

  // 显示动画
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);

  // 关闭通知的事件
  const closeButton = notification.querySelector('.notification-close');
  closeButton.addEventListener('click', () => {
    notification.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  });

  // 自动关闭
  if (duration > 0) {
    setTimeout(() => {
      if (document.body.contains(notification)) {
        notification.classList.remove('show');
        setTimeout(() => {
          if (document.body.contains(notification)) {
            document.body.removeChild(notification);
          }
        }, 300);
      }
    }, duration);
  }

  return notification;
}

// 格式化时间函数
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    secs.toString().padStart(2, '0')
  ].join(':');
}

// 确认对话框
function confirmDialog(title, message, confirmText = '确定', cancelText = '取消') {
  return new Promise((resolve) => {
    // 创建模态对话框
    const modal = document.createElement('div');
    modal.className = 'confirm-dialog-overlay';
    modal.innerHTML = `
      <div class="confirm-dialog">
        <div class="confirm-dialog-header">
          <h3>${title}</h3>
        </div>
        <div class="confirm-dialog-body">
          <p>${message}</p>
        </div>
        <div class="confirm-dialog-footer">
          <button class="btn btn-secondary cancel-btn">${cancelText}</button>
          <button class="btn btn-primary confirm-btn">${confirmText}</button>
        </div>
      </div>
    `;

    // 添加到页面
    document.body.appendChild(modal);

    // 显示动画
    setTimeout(() => {
      modal.classList.add('show');
    }, 10);

    // 绑定事件
    const confirmBtn = modal.querySelector('.confirm-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');

    confirmBtn.addEventListener('click', () => {
      modal.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(modal);
        resolve(true);
      }, 300);
    });

    cancelBtn.addEventListener('click', () => {
      modal.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(modal);
        resolve(false);
      }, 300);
    });
  });
}

// 防抖函数
function debounce(func, wait = 300) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func.apply(this, args);
    }, wait);
  };
}

// 节流函数
function throttle(func, limit = 300) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// 格式化日期
function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }

  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

// 同步表单数据到对象
function syncFormData(formElement, dataObject) {
  const formData = new FormData(formElement);

  for (const [key, value] of formData.entries()) {
    if (key in dataObject) {
      dataObject[key] = value;
    }
  }

  return dataObject;
}

// 将对象数据同步到表单
function fillFormWithData(formElement, dataObject) {
  const elements = formElement.elements;

  for (let i = 0; i < elements.length; i++) {
    const element = elements[i];
    if (element.name && element.name in dataObject) {
      if (element.type === 'checkbox') {
        element.checked = !!dataObject[element.name];
      } else if (element.type === 'radio') {
        element.checked = element.value === dataObject[element.name].toString();
      } else {
        element.value = dataObject[element.name];
      }
    }
  }
}

// 复制文本到剪贴板
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('复制到剪贴板失败:', err);
    return false;
  }
}

// 生成唯一ID
function generateUniqueId(prefix = 'id') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// 导出所有函数
window.utils = {
  showNotification,
  formatTime,
  confirmDialog,
  debounce,
  throttle,
  formatDate,
  syncFormData,
  fillFormWithData,
  copyToClipboard,
  generateUniqueId
};