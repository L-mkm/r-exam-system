# 填空题评分逻辑
import re
from flask import current_app
from difflib import SequenceMatcher


class FillBlankGrader:
    """填空题评分器"""

    def __init__(self, case_sensitive=False, fuzzy_match=True, fuzzy_threshold=0.8):
        """
        初始化填空题评分器

        Args:
            case_sensitive: 是否区分大小写
            fuzzy_match: 是否启用模糊匹配
            fuzzy_threshold: 模糊匹配的相似度阈值
        """
        self.case_sensitive = case_sensitive
        self.fuzzy_match = fuzzy_match
        self.fuzzy_threshold = fuzzy_threshold

    def grade(self, answer, question, max_points):
        """
        评分填空题

        Args:
            answer: StudentAnswer对象，学生的答案
            question: Question对象，题目
            max_points: 题目的最大分值

        Returns:
            float: 得分
        """
        if not answer.answer_content or not answer.answer_content.strip():
            # 未回答，得0分
            answer.points_earned = 0
            answer.feedback = "未作答"
            return 0

        # 学生答案(去除首尾空白)
        student_answer = answer.answer_content.strip()

        # 获取标准答案(可能有多个，用分号分隔)
        if not question.standard_answer:
            answer.points_earned = 0
            answer.feedback = "题目缺少标准答案，请联系老师"
            return 0

        # 分割多个标准答案
        correct_answers = [ans.strip() for ans in question.standard_answer.split(';')]

        # 精确匹配
        for correct in correct_answers:
            # 如果不区分大小写，转换为小写比较
            if not self.case_sensitive:
                if student_answer.lower() == correct.lower():
                    answer.points_earned = max_points
                    answer.feedback = "回答正确"
                    return max_points
            else:
                if student_answer == correct:
                    answer.points_earned = max_points
                    answer.feedback = "回答正确"
                    return max_points

        # 模糊匹配
        if self.fuzzy_match:
            best_match = 0
            best_match_answer = ""

            for correct in correct_answers:
                # 如果不区分大小写，转换为小写比较
                student = student_answer.lower() if not self.case_sensitive else student_answer
                standard = correct.lower() if not self.case_sensitive else correct

                # 计算相似度
                similarity = SequenceMatcher(None, student, standard).ratio()

                if similarity > best_match:
                    best_match = similarity
                    best_match_answer = correct

            # 如果相似度超过阈值，给予部分得分
            if best_match >= self.fuzzy_threshold:
                points = max_points * best_match
                answer.points_earned = round(points, 2)  # 保留两位小数
                answer.feedback = f"接近正确答案 '{best_match_answer}'，相似度: {best_match:.2f}"
                return answer.points_earned

        # 答案错误
        answer.points_earned = 0
        answer.feedback = "回答错误，请参考正确答案"
        return 0