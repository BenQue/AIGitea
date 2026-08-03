"""Safe, machine-readable diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str = "$"
    remediation: str = ""

    def as_dict(self) -> dict[str, str]:
        return {key: value for key, value in asdict(self).items() if value}


class ArchitectureError(Exception):
    """An expected validation failure that is safe to render."""

    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


def fail(code: str, message: str, path: str = "$", remediation: str = "") -> None:
    raise ArchitectureError(Diagnostic(code, message, path, remediation))
