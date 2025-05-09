from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
# 第六次修改
from models.category import Category
from models.code_template import CodeTemplate

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
    template_id = SelectField('测试代码模板', coerce=int, validators=[Optional()])
    reference_answer = TextAreaField('参考答案', validators=[Optional()],
                                     description='编程题参考答案（选填，考试结束后学生可见）')

    # 对于选择题的选项
    options = FieldList(FormField(OptionForm), min_entries=2, max_entries=10, render_kw={"class": "hidden-label"})
    # 第八次修改
    is_public = BooleanField('公开此题目', default=True)

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        # 动态加载分类列表
        self.category_id.choices = [(0, '-- 选择分类 --')] + [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]

        # 添加调试日志
        template_count = CodeTemplate.query.count()
        print(f"加载测试代码模板，数据库中共有 {template_count} 个模板")

        # 动态加载测试代码模板
        templates = CodeTemplate.query.order_by(CodeTemplate.name).all()
        template_choices = [(0, '-- 不使用模板 --')]
        for t in templates:
            template_choices.append((t.id, t.name))
            print(f"添加模板选项: ID={t.id}, 名称={t.name}")

        self.template_id.choices = template_choices

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

    def __init__(self, *args, **kwargs):
        super(QuestionSearchForm, self).__init__(*args, **kwargs)
        # 动态加载分类列表
        self.category_id.choices = [(0, '所有分类')] + [
            (c.id, c.name) for c in Category.query.order_by(Category.name).all()
        ]

class CodeTemplateForm(FlaskForm):
    name = StringField('模板名称', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('描述', validators=[Optional()])
    template_type = SelectField('模板类型',
                                choices=[
                                    ('function_test', '函数正确性测试'),
                                    ('data_processing', '数据处理测试'),
                                    ('statistics', '统计分析测试'),
                                    ('plotting', '图形参数测试'),
                                    ('custom', '自定义测试')
                                ],
                                validators=[DataRequired()])
    template_code = TextAreaField('模板代码', validators=[DataRequired()])


