# Task 01 - 量化数据引擎

## 项目概述

沪深300ETF（510300.SH）量化分析数据引擎，实现**可复现、可缓存、安全**的数据获取与分析流程。

## 目录结构

```
task01_data_engine/
├── README.md              # 项目说明（本文件）
├── spec.md                # 数据规范与接口说明
├── reflection.md          # 复盘与改进记录
├── data/
│   ├── raw/              # 未复权原始数据（CSV 缓存）
│   └── processed/        # 前复权分析数据（CSV）
├── notebooks/
│   └── task01_research.ipynb  # 研究 Notebook
├── dashboard/            # HTML 看板输出
└── outputs/              # 其他输出文件
```

## 快速开始

### 1. 配置 Token

在项目根目录创建 `.env` 文件（不提交）：

```bash
TUSHARE_TOKEN=your_token_here
```

> ⚠️ **Token 安全规则**：  
> - 从环境变量读取，不硬编码  
> - 不打印、不保存 Token 值到任何提交文件  
> - `.env` 已加入 `.gitignore`（如有）

### 2. 获取数据

```bash
cd task01_data_engine
python fetch_data.py
```

脚本会自动：
- 优先尝试实时 API（最近 5 年）
- API 失败时回退到本地缓存
- 显著标记缓存状态和最后数据日期

### 3. 启动分析

```bash
jupyter lab notebooks/task01_research.ipynb
```

## 数据说明

| 文件 | 说明 |
|------|------|
| `data/raw/510300_SH_daily_raw.csv` | 未复权原始数据，日期 YYYY-MM-DD |
| `data/processed/510300_SH_daily_qfq.csv` | 前复权数据，日期 YYYY-MM-DD |

## 技术规范

详见 [spec.md](spec.md)。

## 复盘记录

详见 [reflection.md](reflection.md)。

---

**最后更新**：2026-06-18  
**数据范围**：2021-06-21 至 2026-06-18（共 1211 个交易日）
