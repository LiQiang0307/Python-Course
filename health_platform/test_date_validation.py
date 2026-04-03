#!/usr/bin/env python3
"""
日期验证测试脚本
测试添加健康记录时的日期验证功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.data_service import DataService

def test_date_validation():
    """测试日期验证功能"""
    print("测试日期验证功能")
    print("=" * 50)
    
    data_service = DataService()
    
    # 测试用例
    test_cases = [
        # 有效日期
        ("2026-04-03", True, "记录添加成功"),
        ("2026-01-01", True, "记录添加成功"),
        ("2026-12-31", True, "记录添加成功"),
        # 无效日期格式
        ("2026/04/03", False, "日期格式不正确"),
        ("2026-4-3", False, "日期格式不正确"),
        ("2026-04", False, "日期格式不正确"),
        ("2026", False, "日期格式不正确"),
        ("04-03-2026", False, "日期格式不正确"),
        ("2026-04-03 12:00", False, "日期格式不正确"),
        ("", False, "日期格式不正确"),
    ]
    
    for date_str, expected_valid, expected_msg in test_cases:
        # 调用 add_record 方法
        success, message = data_service.add_record(
            user_id="U0001",
            record_type="其他",
            record_date=date_str,
            value="测试值"
        )
        
        # 检查结果
        status = "✓" if success == expected_valid and expected_msg in message else "✗"
        print(f"  {status} 日期: '{date_str}' -> 成功: {success}, 消息: '{message}'")

def main():
    """主函数"""
    test_date_validation()
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()
