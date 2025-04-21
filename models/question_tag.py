from models.db import db

# 题目和标签的多对多关联表
question_tag = db.Table('question_tag',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)