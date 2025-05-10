# test_grading.py
import logging
from utils.sandbox import RCodeSandbox

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('grading_test')

# 创建沙箱实例
sandbox = RCodeSandbox(timeout=10)

# 简单的学生代码
student_code = """
# 计算平均值函数
calculate_mean <- function(numbers) {
    if(length(numbers) == 0) {
        return(NA)
    }
    return(sum(numbers) / length(numbers))
}
"""

# 测试代码
test_code = """
# 测试用例
test_cases <- list(
    list(input = numeric(0), expected = NA),
    list(input = 5, expected = 5),
    list(input = c(1, 2, 3, 4, 5), expected = 3)
)

# 运行测试
results <- lapply(test_cases, function(test_case) {
    input <- test_case$input
    expected <- test_case$expected

    # 运行学生函数
    actual <- tryCatch({
        calculate_mean(input)
    }, error = function(e) {
        return(paste("错误:", e$message))
    })

    # 检查结果
    if (is.character(actual)) {
        return(list(passed = FALSE, message = actual))
    } else if (is.na(expected) && is.na(actual)) {
        return(list(passed = TRUE, message = "通过"))
    } else if (is.na(expected) || is.na(actual)) {
        return(list(passed = FALSE, message = "结果不匹配"))
    } else if (abs(actual - expected) < 1e-6) {
        return(list(passed = TRUE, message = "通过"))
    } else {
        return(list(passed = FALSE, message = paste("预期", expected, "但得到", actual)))
    }
})

# 计算得分
total_cases <- length(results)
passed_cases <- sum(sapply(results, function(r) r$passed))
score <- round(100 * passed_cases / total_cases)

# 创建测试结果
test_result <- list(
    status = if(passed_cases == total_cases) "success" else "error",
    score = score,
    max_score = 100,
    message = paste("通过测试用例:", passed_cases, "/", total_cases)
)
"""

# 执行测试
logger.info("执行R自动评分测试...")
result = sandbox.execute(student_code, test_code)

# 输出结果
logger.info(f"评分结果:")
logger.info(f"状态: {result['status']}")
logger.info(f"得分: {result['score']}/{result['max_score']}")
logger.info(f"消息: {result['message']}")
logger.info(f"输出: {result.get('output', '')[:200]}...")  # 只显示前200个字符