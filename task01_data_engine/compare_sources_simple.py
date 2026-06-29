#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细对比 Tushare、Akshare、Yfinance 三个数据源的数据差异（简化版）
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

print('=' * 80)
print('详细数据对比：Tushare vs Akshare vs Yfinance（简化版）')
print('=' * 80)

# ============================================================================
# 1. 加载数据并标准化日期格式
# ============================================================================
print('\n1. 加载各数据源数据并标准化...')

# Tushare 数据
df_tushare = pd.read_csv('data/raw/510300_SH_daily_raw.csv')
df_tushare['trade_date'] = pd.to_datetime(df_tushare['trade_date'])
df_tushare['date_str'] = df_tushare['trade_date'].dt.strftime('%Y-%m-%d')
df_tushare = df_tushare.sort_values('trade_date', ascending=True).reset_index(drop=True)
print(f'  Tushare: {len(df_tushare)} 条记录')

# Akshare 未复权数据
df_ak_raw = pd.read_csv('data/multi_source/510300_akshare_raw.csv')
df_ak_raw['日期'] = pd.to_datetime(df_ak_raw['日期'])
df_ak_raw['date_str'] = df_ak_raw['日期'].dt.strftime('%Y-%m-%d')
df_ak_raw = df_ak_raw.sort_values('日期', ascending=True).reset_index(drop=True)
print(f'  Akshare (未复权): {len(df_ak_raw)} 条记录')

# Akshare 前复权数据
df_ak_qfq = pd.read_csv('data/multi_source/510300_akshare_qfq.csv')
df_ak_qfq['日期'] = pd.to_datetime(df_ak_qfq['日期'])
df_ak_qfq['date_str'] = df_ak_qfq['日期'].dt.strftime('%Y-%m-%d')
df_ak_qfq = df_ak_qfq.sort_values('日期', ascending=True).reset_index(drop=True)
print(f'  Akshare (前复权): {len(df_ak_qfq)} 条记录')

# Yfinance 数据
df_yf = pd.read_csv('data/multi_source/510300_yfinance_raw.csv')
df_yf['Date'] = pd.to_datetime(df_yf['Date'])
df_yf['date_str'] = df_yf['Date'].dt.strftime('%Y-%m-%d')
df_yf = df_yf.sort_values('Date', ascending=True).reset_index(drop=True)
print(f'  Yfinance: {len(df_yf)} 条记录')

# ============================================================================
# 2. 使用 merge 进行数据对齐
# ============================================================================
print('\n2. 使用 merge 进行数据对齐...')

# 以 Tushare 数据为基准，合并其他数据源
df_merge = df_tushare[['date_str', 'close', 'vol', 'amount']].copy()
df_merge = df_merge.rename(columns={
    'close': 'tushare_close',
    'vol': 'tushare_vol',
    'amount': 'tushare_amount'
})

# 合并 Akshare (未复权)
df_merge = df_merge.merge(
    df_ak_raw[['date_str', '收盘', '成交量', '成交额']],
    on='date_str',
    how='left'
)
df_merge = df_merge.rename(columns={
    '收盘': 'akshare_raw_close',
    '成交量': 'akshare_raw_vol',
    '成交额': 'akshare_raw_amount'
})

# 合并 Akshare (前复权)
df_merge = df_merge.merge(
    df_ak_qfq[['date_str', '收盘', '成交量', '成交额']],
    on='date_str',
    how='left'
)
df_merge = df_merge.rename(columns={
    '收盘': 'akshare_qfq_close',
    '成交量': 'akshare_qfq_vol',
    '成交额': 'akshare_qfq_amount'
})

# 合并 Yfinance
df_merge = df_merge.merge(
    df_yf[['date_str', 'Close', 'Volume']],
    on='date_str',
    how='left'
)
df_merge = df_merge.rename(columns={
    'Close': 'yfinance_close',
    'Volume': 'yfinance_volume'
})

print(f'  合并后记录数：{len(df_merge)} 条')

