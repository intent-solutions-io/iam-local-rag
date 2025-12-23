"""
Unit tests for PolicyRedactor.
Tests snippet redaction, payload validation, and hybrid safety.
"""
import pytest
from nexus.core.policy import PolicyRedactor
from nexus.core.models import Citation


class TestPolicyRedactor:
    """Test suite for PolicyRedactor"""

    def test_initialization_defaults(self):
        """Test PolicyRedactor initializes with defaults from Config"""
        policy = PolicyRedactor()
        assert policy.hybrid_safe_mode is True  # Default from Config
        assert policy.max_snippet_length == 4000  # Default from Config

    def test_initialization_override(self):
        """Test PolicyRedactor can override defaults"""
        policy = PolicyRedactor(hybrid_safe_mode=False, max_snippet_length=1000)
        assert policy.hybrid_safe_mode is False
        assert policy.max_snippet_length == 1000

    def test_redact_snippets_truncates_in_safe_mode(self):
        """Test snippets are truncated when hybrid_safe_mode is enabled"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=100)

        # Create citation with long excerpt
        long_text = "A" * 200
        citations = [Citation(
            source="test.pdf",
            page=1,
            excerpt=long_text,
            relevance_score=0.9,
            content_hash="hash123"
        )]

        safe_context, hashes = policy.redact_snippets(citations)

        # Should be truncated to 100 chars + "..."
        assert len(safe_context) < 200
        assert "..." in safe_context
        assert len(hashes) == 1

    def test_redact_snippets_no_truncation_when_disabled(self):
        """Test snippets are NOT truncated when hybrid_safe_mode is disabled"""
        policy = PolicyRedactor(hybrid_safe_mode=False, max_snippet_length=100)

        # Create citation with long excerpt
        long_text = "A" * 200
        citations = [Citation(
            source="test.pdf",
            page=1,
            excerpt=long_text,
            relevance_score=0.9,
            content_hash="hash123"
        )]

        safe_context, hashes = policy.redact_snippets(citations)

        # Should NOT be truncated
        assert long_text in safe_context
        assert len(hashes) == 1

    def test_redact_snippets_includes_source_attribution(self):
        """Test redacted snippets include source attribution"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        citations = [Citation(
            source="document.pdf",
            page=5,
            excerpt="This is some content",
            relevance_score=0.9,
            content_hash="hash123"
        )]

        safe_context, hashes = policy.redact_snippets(citations)

        # Should include source attribution
        assert "[Source: document.pdf, Page 5]" in safe_context
        assert "This is some content" in safe_context

    def test_redact_snippets_multiple_citations(self):
        """Test multiple citations are separated correctly"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        citations = [
            Citation(
                source="doc1.pdf",
                page=1,
                excerpt="First document",
                relevance_score=0.9,
                content_hash="hash1"
            ),
            Citation(
                source="doc2.pdf",
                page=2,
                excerpt="Second document",
                relevance_score=0.8,
                content_hash="hash2"
            )
        ]

        safe_context, hashes = policy.redact_snippets(citations)

        # Should have separator
        assert "---" in safe_context
        assert "First document" in safe_context
        assert "Second document" in safe_context
        assert len(hashes) == 2

    def test_redact_snippets_emergency_truncation(self):
        """Test emergency truncation when combined context exceeds bounds"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=100)

        # Create many citations with moderately long excerpts
        citations = [
            Citation(
                source=f"doc{i}.pdf",
                page=i,
                excerpt="A" * 90,  # Each 90 chars (under 100)
                relevance_score=0.9,
                content_hash=f"hash{i}"
            )
            for i in range(20)  # 20 citations
        ]

        safe_context, hashes = policy.redact_snippets(citations)

        # Total should be capped at max_snippet_length * num_citations
        max_allowed = 100 * 20
        assert len(safe_context) <= max_allowed + 100  # Some overhead for safety msg
        assert len(hashes) == 20

    def test_validate_outbound_payload_passes_short_payload(self):
        """Test short payloads pass validation"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        payload = "Short query with context"
        result = policy.validate_outbound_payload(payload)

        assert result is True

    def test_validate_outbound_payload_fails_long_payload(self):
        """Test excessively long payloads fail validation"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        # Payload exceeds max_snippet_length * 10
        payload = "A" * 20000
        result = policy.validate_outbound_payload(payload)

        assert result is False

    def test_validate_outbound_payload_sentinel_detection(self):
        """Test sentinel strings are detected in payloads"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        payload = "This payload contains SECRET_SENTINEL that should not leak"
        result = policy.validate_outbound_payload(payload, sentinel="SECRET_SENTINEL")

        assert result is False

    def test_validate_outbound_payload_no_sentinel_passes(self):
        """Test payloads without sentinel pass"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=1000)

        payload = "This payload is safe"
        result = policy.validate_outbound_payload(payload, sentinel="SECRET_SENTINEL")

        assert result is True

    def test_validate_outbound_payload_disabled_safe_mode(self):
        """Test validation is relaxed when safe mode is disabled"""
        policy = PolicyRedactor(hybrid_safe_mode=False, max_snippet_length=1000)

        # Very long payload
        payload = "A" * 50000
        result = policy.validate_outbound_payload(payload)

        # Should pass because safe mode is disabled
        assert result is True

    def test_hash_content_consistency(self):
        """Test content hashing is consistent"""
        policy = PolicyRedactor()

        content = "Test content for hashing"
        hash1 = policy._hash_content(content)
        hash2 = policy._hash_content(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_hash_content_different_inputs(self):
        """Test different content produces different hashes"""
        policy = PolicyRedactor()

        hash1 = policy._hash_content("Content A")
        hash2 = policy._hash_content("Content B")

        assert hash1 != hash2

    def test_get_policy_summary(self):
        """Test policy summary contains expected fields"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=2000)

        summary = policy.get_policy_summary()

        assert summary["hybrid_safe_mode"] is True
        assert summary["max_snippet_length"] == 2000
        assert summary["policy_enforced"] is True

    def test_redact_snippets_preserves_hash_before_truncation(self):
        """Test excerpt hashes are computed BEFORE truncation"""
        policy = PolicyRedactor(hybrid_safe_mode=True, max_snippet_length=50)

        # Create citation with long excerpt
        full_text = "A" * 200
        citations = [Citation(
            source="test.pdf",
            page=1,
            excerpt=full_text,
            relevance_score=0.9,
            content_hash="hash123"
        )]

        safe_context, hashes = policy.redact_snippets(citations)

        # Hash should be of FULL text, not truncated version
        expected_hash = policy._hash_content(full_text)
        assert hashes[0] == expected_hash

        # But context should be truncated
        assert len(safe_context) < len(full_text)
