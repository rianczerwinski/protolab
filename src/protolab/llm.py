"""Isolated Anthropic API wrapper.

All provider-specific code lives here. When LLM-agnostic support is added,
this module grows a provider abstraction; nothing else changes.
"""

from __future__ import annotations


def call_anthropic(model: str, api_key: str, prompt: str) -> str:
    """Call Anthropic messages API. Return response text.

    Raises clear error if anthropic package not installed.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for --run. "
            "Install it with: pip install protolab[ai]"
        )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content:
        raise RuntimeError("LLM returned empty response.")
    return response.content[0].text
