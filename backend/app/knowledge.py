import re

from app.models import KnowledgeChunk, RetrievedChunk

MAX_RAG_ANSWER_CHARS = 1100


DEFAULT_KNOWLEDGE_SOURCES = {
    "Emergenza immediata 112": """
    Se una persona è in pericolo immediato, teme un'aggressione, è stata minacciata,
    è seguita, inseguita, pedinata o non può mettersi al sicuro, il riferimento è il 112, numero unico
    europeo di emergenza. Il portale non invia richieste alle autorità e non sostituisce
    il pronto intervento. La risposta deve incoraggiare con calma a cercare un luogo
    sicuro, contattare una persona fidata se possibile e chiamare il 112.
    """,
    "Paura di rientrare e piano di sicurezza": """
    Se una persona ha paura a tornare a casa ma non descrive un pericolo immediato in corso,
    la risposta non deve inventare inseguimenti o aggressioni attuali. È utile orientare
    verso il 1522, un centro antiviolenza e la costruzione di un piano di sicurezza.
    La persona può valutare di non rientrare da sola, scegliere un luogo sicuro, contattare
    una risorsa qualificata o chiedere supporto a personale presente in un luogo pubblico.
    Se il pericolo diventa immediato, il riferimento resta il 112.
    """,
    "Numero antiviolenza 1522": """
    Il 1522 è il numero nazionale antiviolenza e stalking promosso dal Dipartimento
    per le Pari Opportunità. È gratuito, attivo 24 ore su 24 e permette di parlare
    con operatrici specializzate. Può orientare verso centri antiviolenza, case rifugio
    e servizi presenti sul territorio. È utile anche quando la persona non è pronta
    a denunciare ma ha bisogno di ascolto, informazioni e orientamento.
    """,
    "Stalking e controllo": """
    Segnali di stalking o controllo possono includere pedinamenti, messaggi insistenti,
    una persona che segue, controllo del telefono, geolocalizzazione, minacce, isolamento da amici o famiglia,
    accesso non autorizzato ad account personali o pressioni continue. La risposta deve
    validare la preoccupazione della persona, evitare giudizi e suggerire di contattare
    il 1522 o un centro antiviolenza per valutare un piano di sicurezza.
    """,
    "Documentazione e supporto legale": """
    Quando una persona parla di screenshot, messaggi, registrazioni, foto, prove,
    denuncia, querela o avvocato, la risposta deve orientare alla raccolta ordinata
    e sicura dei materiali senza dare consulenza legale specifica. È utile suggerire
    di confrontarsi con un centro antiviolenza, il 1522 o supporto legale qualificato
    prima di cancellare, inoltrare o pubblicare contenuti. Il portale non redige denunce
    e non stabilisce colpe.
    """,
    "Supporto medico e sanitario": """
    Se una persona riferisce ferite, aggressione fisica, dolore, rischio sanitario,
    bisogno di ambulanza o pronto soccorso, la risposta deve indicare subito il 112
    in caso di urgenza. Il portale non fornisce diagnosi o indicazioni mediche.
    """,
    "Supporto emotivo e autolesionismo": """
    Se una persona parla di autolesionismo, pensieri suicidari o crisi emotiva intensa,
    la risposta deve essere calma, diretta e non giudicante. In caso di pericolo
    immediato bisogna chiamare il 112. Per ascolto emotivo in Italia è disponibile
    Telefono Amico Italia al numero 02 2327 2327, tutti i giorni dalle 9 alle 24.
    È disponibile anche WhatsApp Amico al 324 011 72 52, tutti i giorni dalle 18
    alle 21. È importante invitare la persona a non restare sola e a contattare
    qualcuno di fidato.
    """,
    "Gravidanza e violenza": """
    La gravidanza o il periodo subito dopo il parto possono aumentare la vulnerabilità
    in situazioni di violenza, controllo o minacce. Se una persona dice di essere
    incinta, di aspettare un figlio o di avere paura durante la gravidanza, la risposta
    deve trattare il dato come fattore di rischio, orientare verso 1522, centro
    antiviolenza e servizi sanitari qualificati. In caso di pericolo immediato,
    dolore, aggressione o rischio sanitario, il riferimento resta il 112.
    """,
    "Utente minorenne": """
    Se chi scrive dice di essere minorenne, avere meno di 18 anni o cita un'età
    compatibile con la minore età, la risposta deve usare parole semplici, non chiedere
    dati identificativi e orientare verso un adulto sicuro, il 112 se c'è pericolo
    immediato, il 1522 per violenza o stalking e il 19696 di Telefono Azzurro per
    ascolto e tutela di bambini e adolescenti.
    """,
    "Riferimenti territoriali Sicilia": """
    Per orientamento territoriale in Sicilia non bisogna inventare contatti locali o
    numeri non verificati. Il riferimento stabile resta il 1522, che dispone della
    mappatura aggiornata dei centri antiviolenza e delle case rifugio. In Sicilia
    esistono servizi e centri in province come Palermo, Catania e Messina; per un uso
    operativo occorre verificare sempre la mappatura 1522, le pagine istituzionali
    regionali e reti qualificate come D.i.Re prima di indicare un centro specifico.
    """,
    "Privacy e minimizzazione": """
    In un portale che tratta segnalazioni sensibili è importante non chiedere dati
    identificativi non necessari. La persona dovrebbe evitare nomi completi, indirizzi
    precisi, numeri di telefono, codici fiscali o dati di terze persone se non sono
    indispensabili. Per un prototipo didattico devono essere usati dati fittizi o
    anonimizzati. I report dovrebbero privilegiare dati aggregati e non descrizioni
    personali complete.
    """,
}


