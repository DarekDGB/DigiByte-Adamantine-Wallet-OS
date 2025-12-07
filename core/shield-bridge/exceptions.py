"""
Custom exceptions for Shield Bridge runtime skeleton.

MIT Licensed.
Author: @Darek_DGB
"""


class ShieldBridgeError(Exception):
    """Base error type for Shield Bridge."""


class LayerUnavailableError(ShieldBridgeError):
    """
    Raised when a configured layer cannot be reached
    or fails in a non-recoverable way.
    """


class AggregationError(ShieldBridgeError):
    """Raised when risk aggregation cannot be completed."""
