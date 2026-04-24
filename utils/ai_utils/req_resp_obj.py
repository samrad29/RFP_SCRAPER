from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    model: str
    provider: str  # "groq" or "openai"
    temperature: float = 0.0

@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    provider: str