BLOCKED_TERMS = [
    "api key",
    "bypass",
    "delete database",
    "drop table",
    "exfiltrate",
    "ignore previous",
    "ignore the previous",
    "jailbreak",
    "openai api key",
    "print environment",
    "reveal credentials",
    "reveal prompt",
    "show me credentials",
    "system prompt",
]


KEYBOARD_SPAM_TERMS = {
    "asdf",
    "asdfgh",
    "qwer",
    "qwerty",
    "zxcv",
    "lorem",
    "blah",
    "lol",
}


OPERATIONAL_TERMS = {
    "ai",
    "1522",
    "112",
    "aiuto",
    "violenza",
    "stalking",
    "autolesionismo",
    "emergenza",
    "paura",
    "casa",
    "segue",
    "seguire",
    "pedina",
    "uomo",
    "strada",
    "ascolto",
    "antiviolenza",
    "ambulanza",
    "ansia",
    "avvocato",
    "bambini",
    "centro",
    "capire",
    "confusa",
    "controlla",
    "denuncia",
    "denunciare",
    "dolore",
    "ferita",
    "figli",
    "foto",
    "gravidanza",
    "incinta",
    "legale",
    "minaccia",
    "minori",
    "minorenne",
    "persona",
    "prove",
    "registrazioni",
    "screenshot",
    "sicurezza",
    "situazione",
    "sola",
    "spaventata",
    "supporto",
    "telefono",
    "tornando",
    "tornare",
    "famiglia",
    "amiche",
    "amici",
    "isolata",
    "isolato",
    "isolamento",
    "sicilia",
    "siciliana",
    "palermo",
    "catania",
    "messina",
    "territorio",
    "vivere",
    "youpol",
}


SHORT_ALLOWED_MESSAGES = {
    "112",
    "1522",
    "19696",
    "aiuto",
    "aiuto per favore",
    "cancella tutto",
    "elimina tutto",
    "ho paura",
    "lui torna",
    "lui sta tornando",
    "non posso",
    "non posso parlare",
    "non sono sola",
    "sono incinta",
    "sono minorenne",
}


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "before",
    "con",
    "da",
    "di",
    "e",
    "for",
    "gli",
    "i",
    "il",
    "in",
    "is",
    "la",
    "le",
    "lo",
    "must",
    "of",
    "or",
    "per",
    "the",
    "to",
    "un",
    "una",
}


