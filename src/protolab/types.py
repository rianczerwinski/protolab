"""Protolab data types.

TypedDict definitions for correction and rule dicts. These serve as
schema documentation, enable IDE autocompletion, and catch field typos
at type-check time. Runtime behavior is unaffected — TypedDict is
structural, not enforced.
"""

from __future__ import annotations

from datetime import datetime
from typing import NotRequired, TypedDict


class Correction(TypedDict):
    """A structured record of a protocol error and its resolution."""

    id: str
    subject: str
    date: datetime
    protocol_version: str
    step: str
    protocol_output: str
    correct_output: str
    reasoning: str
    rule: NotRequired[str]


class Rule(TypedDict):
    """A generalizable discriminator extracted from corrections."""

    id: str
    decision_point: str
    rule: str
    confidence: str  # one of CONFIDENCE_LEVELS
    source: str  # correction ID
    date_added: datetime


CONFIDENCE_LEVELS = ("provisional", "strong_pattern", "structural")

REQUIRED_CORRECTION_FIELDS = frozenset({
    "subject", "step", "protocol_output", "correct_output", "reasoning",
})
