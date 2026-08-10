"""Provider-neutral, auditable Gitea REST adapter."""

from __future__ import annotations

import json
import re
import time
from typing import Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from aisoft_change_name import ChangeName, ChangeNameError

from .contract import (
    COMPLEXITY_LABELS,
    LIFECYCLE_LABELS,
    TRIAGE_CATEGORY_LABELS,
    TRIAGE_LABELS,
    TRIAGE_STATE_LABELS,
    TYPE_LABELS,
)
from .verifier import redact


class GiteaError(RuntimeError):
    """A sanitized Gitea API failure."""


Transport = Callable[
    [str, str, dict[str, str], Optional[bytes]],
    tuple[int, dict[str, str], bytes],
]


class GiteaClient:
    def __init__(
        self,
        base_url: str,
        owner: str,
        repo: str,
        token: str,
        *,
        transport: Optional[Transport] = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise GiteaError("Gitea URL must use http or https")
        if not owner or not repo or not token:
            raise GiteaError("Gitea owner, repo, and token are required")
        if max_attempts < 1 or max_attempts > 5:
            raise GiteaError("max_attempts must be between 1 and 5")
        self._token = token
        self._transport = transport or _default_transport
        self._sleep = sleep
        self._max_attempts = max_attempts
        self._api = (
            base_url.rstrip("/")
            + "/api/v1/repos/"
            + quote(owner, safe="")
            + "/"
            + quote(repo, safe="")
        )

    def get_issue(self, issue_number: int) -> dict[str, object]:
        return self._object("GET", f"/issues/{_number(issue_number)}")

    def list_issues(self, label: str) -> list[dict[str, object]]:
        if not label or any(character in label for character in "\r\n"):
            raise GiteaError("Issue label filter must not be empty")
        values = self._array(
            "GET",
            "/issues?type=issues&state=open&labels=" + quote(label, safe=""),
        )
        issues: list[dict[str, object]] = []
        for value in values:
            if not isinstance(value, dict):
                raise GiteaError("Gitea Issue list response is invalid")
            issues.append(value)
        return issues

    def set_labels(self, issue_number: int, desired: set[str]) -> None:
        self._reconcile_labels(issue_number, platform_labels=desired)

    def set_triage_labels(self, issue_number: int, desired: set[str]) -> None:
        categories = desired & TRIAGE_CATEGORY_LABELS
        states = desired & TRIAGE_STATE_LABELS
        unknown = desired - TRIAGE_LABELS
        if unknown:
            raise GiteaError(f"unknown triage labels: {sorted(unknown)}")
        if len(categories) != 1 or len(states) != 1 or len(desired) != 2:
            raise GiteaError("triage labels require exactly one category and one state")
        self._reconcile_labels(issue_number, triage_labels=desired)

    def _reconcile_labels(
        self,
        issue_number: int,
        *,
        platform_labels: Optional[set[str]] = None,
        triage_labels: Optional[set[str]] = None,
    ) -> None:
        number = _number(issue_number)
        platform_managed = TYPE_LABELS | COMPLEXITY_LABELS | LIFECYCLE_LABELS
        if platform_labels is not None:
            unknown = platform_labels - platform_managed
            type_names = platform_labels & TYPE_LABELS
            complexity_names = platform_labels & COMPLEXITY_LABELS
            lifecycle_names = platform_labels & LIFECYCLE_LABELS
            if unknown:
                raise GiteaError(f"unknown managed labels: {sorted(unknown)}")
            if len(type_names) != 1:
                raise GiteaError("desired labels must contain exactly one type label")
            if len(complexity_names) > 1:
                raise GiteaError("desired labels may contain at most one complexity label")
            if len(lifecycle_names) != 1:
                raise GiteaError("desired labels must contain exactly one lifecycle label")
            if lifecycle_names != {"awaiting-triage"} and len(complexity_names) != 1:
                raise GiteaError("resolved lifecycle labels require one complexity label")

        issue = self.get_issue(number)
        current = issue.get("labels")
        if not isinstance(current, list):
            raise GiteaError("Issue labels response is invalid")
        repository_labels = self._array("GET", "/labels?limit=100")
        ids_by_name: dict[str, int] = {}
        for item in repository_labels:
            if isinstance(item, Mapping) and isinstance(item.get("name"), str):
                try:
                    ids_by_name[str(item["name"])] = int(item["id"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise GiteaError("repository label response is invalid") from exc
        desired = (platform_labels or set()) | (triage_labels or set())
        missing = desired - set(ids_by_name)
        if missing:
            raise GiteaError(f"required Gitea labels are missing: {sorted(missing)}")

        final_ids = {ids_by_name[name] for name in desired}
        for item in current:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name")
            replace_platform = platform_labels is not None and name in platform_managed
            replace_triage = triage_labels is not None and name in TRIAGE_LABELS
            if isinstance(name, str) and not replace_platform and not replace_triage:
                try:
                    final_ids.add(int(item["id"]))
                except (KeyError, TypeError, ValueError) as exc:
                    raise GiteaError("current Issue label response is invalid") from exc
        self._request("PUT", f"/issues/{number}/labels", {"labels": sorted(final_ids)})

    def comment(self, issue_number: int, body: str) -> dict[str, object]:
        if not body.strip():
            raise GiteaError("comment body must not be empty")
        return self._object(
            "POST", f"/issues/{_number(issue_number)}/comments", {"body": body}
        )

    def create_pr(
        self,
        issue_number: int,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> dict[str, object]:
        number = _number(issue_number)
        closes = re.findall(r"(?m)^Closes #([1-9][0-9]*)[ \t]*$", body)
        if closes != [str(number)]:
            raise GiteaError(f"PR body must contain exactly one line: Closes #{number}")
        try:
            change_name = ChangeName.parse_branch(head, allow_legacy=False)
        except ChangeNameError as exc:
            raise GiteaError("new PR head must use change/N-short-description") from exc
        if change_name.issue_number != number:
            raise GiteaError("PR head Issue number does not match")
        assert change_name.slug is not None
        summary_link = re.compile(
            rf"(?<![A-Za-z0-9_./-])docs/changes/"
            rf"{number}-{re.escape(change_name.slug)}/"
            rf"summary-{re.escape(change_name.slug)}-\d{{6}}\.md"
            rf"(?![A-Za-z0-9_./-])"
        )
        if len(summary_link.findall(body)) != 1:
            raise GiteaError("PR body must link the Issue summary document")
        if not title.strip() or not base.strip():
            raise GiteaError("PR title, readable change head, and base are required")
        return self._object(
            "POST",
            "/pulls",
            {"title": title, "head": head, "base": base, "body": body},
        )

    def get_pr(self, pr_number: int) -> dict[str, object]:
        return self._object("GET", f"/pulls/{_number(pr_number)}")

    def get_commit_status(self, sha: str) -> str:
        if not sha or any(character not in "0123456789abcdefABCDEF" for character in sha):
            raise GiteaError("commit SHA must be hexadecimal")
        payload = self._object("GET", f"/commits/{quote(sha, safe='')}/status")
        state = payload.get("state")
        if state in {"pending", "success", "failure"}:
            return str(state)
        if state == "error":
            return "failure"
        raise GiteaError(f"unsupported Gitea commit status: {state!r}")

    def _object(
        self, method: str, path: str, payload: Optional[object] = None
    ) -> dict[str, object]:
        value = self._request(method, path, payload)
        if not isinstance(value, dict):
            raise GiteaError("Gitea response must be a JSON object")
        return value

    def _array(
        self, method: str, path: str, payload: Optional[object] = None
    ) -> list[object]:
        value = self._request(method, path, payload)
        if not isinstance(value, list):
            raise GiteaError("Gitea response must be a JSON array")
        return value

    def _request(
        self, method: str, path: str, payload: Optional[object] = None
    ) -> object:
        url = self._api + path
        body = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"token {self._token}",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
            headers["Content-Type"] = "application/json"

        for attempt in range(1, self._max_attempts + 1):
            try:
                status, response_headers, raw = self._transport(method, url, headers, body)
            except (OSError, URLError) as exc:
                if attempt < self._max_attempts:
                    self._sleep(0.25 * (2 ** (attempt - 1)))
                    continue
                raise GiteaError("Gitea network request failed after bounded retries") from exc
            if 200 <= status < 300:
                if not raw:
                    return {}
                try:
                    return json.loads(raw.decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise GiteaError("Gitea returned invalid JSON") from exc
            if (status == 429 or 500 <= status < 600) and attempt < self._max_attempts:
                delay = 0.25 * (2 ** (attempt - 1))
                retry_after = response_headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = min(max(float(retry_after), 0.0), 5.0)
                    except ValueError:
                        pass
                self._sleep(delay)
                continue
            detail = redact(raw.decode("utf-8", errors="replace"))[:1000]
            raise GiteaError(f"Gitea HTTP {status}: {detail}")
        raise GiteaError("Gitea request exhausted retries")


def _default_transport(
    method: str, url: str, headers: dict[str, str], body: Optional[bytes]
) -> tuple[int, dict[str, str], bytes]:
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


def _number(value: int) -> int:
    if not isinstance(value, int) or value <= 0:
        raise GiteaError("Issue or PR number must be a positive integer")
    return value