# ============================================================================
# 3. 数据完整性检查
# ============================================================================
print('\n3. 数据完整性检查...')

print(f'\n  Tushare 数据缺失：{df_merge["tushare_close"].isna().sum()} 条')
print(f'  Akshare (未复权) 数据缺失：{df_merge["akshare_raw_close"].isna().sum()} 条')
print(f'  Akshare (前复权) 数据缺失：{df_merge["akshare_qfq_close"].isna().sum()} 条')
print(f'  Yfinance 数据缺失：{df_merge["yfinance_close"].isna().sum()} 条')

# ============================================================================
# 4. 价格对比（收盘价）
# ============================================================================
print('\n' + '=' * 80)
print('4. 价格对比（收盘价）')
print('=' * 80)

# 仅对比三个数据源都有的日期
df_valid = df_merge.dropna(subset=['tushare_close', 'akshare_raw_close', 'yfinance_close'])

print(f'\n共同有效记录数：{len(df_valid)} 条')

if len(df_valid) > 0:
    # Tushare vs Akshare (未复权)
    diff_tu_ak = df_valid['tushare_close'] - df_valid['akshare_raw_close']
    print('\nTushare vs Akshare (未复权):')
    print(f'  平均差异：{diff_tu_ak.mean():.6f} 元')
    print(f'  最大差异：{diff_tu_ak.abs().max():.6f} 元')
    print(f'  最小差异：{diff_tu_ak.min():.6f} 元')
    print(f'  差异 > 0.01 元的交易日数：{(diff_tu_ak.abs() > 0.01).sum()}')
    
    # Tushare vs Yfinance
    diff_tu_yf = df_valid['tushare_close'] - df_valid['yfinance_close']
    print('\nTushare vs Yfinance:')
    print(f'  平均差异：{diff_tu_yf.mean():.6f} 元')
    print(f'  最大差异：{diff_tu_yf.abs().max():.6f} 元')
    print(f'  最小差异：{diff_tu_yf.min():.6f} 元')
    print(f'  差异 > 0.01 元的交易日数：{(diff_tu_yf.abs() > 0.01).sum()}')
    
    # Akshare (未复权) vs Yfinance
    diff_ak_yf = df_valid['akshare_raw_close'] - df_valid['yfinance_close']
    print('\nAkshare (未复权) vs Yfinance:')
    print(f'  平均差异：{diff_ak_yf.mean():.6f} 元')
    print(f'  最大差异：{diff_ak_yf.abs().max():.6f} 元')
    print(f'  最小差异：{diff_ak_yf.min():.6f} 元')
    print(f'  差异 > 0.01 元的交易日数：{(diff_ak_yf.abs() > 0.01).sum()}')
    
    # Akshare 未复权 vs 前复权
    diff_ak_raw_qfq = df_valid['akshare_raw_close'] - df_valid['akshare_qfq_close']
    print('\nAkshare 未复权 vs 前复权:')
    print(f'  平均差异：{diff_ak_raw_qfq.mean():.6f} 元')
    print(f'  最大差异：{diff_ak_raw_qfq.abs().max():.6f} 元')
    print(f'  最小差异：{diff_ak_raw_qfq.min():.6f} 元')

# ============================================================================
# 5. 找出差异较大的记录
# ============================================================================
print('\n' + '=' * 80)
print('5. 差异较大的记录（|差异| > 0.01 元）')
print('=' * 80)

if len(df_valid) > 0:
    # Tushare vs Akshare
    idx_tu_ak = (diff_tu_ak.abs() > 0.01)
    if idx_tu_ak.sum() > 0:
        print('\nTushare vs Akshare (未复权):')
        print(df_valid[idx_tu_ak][['date_str', 'tushare_close', 'akshare_raw_close']].head(10))
    
    # Tushare vs Yfinance
    idx_tu_yf = (diff_tu_yf.abs() > 0.01)
    if idx_tu_yf.sum() > 0:
        print('\nTushare vs Yfinance:')
        print(df_valid[idx_tu_yf][['date_str', 'tushare_close', 'yfinance_close']].head(10))
    
    # Akshare 未复权 vs 前复权
    idx_ak = (diff_ak_raw_qfq.abs() > 0.01)
    if idx_ak.sum() > 0:
        print('\nAkshare 未复权 vs 前复权:')
        print(df_valid[idx_ak][['date_str', 'akshare_raw_close', 'akshare_qfq_close']].head(10))

