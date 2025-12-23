"""
Unit tests for ProviderRouter.
Tests provider selection, mode constraints, and validation.
"""
import pytest
import os
from unittest.mock import patch

from nexus.core.router import ProviderRouter
from nexus.core.config import NexusMode, LLMProvider as LLMProviderEnum, EmbeddingProvider as EmbeddingProviderEnum
from nexus.core.providers.ollama_provider import OllamaLLMProvider, OllamaEmbeddingProvider
from nexus.core.providers.anthropic_provider import AnthropicLLMProvider
from nexus.core.providers.openai_provider import OpenAILLMProvider, OpenAIEmbeddingProvider
from nexus.core.providers.vertex_provider import VertexLLMProvider, VertexEmbeddingProvider


class TestProviderRouter:
    """Test suite for ProviderRouter"""

    def test_get_llm_provider_ollama(self):
        """Test Ollama LLM provider selection"""
        provider = ProviderRouter.get_llm_provider(
            provider_name=LLMProviderEnum.OLLAMA.value
        )
        assert isinstance(provider, OllamaLLMProvider)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    def test_get_llm_provider_anthropic(self):
        """Test Anthropic LLM provider selection"""
        provider = ProviderRouter.get_llm_provider(
            provider_name=LLMProviderEnum.ANTHROPIC.value
        )
        assert isinstance(provider, AnthropicLLMProvider)
        assert provider.api_key == "sk-ant-test123"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"})
    def test_get_llm_provider_openai(self):
        """Test OpenAI LLM provider selection"""
        provider = ProviderRouter.get_llm_provider(
            provider_name=LLMProviderEnum.OPENAI.value
        )
        assert isinstance(provider, OpenAILLMProvider)
        assert provider.api_key == "sk-test123"

    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_get_llm_provider_vertex(self):
        """Test Vertex AI LLM provider selection"""
        provider = ProviderRouter.get_llm_provider(
            provider_name=LLMProviderEnum.VERTEX.value
        )
        assert isinstance(provider, VertexLLMProvider)
        assert provider.project == "test-project"

    def test_get_llm_provider_unknown(self):
        """Test error on unknown LLM provider"""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            ProviderRouter.get_llm_provider(provider_name="unknown")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_provider_anthropic_missing_key(self):
        """Test error when Anthropic API key is missing"""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
            ProviderRouter.get_llm_provider(
                provider_name=LLMProviderEnum.ANTHROPIC.value
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_provider_openai_missing_key(self):
        """Test error when OpenAI API key is missing"""
        with pytest.raises(ValueError, match="OPENAI_API_KEY required"):
            ProviderRouter.get_llm_provider(
                provider_name=LLMProviderEnum.OPENAI.value
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_provider_vertex_missing_project(self):
        """Test error when Vertex project is missing"""
        with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT required"):
            ProviderRouter.get_llm_provider(
                provider_name=LLMProviderEnum.VERTEX.value
            )

    def test_local_mode_enforces_ollama_llm(self):
        """Test LOCAL mode enforces Ollama for LLM"""
        with pytest.raises(ValueError, match="LOCAL mode requires Ollama"):
            ProviderRouter.get_llm_provider(
                provider_name=LLMProviderEnum.ANTHROPIC.value,
                mode=NexusMode.LOCAL
            )

    def test_get_embedding_provider_ollama(self):
        """Test Ollama embedding provider selection"""
        provider = ProviderRouter.get_embedding_provider(
            provider_name=EmbeddingProviderEnum.OLLAMA.value
        )
        assert isinstance(provider, OllamaEmbeddingProvider)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"})
    def test_get_embedding_provider_openai(self):
        """Test OpenAI embedding provider selection"""
        provider = ProviderRouter.get_embedding_provider(
            provider_name=EmbeddingProviderEnum.OPENAI.value
        )
        assert isinstance(provider, OpenAIEmbeddingProvider)
        assert provider.api_key == "sk-test123"

    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_get_embedding_provider_vertex(self):
        """Test Vertex AI embedding provider selection"""
        provider = ProviderRouter.get_embedding_provider(
            provider_name=EmbeddingProviderEnum.VERTEX.value
        )
        assert isinstance(provider, VertexEmbeddingProvider)
        assert provider.project == "test-project"

    def test_get_embedding_provider_unknown(self):
        """Test error on unknown embedding provider"""
        with pytest.raises(ValueError, match="Unknown Embedding provider"):
            ProviderRouter.get_embedding_provider(provider_name="unknown")

    def test_local_mode_enforces_ollama_embedding(self):
        """Test LOCAL mode enforces Ollama for embeddings"""
        with pytest.raises(ValueError, match="LOCAL mode requires Ollama"):
            ProviderRouter.get_embedding_provider(
                provider_name=EmbeddingProviderEnum.OPENAI.value,
                mode=NexusMode.LOCAL
            )

    def test_get_providers_returns_both(self):
        """Test get_providers returns both LLM and embedding providers"""
        llm, embed = ProviderRouter.get_providers()
        assert llm is not None
        assert embed is not None

    def test_validate_configuration_ollama(self):
        """Test configuration validation with Ollama"""
        results = ProviderRouter.validate_configuration()

        assert "valid" in results
        assert "mode" in results
        assert "llm_provider" in results
        assert "embed_provider" in results
        assert "llm_available" in results
        assert "embed_available" in results

    @patch.dict(os.environ, {
        "NEXUS_MODE": "HYBRID",
        "HYBRID_SAFE_MODE": "false"
    })
    def test_validate_configuration_hybrid_unsafe_warning(self):
        """Test validation warns when HYBRID_SAFE_MODE is disabled"""
        results = ProviderRouter.validate_configuration()

        # Should have warning about unsafe hybrid mode
        warnings = results.get("warnings", [])
        assert any("HYBRID_SAFE_MODE disabled" in w for w in warnings)
