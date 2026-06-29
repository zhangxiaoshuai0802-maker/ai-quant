#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中芯国际 A股 vs 港股 对比分析看板生成脚本（改进版）
- 使用英文标题（避免中文乱码）
- 修复港股数据格式问题
- 改进图表生成逻辑
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import base64

# 读取 .env 中的 token
from dotenv import load_dotenv
load_dotenv()
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '49446d04948a0760679287f44b2ff9f9f010ad08c03abf0b338dd0')

print('=' * 80)
print('中芯国际 A股 vs 港股 对比分析看板生成（改进版）')
print('=' * 80)

# ============================================================================
# 0. 设置 matplotlib 配置
# ============================================================================
print('\n0. 配置 matplotlib...')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import logging

# 设置英文显示（避免中文乱码）
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 清除字体缓存
try:
    fm._load_fontmanager(try_read_cache=False)
except:
    pass

logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

print('   ✓ 使用英文字体（避免中文乱码）')

# ============================================================================
# 1. 获取数据（A股 + 港股）
# ============================================================================
print('\n1. 获取数据...')

try:
    import tushare as ts
    pro = ts.pro_api(token=TUSHARE_TOKEN)
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    # 1.1 获取 A股数据（688981.SH）
    print(f'   (1/2) 获取 A股数据（688981.SH）...')
    df_a = pro.daily(ts_code='688981.SH', start_date=start_date, end_date=end_date)
    
    if df_a is not None and not df_a.empty:
        df_a = df_a.sort_values('trade_date', ascending=True)
        df_a['trade_date'] = pd.to_datetime(df_a['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        
        os.makedirs('data/smic', exist_ok=True)
        df_a.to_csv('data/smic/688981_SH_daily.csv', index=False, encoding='utf-8-sig')
        
        print(f'      ✓ A股数据获取成功')
        print(f'        记录数：{len(df_a)} 条')
        print(f'        日期范围：{df_a["trade_date"].min()} 至 {df_a["trade_date"].max()}')
        print(f'        列名：{list(df_a.columns)}')
    else:
        print('      ✗ A股数据获取失败：返回为空')
        df_a = None
    
    # 1.2 获取港股数据
    print(f'   (2/2) 获取港股数据（00981.HK）...')
    
    # 使用 akshare 获取港股数据
    try:
        import akshare as ak
        
        df_hk = ak.stock_hk_hist(
            symbol="00981",
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        
        if df_hk is not None and not df_hk.empty:
            # akshare 港股数据列名：['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            print(f'        原始列名：{list(df_hk.columns)}')
            
            # 重命名列为英文（与 Tushare 格式一致）
            df_hk = df_hk.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'vol',
                '成交额': 'amount',
                '涨跌幅': 'pct_chg'
            })
            
            # 确保日期格式为 YYYY-MM-DD
            df_hk['trade_date'] = pd.to_datetime(df_hk['trade_date']).dt.strftime('%Y-%m-%d')
            df_hk = df_hk.sort_values('trade_date', ascending=True)
            
            # 添加 ts_code 列
            df_hk['ts_code'] = '00981.HK'
            
            # 选择需要的列（与 Tushare 格式一致）
            required_cols = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount', 'pct_chg']
            df_hk = df_hk[[col for col in required_cols if col in df_hk.columns]]
            
            os.makedirs('data/smic', exist_ok=True)
            df_hk.to_csv('data/smic/00981_HK_daily.csv', index=False, encoding='utf-8-sig')
            
            print(f'      ✓ 港股数据获取成功（akshare）')
            print(f'        记录数：{len(df_hk)} 条')
            print(f'        日期范围：{df_hk["trade_date"].min()} 至 {df_hk["trade_date"].max()}')
            print(f'        列名：{list(df_hk.columns)}')
        else:
            print('      ✗ 港股数据获取失败：返回为空')
            df_hk = None
            
    except Exception as e:
        print(f'      ✗ 港股数据获取失败：{e}')
        df_hk = None
        
except Exception as e:
    print(f'   ✗ 数据获取失败：{e}')
    df_a = None
    df_hk = None

if df_a is None and df_hk is None:
    print('\n无法获取数据，程序终止')
    exit(1)

# ============================================================================
# 2. 生成 K线图（A股 + 港股）
# ============================================================================
print('\n2. 生成可视化图表...')

os.makedirs('reports', exist_ok=True)

try:
    import mplfinance as mpf
    
    charts_generated = True
    img_a_kline = ''
    img_hk_kline = ''
    img_comparison = ''
    
    # 2.1 A股 K线图
    if df_a is not None:
        print('   生成 A股 K线图...')
        
        # 准备数据（mplfinance 需要特定的列名和格式）
        df_a_plot = df_a.copy()
        df_a_plot['trade_date'] = pd.to_datetime(df_a_plot['trade_date'])
        df_a_plot = df_a_plot.set_index('trade_date')
        
        # mplfinance 需要 'volume' 列名
        if 'vol' in df_a_plot.columns and 'volume' not in df_a_plot.columns:
            df_a_plot = df_a_plot.rename(columns={'vol': 'volume'})
        
        print(f'      A股绘图数据形状：{df_a_plot.shape}')
        print(f'      A股绘图数据列名：{list(df_a_plot.columns)}')
        
        mpf.plot(df_a_plot, 
                 type='candle', 
                 volume=True,
                 title='SMIC A-Share (688981.SH) - Candlestick Chart',
                 ylabel='Price (CNY)',
                 ylabel_lower='Volume (lots)',
                 figsize=(14, 10),
                 style='charles',
                 savefig='reports/smic_a_kline.png')
        
        img_a_kline = base64.b64encode(open('reports/smic_a_kline.png', 'rb').read()).decode('utf-8')
        print('     ✓ A股 K线图已保存')
    
    # 2.2 港股 K线图
    if df_hk is not None:
        print('   生成港股 K线图...')
        
        # 准备数据（mplfinance 需要特定的列名和格式）
        df_hk_plot = df_hk.copy()
        df_hk_plot['trade_date'] = pd.to_datetime(df_hk_plot['trade_date'])
        df_hk_plot = df_hk_plot.set_index('trade_date')
        
        # mplfinance 需要 'volume' 列名
        if 'vol' in df_hk_plot.columns and 'volume' not in df_hk_plot.columns:
            df_hk_plot = df_hk_plot.rename(columns={'vol': 'volume'})
        
        print(f'      港股绘图数据形状：{df_hk_plot.shape}')
        print(f'      港股绘图数据列名：{list(df_hk_plot.columns)}')
        print(f'      港股价格范围：{df_hk_plot["close"].min():.2f} - {df_hk_plot["close"].max():.2f} HKD')
        
        mpf.plot(df_hk_plot, 
                 type='candle', 
                 volume=True,
                 title='SMIC HK-Share (00981.HK) - Candlestick Chart',
                 ylabel='Price (HKD)',
                 ylabel_lower='Volume (shares)',
                 figsize=(14, 10),
                 style='charles',
                 savefig='reports/smic_hk_kline.png')
        
        img_hk_kline = base64.b64encode(open('reports/smic_hk_kline.png', 'rb').read()).decode('utf-8')
        print('     ✓ 港股 K线图已保存')
    
    # 2.3 价格对比图
    if df_a is not None and df_hk is not None:
        print('   生成 A股 vs 港股价格对比图...')
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 归一化处理（便于对比趋势）
        df_a_norm = df_a.copy()
        df_a_norm['close_norm'] = df_a_norm['close'] / df_a_norm['close'].iloc[0] * 100
        
        df_hk_norm = df_hk.copy()
        df_hk_norm['close_norm'] = df_hk_norm['close'] / df_hk_norm['close'].iloc[0] * 100
        
        # 图1：原始价格对比
        ax1 = axes[0]
        ax1.plot(pd.to_datetime(df_a['trade_date']), df_a['close'], 
                label='A-Share (688981.SH)', color='#e74c3c', linewidth=2)
        ax1.plot(pd.to_datetime(df_hk['trade_date']), df_hk['close'], 
                label='HK-Share (00981.HK)', color='#3498db', linewidth=2)
        ax1.set_ylabel('Closing Price', fontsize=12)
        ax1.set_title('SMIC A-Share vs HK-Share Price Comparison', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # 图2：归一化价格对比
        ax2 = axes[1]
        ax2.plot(pd.to_datetime(df_a_norm['trade_date']), df_a_norm['close_norm'], 
                label='A-Share (Normalized)', color='#e74c3c', linewidth=2)
        ax2.plot(pd.to_datetime(df_hk_norm['trade_date']), df_hk_norm['close_norm'], 
                label='HK-Share (Normalized)', color='#3498db', linewidth=2)
        ax2.set_ylabel('Normalized Price (Base=100)', fontsize=12)
        ax2.set_title('Price Trend Comparison (Normalized for Trend Analysis)', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('reports/smic_price_comparison.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        img_comparison = base64.b64encode(open('reports/smic_price_comparison.png', 'rb').read()).decode('utf-8')
        print('     ✓ 价格对比图已保存')
    
except Exception as e:
    print(f'   ✗ 图表生成失败：{e}')
    import traceback
    traceback.print_exc()
    charts_generated = False

# ============================================================================
# 3. 计算统计指标
# ============================================================================
print('\n3. 计算统计指标...')

def calc_metrics(df, price_unit='CNY'):
    if df is None or len(df) == 0:
        return None
    
    latest = df.iloc[-1]
    latest_close = latest['close']
    
    # 计算涨跌
    if 'pct_chg' in df.columns:
        pct_change = latest['pct_chg']
        change = latest_close * pct_change / 100
    else:
        prev_close = df.iloc[-2]['close'] if len(df) > 1 else latest_close
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100 if prev_close != 0 else 0
    
    return {
        'latest_close': latest_close,
        'change': change,
        'pct_change': pct_change,
        'high_52w': df['high'].max(),
        'low_52w': df['low'].min(),
        'avg_vol': df['vol'].mean(),
        'latest_vol': latest['vol'],
        'record_count': len(df),
        'price_unit': price_unit
    }

metrics_a = calc_metrics(df_a, 'CNY')
metrics_hk = calc_metrics(df_hk, 'HKD')

# ============================================================================
# 4. 生成 HTML 看板
# ============================================================================
print('\n4. 生成 HTML 看板...')

# 最近 10 个交易日数据
recent_a = df_a.tail(10).iloc[::-1] if df_a is not None else pd.DataFrame()
recent_hk = df_hk.tail(10).iloc[::-1] if df_hk is not None else pd.DataFrame()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMIC A-Share vs HK-Share Comparison Analysis</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               background: #f5f7fa; color: #333; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        
        /* Header */
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 30px; border-radius: 12px; 
                     margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 14px; opacity: 0.9; }}
        
        /* Metric Cards */
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
                      gap: 15px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                            transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); 
                              box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
        .metric-card .label {{ font-size: 12px; color: #7f8c8d; margin-bottom: 8px; }}
        .metric-card .value {{ font-size: 24px; font-weight: bold; }}
        .metric-card .change {{ font-size: 14px; margin-top: 5px; }}
        .positive {{ color: #e74c3c; }}  /* Red = up (China convention) */
        .negative {{ color: #27ae60; }}  /* Green = down (China convention) */
        
        /* Comparison Table */
        .comparison-table {{ background: white; padding: 25px; border-radius: 12px; 
                             box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
        .comparison-table h2 {{ color: #2c3e50; margin-bottom: 20px; 
                                 padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #3498db; color: white; font-weight: bold; }}
        tr:hover {{ background: #f8f9fa; }}
        
        /* Chart Section */
        .chart-section {{ background: white; padding: 25px; border-radius: 12px; 
                           box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                           margin-bottom: 20px; }}
        .chart-section h2 {{ color: #2c3e50; margin-bottom: 20px; 
                              padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        .chart-img {{ text-align: center; margin: 20px 0; }}
        .chart-img img {{ max-width: 100%; height: auto; border-radius: 8px; }}
        
        /* Data Table */
        .data-table {{ background: white; padding: 25px; border-radius: 12px; 
                           box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }}
        .data-table h2 {{ color: #2c3e50; margin-bottom: 20px; 
                              padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        
        /* Grid Layout */
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 1024px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .metrics {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 22px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📈 SMIC A-Share vs HK-Share Comparison</h1>
            <div class="subtitle">STAR Market (688981.SH) vs Hong Kong Main Board (00981.HK) | Past 1 Year | Updated: {datetime.now().strftime('%Y-%m-%d')}</div>
        </div>
"""

# Add A-Share metric cards
if metrics_a is not None:
    html_content += f"""
        <!-- A-Share Metrics -->
        <div class="metrics">
            <div class="metric-card">
                <div class="label">A-Share Latest Close</div>
                <div class="value" style="color: {'#e74c3c' if metrics_a['change'] >= 0 else '#27ae60'};">
                    {metrics_a['latest_close']:.2f} {metrics_a['price_unit']}
                </div>
                <div class="change {'positive' if metrics_a['change'] >= 0 else 'negative'}">
                    {'+' if metrics_a['change'] >= 0 else ''}{metrics_a['change']:.2f} ({'+' if metrics_a['pct_change'] >= 0 else ''}{metrics_a['pct_change']:.2f}%)
                </div>
            </div>
            
            <div class="metric-card">
                <div class="label">A-Share 52W High</div>
                <div class="value">{metrics_a['high_52w']:.2f} {metrics_a['price_unit']}</div>
            </div>
            
            <div class="metric-card">
                <div class="label">A-Share 52W Low</div>
                <div class="value">{metrics_a['low_52w']:.2f} {metrics_a['price_unit']}</div>
            </div>
            
            <div class="metric-card">
                <div class="label">A-Share Avg Volume</div>
                <div class="value">{metrics_a['avg_vol']:.0f} lots</div>
            </div>
"""

# Add HK-Share metric cards
if metrics_hk is not None:
    html_content += f"""
            <div class="metric-card">
                <div class="label">HK-Share Latest Close</div>
                <div class="value" style="color: {'#e74c3c' if metrics_hk['change'] >= 0 else '#27ae60'};">
                    {metrics_hk['latest_close']:.2f} {metrics_hk['price_unit']}
                </div>
                <div class="change {'positive' if metrics_hk['change'] >= 0 else 'negative'}">
                    {'+' if metrics_hk['change'] >= 0 else ''}{metrics_hk['change']:.2f} ({'+' if metrics_hk['pct_change'] >= 0 else ''}{metrics_hk['pct_change']:.2f}%)
                </div>
            </div>
            
            <div class="metric-card">
                <div class="label">HK-Share 52W High</div>
                <div class="value">{metrics_hk['high_52w']:.2f} {metrics_hk['price_unit']}</div>
            </div>
            
            <div class="metric-card">
                <div class="label">HK-Share 52W Low</div>
                <div class="value">{metrics_hk['low_52w']:.2f} {metrics_hk['price_unit']}</div>
            </div>
            
            <div class="metric-card">
                <div class="label">HK-Share Avg Volume</div>
                <div class="value">{metrics_hk['avg_vol']:.0f} shares</div>
            </div>
"""

html_content += """
        </div>
"""

# Add comparison table
if metrics_a is not None and metrics_hk is not None:
    html_content += f"""
        <!-- Comparison Table -->
        <div class="comparison-table">
            <h2>📊 Key Metrics Comparison</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>A-Share (688981.SH)</th>
                    <th>HK-Share (00981.HK)</th>
                    <th>Difference</th>
                </tr>
                <tr>
                    <td><strong>Latest Close</strong></td>
                    <td>{metrics_a['latest_close']:.2f} CNY</td>
                    <td>{metrics_hk['latest_close']:.2f} HKD</td>
                    <td>—</td>
                </tr>
                <tr>
                    <td><strong>Daily Change (%)</strong></td>
                    <td class="{'positive' if metrics_a['pct_change'] >= 0 else 'negative'}">{'+' if metrics_a['pct_change'] >= 0 else ''}{metrics_a['pct_change']:.2f}%</td>
                    <td class="{'positive' if metrics_hk['pct_change'] >= 0 else 'negative'}">{'+' if metrics_hk['pct_change'] >= 0 else ''}{metrics_hk['pct_change']:.2f}%</td>
                    <td>{(metrics_a['pct_change'] - metrics_hk['pct_change']):.2f}%</td>
                </tr>
                <tr>
                    <td><strong>52W High</strong></td>
                    <td>{metrics_a['high_52w']:.2f} CNY</td>
                    <td>{metrics_hk['high_52w']:.2f} HKD</td>
                    <td>—</td>
                </tr>
                <tr>
                    <td><strong>52W Low</strong></td>
                    <td>{metrics_a['low_52w']:.2f} CNY</td>
                    <td>{metrics_hk['low_52w']:.2f} HKD</td>
                    <td>—</td>
                </tr>
                <tr>
                    <td><strong>Trading Days</strong></td>
                    <td>{metrics_a['record_count']} days (A-share)</td>
                    <td>{metrics_hk['record_count']} days (HK)</td>
                    <td>{metrics_a['record_count'] - metrics_hk['record_count']} days</td>
                </tr>
            </table>
            <p style="margin-top: 15px; color: #7f8c8d; font-size: 13px;">
                ⚠️ Note: A-share and HK-share have different trading hours. Price units are different (CNY vs HKD). Please compare with caution.
            </p>
        </div>
"""

# Add K-line charts (grid layout)
if charts_generated:
    html_content += """
        <!-- K-line Chart Comparison -->
        <div class="grid-2">
    """
    
    if img_a_kline:
        html_content += f"""
            <div class="chart-section">
                <h2>📊 A-Share K-line Chart (688981.SH)</h2>
                <div class="chart-img">
                    <img src="data:image/png;base64,{img_a_kline}" alt="A-Share K-line Chart">
                </div>
            </div>
        """
    
    if img_hk_kline:
        html_content += f"""
            <div class="chart-section">
                <h2>📊 HK-Share K-line Chart (00981.HK)</h2>
                <div class="chart-img">
                    <img src="data:image/png;base64,{img_hk_kline}" alt="HK-Share K-line Chart">
                </div>
            </div>
        """
    
    html_content += """
        </div>
    """

# Add price comparison chart
if img_comparison:
    html_content += f"""
        <!-- Price Comparison Chart -->
        <div class="chart-section">
            <h2>📈 Price Trend Comparison</h2>
            <div class="chart-img">
                <img src="data:image/png;base64,{img_comparison}" alt="Price Comparison Chart">
            </div>
            <p style="text-align: center; color: #7f8c8d; margin-top: 10px;">
                Top: Raw price comparison | Bottom: Normalized price (for trend analysis)
            </p>
        </div>
"""

# Add recent data tables (A-share + HK-share)
if not recent_a.empty:
    html_content += """
        <div class="grid-2">
    """
    
    # A-share recent data
    html_content += """
            <div class="data-table">
                <h2>📋 A-Share Recent 10 Trading Days</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Close</th>
                        <th>Change (%)</th>
                        <th>Volume</th>
                    </tr>
    """
    
    for _, row in recent_a.iterrows():
        pct = row['pct_chg'] if 'pct_chg' in df_a.columns else 0
        row_class = 'positive' if pct >= 0 else 'negative'
        html_content += f"""
                    <tr>
                        <td>{row['trade_date']}</td>
                        <td>{row['close']:.2f}</td>
                        <td class="{row_class}">{'+' if pct >= 0 else ''}{pct:.2f}%</td>
                        <td>{row['vol']:.0f}</td>
                    </tr>
        """
    
    html_content += """
                </table>
            </div>
    """
    
    # HK-share recent data
    if not recent_hk.empty:
        html_content += """
            <div class="data-table">
                <h2>📋 HK-Share Recent 10 Trading Days</h2>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Close</th>
                        <th>Change (%)</th>
                        <th>Volume</th>
                    </tr>
        """
        
        for _, row in recent_hk.iterrows():
            pct = row['pct_chg'] if 'pct_chg' in df_hk.columns else 0
            row_class = 'positive' if pct >= 0 else 'negative'
            html_content += f"""
                    <tr>
                        <td>{row['trade_date']}</td>
                        <td>{row['close']:.2f}</td>
                        <td class="{row_class}">{'+' if pct >= 0 else ''}{pct:.2f}%</td>
                        <td>{row['vol']:.0f}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
        """
    
    html_content += """
        </div>
    """

# Footer
html_content += f"""
        <hr style="margin: 40px 0; border: none; border-top: 1px solid #ecf0f1;">
        <p style="text-align: center; color: #95a5a6; font-size: 12px;">
            Data Source: Tushare Pro API & AKShare | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            <br>⚠️ Disclaimer: This dashboard is for reference only and does not constitute investment advice.
        </p>
    </div>
</body>
</html>"""

# Save HTML file
output_path = 'reports/smic_comparison_dashboard.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'   ✓ HTML dashboard saved to: {output_path}')

# ============================================================================
# 5. 保存元数据
# ============================================================================
print('\n5. 保存元数据...')

metadata = {
    'stocks': {
        'a_share': {
            'code': '688981.SH',
            'name': 'SMIC (A-Share)',
            'market': 'STAR Market',
            'currency': 'CNY',
            'data_range': {
                'start': df_a['trade_date'].min() if df_a is not None else None,
                'end': df_a['trade_date'].max() if df_a is not None else None
            },
            'record_count': len(df_a) if df_a is not None else 0,
            'latest_close': float(metrics_a['latest_close']) if metrics_a is not None else None,
            'pct_change': float(metrics_a['pct_change']) if metrics_a is not None else None
        },
        'hk_share': {
            'code': '00981.HK',
            'name': 'SMIC (HK-Share)',
            'market': 'Hong Kong Main Board',
            'currency': 'HKD',
            'data_range': {
                'start': df_hk['trade_date'].min() if df_hk is not None else None,
                'end': df_hk['trade_date'].max() if df_hk is not None else None
            },
            'record_count': len(df_hk) if df_hk is not None else 0,
            'latest_close': float(metrics_hk['latest_close']) if metrics_hk is not None else None,
            'pct_change': float(metrics_hk['pct_change']) if metrics_hk is not None else None
        }
    },
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

with open('data/smic/comparison_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print('   ✓ Metadata saved to: data/smic/comparison_metadata.json')

# ============================================================================
# Complete
# ============================================================================
print('\n' + '=' * 80)
print('✅ Task Completed!')
print('=' * 80)
print(f'\nOutput Files:')
print(f'  1. data/smic/688981_SH_daily.csv - A-Share data')
if df_hk is not None:
    print(f'  2. data/smic/00981_HK_daily.csv - HK-Share data')
    print(f'  3. data/smic/comparison_metadata.json - Metadata')
    print(f'  4. reports/smic_a_kline.png - A-Share K-line chart')
    print(f'  5. reports/smic_hk_kline.png - HK-Share K-line chart')
    print(f'  6. reports/smic_price_comparison.png - Price comparison chart')
    print(f'  7. reports/smic_comparison_dashboard.html - HTML comparison dashboard')
print(f'\nPlease view the HTML dashboard in the preview panel above 📊')
