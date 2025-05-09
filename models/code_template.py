# models/code_template.py
from datetime import datetime
from models.db import db


class CodeTemplate(db.Model):
    __tablename__ = 'code_template'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_code = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(50))  # 'function_test', 'data_processing', 'statistics', 'plotting'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<CodeTemplate {self.id}: {self.name}>'