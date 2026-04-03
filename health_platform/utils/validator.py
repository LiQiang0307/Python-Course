'''Author: LiQiang
Date: 2026-03-03 13:39:02
LastEditors: LiQiang
LastEditTime: 2026-04-03 13:42:42
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
        if not username:
            return False, "用户名不能为空"
        # 计算用户名长度，中文字符视为2个字符
        length = 0
        for char in username:
            if '\u4e00' <= char <= '\u9fa5':
                length += 2
            else:
                length += 1
        if length < 4 or length > 16:
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
    def validate_date(date_str):
        """验证日期格式 (YYYY-MM-DD)"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False, "日期格式不正确，应为YYYY-MM-DD"
        return True, ""
    
    @staticmethod
    def validate_blood_pressure(bp_str):
        """验证血压格式"""
        pattern = r'^\d{2,3}/\d{2,3}$'
        if not re.match(pattern, bp_str):
            return False, "血压格式不正确，应为收缩压/舒张压（如：120/80）"
        # 验证数值范围
        try:
            systolic, diastolic = map(int, bp_str.split('/'))
            if systolic < 60 or systolic > 200 or diastolic < 40 or diastolic > 130:
                return False, "血压数值超出正常范围"
        except ValueError:
            return False, "血压数值格式不正确"
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
        
        # 验证日期格式
        if 'record_date' in data and data['record_date']:
            is_valid, msg = Validator.validate_date(data['record_date'])
            if not is_valid:
                errors.append(msg)
        
        # 验证血压格式
        if 'blood_pressure' in data and data['blood_pressure']:
            is_valid, msg = Validator.validate_blood_pressure(data['blood_pressure'])
            if not is_valid:
                errors.append(msg)
        
        # 验证数值字段
        if 'value' in data and data['value']:
            try:
                float(data['value'])
            except (ValueError, TypeError):
                errors.append("数值字段必须是数字")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def clean_input(input_str):
        """清洗用户输入"""
        if not input_str:
            return ""
        # 移除首尾空白字符
        cleaned = input_str.strip()
        # 移除连续的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
    
    @staticmethod
    def clean_numeric_input(input_str):
        """清洗数值输入"""
        if not input_str:
            return ""
        # 只保留数字和小数点
        cleaned = re.sub(r'[^0-9.]', '', input_str)
        # 确保只有一个小数点
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        return cleaned
    
    @staticmethod
    def clean_phone_input(phone):
        """清洗手机号输入"""
        if not phone:
            return ""
        # 只保留数字
        cleaned = re.sub(r'\D', '', phone)
        return cleaned
    
    @staticmethod
    def clean_email_input(email):
        """清洗邮箱输入"""
        if not email:
            return ""
        # 移除首尾空白字符
        cleaned = email.strip()
        # 转换为小写
        cleaned = cleaned.lower()
        return cleaned