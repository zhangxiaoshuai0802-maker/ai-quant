# spec.md - 数据规范与接口说明

## 1. 数据源

| 项目 | 说明 |
|------|------|
| 数据源 | Tushare Pro API |
| 标的代码 | `510300.SH`（华泰柏瑞沪深300ETF）|
| 接口 | `pro.fund_daily()`（未复权）、`ts.pro_bar(adj='qfq')`（前复权）|
| 频率 | 日线 |
| 复权口径 | 前复权（qfq）|

## 2. 数据文件规范

### 2.1 未复权原始数据

**文件路径**：`data/raw/510300_SH_daily_raw.csv`

**字段说明**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ts_code` | str | TS代码（如 `510300.SH`）|
| `trade_date` | str | 交易日期（格式：`YYYY-MM-DD`）|
| `pre_close` | float | 昨收价 |
| `open` | float | 开盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价 |
| `change` | float | 价格变动 |
| `pct_chg` | float | 涨跌幅（%）|
| `vol` | float | 成交量（手）|
| `amount` | float | 成交额（千元）|

**保存规则**：
- 不修改 Tushare 返回的原始字段值
- 日期格式统一为 `YYYY-MM-DD`
- 按 `trade_date` 升序排列
- 编码：UTF-8

### 2.2 前复权数据

**文件路径**：`data/processed/510300_SH_daily_qfq.csv`

**字段说明**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `ts_code` | str | TS代码 |
| `trade_date` | str | 交易日期（格式：`YYYY-MM-DD`）|
| `open` | float | 前复权开盘价 |
| `high` | float | 前复权最高价 |
| `low` | float | 前复权最低价 |
| `close` | float | 前复权收盘价 |
| `vol` | float | 成交量（手）|
| `amount` | float | 成交额（千元）|

**保存规则**：
- 使用 Tushare 官方前复权接口或复权因子计算
- 日期格式统一为 `YYYY-MM-DD`
- 按 `trade_date` 升序排列
- 编码：UTF-8

## 3. 缓存机制

### 3.1 缓存策略

| 场景 | 行为 |
|------|------|
| API 可用 | 请求实时数据，更新本地缓存 |
| API 失败 + 有缓存 | 读取缓存继续，显著标记缓存状态 |
| API 失败 + 无缓存 | 停止真实数据分析，报告原因 |

### 3.2 缓存元数据

每次成功获取数据时，同时保存元数据文件：

**文件路径**：`data/raw/510300_SH_daily_raw_meta.json`

**内容**：
```json
{
  "data_source": "Tushare Pro API",
  "ts_code": "510300.SH",
  "fetch_time": "2026-06-18 17:00:00",
  "start_date": "2021-06-21",
  "end_date": "2026-06-18",
  "frequency": "daily",
  "adj": "None",
  "record_count": 1211,
  "cache_type": "real_api"
}
```

## 4. Token 安全规范

| 规则 | 说明 |
|------|------|
| 读取方式 | 从环境变量 `TUSHARE_TOKEN` 读取 |
| 禁止行为 | 不打印、不保存到提交文件、不硬编码 |
| 配置文件 | 使用 `.env` 文件（已加入 `.gitignore`）|
| 验证 | 仅验证 Token 是否存在，不验证值 |

## 5. 数据获取范围

| 优先级 | 时间范围 | 条件 |
|--------|----------|------|
| 1 | 最近 5 年 | Token 权限允许 |
| 2 | 最近 1 年 | 权限不足时退到 1 年 |
| 3 | 报错 | 无数据且无缓存 |

## 6. 禁止行为

- ❌ 随机生成行情数据
- ❌ 使用示例数据冒充真实数据
- ❌ 硬编码 Token
- ❌ 修改 Tushare 返回的原始字段值

---

**版本**：v1.0  
**最后更新**：2026-06-18
