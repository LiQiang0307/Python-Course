'''
Author: LiQiang
Date: 2026-03-14 08:43:26
LastEditors: LiQiang
LastEditTime: 2026-03-14 08:43:33
Description: 文件描述
'''
# -*- coding: utf-8 -*-
"""
模块名称：student_info_register.py
功能描述：学生基本信息登记与处理系统（基础版）
作者：数字媒体技术专业学生
日期：2026年3月14日
"""

def main():
    """主函数：程序入口"""
    
    # --- 1. 数据输入环节 (Input) ---
    # 提示：使用有意义的变量名，遵循蛇形命名法 (snake_case)
    print("=== 欢迎使用学生信息登记系统 ===")
    
    student_name = input("请输入学生姓名: ")
    student_id = input("请输入学号: ")
    student_age = int(input("请输入年龄: "))  # 类型转换：字符串转整型
    
    # 获取成绩并转换为浮点型
    score_regular = float(input("请输入平时成绩 (0-100): "))
    score_final = float(input("请输入期末成绩 (0-100): "))
    
    # --- 2. 数据处理环节 (Process) ---
    # 运算符应用：算术运算
    # 计算总评成绩，保留两位小数
    total_score = score_regular * 0.6 + score_final * 0.4
    
    # 字符串运算：拼接与格式化
    welcome_message = "你好，" + student_name + "！欢迎加入Python编程世界。"
    
    # --- 3. 数据输出环节 (Output) ---
    # 规范输出：使用f-string进行格式化，确保对齐美观
    print("\n=== 学生档案生成成功 ===")
    print(f"{welcome_message}")
    print("-" * 30)  # 使用乘法运算符生成分割线
    print(f"{'姓名':<10}{'学号':<15}{'年龄':<5}")
    print(f"{student_name:<10}{student_id:<15}{student_age:<5}")
    print("-" * 30)
    print(f"{'平时成绩':<10}{'期末成绩':<10}{'总评成绩':<10}")
    # 格式化浮点数，保留2位小数
    print(f"{score_regular:<10.2f}{score_final:<10.2f}{total_score:<10.2f}")
    print("-" * 30)

# 程序入口判断，体现工程化规范
if __name__ == "__main__":
    main()