# R编程题评分逻辑
import os
import tempfile
import json
from flask import current_app
import r_setup
from utils.sandbox import RCodeSandbox


class ProgrammingGrader:
    """R编程题评分器"""

    def __init__(self, timeout=10, memory_limit=500, cpu_limit=1.0):
        """
        初始化编程题评分器

        Args:
            timeout: 代码执行超时时间(秒)
            memory_limit: 内存限制(MB)
            cpu_limit: CPU使用限制(核心数)
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.sandbox = RCodeSandbox(
            timeout=timeout,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit
        )

    def grade(self, answer, question, max_points):
        """
        评分R编程题

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

        if not question.test_code or not question.test_code.strip():
            # 没有测试代码，无法评分
            answer.points_earned = 0
            answer.feedback = "题目缺少测试代码，请联系教师手动评分"
            return 0

        # 获取学生代码和测试代码
        student_code = answer.answer_content.strip()
        test_code = question.test_code.strip()

        try:
            # 使用R代码沙箱执行评分
            result = self.sandbox.execute(student_code, test_code)

            # 解析结果
            if result.get('status') == 'success':
                # 提取得分和反馈
                score_ratio = min(1.0, max(0.0, float(result.get('score', 0)) / float(result.get('max_score', 100))))
                points = round(max_points * score_ratio, 2)

                # 设置得分和反馈
                answer.points_earned = points
                answer.feedback = result.get('message', '自动评分完成')

                # 如果有详细输出，添加到反馈中
                if 'output' in result and result['output']:
                    answer.feedback += f"\n\n程序输出:\n{result['output']}"

                return points
            else:
                # 执行出错
                answer.points_earned = 0
                error_message = result.get('message', '代码执行出错')
                answer.feedback = f"评分错误: {error_message}"

                # 如果有详细输出，添加到反馈中
                if 'output' in result and result['output']:
                    answer.feedback += f"\n\n程序输出:\n{result['output']}"

                return 0

        except Exception as e:
            # 评分过程出现异常
            current_app.logger.error(f"R编程题评分异常: {str(e)}")
            answer.points_earned = 0
            answer.feedback = f"评分过程异常: {str(e)}"
            return 0