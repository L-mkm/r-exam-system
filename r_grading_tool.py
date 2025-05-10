import os
import sys
import json
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块 - 使用修复版沙箱
from utils.sandbox_fix import RCodeSandbox

# 不再导入r_setup，改为使用r_env_config (如果需要的话)
import r_env_config


def run_r_grading_test(student_code, test_code, timeout=10, required_packages=None):
    """
    直接测试R代码评分功能
    """
    print("=" * 50)
    print("开始测试R代码评分")
    print(f"学生代码:\n{student_code}")
    print("-" * 30)
    print(f"测试代码:\n{test_code}")
    print("-" * 30)

    # 检测所需的R包
    if required_packages is None:
        required_packages = []
        # 自动检测常用包
        if "dplyr" in student_code:
            required_packages.append("dplyr")
        if "ggplot2" in student_code:
            required_packages.append("ggplot2")
        if "tidyr" in student_code:
            required_packages.append("tidyr")

    # 创建沙箱，并传入所需包信息
    sandbox = RCodeSandbox(timeout=timeout, required_packages=required_packages)

    # 执行评分
    result = sandbox.execute(student_code, test_code)

    # 打印结果
    print("\n评分结果:")
    print(f"状态: {result.get('status', '未知')}")
    print(f"得分: {result.get('score', 0)}/{result.get('max_score', 100)}")
    print(f"消息: {result.get('message', '无')}")
    print(f"输出:\n{result.get('output', '无')}")

    return result


def run_basic_test():
    """运行最基本的测试"""
    # 最简单的学生代码
    student_code = """
    x <- 5
    y <- 10
    result <- x + y
    """

    # 最简单的测试代码
    test_code = """
    test_result <- list(
      status = "success",
      score = if(exists("result", envir=student_env) && student_env$result == 15) 100 else 0,
      max_score = 100,
      message = if(exists("result", envir=student_env) && student_env$result == 15) "Correct" else "Wrong"
    )
    """

    return run_r_grading_test(student_code, test_code)


def run_function_test():
    """测试函数评分"""
    # 学生的函数实现
    student_code = """
    calculate_sum <- function(numbers) {
      if(length(numbers) == 0) {
        return(0)
      }
      return(sum(numbers))
    }
    """

    # 测试代码
    test_code = """
    # 定义测试用例
    test_cases <- list(
      list(input = c(1, 2, 3), expected = 6),
      list(input = c(10, 20), expected = 30),
      list(input = c(-5, 5), expected = 0),
      list(input = numeric(0), expected = 0)
    )

    # 要测试的函数名称
    function_name <- "calculate_sum"

    # 初始化测试结果
    test_result <- list(
      status = "success",
      score = 0,
      max_score = 100,
      message = ""
    )

    # 检查函数是否存在
    if (!exists(function_name, envir=student_env) || !is.function(student_env[[function_name]])) {
      test_result$status <- "error"
      test_result$message <- paste0("未找到函数 '", function_name, "'")
    } else {
      # 运行测试用例
      correct_count <- 0
      failed_tests <- character(0)

      for (i in 1:length(test_cases)) {
        case <- test_cases[[i]]

        result <- tryCatch({
          # 调用学生函数
          student_result <- student_env[[function_name]](case$input)

          # 检查结果
          if (identical(student_result, case$expected)) {
            correct_count <- correct_count + 1
            TRUE
          } else {
            failed_tests <- c(failed_tests, 
                             sprintf("测试 %d: 输入 %s, 期望 %s, 得到 %s", 
                                    i, 
                                    paste(case$input, collapse=","), 
                                    case$expected, 
                                    student_result))
            FALSE
          }
        }, error = function(e) {
          failed_tests <<- c(failed_tests, 
                           sprintf("测试 %d: 输入 %s, 出错: %s", 
                                  i, 
                                  paste(case$input, collapse=","), 
                                  e$message))
          FALSE
        })
      }

      # 计算分数
      test_result$score <- (correct_count / length(test_cases)) * 100

      if (length(failed_tests) > 0) {
        test_result$message <- paste0("通过 ", correct_count, " 个测试，共 ", length(test_cases), " 个。\\n失败的测试：\\n", paste(failed_tests, collapse="\\n"))
      } else {
        test_result$message <- paste0("所有测试通过！共 ", length(test_cases), " 个测试。")
      }
    }
    """

    return run_r_grading_test(student_code, test_code)


