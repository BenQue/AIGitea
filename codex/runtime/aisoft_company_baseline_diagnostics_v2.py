"""Issue #280: standalone stdout-only diagnostics; no adoption or mutation grant."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
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
CONTRACT = "company-platform-baseline-diagnostics/v2"
PROFILE_CONTRACT = "company-platform-baseline-profile/v1"
PROFILE_FILENAME = "baseline-profile.json"
CONFIG_PATH = "/etc/aisoft/gitea/app.ini"
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


FAILURE_REASONS = (
    "command-unavailable", "command-failed", "timeout", "output-limit",
    "decode-failed", "parse-failed", "config-unavailable",
)


class ProbeFailure(Exception):
    """Closed reason only; never carry input, command output, or OS error text."""

    def __init__(self, reason):
        if reason not in FAILURE_REASONS:
            raise Invalid("REASON_INVALID")
        self.reason = reason


def obj(properties, *, optional=()):
    return {"type": "object", "additionalProperties": False,
            "required": [key for key in properties if key not in optional], "properties": properties}


def enum(*values):
    return {"enum": list(values)}


def number(maximum=2**63 - 1, minimum=0):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}


YESNO = enum("yes", "no")
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
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
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


def run(argv):
    if argv not in COMMANDS:
        raise Invalid("COMMAND_DENIED")
    deadline = time.monotonic() + 4
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
    except OSError:
        raise ProbeFailure("command-unavailable") from None
    with process:
        output = bytearray()
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    left = deadline - time.monotonic()
                    if left <= 0 or not selector.select(left):
                        raise ProbeFailure("timeout")
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > LIMIT:
                        raise ProbeFailure("output-limit")
            try:
                rc = process.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise ProbeFailure("timeout") from None
            if rc != 0:
                raise ProbeFailure("command-failed")
            try:
                return rc, output.decode("utf-8", errors="strict").strip()
            except UnicodeError:
                raise ProbeFailure("decode-failed") from None
        except OSError:
            raise ProbeFailure("command-failed") from None
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def host_digest():
    return hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()


def script_digest():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


PROPERTIES = ("LoadState", "ActiveState", "SubState", "Result", "MainPID", "ExecMainStatus")
SYSTEMD_COMMAND = ["/usr/bin/systemctl", "show", "aisoft-gitea.service",
                   "--property=" + ",".join(PROPERTIES)]
UFW_COMMAND = ["/usr/sbin/ufw", "status", "verbose"]
COMMANDS = (SYSTEMD_COMMAND, UFW_COMMAND)
VALUES = {
    "systemd": obj({
        "load_state": enum("loaded", "not-found", "error", "bad-setting", "masked", "stub", "merged"),
        "active_state": enum("active", "inactive", "failed", "activating", "deactivating", "reloading", "maintenance", "refreshing"),
        "sub_state": enum("running", "dead", "failed", "exited", "start-pre", "start", "start-post", "auto-restart", "stop", "stop-sigterm", "stop-sigkill", "stop-post", "final-sigterm", "final-sigkill", "reload", "condition", "cleaning"),
        "result": enum("success", "resources", "protocol", "timeout", "exit-code", "signal", "core-dump", "watchdog", "start-limit-hit", "oom-kill", "exec-condition", "skip-condition"),
        "main_pid_present": YESNO, "exec_main_status": number(255)}),
    "server_binding": obj({
        "section_present": YESNO, "protocol_state": enum("missing", "http", "other"),
        "http_addr_matches_profile": YESNO, "http_port_matches_profile": YESNO}),
    "ufw": obj({"active": YESNO, "default_deny_incoming": YESNO, "rule_count": number(10000)}),
}


def binding_schema():
    return {"environment": enum("company-scm-ci"), "host_role": enum("scm-ci"),
            "host_sha256": HASH, "source_sha": SHA, "collector_sha256": HASH,
            "profile_sha256": HASH, "evidence_id": UUID, "baseline_evidence_id": UUID}


def check_binding(binding):
    check(binding, obj(binding_schema()))
    if binding["evidence_id"] == binding["baseline_evidence_id"]:
        raise Invalid("UUID_REUSED")


def schema():
    diagnostic = obj({"contract_version": enum(CONTRACT), "collector_version": enum(VERSION),
                      **binding_schema(), "collected_at": TIME,
                      "observations": obj({key: obj({
                          "status": enum("PASS", "GAP", "BLOCKED"),
                          "reason": enum("observed", *FAILURE_REASONS),
                          "value": {"anyOf": [rule, enum(None)]}}) for key, rule in VALUES.items()})})
    receipt = obj({"validation": enum("PASS"), "status": enum("PASS", "GAP", "BLOCKED_EXTERNAL"),
                   "mutation_authorized": enum(False)})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **obj({
        "diagnostic": diagnostic, "diagnostic_sha256": HASH, "receipt": receipt})}


def observation(key, value=None, reason="observed"):
    if reason in FAILURE_REASONS:
        if value is not None:
            raise Invalid("REASON_VALUE_MISMATCH")
        return {"status": "BLOCKED", "reason": reason, "value": None}
    if reason != "observed" or value is None:
        raise Invalid("REASON_VALUE_MISMATCH")
    check(value, VALUES[key])
    if key == "systemd":
        good = value == {"load_state": "loaded", "active_state": "active", "sub_state": "running",
                         "result": "success", "main_pid_present": "yes", "exec_main_status": 0}
    elif key == "server_binding":
        good = (value["protocol_state"] == "http" and all(
            value[key] == "yes" for key in
            ("section_present", "http_addr_matches_profile", "http_port_matches_profile")))
    else:
        good = value["active"] == value["default_deny_incoming"] == "yes"
    return {"status": "PASS" if good else "GAP", "reason": "observed", "value": value}


def seal(diagnostic, now=None):
    check(diagnostic, schema()["properties"]["diagnostic"])
    check_binding({key: diagnostic[key] for key in binding_schema()})
    fresh(diagnostic["collected_at"], now or utcnow())
    for key, record in diagnostic["observations"].items():
        if record != observation(key, record["value"], record["reason"]):
            raise Invalid("STATUS_MISMATCH")
    states = {record["status"] for record in diagnostic["observations"].values()}
    return {"diagnostic": diagnostic, "diagnostic_sha256": digest(diagnostic),
            "receipt": {"validation": "PASS", "status": "BLOCKED_EXTERNAL" if "BLOCKED" in states else
                        "GAP" if "GAP" in states else "PASS", "mutation_authorized": False}}


def verify(envelope, binding, now=None):
    check_binding(binding)
    check(envelope, schema())
    if any(envelope["diagnostic"][key] != value for key, value in binding.items()):
        raise Invalid("BINDING_MISMATCH")
    if envelope != seal(envelope["diagnostic"], now):
        raise Invalid("CHECKSUM_OR_RECEIPT_MISMATCH")
    return envelope["receipt"]


def systemd(text):
    values = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if not separator or key not in PROPERTIES or key in values:
            raise Invalid("PROBE_UNAVAILABLE")
        values[key] = value
    if set(values) != set(PROPERTIES):
        raise Invalid("PROBE_UNAVAILABLE")
    for key in ("MainPID", "ExecMainStatus"):
        if not re.fullmatch(r"[0-9]{1,10}", values[key]):
            raise Invalid("PROBE_UNAVAILABLE")
    if int(values["MainPID"]) > 2**32 - 1:
        raise Invalid("PROBE_UNAVAILABLE")
    result = {key: values[prop] for key, prop in zip(
        ("load_state", "active_state", "sub_state", "result"), PROPERTIES)}
    result.update(main_pid_present="yes" if int(values["MainPID"]) else "no",
                  exec_main_status=int(values["ExecMainStatus"]))
    check(result, VALUES["systemd"])
    return result


def server_binding(profile):
    descriptor = None
    try:
        descriptor = os.open(CONFIG_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022 or info.st_size > LIMIT:
            raise Invalid("CONFIG_UNAVAILABLE")
        raw = bytearray()
        while len(raw) <= LIMIT:
            chunk = os.read(descriptor, min(4096, LIMIT + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) > LIMIT:
            raise Invalid("CONFIG_UNAVAILABLE")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    # Ignore all other sections/keys: no interpolation and no config exception text.
    selected = {}
    inside = seen = False
    for line in raw.decode("utf-8", errors="strict").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            if not re.fullmatch(r"\[[^\[\]\r\n]+\]", line):
                raise Invalid("CONFIG_INVALID")
            inside = line == "[server]"
            if inside and seen:
                raise Invalid("CONFIG_INVALID")
            seen |= inside
            continue
        if inside:
            key, sep, value = line.partition("=")
            key = key.strip()
            if not sep:
                raise Invalid("CONFIG_INVALID")
            if key in {"PROTOCOL", "HTTP_ADDR", "HTTP_PORT"}:
                if key in selected:
                    raise Invalid("CONFIG_INVALID")
                selected[key] = value.strip()
    return {"section_present": "yes" if seen else "no",
            "protocol_state": ("missing" if "PROTOCOL" not in selected else
                               "http" if selected["PROTOCOL"] == "http" else "other"),
            "http_addr_matches_profile": "yes" if selected.get("HTTP_ADDR") == profile["gitea"]["listen_ip"] else "no",
            "http_port_matches_profile": "yes" if selected.get("HTTP_PORT") == str(profile["gitea"]["port"]) else "no"}


def ufw(text):
    if text == "Status: inactive":
        return {"active": "no", "default_deny_incoming": "no", "rule_count": 0}
    lines = text.splitlines()
    if not lines or lines[0] != "Status: active":
        raise Invalid("PROBE_UNAVAILABLE")
    default = None
    logging = profiles = header = separator = False
    count = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith("Logging:") and not logging and not header:
            if not re.fullmatch(r"Logging: (?:on \((?:low|medium|high|full)\)|off)", line):
                raise Invalid("PROBE_UNAVAILABLE")
            logging = True
        elif line.startswith("Default:") and default is None and not header:
            match = re.fullmatch(r"Default: (deny|allow|reject) \(incoming\), (?:deny|allow|reject) \(outgoing\), (?:deny|allow|reject|disabled) \(routed\)", line)
            if not match:
                raise Invalid("PROBE_UNAVAILABLE")
            default = match[1]
        elif line == "New profiles: skip" and not profiles and not header:
            profiles = True
        elif re.fullmatch(r"To\s+Action\s+From", line) and not header:
            header = True
        elif header and not separator and re.fullmatch(r"-+\s+-+\s+-+", line):
            separator = True
        elif separator and re.fullmatch(r"[^\r\n]+?\s{2,}(?:ALLOW|DENY|REJECT|LIMIT)(?: IN| OUT| FWD)?\s{2,}[^\r\n]+", line):
            count += 1
        else:
            raise Invalid("PROBE_UNAVAILABLE")
    if default is None or not logging or not profiles or header != separator or count > 10000:
        raise Invalid("PROBE_UNAVAILABLE")
    return {"active": "yes", "default_deny_incoming": "yes" if default == "deny" else "no", "rule_count": count}


def collect(binding, *, profile=None, invoke=run, config=server_binding, now=None):
    check_binding(binding)
    profile = validate_profile(profile) if profile is not None else load_profile()
    if (binding["host_sha256"] != host_digest() or binding["collector_sha256"] != script_digest()
            or binding["profile_sha256"] != profile_digest(profile)):
        raise Invalid("BINDING_MISMATCH")
    if sys.platform != "linux":
        raise Invalid("TARGET_UNAVAILABLE")
    def command(argv, parse):
        try:
            rc, text = invoke(list(argv))
        except ProbeFailure:
            raise
        except (TimeoutError, subprocess.TimeoutExpired):
            raise ProbeFailure("timeout") from None
        except OSError:
            raise ProbeFailure("command-unavailable") from None
        except UnicodeError:
            raise ProbeFailure("decode-failed") from None
        if rc != 0:
            raise ProbeFailure("command-failed")
        if not isinstance(text, str):
            raise ProbeFailure("parse-failed")
        try:
            size = len(text.encode("utf-8"))
        except UnicodeError:
            raise ProbeFailure("decode-failed") from None
        if size > LIMIT:
            raise ProbeFailure("output-limit")
        try:
            return parse(text)
        except (Invalid, ValueError):
            raise ProbeFailure("parse-failed") from None

    def configuration():
        try:
            return config(profile)
        except UnicodeError:
            raise ProbeFailure("decode-failed") from None
        except OSError:
            raise ProbeFailure("config-unavailable") from None
        except Invalid as exc:
            raise ProbeFailure("config-unavailable" if str(exc) == "CONFIG_UNAVAILABLE"
                               else "parse-failed") from None

    observations = {}
    for key, probe in (("systemd", lambda: command(SYSTEMD_COMMAND, systemd)),
                       ("server_binding", configuration),
                       ("ufw", lambda: command(UFW_COMMAND, ufw))):
        try:
            observations[key] = observation(key, probe())
        except ProbeFailure as exc:
            observations[key] = observation(key, reason=exc.reason)
        except (Invalid, ValueError):
            observations[key] = observation(key, reason="parse-failed")
    return seal({"contract_version": CONTRACT, "collector_version": VERSION, **binding,
                 "collected_at": timestamp(now or utcnow()), "observations": observations}, now)


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
        parser.add_argument("command", choices=("schema", "identity", "collect", "verify"))
        for name in binding_schema():
            parser.add_argument("--" + name.replace("_", "-"))
        args = vars(parser.parse_args(argv))
        command = args.pop("command")
        if command in {"identity", "collect"} and not (
                sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise Invalid("UNSAFE_INTERPRETER")
        if command in {"identity", "schema"}:
            if any(value is not None for value in args.values()):
                raise Invalid("ARGUMENT_INVALID")
            if command == "schema":
                result = schema()
            else:
                profile = load_profile()
                result = {"host_sha256": host_digest(), "collector_sha256": script_digest(),
                          "profile_sha256": profile_digest(profile)}
        else:
            check_binding(args)
            result = collect(args) if command == "collect" else verify(
                decode(sys.stdin.buffer.read(LIMIT + 1)), args)
        emit(result, pretty=command == "schema")
        return 20 if result.get("receipt", result).get("status") == "BLOCKED_EXTERNAL" else 0
    except (Invalid, OSError, UnicodeError, RecursionError) as exc:
        emit({"status": "BLOCKED_EXTERNAL", "code": str(exc) if isinstance(exc, Invalid) else "INPUT_UNAVAILABLE"})
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
