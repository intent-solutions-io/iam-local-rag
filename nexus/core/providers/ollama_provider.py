"""
Ollama provider implementation for local LLM and embeddings.
"""
from typing import List, Dict, Optional
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from .base import LLMProvider, EmbeddingProvider
from ..config import Config


class OllamaLLMProvider(LLMProvider):
    """Ollama LLM provider using LangChain"""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or Config.OLLAMA_MODEL
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self._llm = None

    def _get_llm(self):
        """Lazy initialization of Ollama LLM"""
        if self._llm is None:
            self._llm = Ollama(
                model=self.model,
                base_url=self.base_url
            )
        return self._llm

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        llm = self._get_llm()
        # Ollama doesn't use max_tokens the same way, but we can pass it through
        response = llm.invoke(prompt, temperature=temperature, **kwargs)
        return response

    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate from messages (convert to single prompt for Ollama)"""
        # Convert messages to single prompt
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        return self.generate(prompt, max_tokens, temperature, **kwargs)

    def get_model_name(self) -> str:
        """Return model identifier"""
        return self.model

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            llm = self._get_llm()
            # Try a simple generation to test availability
            llm.invoke("test", max_tokens=1)
            return True
        except Exception:
            return False


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider using LangChain"""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or Config.OLLAMA_MODEL
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self._embeddings = None

    def _get_embeddings(self):
        """Lazy initialization of Ollama embeddings"""
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                model=self.model,
                base_url=self.base_url
            )
        return self._embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents"""
        embeddings = self._get_embeddings()
        return embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for query"""
        embeddings = self._get_embeddings()
        return embeddings.embed_query(text)

    def get_embedding_dimension(self) -> int:
        """Return embedding dimension (Ollama llama3 uses 4096)"""
        # This varies by model, but typical for llama3
        return 4096

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            embeddings = self._get_embeddings()
            # Try a simple embedding to test availability
            embeddings.embed_query("test")
            return True
        except Exception:
            return False
