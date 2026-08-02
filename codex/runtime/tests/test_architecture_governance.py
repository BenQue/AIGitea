from pathlib import Path
import unittest

from aisoft_architecture.jsonio import load_json


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"


class ArchitectureGovernanceTests(unittest.TestCase):
    def test_inventory_is_deduplicated_and_explicit_about_gaps(self) -> None:
        inventory = load_json(ARCH / "evidence/inventory.json")
        project_ids = [item["project_id"] for item in inventory["projects"]]
        asset_ids = [item["asset_id"] for item in inventory["servers"]]
        self.assertEqual(len(project_ids), len(set(project_ids)))
        self.assertEqual(len(asset_ids), len(set(asset_ids)))
        for project in inventory["projects"]:
            for field in ("owner", "purpose", "source", "confidence", "collection_status"):
                self.assertTrue(project[field])
        for server in inventory["servers"]:
            for field in ("owner", "purpose", "source", "collected_at", "collection_status", "confidence"):
                self.assertTrue(server[field])
            self.assertIn("no", server["collection_status"].lower())

    def test_newemaint_evidence_is_dry_run_only(self) -> None:
        inventory = load_json(ARCH / "reference/newemaint/inventory.json")
        self.assertEqual(inventory["authority"]["commit"], "ecbdc674fde1f785cafdee92c6ee88c691104a34")
        self.assertEqual(inventory["repository_status_after_collection"], "clean")
        report = (ARCH / "reference/newemaint/gap-report.md").read_text(encoding="utf-8")
        self.assertIn("NOT MIGRATED, NOT DEPLOYED", report)
        self.assertIn("must not be merged", report)

    def test_governance_docs_keep_candidate_and_delivery_boundaries(self) -> None:
        required = {
            ROOT / "README.md": "Architecture declaration/lock",
            ROOT / "07-内网与生产平移路线.md": "Architecture catalog 采用门",
            ROOT / "09-v3平台简化与Loop-Engineering文档改造规划.md": "Architecture catalog 与 Loop 的边界",
            ROOT / "12-Linux-GitHub-Gitea-双服务器自动部署方案.md": "Architecture lock input",
            ROOT / "skill-for-codex/references/onboarding-runbook.md": "Architecture declaration onboarding",
        }
        for path, marker in required.items():
            with self.subTest(path=path.name):
                self.assertIn(marker, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
