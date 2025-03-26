from datetime import datetime
from models.db import db


class Score(db.Model):
    __tablename__ = 'score'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    total_score = db.Column(db.Float, default=0)  # 学生在此考试中的总得分
    submit_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_graded = db.Column(db.Boolean, default=False)  # 是否已评分

    # 建立与学生答案的关系
    student_answers = db.relationship('StudentAnswer', backref='score', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'exam_id', name='uq_student_exam'),
    )

    def __repr__(self):
        return f'<Score: Student {self.student_id}, Exam {self.exam_id}, Total Score {self.total_score}>'