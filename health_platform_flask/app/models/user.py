"""
用户类
迁移自原 health_platform/models/user.py
"""
from datetime import datetime
import hashlib


class User:
    """用户类"""

    def __init__(self, user_id, username, password, phone='', email='',
                 role='patient', is_hashed=False):
        self.user_id = user_id
        self.username = username
        # 根据标志位决定是否加密（避免双重哈希 Bug）
        self.password = password if is_hashed else self._hash_password(password)
        self.phone = phone
        self.email = email
        self.role = role  # patient, doctor, admin
        self.created_at = datetime.now().isoformat()
        self.last_login = None

    @staticmethod
    def _hash_password(password):
        """密码哈希（教学示例使用 md5，生产建议 bcrypt/argon2）"""
        return hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        """验证密码"""
        return self._hash_password(password) == self.password

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now().isoformat()

    def to_dict(self, include_password=True):
        """转换为字典"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'last_login': self.last_login,
        }
        if include_password:
            data['password'] = self.password
        return data

    def to_public_dict(self):
        """转换为不含敏感信息的公开字典"""
        return self.to_dict(include_password=False)

    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            password=data['password'],
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            role=data.get('role', 'patient'),
            is_hashed=True,
        )

    def __str__(self):
        return f"用户：{self.username} (ID: {self.user_id}, 角色：{self.role})"
