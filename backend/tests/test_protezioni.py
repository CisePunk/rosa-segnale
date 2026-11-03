import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main, repository
from app.honeypot import client_ip


class ProtezioniBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = repository.DB_PATH
        repository.DB_PATH = repository.Path(self.tempdir.name) / "protezioni-test.db"
        repository.init_db()
        self.env_patch = patch.dict(
            os.environ,
            {
                "INTERNAL_AUTH_USERNAME": "operatore",
                "INTERNAL_AUTH_PASSWORD": "password-di-prova",
                "HONEYPOT_HASH_SALT": "s" * 32,
                "AI_PROVIDER": "mock",
            },
        )
        self.env_patch.start()
        for variabile in ("INTERNAL_AUTH_DISABLED", "SECURITY_STRICT", "TRUST_PROXY_HEADER"):
            os.environ.pop(variabile, None)
        main._login_tentativi.clear()
        main._ASSISTANT_RATE.clear()
        self.client = TestClient(main.app)
        self.giusta = ("operatore", "password-di-prova")

    def tearDown(self) -> None:
        main._login_tentativi.clear()
        main._ASSISTANT_RATE.clear()
        main._ai_finestra.update(inizio=0.0, conteggio=0)
        self.env_patch.stop()
        repository.DB_PATH = self.original_db_path
        self.tempdir.cleanup()


class LoginTest(ProtezioniBase):
    def test_too_many_failures_lock_even_the_right_password(self) -> None:
        for _ in range(main._LOGIN_MAX_FALLIMENTI):
            self.assertEqual(self.client.get("/tickets", auth=("operatore", "no")).status_code, 401)
        bloccata = self.client.get("/tickets", auth=self.giusta)
        self.assertEqual(bloccata.status_code, 429)
        self.assertIn("retry-after", bloccata.headers)

    def test_success_clears_previous_failures(self) -> None:
        for _ in range(main._LOGIN_MAX_FALLIMENTI - 1):
            self.client.get("/tickets", auth=("operatore", "no"))
        self.assertEqual(self.client.get("/tickets", auth=self.giusta).status_code, 200)
        self.client.get("/tickets", auth=("operatore", "no"))
        self.assertEqual(self.client.get("/tickets", auth=self.giusta).status_code, 200)

    def test_opening_the_page_without_credentials_does_not_count(self) -> None:
        for _ in range(main._LOGIN_MAX_FALLIMENTI * 2):
            self.assertEqual(self.client.get("/tickets").status_code, 401)
        self.assertEqual(self.client.get("/tickets", auth=self.giusta).status_code, 200)

    def test_public_assistant_ignores_the_lock(self) -> None:
        """Un blocco sull'area interna non deve mai togliere l'aiuto a chi scrive."""
        for _ in range(main._LOGIN_MAX_FALLIMENTI):
            self.client.get("/tickets", auth=("operatore", "no"))
        risposta = self.client.post("/assistant/answer", json={"question": "ho paura di tornare a casa"})
        self.assertEqual(risposta.status_code, 200)


class IndirizzoTest(ProtezioniBase):
    def test_spoofed_forwarded_values_do_not_bypass_the_limit(self) -> None:
        os.environ["TRUST_PROXY_HEADER"] = "x-forwarded-for"
        stati = [
            self.client.post(
                "/assistant/answer",
                json={"question": "ho paura di tornare a casa"},
                headers={"x-forwarded-for": f"9.9.9.{i}, 1.1.1.1"},
            ).status_code
            for i in range(3)
        ]
        self.assertEqual(stati, [200, 429, 429])

    def test_forwarded_header_is_ignored_unless_trusted(self) -> None:
        richiesta = type("R", (), {"headers": {"x-forwarded-for": "9.9.9.9"}, "client": type("C", (), {"host": "1.2.3.4"})})
        self.assertEqual(client_ip(richiesta), "1.2.3.4")


class BudgetAiTest(ProtezioniBase):
    def test_over_budget_answers_locally_without_calling_the_provider(self) -> None:
        main._ai_finestra.update(inizio=main.monotonic(), conteggio=main._AI_MAX_AL_MINUTO)
        with patch("app.main.answer_with_assistant") as provider:
            risposta = self.client.post("/assistant/answer", json={"question": "lui sta tornando, ho paura"})
        provider.assert_not_called()
        self.assertEqual(risposta.status_code, 200)
        self.assertEqual(risposta.json()["provider"], "local-rag-keyword-v1")
        self.assertIn("112", risposta.json()["answer"])


