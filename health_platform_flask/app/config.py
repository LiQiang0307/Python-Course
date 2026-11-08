"""
应用配置模块
支持多环境配置：开发 / 测试 / 生产
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BaseConfig:
    """基础配置"""
    APP_NAME = '东软健康数据管理平台'
    VERSION = '2.0.0'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据目录与文件
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    RECORDS_FILE = os.path.join(DATA_DIR, 'records.json')
    LOG_DIR = os.path.join(BASE_DIR, 'logs')

    # 业务配置
    MAX_LOGIN_ATTEMPTS = 3
    PASSWORD_MIN_LENGTH = 6

    JSON_AS_ASCII = False


class DevelopmentConfig(BaseConfig):
    """开发环境"""
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """测试环境"""
    DEBUG = False
    TESTING = True


class ProductionConfig(BaseConfig):
    """生产环境"""
    DEBUG = False
    TESTING = False


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config(name=None):
    """根据环境变量或参数获取配置类"""
    env = name or os.environ.get('FLASK_ENV', 'development')
    return CONFIG_MAP.get(env, DevelopmentConfig)
