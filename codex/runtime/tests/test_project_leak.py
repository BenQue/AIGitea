"""#368/#396: the ADR 0001 D3 project-name and site-value ratchet."""
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "codex/tests/check-project-leak.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_project_leak", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectLeakTests(unittest.TestCase):
    def setUp(self):
        self.checker = load_checker()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write("codex/config/gitea-governance.json", json.dumps({"repositories": [
            {"name": "platform-repo", "classification": "public-platform"},
            {"name": "AcmeApp", "classification": "internal-application"},
            {"name": "demo", "classification": "public-test"},
        ]}))
        self.write("codex/config/host-access-broker.json", json.dumps({
            "site": {
                "gitea_url": "http://forge.example.test:3000",
                "orbstack_machine": "forge",
                "orbstack_user": "opsuser",
                "credential_root_mac": "/Users/opsuser/creds",
            },
            "projects": [
                {"project_id": "acme-app", "repository": "AcmeApp"},
                {"project_id": "demo", "repository": "demo"},
            ],
        }))
        self.write("codex/config/project-leak-baseline.json",
                   json.dumps({"retired": ["oldproj"], "files": {"README.md": 1}}))
        self.write("docs/adr/0001-platform-boundary.md", self.adr("README.md"))
        self.write("README.md", "Uses AcmeApp.\n")
        self.write("codex/runtime/tests/test_x.py", "AcmeApp acme-app\n")
        self.write("docs/changes/1-x/summary.md", "AcmeApp\n")
        self.write("tool_test.go", "acme-vm\n")
        self.write("guide.md", "generic only\n")
        self.git("init", "-q")
        self.git("add", "-A")

    @staticmethod
    def adr(*paths):
        rows = "".join(f"| `{path}` | reason |\n" for path in paths)
        return f"### D3\n\n#### D3 登记的例外\n\n| 文件 | 理由 |\n|---|---|\n{rows}\n### D4\n\n| `later.md` | x |\n"

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def run_checker(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.checker.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_names_come_from_manifests_only(self):
        self.assertEqual(self.checker.project_names(self.root, ["oldproj"]),
                         ["acme-app", "acmeapp", "demo", "oldproj"])

    def test_site_values_come_from_the_site_segment_longest_first(self):
        self.assertEqual(self.checker.site_values(self.root),
                         ["forge.example.test:3000", "/users/opsuser/creds", "opsuser", "forge"])

    def test_baseline_matches_and_allowed_places_are_ignored(self):
        code, out, _ = self.run_checker()
        self.assertEqual(code, 0)
        self.assertIn("PASS: project-leak (1 baseline files, 1 hits; site 0 files, 0 hits)", out)

    def test_new_file_or_higher_count_fails_and_removal_recovers(self):
        self.write("templates/new.md", "oldproj\n")
        self.git("add", "-A")
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("templates/new.md: 1 project-name hits (baseline 0)", err)
        (self.root / "templates/new.md").unlink()
        self.git("add", "-A")
        self.write("README.md", "AcmeApp and acme-app\n")
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("README.md: 2 project-name hits (baseline 1)", err)
        self.write("README.md", "Uses AcmeApp.\n")
        self.assertEqual(self.run_checker()[0], 0)

    def test_public_test_name_and_site_value_each_fail_a_new_file(self):
        self.write("templates/demo.md", "see demo\n")
        self.write("templates/site.md", "http://forge.example.test:3000/x and /Users/opsuser/creds\n")
        self.git("add", "-A")
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("templates/demo.md: 1 project-name hits (baseline 0)", err)
        self.assertIn("templates/site.md: 2 site-value hits (baseline 0)", err)

    def test_real_manifests_catch_public_test_name_and_site_host(self):
        """#396 AC2 against the real manifests: a public-test repository and the Gitea host."""
        for path in ("codex/config/gitea-governance.json", "codex/config/host-access-broker.json"):
            self.write(path, (ROOT / path).read_text(encoding="utf-8"))
        self.write("README.md", "generic\n")
        self.write("templates/leak.md", "smoke-test\n")
        self.write("templates/host.md", "http://gitea-ci.orb.local:3000/\n")
        self.git("add", "-A")
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("templates/leak.md: 1 project-name hits (baseline 0)", err)
        self.assertIn("templates/host.md: 1 site-value hits (baseline 0)", err)
        for path in ("templates/leak.md", "templates/host.md"):
            (self.root / path).unlink()
        self.git("add", "-A")
        self.assertEqual(self.run_checker()[0], 0)

    def test_lower_count_only_notes_and_write_baseline_tightens(self):
        self.write("README.md", "generic\n")
        code, out, _ = self.run_checker()
        self.assertEqual(code, 0)
        self.assertIn("README.md has no project-name hits left", out)
        self.assertEqual(self.run_checker("--write-baseline")[0], 0)
        baseline = json.loads((self.root / "codex/config/project-leak-baseline.json").read_text())
        self.assertEqual(baseline, {"retired": ["oldproj"], "files": {}, "site_files": {}})

    def test_baseline_entry_must_be_registered_in_the_adr(self):
        """#416: the ratchet tolerates a baseline file only while the ADR registers it."""
        self.write("docs/adr/0001-platform-boundary.md", self.adr("other.md"))
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("README.md: baseline entry not registered", err)
        # A row after the next heading is outside the register.
        self.write("docs/adr/0001-platform-boundary.md", self.adr("other.md").replace("later.md", "README.md"))
        self.assertEqual(self.run_checker()[0], 1)
        # Anything that could hide or fake a row fails closed: a second table, a fence,
        # an HTML comment, an indented line, or the heading appearing twice.
        base = "### D3\n\n#### D3 登记的例外\n\n| 文件 | 理由 |\n|---|---|\n| `other.md` | x |\n"
        for tail in ("\nprose\n\n| `README.md` | x |\n",
                     "\n```\n| `README.md` | example |\n```\n",
                     "\n<!--\n| `README.md` | x |\n-->\n",
                     "\n    | `README.md` | x |\n",
                     "\n```\n#### D3 登记的例外\n```\n"):
            with self.subTest(tail=tail):
                self.write("docs/adr/0001-platform-boundary.md", base + tail)
                code, _, err = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("README.md: baseline entry not registered", err)
        # A fence, comment or raw HTML block anywhere in the ADR fails closed, even a
        # closed one before the heading, and even the variants a renderer reads differently
        # (a backtick info string that cannot open a fence, a closer followed by NBSP).
        for prefix in ("<!--\n", "~~~\n", "````\n", "<!-- note -->\n", "```\n<!--\n```\n",
                       "``` `\n<!--\n```\n", "```\n```\u00a0\n", "<pre>\n"):
            with self.subTest(prefix=prefix):
                self.write("docs/adr/0001-platform-boundary.md", prefix + self.adr("README.md"))
                code, _, err = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("no fences, HTML comments or raw HTML blocks allowed", err)
        commented = "#### D3 登记的例外\n\n<!--\n| 文件 | 理由 |\n|---|---|\n| `README.md` | x |\n-->\n"
        self.write("docs/adr/0001-platform-boundary.md", commented)
        self.assertEqual(self.run_checker()[0], 1)
        (self.root / "docs/adr/0001-platform-boundary.md").unlink()
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("exception register unreadable", err)
        self.write("docs/adr/0001-platform-boundary.md", self.adr("README.md"))
        self.assertEqual(self.run_checker()[0], 0)

    def test_new_manifest_project_needs_no_code_change(self):
        governance = json.loads((self.root / "codex/config/gitea-governance.json").read_text())
        governance["repositories"].append({"name": "NextApp", "classification": "internal-application"})
        self.write("codex/config/gitea-governance.json", json.dumps(governance))
        self.write("guide.md", "NextApp\n")
        code, _, err = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("guide.md: 1 project-name hits (baseline 0)", err)

    def test_checker_source_has_no_registered_project_literal(self):
        source = CHECKER.read_text(encoding="utf-8").lower()
        baseline = json.loads((ROOT / "codex/config/project-leak-baseline.json").read_text())
        for name in self.checker.project_names(ROOT, baseline["retired"]):
            with self.subTest(name=name):
                self.assertNotIn(name, source)
        for value in self.checker.site_values(ROOT):
            with self.subTest(value=value):
                self.assertNotIn(value, source)

    def test_repository_matches_its_baseline(self):
        self.assertEqual(self.checker.main(["--root", str(ROOT)]), 0)


if __name__ == "__main__":
    unittest.main()
