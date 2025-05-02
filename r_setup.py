import os
import sys
# 第九次修改
import tempfile
import json

# 设置R_HOME环境变量
os.environ['R_HOME'] = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'

# 将这个路径添加到sys.path
r_path = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\site-packages'
if r_path not in sys.path:
    sys.path.append(r_path)

# 备注1：可以在这里添加任何其他必要的R设置

# 备注2：在所有需要使用R的Python文件的顶部导入这个模块，指令为：
# import r_setup
# （选）import rpy2.robjects as ro

# 备注3：为确认R_HOME已正确设置，可以在相关代码的开头都添加诊断打印语句
# import os
# print(f"当前R_HOME环境变量: {os.environ.get('R_HOME', '未设置')}")
# import rpy2.robjects as ro
# print(ro.r('R.version.string')[0])

# 备注4：备用方法-在每个导入rpy2的python脚本前强制R_HOME路径为R 4.4.3
# import os
# os.environ['R_HOME'] = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'
# import rpy2.robjects as ro

# 第九次修改
# 运行R测试代码的函数
def run_r_test(student_code, test_code, timeout=10):
    """
    使用rpy2运行R测试代码评估学生代码

    Args:
        student_code (str): 学生提交的R代码
        test_code (str): 测试用例代码
        timeout (int): 执行超时时间(秒)

    Returns:
        dict: 包含测试结果的字典
    """
    try:
        # 导入rpy2模块
        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr
        from rpy2.robjects.vectors import StrVector

        # 导入需要的R包
        base = importr('base')

        # 设置超时
        ro.r(f'options(timeout={timeout})')

        # 创建临时环境
        ro.r('student_env <- new.env()')

        # 捕获输出
        output = []

        def capture_output(x):
            output.append(x)
            return x

        ro.r('sink(textConnection(function(x) { assign("output", c(output, x), envir=.GlobalEnv) }))')

        # 尝试执行学生代码
        try:
            if student_code:
                processed_code = student_code.replace('"""', '\\"')
            else:
                processed_code = ""

            ro.r(f'eval(parse(text="{processed_code}"), envir=student_env)')
            status = "success"
            message = "代码执行成功"
        except Exception as e:
            status = "error"
            message = f"代码执行错误: {str(e)}"
            return {
                'status': status,
                'score': 0,
                'max_score': 100,
                'message': message,
                'output': '\n'.join(output)
            }

        # 重置输出捕获
        ro.r('sink()')

        # 运行测试代码
        test_env_name = 'test_env'
        ro.r(f'{test_env_name} <- new.env(parent=student_env)')

        try:
            if test_code:
                processed_test_code = test_code.replace('"""', '\\"')
            else:
                processed_test_code = ""

            ro.r(f'eval(parse(text="{processed_test_code}"), envir={test_env_name})')

            # 获取测试结果
            if ro.r(f'exists("test_result", envir={test_env_name})')[0]:
                # 获取测试结果
                result = ro.r(f'test_result <- get("test_result", envir={test_env_name})')

                # 将R列表转换为Python字典
                result_dict = {}
                for key in ro.r(f'names(test_result)'):
                    result_dict[key] = ro.r(f'test_result${key}')[0]

                # 添加输出
                result_dict['output'] = '\n'.join(output)
                return result_dict
            else:
                return {
                    'status': 'success',
                    'score': 0,
                    'max_score': 100,
                    'message': '测试代码未返回结果',
                    'output': '\n'.join(output)
                }
        except Exception as e:
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'测试执行错误: {str(e)}',
                'output': '\n'.join(output)
            }
    except Exception as e:
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': f'R环境执行异常: {str(e)}',
            'output': ''
        }