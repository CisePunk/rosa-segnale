import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import repository
from app.main import allowed_cors_origins, app


class InternalAuthTest(unittest.TestCase):
    def setUp(self) -> None:
        # Database temporaneo: senza, queste prove passavano solo sulle macchine dove
        # esiste gia' backend/triage.db, e leggevano quello.
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = repository.DB_PATH
        repository.DB_PATH = repository.Path(self.tempdir.name) / "auth-test.db"
        repository.init_db()

    def tearDown(self) -> None:
        repository.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_internal_routes_fail_closed_when_auth_env_is_absent(self) -> None:
        """Senza credenziali configurate l'area interna deve CHIUDERSI.

        Prima ritornava i dati a chiunque: questa prova affermava che fosse
        giusto cosi'. Su un archivio di segnalazioni sensibili, una variabile
        d'ambiente dimenticata non puo' equivalere a "porta aperta".
        """
        with patch.dict(os.environ, {}, clear=True):
            response = TestClient(app).get("/dashboard")

        self.assertEqual(response.status_code, 503)

    def test_internal_routes_require_basic_auth_when_configured(self) -> None:
        env = {
            "INTERNAL_AUTH_USERNAME": "reviewer",
            "INTERNAL_AUTH_PASSWORD": "secret",
        }

        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app)
            missing = client.get("/dashboard")
            wrong = client.get("/dashboard", auth=("reviewer", "wrong"))
            right = client.get("/dashboard", auth=("reviewer", "secret"))

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertNotEqual(right.status_code, 401)

    def test_dev_switch_must_be_explicit(self) -> None:
        """Lo sviluppo locale si apre solo con una scelta scritta."""
        with patch.dict(os.environ, {"INTERNAL_AUTH_DISABLED": "true"}, clear=True):
            aperta = TestClient(app).get("/dashboard")
        self.assertNotEqual(aperta.status_code, 401)
        self.assertNotEqual(aperta.status_code, 503)

    def test_public_assistant_stays_public(self) -> None:
        """L'assistente e' la parte pubblica: chi cerca aiuto non fa login.

        Se un giorno finisse dietro l'autenticazione, il prodotto smetterebbe
        di fare il suo mestiere. Questa prova serve a impedirlo.
        """
        with patch.dict(os.environ, {}, clear=True):
            risposta = TestClient(app).post(
                "/assistant/answer", json={"question": "Come funziona?", "top_k": 1}
            )
        self.assertNotIn(risposta.status_code, (401, 503))


class CorsTest(unittest.TestCase):
    def test_dev_origins_disappear_once_configured(self) -> None:
        """In produzione localhost non deve restare fra le origini ammesse."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://rosasegnale.it"}, clear=True):
            origini = allowed_cors_origins()
        self.assertEqual(origini, ["https://rosasegnale.it"])
        self.assertNotIn("http://localhost:5173", origini)

    def test_dev_origins_remain_when_nothing_configured(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIn("http://localhost:5173", allowed_cors_origins())


if __name__ == "__main__":
    unittest.main()
