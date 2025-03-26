from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# 定义用户角色的常量
ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'
ROLE_ADMIN = 'admin'

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 建立与其他表的关系
    questions = db.relationship('Question', backref='creator', lazy='dynamic')
    exams_created = db.relationship('Exam', backref='creator', lazy='dynamic')
    scores = db.relationship('Score', backref='student', lazy='dynamic')

    def __init__(self, username, email, password, role=ROLE_STUDENT):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        """设置密码散列"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def is_student(self):
        return self.role == ROLE_STUDENT

    def is_teacher(self):
        return self.role == ROLE_TEACHER

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def __repr__(self):
        return f'<User {self.username}, Role: {self.role}>'