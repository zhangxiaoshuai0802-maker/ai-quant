#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Akshare 和 Yfinance 获取 510300.SH 数据，并与 Tushare 对比
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json

# 读取 Tushare Token
from dotenv import load_dotenv
load_dotenv()
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

# 创建输出目录
output_dir = 'data/multi_source'
os.makedirs(output_dir, exist_ok=True)

print('=' * 80)
print('多数据源数据获取与对比：510300.SH（沪深300ETF）')
print('=' * 80)

# ============================================================================
# 1. 从 Tushare 获取数据（已有缓存则读取，否则重新获取）
# ============================================================================
print('\n' + '=' * 80)
print('1. 从 Tushare 获取数据')
print('=' * 80)

try:
    import tushare as ts
    
    # 检查是否已有缓存
    tushare_raw_file = 'data/raw/510300_SH_daily_raw.csv'
    
    if os.path.exists(tushare_raw_file):
        print(f'✓ 读取 Tushare 缓存数据：{tushare_raw_file}')
        df_tushare = pd.read_csv(tushare_raw_file)
        print(f'  记录数：{len(df_tushare)} 条')
        print(f'  起止日期：{df_tushare["trade_date"].min()} 至 {df_tushare["trade_date"].max()}')
    else:
        print('⚠ Tushare 缓存不存在，重新获取...')
        if not TUSHARE_TOKEN:
            print('✗ TUSHARE_TOKEN 未设置')
            df_tushare = None
        else:
            # 初始化 Tushare Pro API
            pro = ts.pro_api(token=TUSHARE_TOKEN)
            
            # 获取近 5 年数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now().replace(year=datetime.now().year - 5)).strftime('%Y%m%d')
            
            print(f'  请求时间范围：{start_date} 至 {end_date}')
            df = pro.fund_daily(ts_code='510300.SH', start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                # 按交易日期升序排列
                df = df.sort_values('trade_date', ascending=True)
                
                # 转换日期格式为 YYYY-MM-DD
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
                
                # 保存原始数据
                os.makedirs('data/raw', exist_ok=True)
                df.to_csv(tushare_raw_file, index=False, encoding='utf-8-sig')
                
                df_tushare = df
                print(f'✓ Tushare 数据获取成功')
                print(f'  记录数：{len(df_tushare)} 条')
                print(f'  起止日期：{df_tushare["trade_date"].min()} 至 {df_tushare["trade_date"].max()}')
            else:
                print('✗ Tushare 数据获取失败')
                df_tushare = None
    
except Exception as e:
    print(f'✗ Tushare 数据获取失败：{e}')
    df_tushare = None

# ============================================================================
# 2. 从 Akshare 获取数据
# ============================================================================
print('\n' + '=' * 80)
print('2. 从 Akshare 获取数据')
print('=' * 80)

try:
    import akshare as ak
    
    # 510300 是上交所 ETF，使用 fund_etf_hist_em 接口
    # adjust: "qfq"（前复权）、"hfq"（后复权）、""（未复权）
    
    print('  正在获取未复权数据...')
    df_ak_raw = ak.fund_etf_hist_em(
        symbol="510300",
        period="daily",
        start_date="20210621",
        end_date=datetime.now().strftime('%Y%m%d'),
        adjust=""
    )
    
    if df_ak_raw is not None and not df_ak_raw.empty:
        print(f'✓ Akshare 未复权数据获取成功')
        print(f'  记录数：{len(df_ak_raw)} 条')
        print(f'  列名：{list(df_ak_raw.columns)}')
        
        # 保存未复权数据
        df_ak_raw.to_csv(f'{output_dir}/510300_akshare_raw.csv', index=False, encoding='utf-8-sig')
        print(f'  已保存至：{output_dir}/510300_akshare_raw.csv')
    else:
        print('✗ Akshare 未复权数据获取失败')
        df_ak_raw = None
    
    # 获取前复权数据
    print('\n  正在获取前复权数据...')
    df_ak_qfq = ak.fund_etf_hist_em(
        symbol="510300",
        period="daily",
        start_date="20210621",
        end_date=datetime.now().strftime('%Y%m%d'),
        adjust="qfq"
    )
    
    if df_ak_qfq is not None and not df_ak_qfq.empty:
        print(f'✓ Akshare 前复权数据获取成功')
        print(f'  记录数：{len(df_ak_qfq)} 条')
        
        # 保存前复权数据
        df_ak_qfq.to_csv(f'{output_dir}/510300_akshare_qfq.csv', index=False, encoding='utf-8-sig')
        print(f'  已保存至：{output_dir}/510300_akshare_qfq.csv')
    else:
        print('✗ Akshare 前复权数据获取失败')
        df_ak_qfq = None
    
except Exception as e:
    print(f'✗ Akshare 数据获取失败：{e}')
    df_ak_raw = None
    df_ak_qfq = None

# ============================================================================
# 3. 从 Yfinance 获取数据
# ============================================================================
print('\n' + '=' * 80)
print('3. 从 Yfinance 获取数据')
print('=' * 80)

try:
    import yfinance as yf
    
    # 510300.SH 在 Yfinance 中可能表示为 510300.SS
    # 但 Yfinance 主要支持美股，A股 ETF 可能不支持
    # 尝试几个可能的代码
    possible_symbols = ['510300.SS', '510300.SH', '510300']
    
    df_yf = None
    for symbol in possible_symbols:
        try:
            print(f'  尝试获取 {symbol}...')
            ticker = yf.Ticker(symbol)
            df_yf = ticker.history(start="2021-06-21", end=datetime.now().strftime('%Y-%m-%d'))
            
            if df_yf is not None and not df_yf.empty:
                print(f'✓ Yfinance 数据获取成功（{symbol}）')
                print(f'  记录数：{len(df_yf)} 条')
                print(f'  列名：{list(df_yf.columns)}')
                break
        except Exception as e:
            print(f'  ✗ {symbol} 获取失败：{e}')
            continue
    
    if df_yf is None or df_yf.empty:
        print('✗ Yfinance 无法获取 510300.SH 数据（可能不支持 A股 ETF）')
        df_yf = None
    else:
        # 保存数据
        df_yf.to_csv(f'{output_dir}/510300_yfinance_raw.csv', encoding='utf-8-sig')
        print(f'  已保存至：{output_dir}/510300_yfinance_raw.csv')
    
except Exception as e:
    print(f'✗ Yfinance 数据获取失败：{e}')
    df_yf = None

# ============================================================================
# 4. 数据对比分析
# ============================================================================
print('\n' + '=' * 80)
print('4. 数据对比分析')
print('=' * 80)

# 初始化对比结果
comparison_results = {
    'tushare': {
        'status': 'success' if df_tushare is not None else 'failed',
        'record_count': len(df_tushare) if df_tushare is not None else 0,
        'date_range': None,
        'columns': list(df_tushare.columns) if df_tushare is not None else []
    },
    'akshare': {
        'status': 'success' if df_ak_raw is not None else 'failed',
        'record_count': len(df_ak_raw) if df_ak_raw is not None else 0,
        'date_range': None,
        'columns': list(df_ak_raw.columns) if df_ak_raw is not None else []
    },
    'yfinance': {
        'status': 'success' if df_yf is not None else 'failed',
        'record_count': len(df_yf) if df_yf is not None else 0,
        'date_range': None,
        'columns': list(df_yf.columns) if df_yf is not None else []
    }
}

# 更新日期范围
if df_tushare is not None:
    comparison_results['tushare']['date_range'] = {
        'start': df_tushare['trade_date'].min(),
        'end': df_tushare['trade_date'].max()
    }

if df_ak_raw is not None:
    # Akshare 的日期列名可能是 '日期'
    date_col = '日期' if '日期' in df_ak_raw.columns else df_ak_raw.columns[0]
    comparison_results['akshare']['date_range'] = {
        'start': df_ak_raw[date_col].min(),
        'end': df_ak_raw[date_col].max()
    }

if df_yf is not None:
    comparison_results['yfinance']['date_range'] = {
        'start': df_yf.index.min().strftime('%Y-%m-%d'),
        'end': df_yf.index.max().strftime('%Y-%m-%d')
    }

# 打印对比结果
print('\n数据源对比摘要：')
print('-' * 80)
for source, info in comparison_results.items():
    print(f'\n{source.upper()}:')
    print(f'  状态：{info["status"]}')
    print(f'  记录数：{info["record_count"]} 条')
    if info['date_range']:
        print(f'  日期范围：{info["date_range"]["start"]} 至 {info["date_range"]["end"]}')
    print(f'  字段：{info["columns"]}')

# 保存对比结果
with open(f'{output_dir}/comparison_results.json', 'w', encoding='utf-8') as f:
    json.dump(comparison_results, f, ensure_ascii=False, indent=2)

print(f'\n✓ 对比结果已保存至：{output_dir}/comparison_results.json')

# ============================================================================
# 5. 详细对比（如果至少两个数据源成功）
# ============================================================================
print('\n' + '=' * 80)
print('5. 详细数据对比（Tushare vs Akshare）')
print('=' * 80)

if df_tushare is not None and df_ak_raw is not None:
    print('\n正在对比 Tushare 和 Akshare 数据...')
    
    # 标准化日期格式
    df_tushare['trade_date'] = pd.to_datetime(df_tushare['trade_date'])
    
    # Akshare 的日期列
    date_col_ak = '日期' if '日期' in df_ak_raw.columns else df_ak_raw.columns[0]
    df_ak_raw[date_col_ak] = pd.to_datetime(df_ak_raw[date_col_ak])
    
    # 找到共同的日期
    common_dates = set(df_tushare['trade_date'].dt.date) & set(df_ak_raw[date_col_ak].dt.date)
    print(f'  共同交易日数：{len(common_dates)}')
    
    # 保存共同日期的数据用于对比
    if len(common_dates) > 0:
        # 这里需要更详细的对比逻辑，但由于字段名不同，需要先映射
        print('  ⚠ 需要字段映射后才能进行详细对比')
        print('  建议：在 Jupyter Notebook 中进行可视化对比')

print('\n' + '=' * 80)
print('数据获取与对比完成')
print('=' * 80)
print(f'\n输出文件已保存至：{output_dir}/')
print('  1. 510300_akshare_raw.csv - Akshare 未复权数据')
print('  2. 510300_akshare_qfq.csv - Akshare 前复权数据')
print('  3. comparison_results.json - 数据源对比结果')
if df_yf is not None:
    print('  4. 510300_yfinance_raw.csv - Yfinance 数据')
