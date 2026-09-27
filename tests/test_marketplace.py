import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class MarketplacePackageTest(unittest.TestCase):
    def test_marketplace_installs_the_same_skill_as_direct_clone(self) -> None:
        catalog_path = ROOT / ".agents/plugins/marketplace.json"
        self.assertTrue(catalog_path.is_file(), "GitHub marketplace catalog is missing")
        catalog = json.loads(catalog_path.read_text())
        entry, = catalog["plugins"]
        plugin = ROOT / entry["source"]["path"]
        manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(manifest["skills"], "./skills/")

        bundled = plugin / "skills/codex-model-routing"
        for path in ("SKILL.md", "agents/openai.yaml", "scripts/runtime_usage.py"):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), (bundled / path).read_bytes())


if __name__ == "__main__":
    unittest.main()
