import asyncio
import logging
import os
import secrets
import threading
from contextlib import asynccontextmanager
from time import monotonic

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.ai_providers import MockRosaSegnaleTriageProvider, get_triage_provider
from app.assistant_provider import answer_with_assistant
from app.knowledge import (
    answer_from_chunks,
    blocked_answer,
    chunk_text,
    evaluate_chat_policy,
    retrieve_chunks,
)
from app.honeypot import client_ip, inspect_request
from app.models import (
    Alert,
    AlertCreate,
    AlertStatus,
    AlertUpdate,
    ChunkPreviewRequest,
    ChunkPreviewResponse,
    DashboardKpis,
    HealthResponse,
    HoneypotEvent,
    RagAnswerRequest,
    RagAnswerResponse,
    Ticket,
    TicketCreate,
    TicketFollowUpUpdate,
    TriageResult,
    WeeklyReportResponse,
)
from app.repository import (
    create_alert,
    create_honeypot_event,
    create_ticket,
    generate_weekly_report,
    get_dashboard_kpis,
    init_db,
    list_alerts,
    list_honeypot_events,
    list_tickets,
    seed_sample_tickets,
    update_alert_status,
    update_ticket_follow_up,
)
from app.report_scheduler import weekly_report_loop


APP_VERSION = "0.1.0"
AI_PROVIDER_NAME = os.getenv("AI_PROVIDER", "mock")
provider = get_triage_provider(AI_PROVIDER_NAME)
internal_security = HTTPBasic(auto_error=False)

# L'assistente e' la parte PUBBLICA del prodotto (chi cerca aiuto non fa login),
# quindi non e' protetto da autenticazione: l'unico freno e' questo, e deve
# funzionare davvero perche' ogni risposta costa.
_ASSISTANT_RATE: dict[str, float] = {}
_ASSISTANT_RATE_SECONDS = int(os.getenv("ASSISTANT_RATE_LIMIT_SECONDS", "5"))
# Tetto anti-crescita: senza, la mappa aumenta a ogni IP nuovo e non cala mai.
_ASSISTANT_RATE_MAX_VOCI = 10_000
# Le route sincrone girano su piu' thread: i contatori vanno protetti.
_LIMITI_LOCK = threading.Lock()

# Freno GLOBALE alla spesa (come il rateLimiter del companion di NeuroDesk): il
# freno per IP non basta contro richieste da tanti indirizzi. A differenza di
# NeuroDesk qui, superato il tetto, NON si rifiuta: si risponde con le fonti locali,
# che non costano nulla. Chi chiede aiuto deve ricevere comunque 112 e 1522.
_AI_MAX_AL_MINUTO = int(os.getenv("AI_MAX_REQUESTS_PER_MINUTE", "200"))
_ai_finestra = {"inizio": 0.0, "conteggio": 0}

# Tentativi sull'area interna (come LoginRateLimiter di NeuroDesk). Il blocco e' per
# IP, non per utente: altrimenti chiunque potrebbe tenere fuori gli operatori.
_LOGIN_MAX_FALLIMENTI = 8
_LOGIN_FINESTRA_SECONDI = 15 * 60
_LOGIN_BLOCCO_SECONDI = 15 * 60
_LOGIN_MAX_VOCI = 10_000
_login_tentativi: dict[str, dict[str, float]] = {}

# Piu' del necessario per ogni richiesta valida: il testo piu' lungo ammesso e'
# l'anteprima della base di conoscenza, 20.000 caratteri.
_MAX_BODY_BYTES = 1024 * 1024
_METODI_SICURI = {"GET", "HEAD", "OPTIONS"}
_HEADER_SICUREZZA = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=(), usb=()",
    "Cache-Control": "no-store",
}


def _modalita_rigida() -> bool:
    return (os.getenv("SECURITY_STRICT") or "").strip().lower() in {"1", "true", "si", "yes"}


def controlla_segreti() -> None:
    """Come SecurityGuard di NeuroDesk: segnala i segreti deboli all'avvio.

    In locale avvisa. Con SECURITY_STRICT=true, come nell'immagine Docker, impedisce
    l'avvio: cosi' non si va online con valori indovinabili.
    """
    password = (os.getenv("INTERNAL_AUTH_PASSWORD") or "").strip()
    problemi = []
    if len(password) < 12 or "replace_with" in password:
        problemi.append("INTERNAL_AUTH_PASSWORD assente o sotto i 12 caratteri")
    if len((os.getenv("HONEYPOT_HASH_SALT") or "").strip()) < 32:
        problemi.append("HONEYPOT_HASH_SALT assente o sotto i 32 caratteri")
    if _auth_disattivata():
        problemi.append("INTERNAL_AUTH_DISABLED attiva")
    if not problemi:
        return
    messaggio = "Sicurezza: " + "; ".join(problemi)
    if _modalita_rigida():
        raise RuntimeError(messaggio)
    logging.warning(messaggio)


