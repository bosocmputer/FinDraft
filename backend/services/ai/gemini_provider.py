import google.generativeai as genai
from .base_provider import BaseAIProvider, AIMessage, AIResponse


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model

    async def complete(self, message: AIMessage, temperature: float = 0.0) -> AIResponse:
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=message.system,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
        resp = await model.generate_content_async(message.user)
        return AIResponse(
            content=resp.text,
            model=self.model_name,
            input_tokens=resp.usage_metadata.prompt_token_count,
            output_tokens=resp.usage_metadata.candidates_token_count,
        )

    def provider_name(self) -> str:
        return "gemini"
