# test_runner.R - 增强版R语言考试运行器

# 参数定义:
# 1. student_code_file: 学生提交的R代码文件路径
# 2. test_code_file: 测试用例代码文件路径
# 3. timeout: 执行超时时间(秒)

# 加载必要的包
tryCatch({
  # 检查是否安装了jsonlite包，没有则安装
  if (!require("jsonlite", quietly = TRUE)) {
    install.packages("jsonlite", repos = "https://cloud.r-project.org", quiet = TRUE)
    library(jsonlite)
  }
}, error = function(e) {
  # 如果安装失败，打印错误
  cat("加载jsonlite包失败:", e$message, "\n")
})

# 测试运行函数
run_test <- function(student_code, test_code, timeout = 10) {
  # 创建用于存储测试输出的变量
  all_output <- character(0)

  # 定义输出捕获函数
  capture_output <- function() {
    output_buffer <- character(0)
    output_conn <- textConnection("output_buffer", "w", local = TRUE)

    # 保存当前的输出设置
    old_stdout <- stdout()
    old_stderr <- stderr()

    # 重定向输出
    sink(output_conn, type = "output")
    sink(output_conn, type = "message")

    # 返回一个函数用于获取输出并恢复原始设置
    function() {
      sink(type = "message", NULL)
      sink(type = "output", NULL)

      close(output_conn)
      return(output_buffer)
    }
  }

  # 创建临时环境运行学生代码
  student_env <- new.env()

  # 记录开始时间
  start_time <- Sys.time()

  # 设置超时处理
  timeout_handler <- function(timeout_secs) {
    # 创建计时器函数
    start_time <- Sys.time()
    return(function() {
      current_time <- Sys.time()
      elapsed <- as.numeric(difftime(current_time, start_time, units = "secs"))
      if (elapsed > timeout_secs) {
        stop(sprintf("代码执行超时，超过了设定的 %d 秒限制", timeout_secs), call. = FALSE)
      }
    })
  }

  # 创建计时器
  check_time <- timeout_handler(timeout)

  # 启动输出捕获
  get_output <- capture_output()

  # 尝试执行学生代码
  student_result <- tryCatch({
    # 每行代码执行前检查超时
    expr <- parse(text = student_code)
    for (i in seq_along(expr)) {
      check_time()
      eval(expr[i], envir = student_env)
    }

    list(status = "success", message = "代码执行成功")
  }, error = function(e) {
    list(status = "error", message = paste("代码执行错误:", e$message))
  }, warning = function(w) {
    list(status = "warning", message = paste("代码产生警告:", w$message))
  })

  # 获取学生代码执行的输出
  student_output <- get_output()
  all_output <- c(all_output, student_output)

  # 如果学生代码执行成功，则运行测试代码
  if (student_result$status != "error") {
    # 创建测试环境，继承学生环境
    test_env <- new.env(parent = student_env)

    # 重新启动输出捕获
    get_output <- capture_output()

    # 运行测试代码
    test_result <- tryCatch({
      # 每行代码执行前检查超时
      expr <- parse(text = test_code)
      for (i in seq_along(expr)) {
        check_time()
        eval(expr[i], envir = test_env)
      }

      # 检查测试环境中是否有测试结果
      if (exists("test_result", envir = test_env)) {
        get("test_result", envir = test_env)
      } else {
        # 如果没有测试结果，创建默认结果
        list(
          status = "error",
          score = 0,
          max_score = 100,
          message = "测试代码未返回结果，请确保测试代码创建了test_result变量"
        )
      }
    }, error = function(e) {
      list(
        status = "error",
        score = 0,
        max_score = 100,
        message = paste("测试执行错误:", e$message)
      )
    })

    # 获取测试代码执行的输出
    test_output <- get_output()
    all_output <- c(all_output, test_output)
  } else {
    # 如果学生代码执行失败，使用学生代码的结果作为测试结果
    test_result <- list(
      status = "error",
      score = 0,
      max_score = 100,
      message = student_result$message
    )
  }

  # 记录结束时间
  end_time <- Sys.time()
  execution_time <- as.numeric(difftime(end_time, start_time, units = "secs"))

  # 构建最终结果
  final_result <- list(
    status = test_result$status,
    score = test_result$score,
    max_score = test_result$max_score,
    message = test_result$message,
    output = paste(all_output, collapse = "\n"),
    execution_time = execution_time
  )

  # 可选：添加附加信息
  if (!is.null(test_result$details)) {
    final_result$details <- test_result$details
  }

  if (!is.null(test_result$feedback)) {
    final_result$feedback <- test_result$feedback
  }

  # 转换为JSON字符串
  json_result <- jsonlite::toJSON(final_result, auto_unbox = TRUE)

  return(json_result)
}

