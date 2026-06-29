#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成 HTML 对比报告，将图片嵌入为 base64 数据 URI
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import logging
import base64
from io import BytesIO

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

# 创建输出目录
os.makedirs('reports/multi_source', exist_ok=True)

print('=' * 80)
print('生成三个数据源的对比可视化图表（嵌入版）')
print('=' * 80)

# ============================================================================
# 读取数据
# ============================================================================
df = pd.read_csv('data/multi_source/merged_comparison.csv')
df['date_str'] = pd.to_datetime(df['date_str'])
valid = df.dropna(subset=['tushare_close', 'akshare_raw_close', 'yfinance_close'])

# ============================================================================
# 图 1: 三个数据源的收盘价对比（时间序列）
# ============================================================================
print('\n1. 生成收盘价对比图...')

fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(valid['date_str'], valid['tushare_close'], label='Tushare', alpha=0.8, linewidth=2)
ax.plot(valid['date_str'], valid['akshare_raw_close'], label='Akshare (未复权)', alpha=0.7, linewidth=1.5, linestyle='--')
ax.plot(valid['date_str'], valid['yfinance_close'], label='Yfinance', alpha=0.7, linewidth=1.5, linestyle=':')

ax.set_title('510300.SH 收盘价对比（三个数据源）', fontsize=16, fontweight='bold')
ax.set_xlabel('日期', fontsize=12)
ax.set_ylabel('收盘价（元）', fontsize=12)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)

plt.tight_layout()
# 保存为 base64
buffer1 = BytesIO()
plt.savefig(buffer1, format='png', dpi=100, bbox_inches='tight')
plt.close()
img1_base64 = base64.b64encode(buffer1.getvalue()).decode('utf-8')
buffer1.close()

print('  ✓ 图 1 已生成')

# ============================================================================
# 图 2: 价格差异对比
# ============================================================================
print('\n2. 生成价格差异对比图...')

fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# 计算差异
diff_tu_ak = valid['tushare_close'] - valid['akshare_raw_close']
diff_tu_yf = valid['tushare_close'] - valid['yfinance_close']
diff_ak_qfq = valid['akshare_raw_close'] - valid['akshare_qfq_close']

# 子图 1: Tushare vs Akshare
axes[0].plot(valid['date_str'], diff_tu_ak, color='blue', alpha=0.7)
axes[0].axhline(y=0, color='black', linestyle='-', alpha=0.3)
axes[0].set_title('Tushare vs Akshare (未复权) 价格差异', fontsize=14)
axes[0].set_ylabel('差异（元）', fontsize=12)
axes[0].grid(True, alpha=0.3)

# 子图 2: Tushare vs Yfinance
axes[1].plot(valid['date_str'], diff_tu_yf, color='red', alpha=0.7)
axes[1].axhline(y=0, color='black', linestyle='-', alpha=0.3)
axes[1].set_title('Tushare vs Yfinance 价格差异', fontsize=14)
axes[1].set_ylabel('差异（元）', fontsize=12)
axes[1].grid(True, alpha=0.3)

# 子图 3: Akshare 未复权 vs 前复权
axes[2].plot(valid['date_str'], diff_ak_qfq, color='green', alpha=0.7)
axes[2].axhline(y=0, color='black', linestyle='-', alpha=0.3)
axes[2].set_title('Akshare 未复权 vs 前复权 价格差异', fontsize=14)
axes[2].set_xlabel('日期', fontsize=12)
axes[2].set_ylabel('差异（元）', fontsize=12)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
# 保存为 base64
buffer2 = BytesIO()
plt.savefig(buffer2, format='png', dpi=100, bbox_inches='tight')
plt.close()
img2_base64 = base64.b64encode(buffer2.getvalue()).decode('utf-8')
buffer2.close()

print('  ✓ 图 2 已生成')

# ============================================================================
# 图 3: 分布对比（直方图）
# ============================================================================
print('\n3. 生成价格分布对比图...')

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# 子图 1: Tushare vs Akshare
axes[0].hist(diff_tu_ak, bins=50, alpha=0.7, color='blue', edgecolor='black')
axes[0].axvline(x=0, color='black', linestyle='--', linewidth=2)
axes[0].set_title('Tushare vs Akshare (未复权)\n价格差异分布', fontsize=14)
axes[0].set_xlabel('差异（元）', fontsize=12)
axes[0].set_ylabel('频数', fontsize=12)
axes[0].grid(True, alpha=0.3)

# 子图 2: Tushare vs Yfinance
axes[1].hist(diff_tu_yf, bins=50, alpha=0.7, color='red', edgecolor='black')
axes[1].axvline(x=0, color='black', linestyle='--', linewidth=2)
axes[1].set_title('Tushare vs Yfinance\n价格差异分布', fontsize=14)
axes[1].set_xlabel('差异（元）', fontsize=12)
axes[1].set_ylabel('频数', fontsize=12)
axes[1].grid(True, alpha=0.3)

