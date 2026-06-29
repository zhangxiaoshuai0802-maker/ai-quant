#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取中芯国际（688981.SH）近一年数据并生成 HTML 看板
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 读取 .env 中的 token
from dotenv import load_dotenv
load_dotenv()
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '49446d04948a0760679287f44b2ff9f9f9f010ad08c03abf0b338dd0')

print('=' * 80)
print('中芯国际（688981.SH）数据获取与看板生成')
print('=' * 80)

# ============================================================================
# 1. 获取数据
# ============================================================================
print('\n1. 从 Tushare 获取数据...')

try:
    import tushare as ts
    pro = ts.pro_api(token=TUSHARE_TOKEN)
    
    # 中芯国际 A股代码：688981.SH
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    print(f'   时间范围：{start_date} 至 {end_date}')
    print(f'   股票代码：688981.SH')
    
    df = pro.daily(ts_code='688981.SH', start_date=start_date, end_date=end_date)
    
    if df is not None and not df.empty:
        df = df.sort_values('trade_date', ascending=True)
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        
        # 保存数据
        os.makedirs('data/smic', exist_ok=True)
        df.to_csv('data/smic/688981_SH_daily.csv', index=False, encoding='utf-8-sig')
        
        print(f'   ✓ 数据获取成功')
        print(f'     记录数：{len(df)} 条')
        print(f'     日期范围：{df["trade_date"].min()} 至 {df["trade_date"].max()}')
        print(f'     已保存至：data/smic/688981_SH_daily.csv')
    else:
        print('   ✗ 数据获取失败：返回为空')
        df = None
        
except Exception as e:
    print(f'   ✗ 数据获取失败：{e}')
    df = None

if df is None:
    print('\n无法获取数据，程序终止')
    exit(1)

# ============================================================================
# 2. 生成 K线图和成交量图（使用 mplfinance）
# ============================================================================
print('\n2. 生成可视化图表...')

# 创建输出目录
os.makedirs('reports', exist_ok=True)

try:
    import mplfinance as mpf
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import platform
    import logging
    
    # 设置中文字体
    system = platform.system()
    if system == 'Darwin':
        available = [f.name for f in fm.fontManager.ttflist]
        for font in ['Arial Unicode MS', 'STHeiti', 'Heiti SC', 'PingFang SC']:
            if font in available:
                plt.rcParams['font.sans-serif'] = [font]
                break
    elif system == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei']
    
    plt.rcParams['axes.unicode_minus'] = False
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    
    # 准备数据（mplfinance 需要特定的列名）
    df_plot = df.copy()
    df_plot['trade_date'] = pd.to_datetime(df_plot['trade_date'])
    df_plot = df_plot.set_index('trade_date')
    
    # mplfinance 需要 'volume' 列名
    df_plot = df_plot.rename(columns={'vol': 'volume'})
    
    # 图 1: K线图
    print('   生成 K线图...')
    mpf.plot(df_plot, 
             type='candle', 
             volume=False,
             title='中芯国际（688981.SH）K线图',
             ylabel='价格（元）',
             figsize=(14, 7),
             style='charles',
             savefig='reports/smic_kline.png')
    print('     ✓ K线图已保存')
    
    # 图 2: K线图 + 成交量
    print('   生成 K线图 + 成交量图...')
    mpf.plot(df_plot, 
             type='candle', 
             volume=True,
             title='中芯国际（688981.SH）K线图 + 成交量',
             ylabel='价格（元）',
             ylabel_lower='成交量（手）',
             figsize=(14, 10),
             style='charles',
             savefig='reports/smic_kline_volume.png')
    print('     ✓ K线图 + 成交量图已保存')
    
    charts_generated = True
    
except Exception as e:
    print(f'   ✗ 图表生成失败：{e}')
    charts_generated = False

# ============================================================================
# 3. 将图片转换为 base64（嵌入 HTML）
# ============================================================================
print('\n3. 准备 HTML 看板数据...')

import base64
from io import BytesIO

def image_to_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

