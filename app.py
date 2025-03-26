# 导入Flask类（创建Flask应用的基础）
# 1.第一次修改：增加render_template，方便后续接入index.html
# 2.第二次修改：增加request, redirect, url_for
from flask import Flask, render_template, request, redirect, url_for
# 第三次修改：
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# 第三次修改：创建数据库实例
db = SQLAlchemy()

# 初始化：创建Flask应用实例
# __name__是Python的一个特殊变量，代表当前模块的名称
# 这里作为应用名传递给Flask
# app = Flask(__name__)
# 第三次修改：修改为工厂模式，返回一个可配置的实例，使应用更灵活，更符合Python的模块化设计理念
def create_app():
    app = Flask(__name__)

    # 配置数据库
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'r_exam.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your_secret_key_here'  # 设置密钥用于会话安全

    # 初始化数据库
    db.init_app(app)

    # 导入所有模型
    from models.user import User
    from models.question import Question
    from models.exam import Exam
    from models.exam_question import ExamQuestion
    from models.score import Score
    from models.student_answer import StudentAnswer

    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 使用路由装饰器定义一个路由
    # '@app.route('/')' 表示这个函数处理根URL的请求
    # 当用户访问网站首页时，这个函数会被调用
    # 这里第三次修改跟着app对齐
    @app.route('/')
    def index():
        # 返回一个简单的HTML文本，浏览器会直接显示这段文本
        # 初始：return '<h1>Hello, World!</h1><p>欢迎使用R语言在线考试系统</p>'，
        # 第一次修改：渲染首页
        return render_template('index.html')

    #第二次修改：def return渲染表单页面，不传递任何结果
    # 这里第三次修改跟着app对齐，以下同
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

    return app

# 检查是否直接运行此脚本（而非作为模块导入）
if __name__ == '__main__':
    app = create_app()# 第三次修改，跟随工厂模式
    # 启动应用，debug=True会在出错时显示详细信息和启动自动重载
    app.run(debug=True)