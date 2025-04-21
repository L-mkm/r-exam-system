from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class OptionForm(FlaskForm):
    content = TextAreaField('选项内容', validators=[DataRequired()])
    is_correct = BooleanField('是否正确答案', default=False)
    order = IntegerField('排序', default=0)

    # 禁用CSRF保护，因为这是一个子表单
    class Meta:
        csrf = False


class QuestionForm(FlaskForm):
    title = StringField('题目标题', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('题目内容', validators=[DataRequired()])
    question_type = SelectField('题目类型',
                                choices=[('choice', '选择题'), ('fill_blank', '填空题'), ('programming', '编程题')],
                                validators=[DataRequired()])
    difficulty = SelectField('难度级别',
                             choices=[(1, '非常简单'), (2, '简单'), (3, '中等'), (4, '困难'), (5, '非常困难')],
                             validators=[DataRequired()],
                             coerce=int)
    score_default = IntegerField('默认分值', validators=[DataRequired(), NumberRange(min=1, max=100)], default=10)
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    tags = StringField('标签 (用逗号分隔)', validators=[Optional()])
    answer_template = TextAreaField('答案模板 (编程题)', validators=[Optional()])
    standard_answer = TextAreaField('标准答案', validators=[DataRequired()])
    explanation = TextAreaField('题目解析', validators=[Optional()])

    # 对于选择题的选项
    options = FieldList(FormField(OptionForm), min_entries=2, max_entries=10)


class QuestionSearchForm(FlaskForm):
    keyword = StringField('关键词', validators=[Optional()])
    question_type = SelectField('题目类型',
                                choices=[('', '全部'), ('choice', '选择题'), ('fill_blank', '填空题'),
                                         ('programming', '编程题')],
                                validators=[Optional()])
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    tag = StringField('标签', validators=[Optional()])
    difficulty_min = SelectField('最低难度',
                                 choices=[(0, '不限'), (1, '非常简单'), (2, '简单'), (3, '中等'), (4, '困难'),
                                          (5, '非常困难')],
                                 validators=[Optional()],
                                 coerce=int,
                                 default=0)
    difficulty_max = SelectField('最高难度',
                                 choices=[(0, '不限'), (1, '非常简单'), (2, '简单'), (3, '中等'), (4, '困难'),
                                          (5, '非常困难')],
                                 validators=[Optional()],
                                 coerce=int,
                                 default=0)