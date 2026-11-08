"""
认证服务模块
单元4：函数设计与参数传递
单元5：模块化开发
"""
from models.user import User
from utils.file_handler import FileHandler
from utils.validator import Validator
from utils.logger import Logger
import config

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        """初始化认证服务"""
        self.users_file = config.USERS_FILE
        self.file_handler = FileHandler()
        self.validator = Validator()
        self.logger = Logger()
        self.current_user = None
        self.login_attempts = 0
    
    def register(self, username, password, phone='', email='', role='patient'):
        """用户注册"""
        # 验证用户名
        is_valid, msg = self.validator.validate_username(username)
        if not is_valid:
            return False, msg
        
        # 验证密码
        is_valid, msg = self.validator.validate_password(password)
        if not is_valid:
            return False, msg
        
        # 验证手机号（如果提供）
        if phone:
            is_valid, msg = self.validator.validate_phone(phone)
            if not is_valid:
                return False, msg
        
        # 验证邮箱（如果提供）
        if email:
            is_valid, msg = self.validator.validate_email(email)
            if not is_valid:
                return False, msg
        
        # 读取现有用户
        users_data = self.file_handler.read_json(self.users_file)
        
        # 检查用户名是否已存在
        for user_data in users_data:
            if user_data['username'] == username:
                return False, "用户名已存在"
        
        # 生成用户ID
        user_id = f"U{len(users_data) + 1:04d}"
        
        # 创建用户
        user = User(user_id, username, password, phone, email, role)
        users_data.append(user.to_dict())
        
        # 保存用户
        if self.file_handler.write_json(self.users_file, users_data):
            self.logger.info(f"用户注册成功: {username}")
            return True, f"注册成功！用户ID: {user_id}"
        else:
            return False, "保存用户失败"
    
    def login(self, username, password):
        """用户登录"""
        # 检查登录尝试次数
        if self.login_attempts >= config.APP_CONFIG['max_login_attempts']:
            return False, "登录尝试次数过多，请稍后再试"
        
        # 读取用户数据
        users_data = self.file_handler.read_json(self.users_file)
        
        # 查找用户
        for user_data in users_data:
            if user_data['username'] == username:
                user = User.from_dict(user_data)
                
                # 验证密码
                if user.check_password(password):
                    # 更新登录信息
                    user.update_last_login()
                    self.current_user = user
                    
                    # 更新用户数据
                    for i, u in enumerate(users_data):
                        if u['username'] == username:
                            users_data[i] = user.to_dict()
                            break
                    
                    self.file_handler.write_json(self.users_file, users_data)
                    self.login_attempts = 0
                    self.logger.info(f"用户登录成功: {username}")
                    return True, f"欢迎，{username}！"
                else:
                    self.login_attempts += 1
                    remaining = config.APP_CONFIG['max_login_attempts'] - self.login_attempts
                    return False, f"密码错误，剩余尝试次数: {remaining}"
        
        return False, "用户不存在"
    
    def logout(self):
        """用户登出"""
        if self.current_user:
            username = self.current_user.username
            self.current_user = None
            self.logger.info(f"用户登出: {username}")
            return True, "登出成功"
        return False, "当前未登录"
    
    def is_logged_in(self):
        """检查是否已登录"""
        return self.current_user is not None
    
    def get_current_user(self):
        """获取当前用户"""
        return self.current_user