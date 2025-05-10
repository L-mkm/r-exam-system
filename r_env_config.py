# r_env_config.py - 集中管理所有R环境设置
import os
import sys
import platform

# 检测操作系统
is_windows = platform.system() == 'Windows'

# R环境路径（根据您的系统进行修改）
R_HOME_PATH = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R'
R_PACKAGES_PATH = r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\site-packages'


def setup_r_environment():
    """设置R环境变量和路径"""
    # 设置R_HOME环境变量 - 使用正斜杠避免路径问题
    os.environ['R_HOME'] = R_HOME_PATH.replace('\\', '/')
    print(f"R_HOME设置为: {os.environ['R_HOME']}")

    # 设置区域 - 使用C区域设置更加稳定
    os.environ['LC_ALL'] = 'C'
    print(f"LC_ALL设置为: {os.environ['LC_ALL']}")

    # 添加R包路径到Python路径
    r_site_packages = R_PACKAGES_PATH.replace('\\', '/')
    if r_site_packages not in sys.path:
        sys.path.append(r_site_packages)
        print(f"添加R包路径到sys.path: {r_site_packages}")

    return True


# 在导入时自动设置环境
setup_r_environment()