"""Price API client skeletons"""
from typing import Any, Dict, List
import datetime
import os
from dotenv import load_dotenv
import requests
from time import sleep


'''2xx: 响应成功
400: 用户不存在或Token验证未通过
401: Token验证未通过
404: 接口错误统一返回
429: 客户端短时间内请求过多
500: 服务错误统一返回(回传request_id可协助排查)
503: 网关异常或请求频繁'''



class InfoAPI:

    def __init__(self, api_token: str | None = None):
        load_dotenv()
        self.base_url = "https://api.csqaq.com/api/v1/info/"
        self.api_token = api_token or os.getenv("INFO_API_TOKEN")
        if not self.api_token:
            raise EnvironmentError("API token not found.")
        # Cache for item_id -> market_hash_name mapping to avoid repeated API calls
        self._name_cache = {}

    def get_good_info(self, id: int, timeout: float = 10.0, proxies: Dict[str, str] | None = None) -> Dict[str, Any]:
        sleep(1)
        url = f"{self.base_url}good"
        params = {"id": id}
        headers = {"ApiToken": self.api_token}

        response = requests.get(url, headers=headers, params=params, timeout=timeout, proxies=proxies)

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()

        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {data}")

        return data

    def get_reduced_good_info(self, id: int, timeout: float = 10.0, proxies: Dict[str, str] | None = None) -> Dict[str, Any]:
        sleep(1)
        full_info = self.get_good_info(id, timeout, proxies)
        reduced_info = {
            "item_id": full_info.get("id"),
            "name": full_info.get("name"),
            "price": full_info.get("price"),
            "rarity": full_info.get("rarity"),
        }
        return reduced_info

    def get_good_id(self, name: str, timeout: float = 10.0, proxies: Dict[str, str] | None = None) -> list[int]:
        # Use the suggest endpoint which accepts a `text` query (near real-time suggestions)
        sleep(1)

        url = "https://api.csqaq.com/api/v1/search/suggest"
        params = {"text": name}
        headers = {"ApiToken": self.api_token}
        response = requests.get(url, headers=headers, params=params, timeout=timeout, proxies=proxies)

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()

        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {data}")
        
        print(data)

        r = list()

        for i in data.get("data", []):
            r.append(i.get("id"))

        return r[:3:]

    def get_historical_price(self, item_id: int, date: str) -> float:
        """
        Fetch historical price from CSQAQ Chart API (BUFF price).
        Args:
            item_id: The ID of the item (CSQAQ good_id).
            date: The date string (YYYY-MM-DD).
        Returns:
            float: The price (CNY). Returns 0.0 if not found.
        """
        # Initialize cache if needed
        if not hasattr(self, "_history_cache"):
            self._history_cache = {}

        # Check cache
        if item_id not in self._history_cache:
            sleep(1) # Rate limit
            url = "https://api.csqaq.com/api/v1/info/chart"
            # Use platform=1 (BUFF) for reliable pricing
            payload = {
                "good_id": str(item_id),
                "key": "sell_price",
                "platform": 1, 
                "period": "365", # Get 1 year of history
                "style": "all_style"
            }
            headers = {
                "ApiToken": self.api_token,
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != 200:
                    print(f"[API] CSQAQ error for {item_id}: {data.get('msg')}")
                    return 0.0
                
                chart_data = data.get("data", {})
                timestamps = chart_data.get("timestamp", [])
                prices = chart_data.get("main_data", [])
                
                # Store as dict: date_str -> price
                price_map = {}
                for ts, price in zip(timestamps, prices):
                    # ts is milliseconds
                    dt = datetime.datetime.fromtimestamp(ts / 1000.0)
                    d_str = dt.strftime("%Y-%m-%d")
                    price_map[d_str] = float(price)
                
                self._history_cache[item_id] = price_map
                
            except Exception as e:
                print(f"[API] Failed to fetch history for {item_id}: {e}")
                return 0.0

        # Lookup date
        price_map = self._history_cache.get(item_id, {})
        if date in price_map:
            return price_map[date]
            
        # Fallback: Find closest date
        sorted_dates = sorted(price_map.keys())
        if not sorted_dates:
            return 0.0
            
        # If requested date is before all history, return first
        if date < sorted_dates[0]:
            return price_map[sorted_dates[0]]
            
        # If requested date is after all history, return last
        if date > sorted_dates[-1]:
            return price_map[sorted_dates[-1]]
            
        # Otherwise, find closest previous date
        last_date = sorted_dates[0]
        for d in sorted_dates:
            if d > date:
                break
            last_date = d
            
        return price_map[last_date]

if __name__ == "__main__":
    client = InfoAPI()
    resp = client.get_good_id("绿龙 金色")
    print(resp)