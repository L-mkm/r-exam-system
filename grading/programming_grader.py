# grading/programming_grader.py - 更新为使用RCodeGrader
import os
import logging
import re
from flask import current_app
# 导入新创建的R代码评分器
from grading.r_code_grader import RCodeGrader

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('programming_grader')


class ProgrammingGrader:
    """R编程题评分器"""

    def __init__(self, timeout=30, memory_limit=500, cpu_limit=1.0):
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
        # 使用新的R代码评分器
        self.r_grader = RCodeGrader(timeout, memory_limit, cpu_limit)
        logger.info(f"初始化R编程题评分器: timeout={timeout}s, memory_limit={memory_limit}MB, cpu_limit={cpu_limit}")

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
        logger.info(f"开始评分R编程题 - 问题ID: {question.id}, 答案ID: {answer.id}, 最大分值: {max_points}")

        if not answer.answer_content or not answer.answer_content.strip():
            # 未回答，得0分
            answer.points_earned = 0
            answer.feedback = "未作答"
            logger.info("未作答，得分: 0")
            return 0

        if not question.test_code or not question.test_code.strip():
            # 没有测试代码，无法评分
            answer.points_earned = 0
            answer.feedback = "题目缺少测试代码，请联系教师手动评分"
            logger.warning(f"问题 {question.id} 缺少测试代码")
            return 0

        # 获取学生代码和测试代码
        student_code = answer.answer_content.strip()
        test_code = question.test_code.strip()

        # 确定需要的R包
        required_packages = self._get_required_packages(question, student_code)

        try:
            # 使用新的R代码评分器
            result = self.r_grader.grade(student_code, test_code, required_packages)

            # 解析结果
            status = result.get('status', 'error')
            logger.info(f"评分结果状态: {status}")

            if status == 'success':
                # 提取得分和反馈
                score = float(result.get('score', 0))
                max_score = float(result.get('max_score', 100))
                score_ratio = min(1.0, max(0.0, score / max_score))
                points = round(max_points * score_ratio, 2)

                # 设置得分和反馈
                answer.points_earned = points
                answer.feedback = result.get('message', '自动评分完成')

                # 如果有详细输出，添加到反馈中
                if 'output' in result and result['output']:
                    # 截断过长输出，避免数据库问题
                    output = result['output']
                    if len(output) > 5000:
                        output = output[:5000] + "...(输出过长，已截断)"

                    answer.feedback += f"\n\n程序输出:\n{output}"

                logger.info(f"评分成功: {points}/{max_points}")
                return points
            else:
                # 执行出错
                answer.points_earned = 0
                error_message = result.get('message', '代码执行出错')

                # 尝试提供更友好的错误消息
                friendly_message = self._get_friendly_error_message(error_message)
                answer.feedback = f"评分错误: {friendly_message}"

                # 如果有详细输出，添加到反馈中
                if 'output' in result and result['output']:
                    # 截断过长输出
                    output = result['output']
                    if len(output) > 5000:
                        output = output[:5000] + "...(输出过长，已截断)"

                    answer.feedback += f"\n\n程序输出:\n{output}"

                logger.warning(f"评分错误: {error_message}")
                return 0

        except Exception as e:
            # 评分过程出现异常
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"R编程题评分异常: {str(e)}\n{error_trace}")

            answer.points_earned = 0
            answer.feedback = f"评分过程异常: {str(e)}"
            return 0

    def _get_required_packages(self, question, student_code):
        """根据题目和学生代码分析需要的R包"""
        required_packages = []

        # 基础包，始终加载
        basic_packages = ['stats', 'graphics', 'grDevices', 'utils', 'datasets', 'methods']
        required_packages.extend(basic_packages)

        # 根据代码分析需要的包
        code_analysis_packages = set()

        # dplyr相关
        if "dplyr" in student_code or "%>%" in student_code or "group_by" in student_code or "arrange" in student_code:
            code_analysis_packages.add('dplyr')

        # ggplot2相关
        if "ggplot" in student_code or "geom_" in student_code or "aes(" in student_code:
            code_analysis_packages.add('ggplot2')

        # tidyr相关
        if "gather" in student_code or "spread" in student_code or "pivot_" in student_code:
            code_analysis_packages.add('tidyr')

        # 数据处理相关
        if "read.csv" in student_code or "read_csv" in student_code:
            code_analysis_packages.add('readr')

        # 统计分析相关
        if "lm(" in student_code or "glm(" in student_code:
            code_analysis_packages.add('stats')

        # 时间序列相关
        if "ts(" in student_code or "arima" in student_code:
            code_analysis_packages.add('forecast')

        # 添加分析的包
        required_packages.extend(list(code_analysis_packages))

        # 将包去重
        required_packages = list(set(required_packages))

        logger.info(f"分析得到的所需R包: {', '.join(required_packages)}")
        return required_packages

    def _get_friendly_error_message(self, error_message):
        """将R错误消息转换为更友好的消息"""
        # 常见错误模式及友好提示
        error_patterns = {
            "object .* not found": "你使用了未定义的变量或函数，请检查拼写是否正确",
            "could not find function": "找不到指定的函数，可能需要加载相应的包",
            "unexpected.*in": "代码语法错误，请检查括号、逗号等是否匹配",
            "argument .* is missing": "函数调用缺少必要的参数",
            "subscript out of bounds": "索引超出范围，检查数组或列表的长度",
            "non-numeric argument to binary operator": "非数值类型用于数学运算",
            "cannot coerce .* to a double": "类型转换错误，无法将值转换为数值类型",
            "unused argument": "函数调用中使用了未知的参数名",
            "comparison .* is possible only for atomic and list types": "比较操作只能用于基本类型和列表类型"
        }

        # 查找匹配的错误模式
        for pattern, friendly_message in error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return f"{friendly_message} - 原始错误: {error_message}"

        # 如果没有匹配，返回原始错误
        return error_message