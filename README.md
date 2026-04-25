# stock-tdx-server

Termux 下可用的 TDX 股票数据 MCP 服务，提供 A 股行情、K线、分时、财务等数据查询能力。

## 功能特性

- 📈 K线数据（日/周/月/分钟/季度/年）
- 📊 实时行情
- 📋 股票列表
- ⏱️ 分时数据（实时 + 历史）
- 💹 分笔成交
- 💰 财务信息
- 🔄 除权除息
- 🏢 公司信息目录

## 运行方式

本项目默认通过下面这组运行时调用 Python：


原因：在当前环境里直接省略 `glibc-runner` 可能出现请求头/兼容性问题。

## 环境变量

可选覆盖：


## 开发


## MCP 配置示例


## 可用工具

### 1. get_kline
获取股票 K 线数据

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| code | string | 否 | "000001" | 股票代码 |
| market | integer | 否 | 0 | 0=深圳，1=上海 |
| ktype | string | 否 | "day" | K线类型：day/week/month/5min/15min/30min/60min/1min/quarter/year |
| count | integer | 否 | 10 | 数量（1-1000） |

### 2. get_index_kline
获取指数 K 线数据

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| code | string | 否 | "000001" | 指数代码 |
| market | integer | 否 | 1 | 0=深圳，1=上海 |
| ktype | string | 否 | "day" | K线类型 |
| count | integer | 否 | 10 | 数量（1-1000） |

### 3. get_quotes
获取股票实时行情

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| stocks | array | 是 | 格式 ["market,code"]，例如 ["0,000001", "1,600519"]，最多 50 个 |

### 4. get_stock_list
获取股票列表

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| market | integer | 否 | 0 | 0=深圳，1=上海 |
| start | integer | 否 | 0 | 起始位置 |

### 5. get_minute_data
获取分时数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| market | integer | 是 | 0=深圳，1=上海 |
| code | string | 是 | 股票代码 |

### 6. get_history_minute_data
获取历史分时数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| market | integer | 是 | 0=深圳，1=上海 |
| code | string | 是 | 股票代码 |
| date | integer | 是 | 日期 YYYYMMDD |

### 7. get_transaction_data
获取分笔成交数据

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| market | integer | 是 | - | 0=深圳，1=上海 |
| code | string | 是 | - | 股票代码 |
| start | integer | 否 | 0 | 起始位置 |
| count | integer | 否 | 30 | 数量（1-100） |

### 8. get_finance_info
获取财务信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| market | integer | 是 | 0=深圳，1=上海 |
| code | string | 是 | 股票代码 |

### 9. get_xdxr_info
获取除权除息信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| market | integer | 是 | 0=深圳，1=上海 |
| code | string | 是 | 股票代码 |

### 10. get_company_info_category
获取公司信息目录

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| market | integer | 是 | 0=深圳，1=上海 |
| code | string | 是 | 股票代码 |

## 支持的市场范围

- **沪市 (market=1)**：600/601/603/605/688 开头
- **深市 (market=0)**：000/001/002/003/004/300 开头
- **注意**：新三板、北交所多数不支持

## 直接测试 Python 脚本


## 版本

v1.1.0-termux
