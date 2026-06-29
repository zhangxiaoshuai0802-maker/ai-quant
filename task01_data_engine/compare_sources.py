#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细对比 Tushare、Akshare、Yfinance 三个数据源的数据差异
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

print('=' * 80)
print('详细数据对比：Tushare vs Akshare vs Yfinance')
print('=' * 80)

# ============================================================================
# 1. 加载数据
# ============================================================================
print('\n1. 加载各数据源数据...')

# Tushare 数据
df_tushare = pd.read_csv('data/raw/510300_SH_daily_raw.csv')
df_tushare['trade_date'] = pd.to_datetime(df_tushare['trade_date'])
df_tushare = df_tushare.sort_values('trade_date', ascending=True).reset_index(drop=True)
print(f'  Tushare: {len(df_tushare)} 条记录')

# Akshare 未复权数据
df_ak_raw = pd.read_csv('data/multi_source/510300_akshare_raw.csv')
df_ak_raw['日期'] = pd.to_datetime(df_ak_raw['日期'])
df_ak_raw = df_ak_raw.sort_values('日期', ascending=True).reset_index(drop=True)
print(f'  Akshare (未复权): {len(df_ak_raw)} 条记录')

# Akshare 前复权数据
df_ak_qfq = pd.read_csv('data/multi_source/510300_akshare_qfq.csv')
df_ak_qfq['日期'] = pd.to_datetime(df_ak_qfq['日期'])
df_ak_qfq = df_ak_qfq.sort_values('日期', ascending=True).reset_index(drop=True)
print(f'  Akshare (前复权): {len(df_ak_qfq)} 条记录')

# Yfinance 数据
df_yf = pd.read_csv('data/multi_source/510300_yfinance_raw.csv', index_col=0)
df_yf.index = pd.to_datetime(df_yf.index)
df_yf = df_yf.sort_index(ascending=True).reset_index()
df_yf = df_yf.rename(columns={'index': 'Date'})
print(f'  Yfinance: {len(df_yf)} 条记录')

# ============================================================================
# 2. 字段映射
# ============================================================================
print('\n2. 字段映射...')

field_mapping = {
    'tushare': {
        'date': 'trade_date',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'vol',
        'amount': 'amount',
        'pre_close': 'pre_close',
        'change': 'change',
        'pct_chg': 'pct_chg'
    },
    'akshare_raw': {
        'date': '日期',
        'open': '开盘',
        'high': '最高',
        'low': '最低',
        'close': '收盘',
        'volume': '成交量',
        'amount': '成交额',
        'pct_chg': '涨跌幅'
    },
    'akshare_qfq': {
        'date': '日期',
        'open': '开盘',
        'high': '最高',
        'low': '最低',
        'close': '收盘',
        'volume': '成交量',
        'amount': '成交额'
    },
    'yfinance': {
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'amount': None  # Yfinance 没有成交额
    }
}

print('  字段映射完成')

# ============================================================================
# 3. 数据对齐（按日期）
# ============================================================================
print('\n3. 数据对齐（按日期）...')

# 获取所有数据源的日期集合
dates_tushare = set(df_tushare['trade_date'].dt.date)
dates_ak = set(df_ak_raw['日期'].dt.date)
dates_yf = set(df_yf['Date'].dt.date)

print(f'  Tushare 日期范围：{min(dates_tushare)} 至 {max(dates_tushare)}')
print(f'  Akshare 日期范围：{min(dates_ak)} 至 {max(dates_ak)}')
print(f'  Yfinance 日期范围：{min(dates_yf)} 至 {max(dates_yf)}')

# 找到共同日期
common_dates = dates_tushare & dates_ak & dates_yf
print(f'\n  三个数据源共同日期数：{len(common_dates)}')

# 找到仅在两个数据源中存在的日期
tushare_ak_common = dates_tushare & dates_ak
tushare_yf_common = dates_tushare & dates_yf
ak_yf_common = dates_ak & dates_yf

print(f'  Tushare & Akshare 共同日期数：{len(tushare_ak_common)}')
print(f'  Tushare & Yfinance 共同日期数：{len(tushare_yf_common)}')
print(f'  Akshare & Yfinance 共同日期数：{len(ak_yf_common)}')

# 仅在单个数据源中存在的日期
only_tushare = dates_tushare - dates_ak - dates_yf
only_ak = dates_ak - dates_tushare - dates_yf
only_yf = dates_yf - dates_tushare - dates_ak

print(f'\n  仅在 Tushare 中存在的日期数：{len(only_tushare)}')
print(f'  仅在 Akshare 中存在的日期数：{len(only_ak)}')
print(f'  仅在 Yfinance 中存在的日期数：{len(only_yf)}')

