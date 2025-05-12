"""
R编程题自动评分测试脚本 - 最终修复版
此脚本用于测试R编程题的自动评分功能，无需通过Web界面
"""
import json
import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('r_grading_test')


def get_r_executable():
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


def run_r_code_test(student_code, test_code, required_packages=None):
    """
    运行R代码测试，返回测试结果

    参数:
        student_code (str): 学生提交的R代码
        test_code (str): 用于测试学生代码的R测试代码
        required_packages (list): 测试所需的R包列表

    返回:
        dict: 包含测试结果的字典
    """
    logger.info("开始R代码测试")

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
  if(exists("calculate_mean", envir=student_env)) {
    student_function_code <- deparse(student_env$calculate_mean)
    cat(paste(student_function_code, collapse="\\n"))
  } else {
    cat("未找到calculate_mean函数!\\n")
  }
  cat("\\n\\n")

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
        r_script = r_script.replace("TEST_OUTPUT_PATH", os.path.join(temp_dir, "test_output.txt").replace('\\', '/'))

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
        r_executable = get_r_executable()
        logger.info(f"使用R可执行文件: {r_executable}")

        # 运行R脚本
        logger.info(f"开始执行R脚本，工作目录: {temp_dir}")

        process = subprocess.run(
            [r_executable, "--vanilla", "-f", test_file_path],
            cwd=temp_dir,
            timeout=30,  # 设置超时时间
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

        return result

    except subprocess.TimeoutExpired:
        logger.error("R代码执行超时（超过30秒）")
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': '代码执行超时（超过30秒）',
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


# 示例学生代码（正确答案）
CORRECT_STUDENT_CODE = """
calculate_mean <- function(numbers) {
  if (length(numbers) == 0) {
    return(NA)
  }

  if (any(is.na(numbers))) {
    return(NA)
  }

  return(sum(numbers) / length(numbers))
}
"""

# 示例学生代码（错误答案1：不处理空向量）
WRONG_STUDENT_CODE_1 = """
calculate_mean <- function(numbers) {
  return(sum(numbers) / length(numbers))
}
"""

# 示例学生代码（错误答案2：不处理NA值）
WRONG_STUDENT_CODE_2 = """
calculate_mean <- function(numbers) {
  if (length(numbers) == 0) {
    return(NA)
  }
  return(sum(numbers) / length(numbers))
}
"""

# 改进后的测试代码 - 修复了条件长度问题
TEST_CODE = """
# 测试 calculate_mean 函数

# 更明确的测试函数
test_student_function <- function() {
  # 测试用例
  test_cases <- list(
    list(
      name = "基本测试",
      input = c(1, 2, 3, 4, 5),
      expected = 3
    ),
    list(
      name = "空向量",
      input = numeric(0),
      expected = NA
    ),
    list(
      name = "包含NA值",
      input = c(1, 2, NA, 4),
      expected = NA
    ),
    list(
      name = "单个值",
      input = 5,
      expected = 5
    ),
    list(
      name = "大数测试",
      input = c(1000000, 2000000, 3000000),
      expected = 2000000
    )
  )

  # 直接测试边缘情况（无需依赖测试用例）
  cat("直接测试关键边缘情况:\\n")

  # 检查函数是否存在
  if (!exists("calculate_mean", envir=student_env)) {
    cat("错误: 函数 'calculate_mean' 不存在\\n")
    return(list(
      passed = 0,
      total = length(test_cases),
      details = "函数 'calculate_mean' 不存在"
    ))
  }

  # 获取学生定义的函数
  student_function <- get("calculate_mean", envir=student_env)

  # 如果不是函数则返回错误
  if (!is.function(student_function)) {
    cat("错误: 'calculate_mean' 不是一个函数\\n")
    return(list(
      passed = 0,
      total = length(test_cases),
      details = "'calculate_mean' 不是一个函数"
    ))
  }

  # 直接测试关键边缘情况
  cat("▶ 直接测试空向量:\\n")
  tryCatch({
    empty_vector_result <- student_function(numeric(0))
    cat("  输入: numeric(0)\\n")
    cat("  输出: ", if(is.na(empty_vector_result)) "NA" else as.character(empty_vector_result), "\\n")
    cat("  预期: NA\\n")
    cat("  结果: ", if(is.na(empty_vector_result)) "✓ 正确" else "✗ 错误", "\\n\\n")
  }, error = function(e) {
    cat("  错误: ", e$message, "\\n")
    cat("  结果: ✗ 错误\\n\\n")
  })

  cat("▶ 直接测试含NA值向量:\\n")
  tryCatch({
    na_vector_result <- student_function(c(1, 2, NA, 4))
    cat("  输入: c(1, 2, NA, 4)\\n")
    cat("  输出: ", if(is.na(na_vector_result)) "NA" else as.character(na_vector_result), "\\n")
    cat("  预期: NA\\n")
    cat("  结果: ", if(is.na(na_vector_result)) "✓ 正确" else "✗ 错误", "\\n\\n")
  }, error = function(e) {
    cat("  错误: ", e$message, "\\n")
    cat("  结果: ✗ 错误\\n\\n")
  })

  cat("▶ 增强检测: 检查函数是否明确处理空向量和NA值\\n")
  # 修复这里的代码，使用any()确保返回单一结果
  func_code <- paste(deparse(student_function), collapse=" ")
  has_empty_check <- any(grepl("length\\\\(.*\\\\)\\\\s*==\\\\s*0", func_code))
  has_na_check <- any(grepl("is\\\\.na|any\\\\(.*na", func_code))

  cat("  函数包含空向量检查: ", if(has_empty_check) "✓ 是" else "✗ 否", "\\n")
  cat("  函数包含NA值检查: ", if(has_na_check) "✓ 是" else "✗ 否", "\\n\\n")

  # 执行测试
  passed_count <- 0
  feedback <- character(0)

  cat("标准测试用例结果:\\n")

  for (i in 1:length(test_cases)) {
    test_case <- test_cases[[i]]
    passed <- FALSE

    # 打印测试用例信息
    cat("▶ 测试 '", test_case$name, "':\\n", sep="")
    cat("  输入: ", paste(format(test_case$input, trim=TRUE), collapse=", "), "\\n", sep="")
    cat("  预期: ", if(is.na(test_case$expected)) "NA" else format(test_case$expected, trim=TRUE), "\\n", sep="")

    # 尝试调用函数
    result <- tryCatch({
      # 调用学生函数
      actual <- student_function(test_case$input)

      # 打印实际结果
      cat("  实际: ", if(is.na(actual)) "NA" else format(actual, trim=TRUE), "\\n", sep="")

      # 检查结果是否正确
      if (is.na(test_case$expected) && is.na(actual)) {
        # 两者都是NA，视为相等
        passed <- TRUE
        message <- "通过"
      } else if (is.na(test_case$expected) || is.na(actual)) {
        # 一个是NA，一个不是，视为不等
        passed <- FALSE
        message <- paste0("期望 ", 
                       if(is.na(test_case$expected)) "NA" else as.character(test_case$expected), 
                       ", 得到 ", 
                       if(is.na(actual)) "NA" else as.character(actual))
      } else if (is.numeric(test_case$expected) && is.numeric(actual)) {
        # 数值比较，允许小的误差
        if (abs(actual - test_case$expected) < 1e-6) {
          passed <- TRUE
          message <- "通过"
        } else {
          passed <- FALSE
          message <- paste0("期望 ", test_case$expected, ", 得到 ", actual)
        }
      } else {
        # 其他类型，使用严格相等判断
        if (identical(actual, test_case$expected)) {
          passed <- TRUE
          message <- "通过"
        } else {
          passed <- FALSE
          message <- paste0("期望 ", toString(test_case$expected), 
                         ", 得到 ", toString(actual))
        }
      }

      list(passed = passed, message = message)
    }, error = function(e) {
      cat("  错误: ", e$message, "\\n", sep="")
      list(passed = FALSE, message = paste0("函数执行出错: ", e$message))
    })

    passed <- result$passed
    message <- result$message

    # 显示结果
    cat("  结果: ", if(passed) "✓ 通过" else paste0("✗ ", message), "\\n\\n", sep="")

    # 记录测试结果
    if (passed) {
      passed_count <- passed_count + 1
    } else {
      feedback <- c(feedback, paste0("测试 '", test_case$name, "': ", message))
    }
  }

  # 直接检查结果 (对关键测试进行加权)
  empty_vector_correct <- tryCatch(is.na(student_function(numeric(0))), error = function(e) FALSE)
  na_values_correct <- tryCatch(is.na(student_function(c(1, 2, NA, 4))), error = function(e) FALSE)

  # 检查代码结构（注意：这只是启发式的检查，不是绝对可靠的）
  code_structure_score <- 0
  if (has_empty_check) code_structure_score <- code_structure_score + 1
  if (has_na_check) code_structure_score <- code_structure_score + 1

  # 如果关键测试失败，覆盖通过计数
  if (!empty_vector_correct || !na_values_correct) {
    # 减去错误的测试数，每个关键错误至少扣除1个测试的分数
    key_errors <- (!empty_vector_correct) + (!na_values_correct)

    # 确保至少有一些测试通过来给出部分分数
    passed_count = max(0, passed_count - key_errors)

    # 添加关键错误的反馈
    if (!empty_vector_correct) {
      feedback <- c(feedback, "关键错误: 不正确处理空向量")
    }
    if (!na_values_correct) {
      feedback <- c(feedback, "关键错误: 不正确处理含NA值的向量")
    }
  }

  # 计算加权分数
  # 测试用例通过: 60%
  # 边缘情况直接测试: 30%
  # 代码结构检查: 10%
  test_case_score <- passed_count / length(test_cases) * 60
  edge_case_score <- (as.integer(empty_vector_correct) + as.integer(na_values_correct)) / 2 * 30
  structure_score <- code_structure_score / 2 * 10

  # 汇总分数，四舍五入到整数
  total_score <- round(test_case_score + edge_case_score + structure_score)

  cat("分数明细:\\n")
  cat("- 测试用例分数: ", test_case_score, "/60\\n")
  cat("- 边缘情况分数: ", edge_case_score, "/30\\n")
  cat("- 代码结构分数: ", structure_score, "/10\\n")
  cat("总分: ", total_score, "/100\\n")

  # 返回最终结果
  return(list(
    passed = passed_count,
    total = length(test_cases),
    score = total_score,
    details = if (length(feedback) == 0) 
      paste0("通过所有测试! (", passed_count, "/", length(test_cases), ")")
    else 
      paste0("通过 ", passed_count, "/", length(test_cases), " 个测试\\n",
           paste(feedback, collapse = "\\n"))
  ))
}

# 执行测试并设置结果
test_output <- test_student_function()
cat("\\n最终测试结果:\\n")
cat(paste0("通过测试: ", test_output$passed, "/", test_output$total, "\\n"))
cat(paste0("总得分: ", test_output$score, "/100\\n"))
cat(paste0("详情: ", test_output$details, "\\n"))

# 设置最终测试结果
test_result <- list(
  status = "success",
  score = test_output$score,
  max_score = 100,
  message = test_output$details
)
"""


def print_separator():
    """打印分隔线"""
    print("=" * 60)


def print_section_title(title):
    """打印带有分隔线的区块标题"""
    print("\n" + title)
    print("-" * 60)


def run_test_case(title, student_code):
    """运行一个测试用例并打印结果"""
    print_section_title(title)
    result = run_r_code_test(student_code, TEST_CODE)
    print(f"分数: {result.get('score', 0)}/100")
    print(f"消息: {result.get('message', '')}")
    if 'debug_info' in result and result['debug_info']:
        lines = result['debug_info'].split('\n')
        important_lines = [line for line in lines if
                           '▶' in line or '直接测试' in line or '分数明细' in line or '总分' in line]
        if important_lines:
            print("\n重要测试输出:")
            for line in important_lines:
                print(line)
    return result


def main():
    """主函数"""
    print("开始测试R代码自动评分功能")
    print_separator()

    # 测试正确的代码
    result1 = run_test_case("测试正确的学生代码", CORRECT_STUDENT_CODE)

    # 测试错误代码1
    result2 = run_test_case("测试错误的学生代码1（不处理空向量）", WRONG_STUDENT_CODE_1)

    # 测试错误代码2
    result3 = run_test_case("测试错误的学生代码2（不处理NA值）", WRONG_STUDENT_CODE_2)

    # 总结测试结果
    print_separator()
    print("\n测试结果汇总:")
    print(f"正确代码: {result1.get('score', 0)}/100")
    print(f"错误代码1 (不处理空向量): {result2.get('score', 0)}/100")
    print(f"错误代码2 (不处理NA值): {result3.get('score', 0)}/100")
    print("\n所有测试完成！正确的代码应得到满分，错误的代码应得到部分分。")


if __name__ == "__main__":
    main()