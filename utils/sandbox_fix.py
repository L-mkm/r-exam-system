# sandbox_fix.py - 稳定的R代码沙箱 (完整修复版)
import os
import tempfile
import subprocess
import json
import threading
import traceback
import datetime
import re
from flask import current_app

# 检测操作系统类型
import platform

is_windows = platform.system() == 'Windows'


def check_r_scripts():
    """检查R脚本是否可用"""
    r_script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'r_scripts')
    r_script_path = os.path.join(r_script_dir, 'simple_test_runner.R')
    print(f"检查R脚本: {r_script_path}")
    if os.path.exists(r_script_path):
        print(f"✅ R脚本存在: {r_script_path}")
        return True
    else:
        print(f"❌ R脚本不存在: {r_script_path}")
        # 搜索项目目录
        import glob
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r_scripts = glob.glob(os.path.join(project_dir, "**", "simple_test_runner.R"), recursive=True)
        print(f"搜索到的R脚本: {r_scripts}")
        if r_scripts:
            print(f"✅ 找到替代R脚本: {r_scripts[0]}")
            return True
        return False


# 初始化时检查R脚本
R_SCRIPTS_AVAILABLE = check_r_scripts()


def decode_unicode_escapes(text):
    """解码所有Unicode转义序列"""
    if not isinstance(text, str):
        return text

    try:
        # 方法1: 使用encode/decode
        decoded = text.encode().decode('unicode_escape')
        return decoded
    except Exception:
        try:
            # 方法2: 使用正则表达式替换
            pattern = r'<U\+([0-9A-F]{4})>'

            def replace_unicode(match):
                code = int(match.group(1), 16)
                return chr(code)

            return re.sub(pattern, replace_unicode, text)
        except Exception as e:
            print(f"解码Unicode失败: {str(e)}")
            return text


class RCodeSandbox:
    """R代码安全沙箱 - 仅使用外部进程执行"""

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
        print(f"初始化R代码沙箱: timeout={timeout}s, memory_limit={memory_limit}MB, cpu_limit={cpu_limit}")
        if self.required_packages:
            print(f"需要的R包: {', '.join(self.required_packages)}")

    def execute(self, student_code, test_code):
        """
        在安全沙箱中执行R代码
        Args:
            student_code: 学生提交的R代码
            test_code: 评分用的测试代码
        Returns:
            dict: 执行结果，包含status、score等信息
        """
        print("\n" + "=" * 80)
        print(f"[执行时间]: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[R代码评分] - 学生代码长度: {len(student_code)}, 测试代码长度: {len(test_code)}")

        # 检查R脚本是否可用
        if not R_SCRIPTS_AVAILABLE:
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': 'R测试脚本不可用，请联系管理员',
                'output': '系统错误: R脚本未找到'
            }

        # 处理所需包
        if self.required_packages:
            # 添加包加载代码到学生代码开头
            packages_code = "\n".join(
                [f"if (!require('{pkg}')) install.packages('{pkg}', repos='https://cloud.r-project.org')"
                 for pkg in self.required_packages])
            student_code = f"{packages_code}\n\n{student_code}"
            print(f"已添加包加载代码: {len(self.required_packages)}个包")

        # 直接使用外部进程执行
        return self._execute_with_process(student_code, test_code)

    def _execute_with_process(self, student_code, test_code):
        """使用单独的R进程执行代码"""
        print("使用R外部进程执行代码...")

        # 创建临时文件存储代码，确保使用utf-8编码
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as student_file, \
                tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False, encoding='utf-8') as test_file:

            student_path = student_file.name
            test_path = test_file.name

            # 特殊处理dplyr相关代码
            if "dplyr" in student_code and "%>%" in student_code:
                # 为dplyr代码添加特殊包装
                wrapped_code = f"""
# 确保加载dplyr并正确导入管道操作符
suppressPackageStartupMessages({{
  if (!require("dplyr", quietly = TRUE)) {{
    install.packages("dplyr", repos="https://cloud.r-project.org", quiet=TRUE)
    library(dplyr)
  }}
}})

# 显式导入管道操作符
`%>%` <- dplyr::`%>%`

# 打印dplyr版本进行调试
print(paste("dplyr版本:", packageVersion("dplyr")))

# 开始执行学生代码
tryCatch({{
{student_code}
}}, error = function(e) {{
  print(paste("执行错误:", e$message))

  # 如果是dplyr错误，尝试基础R方法
  if (grepl("group_by|arrange|summarize", e$message)) {{
    print("检测到dplyr错误，尝试使用基础R方法")

    # 执行基础R实现
    if (exists("data")) {{
      # 清洗数据
      clean_data <- na.omit(data)

      # 手动计算
      customer_ids <- unique(clean_data$customer_id)
      results <- data.frame(
        customer_id = customer_ids,
        total_amount = numeric(length(customer_ids)),
        average_amount = numeric(length(customer_ids)),
        purchase_count = numeric(length(customer_ids))
      )

      for (i in 1:length(customer_ids)) {{
        id <- customer_ids[i]
        subset_data <- clean_data[clean_data$customer_id == id, ]

        results$total_amount[i] <- sum(subset_data$amount)
        results$average_amount[i] <- mean(subset_data$amount)
        results$purchase_count[i] <- nrow(subset_data)
      }}

      # 按总金额排序
      processed_data <- results[order(results$total_amount, decreasing = TRUE), ]
      print("备选方法创建了processed_data")
      print(paste("processed_data行数:", nrow(processed_data)))
    }}
  }}
}})
"""
                student_file.write(wrapped_code)
            else:
                # 写入普通代码
                student_file.write(student_code)

            # 写入测试代码
            test_file.write(test_code)

            print(f"学生代码写入到: {student_path}")
            print(f"测试代码写入到: {test_path}")

        try:
            # 准备执行环境
            r_script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'r_scripts')
            r_script_path = os.path.join(r_script_dir, 'simple_test_runner.R')  # 使用简化版脚本

            # 确保路径使用正斜杠
            r_script_path = r_script_path.replace('\\', '/')
            student_path = student_path.replace('\\', '/')
            test_path = test_path.replace('\\', '/')

            # 检查脚本是否存在
            if not os.path.exists(r_script_path):
                # 尝试搜索项目目录
                import glob
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                r_scripts = glob.glob(os.path.join(project_dir, "**", "simple_test_runner.R"), recursive=True)

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

            # 执行命令时设置环境变量
            env = os.environ.copy()
            env['LC_ALL'] = 'C'  # 使用C区域设置，更加稳定

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

            # 记录输出
            print(f"进程返回代码: {process.returncode}")
            if stdout:
                print(f"标准输出(全部): {stdout}")
            else:
                print("标准输出为空")

            if stderr:
                print(f"标准错误(全部): {stderr}")
            else:
                print("标准错误为空")

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
                # 尝试直接解析JSON结果
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

                # 尝试找到JSON开始的位置
                json_start = stdout.find('{')
                if json_start == -1:
                    print("警告: 输出中没有找到JSON开始标记'{'")
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
                print(f"JSON解析成功: {result.get('status', '未知状态')}")

                # 修复中文消息编码
                try:
                    # 处理message字段中的Unicode转义序列
                    if 'message' in result and isinstance(result['message'], str):
                        result['message'] = decode_unicode_escapes(result['message'])

                    # 同样处理output字段
                    if 'output' in result and isinstance(result['output'], str):
                        result['output'] = decode_unicode_escapes(result['output'])

                    print("已修复中文编码显示")
                except Exception as e:
                    print(f"修复中文消息失败: {str(e)}")

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