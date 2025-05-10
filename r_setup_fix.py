import os
import sys
import tempfile
import json
import traceback
import re

# 设置R_HOME环境变量 - 使用正斜杠避免路径问题
os.environ['R_HOME'] = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'.replace('\\', '/')

# 添加区域设置，帮助处理中文
os.environ['LC_ALL'] = 'Chinese'  # 适用于Windows中文环境

# 将这个路径添加到sys.path
r_path = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\site-packages'.replace('\\', '/')
if r_path not in sys.path:
    sys.path.append(r_path)

# 修复编码问题
try:
    import rpy2.robjects as ro
    from rpy2.rinterface_lib import callbacks
    import rpy2.rinterface_lib.conversion as conversion

    # 尝试使用不同的编码设置
    conversion._CCHAR_ENCODING = "latin1"  # 尝试latin1编码而不是UTF-8

    # 增加安全的控制台输出处理
    original_console_write = callbacks.consolewrite_print


    def safe_console_write(buf):
        try:
            s = buf.decode('latin1', errors='replace')
            s = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\s]', '', s)
            print(f"R[输出]: {s}")
        except Exception as e:
            print(f"R输出处理失败: {str(e)}")


    callbacks.consolewrite_print = safe_console_write

    # 设置R编码和区域
    ro.r('Sys.setlocale("LC_ALL", "Chinese")')
    ro.r('options(encoding="native.enc")')
    print(f"当前R区域设置: {ro.r('Sys.getlocale()')[0]}")

except Exception as e:
    print(f"设置编码处理时出错: {str(e)}")
    traceback.print_exc()


