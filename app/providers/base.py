from dataclasses import dataclass
from typing import Any
@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
class ProviderError(Exception):
    def __init__(self, message, retryable=False): super().__init__(message); self.retryable=retryable
class BaseProvider:
    name='base'; supports_vision=False
    async def analyze(self, prompt: str, images: list[bytes]|None=None) -> ProviderResult: raise NotImplementedError
