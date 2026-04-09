from openai import AsyncOpenAI
from .base_provider import BaseAIProvider, AIMessage, AIResponse


class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model

    async def complete(self, message: AIMessage, temperature: float = 0.0) -> AIResponse:
        resp = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": message.system},
                {"role": "user", "content": message.user},
            ],
            extra_headers={
                "HTTP-Referer": "https://findraft.app",
                "X-Title": "FinDraft AI",
            },
        )
        choice = resp.choices[0]
        return AIResponse(
            content=choice.message.content,
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
        )

    def provider_name(self) -> str:
        return "openrouter"
