"""Anthropic Claude API client for the Cyber Intelligence Platform.

This module provides a typed wrapper around the Anthropic SDK for sending
prompts and returning plain-text completions. It is designed for use in the
backend service layer and includes environment validation, retries, logging,
and timeout handling.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from dotenv import load_dotenv

from backend.exceptions import CollectorError
from backend.logging_config import LOGGER

load_dotenv()

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover - import path may vary in runtime
    Anthropic = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class ClaudeClientError(Exception):
    """Raised when the Claude client cannot initialize or fulfill a request."""


class ClaudeClient:
    """Reusable client for sending prompts to Anthropic Claude models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ClaudeClientError(
                "ANTHROPIC_API_KEY is not set. Configure it in your environment or .env file."
            )

        if Anthropic is None:
            raise ClaudeClientError(
                "Anthropic SDK is not installed. Install it to use Claude integration."
            ) from _IMPORT_ERROR

        self.model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        self.max_tokens = max_tokens or int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = Anthropic(api_key=self.api_key, timeout=self.timeout_seconds)

    def send_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send a prompt to Claude and return the plain-text response."""
        if not prompt or not prompt.strip():
            raise ClaudeClientError("Prompt must not be empty.")

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=0.2,
                    system=system_prompt or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._extract_text(response)
            except Exception as exc:  # pragma: no cover - network/SDK exceptions
                LOGGER.exception("Claude request attempt %s failed: %s", attempt, exc)
                if attempt == self.max_retries:
                    raise ClaudeClientError(f"Claude request failed after {self.max_retries} attempts") from exc
                time.sleep(self._backoff_seconds(attempt))

        raise ClaudeClientError("Claude request did not complete")

    def _extract_text(self, response: Any) -> str:
        """Extract plain text content from the Anthropic SDK response."""
        try:
            parts = getattr(response, "content", []) or []
            if not parts:
                return ""
            text_chunks = [getattr(part, "text", "") for part in parts if getattr(part, "text", None)]
            return "".join(text_chunks).strip()
        except Exception as exc:  # pragma: no cover - defensive fallback
            LOGGER.exception("Failed to parse Claude response: %s", exc)
            raise ClaudeClientError("Claude returned an unexpected response format") from exc

    def _backoff_seconds(self, attempt: int) -> int:
        return min(2**attempt, 8)
