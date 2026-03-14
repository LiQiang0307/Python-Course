'''
Author: LiQiang
Date: 2026-03-14 09:04:29
LastEditors: LiQiang
LastEditTime: 2026-03-14 09:04:33
Description: 文件描述
'''
# -*- coding: utf-8 -*-
"""
===============================================================================
模块名称：health_record_init.py
功能描述：东软风格个人健康档案初始化与BMI智能评估模块
应用场景：健康管理平台 - 用户建档子系统
作者：数字媒体技术专业学生 (模拟东软初级工程师)
日期：2026-03-14
版本：V1.0
===============================================================================
"""

def main():
    """主函数：执行健康档案录入与评估流程"""
    
    # --- 1. 系统欢迎与信息录入 (Input) ---
    print("=" * 50)
    print("欢迎使用东软健康档案管理系统的建档模块")
    print("=" * 50)
    
    # 使用有意义的标识符 (Snake_case 命名规范)
    patient_name = input("请输入受访者姓名：")
    # 模拟身份证号输入（后续课程可做验证，此处仅做字符串处理）
    patient_id = input("请输入身份证号后四位：") 
    
    # 数据类型转换：确保数值计算正确
    # 提示：身高通常以厘米为单位输入，计算时需转换为米
    height_cm = float(input("请输入身高 (cm): "))
    weight_kg = float(input("请输入体重 (kg): "))
    age = int(input("请输入年龄："))
    
    # --- 2. 核心业务逻辑处理 (Process) ---
    # 【知识点：运算符】BMI = 体重 (kg) / 身高 (m) 的平方
    height_m = height_cm / 100.0  # 单位换算
    bmi_value = weight_kg / (height_m ** 2)
    
    # 【知识点：变量作用与简单逻辑预备】
    # 注：复杂的 if-else 判断将在第二课组学习，此处仅做数值计算
    health_status = "待评估" # 初始化状态变量
    
    # 简单的字符串操作：生成档案编号
    archive_code = "NH-" + patient_id + "-2026" # "NH"代表 Neusoft Health
    
    # --- 3. 标准化报告输出 (Output) ---
    print("\n" + "-" * 50)
    print(f"【健康档案生成成功】档案编号：{archive_code}")
    print("-" * 50)
    
    # 【知识点：格式化输出 f-string】
    # 模拟医疗报表格式，保留两位小数
    print(f"姓名：{patient_name:<10} 年龄：{age} 岁")
    print(f"身高：{height_cm:.1f} cm\t体重：{weight_kg:.1f} kg")
    print(f"体质指数 (BMI): {bmi_value:.2f}")
    
    # 简单的健康建议展示（为后续流程控制做铺垫）
    print("-" * 50)
    print("系统初步建议：")
    print("数据已同步至东软健康云中心。")
    print("请等待专业医生结合临床数据进行详细解读。")
    print("=" * 50)

# 【知识点：工程化规范】程序入口判断
if __name__ == "__main__":
    try:
        main()
    except ValueError:
        print("\n[系统错误] 输入数据格式无效！请确保身高体重为数字。")
        print("提示：本模块将在第八课组学习完整的异常处理机制。")