class RichiesteTest(ProtezioniBase):
    def test_foreign_origin_cannot_write(self) -> None:
        risposta = self.client.post("/sample-data/seed", auth=self.giusta, headers={"Origin": "https://evil.example"})
        self.assertEqual(risposta.status_code, 403)
        self.assertEqual(self.client.get("/tickets", auth=self.giusta).json(), [])

    def test_allowed_origin_can_write(self) -> None:
        risposta = self.client.post("/sample-data/seed", auth=self.giusta, headers={"Origin": "http://127.0.0.1:5173"})
        self.assertEqual(risposta.status_code, 200)

    def test_oversized_body_is_refused(self) -> None:
        risposta = self.client.post(
            "/assistant/answer",
            content=b'{"question":"' + b"a" * main._MAX_BODY_BYTES + b'"}',
            headers={"content-type": "application/json"},
        )
        self.assertEqual(risposta.status_code, 413)

    def test_chunked_body_without_length_is_refused(self) -> None:
        def pezzi():
            yield b'{"question":"aiuto aiuto"}'

        risposta = self.client.post("/assistant/answer", content=pezzi(), headers={"content-type": "application/json"})
        self.assertEqual(risposta.status_code, 411)

    def test_unstorable_values_are_client_errors(self) -> None:
        casi = [
            ("patch", "/alerts/9223372036854775808/take", None, None),
            ("post", "/alerts", None, {"title": "abc", "summary": "abc", "risk_score": 1, "ticket_id": 2**63}),
            ("post", "/alerts", '{"title":"ab\\ud800c","summary":"abc","risk_score":1}', None),
            ("post", "/alerts", '{"title":"abc","summary":"abc","risk_score":NaN}', None),
            ("post", "/alerts", '{"title":"abc","summary":"abc","risk_score":1e999}', None),
        ]
        client = TestClient(main.app, raise_server_exceptions=False)
        for metodo, percorso, grezzo, dati in casi:
            with self.subTest(percorso=percorso, grezzo=grezzo):
                opzioni = {"auth": self.giusta}
                if grezzo is not None:
                    opzioni.update(content=grezzo, headers={"content-type": "application/json"})
                elif dati is not None:
                    opzioni["json"] = dati
                self.assertEqual(getattr(client, metodo)(percorso, **opzioni).status_code, 422)

    def test_public_assistant_rejects_broken_unicode_cleanly(self) -> None:
        client = TestClient(main.app, raise_server_exceptions=False)
        risposta = client.post(
            "/assistant/answer", content='{"question":"aiuto \\ud800 aiuto"}', headers={"content-type": "application/json"}
        )
        self.assertEqual(risposta.status_code, 422)

    def test_validation_errors_do_not_echo_the_text(self) -> None:
        risposta = self.client.post("/assistant/answer", json={"question": "abc"})
        self.assertEqual(risposta.status_code, 422)
        self.assertNotIn("input", risposta.json()["detail"][0])

    def test_security_headers_are_set(self) -> None:
        intestazioni = self.client.get("/health").headers
        self.assertEqual(intestazioni["x-content-type-options"], "nosniff")
        self.assertEqual(intestazioni["x-frame-options"], "DENY")
        self.assertEqual(intestazioni["cache-control"], "no-store")


class HoneypotTettoTest(ProtezioniBase):
    def test_events_are_capped(self) -> None:
        with patch("app.repository.HONEYPOT_MAX_EVENTI", 3):
            for i in range(6):
                self.client.get(f"/debug{i}")
        eventi = self.client.get("/security/honeypot-events", auth=self.giusta).json()
        self.assertEqual(len(eventi), 3)
        self.assertEqual(sorted(e["path"] for e in eventi), ["/debug3", "/debug4", "/debug5"])


class SegretiTest(ProtezioniBase):
    def test_strong_secrets_pass_in_strict_mode(self) -> None:
        with patch.dict(os.environ, {"SECURITY_STRICT": "true"}):
            main.controlla_segreti()

    def test_weak_secrets_only_warn_by_default(self) -> None:
        with patch.dict(os.environ, {"INTERNAL_AUTH_PASSWORD": "corta"}), self.assertLogs(level="WARNING"):
            main.controlla_segreti()

    def test_weak_secrets_block_startup_in_strict_mode(self) -> None:
        for variabili in (
            {"INTERNAL_AUTH_PASSWORD": "corta"},
            {"HONEYPOT_HASH_SALT": "corto"},
            {"INTERNAL_AUTH_DISABLED": "true"},
        ):
            with self.subTest(variabili=variabili), patch.dict(os.environ, {"SECURITY_STRICT": "true", **variabili}):
                with self.assertRaises(RuntimeError):
                    main.controlla_segreti()


if __name__ == "__main__":
    unittest.main()
