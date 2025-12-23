"""
Policy enforcement for hybrid safety mode.
Ensures documents stay local; only snippets go to cloud.
"""
import hashlib
from typing import List, Tuple
from .config import Config
from .models import Citation


class PolicyRedactor:
    """
    Enforces hybrid safety mode policies.
    - Truncates snippets to MAX_SNIPPET_LENGTH
    - Records content hashes (not actual content)
    - Prevents full documents from reaching cloud providers
    """

    def __init__(
        self,
        hybrid_safe_mode: bool = None,
        max_snippet_length: int = None
    ):
        """
        Initialize policy redactor.

        Args:
            hybrid_safe_mode: Enable safety mode (defaults to Config)
            max_snippet_length: Max chars per snippet (defaults to Config)
        """
        self.hybrid_safe_mode = hybrid_safe_mode if hybrid_safe_mode is not None else Config.HYBRID_SAFE_MODE
        self.max_snippet_length = max_snippet_length if max_snippet_length is not None else Config.MAX_SNIPPET_LENGTH

    def redact_snippets(
        self,
        citations: List[Citation]
    ) -> Tuple[str, List[str]]:
        """
        Redact citations into safe snippets for cloud transmission.

        Args:
            citations: List of citations with full excerpts

        Returns:
            Tuple of (combined_context, list of excerpt_hashes)
        """
        safe_snippets = []
        excerpt_hashes = []

        for citation in citations:
            # Get excerpt
            excerpt = citation.excerpt

            # Hash the full excerpt BEFORE truncation (for audit)
            excerpt_hash = self._hash_content(excerpt)
            excerpt_hashes.append(excerpt_hash)

            # Truncate if in safe mode
            if self.hybrid_safe_mode:
                if len(excerpt) > self.max_snippet_length:
                    excerpt = excerpt[:self.max_snippet_length] + "..."

            # Add source attribution
            source_info = f"[Source: {citation.source}"
            if citation.page:
                source_info += f", Page {citation.page}"
            source_info += "]"

            safe_snippet = f"{source_info}\n{excerpt}"
            safe_snippets.append(safe_snippet)

        # Combine all snippets
        combined_context = "\n\n---\n\n".join(safe_snippets)

        # Final length check
        if self.hybrid_safe_mode and len(combined_context) > self.max_snippet_length * len(citations):
            # Emergency truncation if combined length exceeds reasonable bounds
            max_total = self.max_snippet_length * len(citations)
            combined_context = combined_context[:max_total] + "\n\n[Context truncated for safety]"

        return combined_context, excerpt_hashes

    def validate_outbound_payload(
        self,
        payload: str,
        sentinel: str = None
    ) -> bool:
        """
        Validate that outbound payload doesn't contain forbidden content.

        Args:
            payload: Text being sent to cloud
            sentinel: Optional sentinel string that MUST NOT appear (for testing)

        Returns:
            True if payload is safe, False if it contains forbidden content
        """
        # Check length
        if self.hybrid_safe_mode:
            # Allow some overhead for formatting
            max_allowed = self.max_snippet_length * 10  # Reasonable multiplier
            if len(payload) > max_allowed:
                return False

        # Check for sentinel (used in tests to ensure full docs don't leak)
        if sentinel and sentinel in payload:
            return False

        return True

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_policy_summary(self) -> dict:
        """Get current policy settings for logging"""
        return {
            "hybrid_safe_mode": self.hybrid_safe_mode,
            "max_snippet_length": self.max_snippet_length,
            "policy_enforced": True
        }
