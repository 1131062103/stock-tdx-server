#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

interface StockToolArgs {
  code?: string;
  market?: number;
  ktype?: string;
  count?: number;
  stocks?: string[];
  start?: number;
  date?: number;
}

type ToolDef = readonly [
  name: string,
  description: string,
  properties: Record<string, unknown>,
  required: string[],
];

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const runtime = {
  python: process.env.STOCK_TDX_PYTHON || path.join(root, ".venv", "bin", "python"),
  script: process.env.STOCK_TDX_SCRIPT || path.join(root, "StockTDXHist.py"),
  timeoutMs: Number(process.env.STOCK_TDX_TIMEOUT_MS || 30_000),
  env: { ...process.env, PYTHONIOENCODING: "utf-8" },
};

const marketInfo = `支持范围：\n沪市 market=1；深市 market=0。\n常见代码：沪市 600/601/603/605/688；深市 000/001/002/003/004/300。\n新三板、北交所多数不支持。`;

const ktypes = ["day", "week", "month", "quarter", "year", "1min", "5min", "15min", "30min", "60min"];
const stockCode = { type: "string", pattern: "^[0-9]{6}$", description: "6位证券代码" };
const market = { type: "integer", enum: [0, 1], description: "0=深圳 1=上海" };
const count1000 = { type: "integer", minimum: 1, maximum: 1000, default: 10 };
const start = { type: "integer", minimum: 0, default: 0 };

const toolDefs: ToolDef[] = [
  ["get_kline", "获取股票K线数据", { code: { ...stockCode, default: "000001" }, market: { ...market, default: 0 }, ktype: { type: "string", enum: ktypes, default: "day" }, count: count1000 }, []],
  ["get_index_kline", "获取指数K线数据", { code: { ...stockCode, default: "000001" }, market: { ...market, default: 1 }, ktype: { type: "string", enum: ktypes, default: "day" }, count: count1000 }, []],
  ["get_quotes", "获取股票实时行情", { stocks: { type: "array", items: { type: "string", pattern: "^[01],[0-9]{6}$" }, minItems: 1, maxItems: 50 } }, ["stocks"]],
  ["get_stock_list", "获取股票列表", { market: { ...market, default: 0 }, start }, []],
  ["get_minute_data", "获取分时数据", { market, code: stockCode }, ["market", "code"]],
  ["get_history_minute_data", "获取历史分时数据", { market, code: stockCode, date: { type: "integer", description: "YYYYMMDD" } }, ["market", "code", "date"]],
  ["get_transaction_data", "获取分笔成交数据", { market, code: stockCode, start, count: { type: "integer", minimum: 1, maximum: 100, default: 30 } }, ["market", "code"]],
  ["get_finance_info", "获取财务信息", { market, code: stockCode }, ["market", "code"]],
  ["get_xdxr_info", "获取除权除息信息", { market, code: stockCode }, ["market", "code"]],
  ["get_company_info_category", "获取公司信息目录", { market, code: stockCode }, ["market", "code"]],
];

const tools = toolDefs.map(([name, description, properties, required]) => ({
  name,
  description,
  inputSchema: { type: "object", properties, required },
}));

function assertRequired(args: Record<string, unknown>, fields: string[]) {
  for (const field of fields) {
    if (args[field] === undefined || args[field] === null || args[field] === "") throw new Error(`缺少参数: ${field}`);
  }
}

function assertRange(name: string, value: number | undefined, min: number, max: number) {
  if (value === undefined) return;
  if (!Number.isInteger(value) || value < min || value > max) throw new Error(`${name} 必须是 ${min}-${max} 的整数`);
}

function validate(args: StockToolArgs, required: string[]) {
  assertRequired(args as Record<string, unknown>, required);
  if (args.market !== undefined && ![0, 1].includes(args.market)) throw new Error("market 必须为 0 或 1");
  if (args.code !== undefined && !/^\d{6}$/.test(args.code)) throw new Error("code 必须为6位数字");
  if (args.ktype !== undefined && !ktypes.includes(args.ktype)) throw new Error(`ktype 不支持: ${args.ktype}`);
  assertRange("count", args.count, 1, 1000);
  assertRange("start", args.start, 0, Number.MAX_SAFE_INTEGER);
  if (args.stocks && (!Array.isArray(args.stocks) || args.stocks.some((s) => !/^[01],\d{6}$/.test(s)))) {
    throw new Error('stocks 格式必须为 ["0,000001", "1,600519"]');
  }
}

async function runPython(args: string[]) {
  return new Promise<string>((resolve, reject) => {
    const child = spawn(runtime.python, [runtime.script, ...args], { env: runtime.env });
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`执行超时: ${runtime.timeoutMs}ms`));
    }, runtime.timeoutMs);

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data) => (stdout += data));
    child.stderr.on("data", (data) => (stderr += data));
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(new Error(`无法启动 Python: ${error.message}`));
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      code === 0 ? resolve(stdout.trim()) : reject(new Error(`Python执行失败(${code}): ${stderr || stdout}`));
    });
  });
}

const handlers: Record<string, (a: StockToolArgs) => Promise<string>> = {
  get_kline: ({ code = "000001", market = 0, ktype = "day", count = 10 }) => runPython(["kline", "--code", code, "--market", String(market), "--ktype", ktype, "--count", String(count)]),
  get_index_kline: ({ code = "000001", market = 1, ktype = "day", count = 10 }) => runPython(["index_kline", "--code", code, "--market", String(market), "--ktype", ktype, "--count", String(count)]),
  get_quotes: ({ stocks = [] }) => runPython(["quote", "--stocks", ...stocks]),
  get_stock_list: ({ market = 0, start = 0 }) => runPython(["list", "--market", String(market), "--start", String(start)]),
  get_minute_data: ({ market, code }) => runPython(["minute", "--market", String(market), "--code", String(code)]),
  get_history_minute_data: ({ market, code, date }) => runPython(["history_minute", "--market", String(market), "--code", String(code), "--date", String(date)]),
  get_transaction_data: ({ market, code, start = 0, count = 30 }) => runPython(["transaction", "--market", String(market), "--code", String(code), "--start", String(start), "--count", String(count)]),
  get_finance_info: ({ market, code }) => runPython(["finance", "--market", String(market), "--code", String(code)]),
  get_xdxr_info: ({ market, code }) => runPython(["xdxr", "--market", String(market), "--code", String(code)]),
  get_company_info_category: ({ market, code }) => runPython(["company_info", "--market", String(market), "--code", String(code)]),
};

const server = new Server({ name: "stock-tdx-server", version: "1.1.1" }, { capabilities: { resources: {}, tools: {} } });

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{ uri: "stock://markets/info", mimeType: "text/plain", name: "股票市场信息", description: "支持的市场与代码范围" }],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri !== "stock://markets/info") throw new Error(`资源未找到: ${request.params.uri}`);
  return { contents: [{ uri: request.params.uri, mimeType: "text/plain", text: marketInfo }] };
});

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const args = (request.params.arguments || {}) as StockToolArgs;
  const handler = handlers[request.params.name];
  const def = toolDefs.find(([name]) => name === request.params.name);
  if (!handler || !def) throw new Error(`未知工具: ${request.params.name}`);

  try {
    validate(args, def[3]);
    const text = await handler(args);
    return { content: [{ type: "text", text: text || "无数据" }] };
  } catch (error) {
    return { content: [{ type: "text", text: `错误: ${error instanceof Error ? error.message : String(error)}` }], isError: true };
  }
});

await server.connect(new StdioServerTransport());
