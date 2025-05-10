# test_r_integration.py
import r_setup  # 首先导入r_setup

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_r')

logger.info("测试R与Python集成")
logger.info(f"R_HOME环境变量: {os.environ.get('R_HOME', '未设置')}")

# 测试rpy2是否可用
try:
    import rpy2.robjects as ro

    logger.info("✓ 成功导入rpy2.robjects")

    # 测试基本R操作
    result = ro.r('1 + 1')
    logger.info(f"1 + 1 = {result[0]}")

    # 测试获取R版本
    r_version = ro.r('R.version.string')[0]
    logger.info(f"R版本: {r_version}")

    # 测试jsonlite包
    try:
        json_str = ro.r('toJSON(list(name="测试", value=123))')[0]
        logger.info(f"JSON测试: {json_str}")
        logger.info("✓ jsonlite包正常工作")
    except Exception as e:
        logger.error(f"jsonlite包测试失败: {str(e)}")

    # 测试创建简单的数据框
    ro.r('''
    df <- data.frame(
        x = 1:5,
        y = c("a", "b", "c", "d", "e")
    )
    ''')

    # 打印数据框
    logger.info("数据框测试:")
    df_str = ro.r('capture.output(print(df))')
    for line in df_str:
        logger.info(line)

    logger.info("✓ 所有测试通过!")

except Exception as e:
    logger.error(f"测试失败: {str(e)}")
    import traceback

    logger.error(traceback.format_exc())