def run_data_processing_test():
    """测试数据处理题"""
    # 学生代码
    student_code = """
    # 清洗数据（移除NA值）
    clean_data <- na.omit(data)

    # 计算统计信息
    library(dplyr)
    
    # 打印调试信息
    print("开始数据处理")
    print(paste("数据行数:", nrow(clean_data)))

    processed_data <- clean_data %>%
      group_by(customer_id) %>%
      summarize(
        total_amount = sum(amount),
        average_amount = mean(amount),
        purchase_count = n()
      ) %>%
      arrange(desc(total_amount))
    # 打印变量确认
    print("数据处理完成")
    print(paste("processed_data行数:", nrow(processed_data)))
    """

    # 测试代码
    test_code = """
    # 创建测试数据
    data <- data.frame(
      customer_id = c(1, 1, 2, 2, 2, 3, 3, 4, NA),
      date = as.Date(c("2023-01-01", "2023-01-15", "2023-01-05", "2023-01-20", "2023-02-10",
                      "2023-01-10", "2023-02-15", "2023-01-30", "2023-02-01")),
      amount = c(100, 150, 200, 100, 300, 50, 50, 400, 250)
    )

    # 将测试数据加入到学生环境
    assign("data", data, envir=student_env)
    
    # 打印调试信息
    print("测试开始")
    print(paste("测试数据行数:", nrow(data)))
    
    # 打印学生环境中的所有变量
    all_vars <- ls(student_env)
    print(paste("学生环境变量:", paste(all_vars, collapse=", ")))

    # 检查学生是否创建了processed_data
    if (!exists("processed_data", envir=student_env)) {
    print("错误: processed_data变量不存在")
    
    # 尝试查看错误原因
      if ("clean_data" %in% all_vars) {
        print("clean_data存在，检查后续处理")
        print(paste("clean_data行数:", nrow(student_env$clean_data)))
      } else {
        print("clean_data不存在，检查初始处理")
      }
      
      test_result <- list(
        status = "error",
        score = 0,
        max_score = 100,
        message = "未找到变量 'processed_data'"
      )
    } else {
      # 获取学生处理的数据
      student_data <- student_env$processed_data
      print("找到processed_data")
      print(paste("数据类型:", class(student_data)[1]))
      print(paste("列数:", ncol(student_data)))
      print(paste("行数:", nrow(student_data)))

      # 简单的检查
      if (is.data.frame(student_data) && ncol(student_data) >= 4 && nrow(student_data) == 4) {
        test_result <- list(
          status = "success",
          score = 100,
          max_score = 100,
          message = "数据处理结果正确!"
        )
      } else {
        test_result <- list(
          status = "error",
          score = 0,
          max_score = 100,
          message = paste("数据结构不正确，列数:", ncol(student_data), "行数:", nrow(student_data))
        )
      }
    }
    """

    # 指定需要的包
    required_packages = ["dplyr"]

    return run_r_grading_test(student_code, test_code, required_packages=required_packages)


def run_invalid_code_test():
    """测试无效代码的情况"""
    # 错误的学生代码
    student_code = """
    x <- 5
    y <- "hello"
    result <- x + y  # 这会产生错误
    """

    # 测试代码
    test_code = """
    test_result <- list(
      status = "success",
      score = if(exists("result", envir=student_env) && student_env$result == 15) 100 else 0,
      max_score = 100,
      message = if(exists("result", envir=student_env) && student_env$result == 15) "正确" else "错误"
    )
    """

    return run_r_grading_test(student_code, test_code)


def run_custom_test(student_code, test_code, required_packages=None):
    """运行自定义测试"""
    return run_r_grading_test(student_code, test_code, required_packages=required_packages)


def main():
    parser = argparse.ArgumentParser(description='R代码评分测试工具')
    parser.add_argument('--test', type=str, choices=['basic', 'function', 'data', 'invalid', 'all'],
                        help='要运行的测试类型', default='all')
    args = parser.parse_args()

    if args.test == 'basic' or args.test == 'all':
        print("\n==== 运行基本测试 ====")
        run_basic_test()

    if args.test == 'function' or args.test == 'all':
        print("\n==== 运行函数测试 ====")
        run_function_test()

    if args.test == 'data' or args.test == 'all':
        print("\n==== 运行数据处理测试 ====")
        run_data_processing_test()

    if args.test == 'invalid' or args.test == 'all':
        print("\n==== 运行无效代码测试 ====")
        run_invalid_code_test()

    if args.test not in ['basic', 'function', 'data', 'invalid', 'all']:
        print("R代码评分测试工具")
        print("选择测试类型:")
        print("1. 基本变量测试")
        print("2. 函数测试")
        print("3. 数据处理测试")
        print("4. 错误代码测试")
        print("5. 自定义测试")

        choice = input("请输入选项 (1-5): ")

        if choice == "1":
            run_basic_test()
        elif choice == "2":
            run_function_test()
        elif choice == "3":
            run_data_processing_test()
        elif choice == "4":
            run_invalid_code_test()
        elif choice == "5":
            print("\n请输入学生代码 (输入完成后按Ctrl+D或Ctrl+Z+Enter结束):")
            student_lines = []
            while True:
                try:
                    line = input()
                    student_lines.append(line)
                except EOFError:
                    break

            student_code = "\n".join(student_lines)

            print("\n请输入测试代码 (输入完成后按Ctrl+D或Ctrl+Z+Enter结束):")
            test_lines = []
            while True:
                try:
                    line = input()
                    test_lines.append(line)
                except EOFError:
                    break

            test_code = "\n".join(test_lines)

            run_custom_test(student_code, test_code)
        else:
            print("无效选项")


# 当脚本直接运行时才执行main函数
if __name__ == "__main__":
    main()