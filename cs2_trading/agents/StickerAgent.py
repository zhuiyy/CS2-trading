from cs2_trading.agents.base import AgentBase
from cs2_trading.data.api import InfoAPI
from cs2_trading.agents.DataReducingAgent import DataReducingAgent
import re
from typing import List, Any

from datetime import datetime


# --- robust parser for LLM responses (one-item-per-line preferred) ---
def _normalize_list(arr, max_items: int):
    out: List[str] = []
    for x in arr:
        if isinstance(x, (list, tuple)):
            for y in x:
                s = str(y).strip()
                if s and s not in out:
                    out.append(s)
        else:
            s = str(x).strip()
            if s and s not in out:
                out.append(s)
        if len(out) >= max_items:
            break
    return out[:max_items]


def parse_names_from_response(resp_text: str, max_items: int = 5) -> List[str]:
    # 1) try JSON
    try:
        import json as _json

        obj = _json.loads(resp_text)
        if isinstance(obj, dict):
            for key in ("names", "data", "items", "results"):
                v = obj.get(key)
                if isinstance(v, list):
                    return _normalize_list(v, max_items)
            # fallback: if dict contains list-like values
            for v in obj.values():
                if isinstance(v, list):
                    return _normalize_list(v, max_items)
        elif isinstance(obj, list):
            return _normalize_list(obj, max_items)
    except Exception:
        pass

    text = resp_text.strip()

    # 2) If line-based "names:" section exists, extract following lines or YAML-like list
    m = re.search(r"(?i)names[:\s]*\n([\s\S]{0,1000})", text)
    if m:
        block = m.group(1).strip()
        lines = [ln.strip() for ln in re.split(r"\n+", block) if ln.strip()]
        candidates = []
        for ln in lines:
            ln2 = re.sub(r"^[-\d\.\)\s]+", "", ln).strip()
            if ln2:
                candidates.append(ln2)
        if candidates:
            return _normalize_list(candidates, max_items)

    # 3) markdown/list style anywhere: lines starting with '-' or numeric list
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidates = []
    for ln in lines:
        if ln.startswith("- ") or re.match(r"^\d+[\.\)]\s", ln):
            ln2 = re.sub(r"^[-\d\.\)\s]+", "", ln).strip()
            candidates.append(ln2)
    if candidates:
        return _normalize_list(candidates, max_items)

    # 4) single-line CSV
    if "\n" not in text and ("," in text or ";" in text):
        parts = re.split(r"[;,]\s*", text)
        return _normalize_list(parts, max_items)

    # 5) quoted substrings
    quoted = re.findall(r'"([^\"]+)"|\'([^\']+)\'', text)
    if quoted:
        parts = [p[0] or p[1] for p in quoted]
        return _normalize_list(parts, max_items)

    # 6) fallback: first N non-trivial lines
    good_lines = [ln for ln in lines if len(ln) > 2][:max_items]
    return _normalize_list(good_lines, max_items)

class StickerFinder(AgentBase):
    '''
    function: work(news: str) -> list
    '''
    def __init__(self, client, llm_model):
        super().__init__(client, llm_model)
        # Prefer a very simple, one-item-per-line output to improve robustness.
        self.default_system_prompt = (
            "你是一个CS2游戏印花饰品嗅探专家。\n"
            "请从给定的新闻中找出最多 5 个相关的印花饰品名称。\n"
            "非常重要：只输出名称，每行一个，不要解释、不要编号、不要 JSON，不要其它文本。\n"
            "例如：\nZywOo 上海 全息\n绿龙 金色\n如果没有找到任何印花，请只返回单行 EMPTY。"
        )
        self.add_system_message(self.default_system_prompt)

    def work(self, news: str) -> list:
        prompt = f"请根据下面的新闻找出印花名称，注意只返回每行一个名称（最多5个），否则返回 EMPTY:\n\n{news}\n\n"
        response = self.get_response(prompt)

        names = parse_names_from_response(response, max_items=5)

        # Treat sentinel replies like 'EMPTY' as no results. Models may return the
        # literal word EMPTY when nothing is found — we must not treat that as a
        # real item name and then query the info API for it.
        def _filter_empty_tokens(lst):
            out = []
            for x in lst:
                s = str(x).strip()
                if not s:
                    continue
                low = s.lower()
                # common sentinel tokens to ignore
                if low in ("EMPTY", "empty", "none", "n/a", "无", "没有"):
                    continue
                out.append(s)
                if len(out) >= 5:
                    break
            return out

        names = _filter_empty_tokens(names)

        # if parsing failed or returned empty, retry once with a stricter reminder
        if not names:
            response = self.get_response("你必须严格只返回每行一个名称，最多5个；如果没有则返回 EMPTY。请仅输出结果，不要解释。\n\n" + news)
            names = parse_names_from_response(response, max_items=5)
            names = _filter_empty_tokens(names)

        print("finder", names)
        return names