# 测试辅助函数 - 可以在测试代码中使用
test_utils <- list(
  # 比较数值或向量，允许小的差异
  compare_numeric = function(actual, expected, tolerance = 1e-6) {
    if (length(actual) != length(expected)) {
      return(list(
        passed = FALSE,
        message = sprintf("长度不匹配: 实际值长度=%d, 期望值长度=%d", length(actual), length(expected))
      ))
    }

    diff <- abs(actual - expected)
    max_diff <- max(diff)

    if (max_diff <= tolerance) {
      return(list(
        passed = TRUE,
        message = "数值匹配"
      ))
    } else {
      return(list(
        passed = FALSE,
        message = sprintf("数值不匹配，最大差异为 %g", max_diff)
      ))
    }
  },

  # 比较数据框
  compare_dataframe = function(actual, expected, check_row_order = TRUE, check_col_order = TRUE) {
    if (!is.data.frame(actual)) {
      return(list(
        passed = FALSE,
        message = "实际值不是数据框"
      ))
    }

    if (!is.data.frame(expected)) {
      return(list(
        passed = FALSE,
        message = "期望值不是数据框"
      ))
    }

    # 检查维度
    if (nrow(actual) != nrow(expected)) {
      return(list(
        passed = FALSE,
        message = sprintf("行数不匹配: 实际值=%d行, 期望值=%d行", nrow(actual), nrow(expected))
      ))
    }

    if (ncol(actual) != ncol(expected)) {
      return(list(
        passed = FALSE,
        message = sprintf("列数不匹配: 实际值=%d列, 期望值=%d列", ncol(actual), ncol(expected))
      ))
    }

    # 检查列名
    actual_names <- colnames(actual)
    expected_names <- colnames(expected)

    if (check_col_order) {
      # 检查列名及顺序
      if (!identical(actual_names, expected_names)) {
        return(list(
          passed = FALSE,
          message = sprintf("列名不匹配: 实际值=%s, 期望值=%s",
                            paste(actual_names, collapse=", "),
                            paste(expected_names, collapse=", "))
        ))
      }
    } else {
      # 仅检查列名，不考虑顺序
      if (!setequal(actual_names, expected_names)) {
        return(list(
          passed = FALSE,
          message = sprintf("列名不匹配: 实际值=%s, 期望值=%s",
                            paste(actual_names, collapse=", "),
                            paste(expected_names, collapse=", "))
        ))
      }

      # 重新排序数据框列以便比较
      actual <- actual[, expected_names]
    }

    # 如果不检查行顺序，则按某个关键列排序
    if (!check_row_order && nrow(actual) > 0) {
      # 尝试按第一列排序
      tryCatch({
        actual <- actual[order(actual[[1]]), ]
        expected <- expected[order(expected[[1]]), ]
      }, error = function(e) {
        # 排序失败，保持原样
      })
    }

    # 逐列比较
    for (col_name in expected_names) {
      actual_col <- actual[[col_name]]
      expected_col <- expected[[col_name]]

      # 检查类型
      if (class(actual_col) != class(expected_col)) {
        return(list(
          passed = FALSE,
          message = sprintf("列 '%s' 类型不匹配: 实际值=%s, 期望值=%s",
                            col_name, class(actual_col), class(expected_col))
        ))
      }

      # 根据类型进行比较
      if (is.numeric(expected_col)) {
        # 数值比较，允许小的差异
        diff <- abs(actual_col - expected_col)
        if (any(diff > 1e-6, na.rm = TRUE) || !identical(is.na(actual_col), is.na(expected_col))) {
          return(list(
            passed = FALSE,
            message = sprintf("列 '%s' 的值不匹配", col_name)
          ))
        }
      } else {
        # 其他类型直接比较
        if (!identical(actual_col, expected_col)) {
          return(list(
            passed = FALSE,
            message = sprintf("列 '%s' 的值不匹配", col_name)
          ))
        }
      }
    }

    # 所有检查通过
    return(list(
      passed = TRUE,
      message = "数据框匹配"
    ))
  },

  # 检查函数是否存在且返回正确结果
  test_function = function(fn_name, test_cases) {
    if (!exists(fn_name, envir = parent.frame(), inherits = TRUE)) {
      return(list(
        passed = FALSE,
        message = sprintf("函数 '%s' 不存在", fn_name)
      ))
    }

    fn <- get(fn_name, envir = parent.frame(), inherits = TRUE)
    if (!is.function(fn)) {
      return(list(
        passed = FALSE,
        message = sprintf("'%s' 不是一个函数", fn_name)
      ))
    }

    # 测试每个测试用例
    results <- lapply(test_cases, function(test_case) {
      args <- test_case$args
      expected <- test_case$expected

      tryCatch({
        # 调用函数
        result <- do.call(fn, args)

        # 比较结果
        if (identical(result, expected)) {
          return(list(
            passed = TRUE,
            message = sprintf("测试通过：%s", test_case$name)
          ))
        } else {
          return(list(
            passed = FALSE,
            message = sprintf("测试失败：%s - 预期 %s，得到 %s",
                              test_case$name,
                              toString(expected),
                              toString(result))
          ))
        }
      }, error = function(e) {
        return(list(
          passed = FALSE,
          message = sprintf("测试出错：%s - %s", test_case$name, e$message)
        ))
      })
    })

    # 计算通过的测试用例数
    passed <- sum(sapply(results, function(r) r$passed))
    total <- length(test_cases)

    # 返回汇总结果
    return(list(
      passed = passed == total,
      message = sprintf("通过 %d/%d 个测试用例", passed, total),
      details = results
    ))
  }
)