if len(only_tushare) > 0:
    print(f'    示例：{sorted(only_tushare)[:5]}')
if len(only_ak) > 0:
    print(f'    示例：{sorted(only_ak)[:5]}')
if len(only_yf) > 0:
    print(f'    示例：{sorted(only_yf)[:5]}')

# ============================================================================
# 4. 价格对比（收盘价）
# ============================================================================
print('\n' + '=' * 80)
print('4. 价格对比（收盘价）')
print('=' * 80)

# 筛选共同日期的数据
common_dates_sorted = sorted(common_dates)

# 将 common_dates 转换为 Timestamp 以便与 DataFrame 索引匹配
common_dates_timestamps = [pd.Timestamp(d) for d in common_dates_sorted]

# Tushare 收盘价
df_tu_common = df_tushare[df_tushare['trade_date'].dt.date.isin(common_dates)].copy()
df_tu_common = df_tu_common.set_index('trade_date').loc[common_dates_timestamps]

# Akshare 收盘价（未复权）
df_ak_common = df_ak_raw[df_ak_raw['日期'].dt.date.isin(common_dates)].copy()
df_ak_common = df_ak_common.set_index('日期').loc[common_dates_timestamps]

# Yfinance 收盘价
df_yf_common = df_yf[df_yf['Date'].dt.date.isin(common_dates)].copy()
df_yf_common = df_yf_common.set_index('Date').loc[common_dates_timestamps]

# 计算价格差异
price_tu = df_tu_common['close'].values
price_ak = df_ak_common['收盘'].values
price_yf = df_yf_common['Close'].values

print(f'\n对比 {len(common_dates_timestamps)} 个共同交易日：')
print('\nTushare vs Akshare (未复权):')
diff_tu_ak = price_tu - price_ak
print(f'  平均差异：{np.mean(diff_tu_ak):.6f} 元')
print(f'  最大差异：{np.max(np.abs(diff_tu_ak)):.6f} 元')
print(f'  差异 > 0.01 元的交易日数：{np.sum(np.abs(diff_tu_ak) > 0.01)}')

print('\nTushare vs Yfinance:')
diff_tu_yf = price_tu - price_yf
print(f'  平均差异：{np.mean(diff_tu_yf):.6f} 元')
print(f'  最大差异：{np.max(np.abs(diff_tu_yf)):.6f} 元')
print(f'  差异 > 0.01 元的交易日数：{np.sum(np.abs(diff_tu_yf) > 0.01)}')

print('\nAkshare (未复权) vs Yfinance:')
diff_ak_yf = price_ak - price_yf
print(f'  平均差异：{np.mean(diff_ak_yf):.6f} 元')
print(f'  最大差异：{np.max(np.abs(diff_ak_yf)):.6f} 元')
print(f'  差异 > 0.01 元的交易日数：{np.sum(np.abs(diff_ak_yf) > 0.01)}')

# ============================================================================
# 5. 成交量对比
# ============================================================================
print('\n' + '=' * 80)
print('5. 成交量对比')
print('=' * 80)

# 成交量单位可能不同，需要确认
print('\nTushare 成交量单位：手')
print(f'  示例：{df_tushare["vol"].head()}')
print('\nAkshare 成交量单位：？')
print(f'  示例：{df_ak_raw["成交量"].head()}')
print('\nYfinance 成交量单位：股')
print(f'  示例：{df_yf["Volume"].head()}')

# 尝试单位转换
# Tushare: vol (手) -> 需要 * 100 转换为股
# Akshare: 成交量 (手?) -> 需要确认
# Yfinance: Volume (股)

print('\n⚠ 成交量单位可能不同，需要标准化后对比')

# ============================================================================
# 6. 复权数据对比
# ============================================================================
print('\n' + '=' * 80)
print('6. 复权数据对比')
print('=' * 80)

# Akshare 提供了前复权数据，可以对比未复权和前复权的差异
print('\nAkshare 未复权 vs 前复权：')

df_ak_qfq_common = df_ak_qfq[df_ak_qfq['日期'].dt.date.isin(common_dates)].copy()
df_ak_qfq_common = df_ak_qfq_common.set_index('日期').loc[common_dates_timestamps]

price_ak_raw = df_ak_common['收盘'].values
price_ak_qfq = df_ak_qfq_common['收盘'].values

