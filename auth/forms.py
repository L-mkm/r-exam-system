from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models.user import User, ROLE_STUDENT, ROLE_TEACHER, ROLE_ADMIN


class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('角色', choices=[
        (ROLE_STUDENT, '学生'),
        (ROLE_TEACHER, '教师'),
        (ROLE_ADMIN, '管理员')
    ], default=ROLE_STUDENT)
    submit = SubmitField('注册')

    # 自定义验证器
    def validate_username(self, username):
        # 第四次：-无用的修改
        from flask import current_app
        # 确保在请求上下文中执行查询
        with current_app.app_context():
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('该用户名已被使用，请选择不同的用户名')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册，请使用不同的邮箱')