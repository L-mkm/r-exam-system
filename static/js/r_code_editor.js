// r_code_editor.js - R语言代码编辑器交互脚本

class RCodeEditor {
    constructor(config) {
        this.targetElement = config.targetElement || 'answer_content';
        this.container = null;
        this.textarea = null;
        this.lineNumbers = null;
        this.originalTextarea = document.getElementById(this.targetElement);

        if (!this.originalTextarea) {
            console.error('目标textarea元素不存在');
            return;
        }

        this.init();
    }

    init() {
        // 创建编辑器容器
        this.createEditorContainer();

        // 隐藏原始textarea
        this.originalTextarea.style.display = 'none';

        // 添加行号和事件监听
        this.setupLineNumbers();
        this.setupEvents();

        // 初始化语法高亮提示
        this.setupSyntaxHelpers();

        // 把初始内容从原始textarea复制到新编辑器
        if (this.originalTextarea.value) {
            this.textarea.value = this.originalTextarea.value;
            this.updateLineNumbers();
        }
    }

    createEditorContainer() {
        // 创建编辑器容器
        this.container = document.createElement('div');
        this.container.className = 'r-code-editor';

        // 标题栏
        const header = document.createElement('div');
        header.className = 'r-code-editor-header';
        header.innerHTML = `
            <div class="r-code-editor-title">
                <i class="bi bi-code-square"></i>
                <span>R代码编辑器</span>
            </div>
            <div class="r-code-editor-controls">
                <button type="button" class="r-code-editor-btn r-format-btn" title="格式化代码">
                    <i class="bi bi-text-indent-left"></i>
                </button>
                <button type="button" class="r-code-editor-btn r-clear-btn" title="清空代码">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        // 编辑区域 - 使用表格布局确保行号与代码同步
        const content = document.createElement('div');
        content.className = 'r-code-editor-content';

        // 使用表格方式创建编辑器和行号
        const table = document.createElement('table');
        table.className = 'r-code-table';
        table.style.width = '100%';
        table.style.height = '100%';
        table.style.borderCollapse = 'collapse';

        const row = document.createElement('tr');

        // 行号单元格
        const lineNumbersCell = document.createElement('td');
        lineNumbersCell.className = 'r-code-line-numbers-cell';
        lineNumbersCell.style.width = '40px';
        lineNumbersCell.style.backgroundColor = '#f5f7fa';
        lineNumbersCell.style.borderRight = '1px solid #e9ecef';
        lineNumbersCell.style.verticalAlign = 'top';

        this.lineNumbers = document.createElement('div');
        this.lineNumbers.className = 'r-code-line-numbers';
        this.lineNumbers.style.padding = '1rem 0';
        this.lineNumbers.style.fontFamily = "'JetBrains Mono', 'Fira Code', Consolas, monospace";
        this.lineNumbers.style.fontSize = '0.9rem';
        this.lineNumbers.style.color = '#a0aec0';
        this.lineNumbers.style.textAlign = 'right';
        this.lineNumbers.style.userSelect = 'none';

        // 创建初始行号
        for (let i = 1; i <= 10; i++) {
            const lineNumber = document.createElement('div');
            lineNumber.className = 'r-code-line-number';
            lineNumber.style.padding = '0 0.5rem';
            lineNumber.style.lineHeight = '1.5';
            lineNumber.textContent = i;
            this.lineNumbers.appendChild(lineNumber);
        }

        lineNumbersCell.appendChild(this.lineNumbers);

        // 文本编辑单元格
        const editorCell = document.createElement('td');
        editorCell.className = 'r-code-editor-cell';
        editorCell.style.verticalAlign = 'top';

        this.textarea = document.createElement('textarea');
        this.textarea.className = 'r-code-textarea';
        this.textarea.id = 'r-code-textarea';
        this.textarea.style.width = '100%';
        this.textarea.style.height = '300px';
        this.textarea.style.padding = '1rem';
        this.textarea.style.fontFamily = "'JetBrains Mono', 'Fira Code', Consolas, monospace";
        this.textarea.style.fontSize = '0.9rem';
        this.textarea.style.lineHeight = '1.5';
        this.textarea.style.border = 'none';
        this.textarea.style.resize = 'none';
        this.textarea.style.backgroundColor = '#fcfcfc';
        this.textarea.spellcheck = false;
        this.textarea.autocomplete = 'off';
        this.textarea.wrap = 'off';

        editorCell.appendChild(this.textarea);

        // 组装表格
        row.appendChild(lineNumbersCell);
        row.appendChild(editorCell);
        table.appendChild(row);
        content.appendChild(table);

        // 代码提示
        const hints = document.createElement('div');
        hints.className = 'r-code-hints';
        hints.innerHTML = '提示: 使用<span class="r-keyword">Tab</span>键缩进代码, <span class="r-function">Ctrl+/</span>添加注释';

        // 组装编辑器
        this.container.appendChild(header);
        this.container.appendChild(content);
        this.container.appendChild(hints);

        // 插入到原始textarea之前
        this.originalTextarea.parentNode.insertBefore(this.container, this.originalTextarea);
    }

    setupLineNumbers() {
        // 初始化时显示10个空行号
        for (let i = 1; i <= 10; i++) {
            const lineNumber = document.createElement('div');
            lineNumber.className = 'r-code-line-number';
            lineNumber.textContent = i;
            this.lineNumbers.appendChild(lineNumber);
        }

        // 监听滚动同步
        this.textarea.addEventListener('scroll', () => {
            this.lineNumbers.scrollTop = this.textarea.scrollTop;
        });
    }

    updateLineNumbers() {
        // 清空行号
        this.lineNumbers.innerHTML = '';

        // 计算行数
        const lineCount = this.textarea.value.split('\n').length;
        const maxLines = Math.max(lineCount, 10); // 至少显示10行

        // 创建行号
        for (let i = 1; i <= maxLines; i++) {
            const lineNumber = document.createElement('div');
            lineNumber.className = 'r-code-line-number';
            lineNumber.style.padding = '0 0.5rem';
            lineNumber.style.lineHeight = '1.5';
            lineNumber.textContent = i;
            this.lineNumbers.appendChild(lineNumber);
        }
    }

    setupEvents() {
        // 同步内容到原始textarea
        this.textarea.addEventListener('input', () => {
            this.originalTextarea.value = this.textarea.value;
            this.updateLineNumbers();

            // 触发原始textarea的input事件，以便自动保存功能继续工作
            const event = new Event('input', { bubbles: true });
            this.originalTextarea.dispatchEvent(event);
        });

        // Tab键处理
        this.textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();

                const start = this.textarea.selectionStart;
                const end = this.textarea.selectionEnd;
                const value = this.textarea.value;

                // 插入制表符(2个空格)
                this.textarea.value = value.substring(0, start) + '  ' + value.substring(end);

                // 将光标移到插入的制表符之后
                this.textarea.selectionStart = this.textarea.selectionEnd = start + 2;

                // 触发input事件以更新行号和同步内容
                this.textarea.dispatchEvent(new Event('input'));
            }
        });

        // 格式化代码按钮
        this.container.querySelector('.r-format-btn').addEventListener('click', () => {
            this.formatCode();
        });

        // 清空代码按钮
        this.container.querySelector('.r-clear-btn').addEventListener('click', () => {
            if (confirm('确定要清空所有代码吗？')) {
                this.textarea.value = '';
                this.textarea.dispatchEvent(new Event('input'));
            }
        });
    }

    setupSyntaxHelpers() {
        // 这里可以实现简单的语法高亮
        // 完整的语法高亮需要使用专业库如CodeMirror或Prism.js
    }

    formatCode() {
        // 简单的格式化功能
        let code = this.textarea.value;

        // 1. 调整空格 - 操作符前后添加空格
        code = code.replace(/([=+\-*/<>])/g, ' $1 ');

        // 2. 修复多余空格
        code = code.replace(/\s+/g, ' ');

        // 3. 修复括号空格
        code = code.replace(/\(\s+/g, '(');
        code = code.replace(/\s+\)/g, ')');

        // 4. 修复逗号空格
        code = code.replace(/,\s*/g, ', ');

        // 5. 处理行缩进 (简单实现)
        let lines = code.split('\n');
        let indentLevel = 0;

        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();

            // 减少缩进级别
            if (line.match(/^\}/) && indentLevel > 0) {
                indentLevel--;
            }

            // 添加缩进
            lines[i] = '  '.repeat(indentLevel) + line;

            // 增加缩进级别
            if (line.match(/\{$/)) {
                indentLevel++;
            }
        }

        this.textarea.value = lines.join('\n');
        this.textarea.dispatchEvent(new Event('input'));
    }
}

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 监听题目变化，仅在编程题时初始化代码编辑器
    const questionTypeElement = document.getElementById('question-type-badge');
    const answerContainer = document.getElementById('answer-container');

    if (questionTypeElement && answerContainer) {
        // 创建观察器以监听题目类型变化
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'characterData' || mutation.type === 'childList') {
                    const questionType = questionTypeElement.textContent.trim();

                    // 检查是否已经有编辑器
                    const existingEditor = document.querySelector('.r-code-editor');

                    if (questionType === '编程题') {
                        // 如果是编程题且还没有编辑器，则初始化编辑器
                        if (!existingEditor && answerContainer.style.display !== 'none') {
                            new RCodeEditor({
                                targetElement: 'answer_content'
                            });
                        }
                    } else if (existingEditor) {
                        // 如果不是编程题但有编辑器，则移除编辑器并显示原始textarea
                        existingEditor.remove();
                        document.getElementById('answer_content').style.display = 'block';
                    }
                }
            });
        });

        // 配置观察器
        observer.observe(questionTypeElement, {
            characterData: true,
            childList: true,
            subtree: true
        });

        // 立即检查当前题目类型
        if (questionTypeElement.textContent.trim() === '编程题' &&
            answerContainer.style.display !== 'none') {
            new RCodeEditor({
                targetElement: 'answer_content'
            });
        }
    }
});

// 定义全局对象，以便从外部访问和控制代码编辑器
window.RCodeEditor = RCodeEditor;