import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  ExternalLink,
  FileBarChart,
  FileText,
  Gauge,
  GitBranch,
  MessageSquareText,
  PhoneCall,
  RefreshCw,
  ShieldCheck,
  TicketPlus,
} from "lucide-react";
import {
  askAssistant,
  fetchDashboard,
  fetchHealth,
  fetchTickets,
  fetchWeeklyReport,
  seedSampleTickets,
  updateTicketFollowUp,
} from "./api";
import "./styles.css";

const followUpStatuses = ["Da valutare", "In corso", "Ricontatto pianificato", "Escalation esterna", "Chiuso"];
const YOUPOL_URL = "https://youpol.poliziadistato.it/landing";
const MAX_ASSISTANT_CONTEXT_CHARS = 1100;
const QUICK_RESOURCES = [
  {
    label: "112",
    description: "Emergenza immediata",
    href: "tel:112",
    external: false,
    urgent: true,
  },
  {
    label: "1522",
    description: "Antiviolenza e stalking",
    href: "tel:1522",
    external: false,
    urgent: false,
  },
  {
    label: "YouPol",
    description: "Polizia di Stato",
    href: YOUPOL_URL,
    external: true,
    urgent: false,
  },
];

const aodCapabilities = [
  {
    icon: FileText,
    title: "Base conoscenza",
    status: "Anteprima",
    description: "Risorse nazionali e linee guida recuperate per orientare le risposte.",
  },
  {
    icon: BrainCircuit,
    title: "Triage segnalazioni",
    status: "Attivo",
    description: "Classifica bisogno, rischio e percorso di supporto consigliato.",
  },
  {
    icon: MessageSquareText,
    title: "Punto di ascolto AI",
    status: "Attivo",
    description: "Risponde in modo empatico e usa la base di conoscenza per indirizzare.",
  },
  {
    icon: FileBarChart,
    title: "Report settimanale",
    status: "Attivo",
    description: "Produce automaticamente KPI aggregati su rischio, categorie e percorsi.",
  },
  {
    icon: ClipboardList,
    title: "Tracciabilità",
    status: "Attivo",
    description: "Salva modello AI, motivazione e timestamp delle segnalazioni.",
  },
];

