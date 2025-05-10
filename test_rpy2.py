# test_rpy2.py
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('rpy2_test')

# 显示环境变量
logger.info(f"R_HOME: {os.environ.get('R_HOME', '未设置')}")

try:
    # 导入rpy2
    import rpy2.robjects as ro

    logger.info("✅ 成功导入 rpy2.robjects")

    # 检查R版本
    r_version = ro.r('R.version.string')[0]
    logger.info(f"R版本: {r_version}")

    # 执行简单计算
    result = ro.r('1 + 1')[0]
    logger.info(f"1 + 1 = {result}")

    # 测试jsonlite包
    try:
        ro.r('library(jsonlite)')
        json_str = ro.r('toJSON(list(name="测试", value=123))')[0]
        logger.info(f"JSON测试: {json_str}")
        logger.info("✅ jsonlite包可用")
    except Exception as e:
        logger.error(f"jsonlite测试失败: {str(e)}")

    logger.info("rpy2测试成功!")
except Exception as e:
    logger.error(f"rpy2测试失败: {str(e)}")