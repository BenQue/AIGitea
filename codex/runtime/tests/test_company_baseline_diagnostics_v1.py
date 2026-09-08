"""All company observations are fixtures; no company host is contacted."""
import ast
import copy
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import aisoft_company_baseline_diagnostics_v1 as d
from codex.runtime.tests.test_company_baseline_v2 import profile, NOW, ROOT

SCRIPT = ROOT / "codex/runtime/aisoft_company_baseline_diagnostics_v1.py"
SENTINEL = "SECRET_SENTINEL_278"
SYSTEMD = "LoadState=loaded\nActiveState=active\nSubState=running\nResult=success\nMainPID=314159\nExecMainStatus=0"
UFW = ("Status: active\nLogging: on (low)\nDefault: deny (incoming), allow (outgoing), disabled (routed)\n"
       "New profiles: skip\n\nTo                         Action      From\n"
       "--                         ------      ----\n8888/tcp                   ALLOW IN    10.23.45.0/24\n"
       "8888/tcp (v6)              DENY IN     Anywhere (v6)")


def binding():
    return {"environment": "company-scm-ci", "host_role": "scm-ci", "source_sha": "1" * 40,
            "host_sha256": d.host_digest(), "collector_sha256": d.script_digest(),
            "profile_sha256": d.profile_digest(profile()),
            "evidence_id": "12345678-1234-4567-8123-123456789012",
            "baseline_evidence_id": "12345678-1234-4567-8123-123456789013"}


def collect(invoke=None, config=None, pins=None):
    def fake(argv):
        if argv == d.SYSTEMD_COMMAND:
            return 0, SYSTEMD
        if argv == d.UFW_COMMAND:
            return 0, UFW
        raise AssertionError(argv)
    with patch.object(d.sys, "platform", "linux"):
        return d.collect(pins or binding(), profile=profile(), invoke=invoke or fake,
                         config=config or (lambda _: {key: "yes" for key in d.VALUES["server_binding"]["properties"]}), now=NOW)


