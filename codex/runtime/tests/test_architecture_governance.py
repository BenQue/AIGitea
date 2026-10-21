from pathlib import Path
import re
import unittest

from aisoft_architecture.jsonio import load_json


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"


class ArchitectureGovernanceTests(unittest.TestCase):
    def test_inventory_is_deduplicated_complete_and_explicit_about_gaps(self) -> None:
        inventory = load_json(ARCH / "evidence/inventory.json")
        project_ids = [item["project_id"] for item in inventory["projects"]]
        asset_ids = [item["asset_id"] for item in inventory["servers"]]
        lifecycle_components = [item["component"] for item in inventory["lifecycle_findings"]]
        self.assertEqual(len(project_ids), len(set(project_ids)))
        self.assertEqual(len(asset_ids), len(set(asset_ids)))
        self.assertEqual(len(lifecycle_components), len(set(lifecycle_components)))
        self.assertEqual(set(asset_ids), {"gitea-ci", "prod-sim"})
        for project in inventory["projects"]:
            for field in ("owner", "purpose", "source", "confidence", "collection_status"):
                self.assertTrue(project[field])
        for server in inventory["servers"]:
            for field in ("owner", "purpose", "source", "collected_at", "collection_status", "confidence"):
                self.assertTrue(server[field])
            self.assertTrue(server["collection_status"].startswith("complete:"))
            self.assertEqual(server["execution_path"], "host-orb-read-only")
            self.assertEqual(server["os"]["version"], "26.04 LTS")
            self.assertEqual(server["cpu"]["architecture"], "aarch64")
            self.assertEqual(server["runtimes"][0], {"id": "node", "installed": True, "version": "20.20.2"})
            self.assertEqual(server["databases"][0]["server_version"], "18.4 (Ubuntu 18.4-0ubuntu0.26.04.1)")
            self.assertFalse(server["containers"]["docker"]["installed"])
            self.assertFalse(server["containers"]["compose"]["installed"])
            self.assertEqual(server["proxy"]["version"], "1.28.3 (Ubuntu)")
        for finding in inventory["lifecycle_findings"]:
            for field in ("upstream_status", "eol", "source_url", "retrieved_at", "review_by", "action"):
                self.assertTrue(finding[field])
            self.assertTrue(finding["source_url"].startswith("https://"))

        notes = " ".join(inventory["collection_notes"])
        self.assertIn("SANDBOX_PATH_BLOCKED", notes)
        self.assertIn("zero applications", notes)
        self.assertIn("no PM2 daemon remained", notes)

    def test_governance_docs_keep_candidate_and_delivery_boundaries(self) -> None:
        # Pinned by section heading, not body text (R14): rewording a section keeps it green.
        required = {
            ROOT / "README.md": "交付形态参考（按项目选用，非部署步骤事实源）",
            ROOT / "07-内网与生产平移路线.md": "10. Architecture catalog 采用门",
            ROOT / "archive/09-v3平台简化与Loop-Engineering文档改造规划.md": "15. Architecture catalog 与 Loop 的边界",
            ROOT / "12-Linux-GitHub-Gitea-双服务器自动部署方案.md": "20.1 Architecture lock input",
            ROOT / "skills/aisoft-platform/references/onboarding-runbook.md": "9. Architecture declaration onboarding",
        }
        for path, heading in required.items():
            with self.subTest(path=path.name):
                headings = {
                    line.lstrip("#").strip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if re.match(r"#{1,6} ", line)
                }
                self.assertIn(heading, headings)


if __name__ == "__main__":
    unittest.main()
