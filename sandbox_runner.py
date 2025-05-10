import os
import sys
from utils.sandbox_fix import RCodeSandbox


def run_sandbox_test():
    """测试修复版的沙箱运行情况"""
    print("运行修复版R代码沙箱...")

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

    # 创建沙箱并执行测试
    sandbox = RCodeSandbox(timeout=10)
    result = sandbox.execute(student_code, test_code)

    # 打印结果
    print("\n评分结果:")
    print(f"状态: {result.get('status', '未知')}")
    print(f"得分: {result.get('score', 0)}/{result.get('max_score', 100)}")
    print(f"消息: {result.get('message', '无')}")
    print(f"输出前200字符:\n{result.get('output', '无')[:200]}...")

    return result


if __name__ == "__main__":
    run_sandbox_test()