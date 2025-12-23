from cs2_trading.agents.market import StickerScorer, StickerTrader
from cs2_trading.agents.StickerAgent import StickerFinder
from cs2_trading.data.inventory import Inventory
# from cs2_trading.agents.DataReducingAgent import DataReducingAgent
from cs2_trading.agents.FinancialAgent import FinancialAgent
from datetime import datetime, timedelta
import time
import random
import logging

class DailyStrategy:
    def __init__(self, inventory: Inventory, news_agent, info_api, llm_model="gemini-3-pro-preview", target_quantity=20, max_buy_daily=2, save_path="cs2_trading/res/my_inventory.json"):
        self.inventory = inventory
        self.news_agent = news_agent
        self.info_api = info_api
        self.scorer = StickerScorer(llm_model=llm_model)
        self.trader = StickerTrader(llm_model=llm_model)
        self.finder = StickerFinder(llm_model=llm_model)
        # self.data_reducer = DataReducingAgent(llm_model=llm_model)
        self.financial_analyst = FinancialAgent(info_api, llm_model=llm_model)
        self.target_quantity = target_quantity
        self.max_buy_daily = max_buy_daily 
        self.save_path = save_path 

    def run_daily_cycle(self, current_date: datetime):
        date_str = current_date.strftime("%Y-%m-%d")
        
        # --- LOG HEADER ---
        log_header = (
            f"\n"
            f"================================================================================\n"
            f"   DAILY CYCLE START: {date_str}\n"
            f"================================================================================"
        )
        print(f"\n=== Starting Daily Cycle: {date_str} ===")
        logging.info(log_header)
        
        # 1. Get News (Simulated for backtest/forward test if needed, or real)
        print("Step 1: Fetching News...")
        try:
            # In a real scenario, we might pass the date to get_market_news if it supported historical search
            # For now, we assume get_market_news gets "latest" relative to "now". 
            # If simulating past days, we might need to mock this or rely on the agent finding date-relevant info.
            # Here we just call it.
            news_insights = self.news_agent.get_market_news(date=date_str)
            combined_news = "\n\n".join(news_insights)
            
            if not combined_news or len(combined_news) < 50:
                print("No substantial news found. Using fallback simulation data.")
                combined_news = (
                    f"CS2 Market Update ({date_str}): Market sentiment is mixed. "
                    "Some older tournament stickers are seeing increased volume. "
                    "Rumors of a new case release are circulating."
                )
        except Exception as e:
            print(f"News fetch failed: {e}")
            combined_news = "No news available."

        print(f"--- News Summary ---\n{combined_news[:200]}...\n--------------------")
        
        # --- LOG NEWS ---
        logging.info(f"\n>>> [STEP 1] MARKET NEWS & SENTIMENT")
        logging.info(f"--------------------------------------------------------------------------------")
        logging.info(f"{combined_news}")
        logging.info(f"--------------------------------------------------------------------------------")

        # 1.5 Financial Analysis
        print("\nStep 1.5: Conducting Financial Analysis...")
        financial_report = self.financial_analyst.analyze_market_sentiment(combined_news, date_str)
        print(f"Financial Insight: {financial_report}")
        
        # --- LOG FINANCIAL ---
        logging.info(f"\n>>> [STEP 2] FINANCIAL ANALYSIS")
        logging.info(f"--------------------------------------------------------------------------------")
        logging.info(f"{financial_report}")
        logging.info(f"--------------------------------------------------------------------------------")

        # 2. Score Inventory
        print("\nStep 2: Scoring Inventory...")
        logging.info(f"\n>>> [STEP 3] INVENTORY SCORING")
        
        # Batch scoring optimization
        unique_names = list({item.name for item in self.inventory.items})
        print(f"  Batch scoring {len(unique_names)} unique items...")
        
        batch_scores = {}
        if unique_names:
            try:
                batch_scores = self.scorer.score_batch(unique_names, combined_news)
            except Exception as e:
                print(f"  Batch scoring failed: {e}")
                logging.error(f"  Batch scoring failed: {e}")

        for item in self.inventory.items:
            print(f"  Scoring {item.name}...")
            try:
                # Use batch result if available
                res = batch_scores.get(item.name)
                if not res:
                    print(f"    !!! Batch missing for {item.name} !!!")
                    print(f"    -> Context: See 'News Summary' at the start of Day {date_str}.")
                    print(f"    -> Debug: Check 'batch_score_error.log' in workspace root if you suspect a parsing error.")
                    # Fallback: Try individual scoring or use default
                    try:
                        print(f"    -> Attempting individual scoring fallback for {item.name}...")
                        res = self.scorer.score(item.name, combined_news)
                        time.sleep(1) # Rate limit protection
                    except Exception as e:
                        print(f"    -> Individual scoring failed: {e}. Using default.")
                        res = {"score": 50, "reason": "Scoring failed (Batch & Individual)"}
                
                score = res.get("score", 50)
                reason = res.get("reason", "N/A")
                
                item.daily_score.append(score)
                
                # Fetch Real Price
                # This will raise an exception if it fails, as requested.
                real_price = self.info_api.get_historical_price(item.id, date_str)
                
                new_price = real_price
                print(f"    -> Fetched real price: {new_price}")
                
                item.daily_price.append(new_price)
                
                msg_score = f"    -> Scoring {item.name}: Score: {score}, Price: {new_price:.2f}, Reason: {reason}"
                print(msg_score)
                logging.info(msg_score)
            except Exception as e:
                print(f"    -> Error scoring: {e}")
                logging.error(f"    -> Error scoring {item.name}: {e}")
                # Fallback logic to keep lists in sync
                if len(item.daily_price) < len(item.daily_score):
                    fallback_price = item.daily_price[-1] if item.daily_price else item.bought_price
                    item.daily_price.append(fallback_price)
                    print(f"    -> Used fallback price: {fallback_price}")

        # 3. Sell Logic
        print("\nStep 3: Checking Sell Opportunities...")
        logging.info(f"\n>>> [STEP 4] SELL DECISIONS")
        
        # Use list() to create a copy for safe iteration while modifying the original list
        tradeable = list(self.inventory.get_tradeable_items(current_date))
        for item in tradeable:
            if not item.daily_price:
                print(f"  Skipping {item.name} (No price history)")
                continue
            current_price = item.daily_price[-1]
            score = item.daily_score[-1]
            
            print(f"  Analyzing {item.name} (Held {item.days_held(current_date)} days)...")
            
            # Enhance decision with DataReducer
            # Fetch detailed info (mocked or real)
            # item_info = self.info_api.get_good_info(item.id) 
            # For now, we construct a summary string
            item_summary = f"Item: {item.name}, Rarity: {item.extra_info.get('rarity', 'Unknown')}"
            
            # Financial Analysis for specific item
            price_analysis = self.financial_analyst.analyze_item_price(item.name, current_price, item.bought_price)
            
            # Combine news, financial report, and price analysis for the trader
            decision_context = (
                f"{combined_news}\n\n"
                f"--- Financial Analyst Report ---\n{financial_report}\n"
                f"--- Item Price Analysis ---\n{price_analysis}"
            )
            
            decision_res = self.trader.decide(item, current_price, decision_context, score)
            decision = decision_res.get("decision", "HOLD")
            reason = decision_res.get("reason", "N/A")
            
            # --- API RATE LIMIT PROTECTION ---
            time.sleep(2) # Sleep 2s after each LLM call to avoid 429
            
            msg_decision = f"    -> Decision for {item.name}: {decision}, Reason: {reason}"
            print(msg_decision)
            logging.info(msg_decision)
            logging.info(f"       [Context]\n{decision_context.replace(chr(10), chr(10)+'       ')}") # Indent context
            
            if decision == "SELL":
                msg_sell = f"    !!! SELLING {item.name} !!!"
                print(msg_sell)
                logging.info(msg_sell)
                self.inventory.remove_item(item)
                # In a real system, we'd record realized profit here

        # 4. Buy/Restock Logic
        print("\nStep 4: Restocking...")
        logging.info(f"\n>>> [STEP 5] RESTOCKING")
        
        current_count = len(self.inventory.items)
        needed = self.target_quantity - current_count
        
        # Apply daily buy limit
        actual_buy_count = min(needed, self.max_buy_daily)
        
        if actual_buy_count > 0:
            print(f"  Need to buy {needed} items. Daily limit: {self.max_buy_daily}. Will buy: {actual_buy_count}")
            candidates = self.finder.work(combined_news)
            print(f"  Candidates from news: {candidates}")
            logging.info(f"  Candidates from news: {candidates}")
            
            owned_names = {i.name for i in self.inventory.items}
            new_candidates = [c for c in candidates if c not in owned_names]
            
            scored_candidates = []
            for cand in new_candidates:
                res = self.scorer.score(cand, combined_news)
                scored_candidates.append((cand, res.get("score", 0)))
                time.sleep(1) # Sleep 1s after each scoring call
            
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            to_buy = scored_candidates[:actual_buy_count]
            for name, score in to_buy:
                msg_buy = f"    -> Buying {name} (Score: {score})"
                print(msg_buy)
                logging.info(msg_buy)
                
                # Get Real ID from API
                real_id = hash(name) % 100000 # Default fallback
                price = 0.0
                
                try:
                    ids = self.info_api.get_good_id(name)
                    if ids:
                        real_id = ids[0]
                        print(f"       [API] Found real ID: {real_id}")
                        # Fetch real price
                        price = self.info_api.get_historical_price(real_id, date_str)
                        print(f"       [API] Fetched price: {price}")
                    else:
                        print(f"       [API] ID not found for {name}, using mock ID.")
                        # Fallback price simulation if ID not found
                        price = 100.0 * (1 + (score-50)/100)
                except Exception as e:
                    print(f"       [API] Failed to fetch ID/Price: {e}")
                    # Fallback price simulation on error
                    price = 100.0 * (1 + (score-50)/100)
                
                if price > 0:
                    self.inventory.add_item(
                        id=real_id,
                        name=name,
                        price=price,
                        date=current_date,
                        info={"initial_score": score, "rarity": "Unknown"}
                    )
        else:
            print("  Inventory full or daily limit reached, no need to restock.")

        # Save state
        self.inventory.save(self.save_path)
        print("\n=== Daily Cycle Complete ===")
