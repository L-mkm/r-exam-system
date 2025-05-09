# 选择题评分逻辑
import json
from flask import current_app


class ChoiceGrader:
    """选择题评分器"""

    def __init__(self, partial_credit=False, partial_threshold=0.5):
        """
        初始化选择题评分器

        Args:
            partial_credit: 是否启用部分得分
            partial_threshold: 部分得分的阈值比例
        """
        self.partial_credit = partial_credit
        self.partial_threshold = partial_threshold

    def grade(self, answer, question, max_points):
        """
        评分选择题

        Args:
            answer: StudentAnswer对象，学生的答案
            question: Question对象，题目
            max_points: 题目的最大分值

        Returns:
            float: 得分
        """
        if not answer.answer_content:
            # 未回答，得0分
            answer.points_earned = 0
            answer.feedback = "未作答"
            return 0

        try:
            # 解析学生答案（选项ID列表）
            selected_options = json.loads(answer.answer_content)

            # 确保选项ID是整数列表
            if isinstance(selected_options, (int, str)):
                selected_options = [int(selected_options)]
            elif isinstance(selected_options, list):
                selected_options = [int(opt) if isinstance(opt, str) else opt for opt in selected_options]
            else:
                raise ValueError("选项格式无效")

            # 获取正确选项ID列表
            correct_options = [opt.id for opt in question.correct_options]

            # 计算正确率
            student_set = set(selected_options)
            correct_set = set(correct_options)

            # 计算交集和并集
            intersection = student_set.intersection(correct_set)
            union = student_set.union(correct_set)

            # 完全正确
            if student_set == correct_set:
                answer.points_earned = max_points
                answer.feedback = "回答完全正确"
                return max_points

            # 部分正确
            if self.partial_credit and intersection:
                # 计算Jaccard系数（交集/并集）作为相似度
                similarity = len(intersection) / len(union)

                # 完全不相交时的相似度
                if len(intersection) == 0:
                    answer.points_earned = 0
                    answer.feedback = "回答完全错误"
                    return 0

                # 给予部分得分，如果超过阈值
                if similarity >= self.partial_threshold:
                    points = max_points * similarity
                    answer.points_earned = round(points, 2)  # 保留两位小数
                    answer.feedback = f"部分正确 (相似度: {similarity:.2f})"
                    return answer.points_earned
                else:
                    answer.points_earned = 0
                    answer.feedback = f"相似度({similarity:.2f})不足以获得部分分数，需达到{self.partial_threshold}"
                    return 0
            else:
                # 没有启用部分得分或没有交集
                answer.points_earned = 0
                answer.feedback = "回答错误，请参考正确答案"
                return 0

        except Exception as e:
            current_app.logger.error(f"选择题评分出错: {str(e)}")
            answer.points_earned = 0
            answer.feedback = f"评分过程出错: {str(e)}"
            return 0