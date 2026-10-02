"""Public-reader and bounded-writer regressions for the #289 contract."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from aisoft_loop import contract
from aisoft_loop.change_audit import audit_change_documents
from aisoft_loop.documents import publish_plan, publish_spec


RUNTIME = Path(__file__).parents[1]
HISTORICAL_SUMMARY = Path(__file__).parent / "fixtures/required-documents/sfm-142-summary.txt"


class RequiredDocumentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.directory = self.repo / "docs/changes/57-docs-source"
        self.directory.mkdir(parents=True)
        self.summary = self.directory / "summary-docs-source-260808.md"
        self.summary.write_text("""---
issue: 57
gitea_url: http://gitea.test/owner/repo/issues/57
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: platform contract repair
risk_flags:
  - shared-core
required_docs:
  - summary
documents:
  summary: summary-docs-source-260808.md
confidence: high
override_reason: ''
status: approved
branch: change/57-docs-source
pr_url:
created: 2026-08-08
---
""")

    def declare(self, role, *, required=True, present=True):
        text = self.summary.read_text()
        if required:
            text = text.replace("documents:\n", f"  - {role}\ndocuments:\n")
        text = text.replace("confidence: high", f"  {role}: {role}-docs-source-260808.md\nconfidence: high")
        self.summary.write_text(text)
        path = self.directory / f"{role}-docs-source-260808.md"
        if present:
            path.write_text(self.document(role))
        return path

    def document(self, role):
        return ("---\nissue: 57\nbranch: change/57-docs-source\n"
                "effective_complexity: complex\ncreated: 2026-08-08\n---\n"
                f"# {role}\n\n## Acceptance criteria\n- [ ] AC-1 Observable.\n"
                "## 未决问题\n无。\n\n"
                "| Ticket | Blocked by | Status |\n|---|---|---|\n| T01 | - | pending |\n"
                "| AC | Command |\n|---|---|\n| AC-1 | review |\n")

    def issue(self):
        return {"number": 57, "state": "open", "title": "fixture", "body":
                "## Acceptance criteria\n- [ ] AC-1 Observable.\n",
                "labels": ["type/platform", "complexity/complex", "approved"]}

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "aisoft_loop.cli", *args, "--repo", str(self.repo)],
            capture_output=True, text=True,
            env=dict(os.environ, PYTHONPATH=str(RUNTIME), PYTHONDONTWRITEBYTECODE="1"),
        )

    def test_real_sfm_missing_verification_is_rejected_by_all_readers(self):
        self.summary.unlink()
        self.directory.rmdir()
        directory = self.repo / "docs/changes/142-architecture-lock-declaration"
        directory.mkdir()
        (directory / "summary-architecture-lock-declaration-260910.md").write_bytes(
            HISTORICAL_SUMMARY.read_bytes()
        )
        for command, arguments in [("resolve-documents", ["142"]),
                                   ("resolve-required-documents", ["142"]),
                                   ("check-change-documents", [])]:
            with self.subTest(command=command):
                result = self.cli(command, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("142-architecture-lock-declaration", result.stdout + result.stderr)
                self.assertIn("verification-architecture-lock-declaration-260910.md", result.stdout + result.stderr)

    def test_an_optional_explicit_mapping_still_requires_its_file(self):
        self.declare("verification", required=False, present=False)
        with self.assertRaisesRegex(contract.ContractError, "documents.verification.*verification-docs-source"):
            contract.resolve_documents(self.repo, 57)
        self.assertFalse(audit_change_documents(self.repo).ok)

    def test_required_role_requires_a_mapping(self):
        self.summary.write_text(self.summary.read_text().replace("documents:\n", "  - verification\ndocuments:\n"))
        with self.assertRaisesRegex(contract.ContractError, "missing required roles.*verification"):
            contract.resolve_documents(self.repo, 57)

    def test_invalid_required_declarations_fail_closed(self):
        for raw in ["[]", "verification", "\n  - summary\n  - unknown", "\n  - summary\n  - summary",
                    "\n  - summary\n  - 03-verification.md"]:
            with self.subTest(raw=raw):
                old = self.summary.read_text()
                self.summary.write_text(old.replace("required_docs:\n  - summary", "required_docs: " + raw))
                with self.assertRaises(contract.ContractError):
                    contract.resolve_documents(self.repo, 57)
                self.summary.write_text(old)

    def test_undeclared_minimum_is_rejected_in_production(self):
        with self.assertRaisesRegex(contract.ContractError, "route minimum.*spec.*plan"):
            contract.load_contract(self.repo, self.issue())
        self.assertEqual(contract.load_contract(self.repo, self.issue(), change_control="development").required_docs,
                         (self.summary.name,))

    def test_development_keeps_declared_roles_and_terminal_json(self):
        # verification deliberately isn't last: it must not disappear from the route.
        self.declare("verification")
        self.declare("spec")
        classification = contract._classification_from_front_matter(
            contract.parse_front_matter(self.summary.read_text())
        )
        self.assertIn("verification", classification.route(change_control="development").required_docs)
        loaded = contract.load_contract(self.repo, self.issue(), change_control="development")
        self.assertEqual(set(loaded.required_docs), {self.summary.name, "spec-docs-source-260808.md", "verification-docs-source-260808.md"})
        result = self.cli("resolve-required-documents", "57")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["required_docs"], ["summary", "verification", "spec"])

    def test_small_route_also_preserves_declared_verification(self):
        self.declare("verification")
        text = self.summary.read_text().replace("platform", "bugfix").replace("complex", "small")
        text = text.replace("risk_flags:\n  - shared-core", "risk_flags: []")
        self.summary.write_text(text)
        classification = contract._classification_from_front_matter(contract.parse_front_matter(text))
        self.assertEqual(classification.route().required_docs, ("summary", "verification"))
        issue = self.issue()
        issue["labels"] = ["type/bugfix", "complexity/small", "approved"]
        self.assertIn("verification-docs-source-260808.md", contract.load_contract(self.repo, issue).required_docs)

    def test_missing_required_docs_is_not_inferred(self):
        self.summary.write_text(self.summary.read_text().replace("required_docs:\n  - summary\n", ""))
        with self.assertRaisesRegex(contract.ContractError, "required_docs"):
            contract.resolve_documents(self.repo, 57)

    def test_symlink_cannot_stand_in_for_a_declared_document(self):
        path = self.declare("verification", present=False)
        other = self.repo / "outside.md"
        other.write_text(self.document("verification"))
        path.symlink_to(other)
        with self.assertRaisesRegex(contract.ContractError, "symlink"):
            contract.resolve_documents(self.repo, 57)

    def test_dangling_symlink_is_rejected_even_by_writer_declarations(self):
        path = self.declare("spec", present=False)
        path.symlink_to(self.repo / "missing.md")
        self.git("init", "-q", "-b", "change/57-docs-source")
        with self.assertRaisesRegex(contract.ContractError, "symlink"):
            publish_spec(self.repo, self.issue(), self.document("spec"))

    def test_publish_first_spec_then_plan_keeps_strict_reader_red_until_complete(self):
        self.declare("spec", present=False)
        self.declare("plan", present=False)
        self.git("init", "-q", "-b", "change/57-docs-source")
        with self.assertRaises(contract.ContractError):
            contract.resolve_documents(self.repo, 57)
        publish_spec(self.repo, self.issue(), self.document("spec"))
        with self.assertRaises(contract.ContractError):
            contract.resolve_documents(self.repo, 57)
        publish_plan(self.repo, self.issue(), self.document("plan"))
        self.assertTrue(audit_change_documents(self.repo).ok)

    def test_public_reader_does_not_offer_a_skip_existence_option(self):
        self.assertNotEqual(self.cli("resolve-documents", "57", "--skip-existence").returncode, 0)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def test_legacy_required_verification_normalizes_but_unrequired_optional_files_may_be_missing(self):
        self.summary.unlink()
        self.directory.rmdir()
        directory = self.repo / "docs/changes/12"
        directory.mkdir()
        summary = directory / "00-summary.md"
        summary.write_text("---\nissue: 12\nrequired_docs:\n  - 00-summary.md\n---\n")
        self.git("init", "-q")
        self.git("add", "docs")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "history")
        result = self.cli("resolve-required-documents", "12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["required_docs"], ["summary"])
        summary.write_text(summary.read_text().replace("  - 00-summary.md", "  - 00-summary.md\n  - 03-verification.md"))
        self.assertNotEqual(self.cli("resolve-required-documents", "12").returncode, 0)
        (directory / "03-verification.md").write_text("---\nissue: 12\n---\n")
        result = self.cli("resolve-required-documents", "12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["required_docs"], ["summary", "verification"])
