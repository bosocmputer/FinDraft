from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIMessage:
    system: str
    user: str


@dataclass
class AIResponse:
    content: str        # raw text จาก provider
    model: str          # model ที่ใช้จริง
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
