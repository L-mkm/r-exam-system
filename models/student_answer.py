from datetime import datetime
from models.db import db

class StudentAnswer(db.Model):
    __tablename__ = 'student_answer'

    id = db.Column(db.Integer, primary_key=True)
    score_id = db.Column(db.Integer, db.ForeignKey('score.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_content = db.Column(db.Text)  # 学生的答案内容
    points_earned = db.Column(db.Float, default=0)  # 该题得分
    feedback = db.Column(db.Text)  # 教师反馈
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudentAnswer: Score {self.score_id}, Question {self.question_id}, Points {self.points_earned}>'