#!/usr/bin/env python3
"""
数据获取脚本 - 510300.SH (沪深300ETF)
支持缓存机制和 API 失败回退
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import tushare as ts
import pandas as pd

# 加载 Token（从环境变量读取，不显示值）
load_dotenv()
token = os.getenv('TUSHARE_TOKEN')

if not token:
    print("✗ 错误：未找到 TUSHARE_TOKEN 环境变量")
    print("  请创建 .env 文件并添加：TUSHARE_TOKEN=your_token")
    exit(1)

print(f"✓ Token 已加载（长度：{len(token)} 字符）")

# 初始化 Tushare（直接传递 token，避免 ts.set_token() 的权限问题）
pro = ts.pro_api(token=token)

# 计算日期范围
end_date = datetime.now().strftime('%Y%m%d')
start_date_5y = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
start_date_1y = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

print(f"\n目标数据范围：")
print(f"  5 年：{start_date_5y} 至 {end_date}")
print(f"  1 年：{start_date_1y} 至 {end_date}")

# 缓存文件路径
RAW_CACHE = 'data/raw/510300_SH_daily_raw.csv'
META_CACHE = 'data/raw/510300_SH_daily_raw_meta.json'

def save_metadata(data_source, ts_code, start_date, end_date, frequency, adj, record_count, cache_type):
    """保存缓存元数据"""
    meta = {
        "data_source": data_source,
        "ts_code": ts_code,
        "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "start_date": start_date,
        "end_date": end_date,
        "frequency": frequency,
        "adj": adj,
        "record_count": record_count,
        "cache_type": cache_type
    }
    
    with open(META_CACHE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 元数据已保存至：{META_CACHE}")
    return meta

def load_cache():
    """加载缓存数据"""
    if os.path.exists(RAW_CACHE) and os.path.exists(META_CACHE):
        print(f"\n发现本地缓存：{RAW_CACHE}")
        
        # 读取元数据
        with open(META_CACHE, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f"  缓存时间：{meta['fetch_time']}")
        print(f"  数据范围：{meta['start_date']} 至 {meta['end_date']}")
        print(f"  记录数：{meta['record_count']}")
        
        # 读取数据
        df = pd.read_csv(RAW_CACHE)
        return df, meta
    return None, None

def fetch_real_data():
    """尝试获取实时数据"""
    print(f"\n{'='*60}")
    print("尝试获取实时数据...")
    print(f"{'='*60}\n")
    
    try:
        # 方法1：使用 fund_daily 接口（未复权）
        print("步骤 1/2：获取未复权原始数据...")
        df = pro.fund_daily(ts_code='510300.SH', start_date=start_date_5y, end_date=end_date)
        
        if df is not None and not df.empty:
            print(f"✓ 成功获取 5 年数据：{len(df)} 条记录")
            
            # 转换日期格式为 YYYY-MM-DD
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
            
            # 按日期升序排列
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 保存未复权数据
            df.to_csv(RAW_CACHE, index=False, encoding='utf-8')
            print(f"✓ 未复权数据已保存至：{RAW_CACHE}")
            
            # 保存元数据
            meta = save_metadata(
                data_source="Tushare Pro API",
                ts_code="510300.SH",
                start_date=df['trade_date'].min(),
                end_date=df['trade_date'].max(),
                frequency="daily",
                adj="None",
                record_count=len(df),
                cache_type="real_api"
            )
            
            return df, meta
        else:
            print("⚠ 5 年数据为空，尝试获取 1 年数据...")
            df = pro.fund_daily(ts_code='510300.SH', start_date=start_date_1y, end_date=end_date)
            
            if df is not None and not df.empty:
                print(f"✓ 成功获取 1 年数据：{len(df)} 条记录")
                
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
                df = df.sort_values('trade_date').reset_index(drop=True)
                
                df.to_csv(RAW_CACHE, index=False, encoding='utf-8')
                print(f"✓ 未复权数据已保存至：{RAW_CACHE}")
                
                meta = save_metadata(
                    data_source="Tushare Pro API",
                    ts_code="510300.SH",
                    start_date=df['trade_date'].min(),
                    end_date=df['trade_date'].max(),
                    frequency="daily",
                    adj="None",
                    record_count=len(df),
                    cache_type="real_api"
                )
                
                return df, meta
            else:
                print("✗ 无法获取数据（可能权限不足）")
                return None, None
                
    except Exception as e:
        print(f"✗ API 调用失败：{e}")
        return None, None

# 主流程
print(f"\n{'='*60}")
print("数据获取流程开始")
print(f"{'='*60}")

# 步骤1：尝试获取实时数据
df_real, meta_real = fetch_real_data()

if df_real is not None:
    print(f"\n{'='*60}")
    print("✓ 实时数据获取成功")
    print(f"{'='*60}")
    print(f"\n数据概况：")
    print(f"  记录数：{len(df_real)} 条")
    print(f"  时间范围：{df_real['trade_date'].min()} 至 {df_real['trade_date'].max()}")
    print(f"  数据来源：实时 API")
    
else:
    print(f"\n{'='*60}")
    print("⚠ API 失败，尝试加载缓存...")
    print(f"{'='*60}")
    
    # 步骤2：API 失败，尝试加载缓存
    df_cache, meta_cache = load_cache()
    
    if df_cache is not None:
        print(f"\n⚠ 使用缓存数据（最后更新：{meta_cache['fetch_time']}）")
        print(f"\n数据概况：")
        print(f"  记录数：{len(df_cache)} 条")
        print(f"  时间范围：{df_cache['trade_date'].min()} 至 {df_cache['trade_date'].max()}")
        print(f"  数据来源：缓存（非实时）")
        print(f"\n⚠ 请在分析中显著标记：缓存状态、最后数据日期")
        
        # 将缓存数据赋值给 df_real（保持后续代码统一）
        df_real = df_cache
        meta_real = meta_cache
        
    else:
        print(f"\n✗ 无缓存数据可用")
        print(f"  原因：API 调用失败且无本地缓存")
        print(f"  建议：检查网络连接、Token 权限，或手动创建缓存文件")
        exit(1)

# 步骤3：尝试获取前复权数据
print(f"\n{'='*60}")
print("尝试获取前复权数据...")
print(f"{'='*60}")

try:
    df_adj = ts.pro_bar(ts_code='510300.SH', adj='qfq', start_date=start_date_5y, end_date=end_date)
    
    if df_adj is not None and not df_adj.empty:
        print(f"✓ 成功获取前复权数据：{len(df_adj)} 条记录")
        
        # 转换日期格式
        df_adj['trade_date'] = pd.to_datetime(df_adj['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        df_adj = df_adj.sort_values('trade_date').reset_index(drop=True)
        
        # 保存前复权数据
        output_file = 'data/processed/510300_SH_daily_qfq.csv'
        df_adj.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ 前复权数据已保存至：{output_file}")
    else:
        print("⚠ 前复权数据为空（可能权限不足）")
        print("  建议：使用未复权数据进行初步分析")
        
except Exception as e:
    print(f"⚠ 前复权数据获取失败：{e}")

print(f"\n{'='*60}")
print("数据获取流程完成")
print(f"{'='*60}")
