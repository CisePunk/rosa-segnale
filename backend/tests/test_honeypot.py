import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class HoneypotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tempdir.name, "honeypot-test.db")
        self.env_patch = patch.dict(
            os.environ,
            {
                "TRIAGE_DB_PATH": self.db_path,
                "AI_PROVIDER": "mock",
                "HONEYPOT_HASH_SALT": "test-salt",
            },
            clear=False,
        )
        self.env_patch.start()

        import app.repository as repository
        import app.main as main
        from app.ai_providers import MockRosaSegnaleTriageProvider

        self.repository = repository
        self.main = main
        self.original_db_path = repository.DB_PATH
        self.original_provider = main.provider
        repository.DB_PATH = repository.Path(self.db_path)
        main.provider = MockRosaSegnaleTriageProvider()
        repository.init_db()
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        self.repository.DB_PATH = self.original_db_path
        self.main.provider = self.original_provider
        self.env_patch.stop()
        self.tempdir.cleanup()

    def test_trap_path_is_recorded(self) -> None:
        response = self.client.get(
            "/wp-login.php",
            headers={"user-agent": "scanner-test"},
        )

        self.assertEqual(response.status_code, 404)

        events = self.client.get("/security/honeypot-events").json()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["path"], "/wp-login.php")
        self.assertEqual(events[0]["reason"], "trap_path")
        self.assertEqual(events[0]["risk_score"], 4)
        self.assertEqual(events[0]["user_agent"], "scanner-test")
        self.assertEqual(len(events[0]["ip_hash"]), 24)

    def test_regular_route_is_not_recorded(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/security/honeypot-events").json(), [])


if __name__ == "__main__":
    unittest.main()
