"""Config-driven adapter for custom eval schemas.

Uses dot-path field mappings defined in ``[import.<name>]`` sections of
``protolab.toml`` to extract correction data from arbitrary nested structures.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..config import ImportSchema
from .base import BaseAdapter, CorrectionStub, read_file, resolve_path

logger = logging.getLogger(__name__)


class GenericAdapter(BaseAdapter):
    """Adapter driven by an ``ImportSchema`` from protolab.toml."""

    formats = (".jsonl", ".csv", ".json")

    def __init__(self, schema: ImportSchema) -> None:
        self.name = "generic"
        self.schema = schema

    def parse(self, path: Path) -> list[CorrectionStub]:
        rows = read_file(path)
        stubs: list[CorrectionStub] = []
        skipped = 0

        for i, row in enumerate(rows):
            # Apply filter if configured
            if self.schema.filter_field and self.schema.filter_value:
                actual = resolve_path(row, self.schema.filter_field)
                if str(actual) != self.schema.filter_value:
                    continue

            subject = self._resolve_or_default(row, self.schema.subject, None)
            step = self._resolve_or_default(row, self.schema.step, None)
            protocol_output = self._resolve_or_default(
                row, self.schema.protocol_output, None
            )

            if subject is None or step is None or protocol_output is None:
                logger.debug("Row %d: missing required field, skipping", i)
                skipped += 1
                continue

            correct_output = self._resolve_or_default(
                row, self.schema.correct_output, "TODO"
            )
            reasoning = self._resolve_or_default(row, self.schema.reasoning, "TODO")

            # Collect metadata fields
            metadata: dict[str, Any] = {}
            for field_path in self.schema.metadata_fields:
                val = resolve_path(row, field_path)
                if val is not None:
                    # Use the last segment of the dot-path as the key
                    key = field_path.rsplit(".", 1)[-1]
                    metadata[key] = val

            stubs.append(
                CorrectionStub(
                    subject=str(subject),
                    step=str(step),
                    protocol_output=str(protocol_output),
                    correct_output=str(correct_output),
                    reasoning=str(reasoning),
                    metadata=metadata,
                )
            )

        if skipped:
            logger.debug(
                "Generic adapter: %d rows skipped, %d imported",
                skipped,
                len(stubs),
            )
        return stubs

    @staticmethod
    def _resolve_or_default(row: dict[str, Any], path: str, default: Any) -> Any:
        """Resolve a dot-path; return the value, or default if not found.

        For optional fields (``default`` is not ``None``): if the path has
        no dots and isn't found in the row, treat the configured value as
        a literal string (e.g. ``"TODO"``).

        For required fields (``default is None``): missing path means the
        row is incomplete — return ``None`` so the caller can skip it.
        """
        value = resolve_path(row, path)
        if value is not None:
            return value
        if default is None:
            return None
        # Optional field: bare string that isn't a key is a literal default
        if "." not in path and path not in row:
            return path
        return default
