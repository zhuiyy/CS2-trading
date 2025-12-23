import os
import time
import logging
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI

# Configure logging for LLM wrapper
logger = logging.getLogger(__name__)

class LLMWrapper:
    """
    A unified wrapper for different LLM providers (OpenAI, Qwen, Gemini, etc.).
    Allows switching models and providers easily.
    """
    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo", **kwargs):
        self.provider = provider.lower()
        self.model = model
        self.client = None
        self.kwargs = kwargs
        
        self._setup_client()

    def _setup_client(self):
        if self.provider in ["openai", "qwen", "deepseek", "aliyun"]:
            # All these support the OpenAI SDK format
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE_URL")
            
            if not api_key:
                raise ValueError(f"API Key not found for provider {self.provider}")
                
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            
        elif self.provider == "gemini":
            # Use new google-genai SDK for Gemini 3+ support
            try:
                from google import genai
            except ImportError:
                raise ImportError("Please install `google-genai` package: pip install google-genai")
                
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found")
            
            self.client = genai.Client(api_key=api_key)
            
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_retries: int = 5) -> str:
        """
        Unified chat interface with retry logic for 429 errors.
        """
        backoff = 2
        
        for attempt in range(max_retries):
            try:
                if self.provider in ["openai", "qwen", "deepseek", "aliyun"]:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        **self.kwargs
                    )
                    return completion.choices[0].message.content

                elif self.provider == "gemini":
                    from google.genai import types
                    
                    contents = []
                    system_instruction = None
                    
                    for msg in messages:
                        if msg['role'] == 'system':
                            system_instruction = msg['content']
                        elif msg['role'] == 'user':
                            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg['content'])]))
                        elif msg['role'] == 'assistant':
                            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg['content'])]))
                    
                    config_kwargs = {
                        "temperature": temperature,
                    }
                    
                    if system_instruction:
                        config_kwargs["system_instruction"] = system_instruction
                        
                    # Apply thinking config for Gemini 3 models
                    if "gemini-3" in self.model:
                        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="medium")
                    
                    # Enable search if requested
                    if self.kwargs.get("enable_search"):
                        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(**config_kwargs)
                    )
                    
                    return response.text

            
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                    wait_time = backoff * (2 ** attempt)
                    logger.warning(f"LLM Rate Limit (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    print(f"LLM Rate Limit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"LLM Error: {e}")
                    return f"[LLM Error]: {str(e)}"
        
        return "[LLM Error]: Max retries exceeded."

    def simple_ask(self, prompt: str) -> str:
        """
        Helper for single-turn prompt.
        """
        return self.chat([{"role": "user", "content": prompt}])

# Factory/Helper to get the default configured LLM
def get_llm(model_name: str = None) -> LLMWrapper:
    """
    Returns an LLM instance based on environment or arguments.
    Default logic:
    - If model_name contains 'qwen', use aliyun provider.
    - If model_name contains 'gemini', use gemini provider.
    - Else default to openai/env settings.
    """
    # Default from env if not specified
    if not model_name:
        model_name = "qwen-plus" # Default preference as per conversation

    provider = "openai" # Default SDK
    kwargs = {}
    
    if "qwen" in model_name.lower():
        provider = "aliyun"
    elif "gemini" in model_name.lower():
        provider = "gemini"
        # Only enable search if explicitly requested or for specific agents/models if needed.
        # Disabling default search for all Gemini models to prevent initialization errors in agents that don't need it.
        # kwargs['enable_search'] = True 
    
    return LLMWrapper(provider=provider, model=model_name, **kwargs)