def evaluate_chat_policy(question: str) -> str | None:
    normalized = " ".join(question.lower().split())
    terms = _tokenize(question)

    if any(term in normalized for term in BLOCKED_TERMS):
        return "Blocked: possible prompt-injection, credential, or system-abuse attempt."

    if _looks_like_keyboard_spam(normalized, terms):
        return "Blocked: the message looks like random or playful input, not an operational question."

    if len(terms) < 2 and not _is_short_allowed_message(normalized, terms):
        return "Blocked: the message is too short or not meaningful enough for the operations assistant."

    if len(question) > 200 and not terms.intersection(OPERATIONAL_TERMS):
        return "Blocked: no clear operational context was found in the question."

    return None


def blocked_answer(policy_reason: str) -> str:
    return (
        f"{policy_reason} La chat è stata bloccata per questa richiesta. "
        "Scrivi solo messaggi pertinenti a richiesta di aiuto, orientamento, sicurezza personale o supporto."
    )[:MAX_RAG_ANSWER_CHARS]


def chunk_text(
    *,
    source_name: str,
    text: str,
    max_words: int = 120,
    overlap_words: int = 20,
) -> list[KnowledgeChunk]:
    words = text.split()

    if overlap_words >= max_words:
        raise ValueError("overlap_words must be lower than max_words")

    chunks: list[KnowledgeChunk] = []
    start = 0
    step = max_words - overlap_words

    while start < len(words):
        current_words = words[start : start + max_words]

        if not current_words:
            break

        chunks.append(
            KnowledgeChunk(
                source_name=source_name,
                chunk_index=len(chunks) + 1,
                text=" ".join(current_words),
                word_count=len(current_words),
            )
        )

        start += step

    return chunks


def retrieve_chunks(question: str, top_k: int = 3) -> list[RetrievedChunk]:
    normalized = " ".join(question.lower().split())
    query_terms = _expand_query_terms(normalized, _tokenize(question))
    chunks = _default_chunks()
    ranked_chunks: list[RetrievedChunk] = []

    for chunk in chunks:
        chunk_terms = _tokenize(chunk.text)
        score = sum(1 for term in query_terms if term in chunk_terms)
        score += _domain_boost(normalized, chunk.source_name)

        if score > 0:
            ranked_chunks.append(
                RetrievedChunk(
                    **chunk.model_dump(),
                    score=score,
                )
            )

    ranked_chunks.sort(key=lambda chunk: (-chunk.score, chunk.source_name, chunk.chunk_index))
    return ranked_chunks[:top_k]


def answer_from_chunks(question: str, chunks: list[RetrievedChunk]) -> str:
    # The order is intentional: urgent operational requests must be handled before
    # generic empty-context fallback or chunk-driven guidance can dilute them.
    if _is_deletion_help_request(question):
        return _limit_answer(
            "Se temi che qualcuno controlli lo schermo, chiudi subito questa pagina o passa a una schermata neutra. "
            "Quando sei al sicuro, puoi cancellare cronologia e dati del browser; se il pericolo è immediato usa il 112, mentre il 1522 può orientarti anche sui canali più adatti."
        )

    if _is_ambiguous_not_alone(question):
        return _limit_answer(
            "Quando scrivi che non sei sola, la cosa importante è capire se la persona accanto a te ti fa sentire al sicuro o è parte del rischio. "
            "Se non puoi parlare o c'è pericolo adesso, prova a spostarti verso altre persone e usa il 112 solo se puoi farlo senza esporti di più."
        )

    if not chunks:
        return _limit_answer(
            "Il tuo messaggio può essere sufficiente per chiedere aiuto: pensa prima a stare dove altre persone possano vederti. "
            "Se sei in pericolo immediato usa il 112; per violenza, stalking o paura puoi contattare il 1522 per orientamento specializzato."
        )

    main_chunk = chunks[0]
    guidance = _guidance_for_source(main_chunk.source_name, main_chunk.text)

    if _is_immediate_danger(question, main_chunk.source_name):
        if _needs_silent_safety(question):
            return _limit_answer(
                "Se non puoi parlare, prova prima a spostarti verso un luogo con altre persone o a passare a una schermata neutra. "
                "Se il pericolo è immediato, usa il 112 solo se puoi farlo senza esporti di più, oppure chiedi a qualcuno vicino di farlo."
            )

        return _limit_answer(
            "Ti credo: se c'è un pericolo adesso, pensa prima alla tua sicurezza e prova a raggiungere un luogo con altre persone. "
            "Se il pericolo è immediato usa il 112 o chiedi a chi è vicino a te di farlo."
        )

    if main_chunk.source_name == "Paura di rientrare e piano di sicurezza":
        return _limit_answer(
            f"La paura di rientrare merita un piano concreto prima di esporti a nuovi rischi. {guidance}"
        )

    return _limit_answer(
        f"Quello che scrivi merita attenzione e un passo prudente. {guidance} "
        "Se puoi, scegli un posto sicuro mentre cerchi orientamento."
    )


