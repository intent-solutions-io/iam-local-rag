"""
OpenAI provider implementation using official SDK.
"""
from typing import List, Dict, Optional
import time
from .base import LLMProvider, EmbeddingProvider
from ..config import Config


class OpenAILLMProvider(LLMProvider):
    """OpenAI GPT LLM provider using official Python SDK"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.OPENAI_MODEL

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY required. Set it in .env file:\n"
                "OPENAI_API_KEY=sk-..."
            )

        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Install with:\n"
                    "pip install openai"
                )
        return self._client

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        # Convert to messages format
        messages = [{"role": "user", "content": prompt}]
        return self.generate_with_messages(messages, max_tokens, temperature, **kwargs)

    def generate_with_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from messages"""
        client = self._get_client()
        max_tokens = max_tokens or 1024

        # Retry logic for rate limits
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

                return response.choices[0].message.content

            except Exception as e:
                error_str = str(e).lower()

                # Rate limit or server errors
                if 'rate' in error_str or '429' in error_str or '5' in error_str[:3]:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    else:
                        raise ValueError(f"API error after {max_retries} retries: {str(e)}")
                else:
                    raise

        raise ValueError("Max retries exceeded")

    def get_model_name(self) -> str:
        return self.model

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings provider using official SDK"""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-ada-002"):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY required. Set it in .env file:\n"
                "OPENAI_API_KEY=sk-..."
            )

        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Install with:\n"
                    "pip install openai"
                )
        return self._client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents"""
        client = self._get_client()

        # OpenAI has a max batch size, process in chunks
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.embeddings.create(
                        model=self.model,
                        input=batch
                    )

                    embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(embeddings)
                    break

                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1.0 * (2 ** attempt))
                        continue
                    else:
                        raise

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for query"""
        return self.embed_documents([text])[0]

    def get_embedding_dimension(self) -> int:
        return 1536  # text-embedding-ada-002

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False
