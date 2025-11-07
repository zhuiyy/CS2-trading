"""Simple CLI runner for the scaffold project."""
import argparse
from cs2_trading.backtest.backtester import Backtester
from cs2_trading.utils.logger import get_logger


def demo_backtest():
    logger = get_logger("main")
    logger.info("Running demo backtest on scaffold data")
    bt = Backtester()
    # scaffold data: two items with linear prices
    price_series = {
        "item_a": [100, 101, 102, 103, 104],
        "item_b": [200, 198, 199, 201, 205],
    }
    signals = {}
    res = bt.run_backtest(price_series, signals)
    logger.info(f"Sharpe: {res['sharpe']:.4f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true", help="run demo backtest")
    args = p.parse_args()
    if args.demo:
        demo_backtest()
    else:
        print("CS2 Trading Agents scaffold. Use --demo to run demo backtest.")


if __name__ == "__main__":
    main()
