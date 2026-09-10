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

import aisoft_company_baseline_diagnostics_v2 as d
from codex.runtime.tests.test_company_baseline_v2 import profile, NOW, ROOT

SCRIPT = ROOT / "codex/runtime/aisoft_company_baseline_diagnostics_v2.py"
SENTINEL = "SECRET_SENTINEL_280"
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
                         config=config or (lambda _: {key: "http" if key == "protocol_state" else "yes" for key in d.VALUES["server_binding"]["properties"]}), now=NOW)


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
                self.assertEqual(result["diagnostic"]["observations"][key], d.observation(key, reason=("command-failed" if output[0] else
                    "output-limit" if len(output[1]) > d.LIMIT else "parse-failed")))
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
                self.assertEqual(d.observation("server_binding", d.server_binding(profile()))["status"], "PASS")
                for replacement in ("https", "%(SECRET)s", SENTINEL):
                    path.write_text(raw.replace("PROTOCOL=http", "PROTOCOL=" + replacement))
                    result = d.server_binding(profile())
                    self.assertEqual(result["protocol_state"], "other")
                    self.assertNotIn(SENTINEL, json.dumps(result))
                path.write_text("[database]\nPASSWD=" + SENTINEL)
                self.assertEqual(d.server_binding(profile())["protocol_state"], "missing")
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
                    with self.assertRaises(d.ProbeFailure):
                        d.run(d.UFW_COMMAND)
                else:
                    self.assertEqual(d.run(d.UFW_COMMAND), (0, expected))

    def test_cli_schema_identity_and_errors_do_not_leak(self):
        self.assertEqual(d.schema(), json.loads((ROOT / "company-delivery/baseline/diagnostics-v2.schema.json").read_text()))
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

    def test_subprocess_timeout_kills_child_and_drops_stderr(self):
        from unittest.mock import MagicMock
        process = MagicMock()
        process.poll.return_value = None
        process.stdout.fileno.return_value = 17
        popen = MagicMock()
        popen = process
        process.__enter__.return_value = process
        selector = MagicMock()
        selector.__enter__.return_value = selector
        selector.select.return_value = []
        with patch.object(d.subprocess, "Popen", return_value=popen) as factory, \
                patch.object(d.selectors, "DefaultSelector", return_value=selector), \
                patch.object(d.time, "monotonic", return_value=100):
            with self.assertRaises(d.ProbeFailure) as raised:
                d.run(d.UFW_COMMAND)
            self.assertEqual(raised.exception.reason, "timeout")
        selector.select.assert_called_once_with(4)
        process.kill.assert_called_once()
        process.wait.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["stderr"], subprocess.DEVNULL)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "platform"
        self.repo.mkdir()
        self.builder_path = ROOT / "company-delivery/baseline/prepare-diagnostics-v2-bundle.py"
        spec = importlib.util.spec_from_file_location("bundle280", self.builder_path)
        self.b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.b)
        for path in (*self.b.SOURCE_FILES.values(), self.b.BUILDER):
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", self.b.EXPECTED_REMOTE)
        self.commit()
        self.selected = self.root / "baseline-profile.json"
        self.selected.write_bytes(d.profile_bytes(profile()))
        self.selected.chmod(0o600)
        self.pin = d.profile_digest(profile())
        self.output = self.root / "bundle"

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True).stdout.decode().strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.source = self.git("rev-parse", "HEAD")

    def files(self):
        return self.b.materialize(self.repo, self.source, self.selected, self.pin)

    def test_exact_commit_not_dirty_files_and_modes_hash_readback(self):
        files = self.files()
        (self.repo / self.b.COLLECTOR).write_text(SENTINEL)
        (self.repo / "company-delivery/baseline/DIAGNOSTICS-V2.md").write_text(SENTINEL)
        self.assertEqual(files, self.files())
        self.assertEqual(self.b.build(self.output, files)["status"], "PASS")
        manifest = json.loads((self.output / "manifest.json").read_bytes())
        self.assertEqual(manifest["source_sha"], self.source)
        self.assertEqual(manifest["profile_sha256"], self.pin)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        for name, entry in manifest["files"].items():
            self.assertEqual((self.output / name).stat().st_mode & 0o777, 0o600)
            self.assertEqual(entry["sha256"], self.b.sha256((self.output / name).read_bytes()))
        self.assertNotIn(SENTINEL, json.dumps(manifest))
        self.assertEqual(self.b.verify_bundle(self.output, files)["files"], 6)
        second = self.root / "bundle-second"
        self.b.build(second, self.files())
        self.assertEqual({p.name: p.read_bytes() for p in second.iterdir()}, files)
        with self.assertRaises(FileExistsError):
            self.b.build(self.output, files)

    def test_source_commit_repository_object_and_schema_drift(self):
        for source in ("HEAD", "a" * 40):
            with self.assertRaises(self.b.Invalid):
                self.b.materialize(self.repo, source, self.selected, self.pin)
        self.git("remote", "set-url", "origin", "https://example.invalid/wrong.git")
        with self.assertRaisesRegex(self.b.Invalid, "REPOSITORY_MISMATCH"):
            self.files()
        self.git("remote", "set-url", "origin", self.b.EXPECTED_REMOTE)
        original = self.b.git
        def corrupt(repo, *args):
            return b"tamper" if args[0] == "cat-file" else original(repo, *args)
        with patch.object(self.b, "git", side_effect=corrupt), self.assertRaisesRegex(self.b.Invalid, "OBJECT_HASH_MISMATCH"):
            self.files()
        schema = self.repo / "company-delivery/baseline/diagnostics-v2.schema.json"
        schema.write_text("{}")
        self.commit()
        with self.assertRaisesRegex(self.b.Invalid, "SCHEMA_SOURCE_DRIFT"):
            self.files()
        (self.repo / self.b.COLLECTOR).write_text(SENTINEL)
        self.commit()
        with self.assertRaisesRegex(self.b.Invalid, "COLLECTOR_SOURCE_DRIFT"):
            self.files()

    def test_profile_noncanonical_unsafe_and_digest_drift(self):
        with self.assertRaisesRegex(self.b.Invalid, "PROFILE_DIGEST_MISMATCH"):
            self.b.materialize(self.repo, self.source, self.selected, "0" * 64)
        self.selected.write_text(json.dumps(profile(), indent=2))
        with self.assertRaises(ValueError):
            self.files()
        self.selected.write_bytes(d.profile_bytes(profile()))
        self.selected.chmod(0o666)
        with self.assertRaises(ValueError):
            self.files()

    def test_builder_source_and_directory_mode_drift(self):
        files = self.files()
        self.b.build(self.output, files)
        self.output.chmod(0o755)
        with self.assertRaisesRegex(self.b.Invalid, "DIRECTORY_UNSAFE"):
            self.b.verify_bundle(self.output, files)
        (self.repo / self.b.BUILDER).write_text(SENTINEL)
        self.commit()
        with self.assertRaisesRegex(self.b.Invalid, "BUILDER_SOURCE_DRIFT"):
            self.files()

    def test_verify_rejects_file_set_content_manifest_modes_and_symlinks(self):
        files = self.files()
        self.b.build(self.output, files)
        for name in files:
            target = self.output / name
            target.write_bytes(b"tampered")
            with self.assertRaises(self.b.Invalid):
                self.b.verify_bundle(self.output, files)
            target.write_bytes(files[name])
        target = self.output / "manifest.json"
        target.chmod(0o644)
        with self.assertRaises(self.b.Invalid):
            self.b.verify_bundle(self.output, files)
        target.chmod(0o600)
        extra = self.output / "extra"
        extra.touch()
        with self.assertRaises(self.b.Invalid):
            self.b.verify_bundle(self.output, files)
        extra.unlink()
        target.unlink()
        target.symlink_to(self.selected)
        with self.assertRaises(OSError):
            self.b.verify_bundle(self.output, files)
        alias = self.root / "alias"
        alias.symlink_to(self.output)
        with self.assertRaises(self.b.Invalid):
            self.b.verify_bundle(alias, files)

    def test_builder_cli_rejects_without_echoing_input(self):
        common = ["--repo", str(self.repo), "--source-sha", self.source, "--profile", str(self.selected),
                  "--profile-sha256", self.pin, "--output", str(self.output)]
        def cli(command, args):
            return subprocess.run([sys.executable, "-I", "-S", "-B", str(self.builder_path), command, *args], capture_output=True)
        result = cli("build", common)
        self.assertEqual(result.returncode, 0, result.stdout)
        result = cli("verify", common)
        self.assertEqual(result.returncode, 0, result.stdout)
        result = cli("build", common)
        self.assertEqual(json.loads(result.stdout)["code"], "OUTPUT_EXISTS")
        result = cli("build", ["--secret", SENTINEL])
        self.assertEqual(result.returncode, 20)
        self.assertEqual(result.stderr, b"")
        self.assertNotIn(SENTINEL.encode(), result.stdout)


