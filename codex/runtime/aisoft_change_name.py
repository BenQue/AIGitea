"""Canonical Issue-scoped change names shared by controller and host broker."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


SLUG_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+){1,3}"
SLUG_RE = re.compile(rf"^{SLUG_PATTERN}$")
BRANCH_RE = re.compile(rf"^change/([1-9][0-9]*)(?:-({SLUG_PATTERN}))?$")
DIRECTORY_RE = re.compile(rf"^([1-9][0-9]*)(?:-({SLUG_PATTERN}))?$")
WORKTREE_RE = re.compile(rf"^issue-([1-9][0-9]*)(?:-({SLUG_PATTERN}))?$")

RESERVED_SLUGS = frozenset(
    {
        "main",
        "master",
        "head",
        "merge",
        "pull",
        "pr",
        "refs",
        "change",
        "changes",
        "docs",
        "worktree",
        "tmp",
        "temp",
        "legacy",
    }
)
RESERVED_PREFIXES = ("tmp-", "temp-", "legacy-")


class ChangeNameError(ValueError):
    """A change name is invalid or cannot be selected unambiguously."""


def validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or len(slug) > 32 or not SLUG_RE.fullmatch(slug):
        raise ChangeNameError(
            "slug must use 2-4 lowercase ASCII kebab-case segments and at most 32 characters"
        )
    if not re.search(r"[a-z]", slug):
        raise ChangeNameError("slug must contain at least one ASCII letter")
    if slug in RESERVED_SLUGS or slug.startswith(RESERVED_PREFIXES):
        raise ChangeNameError(f"slug is reserved: {slug}")
    return slug


@dataclass(frozen=True, order=True)
class ChangeName:
    issue_number: int
    slug: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.issue_number, int) or self.issue_number <= 0:
            raise ChangeNameError("Issue number must be a positive integer")
        if self.slug is not None:
            validate_slug(self.slug)

    @classmethod
    def new(cls, issue_number: int, slug: str) -> "ChangeName":
        """Create a new-format name; callers cannot use this API for legacy names."""
        return cls(issue_number, validate_slug(slug))

    @classmethod
    def parse_branch(cls, value: str, *, allow_legacy: bool = True) -> "ChangeName":
        return cls._parse(value, BRANCH_RE, "branch", allow_legacy)

    @classmethod
    def parse_directory(
        cls,
        value: str,
        *,
        issue_number: int | None = None,
        allow_legacy: bool = True,
    ) -> "ChangeName":
        parsed = cls._parse(value, DIRECTORY_RE, "directory", allow_legacy)
        if issue_number is not None and parsed.issue_number != issue_number:
            raise ChangeNameError("change directory Issue number does not match")
        return parsed

    @classmethod
    def parse_worktree(cls, value: str, *, allow_legacy: bool = True) -> "ChangeName":
        return cls._parse(value, WORKTREE_RE, "worktree", allow_legacy)

    @classmethod
    def _parse(
        cls, value: str, pattern: re.Pattern[str], kind: str, allow_legacy: bool
    ) -> "ChangeName":
        if not isinstance(value, str):
            raise ChangeNameError(f"{kind} must be a string")
        match = pattern.fullmatch(value)
        if not match:
            raise ChangeNameError(f"invalid change {kind}: {value}")
        parsed = cls(int(match.group(1)), match.group(2))
        if parsed.is_legacy and not allow_legacy:
            raise ChangeNameError(f"legacy change {kind} is not allowed for a new write")
        return parsed

    @property
    def is_legacy(self) -> bool:
        return self.slug is None

    @property
    def suffix(self) -> str:
        return str(self.issue_number) + (f"-{self.slug}" if self.slug else "")

    @property
    def branch(self) -> str:
        return f"change/{self.suffix}"

    @property
    def directory_name(self) -> str:
        return self.suffix

    @property
    def worktree_name(self) -> str:
        return f"issue-{self.suffix}"


def select_change_name(
    issue_number: int,
    candidates: Iterable[ChangeName],
    *,
    required: bool = True,
) -> ChangeName | None:
    """Select exactly one tuple and reject legacy/readable or multi-slug drift."""
    unique = {candidate for candidate in candidates if candidate.issue_number == issue_number}
    if not unique:
        if required:
            raise ChangeNameError(f"no change name found for Issue #{issue_number}")
        return None
    if len(unique) != 1:
        rendered = ", ".join(sorted(candidate.branch for candidate in unique))
        raise ChangeNameError(f"CHANGE_NAME_CONFLICT for Issue #{issue_number}: {rendered}")
    return next(iter(unique))
