from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
# 第六次修改
from models.category import Category

class OptionForm(FlaskForm):
    content = TextAreaField('选项内容', validators=[Optional()])
    is_correct = BooleanField('正确答案', default=False)
    order = IntegerField('排序', default=0)

    # 禁用CSRF保护，因为这是一个子表单
    class Meta:
        csrf = False


class QuestionForm(FlaskForm):
    title = StringField('题目标题', validators=[Optional(), Length(max=200)])
    content = TextAreaField('题目内容', validators=[DataRequired()])
    question_type = SelectField('题目类型',
                                choices=[('choice', '选择题'), ('fill_blank', '填空题'), ('programming', '编程题')],
                                validators=[DataRequired()])
    difficulty = SelectField('难度级别',
                             choices=[(1, '非常简单'), (2, '简单'), (3, '中等'), (4, '困难'), (5, '非常困难')],
                             validators=[DataRequired()],
                             coerce=int)
    score_default = IntegerField('默认分值', validators=[DataRequired(), NumberRange(min=1, max=100)], default=10)
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    tags = StringField('标签 (用逗号分隔)', validators=[Optional()])
    answer_template = TextAreaField('答案模板 (编程题)', validators=[Optional()])
    # 第六次修改：将standard_answer改为支持多答案
    standard_answer = TextAreaField('标准答案', validators=[Optional()],
                                    description='填空题可以设置多个答案，用分号(;)分隔，学生回答其中任意一个即视为正确')
    explanation = TextAreaField('题目解析', validators=[Optional()])
    test_code = TextAreaField('测试代码', validators=[Optional()])

    # 对于选择题的选项
    options = FieldList(FormField(OptionForm), min_entries=2, max_entries=10)

    # 第六次
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # 动态加载分类列表
        self.category_id.choices = [(0, '-- 选择分类 --')] + [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]

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

    # 第六次
    def __init__(self, *args, **kwargs):
        super(QuestionSearchForm, self).__init__(*args, **kwargs)
        # 动态加载分类列表
        self.category_id.choices = [(0, '所有分类')] + [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]