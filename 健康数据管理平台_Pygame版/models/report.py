'''
Author: LiQiang
Date: 2026-03-03 13:39:50
LastEditors: LiQiang
LastEditTime: 2026-03-03 13:44:00
Description: 文件描述
'''
"""
报告类
单元6：类与对象设计模式
"""
from datetime import datetime

class Report:
    """健康报告类"""
    
    def __init__(self, report_id, user_id, title, content, report_type='summary'):
        """初始化报告"""
        self.report_id = report_id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.report_type = report_type
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'report_type': self.report_type,
            'created_at': self.created_at
        }
    
    def save_to_file(self, filepath):
        """保存报告到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"标题: {self.title}\n")
                f.write(f"生成时间: {self.created_at}\n")
                f.write(f"{'='*60}\n\n")
                f.write(self.content)
            return True
        except Exception as e:
            print(f"保存报告失败: {e}")
            return False
    
    def __str__(self):
        """字符串表示"""
        return f"报告: {self.title} ({self.report_type})"