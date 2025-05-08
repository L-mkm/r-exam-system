from datetime import datetime, timedelta

def get_beijing_time():
    """获取北京时间（UTC+8）"""
    return datetime.utcnow() + timedelta(hours=8)