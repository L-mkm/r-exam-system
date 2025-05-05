/**
 * 考试页面离开警告 - 改进版
 */
(() => {
    // 未保存更改标记
    let unsavedChanges = false;

    // 是否已提交考试
    let examSubmitted = false;

    // 设置未保存标记
    window.markUnsaved = function() {
        unsavedChanges = true;
    };

    // 清除未保存标记
    window.markSaved = function() {
        unsavedChanges = false;
    };

    // 标记考试已提交
    window.markExamSubmitted = function() {
        examSubmitted = true;
        unsavedChanges = false; // 提交后不再需要保存
    };

    // 监听表单元素变更
    function setupChangeListeners() {
        document.querySelectorAll('input, textarea, select').forEach(element => {
            element.addEventListener('change', window.markUnsaved);
            if (element.tagName === 'TEXTAREA') {
                element.addEventListener('input', window.markUnsaved);
            }
        });
    }

    // 页面离开提醒
    window.addEventListener('beforeunload', function(e) {
        // 如果已提交或没有未保存的更改，不显示提醒
        if (examSubmitted || !unsavedChanges) {
            return;
        }

        // 显示确认对话框
        e.preventDefault();
        e.returnValue = '您有未保存的答案，确定要离开吗？建议在离开前保存您的答案。';
        return e.returnValue;
    });

    // 页面加载完成后设置监听器
    document.addEventListener('DOMContentLoaded', () => {
        setupChangeListeners();

        // 监听提交按钮点击
        const submitButtons = document.querySelectorAll('#submit-exam-form button[type="submit"], #global-submit-button');
        submitButtons.forEach(button => {
            button.addEventListener('click', function() {
                window.markExamSubmitted();
            });
        });
    });
})();