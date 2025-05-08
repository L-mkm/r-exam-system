from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, session
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
from datetime import datetime, timedelta

# 关于session的备注：实在无法兼顾自动保存和取消返回上一次保存的功能，先记下

@exams_bp.route('/')
@login_required
def index():
    """考试列表页面"""
    # 获取筛选参数
    search_keyword = request.args.get('search', '')
    is_published = request.args.get('is_published', '')
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # 检查权限 - 基础查询
    if current_user.is_admin():
        query = Exam.query
    elif current_user.is_teacher():
        query = Exam.query.filter_by(creator_id=current_user.id)
    else:  # 学生
        # 只显示已发布且在考试时间范围内的考试
        now = datetime.utcnow()
        query = Exam.query.filter(
            Exam.is_published == True,
            Exam.start_time <= now,
            Exam.end_time >= now
        )

    # 应用搜索和筛选条件 (仅对管理员和教师应用)
    if (current_user.is_admin() or current_user.is_teacher()):
        if search_keyword:
            query = query.filter(Exam.title.like(f'%{search_keyword}%'))

        if is_published:
            published = (is_published == 'true')
            query = query.filter(Exam.is_published == published)

        # 根据考试状态筛选
        now = datetime.utcnow()
        if status == 'not_started':
            query = query.filter(Exam.start_time > now)
        elif status == 'in_progress':
            query = query.filter(Exam.start_time <= now, Exam.end_time >= now)
        elif status == 'ended':
            query = query.filter(Exam.end_time < now)

        # 根据创建时间筛选
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Exam.created_at >= start_date_obj)
            except ValueError:
                pass

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # 添加一天，使其包含结束日期当天
                end_date_obj = end_date_obj + timedelta(days=1)
                query = query.filter(Exam.created_at < end_date_obj)
            except ValueError:
                pass

    # 排序结果
    exams = query.order_by(Exam.created_at.desc()).all()

    return render_template('exams/index.html', exams=exams, get_now=datetime.utcnow)

