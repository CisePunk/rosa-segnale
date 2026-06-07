import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models import DashboardKpis, Ticket, TicketCreate, TicketFollowUpUpdate, TriageResult, WeeklyReportResponse


DB_PATH = Path(os.getenv("TRIAGE_DB_PATH", Path(__file__).resolve().parent.parent / "triage.db"))


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                business_impact TEXT NOT NULL,
                technical_area TEXT NOT NULL,
                category TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                escalation TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                rationale TEXT NOT NULL,
                provider TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                follow_up_status TEXT NOT NULL DEFAULT 'Da valutare',
                internal_note TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _ensure_column(connection, "tickets", "follow_up_status", "TEXT NOT NULL DEFAULT 'Da valutare'")
        _ensure_column(connection, "tickets", "internal_note", "TEXT NOT NULL DEFAULT ''")


def create_ticket(ticket: TicketCreate, result: TriageResult) -> Ticket:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                title,
                description,
                priority,
                business_impact,
                technical_area,
                category,
                risk_score,
                escalation,
                recommendation,
                rationale,
                provider
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.title,
                ticket.description,
                ticket.priority.value,
                ticket.business_impact,
                ticket.technical_area,
                result.category.value,
                result.risk_score,
                result.escalation.value,
                result.recommendation,
                result.rationale,
                result.provider,
            ),
        )

        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _row_to_ticket(row)


def seed_sample_tickets(classify) -> list[Ticket]:
    if list_tickets():
        return list_tickets()

    samples = [
        TicketCreate(
            title="Paura a tornare a casa",
            description="Persona riferisce controllo del telefono, isolamento e paura a rientrare nell'abitazione.",
            priority="Alta",
            business_impact="Serve orientamento verso piano di sicurezza e risorse territoriali.",
            technical_area="Ascolto e sicurezza",
        ),
        TicketCreate(
            title="Messaggi e prove da conservare",
            description="Persona ha screenshot e registrazioni e chiede come comportarsi senza cancellare materiale utile.",
            priority="Media",
            business_impact="Serve indirizzamento a supporto qualificato per documentazione e tutela.",
            technical_area="Documentazione",
        ),
        TicketCreate(
            title="Presenza di figli minori",
            description="Persona segnala tensione domestica e paura per i figli presenti in casa.",
            priority="Critica",
            business_impact="Serve valutazione di rischio, rete sicura e coinvolgimento di servizi competenti.",
            technical_area="Minori e famiglia",
        ),
    ]

    for sample in samples:
        create_ticket(sample, classify(sample))

    return list_tickets()


def list_tickets() -> list[Ticket]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC, id DESC"
        ).fetchall()

    return [_row_to_ticket(row) for row in rows]


def update_ticket_follow_up(ticket_id: int, update: TicketFollowUpUpdate) -> Ticket | None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tickets
            SET follow_up_status = ?, internal_note = ?
            WHERE id = ?
            """,
            (update.follow_up_status, update.internal_note, ticket_id),
        )
        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    return _row_to_ticket(row) if row else None


def get_dashboard_kpis() -> DashboardKpis:
    tickets = list_tickets()
    total = len(tickets)

    priority_counts = _count_by(tickets, "priority")
    category_counts = _count_by(tickets, "category")
    escalation_counts = _count_by(tickets, "escalation")
    average_risk = sum(ticket.risk_score for ticket in tickets) / total if total else 0
    high_risk = len([ticket for ticket in tickets if ticket.risk_score >= 4])

    return DashboardKpis(
        total_tickets=total,
        average_risk_score=round(average_risk, 2),
        priority_counts=priority_counts,
        category_counts=category_counts,
        escalation_counts=escalation_counts,
        high_risk_tickets=high_risk,
    )


def generate_weekly_report(period_days: int = 7) -> WeeklyReportResponse:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=period_days)
    tickets = [
        ticket
        for ticket in list_tickets()
        if _parse_created_at(ticket.created_at) >= cutoff
    ]

    total = len(tickets)
    high_risk = len([ticket for ticket in tickets if ticket.risk_score >= 4])
    average_risk = sum(ticket.risk_score for ticket in tickets) / total if total else 0
    priority_counts = _count_by(tickets, "priority")
    category_counts = _count_by(tickets, "category")
    escalation_counts = _count_by(tickets, "escalation")

    summary = (
        f"{total} segnalazioni negli ultimi {period_days} giorni, "
        f"rischio medio {round(average_risk, 2)}, casi ad alto rischio {high_risk}."
    )

    markdown = "\n".join(
        [
            "# Report settimanale Rosa Segnale",
            "",
            f"Generato il: {now.isoformat()}",
            f"Periodo: ultimi {period_days} giorni",
            "",
            f"- Segnalazioni totali: {total}",
            f"- Rischio medio: {round(average_risk, 2)}",
            f"- Alto rischio: {high_risk}",
            f"- Distribuzione urgenza: {_format_counts(priority_counts)}",
            f"- Distribuzione categoria: {_format_counts(category_counts)}",
            f"- Distribuzione percorsi: {_format_counts(escalation_counts)}",
            "",
            "## Segnalazioni a rischio più alto",
            *[
                f"- Risk {ticket.risk_score}/5 | {_display_value(ticket.priority)} | "
                f"{_display_value(ticket.category)}: {ticket.title}"
                for ticket in sorted(tickets, key=lambda ticket: (-ticket.risk_score, ticket.created_at))[:5]
            ],
        ]
    )

    return WeeklyReportResponse(
        title="Report settimanale Rosa Segnale",
        generated_at=now.isoformat(),
        period_days=period_days,
        summary=summary,
        markdown=markdown,
    )


def _row_to_ticket(row: sqlite3.Row) -> Ticket:
    return Ticket(**dict(row))


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}

    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _count_by(tickets: list[Ticket], attribute: str) -> dict[str, int]:
    counts: dict[str, int] = {}

    for ticket in tickets:
        value = getattr(ticket, attribute)
        key = value.value if hasattr(value, "value") else str(value)
        counts[key] = counts.get(key, 0) + 1

    return counts


def _parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"

    return ", ".join(f"{key}: {value}" for key, value in counts.items())


def _display_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)