function App() {
  const [showSafetyNotice, setShowSafetyNotice] = useState(true);
  const [activeView, setActiveView] = useState("listen");
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [sampleStatus, setSampleStatus] = useState({ type: "idle", message: "" });
  const [followUpStatus, setFollowUpStatus] = useState({ type: "idle", message: "" });
  const [loading, setLoading] = useState(false);
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [followUpLoading, setFollowUpLoading] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [ragQuestion, setRagQuestion] = useState("");
  const [ragMessages, setRagMessages] = useState([]);
  const [ragStatus, setRagStatus] = useState({ type: "idle", message: "" });
  const [ragLoading, setRagLoading] = useState(false);
  const [signalCode] = useState(() => createSignalCode());
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [reportStatus, setReportStatus] = useState({ type: "idle", message: "" });
  const [reportLoading, setReportLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [healthData, dashboardData, ticketData] = await Promise.all([
        fetchHealth(),
        fetchDashboard(),
        fetchTickets(),
      ]);
      setHealth(healthData);
      setDashboard(dashboardData);
      setTickets(ticketData);
    } catch (error) {
      setSampleStatus({ type: "error", message: error.message });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!tickets.length) {
      setSelectedTicketId(null);
      return;
    }

    if (!selectedTicketId || !tickets.some((ticket) => ticket.id === selectedTicketId)) {
      setSelectedTicketId(tickets[0].id);
    }
  }, [tickets, selectedTicketId]);

  async function handleAskAssistant(event) {
    event.preventDefault();
    const userQuestion = ragQuestion.trim();
    if (!userQuestion || ragLoading) return;

    setRagStatus({ type: "idle", message: "" });
    setRagLoading(true);
    setRagMessages((messages) => [...messages, { role: "user", text: userQuestion }]);
    setRagQuestion("");

    try {
      const answer = await askAssistant(buildAssistantQuestion(ragMessages, userQuestion));
      setRagMessages((messages) => [
        ...markLatestUserMessage(messages, userQuestion, answer.blocked),
        {
          role: "assistant",
          text: answer.answer,
          blocked: answer.blocked,
          provider: answer.provider,
          sources: answer.retrieved_chunks,
        },
      ]);
      setRagStatus({
        type: answer.blocked ? "error" : "success",
        message: answer.blocked
          ? "Richiesta bloccata dai guardrail locali."
          : "Risposta generata dalle fonti recuperate.",
      });
    } catch (error) {
      setRagMessages((messages) => [
        ...messages,
        {
          role: "assistant",
          text: "Non riesco a generare una risposta in questo momento. Se sei in pericolo immediato, chiama il 112.",
          blocked: true,
          provider: "local-error",
          sources: [],
        },
      ]);
      setRagStatus({ type: "error", message: error.message });
    } finally {
      setRagLoading(false);
    }
  }

  async function handleSeedSamples() {
    setSampleLoading(true);
    setSampleStatus({ type: "idle", message: "" });

    try {
      const beforeCount = tickets.length;
      const sampleTickets = await seedSampleTickets();
      const alreadyPopulated = beforeCount > 0 && sampleTickets.length === beforeCount;
      setSampleStatus({
        type: "success",
        message: alreadyPopulated
          ? "Registro gia popolato: i casi didattici non sono stati duplicati."
          : "Casi didattici caricati nel registro interno.",
      });
      await loadData();
    } catch (error) {
      setSampleStatus({ type: "error", message: error.message });
    } finally {
      setSampleLoading(false);
    }
  }

  async function handleGenerateReport() {
    setReportStatus({ type: "idle", message: "" });
    setReportLoading(true);

    try {
      const report = await fetchWeeklyReport();
      setWeeklyReport(report);
      setReportStatus({ type: "success", message: "Report aggregato generato." });
    } catch (error) {
      setReportStatus({ type: "error", message: error.message });
    } finally {
      setReportLoading(false);
    }
  }

  async function handleSaveFollowUp(ticketId, payload) {
    setFollowUpLoading(true);
    setFollowUpStatus({ type: "idle", message: "" });

    try {
      const updatedTicket = await updateTicketFollowUp(ticketId, payload);
      setFollowUpStatus({ type: "success", message: "Follow-up interno salvato." });
      await loadData();
      setSelectedTicketId(updatedTicket.id);
    } catch (error) {
      setFollowUpStatus({ type: "error", message: error.message });
    } finally {
      setFollowUpLoading(false);
    }
  }

  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) || tickets[0] || null;
  const averageRisk = dashboard?.average_risk_score ?? 0;

  return (
    <main className="app-shell">
      {showSafetyNotice && (
        <div className="safety-overlay" role="dialog" aria-modal="true" aria-labelledby="safety-title">
          <section className="safety-modal">
            <div className="safety-icon">
              <ShieldCheck size={24} />
            </div>
            <div>
              <p className="eyebrow">Avviso di supporto</p>
              <h2 id="safety-title">Non sei sola</h2>
              <p>
                Questo portale è un prototipo di ascolto e orientamento: non sostituisce servizi di emergenza,
                centri antiviolenza, supporto medico, psicologico o legale.
              </p>
              <p>
                Se sei in pericolo immediato chiama il <strong>112</strong>. Per violenza o stalking puoi
                contattare il <strong>1522</strong>, gratuito e attivo 24 ore su 24. Se stai vivendo pensieri di
                autolesionismo o una crisi emotiva, prova a contattare una persona fidata o
                <strong> Telefono Amico Italia 02 2327 2327</strong>.
              </p>
              <p>
                Per la tua sicurezza, evita nomi completi, indirizzi precisi, numeri di telefono,
                codici fiscali o dati di altre persone. Usa informazioni fittizie o anonimizzate.
              </p>
              <div className="safety-actions">
                <button className="primary-button safety-button" type="button" onClick={() => setShowSafetyNotice(false)}>
                  Ho capito
                </button>
                <a className="secondary-button safety-button" href={YOUPOL_URL} target="_blank" rel="noreferrer">
                  <ExternalLink size={18} />
                  Apri YouPol
                </a>
              </div>
            </div>
          </section>
        </div>
      )}

      <section className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <p className="eyebrow">Portale prototipo di ascolto e orientamento</p>
            <h1>Rosa Segnale</h1>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="view-tabs" aria-label="Sezioni del portale">
            <button
              className={activeView === "listen" ? "active" : ""}
              type="button"
              onClick={() => setActiveView("listen")}
            >
              Ascolto
            </button>
            <button
              className={activeView === "internal" ? "active" : ""}
              type="button"
              onClick={() => setActiveView("internal")}
            >
              Area interna
            </button>
          </div>
          {activeView === "internal" && (
            <div className="system-status">
              <span className="status-dot" />
              <span className="provider-name">{health?.provider || "modello in caricamento"}</span>
              <button className="icon-button" onClick={loadData} aria-label="Refresh dashboard" title="Refresh dashboard">
                <RefreshCw size={17} />
              </button>
            </div>
          )}
        </div>
      </section>

      {activeView === "listen" ? (
        <ListenView
          handleAskAssistant={handleAskAssistant}
          ragLoading={ragLoading}
          ragMessages={ragMessages}
          ragQuestion={ragQuestion}
          ragStatus={ragStatus}
          setRagQuestion={setRagQuestion}
          signalCode={signalCode}
        />
      ) : (
        <InternalView
          averageRisk={averageRisk}
          dashboard={dashboard}
          followUpLoading={followUpLoading}
          handleGenerateReport={handleGenerateReport}
          handleSeedSamples={handleSeedSamples}
          handleSaveFollowUp={handleSaveFollowUp}
          loading={loading}
          reportLoading={reportLoading}
          reportStatus={reportStatus}
          sampleLoading={sampleLoading}
          sampleStatus={sampleStatus}
          selectedTicket={selectedTicket}
          selectedTicketId={selectedTicketId}
          setSelectedTicketId={setSelectedTicketId}
          followUpStatus={followUpStatus}
          tickets={tickets}
          weeklyReport={weeklyReport}
        />
      )}
    </main>
  );
}

