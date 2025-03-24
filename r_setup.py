import os
import sys

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