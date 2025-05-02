from flask_wtf import FlaskForm
from wtforms import TextAreaField, HiddenField, StringField, SelectMultipleField
from wtforms.validators import Optional


class StudentAnswerForm(FlaskForm):
    """学生答题表单"""
    question_id = HiddenField('题目ID')
    score_id = HiddenField('得分ID')
    answer_content = TextAreaField('答案', validators=[Optional()])