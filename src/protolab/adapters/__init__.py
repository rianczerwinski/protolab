"""Adapter registry for eval framework integration.

Adapters translate eval framework output into protolab's correction schema.
Built-in adapters are registered at import time; custom adapters are defined
in ``protolab.toml`` under ``[import.<name>]`` sections.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import Config
from .base import BaseAdapter

logger = logging.getLogger(__name__)

# Built-in adapter classes, keyed by name
_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(name: str) -> Any:
    """Class decorator: register a built-in adapter under *name*."""

    def decorator(cls: type[BaseAdapter]) -> type[BaseAdapter]:
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_adapter(name: str, config: Config | None = None) -> BaseAdapter:
    """Resolve an adapter by name.

    Checks built-in adapters first, then custom import schemas from config.
    Raises ``ValueError`` if the name is unknown.
    """
    # Built-in adapter
    if name in _REGISTRY:
        return _REGISTRY[name]()

    # Custom schema from config
    if config and name in config.import_schemas:
        from .generic import GenericAdapter

        return GenericAdapter(config.import_schemas[name])

    available = list_adapters(config)
    raise ValueError(
        f"Unknown adapter '{name}'. Available: {', '.join(available) or 'none'}"
    )


def list_adapters(config: Config | None = None) -> list[str]:
    """Return names of all available adapters (built-in + custom)."""
    names = sorted(_REGISTRY)
    if config:
        names.extend(sorted(config.import_schemas))
    return names


# Import built-in adapters to trigger registration
from . import braintrust as _braintrust  # noqa: E402, F401
from . import promptfoo as _promptfoo  # noqa: E402, F401
