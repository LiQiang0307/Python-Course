"""
主程序入口
综合应用所有单元知识
"""
import os
import sys
from services.auth_service import AuthService
from services.data_service import DataService
from utils.logger import Logger
import config

class HealthPlatform:
    """健康数据管理平台主类"""
    
    def __init__(self):
        """初始化平台"""
        config.init_directories()
        self.auth_service = AuthService()
        self.data_service = DataService()
        self.logger = Logger()
        self.running = True
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_menu(self):
        """打印主菜单"""
        print("\n" + "="*60)
        print(f"  {config.APP_CONFIG['app_name']} v{config.APP_CONFIG['version']}")
        print("="*60)
        print("1. 用户注册")
        print("2. 用户登录")
        print("3. 退出系统")
        print("="*60)
    
    def print_main_menu(self):
        """打印主功能菜单"""
        print("\n" + "="*60)
        print("  主菜单")
        print("="*60)
        print("1. 添加健康记录")
        print("2. 查看健康记录")
        print("3. 查看统计数据")
        print("4. 导出记录到CSV")
        print("5. 生成健康报告")
        print("6. 备份数据")
        print("7. 用户登出")
        print("0. 退出系统")
        print("="*60)
    
    def register(self):
        """用户注册功能"""
        print("\n--- 用户注册 ---")
        username = input("请输入用户名（4-16位）: ").strip()
        password = input("请输入密码（至少6位，含数字和字母）: ").strip()
        phone = input("请输入手机号（可选）: ").strip()
        email = input("请输入邮箱（可选）: ").strip()
        
        success, message = self.auth_service.register(
            username=username,
            password=password,
            phone=phone,
            email=email
        )
        
        print(f"\n{'✓' if success else '✗'} {message}")
        input("\n按回车键继续...")
    
    def login(self):
        """用户登录功能"""
        print("\n--- 用户登录 ---")
        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
        
        success, message = self.auth_service.login(username, password)
        
        print(f"\n{'✓' if success else '✗'} {message}")
        input("\n按回车键继续...")
        
        if success:
            self.main_loop()
    
    def add_record(self):
        """添加健康记录"""
        print("\n--- 添加健康记录 ---")
        print("1. 体检记录")
        print("2. 用药记录")
        print("3. 其他记录")
        
        choice = input("请选择记录类型（1-3）: ").strip()
        
        user = self.auth_service.get_current_user()
        record_date = input("请输入日期（YYYY-MM-DD）: ").strip()
        
        if choice == '1':
            # 体检记录
            height = float(input("身高（cm）: ") or 0)
            weight = float(input("体重（kg）: ") or 0)
            blood_pressure = input("血压（如：120/80）: ").strip()
            blood_sugar = float(input("血糖（mmol/L）: ") or 0)
            heart_rate = int(input("心率（次/分）: ") or 0)
            
            success, message = self.data_service.add_record(
                user_id=user.user_id,
                record_type='体检',
                record_date=record_date,
                value=f"BP:{blood_pressure}, BS:{blood_sugar}",
                height=height,
                weight=weight,
                blood_pressure=blood_pressure,
                blood_sugar=blood_sugar,
                heart_rate=heart_rate
            )
        
        elif choice == '2':
            # 用药记录
            medicine_name = input("药品名称: ").strip()
            dosage = input("剂量: ").strip()
            frequency = input("频次（如：每日3次）: ").strip()
            duration_days = int(input("用药天数: ") or 0)
            
            success, message = self.data_service.add_record(
                user_id=user.user_id,
                record_type='用药',
                record_date=record_date,
                value=f"{dosage} {frequency}",
                medicine_name=medicine_name,
                dosage=dosage,
                frequency=frequency,
                duration_days=duration_days
            )
        
        else:
            # 其他记录
            record_type = input("记录类型: ").strip()
            value = input("数值/内容: ").strip()
            unit = input("单位（可选）: ").strip()
            
            success, message = self.data_service.add_record(
                user_id=user.user_id,
                record_type=record_type,
                record_date=record_date,
                value=value,
                unit=unit
            )
        
        print(f"\n{'✓' if success else '✗'} {message}")
        input("\n按回车键继续...")
    
    def view_records(self):
        """查看健康记录"""
        print("\n--- 查看健康记录 ---")
        user = self.auth_service.get_current_user()
        
        print("1. 全部记录")
        print("2. 体检记录")
        print("3. 用药记录")
        
        choice = input("请选择（1-3）: ").strip()
        
        if choice == '1':
            records = self.data_service.get_user_records(user.user_id)
        elif choice == '2':
            records = self.data_service.get_user_records(user.user_id, '体检')
        elif choice == '3':
            records = self.data_service.get_user_records(user.user_id, '用药')
        else:
            records = []
        
        if not records:
            print("\n暂无记录")
        else:
            print(f"\n找到 {len(records)} 条记录:\n")
            print("-"*60)
            for i, record in enumerate(records, 1):
                print(f"{i}. [{record['record_date']}] {record['record_type']}")
                print(f"   数值: {record['value']} {record.get('unit', '')}")
                if record.get('notes'):
                    print(f"   备注: {record['notes']}")
                print()
        
        input("按回车键继续...")
    
    def view_statistics(self):
        """查看统计数据"""
        print("\n--- 查看统计数据 ---")
        user = self.auth_service.get_current_user()
        
        print("1. 体检统计")
        print("2. 用药统计")
        
        choice = input("请选择（1-2）: ").strip()
        record_type = '体检' if choice == '1' else '用药'
        
        stats = self.data_service.get_statistics(user.user_id, record_type)
        
        if stats:
            print(f"\n{record_type}统计:")
            print("-"*40)
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("\n暂无统计数据")
        
        input("\n按回车键继续...")
    
    def export_records(self):
        """导出记录"""
        print("\n--- 导出记录到CSV ---")
        user = self.auth_service.get_current_user()
        
        filename = f"health_records_{user.user_id}.csv"
        success, message = self.data_service.export_to_csv(user.user_id, filename)
        
        print(f"\n{'✓' if success else '✗'} {message}")
        input("\n按回车键继续...")
    
    def generate_report(self):
        """生成报告"""
        print("\n--- 生成健康报告 ---")
        user = self.auth_service.get_current_user()
        
        report, message = self.data_service.generate_report(
            user.user_id,
            user.username
        )
        
        print(f"\n{'✓' if report else '✗'} {message}")
        input("\n按回车键继续...")
    
    def backup_data(self):
        """备份数据"""
        print("\n--- 备份数据 ---")
        success = self.data_service.backup_data()
        print(f"\n{'✓' if success else '✗'} 备份{'成功' if success else '失败'}")
        input("\n按回车键继续...")
    
    def main_loop(self):
        """主功能循环"""
        while self.running and self.auth_service.is_logged_in():
            self.clear_screen()
            user = self.auth_service.get_current_user()
            print(f"\n当前用户: {user.username} ({user.role})")
            
            self.print_main_menu()
            choice = input("请选择功能（0-7）: ").strip()
            
            if choice == '1':
                self.add_record()
            elif choice == '2':
                self.view_records()
            elif choice == '3':
                self.view_statistics()
            elif choice == '4':
                self.export_records()
            elif choice == '5':
                self.generate_report()
            elif choice == '6':
                self.backup_data()
            elif choice == '7':
                self.auth_service.logout()
                break
            elif choice == '0':
                self.running = False
                print("\n感谢使用，再见！")
            else:
                print("\n✗ 无效选择，请重新输入")
                input("按回车键继续...")
    
    def run(self):
        """运行平台"""
        self.logger.info("平台启动")
        
        while self.running:
            self.clear_screen()
            self.print_menu()
            
            choice = input("请选择功能（1-3）: ").strip()
            
            if choice == '1':
                self.register()
            elif choice == '2':
                self.login()
            elif choice == '3':
                self.running = False
                print("\n感谢使用东软健康数据管理平台，再见！")
                self.logger.info("平台关闭")
            else:
                print("\n✗ 无效选择，请重新输入")
                input("按回车键继续...")


def main():
    """主函数"""
    platform = HealthPlatform()
    platform.run()


if __name__ == '__main__':
    main()