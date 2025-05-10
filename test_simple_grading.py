# test_simple_grading.py
import logging
from utils.sandbox import RCodeSandbox

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('simple_grading_test')

# 创建沙箱实例
sandbox = RCodeSandbox(timeout=10)

# 简单的学生代码
student_code = """
# 计算平方函数
square <- function(x) {
    return(x * x)
}
"""

# 非常简单的测试代码
test_code = """
# 简单测试
result <- square(5)
expected <- 25

# 创建测试结果
test_result <- list(
    status = if(result == expected) "success" else "error",
    score = if(result == expected) 100 else 0,
    max_score = 100,
    message = if(result == expected) "测试通过" else "测试失败"
)
"""

# 执行测试
logger.info("执行简单R评分测试...")
result = sandbox.execute(student_code, test_code)

# 输出结果
logger.info(f"评分结果:")
logger.info(f"状态: {result['status']}")
logger.info(f"得分: {result['score']}/{result['max_score']}")
logger.info(f"消息: {result['message']}")
logger.info(f"输出: {result.get('output', '')[:200]}...")  # 只显示前200个字符