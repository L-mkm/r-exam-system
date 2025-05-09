from app import create_app, db
from models.code_template import CodeTemplate


def init_templates_function(app):
    """初始化测试代码模板 - 接受已有的app实例"""
    with app.app_context():
        # 检查是否已有模板
        if CodeTemplate.query.count() > 0:
            print("模板数据已存在，跳过初始化")
            return

        # 函数正确性测试
        function_test = CodeTemplate(
            name="函数正确性测试",
            description="测试学生实现的函数输出是否符合预期",
            template_type="function_test",
            template_code="""# 函数正确性测试 - 测试学生实现的函数输出是否符合预期
# 变量: function_name, test_cases

test_cases <- list(
 list(input = c(1, 2, 3), expected = 6),
 list(input = c(10, 20), expected = 30),
 list(input = c(-5, 5), expected = 0),
 list(input = c(0), expected = 0)
)

function_name <- "calculate_sum"

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
     student_result <- do.call(student_env[[function_name]], list(case$input))

     # 检查结果
     if (all(abs(student_result - case$expected) < 1e-6)) {
       correct_count <- correct_count + 1
       TRUE
     } else {
       failed_tests <- c(failed_tests, 
                      sprintf("测试 %d: 输入 %s, 期望 %s, 得到 %s", 
                             i, 
                             paste(case$input, collapse=","), 
                             paste(case$expected, collapse=","), 
                             paste(student_result, collapse=",")))
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
   test_result$message <- paste0("通过 ", correct_count, " 个测试，共 ", length(test_cases), " 个。\n失败的测试：\n", paste(failed_tests, collapse="\n"))
 } else {
   test_result$message <- paste0("所有测试通过！共 ", length(test_cases), " 个测试。")
 }
}"""
        )

        # 数据处理测试
        data_processing = CodeTemplate(
            name="数据处理测试",
            description="测试学生处理数据的正确性",
            template_type="data_processing",
            template_code="""# 数据处理测试 - 测试学生处理数据的正确性
# 变量: data_variable, expected_result_variable

data_variable <- "processed_data"
expected_result_variable <- "expected_result"

# 在测试环境中定义预期结果
expected_result <- data.frame(
 x = c(1, 2, 3, 4, 5),
 y = c(2, 4, 6, 8, 10)
)

test_result <- list(
 status = "success",
 score = 0,
 max_score = 100,
 message = ""
)

# 检查变量是否存在
if (!exists(data_variable, envir=student_env)) {
 test_result$status <- "error"
 test_result$message <- paste0("未找到变量 '", data_variable, "'")
} else {
 # 获取学生处理的数据
 student_data <- student_env[[data_variable]]

 # 检查结构
 structure_correct <- TRUE
 reasons <- character(0)

 # 检查是否为数据框
 if (!is.data.frame(student_data)) {
   structure_correct <- FALSE
   reasons <- c(reasons, "结果不是数据框")
 } else {
   # 检查列名
   expected_cols <- colnames(expected_result)
   student_cols <- colnames(student_data)
   missing_cols <- setdiff(expected_cols, student_cols)

   if (length(missing_cols) > 0) {
     structure_correct <- FALSE
     reasons <- c(reasons, paste0("缺少列: ", paste(missing_cols, collapse=", ")))
   }

   # 检查行数
   if (nrow(student_data) != nrow(expected_result)) {
     structure_correct <- FALSE
     reasons <- c(reasons, paste0("行数不匹配. 期望: ", nrow(expected_result), ", 得到: ", nrow(student_data)))
   }
 }

 # 结构检查分数 (40%)
 structure_score <- if(structure_correct) 40 else 0

 # 内容检查 (60%)
 content_score <- 0
 if (structure_correct) {
   # 比较共有列的内容
   common_cols <- intersect(colnames(student_data), colnames(expected_result))
   total_cells <- nrow(expected_result) * length(common_cols)
   correct_cells <- 0

   for (col in common_cols) {
     for (i in 1:nrow(expected_result)) {
       if (i <= nrow(student_data) && identical(student_data[i, col], expected_result[i, col])) {
         correct_cells <- correct_cells + 1
       }
     }
   }

   content_score <- (correct_cells / total_cells) * 60
 }

 # 计算总分
 test_result$score <- structure_score + content_score

 # 设置反馈信息
 if (structure_correct && content_score == 60) {
   test_result$message <- "数据处理结果完全正确！"
 } else if (structure_correct) {
   test_result$message <- paste0("数据结构正确，但有部分数据不匹配。正确率: ", round(content_score/60*100), "%")
 } else {
   test_result$message <- paste0("数据结构错误: ", paste(reasons, collapse="; "))
 }
}"""
        )

        # 统计分析测试
        statistics_test = CodeTemplate(
            name="统计分析测试",
            description="测试统计计算是否正确",
            template_type="statistics",
            template_code="""# 统计分析测试 - 测试统计计算是否正确
# 变量: result_variables, expected_values, tolerance

result_variables <- c("mean_value", "median_value", "sd_value")
expected_values <- c(15.5, 15.5, 8.803408)
tolerance <- 1e-4

test_result <- list(
 status = "success",
 score = 0,
 max_score = 100,
 message = ""
)

# 检查每个统计量
missing_vars <- character(0)
correct_vars <- character(0)
incorrect_vars <- list()

for (i in 1:length(result_variables)) {
 var_name <- result_variables[i]
 expected <- expected_values[i]

 if (!exists(var_name, envir=student_env)) {
   missing_vars <- c(missing_vars, var_name)
 } else {
   student_value <- student_env[[var_name]]
   if (abs(student_value - expected) <= tolerance) {
     correct_vars <- c(correct_vars, var_name)
   } else {
     incorrect_vars[[var_name]] <- list(
       expected = expected,
       actual = student_value
     )
   }
 }
}

# 计算分数 (每个变量等分)
points_per_var <- 100 / length(result_variables)
test_result$score <- length(correct_vars) * points_per_var

# 生成反馈信息
if (length(missing_vars) > 0) {
 test_result$message <- paste0("未找到以下变量: ", paste(missing_vars, collapse=", "), "\n")
}

if (length(incorrect_vars) > 0) {
 test_result$message <- paste0(test_result$message, "以下变量值不正确:\n")
 for (var_name in names(incorrect_vars)) {
   test_result$message <- paste0(test_result$message, var_name, ": 期望 ", 
                            incorrect_vars[[var_name]]$expected, ", 得到 ", 
                            incorrect_vars[[var_name]]$actual, "\n")
 }
}

if (length(correct_vars) == length(result_variables)) {
 test_result$message <- "所有统计分析结果正确！"
} else if (length(correct_vars) > 0) {
 test_result$message <- paste0(test_result$message, "正确的变量: ", paste(correct_vars, collapse=", "))
}"""
        )

        # 图形参数测试
        plotting_test = CodeTemplate(
            name="图形参数测试",
            description="测试绘图函数调用的参数是否正确",
            template_type="plotting",
            template_code="""# 图形参数测试 - 测试绘图函数调用的参数是否正确
# 变量: plot_function, required_params

plot_function <- "create_plot"
required_params <- list(
 main = "分布图",
 xlab = "数值",
 ylab = "频率",
 col = "blue",
 breaks = 10
)

test_result <- list(
 status = "success",
 score = 0,
 max_score = 100,
 message = ""
)

# 替换绘图函数用于捕获参数
if (exists(plot_function, envir=student_env) && is.function(student_env[[plot_function]])) {
 # 保存原始函数
 original_plot <- student_env[[plot_function]]

 # 捕获的参数
 captured_params <- list()

 # 创建监听函数
 monitor_hist <- function(...) {
   args <- list(...)
   for (name in names(args)) {
     captured_params[[name]] <<- args[[name]]
   }
   # 调用原始函数
   return(hist(...))
 }

 # 替换hist函数
 assign("hist", monitor_hist, envir=student_env)

 # 执行学生函数
 tryCatch({
   student_env[[plot_function]]()

   # 恢复原始函数
   assign("hist", graphics::hist, envir=student_env)

   # 检查参数
   correct_params <- character(0)
   incorrect_params <- list()
   missing_params <- character(0)

   for (param_name in names(required_params)) {
     if (param_name %in% names(captured_params)) {
       if (identical(captured_params[[param_name]], required_params[[param_name]])) {
         correct_params <- c(correct_params, param_name)
       } else {
         incorrect_params[[param_name]] <- list(
           expected = required_params[[param_name]],
           actual = captured_params[[param_name]]
         )
       }
     } else {
       missing_params <- c(missing_params, param_name)
     }
   }

   # 计算分数
   points_per_param <- 100 / length(names(required_params))
   test_result$score <- length(correct_params) * points_per_param

   # 生成反馈
   feedback <- character(0)

   if (length(missing_params) > 0) {
     feedback <- c(feedback, paste0("缺少参数: ", paste(missing_params, collapse=", ")))
   }

   if (length(incorrect_params) > 0) {
     for (param in names(incorrect_params)) {
       feedback <- c(feedback, paste0("参数 ", param, " 值不正确. 期望: ", 
                              toString(incorrect_params[[param]]$expected), 
                              ", 得到: ", toString(incorrect_params[[param]]$actual)))
     }
   }

   if (length(feedback) > 0) {
     test_result$message <- paste(feedback, collapse="\n")
   } else {
     test_result$message <- "所有图形参数设置正确！"
   }

 }, error = function(e) {
   # 恢复原始函数
   assign("hist", graphics::hist, envir=student_env)

   test_result$status <- "error"
   test_result$score <- 0
   test_result$message <- paste0("执行绘图函数时出错: ", e$message)
 })

} else {
 test_result$status <- "error"
 test_result$message <- paste0("未找到函数 '", plot_function, "'")
}"""
        )

        db.session.add(function_test)
        db.session.add(data_processing)
        db.session.add(statistics_test)
        db.session.add(plotting_test)
        db.session.commit()
        print("测试代码模板初始化完成")


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    init_templates_function(app)