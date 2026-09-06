"""Strict, bounded JSON contracts. No host discovery or credential access."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat


VERSION = "1.0.0"
COMPONENTS = ["handoff-verifier", "adoption-planner", "action-contracts"]
ACTIONS = ["gitea-adoption", "repo-bootstrap", "protected-main", "required-ci",
           "runner", "one-shot-inbound", "canary"]
SHA256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
SHA1 = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
REFERENCE = {"type": "string", "pattern": "^approval/[a-z0-9][a-z0-9-]{1,63}$"}
DESCRIPTION = {"type": "string", "pattern": "^[^\\r\\n]{1,1500}$"}
BOOL = {"type": "boolean"}
MAX_BYTES = 4 * 1024 * 1024


class BootstrapError(ValueError):
    """Only stable codes are safe to expose; never echo rejected input."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def require(condition: bool, code: str) -> None:
    if not condition:
        raise BootstrapError(code)


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def enum(*values: object) -> dict:
    return {"enum": list(values)}


def array(items: dict, minimum: int = 0, maximum: int = 100) -> dict:
    return {"type": "array", "items": items, "minItems": minimum,
            "maxItems": maximum, "uniqueItems": True}


def obj(**properties: dict) -> dict:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def nullable(value: dict) -> dict:
    return {"anyOf": [value, {"type": "null"}]}


ROLLBACK = obj(kind=enum("uninstalled", "snapshot"), identity_sha256=SHA256,
               source_sha=nullable(SHA1))
PROTECTION = obj(direct_push_denied=BOOL, force_push_denied=BOOL,
                 human_merge_only=BOOL, required_ci=array({"type": "string",
                 "pattern": "^[A-Za-z0-9][A-Za-z0-9 /_().-]{0,127}$"}, 0, 20))