def safe_convert_r_output(items):
    """安全地将R输出转换为Python字符串列表"""
    result = []
    for item in items:
        try:
            # 尝试使用latin1编码
            if hasattr(item, 'encode'):
                s = str(item.encode('latin1', errors='replace').decode('latin1', errors='replace'))
            else:
                s = str(item)
            result.append(s)
        except Exception as e:
            result.append(f"[转换错误: {str(e)}]")
    return result

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
    print("======= 开始执行R测试 =======")
    print(f"学生代码长度: {len(student_code)} 字符")
    print(f"测试代码长度: {len(test_code)} 字符")

    try:
        # 导入rpy2模块
        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr
        from rpy2.robjects.vectors import StrVector

        print("成功导入rpy2模块")
        print(f"R版本: {ro.r('R.version.string')[0]}")

        # 导入需要的R包
        base = importr('base')
        print("成功导入base包")

        print("设置R编码选项...")
        try:
            ro.r('options(encoding="native.enc")')  # 使用本地编码而不是UTF-8
            ro.r('Sys.setlocale("LC_ALL", "Chinese")')
            print(f"当前R区域设置: {ro.r('Sys.getlocale()')[0]}")
        except Exception as e:
            print(f"设置R编码选项时出错: {str(e)}")

        # 设置超时和编码选项
        ro.r(f'options(timeout={timeout}, encoding="native.enc")')
        ro.r('Sys.setlocale("LC_ALL", "Chinese")')  # 适用于Windows中文环境
        print("设置R选项完成")

        # 创建临时环境
        ro.r('student_env <- new.env()')
        ro.r('output <- character(0)')
        print("创建临时环境完成")

        # 安全执行代码的函数
        ro.r('''
        safe_eval <- function(code, env) {
          tryCatch({
            eval(parse(text=code), envir=env)
            return(list(status="success", message="执行成功"))
          }, error=function(e) {
            return(list(status="error", message=paste("错误:", e$message)))
          }, warning=function(w) {
            # 处理警告但继续执行
            warning(w$message)
            return(list(status="warning", message=paste("警告:", w$message)))
          })
        }
        ''')
        print("定义safe_eval函数完成")

        # 安全处理输出捕获
        ro.r('''
        setup_output_capture <- function() {
          output_buffer <- character(0)
          output_conn <- textConnection("output_buffer", "w", local=TRUE)
          sink(output_conn, type="output")
          sink(output_conn, type="message")

          return(function() {
            sink(type="message", NULL)  # 重置message sink
            sink(type="output", NULL)   # 重置output sink
            close(output_conn)
            return(output_buffer)
          })
        }
        ''')
        print("定义输出捕获函数完成")

        # 设置输出捕获
        ro.r('get_output <- setup_output_capture()')
        print("设置输出捕获完成")

        # 尝试执行学生代码
        print("开始执行学生代码...")
        try:
            if student_code:
                # 预处理代码，确保编码正确
                processed_code = student_code.replace('\\', '\\\\').replace('"', '\\"')
                print(f"处理后学生代码的前100个字符: {processed_code[:min(100, len(processed_code))]}")
            else:
                processed_code = ""
                print("学生代码为空")

            # 安全执行学生代码
            result = ro.r(f'safe_eval("{processed_code}", student_env)')
            status = result[0]
            message = result[1]
            print(f"学生代码执行结果: {status} - {message}")

            if status == "error":
                # 获取捕获的输出
                output_text = ro.r('get_output()')
                # output_list = [str(item) for item in output_text]
                output_list = safe_convert_r_output(output_text)
                output_str = '\n'.join(output_list)
                print(f"学生代码执行输出: {output_str[:200]}...")

                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': message,
                    'output': output_str
                }
        except Exception as e:
            print(f"执行学生代码时异常: {str(e)}")
            traceback.print_exc()
            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'代码执行错误: {str(e)}',
                'output': traceback.format_exc()
            }

        # 运行测试代码
        print("开始执行测试代码...")
        test_env_name = 'test_env'
        ro.r(f'{test_env_name} <- new.env(parent=student_env)')

        # 添加环境检查
        print("学生环境中的变量:")
        student_vars = ro.r(f'ls(student_env)')
        print(", ".join([str(var) for var in student_vars]))

        try:
            if test_code:
                # 预处理测试代码 - 更严格的处理引号和转义符
                processed_test_code = test_code.replace('\\', '\\\\').replace('"', '\\"')
                # 在测试代码前后添加调试语句
                enhanced_test_code = f"""
                cat("===== 开始执行测试代码 =====\\n")

                {processed_test_code}

                cat("===== 测试代码执行完毕 =====\\n")
                # 确保test_result存在
                if(!exists("test_result", envir={test_env_name})) {{
                    cat("警告: 测试代码未创建test_result变量，将创建默认结果\\n")
                    test_result <- list(
                        status = "error",
                        score = 0,
                        max_score = 100,
                        message = "测试代码未返回结果 - 未创建test_result变量"
                    )
                    assign("test_result", test_result, envir={test_env_name})
                }}
                cat("测试结果状态:", test_result$status, "\\n")
                """

                print(f"处理后测试代码的前100个字符: {enhanced_test_code[:min(100, len(enhanced_test_code))]}")

                # 执行增强的测试代码
                test_result = ro.r(f'''
                tryCatch({{
                    eval(parse(text=paste('{enhanced_test_code}')), envir={test_env_name})
                    if(exists("test_result", envir={test_env_name})) {{
                        get("test_result", envir={test_env_name})
                    }} else {{
                        list(status="error", score=0, max_score=100, message="测试代码未创建test_result变量")
                    }}
                }}, error=function(e) {{
                    cat("测试代码执行错误:", e$message, "\\n")
                    list(status="error", score=0, max_score=100, message=paste("测试执行错误:", e$message))
                }})
                ''')

                # 验证测试环境中的变量
                print(f"测试环境中的变量:")
                test_vars = ro.r(f'ls({test_env_name})')
                print(", ".join([str(var) for var in test_vars]))

                # 检查test_result是否存在
                test_result_exists = ro.r(f'exists("test_result", envir={test_env_name})')[0]
                print(f"测试结果变量存在: {test_result_exists}")

                if test_result_exists:
                    # 直接从环境中获取测试结果
                    result_dict = {}

                    # 检查test_result的结构
                    result_names = ro.r(f'names(get("test_result", envir={test_env_name}))')
                    print(f"测试结果包含字段: {', '.join([str(name) for name in result_names])}")

                    for key in result_names:
                        key_str = str(key)
                        result_dict[key_str] = ro.r(f'get("test_result", envir={test_env_name})${key_str}')[0]

                    # 获取捕获的输出
                    output_text = ro.r('get_output()')
                    # output_list = [str(item) for item in output_text]
                    output_list = safe_convert_r_output(output_text)
                    output_str = '\n'.join(output_list)

                    # 确保所有必要的字段都存在
                    required_fields = ['status', 'score', 'max_score', 'message']
                    for field in required_fields:
                        if field not in result_dict:
                            result_dict[field] = 0 if field in ['score', 'max_score'] else (
                                'error' if field == 'status' else '字段缺失')

                    # 添加输出
                    result_dict['output'] = output_str
                    print(f"最终结果: {result_dict}")
                    return result_dict
                else:
                    # 获取捕获的输出
                    output_text = ro.r('get_output()')
                    # output_list = [str(item) for item in output_text]
                    output_list = safe_convert_r_output(output_text)
                    output_str = '\n'.join(output_list)
                    print(f"测试代码输出: {output_str[:200]}...")

                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '测试代码未返回结果 - test_result不存在',
                        'output': output_str
                    }
            else:
                print("测试代码为空")
                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': '测试代码为空',
                    'output': ''
                }
        except Exception as e:
            # 获取捕获的输出
            print(f"执行测试代码时异常: {str(e)}")
            traceback.print_exc()

            try:
                output_text = ro.r('get_output()')
                # output_list = [str(item) for item in output_text]
                output_list = safe_convert_r_output(output_text)
                output_str = '\n'.join(output_list)
            except:
                output_str = "无法获取输出"

            return {
                'status': 'error',
                'score': 0,
                'max_score': 100,
                'message': f'测试执行错误: {str(e)}',
                'output': f"{output_str}\n\n{traceback.format_exc()}"
            }
    except Exception as e:
        print(f"R环境执行总体异常: {str(e)}")
        traceback.print_exc()
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': f'R环境执行异常: {str(e)}',
            'output': traceback.format_exc()
        }