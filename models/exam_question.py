from models.db import db
class ExamQuestion(db.Model):
    __tablename__ = 'exam_question'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    order = db.Column(db.Integer, default=0)  # 题目在考试中的顺序
    score = db.Column(db.Float, nullable=False)  # 该题在此考试中的分值

    # 建立与考试和题目的关系
    exam = db.relationship('Exam', back_populates='questions')
    question = db.relationship('Question', back_populates='exams')

    __table_args__ = (
        db.UniqueConstraint('exam_id', 'question_id', name='uq_exam_question'),
    )

    def __repr__(self):
        return f'<ExamQuestion: Exam {self.exam_id}, Question {self.question_id}, Score {self.score}>'