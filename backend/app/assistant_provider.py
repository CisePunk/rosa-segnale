import os
import re

from app.knowledge import MAX_RAG_ANSWER_CHARS, answer_from_chunks
from app.models import RetrievedChunk


_OPENAI_CLIENT = None


def answer_with_assistant(question: str, chunks: list[RetrievedChunk]) -> tuple[str, str]:
    provider_name = os.getenv("AI_PROVIDER", "mock").lower()

    if provider_name != "openai" or not os.getenv("OPENAI_API_KEY"):
        return answer_from_chunks(question, chunks), "local-rag-keyword-v1"

    if not chunks and not _looks_like_support_request(question):
        return answer_from_chunks(question, chunks), "local-rag-no-context-v1"

    try:
        return _answer_with_openai(question, chunks), _openai_provider_name()
    except Exception:
        return answer_from_chunks(question, chunks), "local-rag-keyword-v1"


def _answer_with_openai(question: str, chunks: list[RetrievedChunk]) -> str:
    client = _get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "350"))

    context = _format_context(chunks)
    routing = _routing_context(question, chunks)
    prompt = f"""Sei l'assistente di Rosa Segnale, un prototipo didattico di ascolto e orientamento per segnalazioni sensibili legate a violenza, stalking, sicurezza personale o crisi emotiva.

Obiettivo:
- essere un punto di ascolto empatico, naturale e modulato, non un motore che ripete frasi standard;
- usare la knowledge base solo come bussola di indirizzamento immediato;
- rispondere come una persona attenta: riconosci il vissuto specifico, poi indica il passo più sicuro e concreto;
- distinguere tra ascolto/orientamento, ponte con persone reali e intervento immediato;
- nel follow-up, rispondi al messaggio nuovo e non ripetere la risposta precedente.

Regole di sicurezza:
- Rispondi in italiano.
- Non dire che il portale ha inviato denunce, soccorsi o richieste alle autorità.
- Non chiedere nomi, indirizzi precisi, numeri di telefono o altri dati identificativi non necessari.
- Non dare consulenza legale, medica o psicologica specialistica.
- Se c'e pericolo immediato, aggressione, inseguimento, minaccia, arma, impossibilita a uscire/parlare o rischio sanitario: indica subito il 112.
- In emergenza rispondi al massimo con 2 frasi brevi: sicurezza immediata, 112, luogo con altre persone se possibile.
- Se la persona potrebbe non poter telefonare o parlare, proponi formulazioni prudenti: uscire dalla schermata, raggiungere persone presenti, chiedere a qualcuno vicino di chiamare il 112, contattare 1522 con il canale praticabile quando e al sicuro.
- Se chiede di cancellare la chat o la cronologia, non bloccare: indica di chiudere subito la pagina o passare a una schermata neutra, poi cancellare cronologia/dati browser quando e al sicuro.
- Se dice di essere incinta o in gravidanza, trattalo come fattore di vulnerabilita e orienta verso 1522, centro antiviolenza e servizi sanitari qualificati; 112 se c'e pericolo, dolore o aggressione.
- Se chi scrive dice di essere minorenne o sotto i 18 anni, orienta verso un adulto sicuro, 112 in pericolo immediato, 1522 per violenza/stalking e 19696 Telefono Azzurro.
- Se scrive solo "non sono sola", trattalo come ambiguo e potenzialmente operativo: chiedi se la persona accanto e sicura o parte del rischio, senza aggiungere altre domande.
- Se parla di isolamento da famiglia, amiche o amici, trattalo come segnale di controllo e orienta verso 1522 o centro antiviolenza per un piano di sicurezza.
- Se parla di telefono tolto, telefono disponibile solo per poco tempo, impossibilita a scrivere/chiamare liberamente, spostamenti limitati, comunita/contesto chiuso o uscita solo per commissioni: riconosci controllo coercitivo e proponi un canale umano sicuro appena praticabile.
- Se parla di soldi controllati, impedimento a lavorare, dipendenza economica, bancomat/conto/spese controllate: riconosci possibile violenza economica e orienta verso persona reale, 1522 o centro antiviolenza.
- Se parla di insulti, urla, umiliazione, svalutazione, gaslighting o paura generata da parole: riconosci che anche violenza verbale e psicologica possono essere forme di violenza, senza pretendere prove fisiche.
- Se la persona scrive "non so se e violenza", "voglio capire", "forse esagero", non minimizzare: offri ascolto, nomina i segnali di controllo e proponi passaggio a una persona reale.
- Se il progetto dispone di presidio umano, la proposta standard deve essere: "Se vuoi, posso indirizzarti verso una persona reale del presidio"; non promettere disponibilita 24/7 se non e dichiarata.
- Se parla di aggressione fisica appena avvenuta, dolore, colpi, spinte, muro, ferite o malessere fisico: tratta la sicurezza e il possibile bisogno sanitario come priorita, indica 112 e un luogo con altre persone.
- Se la persona parla di violenza, stalking, controllo, paura di tornare a casa o bisogno di un piano di sicurezza: indica il 1522 e un centro antiviolenza.
- Se chiede prove, screenshot, registrazioni o denuncia: dai solo orientamento generale e suggerisci supporto legale qualificato/centro antiviolenza, senza scrivere atti legali.
- Se parla di autolesionismo o suicidio: invita a non restare sola e a contattare subito 112 o una persona fidata.
- Se l'indirizzamento indica 112, 1522, supporto legale, sanitario, minori o prove, devi nominarlo chiaramente nella risposta.
- Se il messaggio riguarda prove o screenshot, devi suggerire raccolta ordinata e confronto con supporto qualificato prima di cancellare, inoltrare o pubblicare materiale.
- La prima frase deve riconoscere il vissuto della persona; se c'e pericolo attuale, riconosci e passa subito alla sicurezza.
- Evita frasi paternaliste o automatiche come "rimani calma", "capisco", "capisco perfettamente", "mi dispiace molto sentire", "andrà tutto bene", "quello che descrivi va preso sul serio", "è fondamentale".
- Non iniziare con formule generiche: preferisci una frase specifica su quello che la persona ha scritto.
- Non riusare la stessa frase iniziale gia presente nel contesto della conversazione.
- Se la persona risponde "no", "non posso", "non conosco nessuno" o simili, adatta la risposta: proponi alternative concrete come entrare in un luogo pubblico aperto, parlare con personale presente, chiamare il 112 se c'e pericolo immediato, contattare 1522 anche via canali disponibili, evitare di tornare da sola nel luogo di rischio.
- Se la persona dice di non conoscere nessuno, non chiederle di nuovo se ha qualcuno. Non farla sentire in colpa per essere sola.
- Non usare parole leggere come "chiacchierare" in contesti di aggressione o pericolo.
- Non citare "RAG", "chunk", "fonte principale", "database" o punteggi.
- Non chiudere con un elenco burocratico se la persona sembra spaventata.
- Puoi fare al massimo una domanda di follow-up, solo se non rallenta la sicurezza immediata.
- Lunghezza: 4-7 frasi brevi, con tono umano.
- Per messaggi brevi o telefono controllato: usa 2-3 frasi brevi e una sola azione concreta.
- Se nel messaggio sono presenti righe di contesto conversazionale, usale solo per non perdere il filo; la risposta deve riguardare soprattutto il nuovo messaggio della persona.

CONTESTO_KB:
{context}

INDIRIZZAMENTO_DA_USARE:
{routing}

MESSAGGIO_UTENTE:
{question}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=max_output_tokens,
        temperature=0.75,
    )

    return _limit_answer(_polish_answer(response.output_text.strip(), question))


def _get_openai_client():
    global _OPENAI_CLIENT

    if _OPENAI_CLIENT is None:
        from openai import OpenAI

        _OPENAI_CLIENT = OpenAI()

    return _OPENAI_CLIENT


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "Nessun chunk specifico recuperato. Usa solo l'indirizzamento generale, senza inventare servizi o procedure."

    return "\n".join(
        f"- {chunk.source_name} #{chunk.chunk_index}: {chunk.text}" for chunk in chunks
    )


def _routing_context(question: str, chunks: list[RetrievedChunk]) -> str:
    normalized = question.lower()
    sources = {chunk.source_name for chunk in chunks}
    routes: list[str] = []

    if _contains_any(normalized, ["mi segue", "in pericolo", "minaccia", "sta arrivando", "sta tornando", "sta rientrando", "sta venendo", "fuori dalla porta", "non posso parlare", "non sono sola", "arma", "pistola", "coltello", "uccide", "ammazza", "ambulanza", "ferita", "sangue", "male fisico", "sbattuta", "sbattuto", "muro", "mi ha presa", "mi ha preso"]):
        routes.append("Priorita: sicurezza immediata. Indirizza al 112 se il pericolo e attuale o sanitario.")
    if _contains_any(normalized, ["violenza", "stalking", "controlla", "telefono", "paura a tornare", "casa", "pedina", "ci siamo lasciati", "separazione", "lasciato", "incinta", "gravidanza", "mi isola", "famiglia", "amiche", "amici", "tagliata fuori", "tagliato fuori"]) or "Numero antiviolenza 1522" in sources or "Stalking e controllo" in sources:
        routes.append("Orientamento: 1522 e centro antiviolenza per ascolto, stalking, controllo, piano di sicurezza o casa rifugio.")
    if _contains_any(normalized, ["telefono solo", "mi toglie il telefono", "non posso scrivere", "non posso chiamare", "rinchiusa", "rinchiuso", "comunita", "comunità", "commissioni", "commesse", "non posso uscire liberamente"]):
        routes.append("Ponte umano: possibile controllo coercitivo su telefono o spostamenti. Rispondi breve, non chiedere dati, proponi persona reale del presidio appena e sicuro.")
    if _contains_any(normalized, ["soldi", "bancomat", "conto", "spese", "non mi lascia lavorare", "dipendo economicamente", "mi controlla i soldi"]):
        routes.append("Ponte umano: possibile violenza economica. Riconosci il controllo materiale, proponi persona reale/1522/CAV e non ridurre il tema a problema pratico.")
    if _contains_any(normalized, ["mi insulta", "mi umilia", "urla addosso", "non valgo niente", "mi fa sentire pazza", "dice che sono pazza", "mi svaluta"]):
        routes.append("Ascolto: possibile violenza verbale o psicologica. Nomina il comportamento senza minimizzare per assenza di violenza fisica.")
    if _contains_any(normalized, ["non so se e violenza", "non so se è violenza", "forse esagero", "voglio capire", "sto esagerando"]):
        routes.append("Ascolto: la persona sta cercando cornice e conferma. Spiega segnali di controllo e proponi ponte con persona reale.")
    if _contains_any(normalized, ["non sono sola", "non sono solo"]):
        routes.append("Chiarimento breve: frase ambigua; chiedi solo se chi e presente e una persona sicura o parte del rischio.")
    if _contains_any(normalized, ["denuncia", "querela", "avvocato", "legale", "prove", "screenshot", "registrazioni"]) or "Documentazione e supporto legale" in sources:
        routes.append("Orientamento obbligatorio: supporto legale qualificato o centro antiviolenza; raccolta ordinata e sicura dei materiali; non scrivere atti o consulenze specifiche.")
    if _contains_any(normalized, ["figli", "bambini", "figlia", "figlio", "minori"]):
        routes.append("Orientamento: presenza di minori come fattore di rischio; 1522, servizi competenti e rete sicura.")
    if _contains_any(normalized, ["incinta", "gravidanza", "aspetto un figlio", "aspetto una figlia"]):
        routes.append("Orientamento: gravidanza come fattore di vulnerabilita; 1522, centro antiviolenza, servizi sanitari qualificati; 112 se pericolo o dolore.")
    if _looks_like_minor_self_report(normalized):
        routes.append("Orientamento: chi scrive potrebbe essere minorenne; adulto sicuro, 112 se pericolo immediato, 1522 e 19696 Telefono Azzurro.")
    if _contains_any(normalized, ["farmi del male", "non voglio vivere", "suicid", "autolesion"]):
        routes.append("Priorita: emergenza emotiva. Invita a non restare sola e a contattare subito 112 o persona fidata.")
    if _contains_any(normalized, ["cancella tutto", "cancella questa chat", "elimina tutto", "elimina questa chat", "cancellare la cronologia"]):
        routes.append("Orientamento: richiesta di cancellazione come segnale operativo; suggerisci chiusura pagina/schermata neutra e cancellazione cronologia quando e al sicuro.")

    if not routes:
        routes.append("Orientamento generale: ascolto, privacy minima, 112 per emergenza, 1522 per violenza o stalking.")

    return "\n".join(f"- {route}" for route in routes)


def _looks_like_support_request(question: str) -> bool:
    normalized = question.lower()
    return _contains_any(
        normalized,
        [
            "aiuto",
            "paura",
            "non posso parlare",
            "non sono sola",
            "violenza",
            "stalking",
            "segue",
            "seguendo",
            "controlla",
            "soldi",
            "bancomat",
            "spese",
            "mi isola",
            "tagliata fuori",
            "tagliato fuori",
            "telefono solo",
            "mi toglie il telefono",
            "rinchiusa",
            "rinchiuso",
            "comunita",
            "comunità",
            "mi insulta",
            "mi umilia",
            "urla addosso",
            "minaccia",
            "spaventata",
            "denuncia",
            "denunciare",
            "legale",
            "avvocato",
            "screenshot",
            "messaggi",
            "casa",
            "figli",
            "bambini",
            "incinta",
            "gravidanza",
            "minorenne",
            "ansia",
            "confusa",
            "sola",
            "crisi",
            "farmi del male",
            "non voglio vivere",
            "112",
            "1522",
            "youpol",
        ],
    )


def _contains_any(text: str, needles: list[str]) -> bool:
    normalized = " ".join(text.lower().split())
    return any(re.search(rf"\b{re.escape(needle)}\b", normalized) or needle in normalized for needle in needles)


def _openai_provider_name() -> str:
    return f"openai-rag/{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}"


def _limit_answer(answer: str) -> str:
    if len(answer) <= MAX_RAG_ANSWER_CHARS:
        return answer

    return answer[: MAX_RAG_ANSWER_CHARS - 3].rstrip() + "..."


def _polish_answer(answer: str, question: str) -> str:
    cleaned = answer.strip()
    normalized_question = question.lower()

    cleaned = re.sub(r"\b[EÈ] fondamentale\b", "La cosa più importante adesso è", cleaned)
    cleaned = re.sub(r"\b[Nn]on esitare a chiamare\b", "chiama", cleaned)
    cleaned = re.sub(r"\b[Nn]on esitare a\b", "Puoi", cleaned)
    cleaned = re.sub(r"\b[Tt]i invitiamo a\b", "Prova a", cleaned)
    cleaned = cleaned.replace("supporto e consigli", "supporto e orientamento")
    cleaned = cleaned.replace("chiacchierare", "parlare")

    generic_opening = re.match(
        r"^(capisco[^.!?]*[.!?]\s*|mi dispiace(?: molto)?[^.!?]*[.!?]\s*)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if generic_opening:
        cleaned = cleaned[generic_opening.end() :].lstrip()
        if _contains_any(normalized_question, ["non conosco nessuno", "non ho nessuno", "sono sola", "sono solo"]):
            cleaned = (
                "Anche senza una persona di fiducia vicina, puoi cercare subito un posto con altre persone. "
                f"{cleaned}"
            )
        elif _contains_any(normalized_question, ["sbattuta", "sbattuto", "muro", "mi ha presa", "mi ha preso"]):
            cleaned = f"Dopo un'aggressione, la tua sicurezza fisica viene prima di tutto. {cleaned}"

    return cleaned.strip()


def _looks_like_minor_self_report(normalized: str) -> bool:
    if _contains_any(normalized, ["sono minorenne", "sono una minorenne", "sono un minorenne", "ho meno di 18 anni", "ho quasi 18 anni"]):
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
