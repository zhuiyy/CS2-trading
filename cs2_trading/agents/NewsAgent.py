from typing import List, Dict, Optional, Any
import requests
from bs4 import BeautifulSoup
from cs2_trading.agents.base import AgentBase
from cs2_trading.utils.logger import get_logger

class NewsAgent(AgentBase):
    def __init__(self, client: Optional[Any] = None, llm_model: Optional[str] = None):
        # Explicitly enable search for NewsAgent if using Gemini
        if llm_model and "gemini" in llm_model.lower():
             # We need to hack this a bit because AgentBase calls get_llm internally
             # Ideally AgentBase should accept kwargs to pass to get_llm
             pass 
             
        super().__init__(client, llm_model)
        
        # Post-init configuration for search if needed
        if self.llm and self.llm.provider == "gemini":
             # Re-initialize LLMWrapper with search enabled specifically for NewsAgent
             from cs2_trading.llm.wrapper import LLMWrapper
             self.llm = LLMWrapper(provider="gemini", model=llm_model, enable_search=True)

        self.logger = get_logger("NewsAgent")
        # Default sources - can be extended
        self.sources = [
            "https://www.csgo.com.cn/news/index.html", # Perfect World CS2 News (Corrected)
        ]

    def fetch_page_content(self, url: str) -> str:
        """
        Fetches the URL and returns a cleaned text representation suitable for LLM consumption.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            self.logger.info(f"Fetching news from: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
                
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long (simple heuristic to avoid context overflow)
            return text[:15000] 
            
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return ""

    def analyze_news(self, raw_text: str, target_object: Optional[str] = None) -> str:
        """
        Uses the LLM to extract relevant trading information from the raw text.
        If target_object is provided, focuses analysis on that specific item/topic.
        """
        if not raw_text:
            return "No content to analyze."

        base_prompt = (
            "You are a CS2 (Counter-Strike 2) market analyst. "
            "Read the following raw text from a news page and extract ANY information that might affect skin/sticker prices.\n"
        )

        if target_object:
            specific_prompt = (
                f"Your PRIMARY GOAL is to find news specifically related to: '{target_object}'.\n"
                "Look for:\n"
                f"- Direct mentions of {target_object}.\n"
                "- Updates to weapons/maps that might affect its value.\n"
                "- General market trends that would impact this specific item.\n"
                "If the text contains NO information relevant to this object, explicitly state 'No relevant news found for target'.\n"
            )
        else:
            specific_prompt = (
                "Focus on:\n"
                "1. New Case releases or Operation updates.\n"
                "2. Weapon balance changes (nerfs/buffs).\n"
                "3. Map pool changes.\n"
                "4. Major tournament sticker releases.\n"
            )

        closing_prompt = (
            "\nSummarize the findings in a concise list. Prioritize recent events.\n\n"
            f"--- RAW TEXT START ---\n{raw_text}\n--- RAW TEXT END ---"
        )

        prompt = base_prompt + specific_prompt + closing_prompt
        
        # DEBUG: Print raw text length and preview instead of calling LLM
        # print(f"[DEBUG] Fetched content length: {len(raw_text)}")
        # print(f"[DEBUG] Content preview:\n{raw_text[:500]}...")
        # return "DEBUG MODE: Skipped LLM call."
        
        return self.get_response(prompt)

    def get_market_news(self, target_object: Optional[str] = None, date: Optional[str] = None) -> List[str]:
        """
        Iterates through sources, fetches content, and returns a list of insights.
        Args:
            target_object: If provided, the agent will specifically look for news regarding this item.
            date: Optional date string (YYYY-MM-DD) to focus the search/analysis on.
        """
        # Check if LLM supports search (Gemini)
        if self.llm and self.llm.provider == "gemini" and self.llm.kwargs.get("enable_search"):
            return [self.search_news(target_object, date=date)]

        insights = []
        for url in self.sources:
            content = self.fetch_page_content(url)
            if content:
                # Note: analyze_news doesn't currently use date, but could be extended
                analysis = self.analyze_news(content, target_object=target_object)
                insights.append(f"Source: {url}\nTarget: {target_object or 'General'}\nAnalysis:\n{analysis}")
        
        return insights

    def search_news(self, target_object: Optional[str] = None, date: Optional[str] = None) -> str:
        """
        Uses the LLM's search capability (e.g. Gemini Grounding) to find news.
        """
        from datetime import datetime
        if date:
            current_date = date
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        if not target_object:
            query = f"CS2 (Counter-Strike 2) sticker market news updates {current_date}"
        else:
            query = f"CS2 sticker market news price trends {target_object} {current_date}"
            
        prompt = (
            f"Current Date: {current_date}\n"
            f"Please use Google Search to find the LATEST information about: {query}\n"
            "Strictly focus on news from the last 7 days. Ignore any information older than 1 month.\n"
            "If you find information about 'summer slump' or seasonal trends, ensure it matches the current month.\n"
            "Summarize the key findings relevant to trading and investment, specifically mentioning any rising STICKERS (Tournaments, Teams, Autographs).\n"
            "Ignore weapon skins (like AK-47, AWP, etc.) unless they directly affect sticker prices.\n"
            "Do NOT use examples from 2014 (like Titan Holo) unless there is ACTUAL breaking news about them today."
        )
        
        return self.get_response(prompt)
