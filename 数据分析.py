# 第一步：读取数据并查看基础信息
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False

# 读取CSV文件
file_path = '历史行情_2024-12-26_2025-12-26_600519.csv'
df = pd.read_csv(file_path)

# 查看数据基本信息
print("="*60)
print("1. 数据基本信息")
print("="*60)
print(f"数据时间范围：{df.shape[0]} 条记录")
print(f"数据列名：{list(df.columns)}")
print(f"\n数据前5行：")
print(df.head())

print(f"\n数据类型：")
print(df.dtypes)

print(f"\n数据缺失值统计：")
missing_info = df.isnull().sum()
missing_rate = (missing_info / len(df)) * 100
missing_df = pd.DataFrame({
    '缺失数量': missing_info,
    '缺失率(%)': missing_rate.round(2)
})
print(missing_df[missing_df['缺失数量'] > 0])

print(f"\n数据描述性统计：")
# 只对数值型列进行统计
numeric_cols = df.select_dtypes(include=[np.number]).columns
print(df[numeric_cols].describe())