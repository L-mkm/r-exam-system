from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from questions import questions_bp
from models.db import db
from models.question import Question
from models.question_option import QuestionOption
from models.category import Category
from models.tag import Tag
# 第六次：debug
from models.exam import Exam
from forms.question import QuestionForm, QuestionSearchForm


@questions_bp.route('/')
@login_required
def index():
    """题目列表页面"""
    search_form = QuestionSearchForm()

    # 填充分类下拉列表
    search_form.category_id.choices = [(0, '全部')] + [(c.id, c.name) for c in
                                                       Category.query.order_by(Category.name).all()]

    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    question_type = request.args.get('question_type', '')
    category_id = request.args.get('category_id', 0, type=int)
    tag = request.args.get('tag', '')
    difficulty_min = request.args.get('difficulty_min', 0, type=int)
    difficulty_max = request.args.get('difficulty_max', 0, type=int)

    # 构建查询
    query = Question.query

    if keyword:
        query = query.filter(or_(
            Question.title.contains(keyword),
            Question.content.contains(keyword)
        ))

    if question_type:
        query = query.filter(Question.question_type == question_type)

    if category_id > 0:
        query = query.filter(Question.category_id == category_id)

    if tag:
        query = query.join(Question.tags).filter(Tag.name == tag)

    if difficulty_min > 0:
        query = query.filter(Question.difficulty >= difficulty_min)

    if difficulty_max > 0:
        query = query.filter(Question.difficulty <= difficulty_max)

    # 如果不是管理员或教师，只能看到自己创建的题目
    if not (current_user.is_admin() or current_user.is_teacher()):
        query = query.filter(Question.creator_id == current_user.id)

    # 分页
    pagination = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=current_app.config.get('QUESTIONS_PER_PAGE', 10), error_out=False
    )

    questions = pagination.items

    return render_template('questions/index.html',
                           questions=questions,
                           pagination=pagination,
                           search_form=search_form)


