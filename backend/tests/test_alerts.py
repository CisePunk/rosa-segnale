import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class AlertsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tempdir.name, "alerts-test.db")
        self.env_patch = patch.dict(
            os.environ,
            {
                "TRIAGE_DB_PATH": self.db_path,
                "AI_PROVIDER": "mock",
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

    def test_human_handoff_ticket_creates_alert(self) -> None:
        response = self.client.post(
            "/tickets",
            json={
                "title": "Telefono controllato",
                "description": "Avevo il telefono solo un'ora al giorno e potevo scrivere solo quando uscivo.",
                "priority": "Media",
                "business_impact": "Richiesta anonima di orientamento.",
                "technical_area": "Ascolto",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["human_handoff"])
        self.assertEqual(response.json()["emotional_tone"], "Controllo o sorveglianza")
        self.assertGreaterEqual(response.json()["urgency_confidence"], 0.8)
        self.assertEqual(response.json()["misuse_confidence"], 0)

        alerts = self.client.get("/alerts").json()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["status"], "Nuovo")
        self.assertEqual(alerts[0]["operational_area"], "Ponte umano")
        self.assertEqual(alerts[0]["ticket_id"], response.json()["id"])

    def test_alert_take_and_close(self) -> None:
        created = self.client.post(
            "/alerts",
            json={
                "source": "Manuale",
                "title": "Alert manuale",
                "summary": "Test di presa in carico.",
                "risk_score": 4,
                "operational_area": "Ponte umano",
            },
        ).json()

        taken = self.client.patch(f"/alerts/{created['id']}/take")
        closed = self.client.patch(f"/alerts/{created['id']}/close")

        self.assertEqual(taken.status_code, 200)
        self.assertEqual(taken.json()["status"], "In carico")
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.json()["status"], "Chiuso")
        self.assertIsNotNone(closed.json()["closed_at"])


if __name__ == "__main__":
    unittest.main()
