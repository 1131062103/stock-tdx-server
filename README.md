# stock-tdx-server

Termux / Linux 可用的通达信（TDX）A 股行情 MCP 服务。通过 Node.js MCP server 调用 Python `pytdx`，提供 K 线、实时行情、分时、分笔、财务、除权除息等查询。

## 功能

- 股票/指数 K 线：日、周、月、季度、年、1/5/15/30/60 分钟
- 实时行情、多股票批量报价
- 股票列表
- 实时/历史分时
- 分笔成交、财务信息、除权除息、公司信息目录
- AKShare 东方财富龙虎榜详情

## 安装

```bash
git clone https://github.com/1131062103/stock-tdx-server.git
cd stock-tdx-server
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build
```

> 默认使用 `.venv/bin/python` 执行 `StockTDXHist.py`。如需自定义运行时，见环境变量。

## MCP 配置

```json
{
  "mcpServers": {
    "stock-tdx-server": {
      "command": "node",
      "args": ["/path/to/stock-tdx-server/build/index.js"],
      "env": {
        "STOCK_TDX_PYTHON": "/path/to/stock-tdx-server/.venv/bin/python"
      }
    }
  }
}
```

## 环境变量

- `STOCK_TDX_PYTHON`：Python 解释器路径，默认 `项目根/.venv/bin/python`
- `STOCK_TDX_SCRIPT`：Python 脚本路径，默认 `项目根/StockTDXHist.py`
- `STOCK_TDX_TIMEOUT_MS`：通达信工具调用超时，默认 `30000`
- `STOCK_LHB_SCRIPT`：龙虎榜脚本路径，默认 `项目根/StockAKShareLHB.py`
- `STOCK_LHB_TIMEOUT_MS`：龙虎榜工具调用超时，默认 `60000`

## 可用工具

| 工具 | 说明 | 主要参数 |
|---|---|---|
| `get_kline` | 股票 K 线 | `code`, `market`, `ktype`, `count` |
| `get_index_kline` | 指数 K 线 | `code`, `market`, `ktype`, `count` |
| `get_quotes` | 实时行情 | `stocks: ["0,000001", "1,600519"]` |
| `get_stock_list` | 股票列表 | `market`, `start` |
| `get_minute_data` | 实时分时 | `market`, `code` |
| `get_history_minute_data` | 历史分时 | `market`, `code`, `date` |
| `get_transaction_data` | 分笔成交 | `market`, `code`, `start`, `count` |
| `get_finance_info` | 财务信息 | `market`, `code` |
| `get_xdxr_info` | 除权除息 | `market`, `code` |
| `get_company_info_category` | 公司信息目录 | `market`, `code` |
| `get_lhb_detail` | 东方财富龙虎榜详情 | `start_date`, `end_date`, `limit` |

参数说明：`market=0` 深圳，`market=1` 上海；`ktype=day/week/month/quarter/year/1min/5min/15min/30min/60min`。

## 直接测试

```bash
. .venv/bin/activate
python StockTDXHist.py kline --code 600519 --market 1 --ktype day --count 5
python StockTDXHist.py quote --stocks 0,000001 1,600519
python StockAKShareLHB.py detail --start-date 20240417 --end-date 20240430 --limit 5
```

## 注意

- 通达信数据来自公开行情接口，龙虎榜数据来自 AKShare/东方财富接口，稳定性取决于上游连通性。
- 沪市常见代码：600/601/603/605/688；深市常见代码：000/001/002/003/004/300。新三板、北交所多数不支持。

## License

MIT
