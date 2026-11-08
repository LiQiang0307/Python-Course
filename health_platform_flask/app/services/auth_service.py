"""
认证服务模块
迁移自原 health_platform/services/auth_service.py，适配 Flask 会话机制：
登录状态由 Flask session 保存 user_id，本服务不再持有可变全局状态。
"""
from flask import session

from ..models import User
from ..utils import FileHandler, Logger, Validator


class AuthService:
    """认证服务类"""

    def __init__(self, app_config):
        self.config = app_config
        self.users_file = app_config['USERS_FILE']
        self.logger = Logger(app_config['LOG_DIR'])

    # ---------- 内部辅助 ----------
    def _load_users(self):
        return FileHandler.read_json(self.users_file)

    def _save_users(self, users_data):
        return FileHandler.write_json(self.users_file, users_data)

    def find_user(self, user_id):
        """按 user_id 查找用户"""
        for user_data in self._load_users():
            if user_data['user_id'] == user_id:
                return User.from_dict(user_data)
        return None

    # ---------- 核心功能 ----------
    def register(self, username, password, phone='', email='', role='patient'):
        """用户注册，返回 (success, message, user)"""
        is_valid, msg = Validator.validate_username(username)
        if not is_valid:
            return False, msg, None

        is_valid, msg = Validator.validate_password(password)
        if not is_valid:
            return False, msg, None

        if phone:
            is_valid, msg = Validator.validate_phone(phone)
            if not is_valid:
                return False, msg, None

        if email:
            is_valid, msg = Validator.validate_email(email)
            if not is_valid:
                return False, msg, None

        users_data = self._load_users()
        if any(u['username'] == username for u in users_data):
            return False, "用户名已存在", None

        user_id = f"U{len(users_data) + 1:04d}"
        user = User(user_id, username, password, phone, email, role)
        users_data.append(user.to_dict())

        if self._save_users(users_data):
            self.logger.info(f"用户注册成功: {username}")
            return True, f"注册成功！用户ID: {user_id}", user
        return False, "保存用户失败", None

    def login(self, username, password):
        """用户登录，返回 (success, message, user)"""
        users_data = self._load_users()
        for user_data in users_data:
            if user_data['username'] == username:
                user = User.from_dict(user_data)
                if user.check_password(password):
                    user.update_last_login()
                    for i, u in enumerate(users_data):
                        if u['user_id'] == user.user_id:
                            users_data[i] = user.to_dict()
                            break
                    self._save_users(users_data)
                    self.logger.info(f"用户登录成功: {username}")
                    return True, f"欢迎，{username}！", user
                return False, "密码错误", None
        return False, "用户不存在", None

    # ---------- 会话辅助 ----------
    @staticmethod
    def login_session(user):
        """将用户写入 Flask 会话"""
        session['user_id'] = user.user_id
        session['username'] = user.username
        session.permanent = True

    @staticmethod
    def logout_session():
        """从会话移除用户"""
        session.pop('user_id', None)
        session.pop('username', None)

    def get_current_user(self):
        """从会话获取当前登录用户（非请求上下文下返回 None）"""
        try:
            user_id = session.get('user_id')
        except RuntimeError:
            return None
        if not user_id:
            return None
        return self.find_user(user_id)