def _budget_ai_disponibile(adesso: float) -> bool:
    with _LIMITI_LOCK:
        if adesso - _ai_finestra["inizio"] >= 60:
            _ai_finestra["inizio"] = adesso
            _ai_finestra["conteggio"] = 0
        if _ai_finestra["conteggio"] >= _AI_MAX_AL_MINUTO:
            return False
        _ai_finestra["conteggio"] += 1
        return True


def _login_bloccato(ip: str, adesso: float) -> bool:
    with _LIMITI_LOCK:
        voce = _login_tentativi.get(ip)
        return voce is not None and voce["bloccato_fino"] > adesso


def _registra_fallimento_login(ip: str, adesso: float) -> None:
    with _LIMITI_LOCK:
        if len(_login_tentativi) > _LOGIN_MAX_VOCI:
            for chiave, voce in list(_login_tentativi.items()):
                if voce["bloccato_fino"] <= adesso and adesso - voce["inizio"] > _LOGIN_FINESTRA_SECONDI:
                    del _login_tentativi[chiave]
        voce = _login_tentativi.setdefault(ip, {"fallimenti": 0, "inizio": adesso, "bloccato_fino": 0.0})
        if adesso - voce["inizio"] > _LOGIN_FINESTRA_SECONDI:
            voce["fallimenti"] = 0
            voce["inizio"] = adesso
        voce["fallimenti"] += 1
        if voce["fallimenti"] >= _LOGIN_MAX_FALLIMENTI:
            voce["bloccato_fino"] = adesso + _LOGIN_BLOCCO_SECONDI
            voce["fallimenti"] = 0
            voce["inizio"] = adesso


def _purga_scaduti(adesso: float) -> None:
    scaduti = [ip for ip, quando in _ASSISTANT_RATE.items()
               if adesso - quando > _ASSISTANT_RATE_SECONDS]
    for ip in scaduti:
        del _ASSISTANT_RATE[ip]


# Origini di SVILUPPO. Valgono solo finche' nessuno ha configurato le proprie:
# tenerle sempre ammesse significherebbe che, in produzione, una pagina servita
# su quella porta sulla macchina di un operatore gia' autenticato puo' leggere
# le segnalazioni cross-origin (le credenziali Basic il browser le rimanda da se',
# e qui allow_credentials e' True).
ORIGINI_SVILUPPO = ["http://localhost:5173", "http://127.0.0.1:5173"]


def allowed_cors_origins() -> list[str]:
    configurate = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    ]
    # Se ne hai configurate, quelle e basta: e' il caso della produzione.
    return configurate or list(ORIGINI_SVILUPPO)


_ORIGINI_AMMESSE = set(allowed_cors_origins())


