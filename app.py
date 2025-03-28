# 导入Flask类（创建Flask应用的基础）
# 1.第一次修改：增加render_template，方便后续接入index.html
# 2.第二次修改：增加request, redirect, url_for
# 3.第四次修改：增加flash
from flask import Flask, render_template, request, redirect, url_for, flash
# 第三次修改：
# 第四次修改：数据库实例重复，删除了下面这列
# from flask_sqlalchemy import SQLAlchemy
# 第四次修改：增加了下面一行
from flask_login import LoginManager, current_user, login_required
from datetime import datetime
import os
from models.db import db  # 导入已存在的SQLAlchemy实例，不要再创建新的

# 第三次修改：创建数据库实例
# 第四次修改：删除了这里
# db = SQLAlchemy()

# 第四次修改：创建登录管理器
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请登录后访问'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

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
    # 第四次修改：初始化
    login_manager.init_app(app)

    # 第四次修改：注册认证蓝图
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 创建数据库表（第四次修改：因为bug，这段先修改试试）
    #with app.app_context():
        ## 导入所有模型
        # from models.user import User
        # from models.question import Question
        # from models.exam import Exam
        # from models.exam_question import ExamQuestion
        # from models.score import Score
        # from models.student_answer import StudentAnswer

    # 上段改成了：
    def load_models():
        from models.user import User
        from models.question import Question
        from models.exam import Exam
        from models.exam_question import ExamQuestion
        from models.score import Score
        from models.student_answer import StudentAnswer
        return [User, Question, Exam, ExamQuestion, Score, StudentAnswer]

    with app.app_context():
        models = load_models()
        print(f"加载了 {len(models)} 个数据库模型")
        db.create_all()

        ## 创建所有表
        # db.create_all()

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
    @login_required  # 第四次修改：添加登录要求
    def form():
        # 渲染表单页面，不传递任何结果
        return render_template('form.html')

    #第二次修改：
    @app.route('/submit', methods=['POST'])
    @login_required  # 第四次修改：添加登录要求
    def submit():
        # 处理表单提交
        # request.form是一个字典，包含所有表单字段
        r_code = request.form.get('r_code')

        # 在实际应用中，这里会使用rpy2执行R代码
        # 但为了简单起见，这里只是模拟一个结果
        result = f"你输入的代码是: {r_code}"

        # 重新渲染表单页面，但这次传递结果
        return render_template('form.html', result=result)

    # 第四次修改：+错误处理
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

# 检查是否直接运行此脚本（而非作为模块导入）
if __name__ == '__main__':
    app = create_app()# 第三次修改，跟随工厂模式
    # 启动应用，debug=True会在出错时显示详细信息和启动自动重载
    app.run(debug=True)