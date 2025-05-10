import os
import sys
import platform


def check_r_environment():
    """检查R环境与rpy2集成"""
    print("检查R环境与rpy2集成...")

    # 设置R_HOME环境变量 - 使用正斜杠避免路径问题
    r_home = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'.replace('\\', '/')
    os.environ['R_HOME'] = r_home
    print(f"设置R_HOME: {r_home}")

    # 检查rpy2
    try:
        import rpy2
        print(f"rpy2版本: {rpy2.__version__}")

        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr, isinstalled

        # 获取R版本信息
        try:
            r_version = ro.r('R.version.string')[0]
            print(f"R版本: {r_version}")
        except Exception as e:
            print(f"获取R版本时出错: {str(e)}")

        # 使用isinstalled函数检查包
        required_packages = ['base', 'stats', 'graphics', 'utils', 'jsonlite']
        missing_packages = []

        for package in required_packages:
            try:
                # 使用isinstalled函数检查
                if not isinstalled(package):
                    missing_packages.append(package)
                    print(f"包 {package} 未安装")
                else:
                    print(f"包 {package} 已安装")
            except Exception as e:
                print(f"检查包 {package} 时出错: {str(e)}")
                missing_packages.append(package)

        if missing_packages:
            print(f"缺少必要的R包: {', '.join(missing_packages)}")
            quoted_packages = [f'"{pkg}"' for pkg in missing_packages]
            print(f"请在R环境中安装这些包:")
            print(f"install.packages(c({', '.join(quoted_packages)}))")
            return False

        print("所有必要的R包已安装")

        # 简单测试R函数执行
        print("测试简单R函数执行...")
        try:
            result = ro.r('1+1')[0]
            print(f"R计算结果 1+1 = {result}")
            return True
        except Exception as e:
            print(f"执行简单R函数时出错: {str(e)}")
            return False

    except ImportError as e:
        print(f"导入rpy2失败: {str(e)}")
        print("请确保已安装rpy2: pip install rpy2")
        return False
    except Exception as e:
        print(f"检查R环境时出现异常: {str(e)}")
        print("详细错误:", repr(e))
        return False


def test_r_code_execution():
    """测试R代码执行"""
    print("测试R代码执行...")

    try:
        import rpy2.robjects as ro

        print("直接测试R代码执行...")

        # 创建测试环境
        ro.r('student_env <- new.env()')

        # 执行简单的学生代码
        student_code = "x <- 5\ny <- 10\nresult <- x + y"
        print(f"执行学生代码: {student_code}")
        ro.r(f'eval(parse(text="{student_code}"), envir=student_env)')

        # 检查结果
        result_exists = ro.r('exists("result", envir=student_env)')[0]
        print(f"result变量存在: {result_exists}")

        if result_exists:
            result_value = ro.r('student_env$result')[0]
            print(f"result值: {result_value}")

            if result_value == 15:
                print("基本R代码执行测试通过")
                return True
            else:
                print(f"结果不正确: 期望15，得到{result_value}")
                return False
        else:
            print("学生环境中未找到result变量")
            return False

    except Exception as e:
        print(f"测试R代码执行时出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
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

    print("------------------------------")
    print("执行基本R代码测试...")
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