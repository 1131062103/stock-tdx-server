#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通达信股票数据获取工具
基于pytdx库提供股票实时行情、历史行情、股票相关信息等数据

支持的股票代码范围：
- 沪市（market=1）：600、601、603、605、688（科创板）、900（B股）、110（国债）、204（回购）等
- 深市（market=0）：000（主板）、001、002（中小板）、003、004、300（创业板）、200（B股）、080、131（债券）等
- 新三板（如43开头）、北交所（83/87开头）等大多不支持

Author: Stock TDX MCP Server
Version: 1.0.0
"""

import pandas as pd
from pytdx.hq import TdxHq_API
from pytdx.params import TDXParams
from typing import Optional, Literal, List, Tuple, Union
import argparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from contextlib import contextmanager


class TDXStock:
    """通达信股票数据获取封装类"""

    # 默认服务器列表
    DEFAULT_SERVERS = [
        {"ip": "180.153.18.170", "port": 7709},
        {"ip": "115.238.56.198", "port": 7709},
        {"ip": "115.238.90.165", "port": 7709},
        {"ip": "218.75.126.9", "port": 7709},
    ]

    def __init__(self, servers=None):
        """初始化TDX连接参数"""
        self.servers = servers or self.DEFAULT_SERVERS
        self.current_server_index = 0

    @contextmanager
    def _get_api(self):
        """API连接管理器，支持自动切换服务器"""
        api = TdxHq_API()
        connected = False
        
        for i, server in enumerate(self.servers):
            try:
                if api.connect(server["ip"], server["port"]):
                    self.current_server_index = i
                    connected = True
                    break
            except Exception as e:
                continue
        
        if not connected:
            print("错误：所有服务器连接失败", file=sys.stderr)
            yield None
            return
            
        try:
            yield api
        finally:
            try:
                api.disconnect()
            except:
                pass

    def _get_bars(self, api_method: str, ktype_map: dict, code: str, market: int, ktype: str, count: int) -> Optional[pd.DataFrame]:
        """通用K线数据获取（股票/指数）"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = []
                batches = (count + 799) // 800
                
                for i in range(batches):
                    batch_data = getattr(api, api_method)(
                        ktype_map.get(ktype, 9), 
                        market, 
                        code, 
                        (batches-1-i)*800, 
                        min(800, count - i*800)
                    )
                    if batch_data:
                        data.extend(batch_data)
                
                if not data:
                    return None
                    
                df = pd.DataFrame(data)[['datetime', 'open', 'close', 'high', 'low', 'vol', 'amount']].rename(columns={'vol': 'volume'})
                df['volume'] /= 100  # 转换为手
                df = df.sort_values('datetime', ascending=False).reset_index(drop=True)
                return df[:count]
                
            except Exception as e:
                print(f"获取数据失败: {e}", file=sys.stderr)
                return None

    def get_kline(self, code: str = "000001", market: int = 0,
                  ktype: Literal['day', 'week', 'month', 'quarter', 'year', '5min', '15min', '30min', '60min', '1min'] = 'day',
                  count: int = 10) -> Optional[pd.DataFrame]:
        """获取股票K线数据"""
        ktype_map = {
            'day': 9, 'week': 5, 'month': 6, 'quarter': 10, 'year': 11,
            '5min': 0, '15min': 1, '30min': 2, '60min': 3, '1min': 8
        }
        return self._get_bars('get_security_bars', ktype_map, code, market, ktype, count)

    def get_index_kline(self, code: str = "000001", market: int = 1,
                        ktype: Literal['day', 'week', 'month', 'quarter', 'year', '5min', '15min', '30min', '60min', '1min'] = 'day',
                        count: int = 10) -> Optional[pd.DataFrame]:
        """获取指数K线数据"""
        ktype_map = {
            'day': 9, 'week': 5, 'month': 6, 'quarter': 10, 'year': 11,
            '5min': 0, '15min': 1, '30min': 2, '60min': 3, '1min': 8
        }
        return self._get_bars('get_index_bars', ktype_map, code, market, ktype, count)

    def get_quotes(self, stocks: List[Tuple[int, str]]) -> Optional[pd.DataFrame]:
        """获取多只股票实时行情"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_security_quotes(stocks)
                if not data:
                    print("未获取到行情数据", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取行情失败: {e}", file=sys.stderr)
                return None

    def get_stock_list(self, market: int = 0, start: int = 0) -> Optional[pd.DataFrame]:
        """获取股票列表"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_security_list(market, start)
                return pd.DataFrame(data) if data else None
            except Exception as e:
                print(f"获取股票列表失败: {e}", file=sys.stderr)
                return None

    def get_minute_data(self, market: int, code: str) -> Optional[pd.DataFrame]:
        """获取分时数据"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_minute_time_data(market, code)
                if not data:
                    print("未获取到分时数据", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取分时数据失败: {e}", file=sys.stderr)
                return None

    def get_history_minute_data(self, market: int, code: str, date: int) -> Optional[pd.DataFrame]:
        """获取历史分时数据"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_history_minute_time_data(market, code, date)
                if not data:
                    print("未获取到历史分时数据", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取历史分时数据失败: {e}", file=sys.stderr)
                return None

    def get_transaction_data(self, market: int, code: str, start: int = 0, count: int = 30) -> Optional[pd.DataFrame]:
        """获取分笔成交数据"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_transaction_data(market, code, start, count)
                if not data:
                    print("未获取到分笔成交数据", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取分笔成交数据失败: {e}", file=sys.stderr)
                return None

    def get_xdxr_info(self, market: int, code: str) -> Optional[pd.DataFrame]:
        """获取除权除息信息"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_xdxr_info(market, code)
                if not data:
                    print("未获取到除权除息信息", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取除权除息信息失败: {e}", file=sys.stderr)
                return None

    def get_finance_info(self, market: int, code: str) -> Optional[pd.DataFrame]:
        """获取财务信息"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_finance_info(market, code)
                if not data:
                    print("未获取到财务信息", file=sys.stderr)
                    return None
                    
                # 处理不同格式的返回数据
                if isinstance(data, dict):
                    return pd.DataFrame([data])
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取财务信息失败: {e}", file=sys.stderr)
                return None

    def get_company_info_category(self, market: int, code: str) -> Optional[pd.DataFrame]:
        """获取公司信息目录"""
        with self._get_api() as api:
            if api is None:
                return None
                
            try:
                data = api.get_company_info_category(market, code)
                if not data:
                    print("未获取到公司信息目录", file=sys.stderr)
                    return None
                return pd.DataFrame(data)
            except Exception as e:
                print(f"获取公司信息目录失败: {e}", file=sys.stderr)
                return None


def setup_cli_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="通达信股票数据获取工具 v1.0.0")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # K线数据命令
    kline_parser = subparsers.add_parser('kline', help='获取股票K线数据')
    kline_parser.add_argument("--code", type=str, default="000001", help="股票代码")
    kline_parser.add_argument("--market", type=int, default=0, help="市场代码, 0: 深圳, 1: 上海")
    kline_parser.add_argument("--ktype", type=str, default="day", 
                             choices=['day', 'week', 'month', 'quarter', 'year', '5min', '15min', '30min', '60min', '1min'],
                             help="K线类型")
    kline_parser.add_argument("--count", type=int, default=10, help="获取K线数量")

    # 指数K线命令
    index_kline_parser = subparsers.add_parser('index_kline', help='获取指数K线数据')
    index_kline_parser.add_argument("--code", type=str, default="000001", help="指数代码")
    index_kline_parser.add_argument("--market", type=int, default=1, help="市场代码, 0: 深圳, 1: 上海")
    index_kline_parser.add_argument("--ktype", type=str, default="day",
                                    choices=['day', 'week', 'month', 'quarter', 'year', '5min', '15min', '30min', '60min', '1min'],
                                    help="K线类型")
    index_kline_parser.add_argument("--count", type=int, default=10, help="获取K线数量")

    # 实时行情命令
    quote_parser = subparsers.add_parser('quote', help='获取股票实时行情')
    quote_parser.add_argument("--stocks", type=str, nargs='+', required=True,
                             help="股票代码，格式：market,code 如：0,000001 1,600519")

    # 股票列表命令
    list_parser = subparsers.add_parser('list', help='获取股票列表')
    list_parser.add_argument("--market", type=int, default=0, help="市场代码")
    list_parser.add_argument("--start", type=int, default=0, help="起始位置")

    # 分时数据命令
    minute_parser = subparsers.add_parser('minute', help='获取分时数据')
    minute_parser.add_argument("--market", type=int, required=True, help="市场代码")
    minute_parser.add_argument("--code", type=str, required=True, help="股票代码")

    # 历史分时数据命令
    hist_minute_parser = subparsers.add_parser('history_minute', help='获取历史分时数据')
    hist_minute_parser.add_argument("--market", type=int, required=True, help="市场代码")
    hist_minute_parser.add_argument("--code", type=str, required=True, help="股票代码")
    hist_minute_parser.add_argument("--date", type=int, required=True, help="日期，格式如20231201")

    # 分笔成交数据命令
    transaction_parser = subparsers.add_parser('transaction', help='获取分笔成交数据')
    transaction_parser.add_argument("--market", type=int, required=True, help="市场代码")
    transaction_parser.add_argument("--code", type=str, required=True, help="股票代码")
    transaction_parser.add_argument("--start", type=int, default=0, help="起始位置")
    transaction_parser.add_argument("--count", type=int, default=30, help="获取数量")

    # 财务信息命令
    finance_parser = subparsers.add_parser('finance', help='获取财务信息')
    finance_parser.add_argument("--market", type=int, required=True, help="市场代码")
    finance_parser.add_argument("--code", type=str, required=True, help="股票代码")

    # 除权除息信息命令
    xdxr_parser = subparsers.add_parser('xdxr', help='获取除权除息信息')
    xdxr_parser.add_argument("--market", type=int, required=True, help="市场代码")
    xdxr_parser.add_argument("--code", type=str, required=True, help="股票代码")

    # 公司信息目录命令
    company_parser = subparsers.add_parser('company_info', help='获取公司信息目录')
    company_parser.add_argument("--market", type=int, required=True, help="市场代码")
    company_parser.add_argument("--code", type=str, required=True, help="股票代码")

    return parser


def main():
    """主函数"""
    parser = setup_cli_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 创建TDXStock实例
    tdx = TDXStock()

    try:
        # 根据命令执行相应功能
        if args.command == 'kline':
            df = tdx.get_kline(args.code, args.market, args.ktype, args.count)
            if df is not None:
                print(f"获取到 {len(df)} 条K线数据:")
                print(df)

        elif args.command == 'index_kline':
            df = tdx.get_index_kline(args.code, args.market, args.ktype, args.count)
            if df is not None:
                print(f"获取到 {len(df)} 条指数K线数据:")
                print(df)

        elif args.command == 'quote':
            stocks = []
            for stock in args.stocks:
                try:
                    market, code = stock.split(',')
                    stocks.append((int(market), code))
                except ValueError:
                    print(f"错误：股票代码格式不正确: {stock}", file=sys.stderr)
                    return
            
            df = tdx.get_quotes(stocks)
            if df is not None:
                print("实时行情:")
                print(df)

        elif args.command == 'list':
            df = tdx.get_stock_list(args.market, args.start)
            if df is not None:
                print(f"股票列表 (市场:{args.market}):")
                print(df)

        elif args.command == 'minute':
            df = tdx.get_minute_data(args.market, args.code)
            if df is not None:
                print(f"分时数据 ({args.market},{args.code}):")
                print(df)

        elif args.command == 'history_minute':
            df = tdx.get_history_minute_data(args.market, args.code, args.date)
            if df is not None:
                print(f"历史分时数据 ({args.market},{args.code},{args.date}):")
                print(df)

        elif args.command == 'transaction':
            df = tdx.get_transaction_data(args.market, args.code, args.start, args.count)
            if df is not None:
                print(f"分笔成交数据 ({args.market},{args.code}):")
                print(df)

        elif args.command == 'finance':
            df = tdx.get_finance_info(args.market, args.code)
            if df is not None:
                print(f"财务信息 ({args.market},{args.code}):")
                print(df)

        elif args.command == 'xdxr':
            df = tdx.get_xdxr_info(args.market, args.code)
            if df is not None:
                print(f"除权除息信息 ({args.market},{args.code}):")
                print(df)

        elif args.command == 'company_info':
            df = tdx.get_company_info_category(args.market, args.code)
            if df is not None:
                print(f"公司信息目录 ({args.market},{args.code}):")
                print(df)

    except KeyboardInterrupt:
        print("\n用户中断操作", file=sys.stderr)
    except Exception as e:
        print(f"执行错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()


# 使用示例:
"""
基本用法：
python StockTDXHist.py kline --code 600519 --market 1 --ktype week --count 20
python StockTDXHist.py quote --stocks 0,000001 1,600519
python StockTDXHist.py list --market 1 --start 0
python StockTDXHist.py minute --market 1 --code 600519
python StockTDXHist.py finance --market 0 --code 000001
python StockTDXHist.py history_minute --market 1 --code 600519 --date 20231201
python StockTDXHist.py transaction --market 1 --code 600519 --count 50
python StockTDXHist.py xdxr --market 1 --code 600519
python StockTDXHist.py company_info --market 1 --code 600519
"""