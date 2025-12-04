"""
Guardian Wallet – Configuration Models

This module defines the in-memory representation of Guardian configuration:
spending limits, rule requirements, and evaluation helpers.

Typical usage:

    from guardian_wallet.guardian_config import GuardianConfig

    cfg = GuardianConfig.load_from_file("config/guardian-rules.yml")
    rules = cfg.rules_for_operation(asset="DGB", operation="send")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

import datetime as _dt

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


# -----------------------------
# Data classes
# -----------------------------


@dataclass
class SpendingLimit:
    """Simple time-bounded spending limit."""

    max_amount: float
    window_seconds: int
    """Rolling time window in seconds (e.g. 86400 for 24h)."""

    def window(self) -> _dt.timedelta:
        return _dt.timedelta(seconds=self.window_seconds)


@dataclass
class Requirement:
    """
    Additional requirements the wallet must satisfy before allowing an action.

    Examples:
      - "device_pin"
      - "biometric"
      - "guardian_approval"
      - "out_of_band_confirmation"
    """

    code: str
    description: str = ""


@dataclass
class GuardianRule:
    """
    A single Guardian rule describing when extra protection is required.

    The rule is intentionally generic so it can be bound to many use-cases:
    - outgoing DGB transactions
    - DD mint / redeem operations
    - DigiAssets transfers
    """

    id: str
    description: str
    enabled: bool = True

    # Target selection
    assets: List[str] = field(default_factory=list)  # e.g. ["DGB", "DD"]
    operations: List[str] = field(default_factory=list)  # e.g. ["send", "mint", "redeem"]

    # Limits (optional)
    spending_limit: Optional[SpendingLimit] = None

    # Extra requirements (optional)
    requirements: List[Requirement] = field(default_factory=list)

    # Meta
    severity: str = "medium"  # "low" | "medium" | "high" | "critical"
    tags: List[str] = field(default_factory=list)

    def matches(self, *, asset: str, operation: str) -> bool:
        """Return True if this rule applies to the given asset/operation."""
        if not self.enabled:
            return False

        if self.assets and asset not in self.assets and "*" not in self.assets:
            return False

        if self.operations and operation not in self.operations and "*" not in self.operations:
            return False

        return True


@dataclass
class GuardianConfig:
    """Top-level Guardian configuration object."""

    version: str = "1"
    rules: List[GuardianRule] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    # --------- Query helpers ---------

    def rules_for_operation(self, *, asset: str, operation: str) -> List[GuardianRule]:
        """
        Return all rules that apply to the given asset + operation.

        Example:
            cfg.rules_for_operation(asset="DGB", operation="send")
        """
        asset = asset.upper()
        operation = operation.lower()
        return [r for r in self.rules if r.matches(asset=asset, operation=operation)]

    def strongest_severity(self, *, asset: str, operation: str) -> Optional[str]:
        """Return the strongest severity among matching rules (or None)."""
        order = ["low", "medium", "high", "critical"]
        matched = self.rules_for_operation(asset=asset, operation=operation)
        if not matched:
            return None

        max_idx = max(order.index(r.severity) if r.severity in order else 0 for r in matched)
        return order[max_idx]

    # --------- Construction / loading ---------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardianConfig":
        version = str(data.get("version", "1"))
        rules_data = data.get("rules", []) or []

        rules: List[GuardianRule] = []
        for item in rules_data:
            # Spending limit
            sl: Optional[SpendingLimit] = None
            sl_raw = item.get("spending_limit")
            if isinstance(sl_raw, dict):
                sl = SpendingLimit(
                    max_amount=float(sl_raw.get("max_amount", 0.0)),
                    window_seconds=int(sl_raw.get("window_seconds", 0)),
                )

            # Requirements
            reqs: List[Requirement] = []
            for r in item.get("requirements", []) or []:
                if isinstance(r, str):
                    reqs.append(Requirement(code=r, description=""))
                elif isinstance(r, dict):
                    reqs.append(
                        Requirement(
                            code=str(r.get("code", "")),
                            description=str(r.get("description", "")),
                        )
                    )

            rule = GuardianRule(
                id=str(item.get("id", "")),
                description=str(item.get("description", "")),
                enabled=bool(item.get("enabled", True)),
                assets=[str(a).upper() for a in (item.get("assets") or [])],
                operations=[str(op).lower() for op in (item.get("operations") or [])],
                spending_limit=sl,
                requirements=reqs,
                severity=str(item.get("severity", "medium")).lower(),
                tags=[str(t) for t in (item.get("tags") or [])],
            )
            rules.append(rule)

        return cls(version=version, rules=rules, raw=data)

    @classmethod
    def load_from_file(cls, path: str | Path) -> "GuardianConfig":
        """
        Load Guardian configuration from a YAML file.

        The expected schema is:

            version: "1"
            rules:
              - id: "daily-dgb-send-limit"
                description: "Limit DGB spending per 24h"
                enabled: true
                assets: ["DGB"]
                operations: ["send"]
                spending_limit:
                  max_amount: 10000
                  window_seconds: 86400
                requirements:
                  - code: "device_pin"
                    description: "Require local PIN entry"
                  - code: "guardian_approval"
                    description: "Ask guardian to approve large spends"
                severity: "high"
                tags: ["limit", "daily"]

        """
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required to load GuardianConfig from YAML. "
                "Install it with `pip install pyyaml`."
            )

        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            raise ValueError(f"Guardian config at {path} must be a mapping at top level")

        return cls.from_dict(data)
