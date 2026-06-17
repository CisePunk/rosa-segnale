import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models import (
    Alert,
    AlertCreate,
    AlertSource,
    AlertStatus,
    DashboardKpis,
    HoneypotEvent,
    OperationalArea,
    Ticket,
    TicketCreate,
    TicketFollowUpUpdate,
    TriageResult,
    WeeklyReportResponse,
)


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
                operational_area TEXT NOT NULL DEFAULT 'Ascolto e orientamento',
                human_handoff INTEGER NOT NULL DEFAULT 0,
                suspected_misuse INTEGER NOT NULL DEFAULT 0,
                emotional_tone TEXT NOT NULL DEFAULT 'Non determinato',
                urgency_confidence REAL NOT NULL DEFAULT 0,
                misuse_confidence REAL NOT NULL DEFAULT 0,
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
        _ensure_column(connection, "tickets", "operational_area", "TEXT NOT NULL DEFAULT 'Ascolto e orientamento'")
        _ensure_column(connection, "tickets", "human_handoff", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(connection, "tickets", "suspected_misuse", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(connection, "tickets", "emotional_tone", "TEXT NOT NULL DEFAULT 'Non determinato'")
        _ensure_column(connection, "tickets", "urgency_confidence", "REAL NOT NULL DEFAULT 0")
        _ensure_column(connection, "tickets", "misuse_confidence", "REAL NOT NULL DEFAULT 0")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                operational_area TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Nuovo',
                operator_label TEXT NOT NULL DEFAULT '',
                internal_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                taken_at TEXT,
                closed_at TEXT,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS honeypot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                reason TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                ip_hash TEXT NOT NULL,
                user_agent TEXT NOT NULL DEFAULT '',
                query_present INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


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
                operational_area,
                human_handoff,
                suspected_misuse,
                emotional_tone,
                urgency_confidence,
                misuse_confidence,
                recommendation,
                rationale,
                provider
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                result.operational_area.value,
                int(result.human_handoff),
                int(result.suspected_misuse),
                result.emotional_tone,
                result.urgency_confidence,
                result.misuse_confidence,
                result.recommendation,
                result.rationale,
                result.provider,
            ),
        )

        row = connection.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        created_ticket = _row_to_ticket(row)
        if result.human_handoff and not result.suspected_misuse:
            _create_alert_with_connection(
                connection,
                AlertCreate(
                    ticket_id=created_ticket.id,
                    source=AlertSource.ticket,
                    title=created_ticket.title,
                    summary=result.recommendation,
                    risk_score=result.risk_score,
                    operational_area=result.operational_area,
                ),
            )

    return created_ticket


def create_alert(alert: AlertCreate) -> Alert:
    with get_connection() as connection:
        return _create_alert_with_connection(connection, alert)


def _create_alert_with_connection(connection: sqlite3.Connection, alert: AlertCreate) -> Alert:
    cursor = connection.execute(
        """
        INSERT INTO alerts (
            ticket_id,
            source,
            title,
            summary,
            risk_score,
            operational_area
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            alert.ticket_id,
            alert.source.value,
            alert.title,
            alert.summary,
            alert.risk_score,
            alert.operational_area.value,
        ),
    )
    row = connection.execute(
        "SELECT * FROM alerts WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return _row_to_alert(row)


def list_alerts() -> list[Alert]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM alerts
            ORDER BY
                CASE status
                    WHEN 'Nuovo' THEN 0
                    WHEN 'In carico' THEN 1
                    ELSE 2
                END,
                risk_score DESC,
                created_at DESC,
                id DESC
            """
        ).fetchall()

    return [_row_to_alert(row) for row in rows]


def create_honeypot_event(
    *,
    path: str,
    method: str,
    reason: str,
    risk_score: int,
    ip_hash: str,
    user_agent: str = "",
    query_present: bool = False,
) -> HoneypotEvent:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO honeypot_events (
                path,
                method,
                reason,
                risk_score,
                ip_hash,
                user_agent,
                query_present
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                path,
                method,
                reason,
                risk_score,
                ip_hash,
                user_agent,
                int(query_present),
            ),
        )
        row = connection.execute(
            "SELECT * FROM honeypot_events WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return _row_to_honeypot_event(row)


def list_honeypot_events(limit: int = 50) -> list[HoneypotEvent]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM honeypot_events
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_row_to_honeypot_event(row) for row in rows]


def update_alert_status(alert_id: int, status: AlertStatus, operator_label: str = "", internal_note: str = "") -> Alert | None:
    timestamp_field = "taken_at" if status == AlertStatus.in_progress else "closed_at" if status == AlertStatus.closed else None
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    with get_connection() as connection:
        if timestamp_field:
            connection.execute(
                f"""
                UPDATE alerts
                SET status = ?, operator_label = ?, internal_note = ?, {timestamp_field} = COALESCE({timestamp_field}, ?)
                WHERE id = ?
                """,
                (status.value, operator_label, internal_note, now, alert_id),
            )
        else:
            connection.execute(
                """
                UPDATE alerts
                SET status = ?, operator_label = ?, internal_note = ?
                WHERE id = ?
                """,
                (status.value, operator_label, internal_note, alert_id),
            )

        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

    return _row_to_alert(row) if row else None


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
    operational_area_counts = _count_by(tickets, "operational_area")
    average_risk = sum(ticket.risk_score for ticket in tickets) / total if total else 0
    high_risk = len([ticket for ticket in tickets if ticket.risk_score >= 4])

    return DashboardKpis(
        total_tickets=total,
        average_risk_score=round(average_risk, 2),
        priority_counts=priority_counts,
        category_counts=category_counts,
        escalation_counts=escalation_counts,
        operational_area_counts=operational_area_counts,
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
    operational_area_counts = _count_by(tickets, "operational_area")

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
            f"- Distribuzione aree operative: {_format_counts(operational_area_counts)}",
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
    data = dict(row)
    data["human_handoff"] = bool(data.get("human_handoff", False))
    data["suspected_misuse"] = bool(data.get("suspected_misuse", False))
    return Ticket(**data)


def _row_to_alert(row: sqlite3.Row) -> Alert:
    return Alert(**dict(row))


def _row_to_honeypot_event(row: sqlite3.Row) -> HoneypotEvent:
    data = dict(row)
    data["query_present"] = bool(data.get("query_present", False))
    return HoneypotEvent(**data)


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
