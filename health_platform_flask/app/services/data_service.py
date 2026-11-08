"""
数据服务模块
迁移自原 health_platform/services/data_service.py
"""
import re
from datetime import datetime

from ..models import PhysicalExamRecord, MedicationRecord, HealthRecord, Report
from ..utils import FileHandler, Logger, Validator


class DataService:
    """数据服务类"""

    def __init__(self, app_config):
        self.config = app_config
        self.records_file = app_config['RECORDS_FILE']
        self.file_handler = FileHandler()
        self.logger = Logger(app_config['LOG_DIR'])

    def _load_records(self):
        return FileHandler.read_json(self.records_file)

    def _save_records(self, records_data):
        return FileHandler.write_json(self.records_file, records_data)

    # ---------- 记录增查 ----------
    def add_record(self, user_id, record_type, record_date, value='', **kwargs):
        """添加健康记录，返回 (success, message, record)"""
        is_valid, msg = Validator.validate_date(record_date)
        if not is_valid:
            return False, msg, None

        records_data = self._load_records()
        record_id = f"R{len(records_data) + 1:04d}"

        if record_type == '体检':
            record = PhysicalExamRecord(
                record_id=record_id, user_id=user_id, record_date=record_date,
                height=kwargs.get('height', 0), weight=kwargs.get('weight', 0),
                blood_pressure=kwargs.get('blood_pressure', ''),
                blood_sugar=kwargs.get('blood_sugar', 0),
                heart_rate=kwargs.get('heart_rate', 0),
                notes=kwargs.get('notes', ''),
            )
        elif record_type == '用药':
            record = MedicationRecord(
                record_id=record_id, user_id=user_id, record_date=record_date,
                medicine_name=kwargs.get('medicine_name', ''),
                dosage=kwargs.get('dosage', ''),
                frequency=kwargs.get('frequency', ''),
                duration_days=kwargs.get('duration_days', 0),
                notes=kwargs.get('notes', ''),
            )
        else:
            record = HealthRecord(
                record_id=record_id, user_id=user_id, record_type=record_type,
                record_date=record_date, value=value,
                unit=kwargs.get('unit', ''), notes=kwargs.get('notes', ''),
            )

        records_data.append(record.to_dict())
        if self._save_records(records_data):
            self.logger.info(f"添加记录成功: {record_id}")
            return True, f"记录添加成功！记录ID: {record_id}", record
        return False, "保存记录失败", None

    def get_user_records(self, user_id, record_type=None):
        """获取用户记录，按日期倒序"""
        records_data = self._load_records()
        user_records = [r for r in records_data if r['user_id'] == user_id]
        if record_type:
            user_records = [r for r in user_records if r['record_type'] == record_type]
        user_records.sort(key=lambda x: x['record_date'], reverse=True)
        return user_records

    def get_record(self, record_id, user_id=None):
        """按记录 ID 获取单条记录"""
        for record in self._load_records():
            if record['record_id'] == record_id:
                if user_id and record['user_id'] != user_id:
                    return None
                return record
        return None

    def delete_record(self, record_id, user_id):
        """删除记录，返回 (success, message)"""
        records_data = self._load_records()
        for i, record in enumerate(records_data):
            if record['record_id'] == record_id and record['user_id'] == user_id:
                records_data.pop(i)
                if self._save_records(records_data):
                    return True, "删除成功"
                return False, "删除失败"
        return False, "记录不存在"

    # ---------- 统计 ----------
    def get_statistics(self, user_id, record_type=None):
        """获取统计值"""
        records = self.get_user_records(user_id, record_type)
        if not records:
            return None

        values = []
        for record in records:
            try:
                if isinstance(record['value'], (int, float)):
                    values.append(float(record['value']))
                elif isinstance(record['value'], str):
                    numbers = re.findall(r'\d+\.?\d*', record['value'])
                    values.extend(float(n) for n in numbers)
            except (ValueError, TypeError):
                continue

        return {
            'record_type': record_type or '全部',
            'count': len(records),
            'min': min(values) if values else None,
            'max': max(values) if values else None,
            'avg': round(sum(values) / len(values), 2) if values else None,
        }

    # ---------- 导出 / 备份 / 报告 ----------
    def export_to_csv(self, user_id):
        """导出用户记录到 CSV，返回 (success, message, filepath)"""
        records = self.get_user_records(user_id)
        if not records:
            return False, "无记录可导出", None
        filepath = f"health_records_{user_id}.csv"
        if self.file_handler.write_csv(filepath, records):
            self.logger.info(f"导出CSV成功: {filepath}")
            return True, f"导出成功: {filepath}", filepath
        return False, "导出失败", None

    def backup_data(self):
        """备份数据，返回备份路径"""
        path = self.file_handler.backup_file(self.records_file, self.config['BACKUP_DIR'])
        if path:
            self.logger.info(f"数据备份成功: {path}")
        return path

    def generate_report(self, user_id, username):
        """生成健康报告，返回 (report, message)"""
        records = self.get_user_records(user_id)
        if not records:
            return None, "无记录可生成报告"

        record_types = {}
        for record in records:
            rtype = record['record_type']
            record_types[rtype] = record_types.get(rtype, 0) + 1

        content = (
            f"用户健康报告\n{'=' * 60}\n"
            f"用户ID: {user_id}\n用户名: {username}\n"
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"记录统计:\n{'-' * 60}\n总记录数: {len(records)}\n按类型统计:\n"
        )
        for rtype, count in record_types.items():
            content += f"  {rtype}: {count}条\n"

        content += f"\n最新记录:\n{'-' * 60}\n"
        for record in records[:5]:
            content += f"  [{record['record_date']}] {record['record_type']}: {record['value']}\n"

        report_id = f"RP{len(records):04d}"
        report = Report(report_id, user_id, f"{username}的健康报告", content)

        filename = f"report_{user_id}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = f"{self.config['REPORTS_DIR']}/{filename}"
        if report.save_to_file(filepath):
            self.logger.info(f"生成报告成功: {filepath}")
            return report, f"报告生成成功: {filepath}"
        return None, "保存报告失败"