if charts_generated:
    img_kline = image_to_base64('reports/smic_kline.png')
    img_kline_vol = image_to_base64('reports/smic_kline_volume.png')
    print('   ✓ 图片已转换为 base64')
else:
    img_kline = ''
    img_kline_vol = ''

# ============================================================================
# 4. 计算统计指标
# ============================================================================
print('\n4. 计算统计指标...')

latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest

latest_close = latest['close']
prev_close = latest['pre_close'] if 'pre_close' in df.columns else prev['close']
change = latest_close - prev_close
pct_change = (change / prev_close) * 100 if prev_close != 0 else 0

high_52w = df['high'].max()
low_52w = df['low'].min()
avg_vol = df['vol'].mean()
latest_vol = latest['vol']

print(f'   最新收盘价：{latest_close:.2f} 元')
print(f'   涨跌幅：{pct_change:+.2f}%')
print(f'   52周最高：{high_52w:.2f} 元')
print(f'   52周最低：{low_52w:.2f} 元')

# ============================================================================
# 5. 生成 HTML 看板
# ============================================================================
print('\n5. 生成 HTML 看板...')

# 最近 10 个交易日数据（倒序，最新的在前面）
recent_data = df.tail(10).iloc[::-1]

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中芯国际（688981.SH）股票看板</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               background: #f5f7fa; color: #333; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        
        /* 头部 */
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 30px; border-radius: 12px; 
                     margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 14px; opacity: 0.9; }}
        
        /* 指标卡片 */
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                      gap: 15px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                            transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); 
                              box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
        .metric-card .label {{ font-size: 12px; color: #7f8c8d; margin-bottom: 8px; }}
        .metric-card .value {{ font-size: 24px; font-weight: bold; }}
        .metric-card .change {{ font-size: 14px; margin-top: 5px; }}
        .positive {{ color: #e74c3c; }}  /* 红涨 */
        .negative {{ color: #27ae60; }}  /* 绿跌 */
        
        /* 图表区域 */
        .chart-section {{ background: white; padding: 25px; border-radius: 12px; 
                           box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                           margin-bottom: 20px; }}
        .chart-section h2 {{ color: #2c3e50; margin-bottom: 20px; 
                              padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        .chart-img {{ text-align: center; margin: 20px 0; }}
        .chart-img img {{ max-width: 100%; height: auto; border-radius: 8px; }}
        
        /* 数据表格 */
        .data-table {{ background: white; padding: 25px; border-radius: 12px; 
                           box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .data-table h2 {{ color: #2c3e50; margin-bottom: 20px; 
                              padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #3498db; color: white; font-weight: bold; }}
        tr:hover {{ background: #f8f9fa; }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .metrics {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 22px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📈 中芯国际（688981.SH）</h1>
            <div class="subtitle">科创板 | 近一年交易数据 | 数据更新：{datetime.now().strftime('%Y-%m-%d')}</div>
        </div>
        
        <!-- 关键指标 -->
        <div class="metrics">
            <div class="metric-card">
                <div class="label">最新收盘价</div>
                <div class="value" style="color: {'#e74c3c' if change >= 0 else '#27ae60'};">
                    {latest_close:.2f} 元
                </div>
                <div class="change {'positive' if change >= 0 else 'negative'}">
                    {'+' if change >= 0 else ''}{change:.2f} ({'+' if pct_change >= 0 else ''}{pct_change:.2f}%)
                </div>
            </div>
            
            <div class="metric-card">
                <div class="label">52周最高价</div>
                <div class="value">{high_52w:.2f} 元</div>
            </div>
            
            <div class="metric-card">
                <div class="label">52周最低价</div>
                <div class="value">{low_52w:.2f} 元</div>
            </div>
            
            <div class="metric-card">
                <div class="label">平均成交量</div>
                <div class="value">{avg_vol:.0f} 手</div>
            </div>
            
            <div class="metric-card">
                <div class="label">最新成交量</div>
                <div class="value">{latest_vol:.0f} 手</div>
            </div>
            
            <div class="metric-card">
                <div class="label">交易天数</div>
                <div class="value">{len(df)} 天</div>
            </div>
        </div>
"""

# 添加 K线图
if charts_generated:
    html_content += f"""
        <!-- K线图 -->
        <div class="chart-section">
            <h2>📊 K线图（蜡烛图）</h2>
            <div class="chart-img">
                <img src="data:image/png;base64,{img_kline}" alt="K线图">
            </div>
            <p style="text-align: center; color: #7f8c8d; margin-top: 10px;">
                🔴 阳线（收盘 ≥ 开盘）| 🟢 阴线（收盘 < 开盘）
            </p>
        </div>
        
        <!-- K线图 + 成交量 -->
        <div class="chart-section">
            <h2>📉 K线图 + 成交量</h2>
            <div class="chart-img">
                <img src="data:image/png;base64,{img_kline_vol}" alt="K线图 + 成交量">
            </div>
        </div>
"""

# 添加最近数据表格
html_content += f"""
        <!-- 最近数据表格 -->
        <div class="data-table">
            <h2>📋 最近 10 个交易日数据</h2>
            <table>
                <tr>
                    <th>日期</th>
                    <th>开盘</th>
                    <th>最高</th>
                    <th>最低</th>
                    <th>收盘</th>
                    <th>涨跌幅</th>
                    <th>成交量（手）</th>
                    <th>成交额（千元）</th>
                </tr>
"""

for _, row in recent_data.iterrows():
    pct = row['pct_chg'] if 'pct_chg' in df.columns else 0
    row_class = 'positive' if pct >= 0 else 'negative'
    
    html_content += f"""
                <tr>
                    <td>{row['trade_date']}</td>
                    <td>{row['open']:.2f}</td>
                    <td>{row['high']:.2f}</td>
                    <td>{row['low']:.2f}</td>
                    <td>{row['close']:.2f}</td>
                    <td class="{row_class}">{'+' if pct >= 0 else ''}{pct:.2f}%</td>
                    <td>{row['vol']:.0f}</td>
                    <td>{row['amount']:.0f}</td>
                </tr>
"""

html_content += f"""
            </table>
        </div>
        
        <hr style="margin: 40px 0; border: none; border-top: 1px solid #ecf0f1;">
        <p style="text-align: center; color: #95a5a6; font-size: 12px;">
            数据来源：Tushare Pro API | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>"""

# 保存 HTML 文件
os.makedirs('reports', exist_ok=True)
output_path = 'reports/smic_dashboard.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'   ✓ HTML 看板已保存至：{output_path}')
print(f'\n   ℹ️ 图片已嵌入 HTML，可离线打开查看')

# ============================================================================
# 6. 保存元数据
# ============================================================================
print('\n6. 保存元数据...')

metadata = {
    'stock_code': '688981.SH',
    'stock_name': '中芯国际',
    'market': '科创板',
    'data_range': {
        'start': df['trade_date'].min(),
        'end': df['trade_date'].max()
    },
    'record_count': len(df),
    'latest_close': float(latest_close),
    'change': float(change),
    'pct_change': float(pct_change),
    'high_52w': float(high_52w),
    'low_52w': float(low_52w),
    'avg_vol': float(avg_vol),
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

with open('data/smic/metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print('   ✓ 元数据已保存至：data/smic/metadata.json')

# ============================================================================
# 完成
# ============================================================================
print('\n' + '=' * 80)
print('✅ 任务完成！')
print('=' * 80)
print(f'\n输出文件：')
print(f'  1. data/smic/688981_SH_daily.csv - 原始数据')
print(f'  2. data/smic/metadata.json - 元数据')
print(f'  3. reports/smic_kline.png - K线图')
print(f'  4. reports/smic_kline_volume.png - K线图 + 成交量')
print(f'  5. reports/smic_dashboard.html - HTML 看板（已打开）')
print(f'\n请在上方预览面板中查看 HTML 看板 📊')
