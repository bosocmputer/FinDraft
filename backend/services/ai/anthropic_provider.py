import anthropic
from .base_provider import BaseAIProvider, AIMessage, AIResponse


class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, message: AIMessage, temperature: float = 0.0) -> AIResponse:
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=message.system,
            messages=[{"role": "user", "content": message.user}],
        )
        return AIResponse(
            content=resp.content[0].text,
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )

    def provider_name(self) -> str:
        return "anthropic"
