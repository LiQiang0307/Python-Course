#!/usr/bin/env python3
"""
验证器测试脚本
测试正则表达式验证与数据清洗功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.validator import Validator

def test_validation_functions():
    """测试验证功能"""
    print("\n=== 测试验证功能 ===")
    
    # 测试用户名验证
    print("\n1. 测试用户名验证:")
    test_cases = [
        ("user123", True, ""),
        ("李强强", True, ""),
        ("u", False, "用户名长度必须在4-16位之间"),
        ("user1234567890123456", False, "用户名长度必须在4-16位之间"),
        ("user@123", False, "用户名只能包含字母、数字和中文"),
    ]
    
    for username, expected_valid, expected_msg in test_cases:
        is_valid, msg = Validator.validate_username(username)
        status = "✓" if is_valid == expected_valid and msg == expected_msg else "✗"
        print(f"  {status} 用户名: '{username}' -> 有效: {is_valid}, 消息: '{msg}'")
    
    # 测试手机号验证
    print("\n2. 测试手机号验证:")
    test_cases = [
        ("13812345678", True, ""),
        ("19912345678", True, ""),
        ("12345678901", False, "手机号格式不正确"),
        ("1381234567", False, "手机号必须是11位数字"),
        ("138123456789", False, "手机号必须是11位数字"),
        ("1381234567a", False, "手机号必须是11位数字"),
    ]
    
    for phone, expected_valid, expected_msg in test_cases:
        is_valid, msg = Validator.validate_phone(phone)
        status = "✓" if is_valid == expected_valid and msg == expected_msg else "✗"
        print(f"  {status} 手机号: '{phone}' -> 有效: {is_valid}, 消息: '{msg}'")
    
    # 测试邮箱验证
    print("\n3. 测试邮箱验证:")
    test_cases = [
        ("user@example.com", True, ""),
        ("user.name+tag@example.co.uk", True, ""),
        ("user@", False, "邮箱格式不正确"),
        ("@example.com", False, "邮箱格式不正确"),
        ("user@example", False, "邮箱格式不正确"),
    ]
    
    for email, expected_valid, expected_msg in test_cases:
        is_valid, msg = Validator.validate_email(email)
        status = "✓" if is_valid == expected_valid and msg == expected_msg else "✗"
        print(f"  {status} 邮箱: '{email}' -> 有效: {is_valid}, 消息: '{msg}'")
    
    # 测试日期验证
    print("\n4. 测试日期验证:")
    test_cases = [
        ("2026-04-03", True, ""),
        ("2026-04-31", True, ""),  # 格式正确，实际日期有效性不验证
        ("2026/04/03", False, "日期格式不正确，应为YYYY-MM-DD"),
        ("2026-4-3", False, "日期格式不正确，应为YYYY-MM-DD"),
        ("2026-04", False, "日期格式不正确，应为YYYY-MM-DD"),
    ]
    
    for date_str, expected_valid, expected_msg in test_cases:
        is_valid, msg = Validator.validate_date(date_str)
        status = "✓" if is_valid == expected_valid and msg == expected_msg else "✗"
        print(f"  {status} 日期: '{date_str}' -> 有效: {is_valid}, 消息: '{msg}'")
    
    # 测试血压验证
    print("\n5. 测试血压验证:")
    test_cases = [
        ("120/80", True, ""),
        ("90/60", True, ""),
        ("180/110", True, ""),
        ("12080", False, "血压格式不正确，应为收缩压/舒张压（如：120/80）"),
        ("120/80/", False, "血压格式不正确，应为收缩压/舒张压（如：120/80）"),
        ("50/80", False, "血压数值超出正常范围"),
        ("210/80", False, "血压数值超出正常范围"),
        ("120/30", False, "血压数值超出正常范围"),
        ("120/140", False, "血压数值超出正常范围"),
    ]
    
    for bp_str, expected_valid, expected_msg in test_cases:
        is_valid, msg = Validator.validate_blood_pressure(bp_str)
        status = "✓" if is_valid == expected_valid and msg == expected_msg else "✗"
        print(f"  {status} 血压: '{bp_str}' -> 有效: {is_valid}, 消息: '{msg}'")

def test_cleaning_functions():
    """测试数据清洗功能"""
    print("\n=== 测试数据清洗功能 ===")
    
    # 测试通用输入清洗
    print("\n1. 测试通用输入清洗:")
    test_cases = [
        ("  hello world  ", "hello world"),
        ("hello   world", "hello world"),
        ("  ", ""),
        (None, ""),
    ]
    
    for input_str, expected in test_cases:
        result = Validator.clean_input(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} 输入: '{input_str}' -> 清洗后: '{result}'")
    
    # 测试数值输入清洗
    print("\n2. 测试数值输入清洗:")
    test_cases = [
        ("123.45", "123.45"),
        ("  123.45  ", "123.45"),
        ("123a45", "12345"),
        ("123.45.67", "123.4567"),
        ("  ", ""),
        (None, ""),
    ]
    
    for input_str, expected in test_cases:
        result = Validator.clean_numeric_input(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} 输入: '{input_str}' -> 清洗后: '{result}'")
    
    # 测试手机号输入清洗
    print("\n3. 测试手机号输入清洗:")
    test_cases = [
        ("13812345678", "13812345678"),
        ("138-1234-5678", "13812345678"),
        ("+8613812345678", "8613812345678"),
        ("  13812345678  ", "13812345678"),
        ("  ", ""),
        (None, ""),
    ]
    
    for input_str, expected in test_cases:
        result = Validator.clean_phone_input(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} 输入: '{input_str}' -> 清洗后: '{result}'")
    
    # 测试邮箱输入清洗
    print("\n4. 测试邮箱输入清洗:")
    test_cases = [
        ("USER@EXAMPLE.COM", "user@example.com"),
        ("  user@example.com  ", "user@example.com"),
        ("user.name@example.com", "user.name@example.com"),
        ("  ", ""),
        (None, ""),
    ]
    
    for input_str, expected in test_cases:
        result = Validator.clean_email_input(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} 输入: '{input_str}' -> 清洗后: '{result}'")

def main():
    """主函数"""
    print("健康平台验证器测试")
    print("=" * 50)
    
    test_validation_functions()
    test_cleaning_functions()
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    main()
