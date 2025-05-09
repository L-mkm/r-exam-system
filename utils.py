from datetime import datetime, timedelta

def get_beijing_time():
    """获取北京时间（UTC+8）"""
    return datetime.utcnow() + timedelta(hours=8)

def to_beijing_time(utc_time):
    """将UTC时间转换为北京时间"""
    if utc_time is None:
        return None
    return utc_time + timedelta(hours=8)