from models.db import db


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # 建立分类的层级关系
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    # 与题目的关系
    questions = db.relationship('Question', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'