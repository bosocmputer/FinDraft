from openai import AsyncOpenAI
from .base_provider import BaseAIProvider, AIMessage, AIResponse


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, message: AIMessage, temperature: float = 0.0) -> AIResponse:
        resp = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": message.system},
                {"role": "user", "content": message.user},
            ],
        )
        choice = resp.choices[0]
        return AIResponse(
            content=choice.message.content,
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
        )

    def provider_name(self) -> str:
        return "openai"
