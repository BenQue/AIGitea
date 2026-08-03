"""AISoftPlatform architecture catalog validation and lock generation."""

from .errors import ArchitectureError, Diagnostic
from .lockfile import build_lock, validate_lock
from .validator import validate_catalog, validate_project

__all__ = [
    "ArchitectureError",
    "Diagnostic",
    "build_lock",
    "validate_catalog",
    "validate_lock",
    "validate_project",
]
