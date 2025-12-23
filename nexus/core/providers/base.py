"""
Base provider interfaces for LLM and Embedding providers.
All providers must implement these abstract base classes.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a list of messages (chat format).

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured"""
        pass


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured"""
        pass
