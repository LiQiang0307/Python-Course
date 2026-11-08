"""
数据验证模块
迁移自原 health_platform/utils/validator.py
"""
import re


class Validator:
    """数据验证类"""

    @staticmethod
    def validate_username(username):
        """验证用户名（中文字符计为2位，总长度4-16）"""
        if not username:
            return False, "用户名不能为空"
        length = sum(2 if '\u4e00' <= c <= '\u9fa5' else 1 for c in username)
        if length < 4 or length > 16:
            return False, "用户名长度必须在4-16位之间"
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5]+$', username):
            return False, "用户名只能包含字母、数字和中文"
        return True, ""

    @staticmethod
    def validate_password(password):
        """验证密码：至少6位，含数字和字母"""
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
        """验证日期格式 YYYY-MM-DD（含真实日期校验）"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str or ''):
            return False, "日期格式不正确，应为YYYY-MM-DD"
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return False, "日期不是有效的真实日期"
        return True, ""

    @staticmethod
    def validate_blood_pressure(bp_str):
        """验证血压格式，如 120/80"""
        if not re.match(r'^\d{2,3}/\d{2,3}$', bp_str or ''):
            return False, "血压格式不正确，应为收缩压/舒张压（如：120/80）"
        try:
            systolic, diastolic = map(int, bp_str.split('/'))
            if systolic < 60 or systolic > 200 or diastolic < 40 or diastolic > 130:
                return False, "血压数值超出正常范围"
        except ValueError:
            return False, "血压数值格式不正确"
        return True, ""

    @staticmethod
    def validate_record_data(data):
        """验证健康记录数据，返回 (是否合法, 错误列表)"""
        errors = []
        required_fields = ['user_id', 'record_type', 'record_date']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"缺少必需字段: {field}")

        if data.get('record_date'):
            is_valid, msg = Validator.validate_date(data['record_date'])
            if not is_valid:
                errors.append(msg)

        if data.get('blood_pressure'):
            is_valid, msg = Validator.validate_blood_pressure(data['blood_pressure'])
            if not is_valid:
                errors.append(msg)

        if errors:
            return False, errors
        return True, []

    # ---------- 输入清洗 ----------
    @staticmethod
    def clean_input(input_str):
        """清洗用户输入：去除首尾及连续空白"""
        if not input_str:
            return ""
        return re.sub(r'\s+', ' ', input_str.strip())

    @staticmethod
    def clean_numeric_input(input_str):
        """清洗数值输入：只保留数字和小数点"""
        if not input_str:
            return ""
        cleaned = re.sub(r'[^0-9.]', '', input_str)
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        return cleaned

    @staticmethod
    def clean_phone_input(phone):
        """清洗手机号输入：只保留数字"""
        if not phone:
            return ""
        return re.sub(r'\D', '', phone)

    @staticmethod
    def clean_email_input(email):
        """清洗邮箱输入"""
        if not email:
            return ""
        return email.strip().lower()
