# test_r_direct.py
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("r_test")

# 定义可能的R路径
possible_r_paths = [
    # Conda环境中的路径
    r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R\bin\Rscript.exe',
    r'C:\Users\86131\anaconda3\envs\r_exam_env\Lib\R\bin\x64\Rscript.exe',
    r'C:\Users\86131\anaconda3\envs\r_exam_env\Scripts\Rscript.exe',
    # 系统R路径
    r'C:\Program Files\R\R-4.4.1\bin\Rscript.exe',
    # 通用命令
    'Rscript'
]

# 查找第一个存在的R路径
r_path = None
for path in possible_r_paths:
    if os.path.exists(path) or path == 'Rscript':
        r_path = path
        break

logger.info(f"使用R路径: {r_path}")

# 测试R版本
if r_path:
    cmd = [r_path, "-e", "cat(R.version.string)"]
    logger.info(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        logger.info(f"R版本: {result.stdout}")
        logger.info(f"错误输出: {result.stderr if result.stderr else '无'}")
        logger.info(f"退出代码: {result.returncode}")

        # 检查是否为所需的R 4.4.3版本
        if "R version 4.4.3" in result.stdout:
            logger.info("✅ 找到了正确的R 4.4.3版本!")
        else:
            logger.warning("⚠️ R版本不是所需的4.4.3版本")

        # 测试jsonlite包
        cmd = [r_path, "-e", "if(require(jsonlite)) cat('jsonlite可用') else cat('jsonlite不可用')"]
        logger.info(f"检查jsonlite包: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        logger.info(f"jsonlite状态: {result.stdout}")
        logger.info(f"错误输出: {result.stderr if result.stderr else '无'}")
    except Exception as e:
        logger.error(f"执行R命令时出错: {str(e)}")
else:
    logger.error("未找到任何可用的R路径")

# 显示环境变量
logger.info(f"当前R_HOME环境变量: {os.environ.get('R_HOME', '未设置')}")
logger.info(f"当前PATH环境变量: {os.environ.get('PATH', '未设置')}")