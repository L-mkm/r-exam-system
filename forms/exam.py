from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, FloatField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import datetime, timedelta


class ExamForm(FlaskForm):
    title = StringField('考试标题', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('考试说明', validators=[Optional()])

    # 默认开始时间为当前时间后1小时
    start_time = DateTimeField('开始时间', validators=[DataRequired()],
                               default=lambda: datetime.now() + timedelta(hours=1),
                               format='%Y-%m-%dT%H:%M')

    # 默认结束时间为当前时间后3小时
    end_time = DateTimeField('结束时间', validators=[DataRequired()],
                             default=lambda: datetime.now() + timedelta(hours=3),
                             format='%Y-%m-%dT%H:%M')

    # 新增：考试时长（分钟）
    duration = IntegerField('考试时长（分钟）', validators=[Optional(), NumberRange(min=10)], default=120)

    # 新增：是否使用时长而不是结束时间
    use_duration = BooleanField('使用考试时长', default=False)

    total_score = FloatField('总分值', validators=[NumberRange(min=1)], default=100.0)
    is_published = BooleanField('立即发布', default=False)

    # 随机抽题设置
    use_random_questions = BooleanField('启用随机抽题', default=False)

    # 按题型和难度随机抽题
    choice_count = IntegerField('选择题数量', validators=[Optional(), NumberRange(min=0)], default=0)
    choice_difficulty_min = SelectField('选择题最低难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                   (3, '中等'), (4, '困难'), (5, '非常困难')],
                                        validators=[Optional()], coerce=int, default=0)
    choice_difficulty_max = SelectField('选择题最高难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                   (3, '中等'), (4, '困难'), (5, '非常困难')],
                                        validators=[Optional()], coerce=int, default=0)
    choice_score = FloatField('每题分值', validators=[Optional(), NumberRange(min=0)], default=5.0)

    fill_blank_count = IntegerField('填空题数量', validators=[Optional(), NumberRange(min=0)], default=0)
    fill_blank_difficulty_min = SelectField('填空题最低难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                       (3, '中等'), (4, '困难'), (5, '非常困难')],
                                            validators=[Optional()], coerce=int, default=0)
    fill_blank_difficulty_max = SelectField('填空题最高难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                       (3, '中等'), (4, '困难'), (5, '非常困难')],
                                            validators=[Optional()], coerce=int, default=0)
    fill_blank_score = FloatField('每题分值', validators=[Optional(), NumberRange(min=0)], default=10.0)

    programming_count = IntegerField('编程题数量', validators=[Optional(), NumberRange(min=0)], default=0)
    programming_difficulty_min = SelectField('编程题最低难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                        (3, '中等'), (4, '困难'), (5, '非常困难')],
                                             validators=[Optional()], coerce=int, default=0)
    programming_difficulty_max = SelectField('编程题最高难度', choices=[(0, '不限'), (1, '非常简单'), (2, '简单'),
                                                                        (3, '中等'), (4, '困难'), (5, '非常困难')],
                                             validators=[Optional()], coerce=int, default=0)
    programming_score = FloatField('每题分值', validators=[Optional(), NumberRange(min=0)], default=20.0)

    # 按分类抽题
    category_id = SelectField('题目分类', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        # 动态加载分类选项在实际使用时设置