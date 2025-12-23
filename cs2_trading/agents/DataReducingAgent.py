from cs2_trading.agents.base import AgentBase
import json
from datetime import datetime

class DataReducingAgent(AgentBase):
    '''
    function: work(data: json) -> str
    function: reset(last_words_prompt: str, system_prompt: str = None) -> None
    '''
    default_system_prompt  = "你是一个CS2游戏饰品市场数据简化[专家], 擅长从复杂的数据中提取关键信息并进行简明扼要的总结, 你乐于分享你的见解."
    def __init__(self, client=None, llm_model=None):
        super().__init__(client, llm_model)
        self.add_system_message(self.default_system_prompt)

    def work(self, data: json) -> str:
        prompt = f"请你好好分析以下的单个CS2饰品当前截面数据, 并提取出最重要的信息, 总结成一段中文文本. 要求对有效金融数据进行基础概括分析, 并给出简短的投资建议. 数据内容如下:"
        prompt += f"\n\n{json.dumps(data, ensure_ascii=False)}\n\n"

        ans = self.get_response(prompt)
        self.save(name=datetime.now().strftime("%Y%m%d_%H%M%S"), path="./cs2_trading/res/data_reducing", object=ans)
        return ans

    def reset(self, last_words_prompt: str = "请你好好总结一下目前所有的分析, 汇总成一段不超过100字的文字, 并且输出, 我要与另外一个agent交流", system_prompt: str = "你是一个CS2游戏饰品市场数据简化[专家], 擅长从复杂的数据中提取关键信息并进行简明扼要的总结, 你乐于分享你的见解.") -> None:
        self.kill_and_reborn(last_words_prompt=last_words_prompt, system_prompt=system_prompt)

