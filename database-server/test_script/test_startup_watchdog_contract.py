from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StartupWatchdogContractTest(unittest.TestCase):
    def test_database_startup_has_bounded_retries_and_log_capture(self) -> None:
        script = ROOT / "scripts" / "start_storage.ps1"
        self.assertTrue(script.exists(), "database startup watchdog must exist")
        source = script.read_text(encoding="utf-8")
        self.assertIn("$TimeoutSeconds = 600", source)
        self.assertIn("$MaxAttempts = 3", source)
        self.assertIn("docker compose logs --no-color", source)
        self.assertIn("docker inspect", source)
        self.assertIn("postgres", source)
        self.assertIn("neo4j", source)


if __name__ == "__main__":
    unittest.main()
