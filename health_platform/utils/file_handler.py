'''
Author: LiQiang
Date: 2026-03-03 13:38:52
LastEditors: LiQiang
LastEditTime: 2026-03-03 13:42:23
Description: 文件描述
'''
"""
文件操作工具模块
单元8：文件读写与异常处理
"""
import json
import csv
import os
from datetime import datetime

class FileHandler:
    """文件操作类"""
    
    @staticmethod
    def read_json(filepath):
        """读取JSON文件"""
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"✗ JSON格式错误: {e}")
            return []
        except Exception as e:
            print(f"✗ 读取文件失败: {e}")
            return []
    
    @staticmethod
    def write_json(filepath, data):
        """写入JSON文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"✗ 写入文件失败: {e}")
            return False
    
    @staticmethod
    def read_csv(filepath):
        """读取CSV文件"""
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"✗ 读取CSV失败: {e}")
            return []
    
    @staticmethod
    def write_csv(filepath, data, fieldnames=None):
        """写入CSV文件"""
        try:
            if not data:
                print("✗ 数据为空")
                return False
            
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"✗ 写入CSV失败: {e}")
            return False
    
    @staticmethod
    def backup_file(source_file, backup_dir):
        """备份文件"""
        try:
            if not os.path.exists(source_file):
                print("✗ 源文件不存在")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(source_file)
            backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
            
            import shutil
            shutil.copy2(source_file, backup_path)
            print(f"✓ 备份成功: {backup_path}")
            return True
        except Exception as e:
            print(f"✗ 备份失败: {e}")
            return False