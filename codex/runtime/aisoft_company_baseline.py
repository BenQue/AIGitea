"""Issue #271: stdout-only, fixed-target company adoption evidence. Python stdlib."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import selectors
import socket
import stat
import subprocess
import sys
import time

VERSION = "1.0.0"
CONTRACT = "company-platform-baseline/v1"
LIMIT = 65536
HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
SHA = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
TIME = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}
UUID = {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"}
VER = {"type": "string", "pattern": "^[0-9]{1,3}\\.[0-9]{1,3}(\\.[0-9]{1,3})?$"}


class Invalid(ValueError):
    """Only stable codes cross the stdout boundary; never include rejected data."""


def obj(properties, *, optional=()):
    return {"type": "object", "additionalProperties": False,
            "required": [k for k in properties if k not in optional], "properties": properties}


def enum(*values):
    return {"enum": list(values)}


def number(maximum=2**63 - 1):
    return {"type": "integer", "minimum": 0, "maximum": maximum}


SERVICE = obj({"enabled": enum("enabled", "disabled", "static", "masked", "not-found"),
               "active": enum("active", "inactive", "failed", "not-found")})
STORAGE = obj({"kind": enum("directory", "other", "symlink", "absent"),
               "uid": number(2**32-1), "gid": number(2**32-1),
               "mode": number(4095), "free_bytes": number()})
YESNO = enum("yes", "no")
# Closed fields intentionally cannot carry usernames, paths, URLs, headers or logs.
VALUES = {
    "gitea_service": SERVICE, "postgresql_service": SERVICE, "runner_service": SERVICE,
    "gitea_binary": VER, "postgresql_binary": VER,
    "gitea_listener": enum("loopback", "exposed", "absent"),
    "postgresql_listener": enum("loopback", "exposed", "absent"),
    "gitea_health": enum("pass", "fail"), "gitea_api_version": VER,
    "gitea_storage": STORAGE, "postgresql_storage": STORAGE,
    "ufw": obj({"active": YESNO, "default_deny_incoming": YESNO,
                "rule_count": number(10000)}),
    "network": enum("reachable", "unreachable"),
    "authentication": enum("available", "unavailable"),
    "acl": enum("read-allowed", "denied"),
    "repository": obj({"exists": YESNO, "identity_sha256": HASH, "head_sha": {"anyOf": [SHA, enum(None)]}}),
    "protection": obj({"direct_push_denied": YESNO, "force_push_denied": YESNO,
                       "human_only_merge": YESNO, "required_ci_count": number(1000)}),
    "runner_registration": enum("registered", "absent", "unknown"),
    "sync": obj({"timer": SERVICE, "source_sha": {"anyOf": [SHA, enum(None)]},
                 "destination_sha": {"anyOf": [SHA, enum(None)]}}),
    "backup": obj({"available": YESNO, "off_host": YESNO, "set_sha256": {"anyOf": [HASH, enum(None)]}}),
    "isolated_restore": obj({"verified": YESNO, "isolated": YESNO, "set_sha256": {"anyOf": [HASH, enum(None)]}}),
    "postgresql_server_version": VER,
    "ufw_review": enum("approved-networks-only", "remediation-required"),
    "storage_ownership": enum("expected-service-owners", "mismatch"),
    "service_binding": enum("fixed-binaries-and-data", "mismatch"),
}
MANUAL = frozenset({"network", "authentication", "acl", "repository", "protection",
                    "runner_registration", "sync", "backup", "isolated_restore",
                    "postgresql_server_version", "ufw_review", "storage_ownership", "service_binding"})
CRITICAL = frozenset(VALUES) - {"repository", "protection", "runner_registration", "sync", "runner_service"}
UNITS = {"gitea_service": "aisoft-gitea.service",
         "postgresql_service": "postgresql@18-aisoft-gitea.service",
         "runner_service": "act_runner.service"}
BINARIES = {"gitea_binary": ("/opt/aisoft/gitea/1.26.4/gitea", r"Gitea version ([0-9.]+)(?: built with [^\r\n]+)?"),
            "postgresql_binary": ("/usr/lib/postgresql/18/bin/postgres", r"postgres \(PostgreSQL\) ([0-9.]+)(?: \([^\r\n]+\))?")}
STORES = {"gitea_storage": "/var/lib/aisoft-gitea",
          "postgresql_storage": "/var/lib/postgresql/18/aisoft-gitea"}


def observation_schema(key):
    return obj({"status": enum("PASS", "GAP", "BLOCKED", "NOT RUN"),
                "basis": enum("host-probe", "operator-reviewed", "historical", "none"),
                "reason": enum("observed", "not-collected", "probe-unavailable"),
                "value": {"anyOf": [VALUES[key], enum(None)]},
                "evidence_sha256": {"anyOf": [HASH, enum(None)]}})


def binding_schema():
    return {"environment": enum("company-scm-ci"), "host_role": enum("scm-ci"),
            "host_sha256": HASH, "source_sha": SHA, "collector_sha256": HASH, "evidence_id": UUID}


def schema():
    inventory = obj({"contract_version": enum(CONTRACT), "collector_version": enum(VERSION),
                     **binding_schema(), "collected_at": TIME,
                     "current": obj({k: observation_schema(k) for k in VALUES}),
                     "historical": obj({k: observation_schema(k) for k in VALUES}, optional=VALUES)})
    receipt = obj({"validation": enum("PASS"), "decision": enum("adopt", "adopt-with-remediation", "BLOCKED"),
                   "status": enum("PASS", "GAP", "BLOCKED_EXTERNAL"), "mutation_authorized": enum(False),
                   "differences": {"type": "array", "uniqueItems": True,
                                   "maxItems": len(VALUES), "items": enum(*VALUES)}})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **obj({
        "inventory": inventory, "inventory_sha256": HASH, "receipt": receipt})}


def check(value, rule):
    if "anyOf" in rule:
        for choice in rule["anyOf"]:
            try:
                check(value, choice)
                return
            except Invalid:
                pass
        raise Invalid("SCHEMA_INVALID")
    if "enum" in rule and not any(type(value) is type(v) and value == v for v in rule["enum"]):
        raise Invalid("SCHEMA_INVALID")
    kind = rule.get("type")
    if kind == "object":
        if type(value) is not dict or set(value) - set(rule["properties"]) or set(rule["required"]) - set(value):
            raise Invalid("SCHEMA_INVALID")
        for key, item in value.items():
            check(item, rule["properties"][key])
    elif kind == "array":
        if type(value) is not list or len(value) > rule["maxItems"] or len(set(map(canonical, value))) != len(value):
            raise Invalid("SCHEMA_INVALID")
        for item in value:
            check(item, rule["items"])
    elif kind == "string":
        if type(value) is not str or len(value) > 128 or not re.fullmatch(rule["pattern"], value):
            raise Invalid("SCHEMA_INVALID")
    elif kind == "integer":
        if type(value) is not int or not rule["minimum"] <= value <= rule["maximum"]:
            raise Invalid("SCHEMA_INVALID")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    if len(raw) > LIMIT:
        raise Invalid("INPUT_LIMIT")

    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise Invalid("DUPLICATE_KEY")
            result[k] = v
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Invalid("SCHEMA_INVALID")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("JSON_INVALID") from None


def good(key, value):
    if key.endswith("_service"):
        return value == {"enabled": "enabled", "active": "active"}
    if key in {"gitea_binary", "gitea_api_version"}:
        return value == "1.26.4"
    if key in {"postgresql_binary", "postgresql_server_version"}:
        return value == "18.4"
    if key == "gitea_listener":
        return value in {"loopback", "exposed"}  # exposure judged independently by UFW review
    if key == "postgresql_listener":
        return value == "loopback"
    if key.endswith("_storage"):
        return (value["kind"] == "directory" and value["uid"] != 0
                and value["mode"] & 0o7022 == 0 and value["mode"] & 0o700 == 0o700
                and value["free_bytes"] > 0)
    if key == "ufw":
        return value["active"] == "yes" and value["default_deny_incoming"] == "yes"
    if key == "repository":
        return value["exists"] == "yes" and value["head_sha"] is not None
    if key == "protection":
        return all(value[k] == "yes" for k in ("direct_push_denied", "force_push_denied", "human_only_merge")) and value["required_ci_count"] > 0
    if key == "sync":
        return (good("runner_service", value["timer"]) and value["source_sha"] is not None
                and value["source_sha"] == value["destination_sha"])
    if key == "backup":
        return value["available"] == "yes" and value["off_host"] == "yes"
    if key == "isolated_restore":
        return value["verified"] == "yes" and value["isolated"] == "yes"
    return value == {"gitea_health": "pass", "network": "reachable", "authentication": "available",
                     "acl": "read-allowed", "runner_registration": "registered",
                     "ufw_review": "approved-networks-only", "storage_ownership": "expected-service-owners",
                     "service_binding": "fixed-binaries-and-data"}[key]


def observation(key, value=None, *, basis="host-probe", evidence=None, blocked=False):
    if value is None:
        return {"status": "BLOCKED" if blocked else "NOT RUN", "basis": "none",
                "reason": "probe-unavailable" if blocked else "not-collected",
                "value": None, "evidence_sha256": None}
    check(value, VALUES[key])
    if key == "repository" and value["exists"] == "no" and value["head_sha"] is not None:
        raise Invalid("EVIDENCE_INVALID")
    if key == "backup" and (value["available"] == "yes") != (value["set_sha256"] is not None):
        raise Invalid("EVIDENCE_INVALID")
    if key == "isolated_restore" and value["verified"] == "yes" and value["set_sha256"] is None:
        raise Invalid("EVIDENCE_INVALID")
    return {"status": "PASS" if good(key, value) else "GAP", "basis": basis,
            "reason": "observed", "value": value, "evidence_sha256": evidence}


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0)


def timestamp(now):
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def fresh(text, now):
    try:
        age = (now - datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds()
    except ValueError:
        raise Invalid("TIME_INVALID") from None
    if not 0 <= age <= 86400:
        raise Invalid("STALE_EVIDENCE")


def assess(inventory, now=None):
    check(inventory, schema()["properties"]["inventory"])
    fresh(inventory["collected_at"], now or utcnow())
    for layer in ("current", "historical"):
        for key, record in inventory[layer].items():
            value = record["value"]
            if value is None:
                expected = observation(key, blocked=record["status"] == "BLOCKED")
            else:
                basis = "historical" if layer == "historical" else "operator-reviewed" if key in MANUAL else "host-probe"
                if basis != "host-probe" and record["evidence_sha256"] is None:
                    raise Invalid("EVIDENCE_MISSING")
                if basis == "host-probe" and record["evidence_sha256"] is not None:
                    raise Invalid("EVIDENCE_INVALID")
                expected = observation(key, value, basis=basis, evidence=record["evidence_sha256"])
            if record != expected:
                raise Invalid("STATUS_MISMATCH")
    current = inventory["current"]
    differences = sorted(k for k, v in current.items() if v["status"] != "PASS")
    blocked = any(current[k]["status"] in {"BLOCKED", "NOT RUN"} or k in CRITICAL for k in differences)
    backup = current["backup"]["value"]
    restore = current["isolated_restore"]["value"]
    if backup and restore and backup["set_sha256"] != restore["set_sha256"]:
        blocked = True
        differences = sorted(set(differences) | {"isolated_restore"})
    return {"validation": "PASS", "decision": "BLOCKED" if blocked else "adopt-with-remediation" if differences else "adopt",
            "status": "BLOCKED_EXTERNAL" if blocked else "GAP" if differences else "PASS",
            "mutation_authorized": False, "differences": differences}


def seal(inventory, now=None):
    return {"inventory": inventory, "inventory_sha256": digest(inventory), "receipt": assess(inventory, now)}


def verify(envelope, binding, now=None):
    check(envelope, schema())
    if any(envelope["inventory"][k] != v for k, v in binding.items()):
        raise Invalid("BINDING_MISMATCH")
    if envelope != seal(envelope["inventory"], now):
        raise Invalid("CHECKSUM_OR_RECEIPT_MISMATCH")
    return envelope["receipt"]


def run(argv):
    # No inherited environment, shell, stdin, raw stderr, journal or temp files.
    with subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL,
                          env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"}) as process:
        output = bytearray()
        deadline = time.monotonic() + 4
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    left = deadline - time.monotonic()
                    if left <= 0 or not selector.select(left):
                        raise Invalid("PROBE_UNAVAILABLE")
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > LIMIT:
                        raise Invalid("PROBE_UNAVAILABLE")
            rc = process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if rc not in {0, 1, 3, 4}:
                raise Invalid("PROBE_UNAVAILABLE")
            return rc, output.decode("utf-8", errors="strict").strip()
        finally:
            if process.poll() is None:
                process.kill()  # terminate only this collector's bounded read-only child
                process.wait()


def get(path):
    if path not in {"/api/healthz", "/api/v1/version"}:
        raise Invalid("TARGET_DENIED")
    connection = http.client.HTTPConnection("127.0.0.1", 8888, timeout=3)
    try:
        connection.request("GET", path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        return response.status, response.read(LIMIT + 1)
    finally:
        connection.close()


def metadata(path):
    target = Path(path)
    # Reject symlink ancestors before querying target filesystem metadata.
    if any(p.is_symlink() for p in (target, *target.parents)):
        return {"kind": "symlink", "uid": 0, "gid": 0, "mode": 0, "free_bytes": 0}
    try:
        info = target.lstat()
    except FileNotFoundError:
        return {"kind": "absent", "uid": 0, "gid": 0, "mode": 0, "free_bytes": 0}
    space = os.statvfs(target)
    return {"kind": "directory" if stat.S_ISDIR(info.st_mode) else "other", "uid": info.st_uid,
            "gid": info.st_gid, "mode": stat.S_IMODE(info.st_mode), "free_bytes": space.f_bavail * space.f_frsize}


def host_digest():
    return hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()


def script_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def collect(binding, *, invoke=run, http=get, storage=metadata, now=None):
    check(binding, obj(binding_schema()))
    if binding["host_sha256"] != host_digest() or binding["collector_sha256"] != script_digest():
        raise Invalid("BINDING_MISMATCH")
    if sys.platform != "linux":
        raise Invalid("TARGET_UNAVAILABLE")
    inventory = {"contract_version": CONTRACT, "collector_version": VERSION, **binding,
                 "collected_at": timestamp(now or utcnow()),
                 "current": {k: observation(k) for k in VALUES}, "historical": {}}

    def probe(key, fn):
        try:
            value = fn()
            inventory["current"][key] = observation(key, value)
        except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired, HTTPException):
            inventory["current"][key] = observation(key, blocked=True)

    def service(unit):
        return {"enabled": invoke(["/usr/bin/systemctl", "is-enabled", unit])[1],
                "active": invoke(["/usr/bin/systemctl", "is-active", unit])[1]}

    def binary(command, pattern):
        rc, text = invoke([command, "--version"])
        match = re.fullmatch(pattern, text) if rc == 0 else None
        if not match:
            raise Invalid("PROBE_UNAVAILABLE")
        return match[1]

    def listener(port):
        rc, text = invoke(["/usr/bin/ss", "-H", "-ltn", f"sport = :{port}"])
        if rc != 0:
            raise Invalid("PROBE_UNAVAILABLE")
        addresses = []
        for line in text.splitlines():
            fields = line.split()
            if len(fields) != 5 or fields[0] != "LISTEN" or not fields[3].endswith(f":{port}"):
                raise Invalid("PROBE_UNAVAILABLE")
            addresses.append(fields[3].rsplit(":", 1)[0])
        if not addresses:
            return "absent"
        return "loopback" if all(a in {"127.0.0.1", "[::1]", "::1"} for a in addresses) else "exposed"

    def endpoint(path):
        code, raw = http(path)
        if code != 200:
            raise Invalid("PROBE_UNAVAILABLE")
        value = decode(raw)
        if type(value) is not dict:
            raise Invalid("PROBE_UNAVAILABLE")
        if path == "/api/v1/version":
            check(value, obj({"version": VER}))
            return value["version"]
        # Gitea also serves this before install; an empty checks map is not ready.
        checks = value.get("checks")
        if value.get("status") != "pass" or type(checks) is not dict or set(checks) != {"database:ping", "cache:ping"}:
            return "fail"
        if not all(type(entries) is list and entries and all(type(e) is dict and e.get("status") == "pass" for e in entries) for entries in checks.values()):
            return "fail"
        return "pass"

    def ufw():
        rc, text = invoke(["/usr/sbin/ufw", "status", "verbose"])
        if rc != 0 or not text.startswith(("Status: active", "Status: inactive")):
            raise Invalid("PROBE_UNAVAILABLE")
        return {"active": "yes" if text.startswith("Status: active") else "no",
                "default_deny_incoming": "yes" if re.search(r"^Default: deny \(incoming\),", text, re.M) else "no",
                "rule_count": len(re.findall(r"^.*\b(?:ALLOW|DENY|REJECT|LIMIT)\b.*$", text, re.M))}

    for key, unit in UNITS.items():
        probe(key, lambda unit=unit: service(unit))
    for key, (command, pattern) in BINARIES.items():
        probe(key, lambda command=command, pattern=pattern: binary(command, pattern))
    for key, port in (("gitea_listener", 8888), ("postgresql_listener", 55432)):
        probe(key, lambda port=port: listener(port))
    for key, path in (("gitea_health", "/api/healthz"), ("gitea_api_version", "/api/v1/version")):
        probe(key, lambda path=path: endpoint(path))
    for key, path in STORES.items():
        probe(key, lambda path=path: storage(path))
    probe("ufw", ufw)
    return seal(inventory, now)


def supplement(envelope, record, binding, now=None):
    """Offline operator-reviewed metadata; never reads the referenced evidence."""
    now = now or utcnow()
    verify(envelope, binding, now)
    check(record, obj({**binding_schema(), "observed_at": TIME, "evidence_sha256": HASH,
                       "facts": obj({k: VALUES[k] for k in sorted(MANUAL)}, optional=MANUAL)}))
    if any(record[k] != v for k, v in binding.items()):
        raise Invalid("BINDING_MISMATCH")
    fresh(record["observed_at"], now)
    if record["observed_at"] < envelope["inventory"]["collected_at"]:
        raise Invalid("STALE_EVIDENCE")
    inventory = decode(canonical(envelope["inventory"]))
    for key, value in record["facts"].items():
        inventory["current"][key] = observation(key, value, basis="operator-reviewed", evidence=record["evidence_sha256"])
    return seal(inventory, now)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Invalid("ARGUMENT_INVALID")


def emit(value, *, pretty=False):
    try:
        print(json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2 if pretty else None), flush=True)
    except OSError:
        # A closed output channel cannot receive a receipt. Avoid shutdown flush
        # diagnostics and do not open a fallback file, device or log.
        os._exit(20)


def main(argv=None):
    try:
        parser = Parser(description=__doc__, allow_abbrev=False)
        parser.add_argument("command", choices=("schema", "identity", "collect", "verify", "supplement"))
        for name in ("environment", "host-role", "host-sha256", "source-sha", "collector-sha256", "evidence-id"):
            parser.add_argument("--" + name)
        args = vars(parser.parse_args(argv))
        command = args.pop("command")
        if command in {"identity", "collect"} and not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise Invalid("UNSAFE_INTERPRETER")
        if command in {"schema", "identity"}:
            if any(v is not None for v in args.values()):
                raise Invalid("ARGUMENT_INVALID")
            result = schema() if command == "schema" else {"host_sha256": host_digest(), "collector_sha256": script_digest()}
        else:
            check(args, obj(binding_schema()))
            if command == "collect":
                result = collect(args)
            else:
                raw = decode(sys.stdin.buffer.read(LIMIT + 1))
                if command == "verify":
                    result = verify(raw, args)
                else:
                    if type(raw) is not dict or set(raw) != {"envelope", "record"}:
                        raise Invalid("SCHEMA_INVALID")
                    result = supplement(raw["envelope"], raw["record"], args)
        emit(result, pretty=command == "schema")
        receipt = result.get("receipt", result)
        return 20 if receipt.get("decision") == "BLOCKED" else 0
    except (Invalid, OSError, UnicodeError, RecursionError) as exc:
        code = str(exc) if isinstance(exc, Invalid) else "INPUT_UNAVAILABLE"
        emit({"status": "BLOCKED_EXTERNAL", "code": code})
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
