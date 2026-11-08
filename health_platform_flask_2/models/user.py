"""
用户类
单元 6：类与对象设计模式
单元 8：程序健壮性与调试 (修复双重哈希 Bug)
"""
from datetime import datetime
import hashlib

class User:
    """用户类"""
    
    def __init__(self, user_id, username, password, phone='', email='', role='patient', is_hashed=False):
        """初始化用户
        :param is_hashed: 密码是否已经加密，默认 False（注册时为 False，加载时为 True）
        """
        self.user_id = user_id
        self.username = username
        # 【修复点】根据标志位决定是否加密
        if is_hashed:
            self.password = password
        else:
            self.password = self._hash_password(password)
        self.phone = phone
        self.email = email
        self.role = role  # patient, doctor, admin
        self.created_at = datetime.now().isoformat()
        self.last_login = None
    
    def _hash_password(self, password):
        """密码哈希（简单示例）"""
        # 实际项目中建议使用 bcrypt 或 argon2，这里为了教学使用 md5
        return hashlib.md5(password.encode()).hexdigest()
    
    def check_password(self, password):
        """验证密码"""
        # 将输入的明文密码加密后，与存储的哈希密码对比
        return self._hash_password(password) == self.password
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now().isoformat()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,  # 存储的是哈希值
            'phone': self.phone,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象
        【修复点】从文件加载时，密码已经是哈希值，需传入 is_hashed=True
        """
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            password=data['password'],
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            role=data.get('role', 'patient'),
            is_hashed=True  # ⭐ 关键修复：告诉构造函数不要再次加密
        )
    
    def __str__(self):
        """字符串表示"""
        return f"用户：{self.username} (ID: {self.user_id}, 角色：{self.role})"