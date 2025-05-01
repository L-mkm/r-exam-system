from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import func
from exams import exams_bp
from models.db import db
from models.exam import Exam
from models.exam_question import ExamQuestion
from models.question import Question
from models.category import Category
from forms.exam import ExamForm
import random
from datetime import datetime


@exams_bp.route('/')
@login_required
def index():
    """考试列表页面"""
    # 检查权限 - 学生只能看到可参加的考试，教师可以看到自己创建的考试
    if current_user.is_admin():
        exams = Exam.query.order_by(Exam.created_at.desc()).all()
    elif current_user.is_teacher():
        exams = Exam.query.filter_by(creator_id=current_user.id).order_by(Exam.created_at.desc()).all()
    else:  # 学生
        # 只显示已发布且在考试时间范围内的考试
        now = datetime.utcnow()
        exams = Exam.query.filter(
            Exam.is_published == True,
            Exam.start_time <= now,
            Exam.end_time >= now
        ).order_by(Exam.start_time).all()

    current_time = datetime.utcnow()
    return render_template('exams/index.html', exams=exams, current_time=current_time)


@exams_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建新考试"""
    # 检查权限 - 只有管理员和教师可以创建考试
    if not (current_user.is_admin() or current_user.is_teacher()):
        flash('您没有权限创建考试', 'danger')
        return redirect(url_for('exams.index'))

    form = ExamForm()

    # 填充分类下拉列表
    form.category_id.choices = [(0, '不限分类')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        # 创建考试
        exam = Exam(
            title=form.title.data,
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            total_score=form.total_score.data,
            is_published=form.is_published.data,
            creator_id=current_user.id
        )

        db.session.add(exam)
        db.session.commit()

        # 如果启用随机抽题
        if form.use_random_questions.data:
            # 抽取选择题
            if form.choice_count.data > 0:
                choice_questions = get_random_questions(
                    question_type='choice',
                    count=form.choice_count.data,
                    difficulty_min=form.choice_difficulty_min.data,
                    difficulty_max=form.choice_difficulty_max.data,
                    category_id=form.category_id.data if form.category_id.data > 0 else None,
                    score=form.choice_score.data
                )
                add_questions_to_exam(exam, choice_questions, form.choice_score.data)

            # 抽取填空题
            if form.fill_blank_count.data > 0:
                fill_blank_questions = get_random_questions(
                    question_type='fill_blank',
                    count=form.fill_blank_count.data,
                    difficulty_min=form.fill_blank_difficulty_min.data,
                    difficulty_max=form.fill_blank_difficulty_max.data,
                    category_id=form.category_id.data if form.category_id.data > 0 else None,
                    score=form.fill_blank_score.data
                )
                add_questions_to_exam(exam, fill_blank_questions, form.fill_blank_score.data)

            # 抽取编程题
            if form.programming_count.data > 0:
                programming_questions = get_random_questions(
                    question_type='programming',
                    count=form.programming_count.data,
                    difficulty_min=form.programming_difficulty_min.data,
                    difficulty_max=form.programming_difficulty_max.data,
                    category_id=form.category_id.data if form.category_id.data > 0 else None,
                    score=form.programming_score.data
                )
                add_questions_to_exam(exam, programming_questions, form.programming_score.data)

            # 更新考试总分
            update_exam_total_score(exam)

        flash('考试创建成功！', 'success')
        return redirect(url_for('exams.edit', id=exam.id))

    return render_template('exams/create.html', form=form)


@exams_bp.route('/<int:id>')
@login_required
def view(id):
    """查看考试详情"""
    exam = Exam.query.get_or_404(id)

    # 检查权限 - 只有创建者、管理员或考试已发布时学生可查看
    if not (current_user.is_admin() or exam.creator_id == current_user.id or
            (exam.is_published and current_user.is_student())):
        flash('您没有权限查看此考试', 'danger')
        return redirect(url_for('exams.index'))

    current_time = datetime.utcnow()
    return render_template('exams/view.html', exam=exam, current_time=current_time)


@exams_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑考试"""
    exam = Exam.query.get_or_404(id)

    # 检查权限 - 只有创建者和管理员可以编辑
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限编辑此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 如果考试已经开始，禁止编辑
    now = datetime.utcnow()
    if now > exam.start_time:
        flash('考试已经开始，无法编辑', 'danger')
        return redirect(url_for('exams.view', id=exam.id))

    form = ExamForm(obj=exam)

    # 填充分类下拉列表
    form.category_id.choices = [(0, '不限分类')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        # 更新考试信息
        exam.title = form.title.data
        exam.description = form.description.data
        exam.start_time = form.start_time.data
        exam.end_time = form.end_time.data
        exam.is_published = form.is_published.data

        db.session.commit()

        flash('考试信息更新成功！', 'success')
        return redirect(url_for('exams.view', id=exam.id))

    return render_template('exams/edit.html', form=form, exam=exam)


@exams_bp.route('/<int:id>/questions')
@login_required
def manage_questions(id):
    """管理考试题目"""
    exam = Exam.query.get_or_404(id)

    # 检查权限 - 只有创建者和管理员可以管理题目
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限管理此考试的题目', 'danger')
        return redirect(url_for('exams.index'))

    # 获取已添加到考试的题目
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam.id).order_by(ExamQuestion.order).all()

    # 获取可以添加的题目
    # 这里只显示一部分题目，实际应用中可能需要分页和搜索功能
    if current_user.is_admin():
        available_questions = Question.query.filter(
            ~Question.id.in_([eq.question_id for eq in exam_questions])
        ).limit(20).all()
    else:
        available_questions = Question.query.filter(
            ~Question.id.in_([eq.question_id for eq in exam_questions]),
            or_(
                Question.creator_id == current_user.id,
                Question.is_public == True
            )
        ).limit(20).all()

    return render_template('exams/manage_questions.html',
                           exam=exam,
                           exam_questions=exam_questions,
                           available_questions=available_questions)


