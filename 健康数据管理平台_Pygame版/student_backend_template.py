"""学生填空模板：把你自己前8课组的命令行项目接进统一框架。

用法：
1. 直接在【本文件 my_backend_template.py】里填空，把每个 raise NotImplementedError
   换成你的实现。gui_framework.py 第 67 行已 import 本文件，不用改框架那一行。
2. 把你前8课组项目里的 config.py / models/ / services/ / utils/ 拷到本文件同目录。
3. 运行 python gui_framework.py；改框架末尾 main() 可切回 DemoBackend 做对照。

怎么读这份模板的注释（重要）：
- 每个方法的 docstring 只写【契约】：框架会传什么、要你还什么、失败时抛什么。
  这是接头标准，不是答案——真实项目的接口文档也长这样。
- 注释【不写】具体实现，也不写"注意哪几个坑"。填法由你自己决定，
  几个经典的坑留给"验"环节亲自踩出来，踩完写进观察表。
- 想一想：换个界面（网页 / 手机 / 命令行），这些方法还用不用？
  用的是业务，该换的是界面——这就是这节课要你读懂的"解耦"。

AI 边界：契约可以直接看、可以用；具体填空和踩坑过程请独立做。
把整份模板连注释喂给 AI 让它一次生成 13 个方法，等于跳过"验"，
你不会知道接口对不上时到底哪里断了。
"""

from backend_contract import ContractBackend


class MyBackend(ContractBackend):
    """【返回字段契约】框架按下面的字段名 / 类型读记录，对不上就显示不出来。
    这是接头规格，不是实现提示——拿它去核对你自己 to_dict() 的输出，
    发现不一致时改的是你的模型，不是框架。

    记录（get_user_records 返回的 list[dict]，每条至少含）：
      record_date  str   日期，如 '2026-01-01'
      record_type  str   类型短名：'体检' / '用药' / 其他自定义名
                         查询页过滤按钮传的就是这些值
      value        str   一句话摘要；框架直接 str() 显示，别塞 dict / list

    明细（要放在记录的【顶层】，嵌套在 dict 里框架读不到、详情弹窗空白）：
      height, weight, blood_pressure, blood_sugar, heart_rate
      medicine_name, dosage, frequency, duration_days
      unit, notes

    用户对象（get_current_user 返回）：需有 .user_id 和 .username。
    """

    def __init__(self):
        """无返回。契约：建好你项目里已有的服务对象，供下面各方法调用。"""
        raise NotImplementedError

    # ===== 认证：调用你第1-3课组 / 第8课组的用户模块 =====
    def login(self, username, password):
        """契约 -> (ok: bool, msg: str)。"""
        # 用你自己的登录模块核对账号密码。
        raise NotImplementedError

    def register(self, values):
        """契约 -> (ok: bool, msg: str)。values 是 dict，含 username/password/name/phone/email。"""
        # 用你自己的注册模块建账号。
        raise NotImplementedError

    def logout(self):
        """契约 -> 无返回。清掉当前登录状态。"""
        raise NotImplementedError

    def get_current_user(self):
        """契约 -> 用户对象，需有 .user_id 和 .username；未登录 -> None。"""
        raise NotImplementedError

    def is_logged_in(self):
        """契约 -> bool。"""
        raise NotImplementedError

    # ===== 记录业务：调用你第4-8课组的数据模块 =====
    def add_record(self, user_id, kind, record_date, value, **payload):
        """契约 -> (ok: bool, msg: str)。payload 是表单里的其余字段。"""
        # 把一条记录交给你的数据模块持久化。
        raise NotImplementedError

    def get_user_records(self, user_id, kind=None):
        """契约 -> list[dict]；每条的键和类型见类顶部【返回字段契约】。
        kind=None 返回全部，否则只返回 record_type == kind 的记录。"""
        # 取当前用户的记录，按 kind 过滤。
        raise NotImplementedError

    def get_statistics(self, user_id, kind):
        """契约 -> dict，或可迭代的 (指标名, 数值) 对，用于统计页卡片。"""
        raise NotImplementedError

    def export_to_csv(self, user_id, path):
        """契约 -> (ok: bool, msg: str)。把记录写到 path。"""
        raise NotImplementedError

    def generate_report(self, user_id, username):
        """契约 -> (report, msg: str)。report 需有 .content 字符串属性；
        无记录时 report 可为 None（框架只弹提示，不切页）。"""
        raise NotImplementedError

    # ===== 插槽⑦：校验与组装（界面字符串 -> 业务数据）=====
    def prepare_record(self, values, kind):
        """契约 -> (kind, value, payload: dict)；校验失败 raise ValueError('人话提示')。"""
        # 想一想：这段为什么该放在"业务"而不是"界面"？
        raise NotImplementedError

    # ===== 插槽⑧：评测结果计算 =====
    def build_assessment(self, records):
        """契约 -> list[str]，每项是一行结果文字。"""
        raise NotImplementedError

    # ===== 插槽⑥：表单字段规格（可按需覆写）=====
    def field_specs(self, state, record_kind):
        """契约 -> list[(key, label, default, secret)]，决定该页有哪些输入框。"""
        # 先不覆写也能跑通最小闭环；等各页字段需要调整时再回来改。
        return super().field_specs(state, record_kind)
