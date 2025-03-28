# auth/utils.py
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(roles):
    """检查用户是否有所需角色的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)  # 没有权限
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 预定义的权限装饰器
def teacher_required(f):
    """要求教师或管理员权限的装饰器"""
    return role_required(['teacher', 'admin'])(f)

def admin_required(f):
    """要求管理员权限的装饰器"""
    return role_required(['admin'])(f)

def student_required(f):
    """要求学生权限的装饰器"""
    return role_required(['student'])(f)