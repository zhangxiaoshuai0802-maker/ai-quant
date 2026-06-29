#!/usr/bin/env python3
"""
数据质量检查脚本
生成：
1. outputs/data_quality_report.json
2. outputs/anomaly_records.csv
3. outputs/field_dictionary.csv
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime

# 加载数据
print("=" * 70)
print("数据质量检查")
print("=" * 70)

df = pd.read_csv('data/raw/510300_SH_daily_raw.csv')
print(f"\n已加载数据：{len(df)} 条记录")

# 转换日期列
df['trade_date'] = pd.to_datetime(df['trade_date'])

# =====================================================================
# 1. 必需字段检查
# =====================================================================
print("\n" + "=" * 70)
print("1. 必需字段检查")
print("=" * 70)

required_fields = ['trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'pct_chg', 'vol', 'amount']
actual_fields = list(df.columns)

field_mapping = {
    'ts_code': '标的代码',
    'trade_date': '交易日期',
    'pre_close': '昨收价',
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'change': '价格变动',
    'pct_chg': '涨跌幅（%）',
    'vol': '成交量（手）',
    'amount': '成交额（千元）'
}

missing_fields = []
print(f"\n【实际字段列表】")
for i, field in enumerate(actual_fields, 1):
    print(f"  {i}. {field}")

print(f"\n【字段映射说明】")
for field in required_fields:
    if field in actual_fields:
        print(f"  ✓ {field}: {field_mapping.get(field, '无说明')}")
    else:
        print(f"  ✗ {field}: 缺失")
        missing_fields.append(field)

if len(missing_fields) == 0:
    print(f"\n✓ 所有必需字段均已存在")
else:
    print(f"\n⚠️ 缺失必需字段：{missing_fields}")

# =====================================================================
# 2. 日期检查
# =====================================================================
print("\n" + "=" * 70)
print("2. 日期检查")
print("=" * 70)

# 检查日期是否升序
is_ascending = df['trade_date'].is_monotonic_increasing
print(f"\n【日期排序】")
if is_ascending:
    print('  ✓ 日期按升序排列')
else:
    print('  ⚠️ 日期未按升序排列')

# 记录数和起止日期
print(f"\n【记录数】")
print(f"  {len(df)} 条")

print(f"\n【起止日期】")
start_date = df['trade_date'].min()
end_date = df['trade_date'].max()
print(f"  开始：{start_date.date()}")
print(f"  结束：{end_date.date()}")

# 计算实际交易日数
actual_days = (end_date - start_date).days + 1
print(f"\n【日期范围】")
print(f"  日期范围：{actual_days} 天（含周末）")
print(f"  实际交易日：{len(df)} 天")
print(f"  周末和非交易日：{actual_days - len(df)} 天（正常）")

# =====================================================================
# 3. 重复交易日期检查
# =====================================================================
print("\n" + "=" * 70)
print("3. 重复交易日期检查")
print("=" * 70)

duplicates = df[df.duplicated(subset=['trade_date'], keep=False)]
dup_count = duplicates.shape[0]

print(f"\n【重复日期数量】")
print(f"  {dup_count} 条")

if dup_count > 0:
    print(f"\n【重复日期明细】")
    print(duplicates[['trade_date', 'open', 'high', 'low', 'close']])
else:
    print('\n✓ 无重复交易日期')

# =====================================================================
# 4. 缺失值检查
# =====================================================================
print("\n" + "=" * 70)
print("4. 缺失值检查")
print("=" * 70)

missing_stats = []
for col in df.columns:
    missing_count = df[col].isna().sum()
    missing_rate = (missing_count / len(df)) * 100
    missing_stats.append({'field': col, 'missing_count': missing_count, 'missing_rate': missing_rate})

print(f"\n【各字段缺失情况】")
print(f"  {'字段':<20} {'缺失数量':<15} {'缺失率（%）':<15}")
print(f"  {'-'*50}")
for stat in missing_stats:
    if stat['missing_count'] > 0:
        print(f"  {stat['field']:<20} {stat['missing_count']:<15} {stat['missing_rate']:.2f}")

# 检查关键字段是否缺失
critical_fields = ['open', 'high', 'low', 'close', 'vol', 'amount']
critical_missing = [f for f in critical_fields if f in df.columns and df[f].isna().sum() > 0]

print(f"\n【关键字段缺失检查】")
if len(critical_missing) == 0:
    print('  ✓ 所有关键字段无缺失值')
else:
    print(f'  ⚠️ 关键字段缺失：{critical_missing}')

print('\n⚠️ 说明：')
print('  - 周末和非交易日不属于缺失值（ETF 仅在交易日有数据）')
print('  - 完整交易日检查需要交易日历，并考虑停牌情况')

# =====================================================================
# 5. OHLC 逻辑检查
# =====================================================================
print("\n" + "=" * 70)
print("5. OHLC 逻辑检查")
print("=" * 70)

ohlc_violations = []

for i, row in df.iterrows():
    violations = []
    
    # 规则1：high >= max(open, close, low)
    if row['high'] < max(row['open'], row['close'], row['low']):
        violations.append(f"high < max(open, close, low) ({row['high']:.3f} < {max(row['open'], row['close'], row['low']):.3f})")
    
    # 规则2：low <= min(open, close, high)
    if row['low'] > min(row['open'], row['close'], row['high']):
        violations.append(f"low > min(open, close, high) ({row['low']:.3f} > {min(row['open'], row['close'], row['high']):.3f})")
    
    # 规则3：high >= low
    if row['high'] < row['low']:
        violations.append(f"high < low ({row['high']:.3f} < {row['low']:.3f})")
    
    if len(violations) > 0:
        ohlc_violations.append({'index': i, 'date': row['trade_date'], 'violations': violations})

print(f"\n【OHLC 违规数量】")
print(f"  {len(ohlc_violations)} 条")

if len(ohlc_violations) > 0:
    print(f"\n【OHLC 违规明细（前10条）】")
    for v in ohlc_violations[:10]:
        print(f"  日期：{v['date'].date()}")
        for violation in v['violations']:
            print(f"    - {violation}")
else:
    print('\n✓ 无 OHLC 逻辑违规')

# =====================================================================
# 6. 价格和成交量合理性检查
# =====================================================================
print("\n" + "=" * 70)
print("6. 价格和成交量合理性检查")
print("=" * 70)

price_violations = []
volume_violations = []

# 价格检查
price_fields = ['open', 'high', 'low', 'close', 'pre_close']
for field in price_fields:
    if field in df.columns:
        invalid_prices = df[df[field] <= 0]
        if len(invalid_prices) > 0:
            print(f"\n⚠️ {field} 存在 {len(invalid_prices)} 条价格 <= 0 的记录")
            price_violations.extend(invalid_prices.index.tolist())
        else:
            print(f"✓ {field}: 所有价格 > 0")

# 成交量检查
print(f"\n【成交量检查】")
if 'vol' in df.columns:
    negative_vol = df[df['vol'] < 0]
    if len(negative_vol) > 0:
        print(f"⚠️ vol 存在 {len(negative_vol)} 条负值记录")
        volume_violations.extend(negative_vol.index.tolist())
    else:
        print('✓ vol: 所有成交量 >= 0')

# 成交额检查
print(f"\n【成交额检查】")
if 'amount' in df.columns:
    negative_amount = df[df['amount'] < 0]
    if len(negative_amount) > 0:
        print(f"⚠️ amount 存在 {len(negative_amount)} 条负值记录")
        volume_violations.extend(negative_amount.index.tolist())
    else:
        print('✓ amount: 所有成交额 >= 0')

# =====================================================================
# 7. 日收益率异常检查
# =====================================================================
print("\n" + "=" * 70)
print("7. 日收益率异常检查")
print("=" * 70)

# 计算日收益率（根据收盘价）
df['daily_return_calc'] = df['close'].pct_change() * 100  # 百分比

# 标记绝对收益超过 11% 的异常候选
anomaly_threshold = 11.0
anomalies = df[df['daily_return_calc'].abs() > anomaly_threshold]

print(f"\n【日收益率统计】")
print(df['daily_return_calc'].describe())

print(f"\n【异常候选（|日收益率| > {anomaly_threshold}%）】")
print(f"  数量：{len(anomalies)} 条")

if len(anomalies) > 0:
    print(f"\n【异常候选明细】")
    print(anomalies[['trade_date', 'open', 'high', 'low', 'close', 'daily_return_calc']].head(20))
    print(f"\n⚠️ 注意：异常候选需要解释，不能直接等同于错误")
    print(f"  可能原因：")
    print(f"  - 市场极端行情（暴涨/暴跌）")
    print(f"  - 分红除权（未复权数据）")
    print(f"  - 数据错误（需进一步核验）")
else:
    print('✓ 无异常候选')

# =====================================================================
# 8. 数据自带 pct_chg 与自行计算收益比较
# =====================================================================
print("\n" + "=" * 70)
print("8. pct_chg 与自行计算收益比较")
print("=" * 70)

if 'pct_chg' in df.columns:
    # 计算差异
    df['return_diff'] = df['pct_chg'] - df['daily_return_calc']
    
    print(f"\n【差异统计】")
    print(df['return_diff'].describe())
    
    # 找出差异较大的记录
    large_diff = df[df['return_diff'].abs() > 0.01]  # 差异超过 0.01%
    
    print(f"\n【较大差异记录（|差异| > 0.01%）】")
    print(f"  数量：{len(large_diff)} 条")
    
    if len(large_diff) > 0:
        print(f"\n【差异明细（前10条）】")
        print(large_diff[['trade_date', 'close', 'pct_chg', 'daily_return_calc', 'return_diff']].head(10))
    
    print(f"\n【差异原因说明】")
    print(f"  1. 原始/复权口径差异：")
    print(f"     - pct_chg 是基于未复权收盘价计算的")
    print(f"     - daily_return_calc 也是基于未复权收盘价计算的")
    print(f"     - 理论上应该一致，差异可能来自四舍五入")
    print(f"  2. 前复权数据差异：")
    print(f"     - 如果使用前复权数据计算收益率，与 pct_chg 会有显著差异")
    print(f"     - 前复权数据已经过复权调整，收益率计算会不同")
    
else:
    print('⚠️ 数据中无 pct_chg 字段，无法比较')

# =====================================================================
# 生成输出文件
# =====================================================================
print("\n" + "=" * 70)
print("生成输出文件")
print("=" * 70)

# 创建 outputs 目录（如果不存在）
os.makedirs('outputs', exist_ok=True)

# =====================================================================
# 1. 生成 data_quality_report.json
# =====================================================================
print('\n【1/3】生成 data_quality_report.json...')

# 收集质量检查结果
quality_report = {
    'quality_summary': {
        'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_records': int(len(df)),
        'date_range': {
            'start': str(df['trade_date'].min().date()),
            'end': str(df['trade_date'].max().date())
        },
        'missing_fields': missing_fields,
        'duplicate_records': int(dup_count),
        'ohlc_violations': len(ohlc_violations),
        'price_violations': len(price_violations),
        'volume_violations': len(volume_violations),
        'anomaly_candidates': int(len(anomalies))
    },
    'data_meta': {
        'data_source': 'Tushare Pro API',
        'ts_code': '510300.SH',
        'frequency': 'daily',
        'adj': 'None (未复权)',
        'fields': list(df.columns)
    },
    'api_cache_status': {
        'status': 'real_api_success' if os.path.exists('data/raw/510300_SH_daily_raw_meta.json') else 'unknown',
        'cache_age_days': None,
        'cache_file': 'data/raw/510300_SH_daily_raw_meta.json' if os.path.exists('data/raw/510300_SH_daily_raw_meta.json') else None
    },
    'quality_conclusion': {
        'can_proceed': True,
        'red_lines': [],
        'warnings': [],
        'notes': []
    }
}

# 动态质量结论
conclusion = quality_report['quality_conclusion']

# 检查红线
if len(missing_fields) > 0:
    conclusion['red_lines'].append(f"关键字段缺失：{missing_fields}")
    conclusion['can_proceed'] = False

if len(ohlc_violations) > 0:
    conclusion['red_lines'].append(f"OHLC 逻辑违规：{len(ohlc_violations)} 条")
    conclusion['can_proceed'] = False

if len(price_violations) > 0:
    conclusion['red_lines'].append(f"价格异常：{len(price_violations)} 条")
    conclusion['can_proceed'] = False

if len(volume_violations) > 0:
    conclusion['warnings'].append(f"成交量异常：{len(volume_violations)} 条")

if len(anomalies) > 0:
    conclusion['warnings'].append(f"日收益率异常候选：{len(anomalies)} 条（需解释）")

if len(missing_fields) == 0 and len(ohlc_violations) == 0 and len(price_violations) == 0:
    conclusion['notes'].append('数据质量基本通过，可以进入下一阶段研究')

# 保存 JSON
with open('outputs/data_quality_report.json', 'w', encoding='utf-8') as f:
    json.dump(quality_report, f, ensure_ascii=False, indent=2)

print('  ✓ 已保存：outputs/data_quality_report.json')

# =====================================================================
# 2. 生成 anomaly_records.csv
# =====================================================================
print('\n【2/3】生成 anomaly_records.csv...')

with open('outputs/anomaly_records.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['trade_date', 'rule', 'value', 'description'])
    
    # 写入异常记录（如果有）
    if len(anomalies) > 0:
        for _, row in anomalies.iterrows():
            writer.writerow([
                row['trade_date'].date(),
                '|日收益率| > 11%',
                f"{row['daily_return_calc']:.2f}%",
                '日收益率异常候选，需进一步解释'
            ])
    
    # 写入 OHLC 违规（如果有）
    if len(ohlc_violations) > 0:
        for v in ohlc_violations:
            for violation in v['violations']:
                writer.writerow([
                    v['date'].date(),
                    violation,
                    'N/A',
                    'OHLC 逻辑违规'
                ])

print('  ✓ 已保存：outputs/anomaly_records.csv')

# =====================================================================
# 3. 生成 field_dictionary.csv
# =====================================================================
print('\n【3/3】生成 field_dictionary.csv...')

field_dict = [
    ['ts_code', 'TS代码', 'str', '-', '标的唯一标识'],
    ['trade_date', '交易日期', 'str/datetime', '-', '交易日'],
    ['pre_close', '昨收价', 'float', '元', '前一交易日收盘价'],
    ['open', '开盘价', 'float', '元', '当日第一笔成交价'],
    ['high', '最高价', 'float', '元', '当日最高成交价'],
    ['low', '最低价', 'float', '元', '当日最低成交价'],
    ['close', '收盘价', 'float', '元', '当日最后一笔成交价'],
    ['change', '价格变动', 'float', '元', '收盘价 - 昨收价'],
    ['pct_chg', '涨跌幅', 'float', '%', '(收盘价 - 昨收价) / 昨收价 * 100%'],
    ['vol', '成交量', 'float', '手', '当日成交总量（1手=100份）'],
    ['amount', '成交额', 'float', '千元', '当日成交总金额']
]

with open('outputs/field_dictionary.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['field', 'chinese_meaning', 'type', 'unit', 'usage'])
    writer.writerows(field_dict)

print('  ✓ 已保存：outputs/field_dictionary.csv')

# =====================================================================
# 显示质量结论
# =====================================================================
print("\n" + "=" * 70)
print("质量结论")
print("=" * 70)

conclusion = quality_report['quality_conclusion']

print(f"\n【能否进入下一阶段研究】")
if conclusion['can_proceed']:
    print('  ✓ 可以进入下一阶段研究')
else:
    print('  ✗ 存在红线问题，需先解决才能进入下一阶段')

if len(conclusion['red_lines']) > 0:
    print(f"\n【红线问题】")
    for red in conclusion['red_lines']:
        print(f"  ✗ {red}")

if len(conclusion['warnings']) > 0:
    print(f"\n【警告】")
    for warning in conclusion['warnings']:
        print(f"  ⚠️ {warning}")

if len(conclusion['notes']) > 0:
    print(f"\n【备注】")
    for note in conclusion['notes']:
        print(f"  ℹ️ {note}")

print("\n" + "=" * 70)
print("✓ 所有输出文件已生成")
print("=" * 70)
