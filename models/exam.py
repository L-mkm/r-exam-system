from datetime import datetime
from models.db import db

class Exam(db.Model):
    __tablename__ = 'exam'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_score = db.Column(db.Float, default=0)  # 总分值
    is_published = db.Column(db.Boolean, default=False)  # 是否发布
    # 新增：是否为草稿
    is_draft = db.Column(db.Boolean, default=True)  # 默认为草稿状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    has_duration = db.Column(db.Boolean, default=False)
    duration_minutes = db.Column(db.Integer, default=120)  # 默认120分钟

    # 建立与题目的多对多关系，通过中间表
    questions = db.relationship('ExamQuestion', back_populates='exam')

    # 分数关系
    scores = db.relationship('Score', backref='exam', lazy='dynamic')

    def __repr__(self):
        return f'<Exam {self.id}: {self.title}>'