diff_ak_raw_qfq = price_ak_raw - price_ak_qfq
print(f'  未复权收盘价 - 前复权收盘价')
print(f'  平均差异：{np.mean(diff_ak_raw_qfq):.6f} 元')
print(f'  最大差异：{np.max(np.abs(diff_ak_raw_qfq)):.6f} 元')
print(f'  最小差异：{np.min(diff_ak_raw_qfq):.6f} 元')

# ============================================================================
# 7. 生成对比报告
# ============================================================================
print('\n' + '=' * 80)
print('7. 生成对比报告')
print('=' * 80)

report = {
    'comparison_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'data_range': {
        'start': min(min(dates_tushare), min(dates_ak), min(dates_yf)).strftime('%Y-%m-%d'),
        'end': max(max(dates_tushare), max(dates_ak), max(dates_yf)).strftime('%Y-%m-%d')
    },
    'record_counts': {
        'tushare': len(df_tushare),
        'akshare_raw': len(df_ak_raw),
        'akshare_qfq': len(df_ak_qfq),
        'yfinance': len(df_yf)
    },
    'common_dates': {
        'all_three': len(common_dates),
        'tushare_akshare': len(tushare_ak_common),
        'tushare_yfinance': len(tushare_yf_common),
        'akshare_yfinance': len(ak_yf_common)
    },
    'unique_dates': {
        'only_tushare': len(only_tushare),
        'only_akshare': len(only_ak),
        'only_yfinance': len(only_yf)
    },
    'price_comparison': {
        'tushare_vs_akshare': {
            'mean_diff': float(np.mean(diff_tu_ak)),
            'max_abs_diff': float(np.max(np.abs(diff_tu_ak))),
            'count_diff_gt_001': int(np.sum(np.abs(diff_tu_ak) > 0.01))
        },
        'tushare_vs_yfinance': {
            'mean_diff': float(np.mean(diff_tu_yf)),
            'max_abs_diff': float(np.max(np.abs(diff_tu_yf))),
            'count_diff_gt_001': int(np.sum(np.abs(diff_tu_yf) > 0.01))
        },
        'akshare_vs_yfinance': {
            'mean_diff': float(np.mean(diff_ak_yf)),
            'max_abs_diff': float(np.max(np.abs(diff_ak_yf))),
            'count_diff_gt_001': int(np.sum(np.abs(diff_ak_yf) > 0.01))
        }
    },
    'adjustment_comparison': {
        'akshare_raw_vs_qfq': {
            'mean_diff': float(np.mean(diff_ak_raw_qfq)),
            'max_abs_diff': float(np.max(np.abs(diff_ak_raw_qfq))),
            'min_diff': float(np.min(diff_ak_raw_qfq))
        }
    }
}

# 保存报告
with open('data/multi_source/detailed_comparison_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'\n✓ 详细对比报告已保存至：data/multi_source/detailed_comparison_report.json')

# ============================================================================
# 8. 生成对比表格（CSV）
# ============================================================================
print('\n8. 生成对比表格（CSV）...')

# 创建一个包含三个数据源价格的 DataFrame
df_compare = pd.DataFrame({
    'date': [d.strftime('%Y-%m-%d') for d in common_dates_sorted],
    'tushare_close': price_tu,
    'akshare_raw_close': price_ak,
    'yfinance_close': price_yf,
    'diff_tu_ak': diff_tu_ak,
    'diff_tu_yf': diff_tu_yf,
    'diff_ak_yf': diff_ak_yf
})

df_compare.to_csv('data/multi_source/price_comparison.csv', index=False, encoding='utf-8-sig')
print(f'✓ 价格对比表格已保存至：data/multi_source/price_comparison.csv')

# ============================================================================
# 9. 打印总结
# ============================================================================
print('\n' + '=' * 80)
print('对比总结')
print('=' * 80)

print('\n1. 数据完整性：')
print(f'   - Tushare: {len(df_tushare)} 条')
print(f'   - Akshare: {len(df_ak_raw)} 条（未复权）、{len(df_ak_qfq)} 条（前复权）')
print(f'   - Yfinance: {len(df_yf)} 条')

print('\n2. 价格一致性：')
print(f'   - Tushare vs Akshare (未复权): 平均差异 {np.mean(diff_tu_ak):.6f} 元')
print(f'   - Tushare vs Yfinance: 平均差异 {np.mean(diff_tu_yf):.6f} 元')
print(f'   - Akshare (未复权) vs Yfinance: 平均差异 {np.mean(diff_ak_yf):.6f} 元')

print('\n3. 复权影响：')
print(f'   - Akshare 未复权 vs 前复权: 平均差异 {np.mean(diff_ak_raw_qfq):.6f} 元')

print('\n' + '=' * 80)
print('详细对比完成')
print('=' * 80)
