"""
文件操作工具模块
迁移自原 health_platform/utils/file_handler.py
"""
import csv
import json
import os
import shutil
from datetime import datetime


class FileHandler:
    """文件操作类"""

    @staticmethod
    def read_json(filepath):
        """读取 JSON 文件"""
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON格式错误: {e}")
            return []
        except OSError as e:
            print(f"读取文件失败: {e}")
            return []

    @staticmethod
    def write_json(filepath, data):
        """写入 JSON 文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print(f"写入文件失败: {e}")
            return False

    @staticmethod
    def read_csv(filepath):
        """读取 CSV 文件"""
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                return list(csv.DictReader(f))
        except OSError as e:
            print(f"读取CSV失败: {e}")
            return []

    @staticmethod
    def write_csv(filepath, data, fieldnames=None):
        """写入 CSV 文件"""
        try:
            if not data:
                return False
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            return True
        except OSError as e:
            print(f"写入CSV失败: {e}")
            return False

    @staticmethod
    def backup_file(source_file, backup_dir):
        """备份文件"""
        try:
            if not os.path.exists(source_file):
                return False
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(source_file)
            backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
            shutil.copy2(source_file, backup_path)
            return backup_path
        except OSError as e:
            print(f"备份失败: {e}")
            return None
