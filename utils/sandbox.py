import os
import tempfile
import subprocess
import signal
import json
import threading
import traceback
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
        print(f"初始化R代码沙箱: timeout={timeout}, memory_limit={memory_limit}MB, cpu_limit={cpu_limit}")

    def execute(self, student_code, test_code):
        """
        在安全沙箱中执行R代码

        Args:
            student_code: 学生提交的R代码
            test_code: 评分用的测试代码

        Returns:
            dict: 执行结果，包含status、score等信息
        """
        print("=" * 50)
        print(f"开始执行R代码评分 - 代码长度: {len(student_code)} / 测试长度: {len(test_code)}")

        # 首先尝试使用rpy2直接在Python中执行
        try:
            print("尝试使用rpy2方式执行...")
            return self._execute_with_rpy2(student_code, test_code)
        except Exception as e:
            print(f"rpy2执行失败，将使用外部进程执行: {str(e)}")
            if hasattr(current_app, 'logger'):
                current_app.logger.warning(f"rpy2执行失败，将使用外部进程执行: {str(e)}")
            # 如果rpy2执行失败，尝试使用外部R进程执行
            return self._execute_with_process(student_code, test_code)

    def _execute_with_rpy2(self, student_code, test_code):
        """使用rpy2在Python进程内执行R代码"""
        print("使用rpy2执行R代码...")
        try:
            # 直接使用r_setup模块中的函数执行代码
            result = r_setup.run_r_test(student_code, test_code, self.timeout)
            print(f"rpy2执行结果状态: {result.get('status', '未知')}")
            return result
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"rpy2执行失败详细信息:\n{error_trace}")
            raise Exception(f"rpy2执行失败: {str(e)}")

    def _execute_with_process(self, student_code, test_code):
        """使用单独的R进程执行代码"""
        print("使用R外部进程执行代码...")

        # 创建临时文件存储代码，确保使用utf-8编码
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as student_file, \
                tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as test_file:

            student_path = student_file.name
            test_path = test_file.name

            # 写入代码文件
            student_file.write(student_code)
            test_file.write(test_code)

            print(f"学生代码写入到: {student_path}")
            print(f"测试代码写入到: {test_path}")

        try:
            # 准备执行环境
            r_script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'r_scripts')
            r_script_path = os.path.join(r_script_dir, 'test_runner_enhanced.R')

            # 确保路径使用正斜杠
            r_script_path = r_script_path.replace('\\', '/')
            student_path = student_path.replace('\\', '/')
            test_path = test_path.replace('\\', '/')

            # 检查脚本是否存在
            if not os.path.exists(r_script_path):
                # 尝试查找脚本
                print(f"R脚本不存在: {r_script_path}")
                print(f"尝试查找r_scripts目录内容:")
                if os.path.exists(r_script_dir):
                    print(f"目录存在: {r_script_dir}")
                    print(f"目录内容: {os.listdir(r_script_dir)}")
                else:
                    print(f"目录不存在: {r_script_dir}")

                # 尝试搜索项目目录
                import glob
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                r_scripts = glob.glob(os.path.join(project_dir, "**", "test_runner_enhanced.R"), recursive=True)
                print(f"搜索到的R脚本: {r_scripts}")

                if r_scripts:
                    r_script_path = r_scripts[0].replace('\\', '/')
                    print(f"使用找到的脚本: {r_script_path}")
                else:
                    raise FileNotFoundError(f"R脚本不存在，且无法找到: {r_script_path}")

            print(f"R脚本路径: {r_script_path}")

            # 构建命令
            cmd = [
                'Rscript',
                r_script_path,
                student_path,
                test_path,
                str(self.timeout)
            ]

            print(f"执行命令: {' '.join(cmd)}")

            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',  # 尝试UTF-8
                errors='replace'  # 在解码错误时替换为占位符，而不是抛出异常
            )

            # 设置超时
            timer = threading.Timer(self.timeout + 5, process.kill)  # 给R脚本自身的超时机制多5秒余量
            timer.start()

            # 获取输出
            stdout, stderr = process.communicate()

            # 记录输出
            print(f"进程返回代码: {process.returncode}")
            print(f"标准输出(前200字符): {stdout[:200]}...")
            if stderr:
                print(f"标准错误(前200字符): {stderr[:200]}...")

            # 取消超时计时器
            timer.cancel()

            # 解析输出
            if process.returncode != 0:
                # 执行出错
                error_msg = f'R脚本执行错误(返回代码:{process.returncode}): {stderr}'
                print(error_msg)
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': error_msg,
                    'output': stdout
                }

            try:
                # 解析JSON结果
                print("尝试解析JSON结果...")
                if not stdout.strip():
                    print("警告: 标准输出为空")
                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '外部进程未返回任何结果',
                        'output': stderr if stderr else "无输出"
                    }

                # 尝试找到JSON数据的开始位置
                json_start = stdout.find('{')
                if json_start == -1:
                    print("警告: 输出中没有找到JSON开始标记'{}'")
                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '无法在输出中找到JSON数据',
                        'output': stdout + "\n" + stderr
                    }

                json_data = stdout[json_start:]
                result = json.loads(json_data)
                print(f"JSON解析成功: {result.get('status', '未知状态')}")
                return result
            except json.JSONDecodeError as e:
                # JSON解析失败
                print(f"JSON解析失败: {str(e)}")
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': f'无法解析评分结果: {str(e)}',
                    'output': stdout
                }

        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = f'执行异常: {str(e)}'
            print(f"{error_msg}\n{error_trace}")
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': error_msg,
                'output': error_trace
            }
        finally:
            # 清理临时文件
            print("清理临时文件...")
            try:
                os.unlink(student_path)
                os.unlink(test_path)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")