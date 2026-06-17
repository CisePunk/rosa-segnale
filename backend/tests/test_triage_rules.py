import unittest

from app.models import EscalationTeam, OperationalArea, TicketCategory
from app.triage_rules import classify_safety_context


class TriageRulesTest(unittest.TestCase):
    def assert_rule(
        self,
        text: str,
        category: TicketCategory,
        min_risk_score: int,
        escalation: EscalationTeam,
    ) -> None:
        match = classify_safety_context(text)

        self.assertIsNotNone(match, text)
        self.assertEqual(match.category, category)
        self.assertGreaterEqual(match.min_risk_score, min_risk_score)
        self.assertEqual(match.escalation, escalation)

    def test_immediate_danger(self) -> None:
        examples = [
            "Sono in pericolo adesso.",
            "Lui è fuori dalla porta e ho paura.",
            "Mi ha minacciata e sta arrivando qui.",
            "Lui sta tornando.",
            "Non posso parlare.",
            "Non sono sola.",
            "Non posso uscire di casa in sicurezza.",
            "Ho paura che possa farmi del male stanotte.",
            "Ha una pistola in casa.",
            "Tiene un coltello e mi ha minacciata.",
            "Mi ha detto che mi uccide.",
            "Non sono sola, ho i miei figli con me.",
        ]

        for text in examples:
            with self.subTest(text=text):
                self.assert_rule(text, TicketCategory.immediate_risk, 5, EscalationTeam.emergency)

    def test_not_alone_with_children_prefers_emergency(self) -> None:
        self.assert_rule(
            "Non sono sola, ho i miei figli con me.",
            TicketCategory.immediate_risk,
            5,
            EscalationTeam.emergency,
        )

    def test_domestic_violence(self) -> None:
        examples = [
            "Mi ha spinta, ma dice che non è successo niente.",
            "Ci siamo lasciati e non accetta che sia finita.",
            "L'ho lasciato e mi ha detto che non mi lascerà mai.",
            "Non mi lascia vedere le mie amiche e mi ha allontanata dalla mia famiglia.",
            "Mi isola e sono tagliata fuori da tutti.",
            "Vivo con una persona che mi fa paura.",
        ]

        for text in examples:
            with self.subTest(text=text):
                self.assert_rule(text, TicketCategory.domestic_violence, 4, EscalationTeam.anti_violence_center)

    def test_coercive_control_economic_and_verbal_violence(self) -> None:
        cases = [
            (
                "Il mio compagno mi controlla il telefono e mi impedisce di uscire.",
                TicketCategory.coercive_control,
                4,
            ),
            (
                "Ero in comunità e avevo il telefono solo un'ora al giorno.",
                TicketCategory.coercive_control,
                4,
            ),
            (
                "Mi controlla i soldi e non mi lascia lavorare.",
                TicketCategory.economic_violence,
                3,
            ),
            (
                "Mi urla addosso e poi dice che è colpa mia.",
                TicketCategory.verbal_violence,
                3,
            ),
            (
                "Mi insulta e mi fa sentire pazza.",
                TicketCategory.verbal_violence,
                3,
            ),
        ]

        for text, category, risk in cases:
            with self.subTest(text=text):
                match = classify_safety_context(text)

                self.assertIsNotNone(match)
                self.assertEqual(match.category, category)
                self.assertGreaterEqual(match.min_risk_score, risk)
                self.assertEqual(match.escalation, EscalationTeam.anti_violence_center)
                self.assertIn(match.operational_area, [OperationalArea.human_bridge, OperationalArea.listening])
                self.assertTrue(match.human_handoff)

    def test_stalking(self) -> None:
        examples = [
            "Mi segue sotto casa e al lavoro.",
            "Ha creato profili falsi per controllarmi.",
            "Continua a chiamarmi da numeri diversi.",
            "Ricevo messaggi insistenti e minacciosi.",
        ]

        for text in examples:
            with self.subTest(text=text):
                self.assert_rule(text, TicketCategory.stalking, 3, EscalationTeam.anti_violence_center)

    def test_returning_home_is_high_risk(self) -> None:
        examples = [
            "Ho paura a tornare a casa e non so a chi rivolgermi.",
            "Non mi sento al sicuro nel rientrare.",
            "Mi serve un posto sicuro per stanotte.",
        ]

        for text in examples:
            with self.subTest(text=text):
                self.assert_rule(text, TicketCategory.safe_housing, 4, EscalationTeam.anti_violence_center)

    def test_legal_evidence_psychological_social_and_minors(self) -> None:
        cases = [
            ("Vorrei capire se posso parlare con qualcuno per denunciare.", TicketCategory.legal_support, 3, EscalationTeam.legal_desk),
            ("Ho screenshot dei messaggi.", TicketCategory.evidence_documentation, 3, EscalationTeam.evidence_collection),
            ("Ho screenshot dei messaggi insistenti e non so come conservarli.", TicketCategory.evidence_documentation, 3, EscalationTeam.evidence_collection),
            ("Mi sento confusa e non riesco a calmarmi.", TicketCategory.psychological_support, 2, EscalationTeam.psychological_support),
            ("Non ho soldi per andarmene.", TicketCategory.social_support, 3, EscalationTeam.social_services),
            ("Ho paura per i miei figli.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
            ("Sono incinta e ho paura di lui.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
            ("Ho 16 anni e ho paura a casa.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
            ("Ho diciassette anni e ho paura a casa.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
            ("Sono una ragazza di 15 anni e ho paura a casa.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
            ("Sono minorenne ma ho già 17 anni.", TicketCategory.minors_family, 4, EscalationTeam.minors_protection),
        ]

        for text, category, risk, escalation in cases:
            with self.subTest(text=text):
                self.assert_rule(text, category, risk, escalation)

    def test_self_harm_is_risk_five(self) -> None:
        examples = [
            "Sto pensando di farmi del male.",
            "Non voglio più vivere.",
            "Ho paura di fare qualcosa contro me stessa.",
        ]

        for text in examples:
            with self.subTest(text=text):
                self.assert_rule(text, TicketCategory.emotional_crisis, 5, EscalationTeam.emergency)

    def test_out_of_scope(self) -> None:
        examples = [
            "Come faccio la carbonara?",
            "Mi consigli un film?",
            "Puoi scrivere tu una denuncia?",
            "Puoi dirmi se questa persona è colpevole?",
            "Ahah aiuto lol, sto scherzando.",
        ]

        for text in examples:
            with self.subTest(text=text):
                match = classify_safety_context(text)

                self.assertIsNotNone(match, text)
                self.assertEqual(match.category, TicketCategory.out_of_scope)
                self.assertGreaterEqual(match.min_risk_score, 1)
                self.assertEqual(match.escalation, EscalationTeam.insufficient_context)
                self.assertTrue(match.suspected_misuse)

    def test_short_emergency_words_are_not_misuse(self) -> None:
        for text in ["aiuto", "Rosa", "non posso parlare", "lui sta tornando"]:
            with self.subTest(text=text):
                match = classify_safety_context(text)

                if match is not None:
                    self.assertFalse(match.suspected_misuse)
                    self.assertNotEqual(match.category, TicketCategory.out_of_scope)


if __name__ == "__main__":
    unittest.main()
