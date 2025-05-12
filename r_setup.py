# r_setup.py - 改进的R语言集成模块
import os
import sys
import tempfile
import json
import traceback
import logging
import subprocess
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

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
def run_r_test(student_code, test_code):
    """运行R代码测试，返回测试结果"""
    try:
        # 初始化R环境
        logger.info("初始化R环境...")

        # 使用localconverter确保转换规则的上下文正确传递
        with localconverter(ro.default_converter):
            # 激活pandas到R的转换
            pandas2ri.activate()

            # 创建一个新的R环境用于学生代码
            student_env = ro.r('new.env()')

            # 将环境变量传递给R
            ro.globalenv['student_env'] = student_env

            # 执行学生代码
            ro.r(f"""
            tryCatch({{
                # 在学生环境中执行代码
                eval(parse(text = {ro.StrVector([student_code])}), envir = student_env)
            }}, error = function(e) {{
                # 返回错误信息
                print(paste("学生代码执行错误:", e$message))
                stop(e$message)
            }})
            """)

            # 执行测试代码
            result = ro.r(f"""
            tryCatch({{
                # 执行测试代码
                eval(parse(text = {ro.StrVector([test_code])}))

                # 测试代码应该设置一个名为test_result的列表
                if (exists("test_result")) {{
                    test_result
                }} else {{
                    list(
                        status = "error",
                        score = 0,
                        max_score = 100,
                        message = "测试代码未设置test_result变量"
                    )
                }}
            }}, error = function(e) {{
                # 返回错误信息
                list(
                    status = "error",
                    score = 0,
                    max_score = 100,
                    message = paste("测试代码执行错误:", e$message)
                )
            }})
            """)

            # 将R的list转换成Python字典
            py_result = {}
            for key in result.names:
                py_result[key] = result[key][0]

            return py_result
    except Exception as e:
        # 捕获所有异常
        logger.error(f"R环境执行异常: {str(e)}")
        return {
            'status': 'error',
            'score': 0,
            'max_score': 100,
            'message': f'R环境执行异常: {str(e)}'
        }