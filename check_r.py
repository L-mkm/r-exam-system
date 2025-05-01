import os
import sys
import platform


def check_r_environment():
    """检查R环境与rpy2集成"""
    print("检查R环境与rpy2集成...")

    # 设置R_HOME环境变量
    os.environ['R_HOME'] = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'

    # 检查rpy2
    try:
        import rpy2
        print(f"rpy2版本: {rpy2.__version__}")

        import rpy2.robjects as ro
        r_version = ro.r('R.version.string')[0]
        print(f"R版本: {r_version}")

        # 检查必要的R包
        required_packages = ['base', 'stats', 'graphics', 'utils', 'jsonlite']
        missing_packages = []

        for package in required_packages:
            if not ro.r(f'suppressWarnings(require({package}))')[0]:
                missing_packages.append(package)

        if missing_packages:
            print(f"缺少必要的R包: {', '.join(missing_packages)}")
            print("请在R环境中安装这些包:")
            print(f"install.packages(c({', '.join([f'\"{pkg}\"' for pkg in missing_packages])}))")
            return False

        print("所有必要的R包已安装")
        return True
    except ImportError as e:
        print(f"导入rpy2失败: {str(e)}")
        print("请确保已安装rpy2: pip install rpy2")
        return False
    except Exception as e:
        print(f"检查R环境时出现异常: {str(e)}")
        return False


def test_r_code_execution():
    """测试R代码执行"""
    print("测试R代码执行...")

    try:
        import r_setup
        from r_setup import run_r_test

        # 测试执行简单的R代码
        student_code = "x <- 5\ny <- 10\nresult <- x + y"
        test_code = """
        test_result <- list(
          status = "success",
          score = if(exists("result", envir=student_env) && student_env$result == 15) 100 else 0,
          max_score = 100,
          message = if(exists("result", envir=student_env) && student_env$result == 15) "正确" else "错误"
        )
        """

        result = run_r_test(student_code, test_code)
        print(f"测试结果: {result}")

        if result.get('status') == 'success' and result.get('score') == 100:
            print("R代码执行测试通过")
            return True
        else:
            print(f"R代码执行测试失败: {result.get('message')}")
            return False
    except Exception as e:
        print(f"测试R代码执行时出现异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("===== R语言考试系统环境检查 =====")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print("------------------------------")

    r_env_ok = check_r_environment()
    if not r_env_ok:
        print("R环境检查失败，请先解决上述问题。")
        return 1

    execution_ok = test_r_code_execution()

    print("------------------------------")
    print("检查结果汇总:")
    print(f"R环境与rpy2集成: {'✓' if r_env_ok else '✗'}")
    print(f"R代码执行: {'✓' if execution_ok else '✗'}")

    if r_env_ok and execution_ok:
        print("\n✅ 所有检查通过，R语言考试环境已准备就绪！")
        return 0
    else:
        print("\n❌ 环境检查未通过，请解决上述问题后再次运行检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())