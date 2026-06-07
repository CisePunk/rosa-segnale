import unittest
import os
from unittest.mock import patch

from app.assistant_provider import answer_with_assistant, _looks_like_support_request, _routing_context
from app.knowledge import retrieve_chunks


class AssistantProviderRoutingTest(unittest.TestCase):
    def test_support_terms_route_to_openai_path(self) -> None:
        self.assertTrue(_looks_like_support_request("Mi sento confusa e spaventata."))
        self.assertTrue(_looks_like_support_request("Non so se denunciare."))

    def test_immediate_danger_routes_to_112(self) -> None:
        routing = _routing_context("Sono in centro e un uomo mi segue", [])

        self.assertIn("112", routing)
        self.assertIn("sicurezza immediata", routing)

    def test_stalking_routes_to_1522(self) -> None:
        routing = _routing_context("Mi controlla il telefono e ho paura a tornare a casa", [])

        self.assertIn("1522", routing)
        self.assertIn("centro antiviolenza", routing)

    def test_evidence_routes_to_legal_support(self) -> None:
        routing = _routing_context("Ho screenshot e registrazioni, non so come conservarli", [])

        self.assertIn("supporto legale", routing)
        self.assertIn("raccolta ordinata", routing)

    def test_minors_routes_to_competent_services(self) -> None:
        routing = _routing_context("Ho paura per i miei figli", [])

        self.assertIn("minori", routing)
        self.assertIn("servizi competenti", routing)

    def test_new_immediate_danger_routes(self) -> None:
        examples = [
            "Lui sta tornando.",
            "Non posso parlare.",
            "Ha una pistola in casa.",
        ]

        for text in examples:
            with self.subTest(text=text):
                routing = _routing_context(text, [])
                self.assertIn("112", routing)
                self.assertIn("sicurezza immediata", routing)

    def test_pregnancy_minor_and_deletion_routes(self) -> None:
        pregnancy = _routing_context("Sono incinta e ho paura di lui.", [])
        minor = _routing_context("Ho diciassette anni e ho paura a casa.", [])
        deletion = _routing_context("Cancella tutto.", [])

        self.assertIn("gravidanza", pregnancy)
        self.assertIn("1522", pregnancy)
        self.assertIn("19696", minor)
        self.assertIn("minorenne", minor)
        self.assertIn("cancellazione", deletion)
        self.assertIn("schermata neutra", deletion)

    def test_not_alone_and_social_isolation_routes(self) -> None:
        ambiguous = _routing_context("Non sono sola.", [])
        isolation = _routing_context("Non mi lascia vedere le mie amiche.", [])

        self.assertIn("sicurezza immediata", ambiguous)
        self.assertIn("frase ambigua", ambiguous)
        self.assertIn("1522", isolation)
        self.assertIn("centro antiviolenza", isolation)

    def test_openai_error_falls_back_to_local_answer(self) -> None:
        question = "Lui sta tornando."
        chunks = retrieve_chunks(question, 3)

        with patch.dict(
            os.environ,
            {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"},
            clear=False,
        ), patch(
            "app.assistant_provider._answer_with_openai",
            side_effect=RuntimeError("timeout"),
        ):
            answer, provider = answer_with_assistant(question, chunks)

        self.assertEqual(provider, "local-rag-keyword-v1")
        self.assertIn("112", answer)
        self.assertIn("pericolo", answer.lower())


if __name__ == "__main__":
    unittest.main()
