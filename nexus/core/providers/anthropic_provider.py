"""
Anthropic Claude provider implementation.
TODO: Full implementation in Phase 2
"""
from typing import List, Dict, Optional
from .base import LLMProvider
from ..config import Config


class AnthropicLLMProvider(LLMProvider):
    """
    Anthropic Claude LLM provider.

    TODO Phase 2:
    - Implement using official Anthropic Python SDK
    - Add message formatting for Claude
    - Add streaming support
    - Handle rate limits and retries
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.model = model or Config.ANTHROPIC_MODEL

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        # TODO: Implement using Anthropic SDK
        raise NotImplementedError(
            "Anthropic provider will be implemented in Phase 2. "
            "Use NEXUS_LLM_PROVIDER=ollama for now."
        )

    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate from messages"""
        # TODO: Implement using Anthropic SDK messages API
        raise NotImplementedError(
            "Anthropic provider will be implemented in Phase 2"
        )

    def get_model_name(self) -> str:
        """Return model identifier"""
        return self.model

    def is_available(self) -> bool:
        """Check if provider is configured"""
        return self.api_key is not None
