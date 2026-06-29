#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 akshare 获取中芯国际港股（00981.HK）数据
"""

import os
import pandas as pd
from datetime import datetime, timedelta

print('=' * 80)
print('使用 akshare 获取中芯国际港股（00981.HK）数据')
print('=' * 80)

try:
    import akshare as ak
    
    # 港股代码格式：00981（不带 .HK）
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    print(f'\n时间范围：{start_date} 至 {end_date}')
    print(f'股票代码：00981（港股）')
    
    # 获取港股日线数据
    # akshare 港股接口：stock_hk_hist(symbol="00981", period="daily", start_date="20250101", end_date="20251231")
    df_hk = ak.stock_hk_hist(
        symbol="00981",
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=""
    )
    
    if df_hk is not None and not df_hk.empty:
        print(f'\n✓ 港股数据获取成功')
        print(f'  记录数：{len(df_hk)} 条')
        print(f'  列名：{list(df_hk.columns)}')
        print(f'\n前 5 行：')
        print(df_hk.head())
        
        # 保存数据
        os.makedirs('data/smic', exist_ok=True)
        df_hk.to_csv('data/smic/00981_HK_daily.csv', index=False, encoding='utf-8-sig')
        print(f'\n  已保存至：data/smic/00981_HK_daily.csv')
    else:
        print('\n✗ 港股数据获取失败：返回为空')
        
except Exception as e:
    print(f'\n✗ 数据获取失败：{e}')
    import traceback
    traceback.print_exc()
