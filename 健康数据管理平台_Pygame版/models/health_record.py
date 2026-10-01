"""
健康记录类
单元6-7：类与对象设计模式、继承
"""
from datetime import datetime

class HealthRecord:
    """健康记录基类"""
    
    def __init__(self, record_id, user_id, record_type, record_date, value, unit='', notes=''):
        """初始化健康记录"""
        self.record_id = record_id
        self.user_id = user_id
        self.record_type = record_type
        self.record_date = record_date
        self.value = value
        self.unit = unit
        self.notes = notes
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'record_type': self.record_type,
            'record_date': self.record_date,
            'value': self.value,
            'unit': self.unit,
            'notes': self.notes,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            record_id=data['record_id'],
            user_id=data['user_id'],
            record_type=data['record_type'],
            record_date=data['record_date'],
            value=data['value'],
            unit=data.get('unit', ''),
            notes=data.get('notes', '')
        )
    
    def __str__(self):
        """字符串表示"""
        return f"{self.record_type}: {self.value} {self.unit} ({self.record_date})"


class PhysicalExamRecord(HealthRecord):
    """体检记录（继承HealthRecord）"""
    
    def __init__(self, record_id, user_id, record_date, height, weight, blood_pressure, 
                 blood_sugar, heart_rate, notes=''):
        """初始化体检记录"""
        super().__init__(record_id, user_id, '体检', record_date, 
                        f"BP:{blood_pressure}, BS:{blood_sugar}", '', notes)
        self.height = height
        self.weight = weight
        self.blood_pressure = blood_pressure
        self.blood_sugar = blood_sugar
        self.heart_rate = heart_rate
    
    def calculate_bmi(self):
        """计算BMI"""
        if self.height > 0:
            return self.weight / ((self.height / 100) ** 2)
        return 0
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'height': self.height,
            'weight': self.weight,
            'blood_pressure': self.blood_pressure,
            'blood_sugar': self.blood_sugar,
            'heart_rate': self.heart_rate,
            'bmi': self.calculate_bmi()
        })
        return data


class MedicationRecord(HealthRecord):
    """用药记录（继承HealthRecord）"""
    
    def __init__(self, record_id, user_id, record_date, medicine_name, dosage, 
                 frequency, duration_days, notes=''):
        """初始化用药记录"""
        super().__init__(record_id, user_id, '用药', record_date, 
                        f"{dosage} {frequency}", '', notes)
        self.medicine_name = medicine_name
        self.dosage = dosage
        self.frequency = frequency
        self.duration_days = duration_days
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'medicine_name': self.medicine_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration_days': self.duration_days
        })
        return data