class ReasonTests(unittest.TestCase):
    def test_duplicate_protocol_is_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "synthetic.ini")
            path.write_text("[server]\nPROTOCOL=http\nPROTOCOL=https\n")
            path.chmod(0o600)
            with patch.object(d, "CONFIG_PATH", str(path)):
                result = collect(config=d.server_binding)
            self.assertEqual(result["diagnostic"]["observations"]["server_binding"],
                             d.observation("server_binding", reason="parse-failed"))

    def test_protocol_presence_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "synthetic.ini")
            for text, expected in (("", "missing"), (";PROTOCOL=http", "missing"),
                                   ("PROTOCOL=http", "http"), ("PROTOCOL=https", "other"),
                                   ("PROTOCOL=", "other"), ("PROTOCOL=" + SENTINEL, "other")):
                path.write_text("[server]\n" + text + "\nHTTP_ADDR=10.23.45.67\nHTTP_PORT=8888\n")
                path.chmod(0o600)
                with patch.object(d, "CONFIG_PATH", str(path)):
                    observed = d.server_binding(profile())
                self.assertEqual(observed["protocol_state"], expected)
                self.assertNotIn(SENTINEL, json.dumps(observed))

    def test_command_reason_table_and_secret_redaction(self):
        cases = [(FileNotFoundError(SENTINEL), "command-unavailable"),
                 (PermissionError(SENTINEL), "command-unavailable"),
                 (subprocess.TimeoutExpired(SENTINEL, 4), "timeout"),
                 ((1, SENTINEL), "command-failed"), ((0, ""), "parse-failed"),
                 ((0, UFW + "\n" + SENTINEL), "parse-failed"),
                 ((0, UFW.replace("New profiles: skip\n", "")), "parse-failed"),
                 ((0, "x" * (d.LIMIT + 1)), "output-limit")]
        for output, reason in cases:
            def invoke(argv):
                if argv == d.SYSTEMD_COMMAND:
                    return 0, SYSTEMD
                if isinstance(output, Exception):
                    raise output
                return output
            result = collect(invoke=invoke)
            self.assertEqual(result["diagnostic"]["observations"]["ufw"],
                             d.observation("ufw", reason=reason))
            self.assertEqual(d.verify(result, binding(), NOW)["status"], "BLOCKED_EXTERNAL")
            self.assertNotIn(SENTINEL, json.dumps(result))

    def test_config_errors_classified_without_values(self):
        errors = [(PermissionError(SENTINEL), "config-unavailable"),
                  (d.Invalid("CONFIG_UNAVAILABLE"), "config-unavailable"),
                  (d.Invalid("CONFIG_INVALID"), "parse-failed"),
                  (UnicodeDecodeError("utf8", b"\xff", 0, 1, SENTINEL), "decode-failed")]
        for exc, reason in errors:
            def config(_):
                raise exc
            result = collect(config=config)
            self.assertEqual(result["diagnostic"]["observations"]["server_binding"]["reason"], reason)
            self.assertNotIn(SENTINEL, json.dumps(result))

    def test_reason_value_status_forgery_and_versions(self):
        import aisoft_company_baseline_diagnostics_v1 as old
        result = collect()
        for reason, value in (("observed", None), ("timeout", {"x": 1}), ("unknown", None)):
            with self.assertRaises(d.Invalid):
                d.observation("ufw", value, reason)
        for reason, value in (("timeout", result["diagnostic"]["observations"]["ufw"]["value"]),
                              ("observed", None)):
            changed = copy.deepcopy(result["diagnostic"])
            changed["observations"]["ufw"].update(reason=reason, value=value)
            with self.assertRaises(d.Invalid):
                d.seal(changed, NOW)
        with self.assertRaises(old.Invalid):
            old.verify(result, binding(), NOW)
        changed = copy.deepcopy(result)
        changed["diagnostic"]["contract_version"] = old.CONTRACT
        with self.assertRaises(d.Invalid):
            d.verify(changed, binding(), NOW)

    def test_run_control_flow_with_mocked_io(self):
        from unittest.mock import MagicMock
        scenarios = [([b"ok", b""], 0, None, None),
                     ([b"x" * (d.LIMIT + 1)], 0, None, "output-limit"),
                     ([b"\xff", b""], 0, None, "decode-failed"),
                     ([b"",], 1, None, "command-failed"),
                     ([b"",], 0, subprocess.TimeoutExpired("fixture", 4), "timeout")]
        for chunks, rc, wait_error, reason in scenarios:
            process = MagicMock()
            process.__enter__.return_value = process
            process.stdout.fileno.return_value = 17
            process.poll.return_value = 0
            process.wait.return_value = rc
            if wait_error:
                process.wait.side_effect = wait_error
            selector = MagicMock()
            selector.__enter__.return_value = selector
            selector.select.return_value = [True]
            with patch.object(d.subprocess, "Popen", return_value=process) as factory, \
                 patch.object(d.selectors, "DefaultSelector", return_value=selector), \
                 patch.object(d.os, "read", side_effect=chunks), \
                 patch.object(d.time, "monotonic", return_value=100):
                if reason:
                    with self.assertRaises(d.ProbeFailure) as raised:
                        d.run(d.UFW_COMMAND)
                    self.assertEqual(raised.exception.reason, reason)
                else:
                    self.assertEqual(d.run(d.UFW_COMMAND), (0, "ok"))
            self.assertEqual(factory.call_args.kwargs["stderr"], subprocess.DEVNULL)
            self.assertNotIn("shell", factory.call_args.kwargs)
        for error in (FileNotFoundError(SENTINEL), PermissionError(SENTINEL)):
            with patch.object(d.subprocess, "Popen", side_effect=error), self.assertRaises(d.ProbeFailure) as raised:
                d.run(d.UFW_COMMAND)
            self.assertEqual(raised.exception.reason, "command-unavailable")

    def test_v1_bytes_remain_exact(self):
        import hashlib
        pinned = {
            "codex/runtime/aisoft_company_baseline_diagnostics_v1.py":
                "732c4a871c6ecdb77285f3fcc7d31e20b27cf353ab75b4f368ee3aeedf41a3ac",
            "company-delivery/baseline/diagnostics-v1.schema.json":
                "20cb1a0ab51fb4bb69c66a61ac64556a585b53f7770b537fa68d29de9b142f68",
            "company-delivery/baseline/prepare-diagnostics-bundle.py":
                "630cd66ad941012ad7d1ac4391ea61e2d4c547ed4383bb7af6ee2dc19fe53ee8",
            "company-delivery/baseline/DIAGNOSTICS.md":
                "55b5fabe1b82a87e273c36945e78acef03ffe5dd22b5224d51c70c4bdf69f9ff",
        }
        for path, pin in pinned.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), pin)

if __name__ == "__main__":
    unittest.main()
