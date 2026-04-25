#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import * as path from "path";
import { fileURLToPath } from "url";

interface StockToolArgs {
  code?: string;
  market?: number;
  ktype?: string;
  count?: number;
  stocks?: string[];
  start?: number;
  date?: number;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, "..");
const scriptPath = path.join(projectRoot, "StockTDXHist.py");
const pythonPath = path.join(projectRoot, ".venv", "bin", "python");

const RUNTIME = {
  python: process.env.STOCK_TDX_PYTHON || pythonPath,
  script: process.env.STOCK_TDX_SCRIPT || scriptPath,
  env: {
    ...process.env,
    PYTHONIOENCODING: "utf-8",
  },
};

const MARKET_INFO = `支持范围：\n沪市 market=1；深市 market=0。\n常见代码：沪市 600/601/603/605/688；深市 000/001/002/003/004/300。\n新三板、北交所多数不支持。`;

const TOOL_DEFINITIONS = [
  ["get_kline", "获取股票K线数据", {
    code: { type: "string", description: "股票代码", default: "000001" },
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1], default: 0 },
    ktype: { type: "string", description: "K线类型", enum: ["day", "week", "month", "5min", "15min", "30min", "60min", "1min", "quarter", "year"], default: "day" },
    count: { type: "integer", description: "数量", minimum: 1, maximum: 1000, default: 10 },
  }, ["code"]],
  ["get_index_kline", "获取指数K线数据", {
    code: { type: "string", description: "指数代码", default: "000001" },
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1], default: 1 },
    ktype: { type: "string", description: "K线类型", enum: ["day", "week", "month", "5min", "15min", "30min", "60min", "1min", "quarter", "year"], default: "day" },
    count: { type: "integer", description: "数量", minimum: 1, maximum: 1000, default: 10 },
  }, ["code"]],
  ["get_quotes", "获取股票实时行情", {
    stocks: { type: "array", description: "格式 [\"market,code\"]", items: { type: "string", pattern: "^[01],[0-9]{6}$" }, minItems: 1, maxItems: 50 },
  }, ["stocks"]],
  ["get_stock_list", "获取股票列表", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1], default: 0 },
    start: { type: "integer", description: "起始位置", minimum: 0, default: 0 },
  }, []],
  ["get_minute_data", "获取分时数据", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
  }, ["market", "code"]],
  ["get_history_minute_data", "获取历史分时数据", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
    date: { type: "integer", description: "日期 YYYYMMDD" },
  }, ["market", "code", "date"]],
  ["get_transaction_data", "获取分笔成交数据", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
    start: { type: "integer", description: "起始位置", minimum: 0, default: 0 },
    count: { type: "integer", description: "数量", minimum: 1, maximum: 100, default: 30 },
  }, ["market", "code"]],
  ["get_finance_info", "获取财务信息", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
  }, ["market", "code"]],
  ["get_xdxr_info", "获取除权除息信息", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
  }, ["market", "code"]],
  ["get_company_info_category", "获取公司信息目录", {
    market: { type: "integer", description: "0=深圳 1=上海", enum: [0, 1] },
    code: { type: "string", description: "股票代码" },
  }, ["market", "code"]],
].map(([name, description, properties, required]) => ({
  name,
  description,
  inputSchema: { type: "object", properties, required },
}));

function requireArgs(args: Record<string, unknown>, fields: string[]) {
  for (const field of fields) {
    if (args[field] === undefined || args[field] === null || args[field] === "") {
      throw new Error(`缺少参数: ${field}`);
    }
  }
}

async function executePythonScript(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(RUNTIME.python, [RUNTIME.script, ...args], { env: RUNTIME.env });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data) => { stdout += data.toString(); });
    child.stderr.on("data", (data) => { stderr += data.toString(); });

    child.on("close", (code) => {
      if (code === 0) return resolve(stdout.trim());
      reject(new Error(`Python执行失败(${code}): ${stderr || stdout}`));
    });

    child.on("error", (error) => {
      reject(new Error(`无法启动运行时: ${error.message}`));
    });
  });
}

const TOOL_HANDLERS: Record<string, (args: StockToolArgs) => Promise<string>> = {
  get_kline: async ({ code = "000001", market = 0, ktype = "day", count = 10 }) =>
    executePythonScript(["kline", "--code", code, "--market", String(market), "--ktype", ktype, "--count", String(count)]),

  get_index_kline: async ({ code = "000001", market = 1, ktype = "day", count = 10 }) =>
    executePythonScript(["index_kline", "--code", code, "--market", String(market), "--ktype", ktype, "--count", String(count)]),

  get_quotes: async ({ stocks }) => {
    if (!Array.isArray(stocks) || stocks.length === 0) throw new Error("stocks 必须为非空数组");
    return executePythonScript(["quote", "--stocks", ...stocks]);
  },

  get_stock_list: async ({ market = 0, start = 0 }) =>
    executePythonScript(["list", "--market", String(market), "--start", String(start)]),

  get_minute_data: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code"]);
    return executePythonScript(["minute", "--market", String(args.market), "--code", String(args.code)]);
  },

  get_history_minute_data: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code", "date"]);
    return executePythonScript(["history_minute", "--market", String(args.market), "--code", String(args.code), "--date", String(args.date)]);
  },

  get_transaction_data: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code"]);
    return executePythonScript(["transaction", "--market", String(args.market), "--code", String(args.code), "--start", String(args.start ?? 0), "--count", String(args.count ?? 30)]);
  },

  get_finance_info: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code"]);
    return executePythonScript(["finance", "--market", String(args.market), "--code", String(args.code)]);
  },

  get_xdxr_info: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code"]);
    return executePythonScript(["xdxr", "--market", String(args.market), "--code", String(args.code)]);
  },

  get_company_info_category: async (args) => {
    requireArgs(args as Record<string, unknown>, ["market", "code"]);
    return executePythonScript(["company_info", "--market", String(args.market), "--code", String(args.code)]);
  },
};

const server = new Server(
  { name: "stock-tdx-server", version: "1.1.0-termux" },
  { capabilities: { resources: {}, tools: {} } }
);

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{
    uri: "stock://markets/info",
    mimeType: "text/plain",
    name: "股票市场信息",
    description: "支持的市场与代码范围",
  }],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const url = new URL(request.params.uri);
  if (url.pathname !== "/markets/info") throw new Error(`资源未找到: ${request.params.uri}`);
  return { contents: [{ uri: request.params.uri, mimeType: "text/plain", text: MARKET_INFO }] };
});

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOL_DEFINITIONS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;
  const handler = TOOL_HANDLERS[name];
  if (!handler) throw new Error(`未知工具: ${name}`);

  try {
    const result = await handler(args as StockToolArgs);
    return { content: [{ type: "text", text: result }] };
  } catch (error) {
    return {
      content: [{ type: "text", text: `错误: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
