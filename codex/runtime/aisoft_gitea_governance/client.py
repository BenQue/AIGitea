from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiError(RuntimeError):
    operation: str
    status: int

    def __str__(self) -> str:
        return f"{self.operation} failed with HTTP {self.status}"


class GiteaClient:
    def __init__(self, base_url: str, token: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
        operation: str = "Gitea API request",
    ) -> Any:
        body = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"token {self._token}",
        }
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}/api/v1{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = response.status
                data = response.read()
        except urllib.error.HTTPError as exc:
            # Do not include response bodies or headers in errors: they may
            # contain instance-specific details and never help token safety.
            raise ApiError(operation, exc.code) from None
        except urllib.error.URLError:
            raise ApiError(operation, 0) from None
        if status not in expected:
            raise ApiError(operation, status)
        if not data:
            return None
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(f"{operation} returned invalid JSON", status) from None

    def get(self, path: str, operation: str) -> Any:
        return self.request("GET", path, operation=operation)

    def put(self, path: str, payload: dict[str, Any], operation: str) -> Any:
        return self.request("PUT", path, payload=payload, expected=(200, 201, 204),
                            operation=operation)

    def post(self, path: str, payload: dict[str, Any], operation: str) -> Any:
        return self.request("POST", path, payload=payload, expected=(200, 201),
                            operation=operation)

    def patch(self, path: str, payload: dict[str, Any], operation: str) -> Any:
        return self.request("PATCH", path, payload=payload, expected=(200, 201, 204),
                            operation=operation)

    def delete(self, path: str, operation: str) -> Any:
        return self.request("DELETE", path, expected=(200, 204), operation=operation)