@questions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建新题目"""
    # 检查权限
    if not current_user.can_create_question():
        flash('您没有权限创建题目', 'danger')
        return redirect(url_for('questions.index'))

    form = QuestionForm()

    # 填充分类下拉列表
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    # 找不出问题我服了
    # 找到了，这段先留下，以后记得删
    #if request.method == 'POST':
        ## 添加这些调试打印
        #print("提交的表单数据:", request.form)
        #valid = form.validate()
        #print("表单验证结果:", valid)
        #if not valid:
            #print("验证错误:", form.errors)

    if form.validate_on_submit():
        # 创建新题目
        title = form.title.data if form.title.data else "无题目"  # 添加默认标题
        category_id = form.category_id.data if form.category_id.data != 0 else None

        question = Question(
            title=form.title.data,
            content=form.content.data,
            question_type=form.question_type.data,
            difficulty=form.difficulty.data,
            score_default=form.score_default.data,
            # 第六次：category_id=form.category_id.data,
            category_id=category_id,
            answer_template=form.answer_template.data if form.question_type.data == 'programming' else None,
            standard_answer=form.standard_answer.data,
            explanation=form.explanation.data,
            creator_id=current_user.id,
            # 第七次修改
            test_code = form.test_code.data if form.question_type.data == 'programming' else None
        )

        # 处理标签
        if form.tags.data:
            tag_names = [t.strip() for t in form.tags.data.split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    question.tags.append(tag)

        # 处理选择题选项
        if form.question_type.data == 'choice':
            for option_form in form.options.data:
                option = QuestionOption(
                    content=option_form['content'],
                    is_correct=option_form['is_correct'],
                    order=option_form['order']
                )
                question.options.append(option)

        if form.question_type.data == 'fill_blank':
            question.standard_answer = form.standard_answer.data
        else:
            # 选择题和编程题的标准答案逻辑
            question.standard_answer = None if form.question_type.data == 'choice' else form.standard_answer.data

        db.session.add(question)
        db.session.commit()

        flash('题目创建成功！', 'success')
        return redirect(url_for('questions.index'))

    return render_template('questions/create.html', form=form)


@questions_bp.route('/<int:id>')
@login_required
def view(id):
    """查看题目详情"""
    question = Question.query.get_or_404(id)

    # 检查权限 - 学生只能查看与其关联的考试中的题目
    if current_user.is_student():
        # 这里需要检查学生是否有权限查看这个题目
        # 例如判断题目是否在学生参加过的考试中
        is_authorized = question.exam_list.filter(
            Exam.id.in_([score.exam_id for score in current_user.scores])
        ).count() > 0

        if not is_authorized:
            flash('您没有权限查看此题目', 'danger')
            return redirect(url_for('questions.index'))

    return render_template('questions/view.html', question=question)


@questions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑题目"""
    question = Question.query.get_or_404(id)

    # 检查权限 - 只有创建者、管理员或教师可以编辑
    if not (current_user.is_admin() or current_user.is_teacher() or question.creator_id == current_user.id):
        flash('您没有权限编辑此题目', 'danger')
        return redirect(url_for('questions.index'))

    form = QuestionForm(obj=question)

    # 立即处理标签，不等待GET判断
    if request.method == 'GET':
        # 确保tags字段显示的是标签名称的列表，而不是Tag对象的列表
        form.tags.data = ', '.join([tag.name for tag in question.tags])

    # 填充分类下拉列表
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if form.validate_on_submit():
        # 处理标签内容
        tags_data = form.tags.data
        if tags_data and isinstance(tags_data, str) and '[<Tag' in tags_data:
            import re
            tag_names = re.findall(r'<Tag ([^>]+)>', tags_data)
            form.tags.data = ', '.join(tag_names)
        # 更新基本信息
        question.title = form.title.data
        question.content = form.content.data
        question.question_type = form.question_type.data
        question.difficulty = form.difficulty.data
        question.score_default = form.score_default.data
        question.category_id = form.category_id.data
        question.answer_template = form.answer_template.data if form.question_type.data == 'programming' else None
        question.standard_answer = form.standard_answer.data
        question.explanation = form.explanation.data
        # 第七次修改
        question.test_code = form.test_code.data if form.question_type.data == 'programming' else None

        # 处理标签
        # 先清除旧标签
        question.tags = []

        if form.tags.data:
            tag_names = [t.strip() for t in form.tags.data.split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    question.tags.append(tag)

        # 处理选择题选项
        if form.question_type.data == 'choice':
            # 清除旧选项
            for option in question.options.all():
                db.session.delete(option)

            # 添加新选项
            for option_form in form.options.data:
                option = QuestionOption(
                    content=option_form['content'],
                    is_correct=option_form['is_correct'],
                    order=option_form['order']
                )
                question.options.append(option)

        db.session.commit()

        flash('题目更新成功！', 'success')
        return redirect(url_for('questions.view', id=question.id))

    # 对于GET请求，如果是选择题，需要填充选项数据
    if question.is_choice() and request.method == 'GET':
        # 清空默认的空选项
        while len(form.options) > 0:
            form.options.pop_entry()

        # 添加数据库中的选项
        for option in question.options.order_by(QuestionOption.order).all():
            form.options.append_entry({
                'content': option.content,
                'is_correct': option.is_correct,
                'order': option.order
            })

    return render_template('questions/edit.html', form=form, question=question)


@questions_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除题目"""
    question = Question.query.get_or_404(id)

    # 检查权限 - 只有创建者、管理员或教师可以删除
    if not (current_user.is_admin() or current_user.is_teacher() or question.creator_id == current_user.id):
        flash('您没有权限删除此题目', 'danger')
        return redirect(url_for('questions.index'))

    # 检查题目是否已被使用
    if len(question.exams) > 0:
        flash('此题目已被用于考试，无法删除', 'danger')
        return redirect(url_for('questions.view', id=question.id))

    # 删除题目
    db.session.delete(question)
    db.session.commit()

    flash('题目已删除', 'success')
    return redirect(url_for('questions.index'))


@questions_bp.route('/categories')
@login_required
def category_list():
    """分类列表页面"""
    # 检查权限
    if not (current_user.is_admin() or current_user.is_teacher()):
        flash('您没有权限管理分类', 'danger')
        return redirect(url_for('questions.index'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('questions/categories.html', categories=categories)


@questions_bp.route('/tags')
@login_required
def tag_list():
    """标签列表页面"""
    # 检查权限
    if not (current_user.is_admin() or current_user.is_teacher()):
        flash('您没有权限管理标签', 'danger')
        return redirect(url_for('questions.index'))

    tags = Tag.query.order_by(Tag.name).all()
    return render_template('questions/tags.html', tags=tags)