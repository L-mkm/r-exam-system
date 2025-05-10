# 简化版R语言考试测试运行器 (改进版)

# 设置编码和区域
options(encoding = "native.enc")
Sys.setlocale("LC_ALL", "C")

# 导入必要的包
suppressPackageStartupMessages({
  if (!require("jsonlite")) install.packages("jsonlite", repos="https://cloud.r-project.org", quiet=TRUE)
})

# 创建调试日志函数
debug_log <- function(...) {
  cat("[DEBUG] ", ..., "\n", file=stderr())
}

# 定义安全运行函数
run_test <- function(student_code_file, test_code_file, timeout = 10) {
  # 读取文件内容
  tryCatch({
    debug_log("开始读取代码文件")
    student_code <- paste(readLines(student_code_file, warn = FALSE, encoding = "UTF-8"), collapse="\n")
    test_code <- paste(readLines(test_code_file, warn = FALSE, encoding = "UTF-8"), collapse="\n")

    debug_log("成功读取文件")
    debug_log("学生代码长度:", nchar(student_code))

    # 检查学生代码中可能需要的包
    packages_needed <- character(0)
    if (grepl("dplyr", student_code)) {
      packages_needed <- c(packages_needed, "dplyr")
      debug_log("检测到需要 dplyr 包")
    }
    if (grepl("ggplot2", student_code)) {
      packages_needed <- c(packages_needed, "ggplot2")
      debug_log("检测到需要 ggplot2 包")
    }

    # 预加载可能需要的包
    for (pkg in packages_needed) {
      debug_log("尝试加载包:", pkg)
      if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
        debug_log("包不可用，尝试安装:", pkg)
        install.packages(pkg, repos="https://cloud.r-project.org", quiet=TRUE)
        if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
          debug_log("安装失败:", pkg)
        } else {
          debug_log("安装并加载成功:", pkg)
        }
      } else {
        debug_log("包加载成功:", pkg)
      }
    }

    # 创建临时环境运行学生代码
    debug_log("创建学生环境")
    student_env <- new.env()

    # 捕获输出
    debug_log("开始执行学生代码")
    output <- capture.output({
      # 执行学生代码
      tryCatch({
        # 直接在学生环境中评估代码
        eval(parse(text = student_code), envir = student_env)
        debug_log("学生代码执行成功")

        # 列出学生环境中的变量
        vars <- ls(student_env)
        debug_log("学生环境中的变量:", paste(vars, collapse=", "))

        # 检查是否创建了processed_data
        if ("processed_data" %in% vars) {
          debug_log("找到processed_data变量")
          # 检查变量类型
          data_class <- class(student_env$processed_data)
          debug_log("processed_data类型:", paste(data_class, collapse=", "))
        } else {
          debug_log("未找到processed_data变量!")
        }

      }, error = function(e) {
        debug_log("学生代码执行错误:", e$message)
        return(toJSON(list(
          status = "error",
          score = 0,
          max_score = 100,
          message = paste("学生代码执行错误:", e$message),
          output = ""
        ), auto_unbox = TRUE))
      })

      # 执行测试代码
      debug_log("创建测试环境")
      test_env <- new.env(parent = student_env)

      tryCatch({
        debug_log("开始执行测试代码")
        eval(parse(text = test_code), envir = test_env)
        debug_log("测试代码执行成功")

        # 检查测试结果
        if (exists("test_result", envir = test_env)) {
          debug_log("测试结果已生成")
          result <- test_env$test_result
          if (is.null(result$output)) {
            result$output <- ""
          }
          debug_log("测试状态:", result$status)
          debug_log("测试分数:", result$score)
          return(toJSON(result, auto_unbox = TRUE))
        } else {
          debug_log("测试代码未生成test_result")
          return(toJSON(list(
            status = "error",
            score = 0,
            max_score = 100,
            message = "测试代码未生成test_result",
            output = ""
          ), auto_unbox = TRUE))
        }
      }, error = function(e) {
        debug_log("测试代码执行错误:", e$message)
        return(toJSON(list(
          status = "error",
          score = 0,
          max_score = 100,
          message = paste("测试代码执行错误:", e$message),
          output = ""
        ), auto_unbox = TRUE))
      })
    })

    # 返回输出
    paste(output, collapse="\n")
  }, error = function(e) {
    debug_log("文件处理错误:", e$message)
    toJSON(list(
      status = "error",
      score = 0,
      max_score = 100,
      message = paste("文件处理错误:", e$message),
      output = ""
    ), auto_unbox = TRUE)
  })
}

# 运行测试
args <- commandArgs(trailingOnly = TRUE)
if (length(args) >= 2) {
  debug_log("开始运行测试，参数数量:", length(args))
  student_code_file <- args[1]
  test_code_file <- args[2]
  timeout <- if (length(args) >= 3) as.numeric(args[3]) else 10

  debug_log("学生代码文件:", student_code_file)
  debug_log("测试代码文件:", test_code_file)
  debug_log("超时设置:", timeout)

  result <- run_test(student_code_file, test_code_file, timeout)
  cat(result)
} else {
  debug_log("参数不足")
  cat('{"status": "error", "message": "参数不足", "score": 0, "max_score": 100}')
}