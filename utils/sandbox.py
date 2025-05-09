import os
import tempfile
import subprocess
import signal
import json
import threading
from flask import current_app
import r_setup

# 检测操作系统类型，为 Windows 提供替代实现
import platform

is_windows = platform.system() == 'Windows'

# Windows 系统不支持 resource 模块，提供空实现
if not is_windows:
    import resource
else:
    # Windows 替代实现
    class DummyResource:
        @staticmethod
        def setrlimit(*args, **kwargs):
            pass


    resource = DummyResource()


class TimeoutError(Exception):
    """代码执行超时异常"""
    pass


class MemoryLimitError(Exception):
    """内存超限异常"""
    pass

class RCodeSandbox:
    """R代码安全沙箱"""

    def __init__(self, timeout=10, memory_limit=500, cpu_limit=1.0):
        """
        初始化R代码沙箱

        Args:
            timeout: 代码执行超时时间(秒)
            memory_limit: 内存限制(MB)
            cpu_limit: CPU使用限制(核心数)
        """
        self.timeout = timeout
        self.memory_limit = memory_limit  # MB
        self.cpu_limit = cpu_limit

    def execute(self, student_code, test_code):
        """
        在安全沙箱中执行R代码

        Args:
            student_code: 学生提交的R代码
            test_code: 评分用的测试代码

        Returns:
            dict: 执行结果，包含status、score等信息
        """
        # 首先尝试使用rpy2直接在Python中执行
        try:
            return self._execute_with_rpy2(student_code, test_code)
        except Exception as e:
            current_app.logger.warning(f"rpy2执行失败，将使用外部进程执行: {str(e)}")
            # 如果rpy2执行失败，尝试使用外部R进程执行
            return self._execute_with_process(student_code, test_code)

    def _execute_with_rpy2(self, student_code, test_code):
        """使用rpy2在Python进程内执行R代码"""
        try:
            # 直接使用r_setup模块中的函数执行代码
            result = r_setup.run_r_test(student_code, test_code, self.timeout)
            return result
        except Exception as e:
            raise Exception(f"rpy2执行失败: {str(e)}")

    def _execute_with_process(self, student_code, test_code):
        """使用单独的R进程执行代码"""
        # 创建临时文件存储代码
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False) as student_file, \
                tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False) as test_file:

            student_path = student_file.name
            test_path = test_file.name

            # 写入代码文件
            student_file.write(student_code)
            test_file.write(test_code)

        try:
            # 准备执行环境
            r_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         '..', 'r_scripts', 'test_runner_enhanced.R')

            # 确保路径存在
            if not os.path.exists(r_script_path):
                raise FileNotFoundError(f"R脚本不存在: {r_script_path}")

            # 构建命令
            cmd = [
                'Rscript',
                r_script_path,
                student_path,
                test_path,
                str(self.timeout)
            ]

            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 设置超时
            timer = threading.Timer(self.timeout + 5, process.kill)  # 给R脚本自身的超时机制多5秒余量
            timer.start()

            # 获取输出
            stdout, stderr = process.communicate()

            # 取消超时计时器
            timer.cancel()

            # 解析输出
            if process.returncode != 0:
                # 执行出错
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': f'R脚本执行错误: {stderr}',
                    'output': stdout
                }

            try:
                # 解析JSON结果
                result = json.loads(stdout)
                return result
            except json.JSONDecodeError:
                # JSON解析失败
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': '无法解析评分结果',
                    'output': stdout
                }

        except Exception as e:
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'执行异常: {str(e)}',
                'output': ''
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(student_path)
                os.unlink(test_path)
            except:
                pass