function ListenView({
  handleAskAssistant,
  ragLoading,
  ragMessages,
  ragQuestion,
  ragStatus,
  setRagQuestion,
  signalCode,
}) {
  return (
    <>
      <section className="quick-resources" aria-label="Risorse rapide">
        <div>
          <p className="eyebrow">Risorse rapide</p>
          <h2>Contatti e strumenti esterni</h2>
        </div>
        <div className="quick-resource-actions">
          {QUICK_RESOURCES.map((resource) => (
            <a
              className={`quick-resource ${resource.urgent ? "urgent" : ""}`}
              href={resource.href}
              key={resource.label}
              rel={resource.external ? "noreferrer" : undefined}
              target={resource.external ? "_blank" : undefined}
            >
              <span className="resource-medallion" aria-hidden="true">
                {resource.external ? <ExternalLink size={18} /> : <PhoneCall size={18} />}
              </span>
              <span>
                <strong>{resource.label}</strong>
                <small>{resource.description}</small>
              </span>
            </a>
          ))}
        </div>
      </section>

      <section className="listen-grid">
        <section className="listen-intro panel">
          <p className="eyebrow">Spazio di ascolto</p>
          <h2>Puoi scrivere quello che sta succedendo, senza inserire dati personali.</h2>
          <div className="signal-code">
            <div>
              <span>Codice locale</span>
              <strong>{signalCode}</strong>
            </div>
            <small>Non invia richieste di soccorso e non identifica una presa in carico.</small>
          </div>
          <p>
            L'assistente prova a orientarti con parole semplici e fonti interne al prototipo.
            Se c'e un pericolo immediato, la priorita resta contattare il 112 o una persona vicina.
          </p>
        </section>

        <AssistantPanel
          handleAskAssistant={handleAskAssistant}
          ragLoading={ragLoading}
          ragMessages={ragMessages}
          ragQuestion={ragQuestion}
          ragStatus={ragStatus}
          setRagQuestion={setRagQuestion}
          publicMode
        />
      </section>
    </>
  );
}

