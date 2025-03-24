import r_setup
import os
import sys # 表示：如果找不到需要的工具，就告诉用户问题所在，然后干脆停止工作

# 打印当前R_HOME环境变量值
print(f"当前R_HOME环境变量: {os.environ.get('R_HOME', '未设置')}")

try:
    import rpy2.robjects as robjects
    # 打印当前R版本
    print(robjects.r('R.version.string')[0])

    # 执行简单的R代码
    result = robjects.r('1 + 1')
    print(f"R计算结果: {result[0]}")

    # 尝试创建一个简单的图形（可选）
    robjects.r('x <- 1:10')
    robjects.r('y <- x^2')
    robjects.r('plot(x, y, main="测试R绘图")')

    print("R语言集成测试成功！")

except Exception as e:
    print(f"R语言集成测试失败: {e}")
