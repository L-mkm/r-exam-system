from models.db import db


class QuestionOption(db.Model):
    __tablename__ = 'question_option'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 选项内容
    is_correct = db.Column(db.Boolean, default=False)  # 是否为正确选项
    order = db.Column(db.Integer, default=0)  # 选项顺序

    def __repr__(self):
        return f'<Option {self.id} for Question {self.question_id}>'