#!/usr/bin/env python3
"""
cli.py
------
Command-line entry point for the Binance Futures Testnet trading bot.

Examples:
    # Market order
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit order
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 45000

    # Bonus: Stop-Limit order
    python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT \\
        --quantity 0.01 --price 44000 --stop-price 44500

Credentials are read from environment variables (or a local .env file):
    BINANCE_TESTNET_API_KEY
    BINANCE_TESTNET_API_SECRET
"""

import argparse
import os
import sys

from bot.logging_config import setup_logger
from bot.validators import validate_order_request, ValidationError
from bot.client import BinanceFuturesTestnetClient, BinanceClientError
from bot.orders import OrderManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set another way


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument("--type", dest="order_type", required=True,
                         choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
                         help="Order type")
    parser.add_argument("--quantity", required=True, help="Order quantity (base asset units)")
    parser.add_argument("--price", required=False, help="Limit price (required for LIMIT / STOP_LIMIT)")
    parser.add_argument("--stop-price", dest="stop_price", required=False,
                         help="Stop trigger price (required for STOP_LIMIT)")
    parser.add_argument("-v", "--verbose", action="store_true",
                         help="Print DEBUG-level detail to the console as well as the log file")
    return parser


def print_summary(title: str, fields: dict) -> None:
    print(f"\n--- {title} ---")
    width = max(len(k) for k in fields)
    for k, v in fields.items():
        print(f"  {k.ljust(width)} : {v}")


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logger = setup_logger(verbose=args.verbose)

    # 1. Validate input -------------------------------------------------
    try:
        order = validate_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        logger.error("Input validation failed: %s", exc)
        print(f"\n[FAILED] Invalid input: {exc}")
        return 1

    print_summary("Order Request", {
        "Symbol": order["symbol"],
        "Side": order["side"],
        "Type": order["order_type"],
        "Quantity": order["quantity"],
        "Price": order["price"] if order["price"] is not None else "-",
        "Stop Price": order["stop_price"] if order["stop_price"] is not None else "-",
    })

    # 2. Build client -----------------------------------------------------
    api_key = os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")
    try:
        client = BinanceFuturesTestnetClient(api_key, api_secret, logger=logger)
    except BinanceClientError as exc:
        logger.error("Client initialization failed: %s", exc)
        print(f"\n[FAILED] {exc}")
        return 1

    # 3. Place order --------------------------------------------------
    manager = OrderManager(client)
    result = manager.place_order(
        symbol=order["symbol"],
        side=order["side"],
        order_type=order["order_type"],
        quantity=order["quantity"],
        price=order["price"],
        stop_price=order["stop_price"],
    )

    # 4. Report ------------------------------------------------------
    if result.success:
        print_summary("Order Response", {
            "Order ID": result.order_id,
            "Status": result.status,
            "Executed Qty": result.executed_qty,
            "Avg Price": result.avg_price or "-",
        })
        print("\n[SUCCESS] Order placed successfully.\n")
        return 0
    else:
        print(f"\n[FAILED] Order was not placed: {result.error}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
