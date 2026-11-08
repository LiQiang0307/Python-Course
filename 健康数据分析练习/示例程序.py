"""虚构健康数据练习。运行：python 示例程序.py"""
from pathlib import Path
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 无图形界面也可保存图片
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = Path(__file__).resolve().parent
SOURCE = BASE / '模拟健康数据.csv'
RESULT = BASE / '运行结果'
RESULT.mkdir(exist_ok=True)

# 任务 2：读取、检查、去重、填补缺失值。
df = pd.read_csv(SOURCE, encoding='utf-8-sig', parse_dates=['date'])
print('原始数据形状：', df.shape)
print('各列缺失值：\n', df.isna().sum().to_string())
print('完全重复行数：', df.duplicated().sum())
df = df.drop_duplicates().copy()
# 同一个 record_id 如果存在不同内容，不能随意保留一条，应先核对。
if df['record_id'].duplicated().any():
    raise ValueError('存在 record_id 相同但内容不同的记录，请先核对。')

numeric_columns = ['weight_kg', 'steps', 'sleep_hours', 'resting_heart_rate']
for col in numeric_columns:
    # 先用同一用户的中位数，若该用户全缺失，再用全体中位数。
    df[col] = df[col].fillna(df.groupby('user_id')[col].transform('median'))
    df[col] = df[col].fillna(df[col].median())
if df[numeric_columns].isna().any().any():
    raise ValueError('某个数值列全部缺失，无法使用中位数填补。')
df = df.sort_values(['user_id', 'date']).reset_index(drop=True)

# 任务 1：ndarray、dtype、shape、索引切片、向量化和广播。
height_m = df['height_cm'].to_numpy(dtype=float) / 100
weight = df['weight_kg'].to_numpy(dtype=float)
df['bmi'] = np.round(weight / height_m ** 2, 2)
print('\n身高数组 dtype、shape：', height_m.dtype, height_m.shape)
print('前 5 条 BMI：', df['bmi'].to_numpy()[:5])
# 与普通循环对照；运行时间随机器变化，结果是否相等才是重点。
start = time.perf_counter()
bmi_vector = weight / height_m ** 2
vector_time = time.perf_counter() - start
start = time.perf_counter()
bmi_loop = np.array([w / h ** 2 for w, h in zip(weight, height_m)])
loop_time = time.perf_counter() - start
print('向量化与循环结果一致：', np.allclose(bmi_vector, bmi_loop))
print(f'示例耗时：向量化 {vector_time:.6f}s，循环 {loop_time:.6f}s（仅供观察）')

steps = df['steps'].to_numpy(dtype=float)
# 左闭右开：低于 5000、5000 至不足 8000、8000 至不足 10000、10000 及以上。
labels = ['<5000', '5000-7999', '8000-9999', '>=10000']
counts = np.array([(steps < 5000).sum(), ((steps >= 5000) & (steps < 8000)).sum(),
                   ((steps >= 8000) & (steps < 10000)).sum(), (steps >= 10000).sum()])
print('步数区间记录数：', dict(zip(labels, counts.tolist())))
# 广播：每行是一次记录，每列依次为身高（米）、体重（千克）。
height_weight = np.column_stack((df['height_cm'].to_numpy(), weight)) * np.array([0.01, 1.0])
print('身高/体重矩阵形状及前两行：', height_weight.shape, '\n', height_weight[:2])
# 行是用户、列是日期；这是形状转换，不是对原始时间顺序直接 reshape。
step_matrix = df.pivot(index='user_id', columns='date', values='steps')
print('用户×日期的步数矩阵形状：', step_matrix.shape)

# pandas 选择、过滤、排序、分组、合并。
print('\n步数 >= 10000 的前 5 条：\n', df.loc[df['steps'] >= 10000,
      ['user_id', 'date', 'steps']].head().to_string(index=False))
