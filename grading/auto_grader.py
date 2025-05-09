# 自动评分系统主模块
from flask import current_app
import json
from models.question import Question
from models.exam_question import ExamQuestion
from models.student_answer import StudentAnswer
from models.score import Score
from grading.choice_grader import ChoiceGrader
from grading.fill_blank_grader import FillBlankGrader
from grading.programming_grader import ProgrammingGrader


class AutoGrader:
    """自动评分系统的主类"""

    def __init__(self, score_id):
        """
        初始化评分器

        Args:
            score_id: 学生考试得分记录的ID
        """
        self.score_id = score_id
        self.score = Score.query.get(score_id)
        # 添加编程题评分器
        self.programming_grader = ProgrammingGrader()
        if not self.score:
            raise ValueError(f"无法找到ID为{score_id}的得分记录")

        # 初始化各类型题目的评分器
        self.choice_grader = ChoiceGrader()
        self.fill_blank_grader = FillBlankGrader()
        self.programming_grader = ProgrammingGrader()

        # 日志记录
        current_app.logger.info(f"初始化自动评分，学生ID: {self.score.student_id}, 考试ID: {self.score.exam_id}")

    def grade_all(self):
        """
        评分所有题目

        Returns:
            dict: 评分结果统计
        """
        # 获取该分数记录下所有学生答案
        student_answers = StudentAnswer.query.filter_by(score_id=self.score_id).all()

        # 初始化计数器
        results = {
            'total': 0,
            'graded': 0,
            'points_earned': 0,
            'max_points': 0,
            'by_type': {
                'choice': {'count': 0, 'points': 0, 'max': 0},
                'fill_blank': {'count': 0, 'points': 0, 'max': 0},
                'programming': {'count': 0, 'points': 0, 'max': 0}
            }
        }

        # 逐个评分
        for answer in student_answers:
            question = Question.query.get(answer.question_id)
            if not question:
                current_app.logger.warning(f"无法找到问题ID为{answer.question_id}的题目")
                continue

            # 获取题目在考试中的分值
            exam_question = ExamQuestion.query.filter_by(
                exam_id=self.score.exam_id,
                question_id=question.id
            ).first()

            if not exam_question:
                current_app.logger.warning(f"题目{question.id}不属于考试{self.score.exam_id}")
                continue

            question_score = exam_question.score
            results['total'] += 1
            results['max_points'] += question_score
            results['by_type'][question.question_type]['count'] += 1
            results['by_type'][question.question_type]['max'] += question_score

            # 根据题目类型选择评分器
            if question.question_type == 'choice':
                points = self.grade_choice_question(answer, question, question_score)
            elif question.question_type == 'fill_blank':
                points = self.grade_fill_blank_question(answer, question, question_score)
            elif question.question_type == 'programming':
                # 使用编程题评分器
                points = self.grade_programming_question(answer, question, question_score)
            else:
                # 未知题型
                current_app.logger.warning(f"未知题型: {question.question_type}")
                continue

            results['graded'] += 1
            results['points_earned'] += points
            results['by_type'][question.question_type]['points'] += points

        # 更新总分
        self.score.total_score = results['points_earned']

        # 如果所有答案都已评分，标记为已评分
        if results['graded'] == results['total']:
            self.score.is_graded = True

        return results

    def grade_choice_question(self, answer, question, max_points):
        """评分选择题"""
        return self.choice_grader.grade(answer, question, max_points)

    def grade_fill_blank_question(self, answer, question, max_points):
        """评分填空题"""
        return self.fill_blank_grader.grade(answer, question, max_points)

    # 添加编程题评分方法
    def grade_programming_question(self, answer, question, max_points):
        """评分编程题"""
        return self.programming_grader.grade(answer, question, max_points)