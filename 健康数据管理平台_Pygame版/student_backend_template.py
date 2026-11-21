"""学生填空模板：把你自己前8课组的命令行项目接进统一框架。

用法：
1. copy 本文件为 my_backend.py
2. 把每个 TODO 换成你自己项目的代码（调用你的 services / utils / 文件）
3. 在 gui_framework.py 的 main() 里：from my_backend import MyBackend; App(MyBackend()).run()

你不需要改 gui_framework.py 的任何一行。这就是"框架讲一次，各自填业务"。
"""

from backend_contract import ContractBackend


class MyBackend(ContractBackend):
    def __init__(self):
        # TODO: 在这里创建你自己项目的服务对象。
        # 例：from services.auth_service import AuthService
        #     from services.data_service import DataService
        #     self.auth, self.data = AuthService(), DataService()
        self.auth = None
        self.data = None

    # ===== 认证：调用你第1-3课组/第8课组的用户模块 =====
    def login(self, username, password):
        # TODO: return self.auth.login(username, password)  # 你的实现
        raise NotImplementedError('用你自己的登录逻辑替换')

    def register(self, values):
        # TODO: return self.auth.register(**values)
        raise NotImplementedError('用你自己的注册逻辑替换')

    def logout(self):
        # TODO: self.auth.logout()
        raise NotImplementedError

    def get_current_user(self):
        # TODO: return self.auth.get_current_user()  # 需有 .user_id / .username
        raise NotImplementedError

    def is_logged_in(self):
        # TODO: return self.auth.is_logged_in()
        raise NotImplementedError

    # ===== 记录业务：调用你第4-8课组的数据模块 =====
    def add_record(self, user_id, kind, record_date, value, **payload):
        # TODO: return self.data.add_record(user_id, kind, record_date, value, **payload)
        raise NotImplementedError

    def get_user_records(self, user_id, kind=None):
        # TODO: return self.data.get_user_records(user_id, kind)
        raise NotImplementedError

    def get_statistics(self, user_id, kind):
        # TODO: return self.data.get_statistics(user_id, kind)
        raise NotImplementedError

    def export_to_csv(self, user_id, path):
        # TODO: return self.data.export_to_csv(user_id, path)
        raise NotImplementedError

    def generate_report(self, user_id, username):
        # TODO: return self.data.generate_report(user_id, username)
        raise NotImplementedError

    # ===== 插槽⑦：校验与组装（界面字符串 -> 业务数据）=====
    # 想一想：这段为什么该放在"业务"而不是"界面"？
    # 提示：换个界面（网页/手机/命令行），这段还用不用？
    def prepare_record(self, values, kind):
        # TODO: 校验日期、数字、必填项；组装成 (kind, value, payload)
        # 失败时 raise ValueError('人话提示')，框架会显示给用户
        # 返回 (kind, value, payload_dict)
        raise NotImplementedError('把原 gui.py 207-241 行的校验逻辑搬到这里')

    # ===== 插槽⑧：评测结果计算 =====
    def build_assessment(self, records):
        # TODO: 从体检记录算 BMI 等，返回一行行文字 list[str]
        raise NotImplementedError('把原 gui.py 292-301 行的计算搬到这里')

    # ===== 插槽⑥：表单字段规格（可按需覆写）=====
    def field_specs(self, state, record_kind):
        # TODO: 你项目有哪些录入项？按 (key, label, default, secret) 列出
        return super().field_specs(state, record_kind)
