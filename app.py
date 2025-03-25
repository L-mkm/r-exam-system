# 导入Flask类（创建Flask应用的基础）
# 1.第一次修改：增加render_template，方便后续接入index.html
# 2.第二次修改：增加request, redirect, url_for
from flask import Flask, render_template, request, redirect, url_for

# 创建Flask应用实例
# __name__是Python的一个特殊变量，代表当前模块的名称
# 这里作为应用名传递给Flask
app = Flask(__name__)

# 使用路由装饰器定义一个路由
# '@app.route('/')' 表示这个函数处理根URL的请求
# 当用户访问网站首页时，这个函数会被调用
@app.route('/')
def index():
    # 返回一个简单的HTML文本，浏览器会直接显示这段文本
    # 初始：return '<h1>Hello, World!</h1><p>欢迎使用R语言在线考试系统</p>'，
    # 第一次修改：渲染首页
    return render_template('index.html')

#第二次修改：def return渲染表单页面，不传递任何结果
@app.route('/form')
def form():
    # 渲染表单页面，不传递任何结果
    return render_template('form.html')

#第二次修改：
@app.route('/submit', methods=['POST'])
def submit():
    # 处理表单提交
    # request.form是一个字典，包含所有表单字段
    r_code = request.form.get('r_code')

    # 在实际应用中，这里会使用rpy2执行R代码
    # 但为了简单起见，这里只是模拟一个结果
    result = f"你输入的代码是: {r_code}"

    # 重新渲染表单页面，但这次传递结果
    return render_template('form.html', result=result)

# 检查是否直接运行此脚本（而非作为模块导入）
if __name__ == '__main__':
    # 启动应用，debug=True会在出错时显示详细信息和启动自动重载
    app.run(debug=True)