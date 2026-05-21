import os
import hashlib
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

# Generic OpenAI-compatible LLM config
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or "https://api.deepseek.com/v1/chat/completions"
)
DEFAULT_MODEL = os.getenv("LLM_MODEL_NAME") or os.getenv("AGENT_MODEL", "deepseek-v4-flash")

# Simple LRU cache for LLM calls — keyed by hash of (model, messages, temperature)
_llm_cache: dict[str, str] = {}
_CACHE_MAX = 500


def _cache_key(messages: list[dict], model: str, temperature: float) -> str:
    raw = json.dumps({"m": messages, "model": model, "t": temperature}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def call_llm(
    messages: list[dict],
    model: str = None,
    thinking: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    use_cache: bool = False,
) -> str:
    """
    OpenAI-compatible LLM API wrapper. Supports any provider (DeepSeek, Qwen,
    OpenAI, Anthropic, Groq, etc.) via configurable base URL.

    Args:
        messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
        model: model name string
        thinking: enable chain-of-thought reasoning (DeepSeek only)
        max_tokens: max tokens in response
        temperature: 0.0 = deterministic, 1.0 = creative
        use_cache: if True, cache responses to avoid duplicate API calls

    Returns:
        response text content
    """
    model = model or DEFAULT_MODEL

    # Check cache for deterministic calls
    if use_cache and temperature == 0:
        key = _cache_key(messages, model, temperature)
        if key in _llm_cache:
            return _llm_cache[key]

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    # DeepSeek-specific thinking tokens — safe to include for other providers
    # (they'll just ignore the field)
    if thinking:
        payload["thinking"] = {"type": "enabled"}

    try:
        response = httpx.post(
            LLM_BASE_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"]

        # Store in cache
        if use_cache and temperature == 0:
            if len(_llm_cache) < _CACHE_MAX:
                _llm_cache[key] = result
            # Simple evict if full
            elif _llm_cache:
                _llm_cache.pop(next(iter(_llm_cache)))

        return result
    except httpx.HTTPStatusError as e:
        print(f"[LLM ERROR] HTTP {e.response.status_code}: {e.response.text[:500]}")
        raise
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        raise