# 如果从命令行运行，则解析参数
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) >= 3) {
    student_code_file <- args[1]
    test_code_file <- args[2]
    timeout <- as.numeric(args[3])

    # 读取文件内容
    tryCatch({
      student_code <- readLines(student_code_file, warn = FALSE)
      student_code <- paste(student_code, collapse = "\n")

      test_code <- readLines(test_code_file, warn = FALSE)
      test_code <- paste(test_code, collapse = "\n")

      # 在测试代码中添加test_utils对象
      test_code <- paste("test_utils <- ",
                         deparse(test_utils, control = "keepNA"),
                         "\n", test_code, sep = "")

      # 运行测试并输出结果
      result <- run_test(student_code, test_code, timeout)
      cat(result)
    }, error = function(e) {
      error_result <- list(
        status = "error",
        score = 0,
        max_score = 100,
        message = paste("文件读取或测试执行错误:", e$message),
        output = ""
      )
      cat(jsonlite::toJSON(error_result, auto_unbox = TRUE))
    })
  } else {
    # 参数不足
    error_result <- list(
      status = "error",
      score = 0,
      max_score = 100,
      message = "参数不足: 需要学生代码文件, 测试代码文件和超时时间",
      output = ""
    )
    cat(jsonlite::toJSON(error_result, auto_unbox = TRUE))
  }
}