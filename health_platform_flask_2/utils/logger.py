'''
Author: LiQiang
Date: 2026-03-03 13:39:11
LastEditors: LiQiang
LastEditTime: 2026-03-03 13:43:00
Description: 文件描述
'''
"""
日志模块
单元8：文件读写与异常处理
"""
import os
from datetime import datetime

class Logger:
    """日志记录类"""
    
    def __init__(self, log_dir='logs'):
        """初始化日志记录器"""
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        date_str = datetime.now().strftime("%Y%m%d")
        self.log_file = os.path.join(log_dir, f"app_{date_str}.log")
    
    def _write_log(self, level, message):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"写入日志失败: {e}")
    
    def info(self, message):
        """信息日志"""
        self._write_log("INFO", message)
        print(f"[INFO] {message}")
    
    def error(self, message):
        """错误日志"""
        self._write_log("ERROR", message)
        print(f"[ERROR] {message}")
    
    def warning(self, message):
        """警告日志"""
        self._write_log("WARNING", message)
        print(f"[WARNING] {message}")
    
    def debug(self, message):
        """调试日志"""
        self._write_log("DEBUG", message)