from typing import Any, Dict, List, Optional
from pathlib import Path

class AgentBase:
    def __init__(self, client: Optional[Any] = None, llm_model: Optional[str] = None):
        self.client = client
        self.llm_model = llm_model
        self.memory: List[Dict[str, str]] = []
        self.last_words: Optional[str] = None

    def add_system_message(self, message: str) -> None:
        self.memory.append({'role': 'system', 'content': message})

    def get_response(self, user_prompt: str) -> str:
        if self.client is None:
            content = f"[no-llm] echo: {user_prompt}"
        else:
            try:
                completion = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=self.memory + [{'role': 'user', 'content': user_prompt}]
                )
                content = completion.choices[0].message.content
            except Exception:
                try:
                    content = self.client.call(user_prompt)
                except Exception:
                    content = "[llm-call-failed]"

        self.memory.append({'role': 'user', 'content': user_prompt})
        self.memory.append({'role': 'assistant', 'content': content})
        return content

    def kill_and_reborn(self, last_words_prompt: str, system_prompt: str) -> None:
        last_words = self.get_response(last_words_prompt)
        self.memory = []
        self.add_system_message(system_prompt)
        self.memory.append({'role': 'system', 'content': f'以下是上一位与用户对话的智能体最后总结的内容:\n\n{last_words}\n\n你需要阅读并且理解, 在他的基础上继续与用户对话.'})

    def save(self, name: str = 'default', path: str = None, object: Any = None) -> None:

        # default path if not provided
        if path is None:
            path = "./cs2_trading/res/default"

        p = Path(path)
        # create directories if missing
        p.mkdir(parents=True, exist_ok=True)

        file_path = p / f"{name}.txt"
        with file_path.open("w", encoding="utf-8") as f:
            f.write(str(object))
        return