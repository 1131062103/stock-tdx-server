#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare 龙虎榜数据获取工具
当前接入：东方财富-数据中心-龙虎榜单-龙虎榜详情

Author: Stock TDX MCP Server
Version: 1.0.0
"""

import argparse
import re
import sys
from contextlib import contextmanager
from typing import Optional

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@contextmanager
def full_pandas_display():
    """临时完整显示 DataFrame，避免 MCP 输出省略关键列。"""
    old_options = {
        "display.max_columns": pd.get_option("display.max_columns"),
        "display.width": pd.get_option("display.width"),
        "display.max_colwidth": pd.get_option("display.max_colwidth"),
    }
    try:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", None)
        yield
    finally:
        for key, value in old_options.items():
            pd.set_option(key, value)


class AKShareLHB:
    """AKShare 龙虎榜数据封装。"""

    @staticmethod
    def _check_date(value: str, name: str) -> None:
        if not re.fullmatch(r"\d{8}", value or ""):
            raise ValueError(f"{name} 必须为 YYYYMMDD 格式")

    def get_lhb_detail(self, start_date: str, end_date: str, limit: int = 50) -> Optional[pd.DataFrame]:
        """获取东方财富龙虎榜详情。"""
        self._check_date(start_date, "start_date")
        self._check_date(end_date, "end_date")
        if limit < 1 or limit > 1000:
            raise ValueError("limit 必须为 1-1000")

        try:
            import akshare as ak

            df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return None
            return df.head(limit)
        except Exception as exc:
            print(f"获取龙虎榜详情失败: {exc}", file=sys.stderr)
            return None


def setup_cli_parser():
    parser = argparse.ArgumentParser(description="AKShare 龙虎榜数据获取工具 v1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    detail_parser = subparsers.add_parser("detail", help="获取东方财富龙虎榜详情")
    detail_parser.add_argument("--start-date", required=True, help="开始日期 YYYYMMDD")
    detail_parser.add_argument("--end-date", required=True, help="结束日期 YYYYMMDD")
    detail_parser.add_argument("--limit", type=int, default=50, help="返回行数，1-1000")

    return parser


def main():
    parser = setup_cli_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    lhb = AKShareLHB()
    try:
        if args.command == "detail":
            df = lhb.get_lhb_detail(args.start_date, args.end_date, args.limit)
            if df is None:
                print("无数据")
                return
            with full_pandas_display():
                print(f"获取到 {len(df)} 条龙虎榜详情数据:")
                print(df)
    except KeyboardInterrupt:
        print("\n用户中断操作", file=sys.stderr)
    except Exception as exc:
        print(f"执行错误: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