CONTEXTS = array({"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9 /_().-]{0,127}$"}, 1, 20)
STAGING = {"type": "string", "pattern": "^refs/heads/sync/platform-[0-9a-f]{40}$"}
PARAMETERS = {
    "gitea-adoption": obj(package_set_sha256=SHA256, candidate_namespace_sha256=SHA256,
                           gitea_version=enum("1.26.4")),
    "repo-bootstrap": obj(source_refs_sha256=SHA256, transport=enum("approved-git-bundle",
        "allowlisted-github-ref"), transport_identity_sha256=SHA256, staging_ref=STAGING),
    "protected-main": obj(branch=enum("main"), direct_push_allowlist=enum([]),
        force_push_allowlist=enum([]), human_merge_identity_sha256=SHA256, policy_sha256=SHA256),
    "required-ci": obj(contexts=CONTEXTS, branch=enum("main")),
    "runner": obj(binary_sha256=SHA256, configuration_sha256=SHA256,
        registration_approval_reference=REFERENCE, scope=enum("platform-only"), auto_enable=enum(False)),
    "one-shot-inbound": obj(source_refs_sha256=SHA256, transport_identity_sha256=SHA256,
        staging_ref=STAGING, timer_enabled=enum(False)),
    "canary": obj(local_change_sha256=SHA256, company_approval_sha256=SHA256,
        required_contexts=CONTEXTS, merge_policy=enum("manual")),
}
BINDINGS = obj(**PARAMETERS)
EXECUTOR = obj(status=enum("unbound"), binding_requirement=enum("independent-B1-B2-contract"))
SCHEMAS = {
    "actions": obj(contract_version=enum("platform-bootstrap-actions/v1"),
        script_version=enum(VERSION), host_role=enum("scm-ci"), site_executor=enum("BOUND_BY_B1_B2"),
        actions=array(obj(action=enum(*ACTIONS), operation={"type": "string",
            "pattern": "^[a-z][a-z-]{1,63}$"}, exact_inputs=DESCRIPTION, no_op=DESCRIPTION,
            negative_permission=DESCRIPTION, failure_and_readback=DESCRIPTION,
            rollback=DESCRIPTION), len(ACTIONS), len(ACTIONS))),
    "approval": obj(contract_version=enum("platform-bootstrap-approval/v1"),
        reference=REFERENCE, source_sha=SHA1, host_role=enum("scm-ci"),
        components=enum(COMPONENTS), rollback=ROLLBACK),
    "manifest": obj(contract_version=enum("platform-bootstrap/v1"),
        bundle_version=enum(VERSION), source_repository=enum("admin/aisoft-platform"),
        source_sha=SHA1, host_role=enum("scm-ci"), components=enum(COMPONENTS),
        approval_reference=REFERENCE, approval_sha256=SHA256, rollback=ROLLBACK,
        payload_sha256=SHA256, payloads=array(obj(path={"type": "string",
            "pattern": "^(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)*$"}, sha256=SHA256,
            size={"type": "integer", "minimum": 1, "maximum": MAX_BYTES},
            mode=enum(0o644, 0o755)), 1, 100)),
    "handoff": obj(contract_version=enum("platform-bootstrap-handoff/v1"),
        source_sha=SHA1, manifest_sha256=SHA256, archive_sha256=SHA256,
        archive_name=enum("platform-bootstrap.tar.gz")),
    "inventory": obj(contract_version=enum("platform-bootstrap-inventory/v1"),
        target_identity_sha256=SHA256, host_role=enum("scm-ci"),
        evidence_layer=enum("local", "company-live"),
        gitea_state=enum("absent", "present", "unknown"),
        gitea_version=nullable({"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"}),
        gitea_identity_sha256=nullable(SHA256), gitea_healthy=BOOL,
        repository_identity_sha256=nullable(SHA256), source_sha=nullable(SHA1),
        protection=PROTECTION, runner_state=enum("absent", "disabled", "enabled", "unknown"),
        runner_scope=enum("platform-only", "unknown"),
        inbound_state=enum("disabled", "one-shot", "timer", "unknown"),
        ai_present=BOOL, rollback=ROLLBACK, backup_verified=BOOL, restore_verified=BOOL),
    "target": obj(contract_version=enum("platform-bootstrap-target/v1"),
        target_identity_sha256=SHA256, gitea_identity_sha256=SHA256,
        repository_identity_sha256=SHA256,
        approval_reference=REFERENCE, gitea_version=enum("1.26.4"),
        required_ci=CONTEXTS, action_inputs=BINDINGS, site_executor=EXECUTOR),
    "plan": obj(contract_version=enum("platform-bootstrap-plan/v1"),
        source_sha=SHA1, handoff_sha256=SHA256, inventory_sha256=SHA256,
        target_sha256=SHA256, target_identity_sha256=SHA256,
        gitea_identity_sha256=SHA256,
        repository_identity_sha256=SHA256, approval_reference=REFERENCE,
        decision=enum("first-install", "adopt", "adopt-with-remediation",
                      "controlled-upgrade", "BLOCKED"),
        status=enum("PLANNED", "BLOCKED"), reason=enum("READY", "UNKNOWN_STATE", "UNSAFE_HOST",
            "IDENTITY_MISMATCH", "RECOVERY_MISSING", "VERSION_CHANGE", "INCONSISTENT_INVENTORY"),
        rollback=ROLLBACK,
        action_inputs=BINDINGS, site_executor=EXECUTOR,
        actions=array(obj(action=enum(*ACTIONS), mode=enum("change", "no-op")), 0, len(ACTIONS))),
    "request": obj(contract_version=enum("platform-bootstrap-request/v1"),
        plan_sha256=SHA256, source_sha=SHA1, target_identity_sha256=SHA256,
        gitea_identity_sha256=SHA256,
        repository_identity_sha256=SHA256, approval_reference=REFERENCE,
        action=enum(*ACTIONS), direction=enum("apply", "rollback"),
        mode=enum("change", "no-op"), rollback=ROLLBACK,
        exact_inputs={"anyOf": list(PARAMETERS.values())},
        predecessor_actions=array(enum(*ACTIONS), 0, len(ACTIONS)), site_executor=EXECUTOR,
        status=enum("DRY_RUN"), execution=enum("NOT RUN")),
    "observation": obj(contract_version=enum("platform-bootstrap-observation/v1"),
        request_sha256=SHA256, target_identity_sha256=SHA256,
        gitea_identity_sha256=SHA256,
        repository_identity_sha256=SHA256, source_sha=nullable(SHA1),
        company_merge_sha=nullable(SHA1), evidence_layer=enum("local", "company-live"),
        result=enum("PASS", "FAIL", "BLOCKED", "NOT RUN"),
        checks=array(enum("identity", "no-op", "negative-permission", "deliberate-failure",
                          "recovery", "required-ci", "human-merge", "provenance"), 0, 8),
        evidence_sha256=SHA256),
}