def _default_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []

    for source_name, text in DEFAULT_KNOWLEDGE_SOURCES.items():
        chunks.extend(
            chunk_text(
                source_name=source_name,
                text=text,
                max_words=70,
                overlap_words=12,
            )
        )

    return chunks


def _tokenize(text: str) -> set[str]:
    terms = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {term for term in terms if len(term) >= 2 and term not in STOP_WORDS}


def _expand_query_terms(normalized: str, terms: set[str]) -> set[str]:
    expanded = set(terms)

    if any(term in normalized for term in ["mi segue", "mi sta seguendo", "uomo che mi segue", "pedina", "insegue", "sta tornando", "sta rientrando", "sta venendo"]):
        expanded.update({"stalking", "pedinamenti", "seguita", "inseguita", "pedinata", "pericolo", "112"})

    if any(term in normalized for term in ["paura a tornare", "paura di tornare", "paura a rientrare", "non so a chi rivolgermi", "non posso tornare", "casa"]):
        expanded.update({"sicurezza", "piano", "1522", "antiviolenza", "rientrare"})

    if any(term in normalized for term in ["pericolo adesso", "sono in pericolo", "minaccia", "non posso uscire", "fuori dalla porta", "arma", "pistola", "coltello", "uccide", "sta tornando", "non posso parlare"]):
        expanded.update({"emergenza", "sicuro", "112", "antiviolenza"})

    if any(term in normalized for term in ["non sono sola", "non posso parlare"]):
        expanded.update({"emergenza", "sicuro", "112"})

    if _has_social_isolation_signal(normalized):
        expanded.update({"stalking", "controllo", "isolamento", "1522", "antiviolenza", "sicurezza"})

    if any(term in normalized for term in ["sicilia", "siciliana", "palermo", "catania", "messina", "territorio", "centro vicino"]):
        expanded.update({"sicilia", "territoriale", "1522", "mappatura", "antiviolenza", "centri"})

    if any(term in normalized for term in ["incinta", "gravidanza", "aspetto un figlio"]):
        expanded.update({"gravidanza", "sanitario", "1522", "antiviolenza", "112"})

    if _is_minor_self_report(normalized):
        expanded.update({"minorenne", "minori", "19696", "1522", "112"})

    if any(term in normalized for term in ["screenshot", "registrazioni", "prove", "denuncia", "querela", "avvocato", "legale"]):
        expanded.update({"supporto", "legale", "documentazione", "prove", "screenshot", "registrazioni", "1522"})

    if any(term in normalized for term in ["ambulanza", "ferita", "sangue", "pronto soccorso", "male fisico", "sbattuta", "sbattuto", "muro", "mi ha presa", "mi ha preso"]):
        expanded.update({"sanitario", "medico", "112", "urgenza"})

    if any(term in normalized for term in ["farmi del male", "non voglio vivere", "suicid", "autolesion", "pensieri brutti"]):
        expanded.update({"autolesionismo", "suicidari", "crisi", "emotiva", "112", "telefono", "amico"})

    return expanded


