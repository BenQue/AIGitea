"""Issue #274: profile-bound, stdout-only company SCM baseline collector."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
from http.client import HTTPException
import ipaddress
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


VERSION = "2.0.0"
CONTRACT = "company-platform-baseline/v2"
PROFILE_CONTRACT = "company-platform-baseline-profile/v1"
PROFILE_FILENAME = "baseline-profile.json"
LIMIT = 65536
HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
SHA = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
TIME = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}
UUID = {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"}
VER = {"type": "string", "pattern": "^[0-9]{1,3}\\.[0-9]{1,3}(\\.[0-9]{1,3})?$"}
IPV4 = {"type": "string", "pattern": "^[0-9]{1,3}(\\.[0-9]{1,3}){3}$"}
CLUSTER = {"type": "string", "pattern": "^[a-z][a-z0-9]{0,31}$"}


class Invalid(ValueError):
    """Only stable codes cross stdout; rejected input never does."""


def obj(properties, *, optional=()):
    return {"type": "object", "additionalProperties": False,
            "required": [key for key in properties if key not in optional], "properties": properties}


def enum(*values):
    return {"enum": list(values)}


def number(maximum=2**63 - 1, minimum=0):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


SERVICE = obj({"enabled": enum("enabled", "disabled", "static", "masked", "not-found"),
               "active": enum("active", "inactive", "failed", "not-found")})
STORAGE = obj({"kind": enum("directory", "other", "symlink", "absent"),
               "uid": number(2**32 - 1), "gid": number(2**32 - 1),
               "mode": number(4095), "free_bytes": number()})
YESNO = enum("yes", "no")
LISTENER = enum("loopback", "exposed", "absent", "mismatch")
VALUES = {
    "gitea_service": SERVICE, "postgresql_service": SERVICE, "runner_service": SERVICE,
    "gitea_binary": VER, "postgresql_binary": VER,
    "gitea_listener": LISTENER, "postgresql_listener": LISTENER,
    "gitea_health": enum("pass", "fail"), "gitea_api_version": VER,
    "gitea_storage": STORAGE, "postgresql_storage": STORAGE,
    "ufw": obj({"active": YESNO, "default_deny_incoming": YESNO,
                "rule_count": number(10000)}),
    "network": enum("reachable", "unreachable"),
    "authentication": enum("available", "unavailable"),
    "acl": enum("read-allowed", "denied"),
    "repository": obj({"exists": YESNO, "identity_sha256": HASH,
                       "head_sha": {"anyOf": [SHA, enum(None)]}}),
    "protection": obj({"direct_push_denied": YESNO, "force_push_denied": YESNO,
                       "human_only_merge": YESNO, "required_ci_count": number(1000)}),
    "runner_registration": enum("registered", "absent"),
    "sync": obj({"timer": SERVICE, "source_sha": {"anyOf": [SHA, enum(None)]},
                 "destination_sha": {"anyOf": [SHA, enum(None)]}}),
    "backup": obj({"available": YESNO, "off_host": YESNO,
                   "set_sha256": {"anyOf": [HASH, enum(None)]}}),
    "isolated_restore": obj({"verified": YESNO, "isolated": YESNO,
                             "set_sha256": {"anyOf": [HASH, enum(None)]}}),
    "postgresql_server_version": VER,
    "ufw_review": enum("approved-networks-only", "remediation-required"),
    "storage_ownership": enum("expected-service-owners", "mismatch"),
    "service_binding": enum("fixed-binaries-and-data", "mismatch"),
}
MANUAL = frozenset({"network", "authentication", "acl", "repository", "protection",
                    "runner_registration", "sync", "backup", "isolated_restore",
                    "postgresql_server_version", "ufw_review", "storage_ownership",
                    "service_binding"})
CRITICAL = frozenset(VALUES) - {"repository", "protection", "runner_registration", "sync", "runner_service"}


def profile_schema():
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **obj({
        "contract_version": enum(PROFILE_CONTRACT),
        "gitea": obj({
            "unit": enum("aisoft-gitea.service"),
            "binary": enum("/opt/aisoft/gitea/1.26.4/gitea"),
            "expected_version": enum("1.26.4"),
            "listen_ip": IPV4,
            "port": number(65535, 1024),
            "storage": enum("/var/lib/aisoft-gitea"),
        }),
        "postgresql": obj({
            "major": enum(18),
            "cluster": CLUSTER,
            "unit": {"type": "string", "pattern": "^postgresql@18-[a-z][a-z0-9]{0,31}\\.service$"},
            "binary": enum("/usr/lib/postgresql/18/bin/postgres"),
            "expected_version": VER,
            "listen_ip": enum("127.0.0.1"),
            "port": number(65535, 1024),
            "storage": {"type": "string", "pattern": "^/var/lib/postgresql/18/[a-z][a-z0-9]{0,31}$"},
        }),
    })}


def observation_schema(key):
    return obj({"status": enum("PASS", "GAP", "BLOCKED", "NOT RUN"),
                "basis": enum("host-probe", "operator-reviewed", "historical", "none"),
                "reason": enum("observed", "not-collected", "probe-unavailable"),
                "value": {"anyOf": [VALUES[key], enum(None)]},
                "evidence_sha256": {"anyOf": [HASH, enum(None)]}})


def binding_schema():
    return {"environment": enum("company-scm-ci"), "host_role": enum("scm-ci"),
            "host_sha256": HASH, "source_sha": SHA, "collector_sha256": HASH,
            "profile_sha256": HASH, "evidence_id": UUID}


def schema():
    inventory = obj({"contract_version": enum(CONTRACT), "collector_version": enum(VERSION),
                     **binding_schema(), "profile": profile_schema(), "collected_at": TIME,
                     "current": obj({key: observation_schema(key) for key in VALUES}),
                     "historical": obj({key: observation_schema(key) for key in VALUES}, optional=VALUES)})
    receipt = obj({"validation": enum("PASS"),
                   "decision": enum("adopt", "adopt-with-remediation", "BLOCKED"),
                   "status": enum("PASS", "GAP", "BLOCKED_EXTERNAL"),
                   "mutation_authorized": enum(False),
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
    if "enum" in rule and not any(type(value) is type(item) and value == item for item in rule["enum"]):
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
        if type(value) is not int or isinstance(value, bool) or not rule["minimum"] <= value <= rule["maximum"]:
            raise Invalid("SCHEMA_INVALID")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def profile_bytes(profile):
    return canonical(profile) + b"\n"


def profile_digest(profile):
    return hashlib.sha256(profile_bytes(profile)).hexdigest()


def decode(raw):
    if not isinstance(raw, bytes) or len(raw) > LIMIT:
        raise Invalid("INPUT_TOO_LARGE")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid("DUPLICATE_KEY")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Invalid("SCHEMA_INVALID")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("JSON_INVALID") from None


def validate_profile(profile):
    check(profile, profile_schema())
    try:
        address = ipaddress.ip_address(profile["gitea"]["listen_ip"])
    except ValueError:
        raise Invalid("PROFILE_INVALID") from None
    private = any(address in ipaddress.ip_network(network) for network in (
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"))
    if address.version != 4 or not private:
        raise Invalid("PROFILE_INVALID")
    postgresql = profile["postgresql"]
    cluster = postgresql["cluster"]
    if postgresql["unit"] != f"postgresql@18-{cluster}.service":
        raise Invalid("PROFILE_INVALID")
    if postgresql["storage"] != f"/var/lib/postgresql/18/{cluster}":
        raise Invalid("PROFILE_INVALID")
    if not postgresql["expected_version"].startswith("18."):
        raise Invalid("PROFILE_INVALID")
    return profile


def load_profile(path=None):
    target = path or Path(__file__).with_name(PROFILE_FILENAME)
    descriptor = None
    try:
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        descriptor = os.open(target, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
            raise Invalid("PROFILE_FILE_UNSAFE")
        raw = bytearray()
        while len(raw) <= LIMIT:
            chunk = os.read(descriptor, min(4096, LIMIT + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        raw = bytes(raw)
    except Invalid:
        raise
    except OSError:
        raise Invalid("PROFILE_UNAVAILABLE") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    profile = validate_profile(decode(raw))
    if raw != profile_bytes(profile):
        raise Invalid("PROFILE_NOT_CANONICAL")
    return profile


def good(key, value, profile):
    if key.endswith("_service"):
        return value == {"enabled": "enabled", "active": "active"}
    if key in {"gitea_binary", "gitea_api_version"}:
        return value == profile["gitea"]["expected_version"]
    if key in {"postgresql_binary", "postgresql_server_version"}:
        return value == profile["postgresql"]["expected_version"]
    if key == "gitea_listener":
        expected = "loopback" if profile["gitea"]["listen_ip"].startswith("127.") else "exposed"
        return value == expected
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
        return all(value[name] == "yes" for name in (
            "direct_push_denied", "force_push_denied", "human_only_merge")) and value["required_ci_count"] > 0
    if key == "sync":
        return (good("runner_service", value["timer"], profile) and value["source_sha"] is not None
                and value["source_sha"] == value["destination_sha"])
    if key == "backup":
        return value["available"] == "yes" and value["off_host"] == "yes"
    if key == "isolated_restore":
        return value["verified"] == "yes" and value["isolated"] == "yes"
    return value == {"gitea_health": "pass", "network": "reachable",
                     "authentication": "available", "acl": "read-allowed",
                     "runner_registration": "registered", "ufw_review": "approved-networks-only",
                     "storage_ownership": "expected-service-owners",
                     "service_binding": "fixed-binaries-and-data"}[key]


def observation(key, profile, value=None, *, basis="host-probe", evidence=None, blocked=False):
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
    return {"status": "PASS" if good(key, value, profile) else "GAP", "basis": basis,
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
    profile = validate_profile(inventory["profile"])
    if inventory["profile_sha256"] != profile_digest(profile):
        raise Invalid("PROFILE_DIGEST_MISMATCH")
    fresh(inventory["collected_at"], now or utcnow())
    for layer in ("current", "historical"):
        for key, record in inventory[layer].items():
            value = record["value"]
            if value is None:
                expected = observation(key, profile, blocked=record["status"] == "BLOCKED")
            else:
                basis = ("historical" if layer == "historical"
                         else "operator-reviewed" if key in MANUAL else "host-probe")
                if basis != "host-probe" and record["evidence_sha256"] is None:
                    raise Invalid("EVIDENCE_MISSING")
                if basis == "host-probe" and record["evidence_sha256"] is not None:
                    raise Invalid("EVIDENCE_INVALID")
                expected = observation(key, profile, value, basis=basis, evidence=record["evidence_sha256"])
            if record != expected:
                raise Invalid("STATUS_MISMATCH")
    current = inventory["current"]
    differences = sorted(key for key, value in current.items() if value["status"] != "PASS")
    blocked = any(current[key]["status"] in {"BLOCKED", "NOT RUN"} or key in CRITICAL for key in differences)
    backup = current["backup"]["value"]
    restore = current["isolated_restore"]["value"]
    if backup and restore and backup["set_sha256"] != restore["set_sha256"]:
        blocked = True
        differences = sorted(set(differences) | {"isolated_restore"})
    return {"validation": "PASS",
            "decision": "BLOCKED" if blocked else "adopt-with-remediation" if differences else "adopt",
            "status": "BLOCKED_EXTERNAL" if blocked else "GAP" if differences else "PASS",
            "mutation_authorized": False, "differences": differences}


def seal(inventory, now=None):
    return {"inventory": inventory, "inventory_sha256": digest(inventory),
            "receipt": assess(inventory, now)}


def verify(envelope, binding, now=None):
    check(envelope, schema())
    if any(envelope["inventory"][key] != value for key, value in binding.items()):
        raise Invalid("BINDING_MISMATCH")
    if envelope != seal(envelope["inventory"], now):
        raise Invalid("CHECKSUM_OR_RECEIPT_MISMATCH")
    return envelope["receipt"]


def run(argv):
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
                process.kill()
                process.wait()


def get(host, port, path):
    if path not in {"/api/healthz", "/api/v1/version"}:
        raise Invalid("TARGET_DENIED")
    validate_profile({"contract_version": PROFILE_CONTRACT,
                      "gitea": {"unit": "aisoft-gitea.service",
                                "binary": "/opt/aisoft/gitea/1.26.4/gitea",
                                "expected_version": "1.26.4", "listen_ip": host,
                                "port": port, "storage": "/var/lib/aisoft-gitea"},
                      "postgresql": {"major": 18, "cluster": "probe",
                                     "unit": "postgresql@18-probe.service",
                                     "binary": "/usr/lib/postgresql/18/bin/postgres",
                                     "expected_version": "18.0", "listen_ip": "127.0.0.1",
                                     "port": 55432, "storage": "/var/lib/postgresql/18/probe"}})
    connection = http.client.HTTPConnection(host, port, timeout=3)
    try:
        connection.request("GET", path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        return response.status, response.read(LIMIT + 1)
    finally:
        connection.close()


def metadata(path):
    target = Path(path)
    if any(parent.is_symlink() for parent in (target, *target.parents)):
        return {"kind": "symlink", "uid": 0, "gid": 0, "mode": 0, "free_bytes": 0}
    try:
        info = target.lstat()
    except FileNotFoundError:
        return {"kind": "absent", "uid": 0, "gid": 0, "mode": 0, "free_bytes": 0}
    space = os.statvfs(target)
    return {"kind": "directory" if stat.S_ISDIR(info.st_mode) else "other",
            "uid": info.st_uid, "gid": info.st_gid, "mode": stat.S_IMODE(info.st_mode),
            "free_bytes": space.f_bavail * space.f_frsize}


def host_digest():
    return hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()


def script_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def collect(binding, *, profile=None, invoke=run, http=get, storage=metadata, now=None):
    check(binding, obj(binding_schema()))
    profile = validate_profile(profile) if profile is not None else load_profile()
    if (binding["host_sha256"] != host_digest()
            or binding["collector_sha256"] != script_digest()
            or binding["profile_sha256"] != profile_digest(profile)):
        raise Invalid("BINDING_MISMATCH")
    if sys.platform != "linux":
        raise Invalid("TARGET_UNAVAILABLE")
    inventory = {"contract_version": CONTRACT, "collector_version": VERSION, **binding,
                 "profile": profile, "collected_at": timestamp(now or utcnow()),
                 "current": {key: observation(key, profile) for key in VALUES}, "historical": {}}

    def probe(key, function):
        try:
            inventory["current"][key] = observation(key, profile, function())
        except (Invalid, OSError, ValueError, TimeoutError, subprocess.TimeoutExpired, HTTPException):
            inventory["current"][key] = observation(key, profile, blocked=True)

    def service(unit):
        return {"enabled": invoke(["/usr/bin/systemctl", "is-enabled", unit])[1],
                "active": invoke(["/usr/bin/systemctl", "is-active", unit])[1]}

    def binary(command, pattern):
        rc, text = invoke([command, "--version"])
        match = re.fullmatch(pattern, text) if rc == 0 else None
        if not match:
            raise Invalid("PROBE_UNAVAILABLE")
        return match[1]

    def listener(expected_ip, port):
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
        if set(addresses) != {expected_ip}:
            return "mismatch"
        return "loopback" if expected_ip.startswith("127.") else "exposed"

    def endpoint(path):
        gitea = profile["gitea"]
        code, raw = http(gitea["listen_ip"], gitea["port"], path)
        if code != 200 or len(raw) > LIMIT:
            raise Invalid("PROBE_UNAVAILABLE")
        value = decode(raw)
        if type(value) is not dict:
            raise Invalid("PROBE_UNAVAILABLE")
        if path == "/api/v1/version":
            check(value, obj({"version": VER}))
            return value["version"]
        checks = value.get("checks")
        if value.get("status") != "pass" or type(checks) is not dict or set(checks) != {"database:ping", "cache:ping"}:
            return "fail"
        if not all(type(entries) is list and entries
                   and all(type(entry) is dict and entry.get("status") == "pass" for entry in entries)
                   for entries in checks.values()):
            return "fail"
        return "pass"

    def ufw():
        rc, text = invoke(["/usr/sbin/ufw", "status", "verbose"])
        if rc != 0 or not text.startswith(("Status: active", "Status: inactive")):
            raise Invalid("PROBE_UNAVAILABLE")
        return {"active": "yes" if text.startswith("Status: active") else "no",
                "default_deny_incoming": "yes" if re.search(r"^Default: deny \(incoming\),", text, re.M) else "no",
                "rule_count": len(re.findall(r"^.*\b(?:ALLOW|DENY|REJECT|LIMIT)\b.*$", text, re.M))}

    gitea, postgresql = profile["gitea"], profile["postgresql"]
    for key, unit in (("gitea_service", gitea["unit"]),
                      ("postgresql_service", postgresql["unit"]),
                      ("runner_service", "act_runner.service")):
        probe(key, lambda unit=unit: service(unit))
    for key, command, pattern in (
            ("gitea_binary", gitea["binary"], r"Gitea version ([0-9.]+)(?: built with [^\r\n]+)?"),
            ("postgresql_binary", postgresql["binary"], r"postgres \(PostgreSQL\) ([0-9.]+)(?: \([^\r\n]+\))?")):
        probe(key, lambda command=command, pattern=pattern: binary(command, pattern))
    for key, component in (("gitea_listener", gitea), ("postgresql_listener", postgresql)):
        probe(key, lambda component=component: listener(component["listen_ip"], component["port"]))
    for key, path in (("gitea_health", "/api/healthz"), ("gitea_api_version", "/api/v1/version")):
        probe(key, lambda path=path: endpoint(path))
    for key, path in (("gitea_storage", gitea["storage"]),
                      ("postgresql_storage", postgresql["storage"])):
        probe(key, lambda path=path: storage(path))
    probe("ufw", ufw)
    return seal(inventory, now)


def supplement(envelope, record, binding, now=None):
    now = now or utcnow()
    verify(envelope, binding, now)
    profile = envelope["inventory"]["profile"]
    check(record, obj({**binding_schema(), "observed_at": TIME, "evidence_sha256": HASH,
                       "facts": obj({key: VALUES[key] for key in sorted(MANUAL)}, optional=MANUAL)}))
    if any(record[key] != value for key, value in binding.items()):
        raise Invalid("BINDING_MISMATCH")
    fresh(record["observed_at"], now)
    if record["observed_at"] < envelope["inventory"]["collected_at"]:
        raise Invalid("STALE_EVIDENCE")
    inventory = decode(canonical(envelope["inventory"]))
    for key, value in record["facts"].items():
        inventory["current"][key] = observation(
            key, profile, value, basis="operator-reviewed", evidence=record["evidence_sha256"])
    return seal(inventory, now)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Invalid("ARGUMENT_INVALID")


def emit(value, *, pretty=False):
    try:
        print(json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2 if pretty else None), flush=True)
    except OSError:
        os._exit(20)


def main(argv=None):
    try:
        parser = Parser(description=__doc__, allow_abbrev=False)
        parser.add_argument("command", choices=(
            "schema", "profile-schema", "identity", "collect", "verify", "supplement"))
        for name in ("environment", "host-role", "host-sha256", "source-sha",
                     "collector-sha256", "profile-sha256", "evidence-id"):
            parser.add_argument("--" + name)
        args = vars(parser.parse_args(argv))
        command = args.pop("command")
        if command in {"identity", "collect"} and not (
                sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise Invalid("UNSAFE_INTERPRETER")
        if command in {"schema", "profile-schema", "identity"}:
            if any(value is not None for value in args.values()):
                raise Invalid("ARGUMENT_INVALID")
            if command == "schema":
                result = schema()
            elif command == "profile-schema":
                result = profile_schema()
            else:
                profile = load_profile()
                result = {"host_sha256": host_digest(), "collector_sha256": script_digest(),
                          "profile_sha256": profile_digest(profile)}
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
        emit(result, pretty=command in {"schema", "profile-schema"})
        receipt = result.get("receipt", result)
        return 20 if receipt.get("decision") == "BLOCKED" else 0
    except (Invalid, OSError, UnicodeError, RecursionError) as exc:
        code = str(exc) if isinstance(exc, Invalid) else "INPUT_UNAVAILABLE"
        emit({"status": "BLOCKED_EXTERNAL", "code": code})
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
