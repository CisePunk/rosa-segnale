import re
from dataclasses import dataclass

from app.models import EscalationTeam, TicketCategory, TicketCreate, TriageResult


@dataclass(frozen=True)
class SafetyRuleMatch:
    category: TicketCategory
    min_risk_score: int
    escalation: EscalationTeam
    label: str


def apply_safety_overrides(ticket: TicketCreate, result: TriageResult) -> TriageResult:
    match = classify_safety_context(_ticket_text(ticket))

    if match is None:
        return result

    risk_score = max(result.risk_score, match.min_risk_score)
    category = match.category
    escalation = match.escalation

    if category == TicketCategory.out_of_scope:
        risk_score = min(result.risk_score, match.min_risk_score)

    return TriageResult(
        category=category,
        risk_score=risk_score,
        escalation=escalation,
        recommendation=_recommendation_for(match, risk_score),
        provider=result.provider,
        rationale=(
            f"Regola di sicurezza '{match.label}' applicata dopo la classificazione AI/mock: "
            f"categoria {category.value}, rischio minimo {match.min_risk_score}/5, percorso {escalation.value}."
        ),
    )


def classify_safety_context(text: str) -> SafetyRuleMatch | None:
    normalized = _normalize(text)

    if _contains_any(
        normalized,
        [
            "come faccio la carbonara",
            "mi consigli un film",
            "puoi dirmi se questa persona e colpevole",
            "puoi dirmi se questa persona è colpevole",
            "puoi scrivere tu una denuncia",
            "quanto costa un avvocato divorzista",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.out_of_scope,
            1,
            EscalationTeam.insufficient_context,
            "fuori_ambito",
        )

    if _contains_any(
        normalized,
        [
            "sto pensando di farmi del male",
            "non voglio piu vivere",
            "non voglio più vivere",
            "contro me stessa",
            "pensieri brutti",
            "non riesco a fermarli",
            "in pericolo da sola",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.emotional_crisis,
            5,
            EscalationTeam.emergency,
            "crisi_emotiva_rischio_5",
        )

    if _contains_any(
        normalized,
        [
            "pericolo adesso",
            "fuori dalla porta",
            "sta arrivando",
            "sta tornando",
            "sta rientrando",
            "sta venendo",
            "e in arrivo",
            "è in arrivo",
            "mi ha minacciata",
            "mi ha minacciato",
            "mi ha minacciata di morte",
            "mi ha minacciato di morte",
            "mi ha detto che mi uccide",
            "ha detto che mi uccide",
            "mi uccide",
            "mi ammazza",
            "farmi del male stanotte",
            "mi fara del male",
            "mi farà del male",
            "non posso uscire",
            "non posso parlare",
            "emergenza",
            "ha una pistola",
            "ha un coltello",
            "ha un arma",
            "ha un'arma",
            "tiene una pistola",
            "tiene un coltello",
            "arma in casa",
            "armi in casa",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.immediate_risk,
            5,
            EscalationTeam.emergency,
            "emergenza_immediata_rischio_5",
        )

    if _contains_any(
        normalized,
        [
            "sono incinta",
            "sono in gravidanza",
            "aspetto un figlio",
            "aspetto una figlia",
            "aspetto un bambino",
            "aspetto una bambina",
            "gravidanza",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.minors_family,
            4,
            EscalationTeam.minors_protection,
            "gravidanza_fattore_rischio_minimo_4",
        )

    if _is_minor_self_report(normalized):
        return SafetyRuleMatch(
            TicketCategory.minors_family,
            4,
            EscalationTeam.minors_protection,
            "utente_minorenne_rischio_minimo_4",
        )

    if _contains_any(
        normalized,
        [
            "non sono sola",
            "non sono solo",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.immediate_risk,
            5,
            EscalationTeam.emergency,
            "presenza_altra_persona_ambigua_rischio_5",
        )

    if _contains_any(normalized, ["figli", "bambini", "mia figlia", "mio figlio", "minori"]):
        return SafetyRuleMatch(
            TicketCategory.minors_family,
            4,
            EscalationTeam.minors_protection,
            "minori_famiglia_rischio_minimo_4",
        )

    if _contains_any(
        normalized,
        [
            "paura a tornare a casa",
            "paura di tornare a casa",
            "non mi sento al sicuro nel rientrare",
            "non posso dormire a casa",
            "posto sicuro per stanotte",
            "paura della reazione quando rientro",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.safe_housing,
            4,
            EscalationTeam.anti_violence_center,
            "paura_tornare_casa_rischio_minimo_4",
        )

    if _contains_any(
        normalized,
        [
            "screenshot",
            "registrazioni",
            "foto",
            "conservare",
            "tenere traccia",
            "organizzare le prove",
            "perdere le conversazioni",
            "prove",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.evidence_documentation,
            3,
            EscalationTeam.evidence_collection,
            "documentazione_prove",
        )

    if _contains_any(
        normalized,
        [
            "mi segue",
            "mi sta seguendo",
            "sotto casa",
            "al lavoro",
            "profili falsi",
            "numeri diversi",
            "messaggi insistenti",
            "messaggi minacciosi",
            "decine di messaggi",
        ],
    ):
        min_risk = 4 if _contains_any(normalized, ["mi segue", "minacciosi", "sotto casa", "al lavoro"]) else 3
        return SafetyRuleMatch(
            TicketCategory.stalking,
            min_risk,
            EscalationTeam.anti_violence_center,
            "stalking_molestie",
        )

    if _contains_any(
        normalized,
        [
            "mi controlla il telefono",
            "mi impedisce di uscire",
            "urla addosso",
            "colpa mia",
            "mi ha spinta",
            "mi ha picchiata",
            "mi ha picchiato",
            "ci siamo lasciati",
            "l'ho lasciato",
            "lo voglio lasciare",
            "voglio separarmi",
            "mi sto separando",
            "non mi lascera mai",
            "non mi lascerà mai",
            "non accetta la separazione",
            "non accetta che sia finita",
            "mi ha allontanata dalla mia famiglia",
            "mi ha allontanato dalla mia famiglia",
            "non mi lascia vedere le mie amiche",
            "non mi lascia vedere i miei amici",
            "non posso vedere le mie amiche",
            "non posso vedere i miei amici",
            "sono tagliata fuori",
            "sono tagliato fuori",
            "mi isola",
            "isolata da tutti",
            "isolato da tutti",
            "vivo con una persona che mi fa paura",
            "persona che mi fa paura",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.domestic_violence,
            4,
            EscalationTeam.anti_violence_center,
            "violenza_domestica",
        )

    if _contains_any(
        normalized,
        [
            "non ho soldi",
            "dipendo economicamente",
            "non so dove dormire",
            "aiuto pratico",
            "rete familiare",
            "trovare un posto sicuro",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.social_support,
            3,
            EscalationTeam.social_services,
            "supporto_sociale",
        )

    if _contains_any(
        normalized,
        [
            "denunciare",
            "denuncia",
            "orientamento legale",
            "supporto legale",
            "prima di fare una denuncia",
            "avvocato",
            "querela",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.legal_support,
            3,
            EscalationTeam.legal_desk,
            "supporto_legale",
        )

    if _contains_any(
        normalized,
        [
            "confusa",
            "non riesco a calmarmi",
            "mi sento sola",
            "crisi emotiva",
            "non riesco a dormire",
            "ansia",
            "parlare con qualcuno",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.psychological_support,
            2,
            EscalationTeam.psychological_support,
            "supporto_psicologico",
        )

    if _contains_any(
        normalized,
        [
            "non so se sto esagerando",
            "non voglio denunciare",
            "voglio solo capire",
            "non so se e violenza",
            "non so se è violenza",
            "mi sento controllata",
            "mi sento a disagio",
        ],
    ):
        return SafetyRuleMatch(
            TicketCategory.information_request,
            2,
            EscalationTeam.case_worker,
            "orientamento_generico",
        )

    return None


def _recommendation_for(match: SafetyRuleMatch, risk_score: int) -> str:
    if match.escalation == EscalationTeam.emergency:
        return "Rispondere con calma e priorità alla sicurezza: luogo pubblico o persone vicine, 112 se il pericolo è immediato, persona fidata se possibile."
    if match.category == TicketCategory.out_of_scope:
        return "Spiegare che il portale può aiutare solo con ascolto, orientamento e sicurezza in situazioni di violenza, stalking o disagio collegato."
    if match.escalation == EscalationTeam.anti_violence_center:
        return "Accogliere senza giudicare e orientare verso 1522 o centro antiviolenza per valutare un piano di sicurezza."
    if match.escalation == EscalationTeam.legal_desk:
        return "Dare orientamento generale e suggerire supporto legale qualificato, senza produrre consulenza legale specifica."
    if match.escalation == EscalationTeam.evidence_collection:
        return "Suggerire raccolta sicura e ordinata dei materiali e confronto con un servizio qualificato prima di agire."
    if match.escalation == EscalationTeam.minors_protection:
        return "Trattare la presenza di minori come fattore di rischio e orientare verso 1522, servizi competenti e rete sicura."
    if match.escalation == EscalationTeam.social_services:
        return "Orientare verso centro antiviolenza, 1522 e servizi territoriali per bisogni pratici, economici o abitativi."
    if match.escalation == EscalationTeam.psychological_support:
        return "Validare il vissuto e suggerire persona fidata, supporto psicologico o ascolto qualificato; se il rischio cresce, 112."
    return "Offrire ascolto e un prossimo passo prudente, rispettando tempi e privacy della persona."


def _ticket_text(ticket: TicketCreate) -> str:
    return " ".join(
        [
            ticket.title,
            ticket.description,
            ticket.business_impact,
            ticket.technical_area,
        ]
    )


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(_normalize(needle) in text for needle in needles)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _is_minor_self_report(normalized: str) -> bool:
    if _contains_any(
        normalized,
        [
            "sono minorenne",
            "sono una minorenne",
            "sono un minorenne",
            "ho meno di 18 anni",
            "ho quasi 18 anni",
        ],
    ):
        return True

    if re.search(r"\bho\s+(?:gia\s+|già\s+)?(1[0-7]|[6-9])\s+anni\b", normalized):
        return True

    if re.search(r"\b(?:sono|sono una ragazza|sono un ragazzo|sono una persona)\s+di\s+(1[0-7]|[6-9])\s+anni\b", normalized):
        return True

    return any(
        f"ho {age_word} anni" in normalized
        for age_word in [
            "sei",
            "sette",
            "otto",
            "nove",
            "dieci",
            "undici",
            "dodici",
            "tredici",
            "quattordici",
            "quindici",
            "sedici",
            "diciassette",
        ]
    )
