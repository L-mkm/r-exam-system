# 增强版R语言考试测试运行器

# 导入必要的包
suppressPackageStartupMessages({
  if (!require("jsonlite")) install.packages("jsonlite", repos="https://cloud.r-project.org")
})

# 定义安全运行函数
safe_run_test <- function(student_code, test_code, timeout = 10) {
  # 创建临时环境运行学生代码
  student_env <- new.env()

  # 禁用危险函数
  safe_student_env <- function(env) {
    # 禁用系统调用
    env$system <- function(...) stop("禁止使用system函数")
    env$shell <- function(...) stop("禁止使用shell函数")
    env$shell.exec <- function(...) stop("禁止使用shell.exec函数")

    # 禁用文件操作
    env$file.remove <- function(...) stop("禁止使用file.remove函数")
    env$unlink <- function(...) stop("禁止使用unlink函数")
    env$file.rename <- function(...) stop("禁止使用file.rename函数")
    env$file.create <- function(...) stop("禁止使用file.create函数")

    # 限制包加载
    env$library <- function(package, ...) {
      # 允许的安全包列表
      allowed_packages <- c(
        "base", "stats", "graphics", "grDevices", "utils", "datasets",
        "methods", "grid", "MASS", "lattice", "ggplot2", "dplyr",
        "tidyr", "stringr", "lubridate", "forcats"
      )

      package_name <- as.character(substitute(package))
      if (!package_name %in% allowed_packages) {
        stop(sprintf("禁止加载包 '%s'. 仅允许: %s",
                     package_name,
                     paste(allowed_packages, collapse=", ")))
      }

      base::library(package, ...)
    }

    # 返回修改后的环境
    return(env)
  }

  # 应用安全限制
  student_env <- safe_student_env(student_env)

  # 捕获输出信息
  output <- character(0)
  output_connection <- textConnection("output", "w", local = TRUE)
  sink(output_connection, type = "output")
  sink(output_connection, type = "message")

  # 尝试执行学生代码
  result <- tryCatch({
    # 设置超时保护
    setTimeLimit(timeout)

    # 评估学生代码
    eval(parse(text = student_code), envir = student_env)

    # 重置超时
    setTimeLimit()

    list(status = "success", message = "代码执行成功")
  }, error = function(e) {
    list(status = "error", message = paste("代码执行错误:", e$message))
  }, warning = function(w) {
    list(status = "warning", message = paste("代码产生警告:", w$message))
  }, finally = {
    # 确保重置超时
    setTimeLimit()
  })

  # 重置输出捕获
  sink(type = "message")
  sink(type = "output")
  close(output_connection)

  # 运行测试代码
  if (result$status != "error") {
    test_env <- new.env(parent = student_env)

    test_tryCatch <- tryCatch({
      # 设置超时保护
      setTimeLimit(timeout)

      # 评估测试代码
      eval(parse(text = test_code), envir = test_env)

      # 重置超时
      setTimeLimit()

      # 检查测试环境中是否有测试结果
      if (exists("test_result", envir = test_env)) {
        test_result <- get("test_result", envir = test_env)

        # 验证测试结果的结构
        required_fields <- c("status", "score", "max_score", "message")
        missing_fields <- required_fields[!required_fields %in% names(test_result)]

        if (length(missing_fields) > 0) {
          list(
            status = "error",
            score = 0,
            max_score = 100,
            message = paste("测试结果缺少必要字段:",
                          paste(missing_fields, collapse=", "))
          )
        } else {
          # 返回完整的测试结果
          test_result
        }
      } else {
        # 没有测试结果
        list(
          status = "error",
          score = 0,
          max_score = 100,
          message = "测试代码未返回结果"
        )
      }
    }, error = function(e) {
      list(
        status = "error",
        score = 0,
        max_score = 100,
        message = paste("测试执行错误:", e$message)
      )
    }, finally = {
      # 确保重置超时
      setTimeLimit()
    })

    # 使用测试结果
    test_result <- test_tryCatch
  } else {
    # 学生代码执行失败，无法运行测试
    test_result <- list(
      status = "error",
      score = 0,
      max_score = 100,
      message = result$message
    )
  }

  # 构建最终结果
  final_result <- list(
    status = test_result$status,
    score = test_result$score,
    max_score = test_result$max_score,
    message = test_result$message,
    output = paste(output, collapse = "\n")
  )

  # 返回JSON格式的结果
  return(toJSON(final_result, auto_unbox = TRUE))
}

# 主函数：从命令行参数读取文件路径
run_test_from_files <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) < 2) {
    cat('{"status": "error", "message": "参数不足", "score": 0, "max_score": 100}')
    return(1)
  }

  student_code_file <- args[1]
  test_code_file <- args[2]
  timeout <- 10  # 默认超时时间

  if (length(args) >= 3) {
    timeout_arg <- as.numeric(args[3])
    if (!is.na(timeout_arg) && timeout_arg > 0) {
      timeout <- timeout_arg
    }
  }

  # 读取文件内容
  tryCatch({
    student_code <- paste(readLines(student_code_file), collapse = "\n")
    test_code <- paste(readLines(test_code_file), collapse = "\n")

    # 执行测试
    result <- safe_run_test(student_code, test_code, timeout)
    cat(result)

    return(0)
  }, error = function(e) {
    cat(paste0('{"status": "error", "message": "读取文件失败: ',
             gsub('"', '\\\\"', e$message),
             '", "score": 0, "max_score": 100}'))
    return(1)
  })
}

# 如果从命令行运行，则执行测试
if (!interactive()) {
  run_test_from_files()
}