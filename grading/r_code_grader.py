# grading/r_code_grader.py - 专门处理R代码评分
import os
import json
import tempfile
import logging
import subprocess
import sys
from flask import current_app

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('r_code_grader')


class RCodeGrader:
    """专门用于R编程题评分的类"""

    def __init__(self, timeout=30, memory_limit=500, cpu_limit=1.0):
        """初始化R代码评分器"""
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        logger.info(f"初始化R代码评分器: timeout={timeout}s, memory_limit={memory_limit}MB, cpu_limit={cpu_limit}")

    def get_r_executable(self):
        """获取R可执行文件路径"""
        # 优先使用conda环境中的R
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            # Windows路径
            r_path = os.path.join(conda_prefix, 'Scripts', 'R.exe')
            if os.path.exists(r_path):
                logger.info(f"找到conda环境中的R: {r_path}")
                return r_path

            # Linux/Mac路径
            r_path = os.path.join(conda_prefix, 'bin', 'R')
            if os.path.exists(r_path):
                logger.info(f"找到conda环境中的R: {r_path}")
                return r_path

        # 如果conda环境中没有R，尝试使用系统默认的R
        if sys.platform == 'win32':
            logger.info("使用系统默认的R.exe")
            return 'R.exe'  # 假设R在PATH中
        else:
            logger.info("使用系统默认的R")
            return 'R'  # 假设R在PATH中

    def clean_code(self, code_text):
        """清理代码中的非法字符和控制字符"""
        if not isinstance(code_text, str):
            return code_text

        # 替换常见的控制字符
        import re
        # 匹配所有控制字符（ASCII值小于32的字符，除了制表符、换行符和回车符）
        clean_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', code_text)

        # 确保使用统一的换行符
        clean_text = clean_text.replace('\r\n', '\n')

        return clean_text

    def grade(self, student_code, test_code, required_packages=None):
        """
        评分R代码，实现核心评分逻辑

        Args:
            student_code (str): 学生提交的R代码
            test_code (str): 测试用例代码
            required_packages (list): 需要的R包列表

        Returns:
            dict: 评分结果
        """
        logger.info("开始R代码测试")

        student_code = self.clean_code(student_code)
        test_code = self.clean_code(test_code)

        if required_packages is None:
            required_packages = []

        try:
            # 创建临时目录用于测试文件
            temp_dir = tempfile.mkdtemp(prefix="r_test_")
            logger.info(f"创建临时测试目录: {temp_dir}")

            # 创建学生代码文件
            student_file_path = os.path.join(temp_dir, "student_code.R")
            with open(student_file_path, 'w', encoding='utf-8') as f:
                f.write(student_code)
            logger.info(f"学生代码保存至: {student_file_path}")

            # 创建测试脚本
            test_file_path = os.path.join(temp_dir, "test_script.R")

            # 准备R测试脚本
            r_script = """
# 确保必要的库已安装
packages_to_install <- c("jsonlite")
for (pkg in packages_to_install) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org", quiet = TRUE)
  }
}
library(jsonlite)

# 加载测试所需的其他包
REQUIRED_PACKAGES

# 创建学生环境
student_env <- new.env()

# 设置错误处理函数
handle_error <- function(e) {
  write_result(list(
    status = "error",
    score = 0,
    max_score = 100,
    message = paste("执行错误:", e$message),
    debug_info = paste("错误类型:", class(e)[1], "\\n消息:", e$message)
  ))
  quit(status = 1)
}

# 写入结果函数
write_result <- function(result) {
  # 确保结果中包含所有必要字段
  if (is.null(result$status)) result$status <- "error"
  if (is.null(result$score)) result$score <- 0
  if (is.null(result$max_score)) result$max_score <- 100
  if (is.null(result$message)) result$message <- "未提供测试结果消息"

  # 写入JSON结果文件
  write_json(result, "RESULT_PATH", auto_unbox = TRUE, pretty = TRUE)
}

# 尝试执行学生代码
tryCatch({
  # 加载学生代码到学生环境
  student_code_text <- readLines("STUDENT_PATH")
  eval(parse(text = paste(student_code_text, collapse = "\\n")), envir = student_env)

  # 将student_env放入全局环境，供测试代码访问
  assign("student_env", student_env, envir = .GlobalEnv)

  # 执行测试代码前，创建输出捕获文件
  sink("TEST_OUTPUT_PATH")
  cat("====== 测试开始 ======\\n")

  # 打印学生函数源代码用于调试
  cat("学生提交的函数源代码:\\n")
  for (func_name in ls(student_env)) {
    if (is.function(student_env[[func_name]])) {
      cat(func_name, ":\\n")
      student_function_code <- deparse(student_env[[func_name]])
      cat(paste(student_function_code, collapse="\\n"))
      cat("\\n\\n")
    }
  }

  # 执行测试代码
  TEST_CODE_PLACEHOLDER

  # 测试代码执行完毕
  cat("====== 测试结束 ======\\n")
  sink()

  # 检查测试代码是否设置了test_result
  test_output <- readLines("TEST_OUTPUT_PATH")
  if (!exists("test_result")) {
    # 如果没有设置test_result，创建一个默认的错误结果
    test_result <- list(
      status = "error",
      score = 0,
      max_score = 100,
      message = "测试代码未设置test_result变量",
      debug_info = paste(test_output, collapse = "\\n")
    )
  } else {
    # 添加调试信息到test_result
    test_result$debug_info <- paste(test_output, collapse = "\\n")
  }

  # 写入结果
  write_result(test_result)

}, error = handle_error, warning = function(w) {
  cat("警告:", w$message, "\\n")
})
"""

            # 替换占位符
            r_script = r_script.replace("STUDENT_PATH", student_file_path.replace('\\', '/'))
            r_script = r_script.replace("TEST_CODE_PLACEHOLDER", test_code)
            r_script = r_script.replace("RESULT_PATH", os.path.join(temp_dir, "result.json").replace('\\', '/'))
            r_script = r_script.replace("TEST_OUTPUT_PATH",
                                        os.path.join(temp_dir, "test_output.txt").replace('\\', '/'))

            # 添加所需包
            packages_code = ""
            if required_packages:
                for pkg in required_packages:
                    packages_code += f"""
if (!requireNamespace("{pkg}", quietly = TRUE)) {{
  install.packages("{pkg}", repos = "https://cloud.r-project.org", quiet = TRUE)
}}
library({pkg})
"""
            r_script = r_script.replace("REQUIRED_PACKAGES", packages_code)

            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(r_script)
            logger.info(f"测试脚本保存至: {test_file_path}")

            # 获取R可执行文件路径
            r_executable = self.get_r_executable()
            logger.info(f"使用R可执行文件: {r_executable}")

            # 运行R脚本
            logger.info(f"开始执行R脚本，工作目录: {temp_dir}")

            process = subprocess.run(
                [r_executable, "--vanilla", "-f", test_file_path],
                cwd=temp_dir,
                timeout=self.timeout,  # 设置超时时间
                capture_output=True,
                text=True,
                encoding='utf-8'  # 明确指定UTF-8编码
            )

            logger.info(f"R进程返回码: {process.returncode}")
            if process.stdout and len(process.stdout.strip()) > 0:
                logger.debug(f"R标准输出: {process.stdout}")
            if process.stderr and len(process.stderr.strip()) > 0:
                logger.warning(f"R标准错误: {process.stderr}")

            # 读取结果文件
            result_file = os.path.join(temp_dir, "result.json")
            if os.path.exists(result_file):
                logger.info(f"找到结果文件: {result_file}")
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    logger.debug(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                # 如果结果文件不存在，可能是R脚本没有正确执行
                logger.error(f"未找到结果文件: {result_file}")
                result = {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': f'无法获取测试结果',
                    'debug_info': process.stdout + "\n" + process.stderr
                }

            # 如果存在测试输出文件，读取并添加到结果中
            test_output_file = os.path.join(temp_dir, "test_output.txt")
            if os.path.exists(test_output_file):
                with open(test_output_file, 'r', encoding='utf-8') as f:
                    test_output = f.read()
                    logger.debug(f"测试输出: {test_output}")
                    if 'debug_info' not in result:
                        result['debug_info'] = test_output

                    # 将测试输出作为单独的字段供显示
                    result['output'] = test_output

            return result

        except subprocess.TimeoutExpired:
            logger.error(f"R代码执行超时（超过{self.timeout}秒）")
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'代码执行超时（超过{self.timeout}秒）',
                'debug_info': ''
            }
        except Exception as e:
            logger.error(f"执行过程中出现异常: {e}")
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'执行异常: {str(e)}',
                'debug_info': ''
            }
        finally:
            # 清理临时文件
            try:
                # 列出所有临时文件用于调试
                logger.debug(f"临时目录内容: {os.listdir(temp_dir)}")
                for file in os.listdir(temp_dir):
                    os.unlink(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
                logger.info("临时文件已清理")
            except Exception as e:
                logger.warning(f"清理临时文件时出错: {e}")