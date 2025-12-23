"""
OpenAI provider implementation.
TODO: Full implementation in Phase 2
"""
from typing import List, Dict, Optional
from .base import LLMProvider, EmbeddingProvider
from ..config import Config


class OpenAILLMProvider(LLMProvider):
    """OpenAI GPT LLM provider. TODO: Phase 2 implementation"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.7, **kwargs) -> str:
        raise NotImplementedError("OpenAI provider: Phase 2")

    def generate_with_messages(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, temperature: float = 0.7, **kwargs) -> str:
        raise NotImplementedError("OpenAI provider: Phase 2")

    def get_model_name(self) -> str:
        return self.model

    def is_available(self) -> bool:
        return self.api_key is not None


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings provider. TODO: Phase 2 implementation"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("OpenAI embeddings: Phase 2")

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError("OpenAI embeddings: Phase 2")

    def get_embedding_dimension(self) -> int:
        return 1536  # text-embedding-ada-002

    def is_available(self) -> bool:
        return self.api_key is not None