# 子图 3: Akshare 未复权 vs 前复权
axes[2].hist(diff_ak_qfq, bins=50, alpha=0.7, color='green', edgecolor='black')
axes[2].axvline(x=0, color='black', linestyle='--', linewidth=2)
axes[2].set_title('Akshare 未复权 vs 前复权\n价格差异分布', fontsize=14)
axes[2].set_xlabel('差异（元）', fontsize=12)
axes[2].set_ylabel('频数', fontsize=12)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
# 保存为 base64
buffer3 = BytesIO()
plt.savefig(buffer3, format='png', dpi=100, bbox_inches='tight')
plt.close()
img3_base64 = base64.b64encode(buffer3.getvalue()).decode('utf-8')
buffer3.close()

print('  ✓ 图 3 已生成')

# ============================================================================
# 生成 HTML 报告（嵌入图片）
# ============================================================================
print('\n4. 生成 HTML 对比报告（嵌入图片）...')

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>510300.SH 多数据源对比报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .summary ul {{ list-style: none; padding-left: 0; }}
        .summary li {{ padding: 8px 0; border-bottom: 1px solid #bdc3c7; }}
        .summary li:last-child {{ border-bottom: none; }}
        .chart {{ margin: 30px 0; text-align: center; }}
        .chart img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; font-weight: bold; }}
        tr:hover {{ background: #f5f5f5; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 510300.SH（沪深300ETF）多数据源对比报告</h1>
        
        <div class="summary">
            <h2>🔍 数据概览</h2>
            <ul>
                <li><strong>标的：</strong>510300.SH（华泰柏瑞沪深300ETF）</li>
                <li><strong>时间范围：</strong>2021-06-21 至 2026-06-18</li>
                <li><strong>数据频率：</strong>日线（交易日）</li>
                <li><strong>对比数据源：</strong>Tushare、Akshare、Yfinance</li>
            </ul>
        </div>
        
        <div class="success">
            <h2>✅ 主要发现</h2>
            <ul>
                <li><strong>Tushare 与 Akshare (未复权) 数据完全一致</strong>（差异为0）</li>
                <li><strong>Yfinance 数据与 Tushare/Akshare 存在系统性差异</strong>（平均差异约 0.24 元）</li>
                <li><strong>Akshare 前复权数据有效</strong>，可用于技术分析</li>
            </ul>
        </div>
        
        <h2>📈 图表分析</h2>
        
        <div class="chart">
            <h3>图 1: 收盘价对比（时间序列）</h3>
            <img src="data:image/png;base64,{img1_base64}" alt="收盘价对比">
            <p>Tushare 与 Akshare 的未复权数据完全重叠，Yfinance 数据存在明显差异。</p>
        </div>
        
        <div class="chart">
            <h3>图 2: 价格差异时间序列</h3>
            <img src="data:image/png;base64,{img2_base64}" alt="价格差异">
            <p>上图显示各数据源间的价格差异随时间的变化。</p>
        </div>
        
        <div class="chart">
            <h3>图 3: 价格差异分布</h3>
            <img src="data:image/png;base64,{img3_base64}" alt="价格差异分布">
            <p>Tushare vs Akshare 的差异分布集中在 0 附近，说明两者数据一致。</p>
        </div>
        
        <h2>📋 详细数据对比</h2>
        
        <table>
            <tr>
                <th>对比项</th>
                <th>平均差异（元）</th>
                <th>最大差异（元）</th>
                <th>差异 > 0.01 的交易日数</th>
            </tr>
            <tr>
                <td>Tushare vs Akshare (未复权)</td>
                <td>0.000000</td>
                <td>0.000000</td>
                <td>0</td>
            </tr>
            <tr>
                <td>Tushare vs Yfinance</td>
                <td>0.237872</td>
                <td>0.503222</td>
                <td>1111</td>
            </tr>
            <tr>
                <td>Akshare (未复权) vs 前复权</td>
                <td>0.248369</td>
                <td>0.419000</td>
                <td>N/A</td>
            </tr>
        </table>
        
        <div class="warning">
            <h2>⚠️ 注意事项</h2>
            <ul>
                <li><strong>Yfinance 数据差异原因：</strong>可能是数据来源不同、复权方式不同或数据更新延迟</li>
                <li><strong>推荐用法：</strong>对于 A股 ETF，建议使用 Tushare 或 Akshare，两者数据一致且更新及时</li>
                <li><strong>复权数据：</strong>Akshare 支持前复权和后复权，可直接获取</li>
            </ul>
        </div>
        
        <h2>📁 相关文件</h2>
        <ul>
            <li><code>data/multi_source/merged_comparison.csv</code> - 合并对比数据</li>
            <li><code>data/multi_source/final_comparison_report.json</code> - 汇总报告</li>
            <li><code>reports/multi_source/</code> - 可视化图表</li>
        </ul>
        
        <hr style="margin: 40px 0;">
        <p style="text-align: center; color: #7f8c8d;">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

# 保存 HTML 报告
with open('reports/multi_source/comparison_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('  ✓ 已保存至：reports/multi_source/comparison_report.html')
print('\n  ℹ️ 图片已嵌入 HTML，可离线打开查看')

print('\n' + '=' * 80)
print('可视化图表和报告生成完成')
print('=' * 80)
