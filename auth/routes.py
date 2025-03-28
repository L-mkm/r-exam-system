from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from auth.forms import LoginForm, RegistrationForm
from models.user import User
from models.db import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功！现在您可以登录了', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='注册', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('登录失败，请检查邮箱和密码', 'danger')

    return render_template('auth/login.html', title='登录', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('index'))