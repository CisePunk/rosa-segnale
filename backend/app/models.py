from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Priority(str, Enum):
    low = "Bassa"
    medium = "Media"
    high = "Alta"
    critical = "Critica"


class TicketCategory(str, Enum):
    immediate_risk = "Rischio immediato"
    domestic_violence = "Violenza domestica"
    coercive_control = "Controllo coercitivo"
    economic_violence = "Violenza economica"
    verbal_violence = "Violenza verbale"
    institutional_confinement = "Contesto chiuso o istituzionale"
    stalking = "Stalking o controllo"
    legal_support = "Supporto legale"
    psychological_support = "Supporto psicologico"
    emotional_crisis = "Crisi emotiva"
    social_support = "Supporto sociale"
    minors_family = "Minori e famiglia"
    evidence_documentation = "Documentazione e prove"
    medical_support = "Supporto medico"
    safe_housing = "Alloggio sicuro"
    information_request = "Informazioni"
    out_of_scope = "Fuori ambito"


class EscalationTeam(str, Enum):
    emergency = "Emergenza 112"
    anti_violence_center = "Centro antiviolenza"
    legal_desk = "Sportello legale"
    psychological_support = "Supporto psicologico"
    social_services = "Servizi sociali"
    minors_protection = "Protezione minori"
    evidence_collection = "Raccolta documenti"
    medical_support = "Supporto medico"
    case_worker = "Operatrice dedicata"
    insufficient_context = "Informazioni insufficienti"


class OperationalArea(str, Enum):
    listening = "Ascolto e orientamento"
    human_bridge = "Ponte umano"
    immediate_intervention = "Intervento immediato"
    territorial_support = "Supporto territoriale"
    non_operational = "Non operativo"


class AlertStatus(str, Enum):
    new = "Nuovo"
    in_progress = "In carico"
    closed = "Chiuso"


class AlertSource(str, Enum):
    ticket = "Ticket"
    rosa_button = "Bottone Rosa"
    manual = "Manuale"


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    description: str = Field(..., min_length=10, max_length=4000)
    priority: Priority
    business_impact: str = Field(..., min_length=3, max_length=500)
    technical_area: str = Field(..., min_length=2, max_length=120)


class TicketFollowUpUpdate(BaseModel):
    follow_up_status: str = Field(..., min_length=3, max_length=80)
    internal_note: str = Field(default="", max_length=1200)


class AlertCreate(BaseModel):
    source: AlertSource = AlertSource.manual
    title: str = Field(..., min_length=3, max_length=160)
    summary: str = Field(..., min_length=3, max_length=700)
    risk_score: int = Field(..., ge=1, le=5)
    operational_area: OperationalArea = OperationalArea.human_bridge
    ticket_id: int | None = None


class AlertUpdate(BaseModel):
    status: AlertStatus
    operator_label: str = Field(default="", max_length=120)
    internal_note: str = Field(default="", max_length=1200)


class TriageResult(BaseModel):
    category: TicketCategory
    risk_score: int = Field(..., ge=1, le=5)
    escalation: EscalationTeam
    operational_area: OperationalArea = OperationalArea.listening
    human_handoff: bool = False
    suspected_misuse: bool = False
    emotional_tone: str = Field(default="Non determinato", max_length=80)
    urgency_confidence: float = Field(default=0, ge=0, le=1)
    misuse_confidence: float = Field(default=0, ge=0, le=1)
    recommendation: str = Field(..., max_length=700)
    provider: str = Field(..., max_length=80)
    rationale: str = Field(..., max_length=500)


class Ticket(TicketCreate):
    id: int
    category: TicketCategory
    risk_score: int
    escalation: EscalationTeam
    operational_area: OperationalArea = OperationalArea.listening
    human_handoff: bool = False
    suspected_misuse: bool = False
    emotional_tone: str = "Non determinato"
    urgency_confidence: float = 0
    misuse_confidence: float = 0
    recommendation: str
    rationale: str
    provider: str
    created_at: str
    follow_up_status: str = "Da valutare"
    internal_note: str = ""


class Alert(BaseModel):
    id: int
    ticket_id: int | None = None
    source: AlertSource
    title: str
    summary: str
    risk_score: int
    operational_area: OperationalArea
    status: AlertStatus
    operator_label: str = ""
    internal_note: str = ""
    created_at: str
    taken_at: str | None = None
    closed_at: str | None = None


class HoneypotEvent(BaseModel):
    id: int
    path: str
    method: str
    reason: str
    risk_score: int
    ip_hash: str
    user_agent: str = ""
    query_present: bool = False
    created_at: str


class DashboardKpis(BaseModel):
    total_tickets: int
    average_risk_score: float
    priority_counts: dict[str, int]
    category_counts: dict[str, int]
    escalation_counts: dict[str, int]
    operational_area_counts: dict[str, int] = Field(default_factory=dict)
    high_risk_tickets: int


class HealthResponse(BaseModel):
    status: str
    provider: str
    database: str
    version: str


class ChunkPreviewRequest(BaseModel):
    source_name: str = Field(..., min_length=3, max_length=160)
    text: str = Field(..., min_length=20, max_length=20000)
    max_words: int = Field(default=120, ge=40, le=400)
    overlap_words: int = Field(default=20, ge=0, le=80)

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkPreviewRequest":
        if self.overlap_words >= self.max_words:
            raise ValueError("overlap_words must be lower than max_words")
        return self


class KnowledgeChunk(BaseModel):
    source_name: str
    chunk_index: int
    text: str
    word_count: int


class ChunkPreviewResponse(BaseModel):
    source_name: str
    chunk_count: int
    chunks: list[KnowledgeChunk]


class RagAnswerRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1200)
    top_k: int = Field(default=3, ge=1, le=5)


class RetrievedChunk(KnowledgeChunk):
    score: int


class RagAnswerResponse(BaseModel):
    question: str
    answer: str = Field(..., max_length=1100)
    retrieved_chunks: list[RetrievedChunk]
    provider: str
    blocked: bool = False
    policy_reason: str | None = None


class WeeklyReportResponse(BaseModel):
    title: str
    generated_at: str
    period_days: int
    summary: str
    markdown: str
