'''
Author: LiQiang
Date: 2026-03-03 13:39:02
LastEditors: LiQiang
LastEditTime: 2026-03-03 13:42:42
Description: 文件描述
'''
"""
数据验证模块
单元2：程序流程控制与逻辑构建
单元4：函数设计与参数传递
"""
import re

class Validator:
    """数据验证类"""
    
    @staticmethod
    def validate_username(username):
        """验证用户名"""
        if not username or len(username) < 4 or len(username) > 16:
            return False, "用户名长度必须在4-16位之间"
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5]+$', username):
            return False, "用户名只能包含字母、数字和中文"
        return True, ""
    
    @staticmethod
    def validate_password(password):
        """验证密码"""
        if not password or len(password) < 6:
            return False, "密码长度不能少于6位"
        
        has_digit = any(c.isdigit() for c in password)
        has_letter = any(c.isalpha() for c in password)
        
        if not (has_digit and has_letter):
            return False, "密码必须包含数字和字母"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone):
        """验证手机号"""
        if not phone or len(phone) != 11 or not phone.isdigit():
            return False, "手机号必须是11位数字"
        if not phone.startswith(('13', '15', '18', '19')):
            return False, "手机号格式不正确"
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """验证邮箱"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "邮箱格式不正确"
        return True, ""
    
    @staticmethod
    def validate_health_data(data):
        """验证健康数据"""
        errors = []
        
        # 验证必填字段
        required_fields = ['user_id', 'record_type', 'record_date']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证数值字段
        if 'value' in data:
            try:
                float(data['value'])
            except (ValueError, TypeError):
                errors.append("数值字段必须是数字")
        
        if errors:
            return False, errors
        return True, []