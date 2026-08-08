from __future__ import annotations

import hashlib
import json
import os
import pwd
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .broker import BrokerError, TOKEN_RE
from .contract import AccessContract, ProjectContract


IdentityReader = Callable[[str], str]
Replace = Callable[[str | os.PathLike[str], str | os.PathLike[str]], None]


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ProfileMigrator:
    """Transactional migration for one manifest-declared VM project profile."""

    def __init__(
        self,
        contract: AccessContract,
        *,
        home: str | Path,
        source_credential_root: str | Path | None = None,
        target_uid: int | None = None,
        target_gid: int | None = None,
        source_uid: int | None = None,
        identity_reader: IdentityReader | None = None,
        replace: Replace = os.replace,
    ) -> None:
        self.contract = contract
        self.home = Path(home)
        policy = contract.raw["vm_profile_policy"]
        self.source_root = Path(source_credential_root or policy["source_credential_root"])
        if target_uid is None or target_gid is None:
            try:
                account = pwd.getpwnam(policy["runtime_user"])
            except KeyError as exc:
                raise BrokerError("RUNTIME_USER_MISSING", "VM runtime user is unavailable") from exc
            target_uid = account.pw_uid
            target_gid = account.pw_gid
        self.target_uid = target_uid
        self.target_gid = target_gid
        if source_uid is None:
            try:
                source_uid = pwd.getpwnam(policy["source_credential_owner"]).pw_uid
            except KeyError as exc:
                raise BrokerError("SOURCE_OWNER_MISSING", "credential source owner is unavailable") from exc
        self.source_uid = source_uid
        self.allowed_modes = {0o400, 0o600}
        self.identity_reader = identity_reader or self._live_identity
        self.replace = replace

    def plan(self, project_id: str) -> dict[str, object]:
        project = self._project(project_id)
        token = self._read_source_token(project)
        self._verify_token_identity(project, token)
        profile_bytes = self._profile_bytes(project)
        token_bytes = token.encode("utf-8") + b"\n"
        target_profile, target_token = self._targets(project)
        current = self._target_matches(target_profile, profile_bytes) and self._target_matches(
            target_token, token_bytes
        )
        if current:
            self._verify_token_identity(project, self._read_secure(target_token).decode().strip())
        return {
            "status": "PASS",
            "project": project.project_id,
            "profile": project.vm_profile.name if project.vm_profile else None,
            "action": "no-op" if current else "apply",
            "identity": project.project_agent,
            "target": f"{self.contract.governance.owner}/{project.repository}",
        }

    def apply(self, project_id: str) -> dict[str, object]:
        project = self._project(project_id)
        planned = self.plan(project_id)
        if planned["action"] == "no-op":
            return {**planned, "result": "no-op"}
        token = self._read_source_token(project)
        profile_bytes = self._profile_bytes(project)
        token_bytes = token.encode("utf-8") + b"\n"
        target_profile, target_token = self._targets(project)
        self._prepare_parent(target_profile.parent)
        self._prepare_parent(target_token.parent)
        self._validate_existing_target(target_profile)
        self._validate_existing_target(target_token)
        backup = self._create_backup(project, target_profile, target_token)
        staged: list[Path] = []
        try:
            staged_token = self._stage(target_token, token_bytes)
            staged.append(staged_token)
            staged_profile = self._stage(target_profile, profile_bytes)
            staged.append(staged_profile)
            self.replace(staged_token, target_token)
            staged.remove(staged_token)
            self.replace(staged_profile, target_profile)
            staged.remove(staged_profile)
            self._read_back(project, profile_bytes, token_bytes)
        except Exception as exc:
            for item in staged:
                item.unlink(missing_ok=True)
            try:
                self._restore_backup(backup, target_profile, target_token)
            except Exception as rollback_exc:
                raise BrokerError(
                    "PROFILE_TRANSACTION_BROKEN",
                    "profile apply failed and automatic restore failed",
                ) from rollback_exc
            if isinstance(exc, BrokerError):
                raise
            raise BrokerError("PROFILE_APPLY_FAILED", "profile apply failed and was restored") from exc
        return {
            "status": "PASS",
            "project": project.project_id,
            "profile": project.vm_profile.name if project.vm_profile else None,
            "result": "applied",
            "identity": project.project_agent,
            "target": f"{self.contract.governance.owner}/{project.repository}",
            "backup": "latest",
        }

    def read_back(self, project_id: str) -> dict[str, object]:
        project = self._project(project_id)
        token = self._read_source_token(project)
        self._read_back(project, self._profile_bytes(project), token.encode("utf-8") + b"\n")
        return {
            "status": "PASS",
            "project": project.project_id,
            "profile": project.vm_profile.name if project.vm_profile else None,
            "result": "read-back",
            "identity": project.project_agent,
            "target": f"{self.contract.governance.owner}/{project.repository}",
        }

    def consume_check(self, project_id: str) -> dict[str, object]:
        project = self._project(project_id)
        target_profile, target_token = self._targets(project)
        token_bytes = self._read_secure(target_token)
        token = self._parse_token_bytes(token_bytes, "project credential is invalid")
        self._read_back(project, self._profile_bytes(project), token_bytes)
        return {
            "status": "PASS",
            "project": project.project_id,
            "profile": project.vm_profile.name if project.vm_profile else None,
            "result": "consumer-ready",
            "identity": project.project_agent,
            "target": f"{self.contract.governance.owner}/{project.repository}",
        }

    def rollback(self, project_id: str) -> dict[str, object]:
        project = self._project(project_id)
        target_profile, target_token = self._targets(project)
        backup = self._backup_dir(project) / "latest"
        if not (backup / "metadata.json").is_file():
            raise BrokerError("BACKUP_MISSING", "fixed latest profile backup is unavailable")
        self._restore_backup(backup, target_profile, target_token)
        self._verify_restored_metadata(backup, target_profile, target_token)
        return {
            "status": "PASS",
            "project": project.project_id,
            "profile": project.vm_profile.name if project.vm_profile else None,
            "result": "rolled-back",
            "backup": "latest",
        }

    def _project(self, project_id: str) -> ProjectContract:
        try:
            project = self.contract.project(project_id)
        except Exception as exc:
            raise BrokerError("TARGET_DENIED", "project is not in the migration manifest") from exc
        if project.vm_profile is None:
            raise BrokerError("TARGET_DENIED", "project has no approved VM profile migration")
        return project

    def _source_path(self, project: ProjectContract) -> Path:
        return self.source_root / f"{project.project_agent}-project-agent.token"

    def _read_source_token(self, project: ProjectContract) -> str:
        source = self._source_path(project)
        try:
            owner = source.lstat().st_uid
        except OSError as exc:
            raise BrokerError("CREDENTIAL_UNAVAILABLE", "source project credential is unavailable") from exc
        if owner != self.source_uid:
            raise BrokerError("CREDENTIAL_OWNER_INVALID", "source credential owner mismatch")
        return self._parse_token_bytes(
            self._read_secure(source), "source project credential is invalid"
        )

    @staticmethod
    def _parse_token_bytes(data: bytes, message: str) -> str:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BrokerError("CREDENTIAL_INVALID", message) from exc
        token = text[:-1] if text.endswith("\n") else text
        if text not in {token, f"{token}\n"} or not token or not TOKEN_RE.fullmatch(token):
            raise BrokerError("CREDENTIAL_INVALID", message)
        return token

    def _read_secure(self, path: Path) -> bytes:
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise BrokerError("CREDENTIAL_UNAVAILABLE", "required protected file is unavailable") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise BrokerError("CREDENTIAL_MODE_INVALID", "protected file must be a regular non-symlink")
        if stat.S_IMODE(metadata.st_mode) not in self.allowed_modes:
            raise BrokerError("CREDENTIAL_MODE_INVALID", "protected file mode must be 400 or 600")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise BrokerError("CREDENTIAL_UNAVAILABLE", "required protected file cannot be read") from exc

    def _verify_token_identity(self, project: ProjectContract, token: str) -> None:
        try:
            identity = self.identity_reader(token)
        except BrokerError:
            raise
        except Exception as exc:
            raise BrokerError("IDENTITY_READ_FAILED", "credential identity read-back failed") from exc
        if identity != project.project_agent:
            raise BrokerError("IDENTITY_MISMATCH", "credential identity does not match the project-agent")

    def _live_identity(self, token: str) -> str:
        request = Request(
            f"{self.contract.governance.base_url}/api/v1/user",
            headers={"Accept": "application/json", "Authorization": f"token {token}"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
                body = response.read()
        except HTTPError as exc:
            status = exc.code
            body = b""
        except (URLError, TimeoutError, OSError) as exc:
            raise BrokerError("IDENTITY_READ_FAILED", "credential identity read-back failed") from exc
        if status in {401, 403, 404}:
            raise BrokerError(f"HTTP_{status}", f"Gitea returned HTTP {status}")
        if status < 200 or status >= 300:
            raise BrokerError("HTTP_ERROR", f"Gitea returned HTTP {status}")
        try:
            value = json.loads(body)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "identity response is invalid JSON") from exc
        if not isinstance(value, dict) or not isinstance(value.get("login"), str):
            raise BrokerError("RESPONSE_SCHEMA_INVALID", "identity response schema is invalid")
        if value.get("is_admin") is True:
            raise BrokerError("IDENTITY_MISMATCH", "project-agent unexpectedly has site-admin permission")
        return value["login"]

    def _targets(self, project: ProjectContract) -> tuple[Path, Path]:
        assert project.vm_profile is not None
        policy = self.contract.raw["vm_profile_policy"]
        profile = self.home / policy["profile_root"] / f"{project.vm_profile.name}.env"
        token = self.home / policy["token_root"] / f"{project.vm_profile.name}.token"
        return profile, token

    def _profile_bytes(self, project: ProjectContract) -> bytes:
        assert project.vm_profile is not None
        _profile, token = self._targets(project)
        repo_dir = self.home / project.vm_profile.repo_dir
        lines = [
            f"AISOFT_PROJECT_ID={project.project_id}",
            f"GITEA_URL={self.contract.governance.base_url}",
            f"GITEA_OWNER={self.contract.governance.owner}",
            f"GITEA_REPO={project.repository}",
            f"GITEA_IDENTITY={project.project_agent}",
            f"GITEA_TOKEN_FILE={token}",
            f"AGENT_REPO_DIR={repo_dir}",
            f"ANALYSIS_PROVIDER={project.vm_profile.analysis_provider}",
            f"IMPLEMENT_PROVIDER={project.vm_profile.implement_provider}",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _target_matches(self, path: Path, expected: bytes) -> bool:
        if not path.exists() and not path.is_symlink():
            return False
        try:
            metadata = path.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise BrokerError("TARGET_MODE_INVALID", "profile target must be a regular non-symlink")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            return False
        if metadata.st_uid != self.target_uid or metadata.st_gid != self.target_gid:
            return False
        return path.read_bytes() == expected

    def _validate_existing_target(self, path: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise BrokerError("TARGET_MODE_INVALID", "profile target must be a regular non-symlink")
        if stat.S_IMODE(metadata.st_mode) not in self.allowed_modes:
            raise BrokerError("TARGET_MODE_INVALID", "existing profile target mode must be 400 or 600")
        if metadata.st_uid != self.target_uid or metadata.st_gid != self.target_gid:
            raise BrokerError("TARGET_OWNER_INVALID", "existing profile target owner mismatch")

    def _prepare_parent(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise BrokerError("TARGET_MODE_INVALID", "managed parent must be a regular directory")
        if metadata.st_uid not in {os.geteuid(), self.target_uid}:
            raise BrokerError("TARGET_OWNER_INVALID", "managed parent owner mismatch")
        os.chmod(path, 0o700)
        os.chown(path, self.target_uid, self.target_gid)

    def _backup_dir(self, project: ProjectContract) -> Path:
        policy = self.contract.raw["vm_profile_policy"]
        return self.home / policy["backup_root"] / project.project_id

    def _create_backup(self, project: ProjectContract, profile: Path, token: Path) -> Path:
        root = self._backup_dir(project)
        self._prepare_parent(root)
        latest = root / "latest"
        previous = root / "previous"
        for managed in (latest, previous):
            if managed.is_symlink():
                raise BrokerError("BACKUP_MODE_INVALID", "backup path must not be a symlink")
        staging = Path(tempfile.mkdtemp(prefix=".latest-", dir=root))
        os.chmod(staging, 0o700)
        os.chown(staging, self.target_uid, self.target_gid)
        entries: dict[str, dict[str, object]] = {}
        for label, source in (("profile", profile), ("token", token)):
            if source.exists():
                metadata = source.lstat()
                data = source.read_bytes()
                backup_file = staging / f"{label}.pre"
                backup_file.write_bytes(data)
                os.chmod(backup_file, 0o600)
                os.chown(backup_file, self.target_uid, self.target_gid)
                entries[label] = {
                    "existed": True,
                    "mode": stat.S_IMODE(metadata.st_mode),
                    "uid": metadata.st_uid,
                    "gid": metadata.st_gid,
                    "sha256": _sha256(data),
                }
            else:
                entries[label] = {"existed": False}
        metadata_path = staging / "metadata.json"
        metadata_path.write_text(json.dumps({"version": 1, "files": entries}, sort_keys=True) + "\n")
        os.chmod(metadata_path, 0o600)
        os.chown(metadata_path, self.target_uid, self.target_gid)
        if previous.exists():
            shutil.rmtree(previous)
        if latest.exists():
            self.replace(latest, previous)
        self.replace(staging, latest)
        return latest

    def _stage(self, target: Path, data: bytes) -> Path:
        descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        staged = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(staged, 0o600)
            os.chown(staged, self.target_uid, self.target_gid)
            return staged
        except Exception:
            staged.unlink(missing_ok=True)
            raise

    def _read_back(self, project: ProjectContract, profile_bytes: bytes, token_bytes: bytes) -> None:
        target_profile, target_token = self._targets(project)
        for path, expected in ((target_profile, profile_bytes), (target_token, token_bytes)):
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise BrokerError("READ_BACK_MISMATCH", "profile read-back type mismatch")
            if stat.S_IMODE(metadata.st_mode) != 0o600:
                raise BrokerError("READ_BACK_MISMATCH", "profile read-back mode mismatch")
            if metadata.st_uid != self.target_uid or metadata.st_gid != self.target_gid:
                raise BrokerError("READ_BACK_MISMATCH", "profile read-back owner mismatch")
            if path.read_bytes() != expected:
                raise BrokerError("READ_BACK_MISMATCH", "profile read-back bytes mismatch")
        token = self._parse_token_bytes(
            target_token.read_bytes(), "project credential is invalid"
        )
        self._verify_token_identity(project, token)
        parsed: dict[str, str] = {}
        for line in target_profile.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if not separator or key in parsed:
                raise BrokerError("READ_BACK_MISMATCH", "profile read-back schema mismatch")
            parsed[key] = value
        expected = {
            "AISOFT_PROJECT_ID": project.project_id,
            "GITEA_URL": self.contract.governance.base_url,
            "GITEA_OWNER": self.contract.governance.owner,
            "GITEA_REPO": project.repository,
            "GITEA_IDENTITY": project.project_agent,
            "GITEA_TOKEN_FILE": str(target_token),
            "AGENT_REPO_DIR": str(self.home / project.vm_profile.repo_dir),
            "ANALYSIS_PROVIDER": project.vm_profile.analysis_provider,
            "IMPLEMENT_PROVIDER": project.vm_profile.implement_provider,
        }
        if parsed != expected:
            raise BrokerError("READ_BACK_MISMATCH", "profile target mapping mismatch")

    def _restore_backup(self, backup: Path, profile: Path, token: Path) -> None:
        metadata = json.loads((backup / "metadata.json").read_text(encoding="utf-8"))
        for label, target in (("profile", profile), ("token", token)):
            entry = metadata["files"][label]
            if entry["existed"]:
                data = (backup / f"{label}.pre").read_bytes()
                staged = self._stage(target, data)
                os.chmod(staged, int(entry["mode"]))
                os.chown(staged, int(entry["uid"]), int(entry["gid"]))
                self.replace(staged, target)
            else:
                if target.exists() or target.is_symlink():
                    target.unlink()

    def _verify_restored_metadata(self, backup: Path, profile: Path, token: Path) -> None:
        metadata = json.loads((backup / "metadata.json").read_text(encoding="utf-8"))
        for label, target in (("profile", profile), ("token", token)):
            entry = metadata["files"][label]
            if not entry["existed"]:
                if target.exists() or target.is_symlink():
                    raise BrokerError("ROLLBACK_MISMATCH", "rollback should restore target absence")
                continue
            current = target.lstat()
            data = target.read_bytes()
            if (
                stat.S_IMODE(current.st_mode) != int(entry["mode"])
                or current.st_uid != int(entry["uid"])
                or current.st_gid != int(entry["gid"])
                or _sha256(data) != entry["sha256"]
            ):
                raise BrokerError("ROLLBACK_MISMATCH", "rollback metadata or bytes mismatch")