def _domain_boost(normalized: str, source_name: str) -> int:
    danger_signal = any(
        term in normalized
        for term in [
            "mi segue",
            "seguendo",
            "uomo che",
            "pedina",
            "insegue",
            "pericolo adesso",
            "sono in pericolo",
            "minaccia",
            "fuori dalla porta",
            "non posso uscire",
            "non posso parlare",
            "sta tornando",
            "sta rientrando",
            "sta venendo",
            "arma",
            "pistola",
            "coltello",
            "uccide",
        ]
    )
    safety_plan_signal = any(
        term in normalized
        for term in ["paura a tornare", "paura di tornare", "paura a rientrare", "non so a chi rivolgermi", "non posso tornare"]
    )
    privacy_signal = any(
        term in normalized
        for term in ["privacy", "dati", "telefono", "indirizzo", "codice fiscale", "nome completo"]
    )
    evidence_signal = any(
        term in normalized
        for term in ["screenshot", "registrazioni", "prove", "denuncia", "querela", "avvocato", "legale"]
    )
    medical_signal = any(
        term in normalized
        for term in ["ambulanza", "ferita", "sangue", "pronto soccorso", "male fisico", "sbattuta", "sbattuto", "muro", "mi ha presa", "mi ha preso"]
    )
    emotional_crisis_signal = any(
        term in normalized
        for term in ["farmi del male", "non voglio vivere", "suicid", "autolesion", "pensieri brutti"]
    )
    pregnancy_signal = any(
        term in normalized
        for term in ["incinta", "gravidanza", "aspetto un figlio", "aspetto una bambina", "aspetto un bambino"]
    )
    minor_self_signal = _is_minor_self_report(normalized)
    isolation_signal = _has_social_isolation_signal(normalized)
    sicily_signal = any(
        term in normalized
        for term in ["sicilia", "siciliana", "palermo", "catania", "messina", "territorio", "centro vicino"]
    )

    if source_name == "Emergenza immediata 112" and danger_signal:
        return 6
    if source_name == "Paura di rientrare e piano di sicurezza" and safety_plan_signal:
        return 8
    if source_name == "Numero antiviolenza 1522" and safety_plan_signal:
        return 5
    if source_name == "Supporto medico e sanitario" and medical_signal:
        return 7
    if source_name == "Supporto emotivo e autolesionismo" and emotional_crisis_signal:
        return 9
    if source_name == "Emergenza immediata 112" and emotional_crisis_signal:
        return 6
    if source_name == "Documentazione e supporto legale" and evidence_signal:
        return 7
    if source_name == "Gravidanza e violenza" and pregnancy_signal:
        return 8
    if source_name == "Utente minorenne" and minor_self_signal:
        return 8
    if source_name == "Stalking e controllo" and danger_signal:
        return 5
    if source_name == "Stalking e controllo" and isolation_signal:
        return 7
    if source_name == "Numero antiviolenza 1522" and isolation_signal:
        return 5
    if source_name == "Riferimenti territoriali Sicilia" and sicily_signal:
        return 8
    if source_name == "Numero antiviolenza 1522" and sicily_signal:
        return 4
    if source_name == "Numero antiviolenza 1522" and danger_signal:
        return 3
    if source_name == "Privacy e minimizzazione" and danger_signal and not privacy_signal:
        return -3
    if source_name == "Privacy e minimizzazione" and privacy_signal:
        return 5

    return 0


def _guidance_for_source(source_name: str, text: str) -> str:
    if source_name == "Emergenza immediata 112":
        return (
            "Se ti senti in pericolo adesso, prova a entrare in un luogo pubblico o vicino ad altre persone. "
            "Se il pericolo è immediato chiama il 112 o chiedi a chi è vicino a te di farlo."
        )
    if source_name == "Stalking e controllo":
        return (
            "Essere seguita o controllata è un segnale da prendere sul serio. Puoi contattare il 1522 per parlare con operatrici specializzate e valutare un piano di sicurezza."
        )
    if source_name == "Paura di rientrare e piano di sicurezza":
        return (
            "Se hai paura a tornare a casa, puoi contattare il 1522 o un centro antiviolenza per valutare un piano di sicurezza. "
            "Se puoi, evita di rientrare da sola e scegli un luogo sicuro mentre cerchi orientamento."
        )
    if source_name == "Gravidanza e violenza":
        return (
            "La gravidanza va considerata un fattore di vulnerabilità in più: puoi contattare il 1522, un centro antiviolenza o servizi sanitari qualificati per valutare un piano sicuro. "
            "Se c'è pericolo immediato, dolore o aggressione, usa il 112."
        )
    if source_name == "Utente minorenne":
        return (
            "Se hai meno di 18 anni, prova a raggiungere un adulto sicuro o un luogo con persone presenti. "
            "Se c'è pericolo immediato usa il 112; per ascolto e tutela puoi contattare anche il 19696 di Telefono Azzurro."
        )
    if source_name == "Supporto emotivo e autolesionismo":
        return (
            "Se temi di poterti fare del male, prova a non restare sola e contatta subito il 112 o una persona fidata. "
            "Per ascolto emotivo puoi contattare Telefono Amico Italia allo 02 2327 2327, tutti i giorni dalle 9 alle 24."
        )
    if source_name == "Riferimenti territoriali Sicilia":
        return (
            "Per trovare un riferimento territoriale in Sicilia, il canale più prudente è il 1522, che può orientare verso centri antiviolenza e case rifugio aggiornati. "
            "Prima di indicare un centro specifico bisogna verificare la mappatura ufficiale 1522 o pagine istituzionali aggiornate."
        )

    return _extract_first_sentence(text)