@asynccontextmanager
async def lifespan(app: FastAPI):
    controlla_segreti()
    init_db()
    report_task = asyncio.create_task(weekly_report_loop())
    app.state.weekly_report_task = report_task

    yield
    report_task.cancel()
    try:
        await report_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Rosa Segnale API",
    version=APP_VERSION,
    description="Prototipo didattico di ascolto, triage, base di conoscenza AI e reportistica per segnalazioni sensibili.",
    lifespan=lifespan,
    # La documentazione API resta per la demo locale, non per chi va online.
    docs_url=None if _modalita_rigida() else "/docs",
    redoc_url=None if _modalita_rigida() else "/redoc",
    openapi_url=None if _modalita_rigida() else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def errori_validazione_anonimi(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Come ErroriAnonimi di NeuroDesk: si dice cosa non va, senza ripetere il testo
    # ricevuto. Quello predefinito lo rimanda indietro, e con NaN o Infinity nel JSON
    # il rimando stesso andava in errore 500.
    return JSONResponse(
        status_code=422,
        content={"detail": [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]},
    )


@app.exception_handler(OverflowError)
@app.exception_handler(UnicodeEncodeError)
async def valori_non_memorizzabili(_: Request, __: Exception) -> JSONResponse:
    # Numeri oltre i 64 bit e caratteri Unicode spezzati passano la validazione, ma
    # SQLite e la risposta JSON non li sanno trattare: sono input sbagliati, non guasti.
    return JSONResponse(status_code=422, content={"detail": "Valore non valido."})


@app.middleware("http")
async def protezioni_http(request: Request, call_next):
    if request.method not in _METODI_SICURI:
        # Difesa CSRF: un sito esterno puo' inviare un form senza preflight, e il
        # browser ci aggiunge le credenziali Basic che ricorda. L'Origin non lo decide lui.
        origine = request.headers.get("origin")
        if origine and origine not in _ORIGINI_AMMESSE:
            return JSONResponse(status_code=403, content={"detail": "Origine non ammessa."})

        lunghezza = request.headers.get("content-length")
        if lunghezza is None and request.headers.get("transfer-encoding"):
            return JSONResponse(status_code=411, content={"detail": "Lunghezza richiesta."})
        if lunghezza is not None and (not lunghezza.isdigit() or int(lunghezza) > _MAX_BODY_BYTES):
            return JSONResponse(status_code=413, content={"detail": "Richiesta troppo grande."})

    response = await call_next(request)
    for nome, valore in _HEADER_SICUREZZA.items():
        response.headers.setdefault(nome, valore)
    return response


@app.middleware("http")
async def honeypot_monitor(request: Request, call_next):
    match = inspect_request(request)

    if match is not None:
        create_honeypot_event(
            path=match.path,
            method=match.method,
            reason=match.reason,
            risk_score=match.risk_score,
            ip_hash=match.ip_hash,
            user_agent=match.user_agent,
            query_present=match.query_present,
        )

    return await call_next(request)


# Interruttore ESPLICITO per lo sviluppo locale. Deve essere una scelta scritta,
# non l'effetto di una variabile dimenticata: prima, se le credenziali mancavano,
# l'area interna si apriva da sola e le segnalazioni erano di chiunque passasse.
# Stesso principio di neurodesk.security.strict: di base si fallisce CHIUSI.
def _auth_disattivata() -> bool:
    return (os.getenv("INTERNAL_AUTH_DISABLED") or "").strip().lower() in {"1", "true", "si", "yes"}


def require_internal_auth(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(internal_security),
) -> None:
    if _auth_disattivata():
        return None

    username = (os.getenv("INTERNAL_AUTH_USERNAME") or "").strip()
    password = (os.getenv("INTERNAL_AUTH_PASSWORD") or "").strip()

    # Credenziali assenti = servizio non configurato, non "porta aperta".
    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail=(
                "Area interna non configurata: imposta INTERNAL_AUTH_USERNAME e "
                "INTERNAL_AUTH_PASSWORD. Solo in sviluppo locale puoi usare "
                "INTERNAL_AUTH_DISABLED=true."
            ),
        )

    ip = client_ip(request)
    adesso = monotonic()
    if _login_bloccato(ip, adesso):
        raise HTTPException(
            status_code=429,
            detail="Troppi tentativi. Riprova tra qualche minuto.",
            headers={"Retry-After": str(_LOGIN_BLOCCO_SECONDI)},
        )

    authenticated = False
    if credentials is not None:
        # Entrambi i confronti sempre: con "and" il tempo di risposta rivela se
        # l'utente e' giusto. In byte, perche' compare_digest rifiuta i testi non ASCII.
        utente_ok = secrets.compare_digest(credentials.username.encode(), username.encode())
        password_ok = secrets.compare_digest(credentials.password.encode(), password.encode())
        authenticated = utente_ok and password_ok

        if authenticated:
            with _LIMITI_LOCK:
                _login_tentativi.pop(ip, None)
        else:
            # Solo i tentativi veri: aprire la pagina senza credenziali non conta.
            _registra_fallimento_login(ip, adesso)

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Autenticazione richiesta per l'area interna.",
            headers={"WWW-Authenticate": "Basic"},
        )

    return None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        provider=provider.name,
        database="sqlite",
        version=APP_VERSION,
    )


@app.post("/triage/preview", response_model=TriageResult)
def preview_triage(ticket: TicketCreate, _: None = Depends(require_internal_auth)) -> TriageResult:
    return provider.classify(ticket)


@app.post("/tickets", response_model=Ticket)
def submit_ticket(ticket: TicketCreate, _: None = Depends(require_internal_auth)) -> Ticket:
    result = provider.classify(ticket)
    return create_ticket(ticket, result)


@app.get("/tickets", response_model=list[Ticket])
def get_tickets(_: None = Depends(require_internal_auth)) -> list[Ticket]:
    return list_tickets()


