"""业务插槽契约 —— 学生要把自己的命令行项目接到框架上时，实现这个类。

框架 gui_framework.py 只认这里的方法签名，不关心内部是你自己的代码、
还是老师提供的 AuthService/DataService。这就是"解耦"的接头。

学生填空规则：
1. 每个方法返回什么、抛什么，严格按 docstring（框架依赖这些约定）。
2. 其余内部实现随意，用你前8课组写过的任何模块都可以。
3. 直接继承 ContractBackend，把 NotImplemented 换成你的代码。
"""

from abc import ABC, abstractmethod


class ContractBackend(ABC):
    """框架与业务之间的唯一约定（接口 / 抽象基类）。"""

    # ---------- 认证（对应第1-3/8课组）----------
    @abstractmethod
    def login(self, username, password):
        """-> (ok: bool, msg: str)"""
        raise NotImplementedError

    @abstractmethod
    def register(self, values):
        """values: dict（含 username/password/phone/email） -> (ok, msg)"""
        raise NotImplementedError

    @abstractmethod
    def logout(self):
        raise NotImplementedError

    @abstractmethod
    def get_current_user(self):
        """-> 用户对象，需有 .user_id 和 .username；未登录 -> None"""
        raise NotImplementedError

    @abstractmethod
    def is_logged_in(self):
        """-> bool"""
        raise NotImplementedError

    # ---------- 记录业务（对应第4-8课组）----------
    @abstractmethod
    def add_record(self, user_id, kind, record_date, value, **payload):
        """-> (ok, msg)。可复用你第8课组的 DataService.add_record。"""
        raise NotImplementedError

    @abstractmethod
    def get_user_records(self, user_id, kind=None):
        """-> list[dict]，每条至少含 record_date / value / kind。"""
        raise NotImplementedError

    @abstractmethod
    def get_statistics(self, user_id, kind):
        """-> dict 或可迭代的 (指标名, 数值)，用于统计页卡片。"""
        raise NotImplementedError

    @abstractmethod
    def export_to_csv(self, user_id, path):
        """-> (ok, msg)，把记录写到 path。"""
        raise NotImplementedError

    @abstractmethod
    def generate_report(self, user_id, username):
        """-> (report, msg)，report 需有 .content 属性（字符串）。"""
        raise NotImplementedError

    # ---------- 插槽⑦：校验与组装（原 gui.py 207-241 行搬回业务层）----------
    @abstractmethod
    def prepare_record(self, values, kind):
        """把界面收集的字符串 -> (kind, value, payload: dict)。

        校验失败请 raise ValueError('人话错误提示')；框架会捕获并显示。
        这是"界面给字符串、业务要结构化数据"的转换点，应由业务负责。
        """
        raise NotImplementedError

    # ---------- 插槽⑧：评测结果计算（原 gui.py 292-301 行搬回业务层）----------
    @abstractmethod
    def build_assessment(self, records):
        """-> list[str]，根据体检记录生成结果面板的每一行文字。"""
        raise NotImplementedError

    # ---------- 插槽⑥：表单字段规格（原 gui.py change() 156-176 行）----------
    def field_specs(self, state, record_kind):
        """-> list[(key, label, default, secret)]；不覆写则用下面的默认示例。"""
        defaults = {
            'login': [('username', '用户名', '', False), ('password', '密码', '', True)],
            'register': [('username', '用户名', '', False), ('password', '密码', '', True),
                         ('phone', '手机号（选填）', '', False), ('email', '邮箱（选填）', '', False)],
            'add': [('record_date', '日期 YYYY-MM-DD', '2026-01-01', False)],
        }
        return defaults.get(state, [])
