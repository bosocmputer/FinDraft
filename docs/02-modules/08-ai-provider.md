# Module 8 — AI Provider Abstraction

_Blueprint v3.2 | [← Index](../README.md)_

---

## หลักการ

ระบบไม่ผูกกับ provider ใด — `account_mapper.py` และ `draft_engine.py` เรียกผ่าน **abstract interface** เสมอ
admin ของแต่ละ org เลือก provider + model + API key ของตัวเองได้จากหน้า Settings

## Providers ที่รองรับ

| Provider    | Model เริ่มต้น           | หมายเหตุ                                        |
| ----------- | ------------------------ | ----------------------------------------------- |
| Anthropic   | claude-sonnet-4-6        | default — แนะนำสำหรับภาษาไทย                    |
| OpenAI      | gpt-4o                   | รองรับ JSON mode                                 |
| Gemini      | gemini-2.0-flash         | Google AI Studio / Vertex AI                    |
| OpenRouter  | (user เลือก model เอง)   | gateway รวม provider อื่น — ใช้ OpenAI-compat API |

## Abstract Base Class

```python
# services/ai/base_provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AIMessage:
    system: str
    user: str

@dataclass
class AIResponse:
    content: str          # raw text จาก provider
    model: str            # model ที่ใช้จริง
    input_tokens: int
    output_tokens: int

class BaseAIProvider(ABC):
    """Interface กลาง — ทุก provider ต้อง implement"""

    @abstractmethod
    async def complete(self, message: AIMessage, temperature: float = 0.0) -> AIResponse:
        """ส่ง prompt และรับ response เป็น text"""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...
```

## Anthropic Provider

```python
# services/ai/anthropic_provider.py
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
```

## OpenAI Provider

```python
# services/ai/openai_provider.py
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
            response_format={"type": "json_object"},  # JSON mode
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
```

## Gemini Provider

```python
# services/ai/gemini_provider.py
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
                response_mime_type="application/json",  # JSON mode
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
```

## OpenRouter Provider

```python
# services/ai/openrouter_provider.py
# OpenRouter ใช้ OpenAI-compatible API — เปลี่ยนแค่ base_url
from openai import AsyncOpenAI
from .base_provider import BaseAIProvider, AIMessage, AIResponse

class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str):
        # model เช่น "meta-llama/llama-3.3-70b-instruct" หรือ "google/gemini-2.0-flash"
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
```

## Provider Factory

```python
# services/ai/provider_factory.py
from .base_provider import BaseAIProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider

async def get_provider(org_id: str) -> BaseAIProvider:
    """
    ดึง provider config จาก DB ตาม org_id
    ถ้าไม่มี config → fallback ไป Anthropic (system default)
    """
    config = await get_org_ai_config(org_id)  # query จาก org_ai_configs table

    if not config:
        # fallback: ใช้ system-level Anthropic key จาก env
        import os
        return AnthropicProvider(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model="claude-sonnet-4-6",
        )

    provider = config["provider"]
    api_key = config["api_key"]      # encrypted ใน DB, decrypt ที่นี่
    model   = config["model"]

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
```

## การใช้งานใน Account Mapper

```python
# services/ai/account_mapper.py  (ตัวอย่างการเรียกใช้)
from .provider_factory import get_provider
from .base_provider import AIMessage
from .response_sanitizer import sanitize_and_parse_json

async def call_ai_mapper(batch: list[TBRow], org_id: str) -> str:
    provider = await get_provider(org_id)          # ดึง provider ตาม org
    message = AIMessage(
        system=SYSTEM_PROMPT_MAPPER,
        user=build_mapper_user_prompt(batch),
    )
    response = await provider.complete(message, temperature=0.0)
    return response.content                         # raw JSON string
```

## API Key Security

- API key ของ org เข้ารหัสด้วย **AES-256-GCM** ก่อนบันทึกลง DB (`org_ai_configs.api_key_encrypted`)
- Encryption key เก็บใน environment variable `AI_KEY_ENCRYPTION_SECRET` ไม่เก็บใน DB
- ไม่มี endpoint ที่ return API key กลับมาเป็น plaintext เด็ดขาด

```python
# utils/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64, secrets

SECRET = base64.b64decode(os.environ["AI_KEY_ENCRYPTION_SECRET"])  # 32 bytes

def encrypt_api_key(plaintext: str) -> str:
    nonce = secrets.token_bytes(12)
    ct = AESGCM(SECRET).encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_api_key(ciphertext: str) -> str:
    raw = base64.b64decode(ciphertext)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM(SECRET).decrypt(nonce, ct, None).decode()
```

## Claude Code Prompt

```
สร้าง AI Provider abstraction layer ใน services/ai/ ที่:
1. base_provider.py: abstract class BaseAIProvider พร้อม AIMessage และ AIResponse dataclass
2. anthropic_provider.py, openai_provider.py, gemini_provider.py, openrouter_provider.py
   ทุกตัว implement complete() และ provider_name()
3. provider_factory.py: get_provider(org_id) ดึง config จาก org_ai_configs table
   fallback เป็น Anthropic system key ถ้าไม่มี org config
4. utils/encryption.py: encrypt/decrypt API key ด้วย AES-256-GCM
5. account_mapper.py และ draft_engine.py เรียกใช้ผ่าน get_provider() เท่านั้น — ไม่ import provider โดยตรง
```
