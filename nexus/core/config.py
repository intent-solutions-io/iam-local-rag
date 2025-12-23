"""
Configuration management for NEXUS.
Reads from environment variables with sensible defaults.
"""
import os
from enum import Enum
from typing import Optional
from pathlib import Path


class NexusMode(str, Enum):
    """Operating mode for NEXUS"""
    LOCAL = "local"  # Ollama only, no cloud
    CLOUD = "cloud"  # Cloud LLMs only
    HYBRID = "hybrid"  # Local retrieval + cloud generation


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    VERTEX = "vertex"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    VERTEX = "vertex"


class Config:
    """Central configuration for NEXUS"""

    # --- Mode Selection ---
    NEXUS_MODE: NexusMode = NexusMode(os.getenv("NEXUS_MODE", "hybrid"))

    # --- Provider Selection ---
    NEXUS_LLM_PROVIDER: LLMProvider = LLMProvider(
        os.getenv("NEXUS_LLM_PROVIDER", "ollama")
    )
    NEXUS_EMBED_PROVIDER: EmbeddingProvider = EmbeddingProvider(
        os.getenv("NEXUS_EMBED_PROVIDER", "ollama")
    )

    # --- Ollama Configuration ---
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # --- Anthropic Configuration ---
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # --- OpenAI Configuration ---
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # --- Vertex AI Configuration ---
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_REGION: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    VERTEX_MODEL: str = os.getenv("VERTEX_MODEL", "gemini-1.5-pro")

    # --- Document Processing ---
    DOCUMENTS_DIR: str = os.getenv("DOCUMENTS_DIR", "documents")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # --- Vector Store ---
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db_optimized")
    LEDGER_DB_PATH: str = os.getenv("LEDGER_DB_PATH", "./nexus_ledger.db")
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./rag_cache")
    INDEX_METADATA_PATH: str = os.getenv("INDEX_METADATA_PATH", "./index_metadata.json")

    # --- Performance Tuning ---
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "50"))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    MAX_CACHE_SIZE: int = int(os.getenv("MAX_CACHE_SIZE", "100"))

    # --- API Configuration ---
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))

    # --- Privacy/Security Settings ---
    HYBRID_SAFE_MODE: bool = os.getenv("HYBRID_SAFE_MODE", "true").lower() == "true"
    MAX_SNIPPET_LENGTH: int = int(os.getenv("MAX_SNIPPET_LENGTH", "4000"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration and check required keys"""
        # Check mode-specific requirements
        if cls.NEXUS_MODE in (NexusMode.CLOUD, NexusMode.HYBRID):
            if cls.NEXUS_LLM_PROVIDER == LLMProvider.ANTHROPIC and not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY required when using Anthropic provider")
            if cls.NEXUS_LLM_PROVIDER == LLMProvider.OPENAI and not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY required when using OpenAI provider")
            if cls.NEXUS_LLM_PROVIDER == LLMProvider.VERTEX and not cls.GOOGLE_CLOUD_PROJECT:
                raise ValueError("GOOGLE_CLOUD_PROJECT required when using Vertex provider")

        # Validate chunk settings
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")

        # Ensure directories exist
        Path(cls.DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.CACHE_DIR).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for logging/debugging"""
        return {
            "mode": cls.NEXUS_MODE.value,
            "llm_provider": cls.NEXUS_LLM_PROVIDER.value,
            "embed_provider": cls.NEXUS_EMBED_PROVIDER.value,
            "hybrid_safe_mode": cls.HYBRID_SAFE_MODE,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
        }
