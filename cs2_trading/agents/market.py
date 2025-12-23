from cs2_trading.agents.base import AgentBase
from cs2_trading.data.inventory import Stuff
import json
import re
from datetime import datetime

class StickerScorer(AgentBase):
    """
    Agent responsible for scoring a sticker based on news sentiment.
    """
    def __init__(self, client=None, llm_model=None):
        super().__init__(client, llm_model)
        self.system_prompt = (
            "你是一个CS2饰品市场情绪分析师。\n"
            "请根据提供的新闻，对指定的印花进行打分（0-100分）。\n"
            "0分表示极度看空/无热度，100分表示极度看多/热度爆表。\n"
            "请只返回一个JSON格式的结果，包含 'score' (整数) 和 'reason' (简短理由)。\n"
            "例如: {\"score\": 85, \"reason\": \"Major夺冠热门，选手使用率高\"}"
        )
        self.add_system_message(self.system_prompt)

    def score(self, sticker_name: str, news: str) -> dict:
        prompt = f"印花名称: {sticker_name}\n\n相关新闻:\n{news}\n\n请打分:"
        response = self.get_response(prompt)
        
        # Parse JSON
        try:
            # Try to find JSON block
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return {"score": 50, "reason": "无法解析模型输出", "raw": response}
        except Exception as e:
            return {"score": 50, "reason": f"解析错误: {e}", "raw": response}

    def score_batch(self, sticker_names: list[str], news: str) -> dict:
        if not sticker_names:
            return {}
            
        names_str = ", ".join(sticker_names)
        prompt = (
            f"相关新闻:\n{news}\n\n"
            f"任务: 对以下印花进行批量打分: {names_str}\n"
            "要求:\n"
            "1. 必须返回合法的JSON格式。\n"
            "2. 不要使用Markdown代码块(```json ... ```)，直接返回JSON字符串。\n"
            "3. JSON结构: 键是印花名称，值是 {\"score\": int, \"reason\": str}。\n"
            "4. 确保包含列表中的所有印花。\n"
            "例如: {\"印花A\": {\"score\": 80, \"reason\": \"理由...\"}, \"印花B\": {\"score\": 40, \"reason\": \"理由...\"}}"
        )
        
        response = self.get_response(prompt)
        
        # Clean up response (sometimes LLMs still add markdown)
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        try:
            # Try parsing cleaned response
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            # Try regex extraction if direct parse fails
            try:
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    return json.loads(json_str)
            except Exception:
                pass
            
            # Log for human review
            print(f"[Scorer] Batch JSON parse failed. Raw response saved to 'batch_score_error.log'")
            with open("batch_score_error.log", "a", encoding="utf-8") as f:
                f.write(f"--- {datetime.now()} ---\n{response}\n\n")
            return {}


class StickerTrader(AgentBase):
    """
    Agent responsible for making Sell/Hold decisions.
    """
    def __init__(self, client=None, llm_model=None):
        super().__init__(client, llm_model)
        self.system_prompt = (
            "你是一个专业的CS2饰品交易员。\n"
            "你需要根据印花的持仓信息、当前市场价格、新闻分析以及情绪评分，决定是 'SELL' (卖出) 还是 'HOLD' (持有)。\n"
            "请只返回一个JSON格式的结果，包含 'decision' ('SELL' 或 'HOLD') 和 'reason' (理由)。"
        )
        self.add_system_message(self.system_prompt)

    def decide(self, item: Stuff, current_price: float, news: str, score: int) -> dict:
        profit_rate = (current_price - item.bought_price) / item.bought_price * 100
        
        info_str = (
            f"印花名称: {item.name}\n"
            f"买入价格: {item.bought_price}\n"
            f"当前价格: {current_price}\n"
            f"盈亏比例: {profit_rate:.2f}%\n"
            f"持仓天数: {len(item.daily_score)}天\n" # Assuming daily_score len is days held roughly
            f"今日情绪评分: {score}/100\n"
        )
        
        prompt = f"{info_str}\n\n市场新闻:\n{news}\n\n请做出交易决策:"
        response = self.get_response(prompt)
        
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {"decision": "HOLD", "reason": "无法解析决策", "raw": response}
        except Exception:
            return {"decision": "HOLD", "reason": "解析异常", "raw": response}

