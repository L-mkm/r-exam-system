from datetime import datetime
from models.db import db

class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'fill_blank', 'programming'
    answer_template = db.Column(db.Text)  # R代码模板（对于编程题）
    standard_answer = db.Column(db.Text)  # 标准答案
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 建立与考试的多对多关系，通过中间表
    exams = db.relationship('ExamQuestion', back_populates='question')

    # 学生答案关系
    student_answers = db.relationship('StudentAnswer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'<Question {self.id}: {self.title[:20]}...>'