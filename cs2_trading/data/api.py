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

if __name__ == "__main__":
    client = InfoAPI()
    resp = client.get_good_id("绿龙 金色")
    print(resp)