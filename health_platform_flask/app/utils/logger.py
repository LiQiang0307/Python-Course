"""
日志模块
迁移自原 health_platform/utils/logger.py
"""
import os
from datetime import datetime


class Logger:
    """日志记录类（文件 + 控制台）"""

    def __init__(self, log_dir=None):
        self.log_dir = log_dir or 'logs'
        os.makedirs(self.log_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        self.log_file = os.path.join(self.log_dir, f"app_{date_str}.log")

    def _write_log(self, level, message):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except OSError as e:
            print(f"写入日志失败: {e}")

    def info(self, message):
        self._write_log("INFO", message)

    def error(self, message):
        self._write_log("ERROR", message)

    def warning(self, message):
        self._write_log("WARNING", message)

    def debug(self, message):
        self._write_log("DEBUG", message)
