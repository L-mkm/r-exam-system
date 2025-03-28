from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 未登录用户重定向到登录页面
login_manager.login_message = '请登录后访问此页面'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))