by_terminal = df.groupby('terminal', as_index=False).agg(
    记录数=('record_id', 'size'), 平均步数=('steps', 'mean'),
    平均睡眠小时=('sleep_hours', 'mean'), 平均静息心率=('resting_heart_rate', 'mean'),
    平均BMI=('bmi', 'mean')).round(2).sort_values('平均步数', ascending=False)
by_day = df.groupby('date', as_index=False).agg(平均步数=('steps', 'mean'), 平均睡眠小时=('sleep_hours', 'mean'))
# 演示 merge：把每位用户的平均步数合并回用户基本资料。
users = df[['user_id', 'gender', 'age']].drop_duplicates('user_id')
user_steps = df.groupby('user_id', as_index=False)['steps'].mean().rename(columns={'steps': '平均步数'})
user_summary = users.merge(user_steps, on='user_id', validate='one_to_one')
print('\n按终端统计：\n', by_terminal.to_string(index=False))

df.to_csv(RESULT / '清洗后数据.csv', index=False, encoding='utf-8-sig')
by_terminal.to_csv(RESULT / '终端分组统计.csv', index=False, encoding='utf-8-sig')
user_summary.to_csv(RESULT / '用户平均步数.csv', index=False, encoding='utf-8-sig')
step_matrix.to_csv(RESULT / '用户日期步数矩阵.csv', encoding='utf-8-sig')
# 同一份清洗数据另存 JSON，并示范重新读取。
json_path = RESULT / '清洗后数据.json'
df.to_json(json_path, orient='records', force_ascii=False, date_format='iso', indent=2)
json_df = pd.read_json(json_path, orient='records')
print('JSON 读取行数：', len(json_df))

# 任务 3：折线图、柱状图、分布图、散点图；优先使用系统中的中文字体。
font_names = {f.name for f in font_manager.fontManager.ttflist}
font = next((f for f in ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
                         'SimHei', 'Noto Sans CJK SC', 'Arial Unicode MS'] if f in font_names), None)
if font:
    plt.rcParams['font.sans-serif'] = [font]
plt.rcParams['axes.unicode_minus'] = False
# 没有中文字体时使用英文标签，避免生成乱码图片。
cn = bool(font)
fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
a = axes[0, 0]
a.plot(by_day['date'], by_day['平均步数'], marker='o', label='平均步数' if cn else 'Mean steps')
a.set(title='每日平均步数趋势' if cn else 'Daily mean steps', xlabel='日期' if cn else 'Date', ylabel='步数' if cn else 'Steps')
a.tick_params(axis='x', rotation=40); a.legend(); a.grid(alpha=.25)
a = axes[0, 1]
terminal_labels = by_terminal['terminal'] if cn else by_terminal['terminal'].map({'手环':'Band', '手机':'Phone', '手表':'Watch'})
a.bar(terminal_labels, by_terminal['平均步数'], color=['#4c78a8', '#72b7b2', '#f58518'])
a.set(title='不同终端的平均步数' if cn else 'Mean steps by device', xlabel='终端' if cn else 'Device', ylabel='步数' if cn else 'Steps')
a = axes[1, 0]
a.hist(df['sleep_hours'], bins=12, color='#59a14f', edgecolor='white')
a.set(title='睡眠时长分布' if cn else 'Sleep duration distribution', xlabel='小时' if cn else 'Hours', ylabel='记录数' if cn else 'Records')
a = axes[1, 1]
a.scatter(df['sleep_hours'], df['resting_heart_rate'], alpha=.45, s=18, color='#b279a2')
a.set(title='睡眠与静息心率' if cn else 'Sleep and resting heart rate', xlabel='睡眠时长（小时）' if cn else 'Sleep (hours)', ylabel='静息心率（次/分钟）' if cn else 'Resting heart rate (bpm)')
fig.suptitle('模拟健康数据分析' if cn else 'Simulated health data analysis', fontsize=16)
fig.savefig(RESULT / '健康数据分析报告.png', dpi=180)
plt.close(fig)
print('\n分析完成，结果目录：', RESULT)