@app.post("/alerts", response_model=Alert)
def submit_alert(alert: AlertCreate, _: None = Depends(require_internal_auth)) -> Alert:
    return create_alert(alert)


@app.get("/alerts", response_model=list[Alert])
def get_alerts(_: None = Depends(require_internal_auth)) -> list[Alert]:
    return list_alerts()


@app.get("/security/honeypot-events", response_model=list[HoneypotEvent])
def get_honeypot_events(_: None = Depends(require_internal_auth)) -> list[HoneypotEvent]:
    return list_honeypot_events()


@app.patch("/alerts/{alert_id}", response_model=Alert)
def patch_alert(
    alert_id: int,
    update: AlertUpdate,
    _: None = Depends(require_internal_auth),
) -> Alert:
    alert = update_alert_status(
        alert_id=alert_id,
        status=update.status,
        operator_label=update.operator_label,
        internal_note=update.internal_note,
    )

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert non trovato.")

    return alert


@app.patch("/alerts/{alert_id}/take", response_model=Alert)
def take_alert(alert_id: int, _: None = Depends(require_internal_auth)) -> Alert:
    alert = update_alert_status(alert_id=alert_id, status=AlertStatus.in_progress)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert non trovato.")

    return alert


@app.patch("/alerts/{alert_id}/close", response_model=Alert)
def close_alert(alert_id: int, _: None = Depends(require_internal_auth)) -> Alert:
    alert = update_alert_status(alert_id=alert_id, status=AlertStatus.closed)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert non trovato.")

    return alert


@app.post("/sample-data/seed", response_model=list[Ticket])
def seed_sample_data(_: None = Depends(require_internal_auth)) -> list[Ticket]:
    sample_provider = MockRosaSegnaleTriageProvider()
    return seed_sample_tickets(sample_provider.classify)


@app.patch("/tickets/{ticket_id}/follow-up", response_model=Ticket)
def update_follow_up(
    ticket_id: int,
    update: TicketFollowUpUpdate,
    _: None = Depends(require_internal_auth),
) -> Ticket:
    ticket = update_ticket_follow_up(ticket_id, update)

    if ticket is None:
        raise HTTPException(status_code=404, detail="Segnalazione non trovata.")

    return ticket


@app.get("/dashboard", response_model=DashboardKpis)
def dashboard(_: None = Depends(require_internal_auth)) -> DashboardKpis:
    return get_dashboard_kpis()


@app.post("/knowledge/chunks/preview", response_model=ChunkPreviewResponse)
def preview_chunks(
    request: ChunkPreviewRequest,
    _: None = Depends(require_internal_auth),
) -> ChunkPreviewResponse:
    chunks = chunk_text(
        source_name=request.source_name,
        text=request.text,
        max_words=request.max_words,
        overlap_words=request.overlap_words,
    )

    return ChunkPreviewResponse(
        source_name=request.source_name,
        chunk_count=len(chunks),
        chunks=chunks,
    )


@app.post("/assistant/answer", response_model=RagAnswerResponse)
def answer_with_rag(body: RagAnswerRequest, http_request: Request) -> RagAnswerResponse:
    ip = client_ip(http_request)
    now = monotonic()
    with _LIMITI_LOCK:
        if len(_ASSISTANT_RATE) > _ASSISTANT_RATE_MAX_VOCI:
            _purga_scaduti(now)
        if now - _ASSISTANT_RATE.get(ip, 0.0) < _ASSISTANT_RATE_SECONDS:
            raise HTTPException(status_code=429, detail="Troppe richieste. Attendi qualche secondo e riprova.")
        _ASSISTANT_RATE[ip] = now

    policy_reason = evaluate_chat_policy(body.question)

    if policy_reason:
        return RagAnswerResponse(
            question=body.question,
            answer=blocked_answer(policy_reason),
            retrieved_chunks=[],
            provider="local-chat-policy-v1",
            blocked=True,
            policy_reason=policy_reason,
        )

    chunks = retrieve_chunks(body.question, body.top_k)
    if _budget_ai_disponibile(now):
        answer, answer_provider = answer_with_assistant(body.question, chunks)
    else:
        answer, answer_provider = answer_from_chunks(body.question, chunks), "local-rag-keyword-v1"

    return RagAnswerResponse(
        question=body.question,
        answer=answer,
        retrieved_chunks=chunks,
        provider=answer_provider,
    )


@app.get("/reports/weekly", response_model=WeeklyReportResponse)
def weekly_report(_: None = Depends(require_internal_auth)) -> WeeklyReportResponse:
    return generate_weekly_report()
