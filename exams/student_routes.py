from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from exams import exams_bp
from models.db import db
from models.exam import Exam
from models.exam_question import ExamQuestion
from models.question import Question
from models.score import Score
from models.student_answer import StudentAnswer
from models.question_option import QuestionOption
from forms.student_answer import StudentAnswerForm
from datetime import datetime, timedelta
import json
import r_setup
from grading import AutoGrader

@exams_bp.route('/student/exams')
@login_required
def student_exams():
    """学生可参加的考试列表"""
    if not current_user.is_student():
        flash('只有学生可以访问此页面', 'danger')
        return redirect(url_for('index'))

    from sqlalchemy import and_, or_

    # 获取当前UTC时间
    now_utc = datetime.utcnow()

    # 转换为北京时间（UTC+8）
    now_local = now_utc + timedelta(hours=8)

    current_app.logger.debug(f"当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    current_app.logger.debug(f"当前北京时间: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")

    # 查询所有已发布的考试做时间分析
    all_exams = Exam.query.filter(Exam.is_published == True).all()
    for exam in all_exams:
        current_app.logger.debug(
            f"考试ID: {exam.id}, 标题: {exam.title}, "
            f"开始时间: {exam.start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"结束时间: {exam.end_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"本地时间是否在范围内: {exam.start_time <= now_local <= exam.end_time}"
        )

    # 获取学生已提交的考试ID列表
    submitted_exam_ids = [score.exam_id for score in Score.query.filter_by(
        student_id=current_user.id
    ).filter(
        or_(Score.is_final_submit == True, Score.is_graded == True)
    ).all()]

    # 查询可参加的考试 - 使用本地时间（北京时间）
    available_exams = Exam.query.filter(
        Exam.is_published == True,
        Exam.start_time <= now_local,  # 使用北京时间
        Exam.end_time >= now_local,  # 使用北京时间
        ~Exam.id.in_(submitted_exam_ids) if submitted_exam_ids else True
    ).order_by(Exam.start_time).all()

    current_app.logger.debug(f"可参加的考试数量: {len(available_exams)}")
    for exam in available_exams:
        current_app.logger.debug(f"可参加考试: ID={exam.id}, 标题={exam.title}")

    # 查询即将开始的考试 - 使用本地时间
    upcoming_exams = Exam.query.filter(
        Exam.is_published == True,
        Exam.start_time > now_local  # 使用北京时间
    ).order_by(Exam.start_time).all()

    # 获取已结束的考试IDs - 使用本地时间
    ended_exam_ids = [exam.id for exam in Exam.query.filter(
        Exam.is_published == True,
        Exam.end_time < now_local  # 使用北京时间
    ).all()]

    # 合并两种情况的考试IDs
    completed_exam_ids = list(set(submitted_exam_ids + ended_exam_ids))

    # 只查询有成绩记录的已完成考试
    if completed_exam_ids:
        completed_exams = Exam.query.join(
            Score, and_(
                Score.exam_id == Exam.id,
                Score.student_id == current_user.id
            )
        ).filter(
            Exam.id.in_(completed_exam_ids)
        ).all()
    else:
        completed_exams = []

    # 添加调试日志
    current_app.logger.debug(f"已提交的考试IDs: {submitted_exam_ids}")
    current_app.logger.debug(f"已结束的考试IDs: {ended_exam_ids}")
    current_app.logger.debug(f"最终已完成的考试IDs: {completed_exam_ids}")
    current_app.logger.debug(f"已完成考试数量: {len(completed_exams)}")

    # 对完成的考试按结束时间倒序排序
    completed_exams.sort(key=lambda x: x.end_time, reverse=True)

    return render_template('exams/student_exams.html',
                           available_exams=available_exams,
                           upcoming_exams=upcoming_exams,
                           completed_exams=completed_exams,
                           current_time=now_local)  # 传递本地时间到模板


@exams_bp.route('/student/take_exam/<int:exam_id>')
@login_required
def take_exam(exam_id):
    """参加考试页面"""
    if not current_user.is_student():
        flash('只有学生可以参加考试', 'danger')
        return redirect(url_for('exams.student_exams'))

    # 获取考试信息
    exam = Exam.query.get_or_404(exam_id)

    # 检查考试是否已发布
    if not exam.is_published:
        flash('该考试尚未发布', 'danger')
        return redirect(url_for('exams.student_exams'))

    # 获取当前时间并转换为北京时间
    now_utc = datetime.utcnow()
    now_local = now_utc + timedelta(hours=8)  # UTC+8

    current_app.logger.debug(
        f"【参加考试】当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"当前北京时间: {now_local.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"考试开始时间: {exam.start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"结束时间: {exam.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # 检查考试时间 - 使用北京时间
    if now_local < exam.start_time:
        flash('考试尚未开始', 'warning')
        return redirect(url_for('exams.student_exams'))

    if now_local > exam.end_time:
        flash('考试已结束', 'warning')
        return redirect(url_for('exams.student_exams'))

    # 检查是否已存在考试记录
    existing_score = Score.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id
    ).first()

    # 如果没有考试记录，创建一个
    if not existing_score:
        new_score = Score(
            student_id=current_user.id,
            exam_id=exam_id,
            is_graded=False
        )
        db.session.add(new_score)
        db.session.commit()
        score_id = new_score.id
    else:
        # 如果已提交，则不能再次参加
        if existing_score.is_graded:
            flash('您已完成此考试', 'info')
            return redirect(url_for('exams.view_result', exam_id=exam_id))
        # 如果已最终提交，则不能再次参加
        if existing_score.is_final_submit:
            flash('您已提交此考试，无法再次修改答案。', 'info')
            return redirect(url_for('exams.view_result', exam_id=exam_id))
        score_id = existing_score.id

    # 获取考试题目
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).order_by(ExamQuestion.order).all()

    # 计算剩余时间（秒）- 使用北京时间
    remaining_seconds = int((exam.end_time - now_local).total_seconds())

    # 创建学生答题表单
    answer_form = StudentAnswerForm()

    return render_template('exams/take_exam.html',
                           exam=exam,
                           exam_questions=exam_questions,
                           score_id=score_id,
                           remaining_seconds=remaining_seconds,
                           answer_form=answer_form)

@exams_bp.route('/student/get_question/<int:exam_id>/<int:question_id>')
@login_required
def get_question(exam_id, question_id):
    """获取题目详情"""
    try:
        if not current_user.is_student():
            return jsonify({'error': '权限不足', 'message': '只有学生可以访问此API'}), 403

        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在', 'message': f'找不到ID为{exam_id}的考试'}), 404

        # 获取题目信息
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': '题目不存在', 'message': f'找不到ID为{question_id}的题目'}), 404

        # 获取考试题目关联信息
        exam_question = ExamQuestion.query.filter_by(
            exam_id=exam_id,
            question_id=question_id
        ).first()
        if not exam_question:
            return jsonify({'error': '题目不在考试中', 'message': f'题目{question_id}不属于考试{exam_id}'}), 404

        # 获取学生得分记录
        score = Score.query.filter_by(
            student_id=current_user.id,
            exam_id=exam_id
        ).first()

        if not score:
            return jsonify({'error': '考试记录不存在', 'message': '未找到您的考试记录'}), 404

        # 获取学生已保存的答案
        student_answer = StudentAnswer.query.filter_by(
            score_id=score.id,
            question_id=question_id
        ).first()

        # 准备题目数据
        question_data = {
            'id': question.id,
            'title': question.title,
            'content': question.content,
            'question_type': question.question_type,
            'score': exam_question.score,
            'answer_template': question.answer_template,
            'saved_answer': student_answer.answer_content if student_answer else '',
        }

        # 如果是选择题，添加选项
        if question.question_type == 'choice':
            options = []
            for option in question.options:
                options.append({
                    'id': option.id,
                    'content': option.content,
                })
            question_data['options'] = options

        return jsonify(question_data)
    except Exception as e:
        # 记录错误到日志
        current_app.logger.error(f"获取题目时出错: {str(e)}")
        return jsonify({'error': '服务器错误', 'message': f'获取题目时发生错误: {str(e)}'}), 500


@exams_bp.route('/student/get_answer_status/<int:exam_id>')
@login_required
def get_answer_status(exam_id):
    """获取答题状态（AJAX）"""
    try:
        if not current_user.is_student():
            return jsonify({'error': '权限不足', 'message': '只有学生可以访问此API'}), 403

        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在', 'message': f'找不到ID为{exam_id}的考试'}), 404

        # 获取学生得分记录
        score = Score.query.filter_by(
            student_id=current_user.id,
            exam_id=exam_id
        ).first()

        if not score:
            return jsonify({'error': '考试记录不存在', 'message': '未找到您的考试记录'}), 404

        # 获取考试所有题目
        exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()

        # 获取已回答的题目
        answered_questions = StudentAnswer.query.filter_by(score_id=score.id).all()

        # 统计已回答题目数
        answered_count = len(answered_questions)
        total_count = len(exam_questions)

        # 创建题目回答状态
        question_status = {}
        for eq in exam_questions:
            is_answered = any(a.question_id == eq.question_id for a in answered_questions)
            question_status[str(eq.question_id)] = is_answered  # 将键转换为字符串，确保JSON序列化正确

        # 记录一下返回结果用于调试
        result = {
            'answered_count': answered_count,
            'total_count': total_count,
            'question_status': question_status
        }
        current_app.logger.debug(f"答题状态API返回: {result}")

        return jsonify(result)
    except Exception as e:
        # 记录错误到日志
        current_app.logger.error(f"获取答题状态时出错: {str(e)}")
        return jsonify({'error': '服务器错误', 'message': f'获取答题状态时发生错误: {str(e)}'}), 500

@exams_bp.route('/student/save_answer', methods=['POST'])
@login_required
def save_answer():
    """保存学生答案（AJAX）"""
    if not current_user.is_student():
        return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效请求'}), 400

        score_id = data.get('score_id')
        question_id = data.get('question_id')
        answer_content = data.get('answer_content')

        if not all([score_id, question_id]):
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        # 添加日志，帮助调试
        current_app.logger.debug(f"接收到的答案数据: score_id={score_id}, question_id={question_id}")

        # 获取题目类型，以便进行适当的处理
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'success': False, 'message': '题目不存在'}), 404

        # 对选择题答案的特殊处理
        if question.question_type == 'choice':
            try:
                # 尝试验证JSON格式
                if isinstance(answer_content, str):
                    # 确保是有效的JSON
                    json.loads(answer_content)
                    current_app.logger.debug(f"选择题答案: {answer_content}")
                else:
                    # 如果不是字符串，确保转换为JSON字符串
                    answer_content = json.dumps(answer_content)
                    current_app.logger.debug(f"转换后的选择题答案: {answer_content}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"选择题答案JSON解析失败: {e}, 原始内容: {answer_content}")
                return jsonify({'success': False, 'message': f'选择题答案格式错误: {str(e)}'}), 400

        # 检查得分记录是否存在且属于当前用户
        score = Score.query.get_or_404(score_id)
        if score.student_id != current_user.id:
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 检查考试是否在进行中 - 使用北京时间
        exam = Exam.query.get_or_404(score.exam_id)
        now_utc = datetime.utcnow()
        now_local = now_utc + timedelta(hours=8)  # UTC+8

        current_app.logger.debug(
            f"【保存答案】当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"当前北京时间: {now_local.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"考试结束时间: {exam.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if now_local > exam.end_time or now_local < exam.start_time:
            return jsonify({'success': False, 'message': '考试时间已过或未开始'}), 403

        # 查找已存在的答案记录
        existing_answer = StudentAnswer.query.filter_by(
            score_id=score_id,
            question_id=question_id
        ).first()

        if existing_answer:
            # 更新现有答案
            existing_answer.answer_content = answer_content
            existing_answer.submitted_at = datetime.utcnow()
            current_app.logger.debug(f"更新答案: question_id={question_id}")
        else:
            # 创建新答案记录
            new_answer = StudentAnswer(
                score_id=score_id,
                question_id=question_id,
                answer_content=answer_content,
                points_earned=0  # 初始分数为0
            )
            db.session.add(new_answer)
            current_app.logger.debug(f"创建新答案: question_id={question_id}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '答案已保存',
            'saved_at': now_local.strftime('%Y-%m-%d %H:%M:%S')  # 返回北京时间
        })

    except Exception as e:
        current_app.logger.error(f"保存答案时发生错误: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存答案失败: {str(e)}'}), 500

@exams_bp.route('/student/submit_exam/<int:exam_id>', methods=['POST'])
@login_required
def submit_exam(exam_id):
    """提交考试"""
    if not current_user.is_student():
        flash('只有学生可以参加考试', 'danger')
        return redirect(url_for('exams.student_exams'))

    # 获取考试信息
    exam = Exam.query.get_or_404(exam_id)

    # 获取学生得分记录
    score = Score.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id
    ).first_or_404()

    # 标记为已提交
    score.is_graded = False  # 暂时设为False，等待完全评分
    score.submit_time = datetime.utcnow()

    # 设置为最终提交
    score.is_final_submit = True

    try:
        # 使用自动评分系统评分选择题和填空题
        grader = AutoGrader(score.id)
        results = grader.grade_all()

        # 记录评分结果
        current_app.logger.info(f"自动评分结果: {results}")

        # 更新Flash消息，包含评分信息
        flash_message = f'考试已提交，自动评分完成！共计得分: {results["points_earned"]}/{results["max_points"]}分。'

        # 如果有编程题未评分，提示教师需手动评分
        if results['by_type']['programming']['count'] > 0:
            flash_message += ' 编程题将由教师手动评分。'

        flash(flash_message, 'success')
    except Exception as e:
        current_app.logger.error(f"自动评分过程出错: {str(e)}")
        flash('考试已提交，但自动评分过程出错，请联系教师。', 'warning')
        # 确保事务可以继续，不会因为评分错误而阻止提交

    db.session.commit()

    # flash('考试已提交，谢谢参与！', 'success')
    return redirect(url_for('exams.view_result', exam_id=exam_id))


@exams_bp.route('/student/view_result/<int:exam_id>')
@login_required
def view_result(exam_id):
    """查看考试结果"""
    if not current_user.is_student():
        flash('只有学生可以查看考试结果', 'danger')
        return redirect(url_for('index'))

    # 获取考试信息
    exam = Exam.query.get_or_404(exam_id)

    # 获取学生得分记录
    score = Score.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id
    ).first_or_404()

    # 获取所有答题记录
    student_answers = StudentAnswer.query.filter_by(score_id=score.id).all()

    # 获取考试题目
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).order_by(ExamQuestion.order).all()

    # 创建题目和答案的映射
    question_answers = {}
    for eq in exam_questions:
        question = eq.question
        answer = next((a for a in student_answers if a.question_id == question.id), None)
        question_answers[question.id] = {
            'question': question,
            'exam_question': eq,
            'answer': answer
        }

    return render_template('exams/view_result.html',
                           exam=exam,
                           score=score,
                           question_answers=question_answers)

@exams_bp.route('/student/check_time/<int:exam_id>')
@login_required
def check_time(exam_id):
    """检查考试剩余时间（AJAX）"""
    try:
        if not current_user.is_student():
            return jsonify({'error': '权限不足', 'message': '只有学生可以访问此API'}), 403

        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': '考试不存在', 'message': f'找不到ID为{exam_id}的考试'}), 404

        # 获取当前时间并转换为北京时间
        now_utc = datetime.utcnow()
        now_local = now_utc + timedelta(hours=8)  # UTC+8

        current_app.logger.debug(
            f"【时间检查】当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"当前北京时间: {now_local.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"考试开始时间: {exam.start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"结束时间: {exam.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 计算剩余时间 - 使用北京时间与考试时间比较
        if now_local > exam.end_time:
            remaining_seconds = 0
            status = 'ended'
            current_app.logger.debug("【时间检查】考试已结束")
        elif now_local < exam.start_time:
            remaining_seconds = int((exam.start_time - now_local).total_seconds())
            status = 'not_started'
            current_app.logger.debug(f"【时间检查】考试未开始，还有 {remaining_seconds} 秒")
        else:
            remaining_seconds = int((exam.end_time - now_local).total_seconds())
            status = 'in_progress'
            current_app.logger.debug(f"【时间检查】考试进行中，剩余 {remaining_seconds} 秒")

        result = {
            'remaining_seconds': remaining_seconds,
            'status': status,
            'current_time': now_local.strftime('%Y-%m-%d %H:%M:%S'),
            'start_time': exam.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': exam.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'server_timestamp': int(now_local.timestamp())
        }

        return jsonify(result)
    except Exception as e:
        # 记录错误到日志
        current_app.logger.error(f"检查考试时间时出错: {str(e)}")
        return jsonify({'error': '服务器错误', 'message': f'检查考试时间时发生错误: {str(e)}'}), 500

def auto_grade_choice_questions(score):
    """自动评分选择题"""
    # 获取所有选择题答案
    student_answers = StudentAnswer.query.join(
        Question, StudentAnswer.question_id == Question.id
    ).filter(
        StudentAnswer.score_id == score.id,
        Question.question_type == 'choice'
    ).all()

    total_points = 0

    for answer in student_answers:
        question = Question.query.get(answer.question_id)
        exam_question = ExamQuestion.query.filter_by(
            exam_id=score.exam_id,
            question_id=question.id
        ).first()

        if not exam_question:
            continue

        # 获取题目分值
        question_score = exam_question.score

        # 解析学生答案（选项ID列表）
        try:
            selected_options = json.loads(answer.answer_content)
        except:
            selected_options = []

        # 获取正确选项
        correct_options = [opt.id for opt in question.correct_options]

        # 如果答案完全一致，得满分
        if set(selected_options) == set(correct_options):
            answer.points_earned = question_score
        else:
            answer.points_earned = 0

        total_points += answer.points_earned

    # 更新总分
    score.total_score = total_points


def auto_grade_programming_questions(score):
    """自动评分编程题（R语言）"""
    # 获取所有编程题答案
    student_answers = StudentAnswer.query.join(
        Question, StudentAnswer.question_id == Question.id
    ).filter(
        StudentAnswer.score_id == score.id,
        Question.question_type == 'programming'
    ).all()

    for answer in student_answers:
        question = Question.query.get(answer.question_id)
        exam_question = ExamQuestion.query.filter_by(
            exam_id=score.exam_id,
            question_id=question.id
        ).first()

        if not exam_question or not question.test_code:
            continue

        # 获取题目分值
        question_score = exam_question.score

        # 运行R测试代码
        student_code = answer.answer_content or ""
        test_code = question.test_code

        try:
            # 使用R运行测试
            result = r_setup.run_r_test(student_code, test_code)

            # 计算得分
            if result['status'] == 'success':
                answer.points_earned = float(result['score'])
                answer.feedback = result['message']
            else:
                answer.points_earned = 0
                answer.feedback = result['message']
        except Exception as e:
            answer.points_earned = 0
            answer.feedback = f"评分过程出错: {str(e)}"

    # 重新计算总分
    db.session.commit()

    # 计算总得分
    total_points = db.session.query(db.func.sum(StudentAnswer.points_earned)).filter(
        StudentAnswer.score_id == score.id
    ).scalar() or 0

    score.total_score = total_points


@exams_bp.route('/admin/grade_exam/<int:score_id>', methods=['POST'])
@login_required
def admin_grade_exam(score_id):
    """管理员手动触发自动评分"""
    # 检查权限 - 只有管理员或教师可以操作
    if not (current_user.is_admin() or current_user.is_teacher()):
        flash('权限不足', 'danger')
        return redirect(url_for('index'))

    # 获取学生得分记录
    score = Score.query.get_or_404(score_id)

    try:
        # 使用自动评分系统评分
        grader = AutoGrader(score.id)
        results = grader.grade_all()

        # 更新数据库
        db.session.commit()

        flash(f'自动评分完成！学生得分: {results["points_earned"]}/{results["max_points"]}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'自动评分失败: {str(e)}', 'danger')

    # 重定向回学生考试结果页面
    return redirect(url_for('exams.view_result', exam_id=score.exam_id))