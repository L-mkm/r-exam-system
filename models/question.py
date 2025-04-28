from datetime import datetime
from models.db import db
# 第五次修改：
from sqlalchemy.ext.associationproxy import association_proxy

class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'choice', 'fill_blank', 'programming'
    # 第五次修改
    difficulty = db.Column(db.Integer, default=3)  # 难度级别：1-5
    score_default = db.Column(db.Integer, default=10)  # 默认分值
    answer_template = db.Column(db.Text)  # R代码模板（对于编程题）
    standard_answer = db.Column(db.Text)  # 标准答案
    # 5+
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 5+
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # 第七次修改
    test_code = db.Column(db.Text)  # R测试代码（对于编程题）

    # 第五次修改
    # 类别和标签关系
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    tags = db.relationship('Tag', secondary='question_tag', backref=db.backref('questions', lazy='dynamic'))

    # 选择题选项
    options = db.relationship('QuestionOption', backref='question', lazy='dynamic', cascade='all, delete-orphan')

    # 建立与考试的多对多关系，通过中间表
    exams = db.relationship('ExamQuestion', back_populates='question')

    # 学生答案关系
    student_answers = db.relationship('StudentAnswer', backref='question', lazy='dynamic')

    # 第五次修改
    # 通过代理访问考试
    exam_list = association_proxy('exams', 'exam')

    def __repr__(self):
        return f'<Question {self.id}: {self.title[:20]}...>'

    # 第五次修改
    def is_choice(self):
        return self.question_type == 'choice'

    def is_fill_blank(self):
        return self.question_type == 'fill_blank'

    def is_programming(self):
        return self.question_type == 'programming'

    @property
    def correct_options(self):
        """获取所有正确选项"""
        if not self.is_choice():
            return []
        return [opt for opt in self.options if opt.is_correct]