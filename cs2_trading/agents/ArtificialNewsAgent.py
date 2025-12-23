import os
from datetime import datetime
from cs2_trading.agents.NewsAgent import NewsAgent
from cs2_trading.utils.logger import get_logger

class ArtificialNewsAgent(NewsAgent):
    def __init__(self, news_dir="cs2_trading/res/news_artificial"):
        # Initialize parent but we won't use the LLM for searching
        super().__init__(llm_model="gemini-3-pro-preview") 
        self.news_dir = news_dir
        self.logger = get_logger("ArtificialNewsAgent")

    def search_news(self, query: str = None, date: str = None) -> str:
        """
        Override search_news to read from local file based on date.
        
        Args:
            query: The search query (ignored in this agent, but kept for signature compatibility if needed)
            date: The specific date string (YYYY-MM-DD) to look for.
        """
        # If date is passed directly, use it.
        if date:
            date_str = date
        else:
            # Fallback: try to extract from query if it was passed as the first arg (legacy behavior)
            # In the new signature, the first arg is 'target_object' in base class, but here we named it query.
            # Let's handle both cases.
            import re
            # If query is actually the target_object or None, we might not find the date.
            # But let's try to find it in the string if it's a string.
            if isinstance(query, str):
                date_match = re.search(r"Current Date: (\d{4}-\d{2}-\d{2})", query)
                if date_match:
                    date_str = date_match.group(1)
                else:
                    # Try to find just a date pattern
                    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", query)
                    if date_match:
                        date_str = date_match.group(1)
                    else:
                        return "Could not determine date for artificial news."
            else:
                 return "Could not determine date for artificial news."

        file_date_prefix = date_str.replace("-", "") # YYYYMMDD
        
        # Find all files starting with this prefix in the directory
        found_files = []
        if os.path.exists(self.news_dir):
            try:
                for filename in os.listdir(self.news_dir):
                    # Match files like 20251125.txt, 20251125_1.txt, 20251125_morning.txt
                    if filename.startswith(file_date_prefix) and filename.endswith(".txt"):
                        found_files.append(os.path.join(self.news_dir, filename))
            except OSError as e:
                self.logger.error(f"Error listing directory {self.news_dir}: {e}")

        if found_files:
            combined_content = ""
            found_files.sort() # Ensure deterministic order
            for fp in found_files:
                self.logger.info(f"Loading artificial news from {fp}")
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                        combined_content += f"\n\n--- SOURCE: {os.path.basename(fp)} ---\n{content}"
                except Exception as e:
                    self.logger.error(f"Error reading {fp}: {e}")

            return f"--- ARTIFICIAL NEWS FOR {date_str} (Found {len(found_files)} files) ---{combined_content}"
        else:
            self.logger.warning(f"No artificial news found for {date_str} in {self.news_dir}")
            return f"No significant market news found for {date_str}."
