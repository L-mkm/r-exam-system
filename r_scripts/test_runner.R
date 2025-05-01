# R语言考试运行器

# 参数定义:
# 1. student_code: 学生提交的R代码
# 2. test_code: 测试用例代码
# 3. timeout: 执行超时时间(秒)

run_test <- function(student_code, test_code, timeout = 10) {
  # 创建临时环境运行学生代码
  student_env <- new.env()

  # 捕获输出信息
  output <- capture.output({

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
  })

  # 运行测试代码
  if (result$status != "error") {
    test_env <- new.env(parent = student_env)
    test_result <- tryCatch({
      # 设置超时保护
      setTimeLimit(timeout)
      # 评估测试代码
      eval(parse(text = test_code), envir = test_env)
      # 重置超时
      setTimeLimit()

      # 检查测试环境中是否有测试结果
      if (exists("test_result", envir = test_env)) {
        get("test_result", envir = test_env)
      } else {
        list(
          status = "success",
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
  } else {
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

  # 转换为JSON字符串
  jsonlite::toJSON(final_result, auto_unbox = TRUE)
}

# 如果从命令行运行，则解析参数
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) >= 3) {
    student_code_file <- args[1]
    test_code_file <- args[2]
    timeout <- as.numeric(args[3])

    student_code <- readLines(student_code_file, warn = FALSE)
    student_code <- paste(student_code, collapse = "\n")

    test_code <- readLines(test_code_file, warn = FALSE)
    test_code <- paste(test_code, collapse = "\n")

    result <- run_test(student_code, test_code, timeout)
    cat(result)
  } else {
    cat('{"status": "error", "message": "参数不足", "score": 0, "max_score": 100}')
  }
}