def validate(value: object, schema: dict) -> None:
    """The closed schema subset used above; no remote refs or dependencies."""
    if "anyOf" in schema:
        for candidate in schema["anyOf"]:
            try:
                validate(value, candidate)
                return
            except BootstrapError:
                pass
        raise BootstrapError("SCHEMA_INVALID")
    if "enum" in schema:
        require(any(type(value) is type(item) and value == item
                    for item in schema["enum"]), "SCHEMA_INVALID")
    kind = schema.get("type")
    if kind:
        require(type(value) is {"object": dict, "array": list, "string": str,
                "integer": int, "boolean": bool, "null": type(None)}[kind], "SCHEMA_INVALID")
    if kind == "object":
        require(set(value) == set(schema["properties"]), "SCHEMA_INVALID")
        for key, child in schema["properties"].items():
            validate(value[key], child)
    elif kind == "array":
        require(schema["minItems"] <= len(value) <= schema["maxItems"], "SCHEMA_INVALID")
        require(len({canonical(item) for item in value}) == len(value), "SCHEMA_INVALID")
        for item in value:
            validate(item, schema["items"])
    elif kind == "string" and "pattern" in schema:
        require(re.fullmatch(schema["pattern"], value) is not None, "SCHEMA_INVALID")
    elif kind == "integer":
        require(schema["minimum"] <= value <= schema["maximum"], "SCHEMA_INVALID")


def document(value: object, kind: str) -> dict:
    validate(value, SCHEMAS[kind])
    if kind == "actions":
        require([entry["action"] for entry in value["actions"]] == ACTIONS, "ACTION_INVALID")
    if kind == "request":
        validate(value["exact_inputs"], PARAMETERS[value["action"]])
        require(value["predecessor_actions"] == ACTIONS[:ACTIONS.index(value["action"])], "ACTION_INVALID")
    if kind == "target":
        inputs = value["action_inputs"]
        require(inputs["gitea-adoption"]["gitea_version"] == value["gitea_version"] and
                inputs["required-ci"]["contexts"] == inputs["canary"]["required_contexts"] == value["required_ci"],
                "IDENTITY_MISMATCH")
        require(inputs["repo-bootstrap"]["staging_ref"] == inputs["one-shot-inbound"]["staging_ref"] and
                inputs["repo-bootstrap"]["source_refs_sha256"] == inputs["one-shot-inbound"]["source_refs_sha256"] and
                inputs["repo-bootstrap"]["transport_identity_sha256"] == inputs["one-shot-inbound"]["transport_identity_sha256"],
                "IDENTITY_MISMATCH")
    if "rollback" in value:
        rollback = value["rollback"]
        require(rollback["kind"] != "uninstalled" or rollback["source_sha"] is None,
                "ROLLBACK_INVALID")
    return value


def _pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON_INVALID")
        result[key] = value
    return result


def parse(data: bytes, kind: str) -> dict:
    require(len(data) <= MAX_BYTES, "RESOURCE_LIMIT")
    try:
        value = json.loads(data, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(BootstrapError("JSON_INVALID")))
        return document(value, kind)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise BootstrapError("JSON_INVALID") from exc


def safe_path(path: Path) -> Path:
    require(path.is_absolute() and ".." not in path.parts, "UNSAFE_PATH")
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "UNSAFE_PATH")
    return path


def read_regular(path: Path, limit: int = MAX_BYTES) -> bytes:
    safe_path(path)
    meta = path.lstat()
    require(stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1, "UNSAFE_PATH")
    require(meta.st_size <= limit, "RESOURCE_LIMIT")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "RESOURCE_LIMIT")
    return data


def load(path: Path, kind: str) -> dict:
    return parse(read_regular(path), kind)


def write_new(path: Path, data: bytes) -> None:
    safe_path(path)
    with path.open("xb") as stream:
        path.chmod(0o600)
        stream.write(data)
