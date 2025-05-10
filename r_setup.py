# r_setup.py - 改进的R语言集成模块
import os
import sys
import tempfile
import json
import traceback
import logging
import subprocess

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('r_setup')


# 确保使用conda环境中的R4.4.3
def initialize_r_environment():
    """初始化R环境，确保使用conda环境中的R4.4.3"""
    # 设置R_HOME环境变量 - 使用正斜杠避免路径问题
    conda_r_home = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'
    os.environ['R_HOME'] = conda_r_home.replace('\\', '/')

    # 将R bin目录添加到PATH的最前面，确保它被优先使用
    r_bin_path = os.path.join(conda_r_home, 'bin').replace('\\', '/')
    os.environ['PATH'] = r_bin_path + os.pathsep + os.environ.get('PATH', '')

    # 将conda环境的site-packages添加到sys.path
    r_path = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\site-packages'
    if r_path not in sys.path:
        sys.path.append(r_path.replace('\\', '/'))

    # 设置区域以支持中文，但避免编码问题
    os.environ['LC_ALL'] = 'C'  # 使用C区域设置，避免编码问题

    logger.info(f"R环境初始化完成: R_HOME={os.environ.get('R_HOME')}")
    logger.info(f"PATH前缀: {r_bin_path}")
    logger.info(f"R路径已添加: {r_path}")
    logger.info(f"区域设置: LC_ALL={os.environ.get('LC_ALL')}")

    # 验证Rscript命令指向正确的版本
    try:
        # 使用subprocess直接调用Rscript来检查版本
        result = subprocess.run(['Rscript', '-e', 'cat(R.version.string)'],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        r_version = result.stdout.strip()
        logger.info(f"检测到R版本: {r_version}")

        if "R version 4.4.3" in r_version:
            logger.info("✓ 正确使用Conda环境中的R 4.4.3")
        else:
            logger.warning(f"! 警告: 预期R 4.4.3，但检测到 {r_version}")
            logger.warning("可能仍在使用系统R而非Conda环境中的R")
            # 尝试直接使用完整路径的Rscript
            r_script_path = os.path.join(r_bin_path, 'Rscript.exe')
            if os.path.exists(r_script_path):
                result = subprocess.run([r_script_path, '-e', 'cat(R.version.string)'],
                                        capture_output=True, text=True, encoding='utf-8', errors='replace')
                r_version = result.stdout.strip()
                logger.info(f"使用完整路径检测到R版本: {r_version}")
                if "R version 4.4.3" in r_version:
                    logger.info("✓ 使用完整路径可以访问R 4.4.3")
                    # 添加一个全局变量，存储完整的Rscript路径
                    global CONDA_R_SCRIPT_PATH
                    CONDA_R_SCRIPT_PATH = r_script_path
                    return True
            return False
        return True
    except Exception as e:
        logger.error(f"验证R版本失败: {str(e)}")
        return False

    # 验证rpy2是否能正确使用R 4.4.3
    try:
        import rpy2.robjects as ro
        r_version = ro.r('R.version.string')[0]
        logger.info(f"rpy2加载的R版本: {r_version}")

        if "R version 4.4.3" in r_version:
            logger.info("✓ rpy2成功加载R 4.4.3")
            return True
        else:
            logger.warning(f"! 警告: rpy2加载了 {r_version}，而非预期的R 4.4.3")
            return False
    except Exception as e:
        logger.error(f"rpy2初始化失败: {str(e)}")
        return False


# 定义一个全局变量，存储完整的Rscript路径（如果需要）
CONDA_R_SCRIPT_PATH = None

# 初始化R环境
r_initialized = initialize_r_environment()
if not r_initialized:
    logger.error("!!! R环境初始化失败，可能会影响后续操作 !!!")


# 安全转换R输出为Python字符串
def safe_convert_r_output(items):
    """安全地将R输出转换为Python字符串列表"""
    result = []
    for item in items:
        try:
            # 尝试直接转换
            result.append(str(item))
        except UnicodeDecodeError:
            try:
                # 尝试使用GBK或其他常见的中文编码
                if hasattr(item, 'encode'):
                    s = str(item.encode('latin1').decode('gbk', errors='replace'))
                else:
                    s = f"[编码问题的文本: {repr(item)}]"
                result.append(s)
            except Exception:
                # 最后的备选：添加一个占位符
                result.append(f"[无法解码的文本]")
    return result


# 尝试安装和加载jsonlite包
def ensure_jsonlite_package():
    """确保jsonlite包已安装并可用"""
    try:
        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr

        # 尝试导入jsonlite
        try:
            logger.info("尝试加载jsonlite包...")
            jsonlite = importr('jsonlite')
            logger.info("✓ jsonlite包加载成功")
            return True
        except Exception as e:
            logger.warning(f"jsonlite包加载失败: {str(e)}")

            # 尝试安装jsonlite
            try:
                logger.info("尝试安装jsonlite包...")
                utils = importr('utils')
                utils.install_packages("jsonlite", repos="https://cloud.r-project.org")
                jsonlite = importr('jsonlite')
                logger.info("✓ jsonlite包安装并加载成功")
                return True
            except Exception as e:
                logger.error(f"jsonlite包安装失败: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"确保jsonlite包时出错: {str(e)}")
        return False


# 加载jsonlite包
jsonlite_available = ensure_jsonlite_package()
if not jsonlite_available:
    logger.warning("jsonlite包不可用，可能会影响JSON处理功能")


# R高级接口 - 基于文献中的高级接口实现
class RHighLevelInterface:
    """R语言高级接口，提供简单的函数调用和数据转换"""

    def __init__(self):
        """初始化高级接口"""
        try:
            import rpy2.robjects as ro
            self.r = ro.r
            self.robjects = ro
            self.packages = ro.packages
            logger.info("R高级接口初始化成功")
        except Exception as e:
            logger.error(f"R高级接口初始化失败: {str(e)}")
            raise

    def execute(self, r_code):
        """执行R代码并返回结果"""
        try:
            return self.r(r_code)
        except Exception as e:
            logger.error(f"执行R代码失败: {str(e)}")
            raise

    def create_dataframe(self, data_dict):
        """从Python字典创建R数据框"""
        try:
            return self.robjects.vectors.DataFrame(data_dict)
        except Exception as e:
            logger.error(f"创建R数据框失败: {str(e)}")
            raise

    def convert_to_python(self, r_object):
        """将R对象转换为Python对象"""
        try:
            if isinstance(r_object, self.robjects.vectors.DataFrame):
                # 转换数据框为Python字典
                names = list(r_object.names)
                result = {name: list(r_object.rx2(name)) for name in names}
                return result
            elif isinstance(r_object, self.robjects.vectors.Vector):
                # 转换向量为Python列表
                return list(r_object)
            else:
                # 其他类型直接返回
                return r_object
        except Exception as e:
            logger.error(f"转换R对象失败: {str(e)}")
            raise

    def import_r_package(self, package_name):
        """导入R包"""
        try:
            return self.packages.importr(package_name)
        except Exception as e:
            logger.error(f"导入R包 {package_name} 失败: {str(e)}")
            raise


# R低级接口 - 基于文献中的低级接口实现
class RLowLevelInterface:
    """R语言低级接口，提供对R环境和对象的底层访问"""

    def __init__(self):
        """初始化低级接口"""
        try:
            import rpy2.rinterface as rinterface
            self.rinterface = rinterface
            rinterface.initr()
            self.globalenv = rinterface.globalenv
            logger.info("R低级接口初始化成功")
        except Exception as e:
            logger.error(f"R低级接口初始化失败: {str(e)}")
            raise

    def get_object(self, name):
        """从R全局环境获取对象"""
        try:
            return self.globalenv.find(name)
        except Exception as e:
            logger.error(f"获取R对象 {name} 失败: {str(e)}")
            raise

    def set_object(self, name, value):
        """在R全局环境中设置对象"""
        try:
            self.globalenv[name] = value
            return True
        except Exception as e:
            logger.error(f"设置R对象 {name} 失败: {str(e)}")
            raise

    def eval_r(self, r_code):
        """在R中评估代码并返回结果"""
        try:
            return self.rinterface.parse(r_code)
        except Exception as e:
            logger.error(f"评估R代码失败: {str(e)}")
            raise


# 主要的R代码测试函数
def run_r_test(student_code, test_code, timeout=10, required_packages=None):
    """
    使用rpy2运行R测试代码评估学生代码

    Args:
        student_code (str): 学生提交的R代码
        test_code (str): 测试用例代码
        timeout (int): 执行超时时间(秒)
        required_packages (list): 需要的R包列表

    Returns:
        dict: 包含测试结果的字典
    """
    logger.info("======= 开始执行R测试 =======")
    logger.info(f"学生代码长度: {len(student_code)} 字符")
    logger.info(f"测试代码长度: {len(test_code)} 字符")

    if required_packages:
        logger.info(f"需要的R包: {', '.join(required_packages)}")

    try:
        # 导入rpy2模块
        import rpy2.robjects as ro
        from rpy2.robjects.packages import importr

        # 记录R版本
        logger.info(f"R版本: {ro.r('R.version.string')[0]}")

        # 导入基础包
        base = importr('base')
        utils = importr('utils')

        # 导入所需的包
        if required_packages:
            for package in required_packages:
                try:
                    logger.info(f"导入R包: {package}")
                    importr(package)
                except Exception as e:
                    logger.warning(f"导入R包 {package} 失败: {str(e)}")
                    try:
                        # 尝试安装包
                        logger.info(f"尝试安装R包: {package}")
                        utils.install_packages(package, repos="https://cloud.r-project.org")
                        importr(package)
                        logger.info(f"成功安装并导入R包: {package}")
                    except Exception as e:
                        logger.error(f"安装R包 {package} 失败: {str(e)}")

        # 设置R编码选项和区域
        ro.r('options(encoding="native.enc")')
        ro.r('Sys.setlocale("LC_ALL", "C")')  # 使用C区域设置，避免编码问题
        logger.info(f"当前R区域设置: {ro.r('Sys.getlocale()')[0]}")

        # 设置超时
        ro.r(f'options(timeout={timeout})')

        # 创建临时环境
        ro.r('student_env <- new.env()')

        # 设置输出捕获
        ro.r('''
        capture_output <- function() {
          output_buffer <- character(0)
          output_conn <- textConnection("output_buffer", "w", local=TRUE)

          # 保存当前的输出和消息接收器
          old_output <- getOption("connectionObserver")
          options(connectionObserver = NULL)  # 临时禁用连接观察器

          # 重定向输出和消息
          sink(output_conn, type="output")
          sink(output_conn, type="message")

          # 返回一个函数用于获取输出并恢复原始接收器
          return(function() {
            # 恢复原始接收器
            sink(type="message", NULL)
            sink(type="output", NULL)
            options(connectionObserver = old_output)

            # 关闭连接并返回缓冲区内容
            close(output_conn)
            return(output_buffer)
          })
        }

        # 初始化输出捕获
        get_output <- capture_output()
        ''')

        # 安全执行函数
        ro.r('''
        safe_eval <- function(code, env) {
          tryCatch({
            eval(parse(text=code), envir=env)
            return(list(status="success", message="代码执行成功"))
          }, error=function(e) {
            return(list(status="error", message=paste("错误:", e$message)))
          }, warning=function(w) {
            warning(w$message)
            return(list(status="warning", message=paste("警告:", w$message)))
          })
        }
        ''')

        # 执行学生代码
        logger.info("开始执行学生代码...")
        if student_code:
            # 预处理代码，处理特殊字符
            processed_code = student_code.replace('\\', '\\\\').replace('"', '\\"')
            # 安全执行
            result = ro.r(f'safe_eval("{processed_code}", student_env)')
            status = result[0]
            message = result[1]
            logger.info(f"学生代码执行结果: {status} - {message}")

            if status == "error":
                # 获取输出
                output_text = ro.r('get_output()')
                output_list = safe_convert_r_output(output_text)
                output_str = '\n'.join(output_list)

                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': message,
                    'output': output_str
                }
        else:
            logger.info("学生代码为空")

        # 修改执行测试代码的部分
        logger.info("开始执行测试代码...")
        if test_code:
            # 创建测试环境，继承学生环境
            ro.r('test_env <- new.env(parent=student_env)')

            # 检查学生环境中的变量
            student_vars = ro.r('ls(student_env)')
            logger.info(
                f"学生环境中的变量: {', '.join([str(var) for var in student_vars]) if len(student_vars) > 0 else '无'}")

            try:
                # 不要尝试在Python中处理R代码，而是将测试代码写入临时文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8') as tmp_file:
                    tmp_file_path = tmp_file.name

                    # 添加测试环境设置和时间记录
                    tmp_file.write("""
        # 测试开始
        test_start_time <- Sys.time()

        # 创建测试环境，继承学生环境
        if(!exists("test_env")) {
          test_env <- new.env(parent=parent.env(globalenv()))
          # 复制学生环境中的所有变量
          student_vars <- ls(parent.env(globalenv()))
          for(var in student_vars) {
            assign(var, get(var, envir=parent.env(globalenv())), envir=test_env)
          }
        }

        # 执行测试代码
        """)

                    # 写入原始测试代码，不做任何处理
                    tmp_file.write(test_code)

                    # 添加结果检查代码
                    tmp_file.write("""

        # 确保test_result存在
        if(!exists("test_result", envir=test_env)) {
          test_result <- list(
            status = "error",
            score = 0,
            max_score = 100,
            message = "测试代码未创建test_result变量"
          )
        }

        # 记录测试时间
        test_end_time <- Sys.time()
        test_duration <- as.numeric(difftime(test_end_time, test_start_time, units="secs"))
        test_result$duration <- test_duration

        # 返回test_result到全局环境
        assign("test_result", test_result, envir=globalenv())
        """)

                # 用R执行临时文件
                logger.info(f"通过临时文件执行测试代码: {tmp_file_path}")
                # 将路径中的反斜杠替换为正斜杠
                converted_path = tmp_file_path.replace("\\", "/")
                # 使用转换后的路径
                ro.r(f'source("{converted_path}", local=test_env)')

                # 检查测试结果
                test_result_exists = ro.r('exists("test_result")')[0]
                logger.info(f"测试结果变量存在: {test_result_exists}")

                if test_result_exists:
                    # 获取测试结果
                    result_dict = {}

                    # 获取测试结果的字段名
                    result_names = ro.r('names(test_result)')
                    logger.info(f"测试结果包含字段: {', '.join([str(name) for name in result_names])}")

                    # 获取每个字段的值
                    for key in result_names:
                        key_str = str(key)
                        try:
                            value = ro.r(f'test_result${key_str}')
                            if len(value) == 1:
                                result_dict[key_str] = value[0]
                            else:
                                result_dict[key_str] = [v for v in value]
                        except Exception as e:
                            logger.error(f"获取测试结果字段 {key_str} 失败: {str(e)}")
                            result_dict[key_str] = f"[获取失败: {str(e)}]"

                    # 获取输出
                    output_text = ro.r('get_output()')
                    output_list = safe_convert_r_output(output_text)
                    output_str = '\n'.join(output_list)

                    # 确保必要字段存在
                    required_fields = ['status', 'score', 'max_score', 'message']
                    for field in required_fields:
                        if field not in result_dict:
                            result_dict[field] = 0 if field in ['score', 'max_score'] else (
                                'error' if field == 'status' else '字段缺失')

                    # 添加输出
                    result_dict['output'] = output_str

                    # 删除临时文件
                    try:
                        os.unlink(tmp_file_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {str(e)}")

                    logger.info(
                        f"测试完成: 状态={result_dict.get('status')}, 得分={result_dict.get('score')}/{result_dict.get('max_score')}")
                    return result_dict
                else:
                    # 没有找到测试结果
                    output_text = ro.r('get_output()')
                    output_list = safe_convert_r_output(output_text)
                    output_str = '\n'.join(output_list)

                    # 删除临时文件
                    try:
                        os.unlink(tmp_file_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {str(e)}")

                    return {
                        'status': 'error',
                        'score': 0,
                        'max_score': 100,
                        'message': '测试代码未返回结果 - test_result不存在',
                        'output': output_str
                    }
            except Exception as e:
                # 测试代码执行出错
                logger.error(f"执行测试代码时出错: {str(e)}")
                traceback_str = traceback.format_exc()

                # 获取输出
                try:
                    output_text = ro.r('get_output()')
                    output_list = safe_convert_r_output(output_text)
                    output_str = '\n'.join(output_list)
                except Exception:
                    output_str = "无法获取输出"

                return {
                    'status': 'error',
                    'score': 0,
                    'max_score': 100,
                    'message': f'测试执行错误: {str(e)}',
                    'output': f"{output_str}\n\n{traceback_str}"
                }
    except Exception as e:
        # 整个过程出错
        logger.error(f"R环境执行总体异常: {str(e)}")
        traceback_str = traceback.format_exc()
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': f'R环境执行异常: {str(e)}',
            'output': traceback_str
        }