"""Simple CLI runner for the scaffold project."""
import argparse
import os
from dotenv import load_dotenv
from cs2_trading.backtest.backtester import Backtester
from cs2_trading.utils.logger import get_logger
from cs2_trading.agents.NewsAgent import NewsAgent
from cs2_trading.agents.StickerAgent import StickerAgent
from cs2_trading.data.api import InfoAPI

def run_agents():
    logger = get_logger("main")
    logger.info("Starting Agent Orchestration...")
    
    # 1. Instantiate Agents
    # Ensure API keys are loaded
    load_dotenv()
    
    # You might want to make models configurable via args
    news_agent = NewsAgent(llm_model="qwen-plus") 
    
    # InfoAPI is needed for StickerAgent to look up item IDs
    info_api_token = os.getenv("INFO_API_TOKEN")
    info_api = InfoAPI(info_api_token) if info_api_token else InfoAPI()
    
    sticker_agent = StickerAgent(llm_model="gemini-1.5-pro", info_api=info_api)

    # 2. Fetch News (The Producer)
    logger.info("Fetching market news...")
    news_insights = news_agent.get_market_news()
    
    if not news_insights:
        logger.warning("No news found. Exiting.")
        return

    # Combine insights into a single context string
    combined_news = "\n\n".join(news_insights)
    logger.info(f"Collected {len(news_insights)} news insights.")

    # 3. Analyze News (The Consumer)
    logger.info("Analyzing news for sticker opportunities...")
    advice = sticker_agent.work(combined_news)
    
    logger.info("--- Final Advice ---")
    print(advice)
    logger.info("--------------------")


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
    p.add_argument("--run-agents", action="store_true", help="run the news->sticker agent pipeline")
    args = p.parse_args()
    
    if args.demo:
        demo_backtest()
    elif args.run_agents:
        run_agents()
    else:
        print("CS2 Trading Agents scaffold.")
        print("Use --demo to run demo backtest.")
        print("Use --run-agents to run the agent pipeline.")


if __name__ == "__main__":
    main()
