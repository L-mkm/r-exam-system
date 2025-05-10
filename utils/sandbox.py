# sandbox.py - 集成的R代码安全沙箱
import os
import tempfile
import subprocess
import signal
import json
import threading
import traceback
import platform
import logging
import datetime
import re
from flask import current_app
import r_setup


def find_conda_r_path():
    """动态查找Conda环境中的Rscript路径"""
    try:
        # 获取当前活动的Conda环境名称
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'r_exam_env')

        # 获取Conda环境信息
        process = subprocess.run(
            ['conda', 'info', '--envs', '--json'],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        conda_info = json.loads(process.stdout)

        # 查找指定环境的路径
        env_path = None
        for env in conda_info.get('envs', []):
            if os.path.basename(env) == conda_env:
                env_path = env
                break

        if env_path:
            # 在环境中查找Rscript路径
            r_script_path = os.path.join(env_path, 'Lib', 'R', 'bin', 'Rscript.exe')
            if os.path.exists(r_script_path):
                return r_script_path

        # 回退：尝试直接查找
        fallback_path = os.path.join(
            os.path.expanduser('~'),
            'anaconda3',
            'envs',
            conda_env,
            'Lib',
            'R',
            'bin',
            'Rscript.exe'
        )
        if os.path.exists(fallback_path):
            return fallback_path

    except Exception as e:
        print(f"查找Conda R路径时出错: {str(e)}")

    # 如果找不到则返回默认命令
    return 'Rscript'

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('r_sandbox')

# 检测操作系统类型
is_windows = platform.system() == 'Windows'

# 对Windows系统的特殊处理
if not is_windows:
    import resource
else:
    # Windows 替代实现
    class DummyResource:
        @staticmethod
        def setrlimit(*args, **kwargs):
            pass


    resource = DummyResource()


def decode_unicode_escapes(text):
    """解码所有Unicode转义序列"""
    if not isinstance(text, str):
        return text

    try:
        # 使用encode/decode
        decoded = text.encode().decode('unicode_escape')
        return decoded
    except Exception:
        try:
            # 使用正则表达式替换
            pattern = r'<U\+([0-9A-F]{4})>'

            def replace_unicode(match):
                code = int(match.group(1), 16)
                return chr(code)

            return re.sub(pattern, replace_unicode, text)
        except Exception as e:
            logger.error(f"解码Unicode失败: {str(e)}")
            return text


class RCodeSandbox:
    """R代码安全沙箱 - 集成版"""

    def __init__(self, timeout=10, memory_limit=500, cpu_limit=1.0, required_packages=None):
        """
        初始化R代码沙箱

        Args:
            timeout: 代码执行超时时间(秒)
            memory_limit: 内存限制(MB)
            cpu_limit: CPU使用限制(核心数)
            required_packages: 需要的R包列表
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.required_packages = required_packages or []
        logger.info(f"初始化R代码沙箱: timeout={timeout}s, memory_limit={memory_limit}MB, cpu_limit={cpu_limit}")
        if self.required_packages:
            logger.info(f"需要的R包: {', '.join(self.required_packages)}")

    def execute(self, student_code, test_code):
        """
        在安全沙箱中执行R代码

        Args:
            student_code: 学生提交的R代码
            test_code: 评分用的测试代码

        Returns:
            dict: 执行结果，包含status、score等信息
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"[执行时间]: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"[R代码评分] - 学生代码长度: {len(student_code)}, 测试代码长度: {len(test_code)}")

        # 处理所需包
        if self.required_packages:
            # 尝试预加载包
            packages_code = "\n".join([
                f"suppressPackageStartupMessages({{" +
                f"if (!require('{pkg}', quietly = TRUE)) " +
                f"install.packages('{pkg}', repos='https://cloud.r-project.org', quiet=TRUE)}}"
                for pkg in self.required_packages
            ])
            student_code = f"{packages_code}\n\n{student_code}"
            logger.info(f"已添加包加载代码: {len(self.required_packages)}个包")

        # 首先尝试使用rpy2直接执行
        try:
            logger.info("尝试使用rpy2方式执行...")
            return self._execute_with_rpy2(student_code, test_code)
        except Exception as e:
            logger.warning(f"rpy2执行失败，将使用外部进程执行: {str(e)}")
            # 如果rpy2执行失败，尝试使用外部R进程
            return self._execute_with_process(student_code, test_code)

    def _execute_with_rpy2(self, student_code, test_code):
        """使用rpy2在Python进程内执行R代码"""
        logger.info("使用rpy2执行R代码...")
        try:
            # 使用r_setup模块中的高级函数执行代码
            result = r_setup.run_r_test(
                student_code,
                test_code,
                self.timeout,
                self.required_packages
            )
            logger.info(f"rpy2执行结果状态: {result.get('status', '未知')}")
            return result
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"rpy2执行失败详细信息:\n{error_trace}")
            raise Exception(f"rpy2执行失败: {str(e)}")

    def _execute_with_process(self, student_code, test_code):
        """使用单独的R进程执行代码"""
        logger.info("使用R外部进程执行代码...")

        # 创建临时文件存储代码，确保使用utf-8编码
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as student_file, \
                tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as test_file:

            student_path = student_file.name
            test_path = test_file.name

            # 特殊处理dplyr相关代码
            if "dplyr" in student_code and "%>%" in student_code:
                # 为dplyr代码添加特殊包装
                student_file.write(self._wrap_dplyr_code(student_code))
            else:
                # 写入普通代码
                student_file.write(student_code)

            # 写入测试代码
            test_file.write(test_code)

            logger.info(f"学生代码写入到: {student_path}")
            logger.info(f"测试代码写入到: {test_path}")

        try:
            # 准备执行环境
            r_script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'r_scripts')
            r_script_path = os.path.join(r_script_dir, 'test_runner.R')

            # 确保路径使用正斜杠
            r_script_path = r_script_path.replace('\\', '/')
            student_path = student_path.replace('\\', '/')
            test_path = test_path.replace('\\', '/')

            # 检查脚本是否存在
            if not os.path.exists(r_script_path):
                # 尝试搜索项目目录
                import glob
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                r_scripts = glob.glob(os.path.join(project_dir, "**", "test_runner.R"), recursive=True)

                if r_scripts:
                    r_script_path = r_scripts[0].replace('\\', '/')
                    logger.info(f"使用找到的脚本: {r_script_path}")
                else:
                    raise FileNotFoundError(f"R脚本不存在，且无法找到: {r_script_path}")

            logger.info(f"R脚本路径: {r_script_path}")

            # 获取Conda环境中的Rscript路径
            conda_r_script = find_conda_r_path()
            logger.info(f"使用R路径: {conda_r_script}")

            # 构建命令
            cmd = [
                conda_r_script,
                r_script_path,
                student_path,
                test_path,
                str(self.timeout)
            ]

            logger.info(f"执行命令: {' '.join(cmd)}")

            # 执行命令时设置环境变量
            env = os.environ.copy()
            env['LC_ALL'] = 'C'  # 使用C区域设置，更加稳定
            env['R_HOME'] = os.environ.get('R_HOME', r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R').replace('\\',
                                                                                                                '/')

            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                errors='replace',  # 解码错误时替换
                env=env
            )

            # 设置超时
            timer = threading.Timer(self.timeout + 5, process.kill)  # 额外5秒余量
            timer.start()

            # 获取输出
            stdout, stderr = process.communicate()

            # 取消超时计时器
            timer.cancel()

            # 记录输出
            logger.info(f"进程返回代码: {process.returncode}")
            if stdout:
                logger.info(f"标准输出(前200字符): {stdout[:200]}...")
            else:
                logger.info("标准输出为空")

            if stderr:
                logger.info(f"标准错误(前200字符): {stderr[:200]}...")
            else:
                logger.info("标准错误为空")

            # 解析输出
            if process.returncode != 0:
                # 执行出错
                error_msg = f'R脚本执行错误(返回代码:{process.returncode}): {stderr}'
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': error_msg,
                    'output': stdout
                }

            try:
                # 尝试直接解析JSON结果
                logger.info("尝试解析JSON结果...")
                if not stdout.strip():
                    logger.warning("标准输出为空")
                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '外部进程未返回任何结果',
                        'output': stderr if stderr else "无输出"
                    }

                # 尝试找到JSON开始的位置
                json_start = stdout.find('{')
                if json_start == -1:
                    logger.warning("输出中没有找到JSON开始标记'{'")
                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '无法在输出中找到JSON数据',
                        'output': stdout + "\n" + stderr
                    }

                # 提取JSON部分
                json_text = stdout[json_start:].strip()
                result = json.loads(json_text)
                logger.info(f"JSON解析成功: {result.get('status', '未知状态')}")

                # 修复中文消息编码
                try:
                    # 处理message字段中的Unicode转义序列
                    if 'message' in result and isinstance(result['message'], str):
                        result['message'] = decode_unicode_escapes(result['message'])

                    # 同样处理output字段
                    if 'output' in result and isinstance(result['output'], str):
                        result['output'] = decode_unicode_escapes(result['output'])

                    logger.info("已修复中文编码显示")
                except Exception as e:
                    logger.error(f"修复中文消息失败: {str(e)}")

                # 确保所有必要的字段都存在
                required_fields = ['status', 'score', 'max_score', 'message']
                for field in required_fields:
                    if field not in result:
                        result[field] = 0 if field in ['score', 'max_score'] else (
                            'error' if field == 'status' else '字段缺失')

                # 添加输出
                if 'output' not in result or not result['output']:
                    result['output'] = stdout

                return result

            except json.JSONDecodeError as e:
                # JSON解析失败
                logger.error(f"JSON解析失败: {str(e)}")
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
            logger.error(f"{error_msg}\n{error_trace}")
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': error_msg,
                'output': error_trace
            }
        finally:
            # 清理临时文件
            logger.info("清理临时文件...")
            try:
                os.unlink(student_path)
                os.unlink(test_path)
            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")

    def _wrap_dplyr_code(self, code):
        """为dplyr代码添加特殊包装，处理常见的dplyr问题"""
        return f"""
# 确保加载dplyr并正确导入管道操作符
suppressPackageStartupMessages({{
  if (!require("dplyr", quietly = TRUE)) {{
    install.packages("dplyr", repos="https://cloud.r-project.org", quiet=TRUE)
    library(dplyr)
  }}
}})

# 显式导入管道操作符
`%>%` <- dplyr::`%>%`

# 执行学生代码
tryCatch({{
{code}
}}, error = function(e) {{
  cat(paste("执行错误:", e$message, "\\n"))

  # 如果是dplyr错误，尝试基础R方法
  if (grepl("group_by|arrange|summarize|filter|select|mutate", e$message)) {{
    cat("检测到dplyr错误，尝试使用基础R方法\\n")

    # 可以在这里添加一些基础R的替代实现
    # 这部分代码应该根据你的具体需求进行定制
  }}
}})
"""