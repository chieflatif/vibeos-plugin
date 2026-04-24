import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "plugins/vibeos/scripts/evidence-recall.py"
SPEC = importlib.util.spec_from_file_location("evidence_recall", MODULE_PATH)
evidence_recall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence_recall)


class EvidenceRecallTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        planning = root / "docs/planning"
        planning.mkdir(parents=True)
        (planning / "WO-001-alpha.md").write_text(
            "# WO-001: Alpha\n\n## Objective\n\nBuild session checkpoint recall for memory evidence.\n\n"
            "## Evidence\n\nReferences WO-002 and `.vibeos/session-state.json`.\n",
            encoding="utf-8",
        )
        (planning / "WO-002-beta.md").write_text(
            "# WO-002: Beta\n\n## Objective\n\nBuild audit consensus and findings registry support.\n",
            encoding="utf-8",
        )
        (root / ".vibeos").mkdir()
        (root / ".vibeos/session-state.json").write_text(
            json.dumps({"active": True, "active_wo": "docs/planning/WO-001-alpha.md"}),
            encoding="utf-8",
        )
        return temp, root

    def test_index_records_have_citations_and_schema(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        index = evidence_recall.build_index(root)
        self.assertGreaterEqual(index["record_count"], 3)
        record = index["records"][0]
        for field in ("source_path", "source_locator", "record_type", "confidence", "freshness", "tags", "references", "reason_for_inclusion"):
            self.assertIn(field, record)
        self.assertIn(":", record["source_locator"])

    def test_query_returns_bounded_cited_results(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        index = evidence_recall.build_index(root)
        results = evidence_recall.query(index, "session checkpoint memory evidence", 5, True)
        self.assertTrue(results)
        self.assertTrue(results[0]["source_locator"].startswith("docs/planning/WO-001"))
        self.assertLessEqual(len(results[0]["excerpt"]), 700)

    def test_default_cache_path_and_index_write(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        cache = evidence_recall.default_cache(root)
        self.assertEqual(cache, root / ".vibeos/cache/evidence-recall-index.json")
        index = evidence_recall.load_or_build(root, True)
        self.assertTrue(cache.exists())
        cached = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual(cached["record_count"], index["record_count"])

    def test_query_diversifies_by_source(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        index = evidence_recall.build_index(root)
        results = evidence_recall.query(index, "build evidence objective", 10, True)
        sources = [item["source_path"] for item in results]
        self.assertEqual(len(sources), len(set(sources)))


if __name__ == "__main__":
    unittest.main()
