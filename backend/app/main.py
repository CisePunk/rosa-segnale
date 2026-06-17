import asyncio
import os
import secrets
from contextlib import asynccontextmanager
from time import monotonic

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.ai_providers import MockRosaSegnaleTriageProvider, get_triage_provider
from app.assistant_provider import answer_with_assistant
from app.knowledge import (
    blocked_answer,
    chunk_text,
    evaluate_chat_policy,
    retrieve_chunks,
)
from app.honeypot import inspect_request
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

_ASSISTANT_RATE: dict[str, float] = {}
_ASSISTANT_RATE_SECONDS = int(os.getenv("ASSISTANT_RATE_LIMIT_SECONDS", "5"))


def allowed_cors_origins() -> list[str]:
    default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    extra_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    ]
    return [*default_origins, *extra_origins]


@asynccontextmanager
async def lifespan(app: FastAPI):
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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def require_internal_auth(
    credentials: HTTPBasicCredentials | None = Depends(internal_security),
) -> None:
    username = (os.getenv("INTERNAL_AUTH_USERNAME") or "").strip()
    password = (os.getenv("INTERNAL_AUTH_PASSWORD") or "").strip()

    if not username and not password:
        return None

    if not username or not password:
        raise HTTPException(status_code=500, detail="Autenticazione interna non configurata correttamente.")

    authenticated = (
        credentials is not None
        and secrets.compare_digest(credentials.username, username)
        and secrets.compare_digest(credentials.password, password)
    )

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
    client_ip = http_request.client.host if http_request.client else "unknown"
    now = monotonic()
    if now - _ASSISTANT_RATE.get(client_ip, 0.0) < _ASSISTANT_RATE_SECONDS:
        raise HTTPException(status_code=429, detail="Troppe richieste. Attendi qualche secondo e riprova.")
    _ASSISTANT_RATE[client_ip] = now

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
    answer, answer_provider = answer_with_assistant(body.question, chunks)

    return RagAnswerResponse(
        question=body.question,
        answer=answer,
        retrieved_chunks=chunks,
        provider=answer_provider,
    )


@app.get("/reports/weekly", response_model=WeeklyReportResponse)
def weekly_report(_: None = Depends(require_internal_auth)) -> WeeklyReportResponse:
    return generate_weekly_report()
