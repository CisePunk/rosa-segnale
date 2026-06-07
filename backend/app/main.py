import os
import asyncio
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
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
from app.models import (
    ChunkPreviewRequest,
    ChunkPreviewResponse,
    DashboardKpis,
    HealthResponse,
    RagAnswerRequest,
    RagAnswerResponse,
    Ticket,
    TicketCreate,
    TicketFollowUpUpdate,
    TriageResult,
    WeeklyReportResponse,
)
from app.repository import (
    create_ticket,
    generate_weekly_report,
    get_dashboard_kpis,
    init_db,
    list_tickets,
    seed_sample_tickets,
    update_ticket_follow_up,
)
from app.report_scheduler import weekly_report_loop


APP_VERSION = "0.1.0"
AI_PROVIDER_NAME = os.getenv("AI_PROVIDER", "mock")
provider = get_triage_provider(AI_PROVIDER_NAME)
internal_security = HTTPBasic(auto_error=False)


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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_internal_auth(
    credentials: HTTPBasicCredentials | None = Depends(internal_security),
) -> None:
    username = os.getenv("INTERNAL_AUTH_USERNAME")
    password = os.getenv("INTERNAL_AUTH_PASSWORD")

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
def answer_with_rag(request: RagAnswerRequest) -> RagAnswerResponse:
    policy_reason = evaluate_chat_policy(request.question)

    if policy_reason:
        return RagAnswerResponse(
            question=request.question,
            answer=blocked_answer(policy_reason),
            retrieved_chunks=[],
            provider="local-chat-policy-v1",
            blocked=True,
            policy_reason=policy_reason,
        )

    chunks = retrieve_chunks(request.question, request.top_k)
    answer, answer_provider = answer_with_assistant(request.question, chunks)

    return RagAnswerResponse(
        question=request.question,
        answer=answer,
        retrieved_chunks=chunks,
        provider=answer_provider,
    )


@app.get("/reports/weekly", response_model=WeeklyReportResponse)
def weekly_report(_: None = Depends(require_internal_auth)) -> WeeklyReportResponse:
    return generate_weekly_report()
