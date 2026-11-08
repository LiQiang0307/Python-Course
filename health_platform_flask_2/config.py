'''
Author: LiQiang
Date: 2026-03-03 13:37:48
LastEditors: LiQiang
LastEditTime: 2026-03-03 13:41:24
Description: 文件描述
'''
"""
项目配置文件
单元5：模块化开发与代码复用
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')

# 文件路径
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
RECORDS_FILE = os.path.join(DATA_DIR, 'records.json')

# 应用配置
APP_CONFIG = {
    'app_name': '东软健康数据管理平台',
    'version': '1.0.0',
    'debug': False,
    'max_login_attempts': 3,
    'password_min_length': 6
}

# 确保目录存在
def init_directories():
    """初始化目录结构"""
    for dir_path in [DATA_DIR, REPORTS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✓ 创建目录: {dir_path}")