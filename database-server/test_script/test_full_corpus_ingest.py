from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FullCorpusIngestTest(unittest.TestCase):
    def test_canonical_documents_have_stable_unique_source_ids(self) -> None:
        from scripts.ingest_full_corpus import discover_documents

        documents = discover_documents(ROOT / "rsc" / "data")
        self.assertGreater(len(documents), 20)
        source_ids = [document.source_id for document in documents]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertTrue(all(document.content.strip() for document in documents))

    def test_ingest_uses_idempotent_upsert_without_erasing_embeddings(self) -> None:
        source = (ROOT / "scripts" / "ingest_full_corpus.py").read_text(encoding="utf-8")
        self.assertIn("ON CONFLICT (source_id) DO UPDATE", source)
        update_clause = source.split("ON CONFLICT (source_id) DO UPDATE", maxsplit=1)[1]
        self.assertNotIn("embedding =", update_clause)


if __name__ == "__main__":
    unittest.main()
