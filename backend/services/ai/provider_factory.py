import os
from .base_provider import BaseAIProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider


async def get_org_ai_config(org_id: str) -> dict | None:
    """
    ดึง config จาก org_ai_configs table
    TODO: implement DB query + decrypt api_key
    """
    return None  # placeholder — fallback to system default


async def get_provider(org_id: str) -> BaseAIProvider:
    """
    ดึง provider config จาก DB ตาม org_id
    ถ้าไม่มี config → fallback ไป Anthropic (system default)
    """
    config = await get_org_ai_config(org_id)

    if not config:
        # System default — ดึงจาก env (ตอนนี้ใช้ OpenRouter)
        provider_env = os.getenv("AI_PROVIDER", "openrouter")
        if provider_env == "openrouter":
            return OpenRouterProvider(
                api_key=os.environ["OPENROUTER_API_KEY"],
                model=os.getenv("AI_MODEL", "meta-llama/llama-3.3-70b-instruct"),
            )
        return AnthropicProvider(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        )

    provider = config["provider"]
    api_key = config["api_key"]  # already decrypted
    model = config["model"]

    if provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    elif provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    elif provider == "gemini":
        return GeminiProvider(api_key=api_key, model=model)
    elif provider == "openrouter":
        return OpenRouterProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