@exams_bp.route('/<int:id>/add_question/<int:question_id>', methods=['POST'])
@login_required
def add_question(id, question_id):
    """添加题目到考试"""
    exam = Exam.query.get_or_404(id)
    question = Question.query.get_or_404(question_id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限修改此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 检查题目是否已在考试中
    existing = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first()
    if existing:
        flash('此题目已在考试中', 'warning')
        return redirect(url_for('exams.manage_questions', id=id))

    # 获取当前最大顺序号
    max_order = db.session.query(db.func.max(ExamQuestion.order)).filter_by(exam_id=id).scalar() or 0

    # 添加题目到考试
    exam_question = ExamQuestion(
        exam_id=id,
        question_id=question_id,
        order=max_order + 1,
        score=question.score_default
    )

    db.session.add(exam_question)
    db.session.commit()

    # 更新考试总分
    update_exam_total_score(exam)

    flash('题目已添加到考试', 'success')
    return redirect(url_for('exams.manage_questions', id=id))


@exams_bp.route('/<int:id>/remove_question/<int:question_id>', methods=['POST'])
@login_required
def remove_question(id, question_id):
    """从考试中移除题目"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限修改此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 查找并删除考试题目关联
    exam_question = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first_or_404()
    db.session.delete(exam_question)
    db.session.commit()

    # 更新考试总分
    update_exam_total_score(exam)

    # 重新排序剩余题目
    remaining_questions = ExamQuestion.query.filter_by(exam_id=id).order_by(ExamQuestion.order).all()
    for i, eq in enumerate(remaining_questions, 1):
        eq.order = i
    db.session.commit()

    flash('题目已从考试中移除', 'success')
    return redirect(url_for('exams.manage_questions', id=id))


@exams_bp.route('/<int:id>/update_question_score/<int:question_id>', methods=['POST'])
@login_required
def update_question_score(id, question_id):
    """更新考试题目分值"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限修改此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 获取新分值
    new_score = request.form.get('score', type=float)
    if not new_score or new_score <= 0:
        flash('请输入有效的分值', 'danger')
        return redirect(url_for('exams.manage_questions', id=id))

    # 更新分值
    exam_question = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first_or_404()
    exam_question.score = new_score
    db.session.commit()

    # 更新考试总分
    update_exam_total_score(exam)

    flash('题目分值已更新', 'success')
    return redirect(url_for('exams.manage_questions', id=id))


@exams_bp.route('/<int:id>/reorder_questions', methods=['POST'])
@login_required
def reorder_questions(id):
    """重新排序考试题目"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限修改此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 获取排序数据
    question_orders = request.get_json()
    if not question_orders:
        return {'success': False, 'message': '未收到排序数据'}, 400

    # 更新排序
    for question_id, order in question_orders.items():
        exam_question = ExamQuestion.query.filter_by(
            exam_id=id, question_id=int(question_id)).first()
        if exam_question:
            exam_question.order = order

    db.session.commit()

    return {'success': True}, 200


@exams_bp.route('/<int:id>/publish', methods=['POST'])
@login_required
def publish_exam(id):
    """发布考试"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限发布此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 检查考试是否有题目
    if len(exam.questions) == 0:
        flash('考试必须至少包含一道题目才能发布', 'danger')
        return redirect(url_for('exams.manage_questions', id=id))

    exam.is_published = True
    db.session.commit()

    flash('考试已发布', 'success')
    return redirect(url_for('exams.view', id=id))


@exams_bp.route('/<int:id>/unpublish', methods=['POST'])
@login_required
def unpublish_exam(id):
    """取消发布考试"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限修改此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 如果考试已经开始，不能取消发布
    now = datetime.utcnow()
    if now > exam.start_time:
        flash('考试已经开始，无法取消发布', 'danger')
        return redirect(url_for('exams.view', id=id))

    exam.is_published = False
    db.session.commit()

    flash('已取消发布考试', 'success')
    return redirect(url_for('exams.view', id=id))


# 辅助函数
def get_random_questions(question_type, count, difficulty_min=0, difficulty_max=0, category_id=None, score=None):
    """随机抽取题目"""
    query = Question.query.filter_by(question_type=question_type)

    # 根据难度筛选
    if difficulty_min > 0:
        query = query.filter(Question.difficulty >= difficulty_min)
    if difficulty_max > 0:
        query = query.filter(Question.difficulty <= difficulty_max)

    # 根据分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 获取可用题目列表
    available_questions = query.all()

    # 如果可用题目数量不足，返回全部
    if len(available_questions) <= count:
        return available_questions

    # 随机抽取指定数量的题目
    return random.sample(available_questions, count)


def add_questions_to_exam(exam, questions, score):
    """将题目添加到考试中"""
    # 获取当前最大顺序号
    max_order = db.session.query(db.func.max(ExamQuestion.order)).filter_by(exam_id=exam.id).scalar() or 0

    # 添加题目
    for i, question in enumerate(questions):
        # 检查题目是否已在考试中
        existing = ExamQuestion.query.filter_by(exam_id=exam.id, question_id=question.id).first()
        if not existing:
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question.id,
                order=max_order + i + 1,
                score=score or question.score_default
            )
            db.session.add(exam_question)

    db.session.commit()


def update_exam_total_score(exam):
    """更新考试总分"""
    # 计算所有题目的分值总和
    total_score = db.session.query(db.func.sum(ExamQuestion.score)).filter_by(exam_id=exam.id).scalar() or 0

    exam.total_score = total_score
    db.session.commit()