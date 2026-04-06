# stock-tdx-server

Termux 下可用的 TDX 股票数据 MCP 服务。

## 运行方式

本项目默认通过下面这组运行时调用 Python：

```bash
glibc-runner /data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/.venv/bin/python /data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/StockTDXHist.py
```

原因：在当前环境里直接省略 `glibc-runner` 可能出现请求头/兼容性问题。

## 环境变量

可选覆盖：

```bash
STOCK_TDX_PY_WRAPPER=glibc-runner
STOCK_TDX_PYTHON=/data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/.venv/bin/python
STOCK_TDX_SCRIPT=/data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/StockTDXHist.py
```

## 开发

```bash
npm run build
node build/index.js
```

## MCP 配置示例

```json
{
  "stock-tdx-server": {
    "disabled": false,
    "timeout": 60,
    "command": "node",
    "args": [
      "/data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/build/index.js"
    ],
    "env": {
      "STOCK_TDX_PY_WRAPPER": "glibc-runner",
      "STOCK_TDX_PYTHON": "/data/data/com.termux/files/usr/opt/MCP/stock-tdx-server/.venv/bin/python"
    }
  }
}
```

## 直接测试

```bash
glibc-runner ./.venv/bin/python StockTDXHist.py quote --stocks 1,600519
glibc-runner ./.venv/bin/python StockTDXHist.py kline --code 600519 --market 1 --ktype day --count 5
```
