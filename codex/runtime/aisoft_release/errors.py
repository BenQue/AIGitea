"""Safe, machine-classifiable release runtime errors."""

from __future__ import annotations


class ReleaseError(RuntimeError):
    """Base error whose message is safe to emit without subprocess output."""

    code = "RELEASE_ERROR"

    def __init__(self, message: str) -> None:
        self.safe_message = message
        super().__init__(message)


class ContractError(ReleaseError, ValueError):
    code = "INVALID_CONTRACT"


class HostRoleError(ReleaseError):
    code = "HOST_ROLE_DENIED"


class GateError(ReleaseError):
    code = "ACTION_GATE_DENIED"


class TransportError(ReleaseError):
    code = "TRANSPORT_FAILED"


class StateError(ReleaseError):
    code = "INVALID_STATE"


class DeploymentError(ReleaseError):
    code = "DEPLOYMENT_FAILED"
