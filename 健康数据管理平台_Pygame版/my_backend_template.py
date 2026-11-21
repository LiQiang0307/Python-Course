"""已填好的 backend：把 GitHub 项目(健康数据管理平台_Pygame版)的业务接进通用框架。

这是 student_backend_template.py 的"标准答案"——针对你仓库里真实的
AuthService / DataService / Validator 接口写好的实现。

使用三步（在本教学包目录下）：
  1. 把你 GitHub 项目的 models/ services/ utils/ config.py 拷到本目录
     （即：本目录要有 config.py、models/、services/、utils/ 四个东西）
  2. 把 gui_framework.py 的 main() 改成：
         from my_backend_filled import MyBackend
         App(MyBackend()).run()
  3. python gui_framework.py

填空要点都在注释里，尤其是 register 的 **values 陷阱。
"""

import config
from models.health_record import PhysicalExamRecord, MedicationRecord, HealthRecord
from services.auth_service import AuthService
from services.data_service import DataService
from utils.validator import Validator
from backend_contract import ContractBackend


class MyBackend(ContractBackend):
    def __init__(self):
        # ★ 关键：先建数据目录（data/ 和 data/reports/）。
        #   原 gui.py 的 __init__ 里有 config.init_directories()，提取框架时易漏。
        #   漏掉后"生成报告"会因 reports 目录不存在而报"保存报告失败"。
        config.init_directories()
        # 直接复用你前8课组写好的服务类（零改动）
        self.auth = AuthService()
        self.data = DataService()

    # ===== 认证：几乎一对一搬运 =====
    def login(self, username, password):
        return self.auth.login(username, password)          # -> (ok, msg)

    def register(self, values):
        # ⚠ 陷阱：契约传的是 dict，真实 register 是拆开的关键字参数。
        #   直接 self.auth.register(values) 会报 "missing username"。
        #   必须用 ** 展开，且只保留真实签名认识的参数。
        allowed = {'username', 'password', 'phone', 'email'}
        kwargs = {k: v for k, v in values.items() if k in allowed}
        return self.auth.register(**kwargs)                  # -> (ok, msg)

    def logout(self):
        self.auth.logout()

    def get_current_user(self):
        return self.auth.get_current_user()                  # 有 .user_id / .username

    def is_logged_in(self):
        return self.auth.is_logged_in()

    # ===== 记录业务：位置传参，参数名不同不影响 =====
    def add_record(self, user_id, kind, record_date, value, **payload):
        # 真实签名第二个参数叫 record_type，但你用位置传参，无需改名
        return self.data.add_record(user_id, kind, record_date, value, **payload)

    def get_user_records(self, user_id, kind=None):
        return self.data.get_user_records(user_id, kind)     # -> list[dict]

    def get_statistics(self, user_id, kind):
        stats = self.data.get_statistics(user_id, kind)      # 无记录时返回 None
        return stats if stats is not None else {}

    def export_to_csv(self, user_id, path):
        return self.data.export_to_csv(user_id, path)        # -> (ok, msg)

    def generate_report(self, user_id, username):
        report, msg = self.data.generate_report(user_id, username)
        # 无记录时真实服务返回 (None, msg)，框架侧要能容忍
        return (report, msg) if report is not None else (None, msg)

    # ===== 插槽⑦：校验与组装（原 gui.py 207-241 行，从界面搬回业务）=====
    def prepare_record(self, values, kind):
        import math
        from datetime import date

        ok, msg = Validator.validate_date(values['record_date'])
        if not ok:
            raise ValueError(msg)
        if values['record_date'] > date.today().isoformat():
            raise ValueError('健康记录日期不能晚于今天')

        # 组装：除日期外的字段都进 payload
        payload = {k: v for k, v in values.items() if k != 'record_date'}
        if kind == '体检':
            for key in ['height', 'weight', 'blood_sugar', 'heart_rate']:
                try:
                    number = float(values[key])
                except ValueError:
                    raise ValueError('身高、体重、血糖、心率必须填写有效数字')
                if not math.isfinite(number) or number <= 0:
                    raise ValueError('数值必须为大于0的有限数字')
                if key == 'heart_rate' and not number.is_integer():
                    raise ValueError('心率必须为正整数')
                payload[key] = int(number) if key == 'heart_rate' else number
            ok, msg = Validator.validate_blood_pressure(values['blood_pressure'])
            if not ok:
                raise ValueError(msg)
            value = 'BP:%s, BS:%s' % (payload['blood_pressure'], payload['blood_sugar'])
        elif kind == '用药':
            if not all(values.get(k) for k in ['medicine_name', 'dosage', 'frequency']):
                raise ValueError('请完整填写药品名称、剂量和频次')
            if not values['duration_days'].isdigit() or int(values['duration_days']) <= 0:
                raise ValueError('用药天数必须为正整数')
            payload['duration_days'] = int(values['duration_days'])
            value = values['dosage'] + ' ' + values['frequency']
        else:
            kind = payload.pop('record_type', '') or values.get('record_type', '')
            value = payload.pop('value', '') or values.get('value', '')
            if not kind or not value or kind in ('体检', '用药'):
                raise ValueError('请填写其他记录类型和内容；体检/用药请使用专用表单')
        return kind, value, payload

    # ===== 插槽⑧：评测结果（原 gui.py 292-301 行）=====
    def build_assessment(self, records):
        if not records:
            return ['暂无体检记录']
        r = records[0]                      # get_user_records 已按日期降序
        bmi = r.get('bmi')
        if not isinstance(bmi, (int, float)) and r.get('height', 0) > 0:
            bmi = r.get('weight', 0) / (r['height'] / 100) ** 2
        return [
            '最新体检日期：' + str(r.get('record_date', '未提供')),
            'BMI：' + (f'{bmi:.2f}' if isinstance(bmi, (int, float)) else '未提供'),
            '血压：' + str(r.get('blood_pressure', '未提供')) + ' mmHg',
            '血糖：' + str(r.get('blood_sugar', '未提供')) + ' mmol/L',
            '心率：' + str(r.get('heart_rate', '未提供')) + ' 次/分',
            '已归档体检记录：%d 条' % len(records),
            '仅作数据汇总，不提供诊断或用药建议。',
        ]

    # ===== 插槽⑥：表单字段规格（原 gui.py change() 156-176 行）=====
    def field_specs(self, state, record_kind):
        if state in ('login', 'register'):
            specs = [('username', '用户名', '', False), ('password', '密码', '', True)]
            if state == 'register':
                specs += [('phone', '手机号（选填）', '', False),
                          ('email', '邮箱（选填）', '', False)]
            return specs
        if state == 'add':
            specs = [('record_date', '日期 YYYY-MM-DD', '2026-01-01', False)]
            if record_kind == '体检':
                specs += [('height', '身高 cm', '', False), ('weight', '体重 kg', '', False),
                          ('blood_pressure', '血压 120/80', '', False),
                          ('blood_sugar', '血糖 mmol/L', '', False),
                          ('heart_rate', '心率 次/分', '', False)]
            elif record_kind == '用药':
                specs += [('medicine_name', '药品名称', '', False),
                          ('dosage', '剂量（如1片）', '', False),
                          ('frequency', '频次（如每日3次）', '', False),
                          ('duration_days', '用药天数', '', False)]
            else:
                specs += [('record_type', '记录类型', '', False),
                          ('value', '数值/内容', '', False), ('unit', '单位（选填）', '', False)]
            return specs + [('notes', '备注（选填）', '', False)]
        return []
