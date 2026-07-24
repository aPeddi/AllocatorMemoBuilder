"""Project exception hierarchy.

A single base (``AmbError``) so callers can catch "anything this package raised"
distinctly from arbitrary bugs, with narrow subclasses per subsystem. Prefer
raising these over returning ``None`` for genuine failures; reserve ``None`` for
values that are legitimately absent (e.g. a metric that is mathematically
undefined), never for "something broke."
"""
from __future__ import annotations


class AmbError(Exception):
    """Base class for every error this package raises deliberately."""


class IngestError(AmbError):
    """A CSV could not be parsed into the expected fund/return shape."""


class MarketDataError(AmbError):
    """A benchmark / risk-free source (FRED, cache, snapshot) could not be resolved."""


class LLMError(AmbError):
    """A claims provider failed to produce a usable payload."""


class ConfigError(AmbError):
    """Configuration is missing or invalid for the requested operation."""