@exams_bp.route('/create_ajax', methods=['POST'])
@login_required
def create_ajax():
    """创建新考试的AJAX处理"""
    # 检查权限
    if not (current_user.is_admin() or current_user.is_teacher()):
        return jsonify({'success': False, 'message': '您没有权限创建考试'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    try:
        # 创建考试
        exam = Exam(
            title=data.get('title', '未命名考试'),
            description=data.get('description', ''),
            creator_id=current_user.id,
            is_published=data.get('is_published', False),
            is_draft=False  # 直接创建为非草稿状态
        )

        # 处理时间数据
        try:
            if data.get('start_time'):
                exam.start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%dT%H:%M')
            else:
                # 默认开始时间为当前时间后1小时
                exam.start_time = datetime.now() + timedelta(hours=1)

            if data.get('end_time'):
                exam.end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%dT%H:%M')
            else:
                # 默认结束时间为开始时间后2小时
                exam.end_time = exam.start_time + timedelta(hours=2)
        except ValueError as e:
            return jsonify({'success': False, 'message': f'日期格式错误: {str(e)}'}), 400

        # 处理考试时长选项
        use_duration = data.get('use_duration', False)
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(data.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        # 保存考试
        db.session.add(exam)
        db.session.commit()

        return jsonify({
            'success': True,
            'exam_id': exam.id,
            'message': '考试创建成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500

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
            total_score=0,  # 先设为0，后面再更新
            is_published=form.is_published.data,
            creator_id=current_user.id,
            is_draft=False  # 直接设为非草稿状态
        )

        # 记录开始和结束时间，确保正确保存
        current_app.logger.debug(
            f"创建考试 - 开始时间: {exam.start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"结束时间: {exam.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 处理考试时长选项
        use_duration = request.form.get('use_duration') == 'on'
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(request.form.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        db.session.add(exam)
        db.session.commit()

        flash('考试创建成功！', 'success')
        # 直接跳转到考试详情页面
        return redirect(url_for('exams.view', id=exam.id))

    return render_template('exams/create.html', form=form)


@exams_bp.route('/<int:id>/continue_create', methods=['GET', 'POST'])
@login_required
def continue_create(id):
    """继续创建草稿状态的考试"""
    exam = Exam.query.get_or_404(id)

    # 检查权限和状态
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限编辑此考试', 'danger')
        return redirect(url_for('exams.index'))

    if not exam.is_draft:
        flash('此考试已不是草稿状态，无法继续创建流程', 'warning')
        return redirect(url_for('exams.edit', id=exam.id))

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

        # 处理考试时长选项
        use_duration = request.form.get('use_duration') == 'on'
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(request.form.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        # 如果选择发布，则改变草稿状态
        if form.is_published.data:
            exam.is_draft = False
            exam.is_published = True
            flash('考试已从草稿状态发布！', 'success')
        else:
            exam.is_published = False
            # 此处也将草稿状态改为false，表示完成创建
            exam.is_draft = False

        db.session.commit()

        flash('考试创建已完成！', 'success')
        # 无论如何，都跳转到考试详情页面
        return redirect(url_for('exams.view', id=exam.id))

    # 传递额外信息到模板
    extra_data = {
        'has_duration': getattr(exam, 'has_duration', False),
        'duration_minutes': getattr(exam, 'duration_minutes', 120)
    }

    return render_template('exams/continue_create.html', form=form, exam=exam, **extra_data)


@exams_bp.route('/complete_creation', methods=['POST'])
@login_required
def complete_creation():
    """完成考试创建的AJAX处理"""
    # 获取请求数据
    data = request.get_json()
    if not data or 'exam_id' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    try:
        exam_id = int(data['exam_id'])
        exam = Exam.query.get_or_404(exam_id)

        # 权限检查
        if not (current_user.is_admin() or exam.creator_id == current_user.id):
            return jsonify({'success': False, 'message': '您没有权限修改此考试'}), 403

        # 更新考试信息
        exam.title = data.get('title', exam.title)
        exam.description = data.get('description', exam.description)

        # 处理时间数据
        try:
            if data.get('start_time'):
                exam.start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%dT%H:%M')

            if data.get('end_time'):
                exam.end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%dT%H:%M')
        except ValueError as e:
            return jsonify({'success': False, 'message': f'日期格式错误: {str(e)}'}), 400

        # 处理考试时长选项
        use_duration = data.get('use_duration', False)
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(data.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        # 更新发布状态
        exam.is_published = data.get('is_published', exam.is_published)

        # 将草稿状态设为False
        exam.is_draft = False

        # 保存更改
        db.session.commit()

        return jsonify({
            'success': True,
            'exam_id': exam.id,
            'message': '考试创建完成'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'完成创建失败: {str(e)}'}), 500


@exams_bp.route('/save_draft', methods=['POST'])
@login_required
def save_draft():
    """保存考试草稿"""
    # 检查权限
    if not (current_user.is_admin() or current_user.is_teacher()):
        return jsonify({'success': False, 'message': '您没有权限操作'}), 403

    # 获取表单数据
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '未接收到数据'})

    try:
        # 创建或更新草稿
        if data.get('exam_id'):
            # 更新现有考试
            try:
                exam_id = int(data.get('exam_id'))
                exam = Exam.query.get(exam_id)
                if not exam:
                    return jsonify({'success': False, 'message': f'未找到ID为{exam_id}的考试'})

                # 权限检查
                if not current_user.is_admin() and exam.creator_id != current_user.id:
                    return jsonify({'success': False, 'message': '无权修改此考试'})
            except (TypeError, ValueError):
                return jsonify({'success': False, 'message': '无效的考试ID'})
        else:
            # 创建新考试
            exam = Exam(creator_id=current_user.id)
            db.session.add(exam)

        # 更新考试属性
        if 'title' in data:
            exam.title = data.get('title') or '未命名考试'

        if 'description' in data:
            exam.description = data.get('description', '')

        # 处理时间数据
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        try:
            if start_time_str:
                exam.start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            else:
                # 默认开始时间为当前时间后1小时
                exam.start_time = datetime.now() + timedelta(hours=1)

            if end_time_str:
                exam.end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            else:
                # 默认结束时间为开始时间后2小时
                exam.end_time = exam.start_time + timedelta(hours=2)

        except ValueError as e:
            return jsonify({'success': False, 'message': f'日期格式错误: {str(e)}'})

        # 检查开始时间必须早于结束时间
        if exam.start_time >= exam.end_time:
            return jsonify({'success': False, 'message': '开始时间必须早于结束时间'})

        # 处理是否发布状态
        if 'is_published' in data:
            exam.is_published = data.get('is_published', False)

        # 处理考试时长选项
        use_duration = data.get('use_duration', False)
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(data.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        # 关键：强制设置为草稿状态，无论前端传入什么
        exam.is_draft = True

        # 提交到数据库
        db.session.commit()

        # 返回成功响应
        return jsonify({
            'success': True,
            'exam_id': exam.id,
            'message': '草稿已保存',
            'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        # 出错时回滚事务
        db.session.rollback()
        import traceback
        traceback.print_exc()  # 打印错误堆栈便于调试
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

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
    limited_mode = request.args.get('limited', 'false') == 'true'

    # 检查权限 - 只有创建者和管理员可以编辑
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        flash('您没有权限编辑此考试', 'danger')
        return redirect(url_for('exams.index'))

    # 判断考试状态与编辑模式
    now = datetime.utcnow()
    is_exam_started = now > exam.start_time
    is_exam_ended = now > exam.end_time

    # 考试已结束，无法编辑
    if is_exam_ended:
        flash('考试已经结束，无法编辑', 'danger')
        return redirect(url_for('exams.view', id=exam.id))

    # 考试已开始但未指定有限模式，重定向到有限模式
    if is_exam_started and not limited_mode:
        flash('考试已经开始，只能进行有限的编辑', 'warning')
        return redirect(url_for('exams.edit', id=exam.id, limited='true'))

    form = ExamForm(obj=exam)

    # 填充分类下拉列表
    form.category_id.choices = [(0, '不限分类')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        # 更新考试信息
        if not limited_mode:
            # 完全编辑模式
            exam.title = form.title.data
            exam.description = form.description.data
            exam.start_time = form.start_time.data
            exam.end_time = form.end_time.data
            exam.is_published = form.is_published.data
        else:
            # 有限编辑模式 - 只能修改描述、时间和时长
            exam.description = form.description.data
            exam.start_time = form.start_time.data
            exam.end_time = form.end_time.data

        # 处理考试时长选项
        use_duration = request.form.get('use_duration') == 'on'
        exam.has_duration = use_duration
        if use_duration:
            try:
                duration_minutes = int(request.form.get('exam_duration', 120))
                exam.duration_minutes = duration_minutes
            except (ValueError, TypeError):
                exam.duration_minutes = 120

        # 有限模式下处理题目分值更新
        if limited_mode and 'update_scores' in request.form:
            for eq in exam.questions:
                score_key = f'question_score_{eq.question_id}'
                if score_key in request.form:
                    try:
                        new_score = float(request.form.get(score_key, eq.score))
                        if new_score >= 0:  # 确保分值非负
                            eq.score = new_score
                    except ValueError:
                        pass  # 忽略无效输入

            # 更新考试总分
            update_exam_total_score(exam)

        db.session.commit()

        flash('考试信息更新成功！', 'success')
        return redirect(url_for('exams.view', id=exam.id))

    return render_template('exams/edit.html', form=form, exam=exam)


@exams_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_exam(id):
    """删除考试"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限删除此考试'}), 403

    try:
        # 删除考试题目关联
        ExamQuestion.query.filter_by(exam_id=id).delete()

        # 删除考试
        db.session.delete(exam)
        db.session.commit()

        return jsonify({'success': True, 'message': '考试已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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

    # 保存原始题目状态到会话
    session[f'exam_{id}_original_questions'] = [eq.question_id for eq in exam_questions]

    # 获取可以添加的题目（首页只显示部分，其余通过AJAX加载）
    if current_user.is_admin():
        available_questions = Question.query.filter(
            ~Question.id.in_([eq.question_id for eq in exam_questions]) if exam_questions else True
        ).order_by(Question.created_at.desc()).limit(20).all()
    else:
        available_questions = Question.query.filter(
            ~Question.id.in_([eq.question_id for eq in exam_questions]) if exam_questions else True,
            or_(
                Question.creator_id == current_user.id,
                Question.is_public == True
            )
        ).order_by(Question.created_at.desc()).limit(20).all()

        # 获取所有分类
        categories = Category.query.order_by(Category.name).all()

    return render_template('exams/manage_questions.html',
                           exam=exam,
                           exam_questions=exam_questions,
                           available_questions=available_questions,
                           categories=categories)



@exams_bp.route('/<int:id>/preview_random_questions', methods=['POST'])
@login_required
def preview_random_questions(id):
    """预览随机抽题"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    # 统计可用题目数量
    choice_count, fill_blank_count, programming_count = count_available_questions(
        data.get('category_id'),
        data.get('choice_difficulty_min'), data.get('choice_difficulty_max'),
        data.get('fill_blank_difficulty_min'), data.get('fill_blank_difficulty_max'),
        data.get('programming_difficulty_min'), data.get('programming_difficulty_max')
    )

    # 计算实际可抽取数量
    actual_choice_count = min(choice_count, data.get('choice_count', 0))
    actual_fill_blank_count = min(fill_blank_count, data.get('fill_blank_count', 0))
    actual_programming_count = min(programming_count, data.get('programming_count', 0))

    # 计算总分值
    total_score = (
            actual_choice_count * (data.get('choice_score', 0)) +
            actual_fill_blank_count * (data.get('fill_blank_score', 0)) +
            actual_programming_count * (data.get('programming_score', 0))
    )

    return jsonify({
        'success': True,
        'choice_count': actual_choice_count,
        'fill_blank_count': actual_fill_blank_count,
        'programming_count': actual_programming_count,
        'total_count': actual_choice_count + actual_fill_blank_count + actual_programming_count,
        'total_score': total_score
    })


@exams_bp.route('/<int:id>/apply_random_questions', methods=['POST'])
@login_required
def apply_random_questions(id):
    """应用随机抽题"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    try:
        # 开始数据库事务
        db.session.begin_nested()

        # 删除现有题目
        ExamQuestion.query.filter_by(exam_id=id).delete()

        # 抽取选择题
        choice_questions = []
        if data.get('choice_count', 0) > 0:
            choice_questions = get_random_questions(
                question_type='choice',
                count=data.get('choice_count', 0),
                difficulty_min=data.get('choice_difficulty_min', 0),
                difficulty_max=data.get('choice_difficulty_max', 0),
                category_id=data.get('category_id') if int(data.get('category_id', 0)) > 0 else None,
                score=data.get('choice_score', 0)
            )
            add_questions_to_exam(exam, choice_questions, data.get('choice_score', 0))

        # 抽取填空题
        fill_blank_questions = []
        if data.get('fill_blank_count', 0) > 0:
            fill_blank_questions = get_random_questions(
                question_type='fill_blank',
                count=data.get('fill_blank_count', 0),
                difficulty_min=data.get('fill_blank_difficulty_min', 0),
                difficulty_max=data.get('fill_blank_difficulty_max', 0),
                category_id=data.get('category_id') if int(data.get('category_id', 0)) > 0 else None,
                score=data.get('fill_blank_score', 0)
            )
            add_questions_to_exam(exam, fill_blank_questions, data.get('fill_blank_score', 0))

        # 抽取编程题
        programming_questions = []
        if data.get('programming_count', 0) > 0:
            programming_questions = get_random_questions(
                question_type='programming',
                count=data.get('programming_count', 0),
                difficulty_min=data.get('programming_difficulty_min', 0),
                difficulty_max=data.get('programming_difficulty_max', 0),
                category_id=data.get('category_id') if int(data.get('category_id', 0)) > 0 else None,
                score=data.get('programming_score', 0)
            )
            add_questions_to_exam(exam, programming_questions, data.get('programming_score', 0))

        # 更新考试总分
        update_exam_total_score(exam)

        # 提交事务
        db.session.commit()

        return jsonify({
            'success': True,
            'choice_count': len(choice_questions),
            'fill_blank_count': len(fill_blank_questions),
            'programming_count': len(programming_questions),
            'total_count': len(choice_questions) + len(fill_blank_questions) + len(programming_questions),
            'total_score': exam.total_score
        })

    except Exception as e:
        # 回滚事务
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@exams_bp.route('/<int:id>/batch_add_questions', methods=['POST'])
@login_required
def batch_add_questions(id):
    """批量添加题目"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data or 'question_ids' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    question_ids = data['question_ids']
    if not question_ids:
        return jsonify({'success': False, 'message': '未选择题目'}), 400

    try:
        # 获取当前最大顺序号
        max_order = db.session.query(db.func.max(ExamQuestion.order)).filter_by(exam_id=id).scalar() or 0

        # 添加题目
        added_count = 0
        for i, question_id in enumerate(question_ids):
            question = Question.query.get(question_id)
            if not question:
                continue

            # 检查题目是否已在考试中
            existing = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first()
            if existing:
                continue

            # 添加题目
            exam_question = ExamQuestion(
                exam_id=id,
                question_id=question_id,
                order=max_order + i + 1,
                score=question.score_default
            )
            db.session.add(exam_question)
            added_count += 1

        # 更新考试总分
        if added_count > 0:
            db.session.commit()
            update_exam_total_score(exam)

        return jsonify({
            'success': True,
            'added_count': added_count,
            'message': f'成功添加 {added_count} 道题目'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@exams_bp.route('/<int:id>/batch_remove_questions', methods=['POST'])
@login_required
def batch_remove_questions(id):
    """批量移除题目"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data or 'question_ids' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    question_ids = data['question_ids']
    if not question_ids:
        return jsonify({'success': False, 'message': '未选择题目'}), 400

    try:
        # 删除题目
        removed_count = 0
        for question_id in question_ids:
            exam_question = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first()
            if exam_question:
                db.session.delete(exam_question)
                removed_count += 1

        # 更新考试总分
        if removed_count > 0:
            db.session.commit()

            # 重新排序剩余题目
            remaining_questions = ExamQuestion.query.filter_by(exam_id=id).order_by(ExamQuestion.order).all()
            for i, eq in enumerate(remaining_questions, 1):
                eq.order = i
            db.session.commit()

            update_exam_total_score(exam)

        return jsonify({
            'success': True,
            'removed_count': removed_count,
            'message': f'成功移除 {removed_count} 道题目'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@exams_bp.route('/<int:id>/available_questions')
@login_required
def available_questions(id):
    """获取可用题目列表（带分页和筛选）"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    # 获取分页和筛选参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    question_type = request.args.get('type', '')
    difficulty = request.args.get('difficulty', 0, type=int)
    category_id = request.args.get('category', 0, type=int)

    # 构建查询
    query = Question.query

    # 排除已添加到考试的题目
    existing_question_ids = [eq.question_id for eq in ExamQuestion.query.filter_by(exam_id=id).all()]
    if existing_question_ids:
        query = query.filter(~Question.id.in_(existing_question_ids))

    # 应用筛选条件
    if search:
        query = query.filter(Question.title.like(f'%{search}%'))

    if question_type:
        query = query.filter(Question.question_type == question_type)

    if difficulty > 0:
        query = query.filter(Question.difficulty == difficulty)

    if category_id > 0:
        query = query.filter(Question.category_id == category_id)

    # 非管理员只能看到自己创建的和公开的题目
    if not current_user.is_admin():
        query = query.filter(or_(
            Question.creator_id == current_user.id,
            Question.is_public == True
        ))

    # 分页
    questions = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)

    # 格式化结果
    return jsonify({
        'success': True,
        'questions': [
            {
                'id': q.id,
                'title': q.title,
                'question_type': q.question_type,
                'difficulty': q.difficulty,
                'score_default': q.score_default,
                'category_id': q.category_id
            }
            for q in questions.items
        ],
        'total': questions.total,
        'pages': questions.pages,
        'page': page
    })


@exams_bp.route('/<int:id>/save_all', methods=['POST'])
@login_required
def save_all(id):
    """保存所有更改"""
    exam = Exam.query.get_or_404(id)

    # 权限检查
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    try:
        # 更新考试总分
        update_exam_total_score(exam)

        # 确定重定向URL
        redirect_url = url_for('exams.continue_create', id=id) if exam.is_draft else url_for('exams.edit', id=id)

        return jsonify({
            'success': True,
            'message': '所有更改已保存',
            'redirect': redirect_url,
            'is_draft': exam.is_draft
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@exams_bp.route('/<int:id>/check_status')
@login_required
def check_status(id):
    """检查考试状态API"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    return jsonify({
        'success': True,
        'is_draft': exam.is_draft,
        'is_published': exam.is_published
    })


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

    # 返回更多有用信息
    return jsonify({
        'success': True,
        'message': '题目已添加到考试',
        'exam_question': {
            'id': exam_question.id,
            'order': exam_question.order,
            'score': exam_question.score
        }
    })


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

    # 获取新分值(从JSON)
    data = request.get_json()
    if not data or 'score' not in data:
        return jsonify({'success': False, 'message': '未收到有效的分值数据'}), 400

    new_score = float(data.get('score', 0))
    if not new_score or new_score <= 0:
        return jsonify({'success': False, 'message': '请输入有效的分值'}), 400

    try:
        # 更新分值
        exam_question = ExamQuestion.query.filter_by(exam_id=id, question_id=question_id).first_or_404()
        exam_question.score = new_score
        db.session.commit()

        # 更新考试总分
        update_exam_total_score(exam)

        return jsonify({'success': True, 'message': '题目分值已更新'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


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


@exams_bp.route('/<int:id>/revert_questions', methods=['POST'])
@login_required
def revert_questions(id):
    """恢复考试题目到上次保存状态"""
    exam = Exam.query.get_or_404(id)

    # 检查权限
    if not (current_user.is_admin() or exam.creator_id == current_user.id):
        return jsonify({'success': False, 'message': '无权限操作'}), 403


    try:
        # 获取管理题目页面开始前的原始题目状态
        # 这需要在服务器端存储原始状态，可以使用会话数据
        original_question_ids = session.get(f'exam_{id}_original_questions', [])

        # 首先清除所有当前题目
        ExamQuestion.query.filter_by(exam_id=id).delete()

        # 如果有原始题目，恢复它们
        if original_question_ids:
            for i, q_id in enumerate(original_question_ids):
                question = Question.query.get(q_id)
                if question:
                    exam_question = ExamQuestion(
                        exam_id=id,
                        question_id=q_id,
                        order=i + 1,
                        score=question.score_default
                    )
                    db.session.add(exam_question)

        db.session.commit()
        update_exam_total_score(exam)

        return jsonify({'success': True, 'message': '已恢复原始设置'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


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

# +辅助函数
def count_available_questions(category_id=None,
                              choice_difficulty_min=0, choice_difficulty_max=0,
                              fill_blank_difficulty_min=0, fill_blank_difficulty_max=0,
                              programming_difficulty_min=0, programming_difficulty_max=0):
    """统计可用题目数量"""
    # 选择题查询
    choice_query = Question.query.filter_by(question_type='choice')
    if category_id and int(category_id) > 0:
        choice_query = choice_query.filter_by(category_id=int(category_id))
    if choice_difficulty_min > 0:
        choice_query = choice_query.filter(Question.difficulty >= choice_difficulty_min)
    if choice_difficulty_max > 0:
        choice_query = choice_query.filter(Question.difficulty <= choice_difficulty_max)
    choice_count = choice_query.count()

    # 填空题查询
    fill_blank_query = Question.query.filter_by(question_type='fill_blank')
    if category_id and int(category_id) > 0:
        fill_blank_query = fill_blank_query.filter_by(category_id=int(category_id))
    if fill_blank_difficulty_min > 0:
        fill_blank_query = fill_blank_query.filter(Question.difficulty >= fill_blank_difficulty_min)
    if fill_blank_difficulty_max > 0:
        fill_blank_query = fill_blank_query.filter(Question.difficulty <= fill_blank_difficulty_max)
    fill_blank_count = fill_blank_query.count()

    # 编程题查询
    programming_query = Question.query.filter_by(question_type='programming')
    if category_id and int(category_id) > 0:
        programming_query = programming_query.filter_by(category_id=int(category_id))
    if programming_difficulty_min > 0:
        programming_query = programming_query.filter(Question.difficulty >= programming_difficulty_min)
    if programming_difficulty_max > 0:
        programming_query = programming_query.filter(Question.difficulty <= programming_difficulty_max)
    programming_count = programming_query.count()

    return choice_count, fill_blank_count, programming_count