"""Isolated Anthropic API wrapper.

All provider-specific code lives here. When LLM-agnostic support is added,
this module grows a provider abstraction; nothing else changes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 8192


def call_anthropic(model: str, api_key: str, prompt: str) -> str:
    """Call the Anthropic messages API and return the response text.

    Raises ``ImportError`` with install instructions if the ``anthropic``
    package is not available. Raises ``RuntimeError`` if the API returns
    an empty response.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for --run. "
            "Install it with: pip install protolab[ai]"
        )

    logger.debug("Calling %s (prompt length: %d chars)", model, len(prompt))

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content:
        raise RuntimeError("LLM returned empty response.")

    text = response.content[0].text
    logger.debug("Response received (%d chars)", len(text))
    return text