# ============================================================================
# 6. 保存对比结果
# ============================================================================
print('\n' + '=' * 80)
print('6. 保存对比结果')
print('=' * 80)

# 保存合并后的数据
df_merge.to_csv('data/multi_source/merged_comparison.csv', index=False, encoding='utf-8-sig')
print(f'✓ 合并数据已保存至：data/multi_source/merged_comparison.csv')

# 生成汇总报告
report = {
    'comparison_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_records': len(df_merge),
    'valid_records': len(df_valid),
    'missing_data': {
        'tushare': int(df_merge['tushare_close'].isna().sum()),
        'akshare_raw': int(df_merge['akshare_raw_close'].isna().sum()),
        'akshare_qfq': int(df_merge['akshare_qfq_close'].isna().sum()),
        'yfinance': int(df_merge['yfinance_close'].isna().sum())
    }
}

if len(df_valid) > 0:
    report['price_differences'] = {
        'tushare_vs_akshare': {
            'mean': float(diff_tu_ak.mean()),
            'max_abs': float(diff_tu_ak.abs().max()),
            'count_gt_001': int((diff_tu_ak.abs() > 0.01).sum())
        },
        'tushare_vs_yfinance': {
            'mean': float(diff_tu_yf.mean()),
            'max_abs': float(diff_tu_yf.abs().max()),
            'count_gt_001': int((diff_tu_yf.abs() > 0.01).sum())
        },
        'akshare_raw_vs_yfinance': {
            'mean': float(diff_ak_yf.mean()),
            'max_abs': float(diff_ak_yf.abs().max()),
            'count_gt_001': int((diff_ak_yf.abs() > 0.01).sum())
        },
        'akshare_raw_vs_qfq': {
            'mean': float(diff_ak_raw_qfq.mean()),
            'max_abs': float(diff_ak_raw_qfq.abs().max()),
            'count_gt_001': int((diff_ak_raw_qfq.abs() > 0.01).sum())
        }
    }

# 保存报告
with open('data/multi_source/final_comparison_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'✓ 汇总报告已保存至：data/multi_source/final_comparison_report.json')

# ============================================================================
# 7. 打印总结
# ============================================================================
print('\n' + '=' * 80)
print('对比总结')
print('=' * 80)

print('\n✅ 数据获取成功：')
print(f'  - Tushare: {len(df_tushare)} 条')
print(f'  - Akshare (未复权): {len(df_ak_raw)} 条')
print(f'  - Akshare (前复权): {len(df_ak_qfq)} 条')
print(f'  - Yfinance: {len(df_yf)} 条')

print('\n✅ 数据对齐成功：')
print(f'  - 合并后记录数：{len(df_merge)} 条')
print(f'  - 三个数据源都有效的记录数：{len(df_valid)} 条')

if len(df_valid) > 0:
    print('\n⚠️ 价格差异：')
    print(f'  - Tushare vs Akshare (未复权): 平均差异 {diff_tu_ak.mean():.6f} 元')
    print(f'  - Tushare vs Yfinance: 平均差异 {diff_tu_yf.mean():.6f} 元')
    print(f'  - Akshare (未复权) vs 前复权: 平均差异 {diff_ak_raw_qfq.mean():.6f} 元')

print('\n' + '=' * 80)
print('详细对比完成')
print('=' * 80)
print(f'\n输出文件：')
print(f'  1. data/multi_source/merged_comparison.csv - 合并对比数据')
print(f'  2. data/multi_source/final_comparison_report.json - 汇总报告')
