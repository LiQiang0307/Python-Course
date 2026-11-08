"""
健康评测服务模块（新增）
提供 BMI / 血压 / 血糖 / 心率等指标的健康评测，用于"评测结果"页面。
"""


class AssessmentService:
    """健康评测服务类"""

    @staticmethod
    def evaluate_bmi(bmi):
        """评测 BMI，返回 (级别, 建议, 颜色标识)"""
        if bmi <= 0:
            return None, None, None
        if bmi < 18.5:
            return '偏瘦', '建议增加营养摄入，适当进行力量训练。', 'warning'
        if bmi < 24:
            return '正常', '体重正常，请继续保持良好的饮食与运动习惯。', 'success'
        if bmi < 28:
            return '超重', '建议控制饮食总热量，增加有氧运动。', 'warning'
        return '肥胖', '建议在医生指导下制定减重计划，控制慢性病风险。', 'danger'

    @staticmethod
    def evaluate_blood_pressure(blood_pressure):
        """评测血压（如 120/80），返回 (级别, 建议, 颜色标识)"""
        if not blood_pressure:
            return None, None, None
        try:
            systolic, diastolic = map(int, blood_pressure.split('/'))
        except ValueError:
            return None, None, None

        if systolic < 90 or diastolic < 60:
            return '低血压', '建议增加饮水与盐分摄入，起身时注意防止眩晕。', 'warning'
        if systolic < 120 and diastolic < 80:
            return '正常', '血压正常，请继续保持。', 'success'
        if systolic < 130 or diastolic < 80:
            return '正常高值', '血压偏高趋势，建议清淡饮食、规律作息。', 'warning'
        if systolic < 140 or diastolic < 90:
            return '1级高血压', '建议低盐饮食，定期监测血压，必要时就医。', 'danger'
        return '2级及以上高血压', '建议尽快就医，规范降压治疗。', 'danger'

    @staticmethod
    def evaluate_blood_sugar(blood_sugar):
        """评测空腹血糖 (mmol/L)，返回 (级别, 建议, 颜色标识)"""
        if not blood_sugar:
            return None, None, None
        if blood_sugar < 3.9:
            return '低血糖', '建议及时补充糖分，排查诱因。', 'warning'
        if blood_sugar < 6.1:
            return '正常', '空腹血糖正常，请继续保持。', 'success'
        if blood_sugar < 7.0:
            return '空腹血糖受损', '处于糖尿病前期，建议控制饮食并复查。', 'warning'
        return '糖尿病可能', '建议尽快就医检查，规范治疗。', 'danger'

    @staticmethod
    def evaluate_heart_rate(heart_rate):
        """评测静息心率 (次/分)，返回 (级别, 建议, 颜色标识)"""
        if not heart_rate:
            return None, None, None
        if heart_rate < 60:
            return '心动过缓', '若无运动习惯，建议就医评估。', 'warning'
        if heart_rate <= 100:
            return '正常', '心率正常，请继续保持。', 'success'
        return '心动过速', '建议排查诱因（发热/情绪/咖啡因），必要时就医。', 'danger'

    @classmethod
    def full_assessment(cls, height, weight, blood_pressure, blood_sugar, heart_rate):
        """
        综合评测，返回结果字典：
        {
            'bmi': ..., 'bmi_level': ..., ...
            'overall': '良好/一般/需关注',
            'items': [ {name, value, level, advice, tag}, ... ]
        }
        """
        bmi = 0
        if height and weight and height > 0:
            bmi = round(weight / ((height / 100) ** 2), 1)

        evaluations = [
            ('BMI', bmi, cls.evaluate_bmi(bmi)),
            ('血压', blood_pressure, cls.evaluate_blood_pressure(blood_pressure)),
            ('空腹血糖', f"{blood_sugar} mmol/L" if blood_sugar else None,
             cls.evaluate_blood_sugar(blood_sugar)),
            ('静息心率', f"{heart_rate} 次/分" if heart_rate else None,
             cls.evaluate_heart_rate(heart_rate)),
        ]

        items = []
        levels = []
        for name, value, (level, advice, tag) in evaluations:
            if level is None:
                continue
            items.append({
                'name': name, 'value': value, 'level': level,
                'advice': advice, 'tag': tag,
            })
            levels.append(tag)

        # 综合评级：有 danger → 需关注；有 warning → 一般；否则 良好
        if 'danger' in levels:
            overall, overall_tag, overall_advice = '需关注', 'danger', '存在异常指标，建议尽快就医并定期复查。'
        elif 'warning' in levels:
            overall, overall_tag, overall_advice = '一般', 'warning', '部分指标处于临界状态，建议调整生活方式后复查。'
        elif levels:
            overall, overall_tag, overall_advice = '良好', 'success', '各项指标正常，请继续保持健康的生活方式。'
        else:
            overall, overall_tag, overall_advice = '无数据', 'secondary', '暂无可评测的指标数据。'

        return {
            'bmi': bmi,
            'overall': overall,
            'overall_tag': overall_tag,
            'overall_advice': overall_advice,
            'indicators': items,
        }
