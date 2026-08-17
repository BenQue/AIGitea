"""Deterministic, no-secret company delivery operator contracts."""

from .contract import (
    EVIDENCE_VERSION,
    HANDOFF_VERSION,
    INVENTORY_VERSION,
    INVENTORY_V1_VERSION,
    INVENTORY_V2_VERSION,
    TRANSITION_VERSION,
    CompanyDeliveryError,
    verify_gitea_transition,
    verify_legacy_health,
)

__all__ = [
    "EVIDENCE_VERSION",
    "HANDOFF_VERSION",
    "INVENTORY_VERSION",
    "INVENTORY_V1_VERSION",
    "INVENTORY_V2_VERSION",
    "TRANSITION_VERSION",
    "CompanyDeliveryError",
    "verify_gitea_transition",
    "verify_legacy_health",
]
