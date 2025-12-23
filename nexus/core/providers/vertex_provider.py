"""
Google Vertex AI provider implementation.
TODO: Full implementation in Phase 2
"""
from typing import List, Dict, Optional
from .base import LLMProvider, EmbeddingProvider
from ..config import Config


class VertexLLMProvider(LLMProvider):
    """Vertex AI Gemini LLM provider. TODO: Phase 2"""

    def __init__(self, project: Optional[str] = None, region: Optional[str] = None, model: Optional[str] = None):
        self.project = project or Config.GOOGLE_CLOUD_PROJECT
        self.region = region or Config.GOOGLE_CLOUD_REGION
        self.model = model or Config.VERTEX_MODEL
        if not self.project:
            raise ValueError("GOOGLE_CLOUD_PROJECT required")

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.7, **kwargs) -> str:
        raise NotImplementedError("Vertex AI provider: Phase 2")

    def generate_with_messages(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, temperature: float = 0.7, **kwargs) -> str:
        raise NotImplementedError("Vertex AI provider: Phase 2")

    def get_model_name(self) -> str:
        return self.model

    def is_available(self) -> bool:
        return self.project is not None


class VertexEmbeddingProvider(EmbeddingProvider):
    """Vertex AI embeddings provider. TODO: Phase 2"""

    def __init__(self, project: Optional[str] = None, region: Optional[str] = None):
        self.project = project or Config.GOOGLE_CLOUD_PROJECT
        self.region = region or Config.GOOGLE_CLOUD_REGION
        if not self.project:
            raise ValueError("GOOGLE_CLOUD_PROJECT required")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Vertex embeddings: Phase 2")

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError("Vertex embeddings: Phase 2")

    def get_embedding_dimension(self) -> int:
        return 768  # textembedding-gecko

    def is_available(self) -> bool:
        return self.project is not None
