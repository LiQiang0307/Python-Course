"""
数据服务模块
单元3：序列数据操作
单元5：模块化开发
单元8：文件操作
"""
from models.health_record import HealthRecord, PhysicalExamRecord, MedicationRecord
from models.report import Report
from utils.file_handler import FileHandler
from utils.logger import Logger
import config
from datetime import datetime

class DataService:
    """数据服务类"""
    
    def __init__(self):
        """初始化数据服务"""
        self.records_file = config.RECORDS_FILE
        self.file_handler = FileHandler()
        self.logger = Logger()
    
    def add_record(self, user_id, record_type, record_date, value, **kwargs):
        """添加健康记录"""
        # 验证日期格式
        from utils.validator import Validator
        is_valid, msg = Validator.validate_date(record_date)
        if not is_valid:
            return False, msg
        
        records_data = self.file_handler.read_json(self.records_file)
        
        # 生成记录ID
        record_id = f"R{len(records_data) + 1:04d}"
        
        # 创建记录对象
        if record_type == '体检':
            record = PhysicalExamRecord(
                record_id=record_id,
                user_id=user_id,
                record_date=record_date,
                height=kwargs.get('height', 0),
                weight=kwargs.get('weight', 0),
                blood_pressure=kwargs.get('blood_pressure', ''),
                blood_sugar=kwargs.get('blood_sugar', 0),
                heart_rate=kwargs.get('heart_rate', 0),
                notes=kwargs.get('notes', '')
            )
        elif record_type == '用药':
            record = MedicationRecord(
                record_id=record_id,
                user_id=user_id,
                record_date=record_date,
                medicine_name=kwargs.get('medicine_name', ''),
                dosage=kwargs.get('dosage', ''),
                frequency=kwargs.get('frequency', ''),
                duration_days=kwargs.get('duration_days', 0),
                notes=kwargs.get('notes', '')
            )
        else:
            record = HealthRecord(
                record_id=record_id,
                user_id=user_id,
                record_type=record_type,
                record_date=record_date,
                value=value,
                unit=kwargs.get('unit', ''),
                notes=kwargs.get('notes', '')
            )
        
        records_data.append(record.to_dict())
        
        if self.file_handler.write_json(self.records_file, records_data):
            self.logger.info(f"添加记录成功: {record_id}")
            return True, f"记录添加成功！记录ID: {record_id}"
        else:
            return False, "保存记录失败"
    
    def get_user_records(self, user_id, record_type=None):
        """获取用户记录"""
        records_data = self.file_handler.read_json(self.records_file)
        
        # 筛选用户记录
        user_records = [r for r in records_data if r['user_id'] == user_id]
        
        # 按类型筛选
        if record_type:
            user_records = [r for r in user_records if r['record_type'] == record_type]
        
        # 按日期排序
        user_records.sort(key=lambda x: x['record_date'], reverse=True)
        
        return user_records
    
    def get_statistics(self, user_id, record_type):
        """获取统计数据"""
        records = self.get_user_records(user_id, record_type)
        
        if not records:
            return None
        
        # 计算统计值
        values = []
        for record in records:
            try:
                if isinstance(record['value'], (int, float)):
                    values.append(float(record['value']))
                elif isinstance(record['value'], str):
                    # 尝试从字符串中提取数值
                    import re
                    numbers = re.findall(r'\d+\.?\d*', record['value'])
                    if numbers:
                        values.extend([float(n) for n in numbers])
            except (ValueError, TypeError):
                continue
        
        if not values:
            return {
                'count': len(records),
                'message': '无数值数据可统计'
            }
        
        return {
            'count': len(records),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None
        }
    
    def export_to_csv(self, user_id, filepath):
        """导出用户记录到CSV"""
        records = self.get_user_records(user_id)
        
        if not records:
            return False, "无记录可导出"
        
        if self.file_handler.write_csv(filepath, records):
            self.logger.info(f"导出CSV成功: {filepath}")
            return True, f"导出成功: {filepath}"
        else:
            return False, "导出失败"
    
    def backup_data(self):
        """备份数据"""
        return self.file_handler.backup_file(
            self.records_file,
            config.DATA_DIR
        )
    
    def generate_report(self, user_id, username):
        """生成健康报告"""
        records = self.get_user_records(user_id)
        
        if not records:
            return None, "无记录可生成报告"
        
        # 统计各类记录
        record_types = {}
        for record in records:
            rtype = record['record_type']
            record_types[rtype] = record_types.get(rtype, 0) + 1
        
        # 生成报告内容
        content = f"""
用户健康报告
{'='*60}
用户ID: {user_id}
用户名: {username}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

记录统计:
{'-'*60}
总记录数: {len(records)}

按类型统计:
"""
        for rtype, count in record_types.items():
            content += f"  {rtype}: {count}条\n"
        
        # 添加最新记录
        content += f"\n最新记录:\n{'-'*60}\n"
        for record in records[:5]:
            content += f"  [{record['record_date']}] {record['record_type']}: {record['value']}\n"
        
        # 创建报告对象
        report_id = f"RP{len(records):04d}"
        report = Report(report_id, user_id, f"{username}的健康报告", content)
        
        # 保存报告
        report_filename = f"report_{user_id}_{datetime.now().strftime('%Y%m%d')}.txt"
        report_filepath = f"{config.REPORTS_DIR}/{report_filename}"
        
        if report.save_to_file(report_filepath):
            self.logger.info(f"生成报告成功: {report_filepath}")
            return report, f"报告生成成功: {report_filepath}"
        else:
            return None, "保存报告失败"