def _is_immediate_danger(question: str, source_name: str) -> bool:
    normalized = " ".join(question.lower().split())
    danger_signal = any(
        term in normalized
        for term in [
            "mi segue",
            "mi sta seguendo",
            "mi insegue",
            "uomo che mi segue",
            "sono in pericolo",
            "pericolo adesso",
            "minaccia",
            "mi sta aspettando",
            "sta arrivando",
            "sta tornando",
            "sta rientrando",
            "sta venendo",
            "fuori dalla porta",
            "non posso uscire",
            "non posso parlare",
            "non sono sola",
            "arma",
            "pistola",
            "coltello",
        ]
    )
    return source_name == "Emergenza immediata 112" and danger_signal


def _looks_like_keyboard_spam(normalized: str, terms: set[str]) -> bool:
    if any(term in normalized for term in KEYBOARD_SPAM_TERMS):
        return True

    compact = normalized.replace(" ", "")
    if _looks_like_reference_code(normalized, compact):
        return False

    if re.search(r"(.)\1{5,}", compact):
        return True

    if terms and len(terms) <= 3 and not terms.intersection(OPERATIONAL_TERMS):
        vowel_count = len(re.findall(r"[aeiou]", compact))
        return vowel_count / max(len(compact), 1) < 0.18

    return False


def _looks_like_reference_code(normalized: str, compact: str) -> bool:
    has_letter = bool(re.search(r"[a-z]", compact))
    has_digit = bool(re.search(r"\d", compact))
    return has_letter and has_digit and 6 <= len(compact) <= 24


def _is_short_allowed_message(normalized: str, terms: set[str]) -> bool:
    return normalized in SHORT_ALLOWED_MESSAGES or bool(terms.intersection(OPERATIONAL_TERMS))


def _is_deletion_help_request(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    return any(
        term in normalized
        for term in [
            "cancella questa chat",
            "cancella tutto",
            "elimina questa chat",
            "elimina tutto",
            "cancellare la conversazione",
            "cancellare la cronologia",
        ]
    )


def _is_ambiguous_not_alone(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    return normalized in {
        "non sono sola",
        "non sono solo",
        "non sono sola adesso",
        "non sono solo adesso",
        "non sono sola qui",
        "non sono solo qui",
    }


def _needs_silent_safety(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    return any(
        term in normalized
        for term in [
            "non posso parlare",
            "non posso chiamare",
            "non posso telefonare",
            "non posso farmi sentire",
            "non sono sola",
            "non sono solo",
        ]
    )


def _has_social_isolation_signal(normalized: str) -> bool:
    return any(
        term in normalized
        for term in [
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
        ]
    )


def _is_minor_self_report(normalized: str) -> bool:
    if any(
        term in normalized
        for term in [
            "sono minorenne",
            "sono una minorenne",
            "sono un minorenne",
            "ho meno di 18 anni",
            "ho quasi 18 anni",
        ]
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


def _extract_first_sentence(text: str) -> str:
    normalized = " ".join(text.split())
    sentence = normalized.split(".")[0].strip()
    return sentence + "." if sentence else normalized


def _limit_answer(answer: str) -> str:
    if len(answer) <= MAX_RAG_ANSWER_CHARS:
        return answer

    return answer[: MAX_RAG_ANSWER_CHARS - 3].rstrip() + "..."