class StickerAdviser(AgentBase):
    '''
    function: work(data: json) -> str
    function: reset(last_words_prompt: str, system_prompt: str = None) -> None
    '''
    def __init__(self, client, llm_model):
        super().__init__(client, llm_model)
        self.default_system_prompt = "你是一个CS2游戏**印花饰品**分析[专家], 擅长从多元化的新闻中分析职业队伍/选手/比赛动态, 同时擅长结合金融分析数据给出投资建议(事实上金融分析师给出的数据没有考虑到近期新闻内容, 所以需要你好好把握衡量), 值得注意的是, 你要考虑到CS2市场的t+7性质, 基于此做出评价并给出建议."
        self.add_system_message(self.default_system_prompt)

    def work(self, news_data: str) -> str:
        prompt = f"请你好好分析以下新闻与金融分析, 并回复一个段文本(每件关注的物品200字左右):"
        prompt += f"\n\n{news_data}\n\n"

        ans = self.get_response(prompt)
        self.save(name=datetime.now().strftime("%Y%m%d_%H%M%S"), path="./cs2_trading/res/sticker_adviser", object=ans)
        return ans

    def reset(self, last_words_prompt: str, system_prompt: str = None) -> None:
        self.kill_and_reborn(last_words_prompt=last_words_prompt, system_prompt=system_prompt)


class StickerAgent:
    '''
    function: find_stickers(news: str) -> list
    function: advise_stickers(news_data: str) -> str
    '''
    def __init__(self, client, llm_model, info_api: Any = None):
        # composition-based agent (does not inherit AgentBase)
        self.client = client
        self.llm_model = llm_model
        self.finder = StickerFinder(client, llm_model)
        self.adviser = StickerAdviser(client, llm_model)
        self.info_api = info_api or InfoAPI()
        self.data_reducer = DataReducingAgent(client, llm_model)

    def work(self, news: str) -> str:
        sticker_names = self.finder.work(news)
        if not sticker_names:
            news_data = f"新闻内容:\n{news}\n\n"

            advice = self.adviser.work(news_data)
            print("No stickers found, general advice given.")
            return advice
        
        # Resolve names to ids; handle single id or list of ids from API
        sticker_ids = []
        for name in sticker_names:
                id_list = self.info_api.get_good_id(name)
                sticker_ids += id_list

        analyzed_infos = ''
        for sid in sticker_ids:
            info = self.info_api.get_good_info(int(sid))
            info = self.data_reducer.work(info)
            analyzed_infos += info + "\n"

        news_data = f"新闻内容:\n{news}\n\n涉及的印花饰品市场情况:\n{analyzed_infos}"

        advice = self.adviser.work(news_data)
        return advice
    
    def reset(self, last_words_prompt: str, system_prompt: str = None) -> None:
        # Recreate internal components and forward reset to adviser if supported
        self.finder = StickerFinder(self.client, self.llm_model)
        try:
            self.adviser.reset(last_words_prompt=last_words_prompt, system_prompt=system_prompt)
        except Exception:
            self.adviser = StickerAdviser(self.client, self.llm_model)