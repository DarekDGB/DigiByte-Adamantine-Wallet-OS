"""
Shim module so imports of `core.guardian_wallet.adapter`
keep working while the real implementation lives in
`guardian_adapter.py`.
"""

from .guardian_adapter import GuardianAdapter, GuardianDecision

__all__ = ["GuardianAdapter", "GuardianDecision"]
