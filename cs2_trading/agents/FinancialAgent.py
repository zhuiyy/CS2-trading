from cs2_trading.utils.logger import get_logger
from ..llm.wrapper import LLMWrapper
from ..data.api import InfoAPI
import random

class FinancialAgent:
    def __init__(self, info_api: InfoAPI, llm_model="gemini-3-pro-preview"):
        self.llm = LLMWrapper(provider="gemini", model=llm_model)
        self.logger = get_logger("FinancialAgent")
        self.info_api = info_api

    def analyze_market_sentiment(self, news_summary, current_date):
        """
        根据新闻和模拟的市场数据，生成一份简短的金融分析报告。
        """
        # ... (Logic similar to previous proposal, but can now use self.get_historical_price if implemented)
        
        prompt = f"""
        Role: You are a professional crypto/asset trader specializing in CS2 sticker markets.
        Task: Analyze the current financial situation for the CS2 sticker market based on the provided news.
        
        Current Date: {current_date}
        News Context: {news_summary}
        
        Output:
        Provide a concise 3-sentence financial analysis. 
        1. Assess the risk level.
        2. Give a recommendation (Buy/Sell/Hold) based purely on financial data.
        """
        
        return self.llm.simple_ask(prompt)

    def analyze_item_price(self, item_name, current_price, purchase_price):
        """
        分析单个物品的价格表现
        """
        pnl_percent = ((current_price - purchase_price) / purchase_price) * 100
        
        prompt = f"""
        Analyze the financial performance of this asset:
        Item: {item_name}
        Purchase Price: ${purchase_price:.2f}
        Current Price: ${current_price:.2f}
        PnL: {pnl_percent:.2f}%
        
        Is this a good time to take profit or cut loss? Answer in 1 short sentence.
        """
        return self.llm.simple_ask(prompt)