class DiagnosticsTests(unittest.TestCase):
    def test_success_is_independent_and_only_sanitized_metadata(self):
        result = collect()
        self.assertEqual(d.verify(result, binding(), NOW), {"validation": "PASS", "status": "PASS", "mutation_authorized": False})
        text = json.dumps(result)
        for forbidden in ("314159", "10.23.45", "8888", "[server]", "ExecStart", SENTINEL):
            self.assertNotIn(forbidden, text)
        self.assertEqual(result["diagnostic"]["observations"]["ufw"]["value"]["rule_count"], 2)
        self.assertEqual(collect(), collect())

    def test_binding_pins_fail_before_probe_and_verifier_checks_all(self):
        for key, value in (("host_sha256", "a" * 64), ("collector_sha256", "b" * 64),
                           ("profile_sha256", "c" * 64), ("environment", "elsewhere"), ("host_role", "appserver-prod")):
            pins = binding()
            pins[key] = value
            with self.subTest(key=key), self.assertRaises(d.Invalid):
                collect(pins=pins, invoke=lambda _: self.fail("probe before pin check"))
        result = collect()
        for key in d.binding_schema():
            pins = binding()
            pins[key] = "0" * len(pins[key])
            with self.subTest(key=key), self.assertRaises(d.Invalid):
                d.verify(result, pins, NOW)
        pins = binding()
        pins["baseline_evidence_id"] = pins["evidence_id"]
        with self.assertRaisesRegex(d.Invalid, "UUID_REUSED"):
            collect(pins=pins)

    def test_receipt_checksum_status_and_freshness_fail_closed(self):
        result = collect()
        for path, value in ((("receipt", "mutation_authorized"), True),
                            (("receipt", "status"), "GAP"), (("diagnostic_sha256",), "0" * 64),
                            (("diagnostic", "raw"), SENTINEL)):
            changed = copy.deepcopy(result)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.assertRaises(d.Invalid):
                d.verify(changed, binding(), NOW)
        for now in (NOW - timedelta(seconds=1), NOW + timedelta(days=2)):
            with self.assertRaises(d.Invalid):
                d.verify(result, binding(), now)
        changed = copy.deepcopy(result["diagnostic"])
        changed["observations"]["ufw"]["status"] = "BLOCKED"
        with self.assertRaises(d.Invalid):
            d.seal(changed, NOW)

    def test_missing_permissions_errors_and_oversize_do_not_fabricate_facts(self):
        cases = [(1, ""), (0, ""), (9, UFW), (0, SENTINEL), (0, "x" * (d.LIMIT + 1))]
        for output in cases:
            result = collect(invoke=lambda _: output)
            for key in ("systemd", "ufw"):
                self.assertEqual(result["diagnostic"]["observations"][key], d.observation(key))
            self.assertNotIn(SENTINEL, json.dumps(result))
        for error in (PermissionError, FileNotFoundError, ConnectionRefusedError, TimeoutError):
            def fail(*_):
                raise error(SENTINEL)
            result = collect(invoke=fail, config=fail)
            self.assertEqual(result["receipt"]["status"], "BLOCKED_EXTERNAL")
            self.assertNotIn(SENTINEL, json.dumps(result))

    def test_systemd_exact_properties_enums_and_numbers(self):
        self.assertEqual(d.systemd(SYSTEMD)["main_pid_present"], "yes")
        self.assertEqual(d.systemd(SYSTEMD.replace("314159", "0"))["main_pid_present"], "no")
        for text in (SYSTEMD + "\nExecStart=" + SENTINEL, SYSTEMD + "\nMainPID=1",
                     SYSTEMD.replace("LoadState=loaded\n", ""), SYSTEMD.replace("running", SENTINEL),
                     SYSTEMD.replace("314159", "4294967296"), SYSTEMD.replace("ExecMainStatus=0", "ExecMainStatus=256"),
                     SYSTEMD.replace("314159", "-1")):
            with self.assertRaises(d.Invalid):
                d.systemd(text)
        value = d.systemd(SYSTEMD.replace("ActiveState=active", "ActiveState=failed"))
        self.assertEqual(d.observation("systemd", value)["status"], "GAP")

    def test_config_only_boolean_comparisons_and_no_interpolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "app.ini")
            raw = ("[database]\nPASSWD=" + SENTINEL + "\n[server]\nPROTOCOL=http\nHTTP_ADDR=10.23.45.67\nHTTP_PORT=8888\n"
                   "SECRET=" + SENTINEL + "\n[security]\nINTERNAL_TOKEN=" + SENTINEL)
            path.write_text(raw)
            path.chmod(0o600)
            with patch.object(d, "CONFIG_PATH", str(path)):
                self.assertTrue(all(value == "yes" for value in d.server_binding(profile()).values()))
                for replacement in ("https", "%(SECRET)s", SENTINEL):
                    path.write_text(raw.replace("PROTOCOL=http", "PROTOCOL=" + replacement))
                    result = d.server_binding(profile())
                    self.assertEqual(result["protocol_http"], "no")
                    self.assertNotIn(SENTINEL, json.dumps(result))
                path.write_text("[database]\nPASSWD=" + SENTINEL)
                self.assertTrue(all(value == "no" for value in d.server_binding(profile()).values()))
                for text in (raw + "\n[server]", raw.replace("HTTP_PORT=8888", "HTTP_PORT=8888\nHTTP_PORT=9999"),
                             raw.replace("HTTP_PORT=8888", "malformed"), "[server", "x" * (d.LIMIT + 1)):
                    path.write_text(text)
                    with self.assertRaises(d.Invalid):
                        d.server_binding(profile())
                path.write_bytes(b"\xff")
                with self.assertRaises(UnicodeError):
                    d.server_binding(profile())

    def test_config_unsafe_files_and_fixed_open_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "app.ini")
            real = Path(tmp, "real")
            real.write_text("[server]")
            path.symlink_to(real)
            with patch.object(d, "CONFIG_PATH", str(path)), self.assertRaises(OSError):
                d.server_binding(profile())
            path.unlink()
            path.write_text("[server]")
            path.chmod(0o666)
            with patch.object(d, "CONFIG_PATH", str(path)), self.assertRaises(d.Invalid):
                d.server_binding(profile())
            path.unlink()
            path.mkdir()
            with patch.object(d, "CONFIG_PATH", str(path)), self.assertRaises(d.Invalid):
                d.server_binding(profile())
            path.rmdir()
            os.mkfifo(path)
            with patch.object(d, "CONFIG_PATH", str(path)), self.assertRaises(d.Invalid):
                d.server_binding(profile())
        with patch.object(d.os, "open", side_effect=PermissionError) as opened:
            with self.assertRaises(PermissionError):
                d.server_binding(profile())
            self.assertEqual(opened.call_args.args[0], "/etc/aisoft/gitea/app.ini")

    def test_ufw_closed_normalization(self):
        self.assertEqual(d.ufw("Status: inactive"), {"active": "no", "default_deny_incoming": "no", "rule_count": 0})
        for raw in ("", "Status: active", "Status: inactive\n" + SENTINEL, UFW + "\n" + SENTINEL,
                    UFW.replace("Default: deny", "Default: strange"), UFW.replace("ALLOW IN", "UNKNOWN"),
                    UFW + "\nDefault: deny (incoming), allow (outgoing), disabled (routed)"):
            with self.assertRaises(d.Invalid):
                d.ufw(raw)
        self.assertEqual(d.ufw(UFW.replace("deny (incoming)", "allow (incoming)"))["default_deny_incoming"], "no")

    def test_no_host_mutation_or_http_or_environment_access_in_ast(self):
        tree = ast.parse(SCRIPT.read_text())
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertNotIn("http.client", imports)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        forbidden = {"system", "getenv", "walk", "listdir", "write_text", "write_bytes", "mkdir", "unlink", "connect", "urlopen"}
        for call in calls:
            if isinstance(call.func, ast.Attribute):
                self.assertNotIn(call.func.attr, forbidden)
        self.assertNotIn("os.environ", SCRIPT.read_text())
        self.assertEqual(d.COMMANDS, (["/usr/bin/systemctl", "show", "aisoft-gitea.service", "--property=LoadState,ActiveState,SubState,Result,MainPID,ExecMainStatus"], ["/usr/sbin/ufw", "status", "verbose"]))
        for argv in (["sudo", "ufw", "status"], ["/usr/bin/systemctl", "restart", "aisoft-gitea.service"]):
            with patch.object(d.subprocess, "Popen") as popen, self.assertRaises(d.Invalid):
                d.run(argv)
            popen.assert_not_called()

    def test_subprocess_guardrails_real_pipes_fake_executable(self):
        real_popen = subprocess.Popen
        for code, expected in (("import sys; print('ok'); print('" + SENTINEL + "',file=sys.stderr)", "ok"),
                               ("print('x'*65537)", None), ("import sys; sys.exit(1)", None)):
            def fake(argv, **kwargs):
                self.assertEqual(argv, d.UFW_COMMAND)
                self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
                self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
                self.assertEqual(kwargs["env"], {"LANG": "C", "LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
                self.assertNotIn("shell", kwargs)
                return real_popen([sys.executable, "-I", "-S", "-B", "-c", code], **kwargs)
            with patch.object(d.subprocess, "Popen", side_effect=fake):
                if expected is None:
                    with self.assertRaises(d.Invalid):
                        d.run(d.UFW_COMMAND)
                else:
                    self.assertEqual(d.run(d.UFW_COMMAND), (0, expected))

    def test_cli_schema_identity_and_errors_do_not_leak(self):
        self.assertEqual(d.schema(), json.loads((ROOT / "company-delivery/baseline/diagnostics-v1.schema.json").read_text()))
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, SCRIPT.name)
            shutil.copyfile(SCRIPT, script)
            selected = Path(tmp, d.PROFILE_FILENAME)
            selected.write_bytes(d.profile_bytes(profile()))
            selected.chmod(0o600)
            result = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), "identity"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(set(json.loads(result.stdout)), {"host_sha256", "collector_sha256", "profile_sha256"})
            for args, raw in ((["collect", "--secret", SENTINEL], b""), (["verify"], SENTINEL.encode())):
                result = subprocess.run([sys.executable, "-I", "-S", "-B", str(script), *args], input=raw, capture_output=True)
                self.assertEqual(result.returncode, 20)
                self.assertNotIn(SENTINEL.encode(), result.stdout + result.stderr)
                self.assertEqual(result.stderr, b"")
        args = [item for key, value in binding().items() for item in ("--" + key.replace("_", "-"), value)]
        # Fresh fixture for a real offline CLI verification.
        result = collect()
        result["diagnostic"]["collected_at"] = d.timestamp(d.utcnow())
        result = d.seal(result["diagnostic"])
        verified = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), "verify", *args], input=d.canonical(result), capture_output=True)
        self.assertEqual(verified.returncode, 0, verified.stdout)
        self.assertEqual(verified.stderr, b"")
        self.assertFalse(json.loads(verified.stdout)["mutation_authorized"])


if __name__ == "__main__":
    unittest.main()
