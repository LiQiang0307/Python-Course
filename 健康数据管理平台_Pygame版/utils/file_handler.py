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
        except (OSError, json.JSONDecodeError) as e:
            # 不把损坏文件当成空列表，避免后续保存覆盖已有数据。
            raise ValueError(f"无法读取数据文件 {filepath}: {e}") from e

    @staticmethod
    def write_json(filepath, data):
        """写入JSON文件"""
        try:
            import tempfile
            directory = os.path.dirname(os.path.abspath(filepath))
            os.makedirs(directory, exist_ok=True)
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=directory,
                                                 delete=False) as f:
                    temp_path = f.name
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, filepath)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
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
                fieldnames = list(dict.fromkeys(key for row in data for key in row))
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                # 电子表格打开 CSV 时，用户文本不应被当作公式执行。
                safe = [{k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@'))
                             else v) for k, v in row.items()} for row in data]
                writer.writerows(safe)
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