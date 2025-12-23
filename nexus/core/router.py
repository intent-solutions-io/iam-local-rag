"""
Provider router - selects LLM and Embedding providers based on configuration.
"""
from typing import Tuple
from .config import Config, NexusMode, LLMProvider as LLMProviderEnum, EmbeddingProvider as EmbeddingProviderEnum
from .providers.base import LLMProvider, EmbeddingProvider
from .providers.ollama_provider import OllamaLLMProvider, OllamaEmbeddingProvider
from .providers.anthropic_provider import AnthropicLLMProvider
from .providers.openai_provider import OpenAILLMProvider, OpenAIEmbeddingProvider
from .providers.vertex_provider import VertexLLMProvider, VertexEmbeddingProvider


class ProviderRouter:
    """
    Routes to appropriate LLM and Embedding providers based on configuration.
    Enforces mode-based constraints (local/cloud/hybrid).
    """

    @staticmethod
    def get_llm_provider(
        provider_name: str = None,
        mode: str = None
    ) -> LLMProvider:
        """
        Get LLM provider instance based on configuration.

        Args:
            provider_name: Override provider (defaults to Config.NEXUS_LLM_PROVIDER)
            mode: Override mode (defaults to Config.NEXUS_MODE)

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider not available or misconfigured
        """
        provider_name = provider_name or Config.NEXUS_LLM_PROVIDER.value
        mode = mode or Config.NEXUS_MODE.value

        # Enforce mode constraints
        if mode == NexusMode.LOCAL and provider_name != LLMProviderEnum.OLLAMA.value:
            raise ValueError(
                f"LOCAL mode requires Ollama provider, got: {provider_name}. "
                f"Set NEXUS_LLM_PROVIDER=ollama or change NEXUS_MODE."
            )

        # Select provider
        if provider_name == LLMProviderEnum.OLLAMA.value:
            return OllamaLLMProvider()

        elif provider_name == LLMProviderEnum.ANTHROPIC.value:
            if not Config.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY required for Anthropic provider. "
                    "Set it in .env or use NEXUS_LLM_PROVIDER=ollama for local-only."
                )
            return AnthropicLLMProvider()

        elif provider_name == LLMProviderEnum.OPENAI.value:
            if not Config.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY required for OpenAI provider. "
                    "Set it in .env or use NEXUS_LLM_PROVIDER=ollama for local-only."
                )
            return OpenAILLMProvider()

        elif provider_name == LLMProviderEnum.VERTEX.value:
            if not Config.GOOGLE_CLOUD_PROJECT:
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT required for Vertex provider. "
                    "Set it in .env or use NEXUS_LLM_PROVIDER=ollama for local-only."
                )
            return VertexLLMProvider()

        else:
            raise ValueError(
                f"Unknown LLM provider: {provider_name}. "
                f"Valid options: {[p.value for p in LLMProviderEnum]}"
            )

    @staticmethod
    def get_embedding_provider(
        provider_name: str = None,
        mode: str = None
    ) -> EmbeddingProvider:
        """
        Get Embedding provider instance based on configuration.

        Args:
            provider_name: Override provider (defaults to Config.NEXUS_EMBED_PROVIDER)
            mode: Override mode (defaults to Config.NEXUS_MODE)

        Returns:
            EmbeddingProvider instance

        Raises:
            ValueError: If provider not available or misconfigured
        """
        provider_name = provider_name or Config.NEXUS_EMBED_PROVIDER.value
        mode = mode or Config.NEXUS_MODE.value

        # Enforce mode constraints
        # Note: Hybrid mode typically uses LOCAL embeddings (retrieval local)
        # But we allow override if user explicitly configures cloud embeddings
        if mode == NexusMode.LOCAL and provider_name != EmbeddingProviderEnum.OLLAMA.value:
            raise ValueError(
                f"LOCAL mode requires Ollama embeddings, got: {provider_name}. "
                f"Set NEXUS_EMBED_PROVIDER=ollama or change NEXUS_MODE."
            )

        # Select provider
        if provider_name == EmbeddingProviderEnum.OLLAMA.value:
            return OllamaEmbeddingProvider()

        elif provider_name == EmbeddingProviderEnum.OPENAI.value:
            if not Config.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY required for OpenAI embeddings. "
                    "Set it in .env or use NEXUS_EMBED_PROVIDER=ollama."
                )
            return OpenAIEmbeddingProvider()

        elif provider_name == EmbeddingProviderEnum.VERTEX.value:
            if not Config.GOOGLE_CLOUD_PROJECT:
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT required for Vertex embeddings. "
                    "Set it in .env or use NEXUS_EMBED_PROVIDER=ollama."
                )
            return VertexEmbeddingProvider()

        else:
            raise ValueError(
                f"Unknown Embedding provider: {provider_name}. "
                f"Valid options: {[p.value for p in EmbeddingProviderEnum]}"
            )

    @staticmethod
    def get_providers(
        llm_provider_name: str = None,
        embed_provider_name: str = None,
        mode: str = None
    ) -> Tuple[LLMProvider, EmbeddingProvider]:
        """
        Get both LLM and Embedding providers based on configuration.

        Args:
            llm_provider_name: Override LLM provider
            embed_provider_name: Override Embedding provider
            mode: Override mode

        Returns:
            Tuple of (LLMProvider, EmbeddingProvider)
        """
        llm = ProviderRouter.get_llm_provider(llm_provider_name, mode)
        embed = ProviderRouter.get_embedding_provider(embed_provider_name, mode)

        return llm, embed

    @staticmethod
    def validate_configuration() -> dict:
        """
        Validate current configuration and return status.

        Returns:
            Dict with validation results
        """
        results = {
            "valid": True,
            "mode": Config.NEXUS_MODE.value,
            "llm_provider": Config.NEXUS_LLM_PROVIDER.value,
            "embed_provider": Config.NEXUS_EMBED_PROVIDER.value,
            "warnings": [],
            "errors": []
        }

        # Check LLM provider
        try:
            llm = ProviderRouter.get_llm_provider()
            results["llm_available"] = llm.is_available()
            if not results["llm_available"]:
                results["warnings"].append(f"LLM provider {Config.NEXUS_LLM_PROVIDER.value} not available")
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"LLM provider error: {str(e)}")
            results["llm_available"] = False

        # Check Embedding provider
        try:
            embed = ProviderRouter.get_embedding_provider()
            results["embed_available"] = embed.is_available()
            if not results["embed_available"]:
                results["warnings"].append(f"Embedding provider {Config.NEXUS_EMBED_PROVIDER.value} not available")
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Embedding provider error: {str(e)}")
            results["embed_available"] = False

        # Check mode-specific constraints
        if Config.NEXUS_MODE == NexusMode.HYBRID:
            if Config.HYBRID_SAFE_MODE:
                results["safety_mode"] = "HYBRID SAFE (docs local, snippets only to cloud)"
            else:
                results["warnings"].append("HYBRID_SAFE_MODE disabled - full docs may be sent to cloud")

        return results
