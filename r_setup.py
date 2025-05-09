import os
import sys
# 第九次修改
import tempfile
import json

# 设置R_HOME环境变量
os.environ['R_HOME'] = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'
# 添加区域设置，帮助处理中文
os.environ['LC_ALL'] = 'Chinese'  # 适用于Windows中文环境

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

        # 设置超时和编码选项
        ro.r(f'options(timeout={timeout}, encoding="UTF-8")')
        ro.r('Sys.setlocale("LC_ALL", "Chinese")')  # 适用于Windows中文环境

        # 创建临时环境
        ro.r('student_env <- new.env()')
        ro.r('output <- character(0)')

        # 安全执行代码的函数
        ro.r('''
        safe_eval <- function(code, env) {
          tryCatch({
            eval(parse(text=code), envir=env)
            return(list(status="success", message="执行成功"))
          }, error=function(e) {
            return(list(status="error", message=paste("错误:", e$message)))
          })
        }
        ''')

        # 安全处理输出捕获
        ro.r('''
        setup_output_capture <- function() {
          output_buffer <- character(0)
          output_conn <- textConnection("output_buffer", "w", local=TRUE)
          sink(output_conn, type="output")
          sink(output_conn, type="message")

          return(function() {
            sink(type="output")
            sink(type="message")
            close(output_conn)
            return(output_buffer)
          })
        }
        ''')

        # 设置输出捕获
        ro.r('get_output <- setup_output_capture()')

        # 尝试执行学生代码
        try:
            if student_code:
                # 预处理代码，确保编码正确
                processed_code = student_code.replace('\\', '\\\\').replace('"', '\\"')
            else:
                processed_code = ""

            # 安全执行学生代码
            result = ro.r(f'safe_eval("{processed_code}", student_env)')
            status = result[0]
            message = result[1]

            if status == "error":
                # 获取捕获的输出
                output_text = ro.r('get_output()')
                output_list = [str(item) for item in output_text]

                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': message,
                    'output': '\n'.join(output_list)
                }
        except Exception as e:
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'代码执行错误: {str(e)}',
                'output': ''
            }

        # 运行测试代码
        test_env_name = 'test_env'
        ro.r(f'{test_env_name} <- new.env(parent=student_env)')

        try:
            if test_code:
                # 预处理测试代码
                processed_test_code = test_code.replace('\\', '\\\\').replace('"', '\\"')
            else:
                processed_test_code = ""

            # 安全执行测试代码
            test_result = ro.r(f'safe_eval("{processed_test_code}", {test_env_name})')

            # 获取测试结果
            if ro.r(f'exists("test_result", envir={test_env_name})')[0]:
                # 获取测试结果
                result = ro.r(f'test_result <- get("test_result", envir={test_env_name})')

                # 将R列表转换为Python字典
                result_dict = {}
                for key in ro.r(f'names(test_result)'):
                    result_dict[key] = ro.r(f'test_result${key}')[0]

                # 获取捕获的输出
                output_text = ro.r('get_output()')
                output_list = [str(item) for item in output_text]

                # 添加输出
                result_dict['output'] = '\n'.join(output_list)
                return result_dict
            else:
                # 获取捕获的输出
                output_text = ro.r('get_output()')
                output_list = [str(item) for item in output_text]

                return {
                    'status': 'success',
                    'score': 0,
                    'max_score': 100,
                    'message': '测试代码未返回结果',
                    'output': '\n'.join(output_list)
                }
        except Exception as e:
            # 获取捕获的输出
            output_text = ro.r('get_output()')
            output_list = [str(item) for item in output_text]

            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'测试执行错误: {str(e)}',
                'output': '\n'.join(output_list)
            }
    except Exception as e:
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': f'R环境执行异常: {str(e)}',
            'output': ''
        }