function InternalView({
  averageRisk,
  dashboard,
  followUpLoading,
  handleGenerateReport,
  handleSeedSamples,
  handleSaveFollowUp,
  loading,
  reportLoading,
  reportStatus,
  sampleLoading,
  sampleStatus,
  selectedTicket,
  selectedTicketId,
  setSelectedTicketId,
  followUpStatus,
  tickets,
  weeklyReport,
}) {
  return (
    <>
      <section className="kpi-grid">
        <KpiCard icon={TicketPlus} label="Segnalazioni" value={dashboard?.total_tickets ?? 0} />
        <KpiCard icon={Gauge} label="Rischio medio" value={averageRisk.toFixed(2)} />
        <KpiCard icon={AlertTriangle} label="Alto rischio" value={dashboard?.high_risk_tickets ?? 0} />
        <KpiCard icon={GitBranch} label="Percorsi" value={Object.keys(dashboard?.escalation_counts || {}).length} />
      </section>

      <section className="ops-tools panel">
        <div>
          <p className="eyebrow">Ambiente operativo</p>
          <h2>Registro interno pulito</h2>
          <p>
            L'area interna mostra le segnalazioni registrate e i report aggregati generati dal backend.
            Per la presentazione puoi caricare casi didattici sintetici, senza dati reali.
          </p>
        </div>
        <div className="ops-actions">
          <button className="secondary-button" type="button" onClick={handleSeedSamples} disabled={sampleLoading}>
            <ClipboardList size={17} />
            {sampleLoading ? "Carico" : "Carica casi didattici"}
          </button>
          <span className="status-pill status-attivo">Dati reali non inclusi</span>
        </div>
        {sampleStatus.message && (
          <p className={`notice ${sampleStatus.type}`}>
            {sampleStatus.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            {sampleStatus.message}
          </p>
        )}
      </section>

      <section className="aod-feature panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Rosa Segnale</p>
            <h2>Funzioni interne</h2>
          </div>
          <ShieldCheck size={22} />
        </div>
        <div className="capability-grid">
          {aodCapabilities.map((capability) => (
            <CapabilityCard key={capability.title} capability={capability} />
          ))}
        </div>
      </section>

      <ReportPanel
        handleGenerateReport={handleGenerateReport}
        reportLoading={reportLoading}
        reportStatus={reportStatus}
        weeklyReport={weeklyReport}
      />

      <section className="workspace-grid">
        <FollowUpPanel
          followUpLoading={followUpLoading}
          onSave={handleSaveFollowUp}
          status={followUpStatus}
          ticket={selectedTicket}
        />

        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Esito orientativo</p>
              <h2>Ultima classificazione</h2>
            </div>
            <BarChart3 size={22} />
          </div>

          {selectedTicket ? (
            <TicketDecision ticket={selectedTicket} />
          ) : (
            <p className="empty-state">Nessuna segnalazione presente.</p>
          )}

          <Distribution title="Urgenze" data={dashboard?.priority_counts || {}} />
          <Distribution title="Categorie" data={dashboard?.category_counts || {}} />
          <Distribution title="Percorsi" data={dashboard?.escalation_counts || {}} />
        </section>
      </section>

      <section className="panel ticket-table-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Vista operativa</p>
            <h2>Registro segnalazioni</h2>
          </div>
          <span className="subtle">{loading ? "Aggiorno" : `${tickets.length} record`}</span>
        </div>
        <TicketTable
          onSelectTicket={setSelectedTicketId}
          selectedTicketId={selectedTicketId}
          tickets={tickets}
        />
      </section>
    </>
  );
}

function AssistantPanel({
  handleAskAssistant,
  publicMode = false,
  ragLoading,
  ragMessages,
  ragQuestion,
  ragStatus,
  setRagQuestion,
}) {
  return (
    <section className={`rag-panel panel ${publicMode ? "public-assistant" : ""}`}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Assistente di orientamento</p>
          <h2>{publicMode ? "Scrivi all'assistente" : "Chiedi alla base di conoscenza"}</h2>
        </div>
        <MessageSquareText size={22} />
      </div>
      <form className="rag-form" onSubmit={handleAskAssistant}>
        <label>
          Messaggio
          <textarea
            className="compact"
            value={ragQuestion}
            onChange={(event) => setRagQuestion(event.target.value)}
            maxLength={600}
            placeholder="Scrivi quello che sta succedendo…"
            required
          />
        </label>
        <button className="primary-button" type="submit" disabled={ragLoading || ragQuestion.trim().length < 5}>
          <MessageSquareText size={18} />
          {ragLoading ? "Sto rispondendo" : "Invia"}
        </button>
      </form>

      {ragStatus.message && (
        <p className={`notice ${ragStatus.type}`}>
          {ragStatus.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {ragStatus.message}
        </p>
      )}

      {ragMessages.length > 0 && (
        <div className="chat-thread" aria-live="polite">
          {ragMessages.map((message, index) => (
            <article
              className={`chat-message ${message.role === "user" ? "from-user" : "from-assistant"} ${
                message.blocked ? "blocked" : ""
              }`}
              key={`${message.role}-${index}`}
            >
              <span>{message.role === "user" ? "Tu" : "Rosa Segnale"}</span>
              {!publicMode && message.role === "assistant" && message.provider && (
                <small className="provider-tag">{formatProviderLabel(message.provider)}</small>
              )}
              <p>{message.text}</p>
              {!publicMode && message.role === "assistant" && message.sources?.length > 0 && (
                <div className="source-list">
                  {message.sources.map((chunk) => (
                    <div className="source-item" key={`${chunk.source_name}-${chunk.chunk_index}`}>
                      <strong>{chunk.source_name} #{chunk.chunk_index}</strong>
                      <span>Rilevanza {chunk.score}</span>
                      <p>{chunk.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}

    </section>
  );
}

function buildAssistantQuestion(messages, currentQuestion) {
  const recentContext = messages
    .slice(-4)
    .filter((message) => !message.blocked)
    .map((message) => {
      const compactText = message.text.length > 220 ? `${message.text.slice(0, 217)}...` : message.text;
      return `${message.role === "user" ? "Persona" : "Assistente"}: ${compactText}`;
    })
    .join("\n");
  const prompt = recentContext
    ? `Contesto breve della conversazione:\n${recentContext}\n\nNuovo messaggio della persona:\n${currentQuestion}`
    : currentQuestion;

  if (prompt.length <= MAX_ASSISTANT_CONTEXT_CHARS) {
    return prompt;
  }

  const trimmedContext = recentContext.slice(0, Math.max(0, MAX_ASSISTANT_CONTEXT_CHARS - currentQuestion.length - 80));
  return `Contesto breve della conversazione:\n${trimmedContext}\n\nNuovo messaggio della persona:\n${currentQuestion}`;
}

function createSignalCode() {
  const bytes = new Uint8Array(4);
  if (window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(bytes);
  } else {
    bytes.forEach((_, index) => {
      bytes[index] = Math.floor(Math.random() * 256);
    });
  }

  return `RS-${Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}`;
}

function formatProviderLabel(provider) {
  if (provider.startsWith("openai")) return "OpenAI";
  if (provider.startsWith("local")) return "Fallback locale";
  return provider;
}

function markLatestUserMessage(messages, text, blocked) {
  if (!blocked) return messages;

  const updatedMessages = [...messages];
  for (let index = updatedMessages.length - 1; index >= 0; index -= 1) {
    const message = updatedMessages[index];
    if (message.role === "user" && message.text === text) {
      updatedMessages[index] = { ...message, blocked: true };
      break;
    }
  }

  return updatedMessages;
}

function ReportPanel({ handleGenerateReport, reportLoading, reportStatus, weeklyReport }) {
  const reportMetrics = weeklyReport ? extractReportMetrics(weeklyReport.markdown) : [];
  const highRiskItems = weeklyReport ? extractHighRiskItems(weeklyReport.markdown) : [];

  return (
    <section className="report-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Report aggregato</p>
          <h2>Report settimanale</h2>
        </div>
        <FileBarChart size={22} />
      </div>
      <div className="report-actions">
        <p>
          Il backend genera automaticamente un report settimanale con KPI aggregati. Il pulsante permette di
          rigenerarlo subito quando serve.
        </p>
        <button className="primary-button" type="button" onClick={handleGenerateReport} disabled={reportLoading}>
          <FileBarChart size={18} />
          {reportLoading ? "Genero report" : "Genera report"}
        </button>
      </div>

      {reportStatus.message && (
        <p className={`notice ${reportStatus.type}`}>
          {reportStatus.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {reportStatus.message}
        </p>
      )}

      {weeklyReport && (
        <article className="weekly-report">
          <div className="weekly-report-header">
            <h3>{weeklyReport.title}</h3>
            <span>{new Date(weeklyReport.generated_at).toLocaleString()}</span>
          </div>
          <p>{weeklyReport.summary}</p>
          <div className="report-metric-grid">
            {reportMetrics.map((metric) => (
              <div className="report-metric" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>
          {highRiskItems.length > 0 && (
            <div className="high-risk-list">
              <h3>Segnalazioni a rischio più alto</h3>
              {highRiskItems.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          )}
          <details className="raw-report">
            <summary>Markdown generato</summary>
            <pre>{weeklyReport.markdown}</pre>
          </details>
        </article>
      )}
    </section>
  );
}

function extractReportMetrics(markdown) {
  return markdown
    .split("\n")
    .filter((line) => line.startsWith("- ") && !line.includes("Risk "))
    .map((line) => line.replace("- ", ""))
    .map((line) => {
      const [label, ...rest] = line.split(": ");
      return {
        label,
        value: rest.join(": ") || "-",
      };
    })
    .slice(0, 6);
}

function extractHighRiskItems(markdown) {
  return markdown
    .split("\n")
    .filter((line) => line.startsWith("- Risk "))
    .map((line) => line.replace("- ", ""));
}

function FollowUpPanel({ followUpLoading, onSave, status, ticket }) {
  const [followUpStatus, setFollowUpStatus] = useState("Da valutare");
  const [internalNote, setInternalNote] = useState("");

  useEffect(() => {
    setFollowUpStatus(ticket?.follow_up_status || "Da valutare");
    setInternalNote(ticket?.internal_note || "");
  }, [ticket]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!ticket || followUpLoading) return;

    await onSave(ticket.id, {
      follow_up_status: followUpStatus,
      internal_note: internalNote,
    });
  }

  if (!ticket) {
    return (
      <section className="panel follow-up-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Follow-up operativo</p>
            <h2>Nessun caso selezionato</h2>
          </div>
          <ClipboardList size={22} />
        </div>
        <p className="empty-state">Quando saranno presenti segnalazioni, potrai aggiungere stato e nota interna.</p>
      </section>
    );
  }

  return (
    <form className="panel follow-up-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Follow-up operativo</p>
          <h2>Commenta il caso selezionato</h2>
        </div>
        <ClipboardList size={22} />
      </div>

      <article className="case-summary">
        <span className={`risk risk-${ticket.risk_score}`}>Rischio {ticket.risk_score}/5</span>
        <h3>{ticket.title}</h3>
        <p>{ticket.description}</p>
        <dl>
          <div>
            <dt>Percorso</dt>
            <dd>{ticket.escalation}</dd>
          </div>
          <div>
            <dt>Categoria</dt>
            <dd>{ticket.category}</dd>
          </div>
        </dl>
      </article>

      <label>
        Stato follow-up
        <select value={followUpStatus} onChange={(event) => setFollowUpStatus(event.target.value)}>
          {followUpStatuses.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      </label>

      <label>
        Nota interna
        <textarea
          className="compact"
          maxLength={1200}
          value={internalNote}
          onChange={(event) => setInternalNote(event.target.value)}
          placeholder="Annota follow-up, prossimo contatto, invio a servizio competente o informazioni raccolte senza dati identificativi superflui."
        />
      </label>

      <button className="primary-button" type="submit" disabled={followUpLoading}>
        <ShieldCheck size={18} />
        {followUpLoading ? "Salvo follow-up" : "Salva follow-up"}
      </button>

      {status.message && (
        <p className={`notice ${status.type}`}>
          {status.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {status.message}
        </p>
      )}
    </form>
  );
}

function KpiCard({ icon: Icon, label, value }) {
  return (
    <article className="kpi-card">
      <Icon size={20} />
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function CapabilityCard({ capability }) {
  const Icon = capability.icon;

  return (
    <article className="capability-card">
      <div className="capability-header">
        <Icon size={18} />
        <span className={`status-pill status-${capability.status.toLowerCase()}`}>
          {capability.status}
        </span>
      </div>
      <h3>{capability.title}</h3>
      <p>{capability.description}</p>
    </article>
  );
}

function TicketDecision({ ticket }) {
  return (
    <article className="decision-card">
      <div className="decision-header">
        <span className="tag">{ticket.category}</span>
        <span className={`risk risk-${ticket.risk_score}`}>Rischio {ticket.risk_score}/5</span>
      </div>
      <h3>{ticket.title}</h3>
      <p>{ticket.recommendation}</p>
      <dl>
        <div>
          <dt>Percorso</dt>
          <dd>{ticket.escalation}</dd>
        </div>
        <div>
          <dt>Bisogno</dt>
          <dd>{ticket.technical_area}</dd>
        </div>
        <div>
          <dt>Follow-up</dt>
          <dd>{ticket.follow_up_status}</dd>
        </div>
      </dl>
    </article>
  );
}

function Distribution({ title, data }) {
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, value]) => value), 1);

  return (
    <div className="distribution">
      <h3>{title}</h3>
      {entries.length === 0 ? (
        <p className="empty-state">Nessun dato</p>
      ) : (
        entries.map(([label, value]) => (
          <div className="bar-row" key={label}>
            <span>{label}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
            </div>
            <strong>{value}</strong>
          </div>
        ))
      )}
    </div>
  );
}

function TicketTable({ onSelectTicket, selectedTicketId, tickets }) {
  if (!tickets.length) {
    return <p className="empty-state">Nessuna segnalazione disponibile.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Titolo</th>
            <th>Urgenza</th>
            <th>Categoria</th>
            <th>Rischio</th>
            <th>Percorso</th>
            <th>Follow-up</th>
            <th>Creata</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr className={ticket.id === selectedTicketId ? "selected-row" : ""} key={ticket.id}>
              <td>
                <strong>{ticket.title}</strong>
                <span>{ticket.business_impact}</span>
              </td>
              <td>{ticket.priority}</td>
              <td>{ticket.category}</td>
              <td>
                <span className={`risk risk-${ticket.risk_score}`}>{ticket.risk_score}/5</span>
              </td>
              <td>{ticket.escalation}</td>
              <td>{ticket.follow_up_status}</td>
              <td>{new Date(`${ticket.created_at}Z`).toLocaleString()}</td>
              <td>
                <button className="table-action" type="button" onClick={() => onSelectTicket(ticket.id)}>
                  Apri
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
