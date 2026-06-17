import React, { useEffect, useRef, useState } from "react";
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
  MessageSquareText,
  PhoneCall,
  RefreshCw,
  ShieldCheck,
  TicketPlus,
} from "lucide-react";
import {
  askAssistant,
  closeAlert,
  fetchAlerts,
  fetchDashboard,
  fetchHealth,
  fetchHoneypotEvents,
  fetchTickets,
  fetchWeeklyReport,
  seedSampleTickets,
  takeAlert,
  updateAlert,
  updateTicketFollowUp,
} from "./api";
import "./styles.css";

const followUpStatuses = ["Da valutare", "In corso", "Ricontatto pianificato", "Escalation esterna", "Chiuso"];
const HUMAN_HANDOFF_LABEL = "Richiede persona reale";
const YOUPOL_URL = "https://youpol.poliziadistato.it/landing";
const MAX_ASSISTANT_CONTEXT_CHARS = 1100;
const MIN_ASSISTANT_MESSAGE_CHARS = 4;
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
  const safetyModalRef = useRef(null);
  const [showSafetyNotice, setShowSafetyNotice] = useState(true);
  const [activeView, setActiveView] = useState("listen");
  const [health, setHealth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [honeypotEvents, setHoneypotEvents] = useState([]);
  const [sampleStatus, setSampleStatus] = useState({ type: "idle", message: "" });
  const [alertStatus, setAlertStatus] = useState({ type: "idle", message: "" });
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
  const [alertLoadingId, setAlertLoadingId] = useState(null);

  async function loadData() {
    setLoading(true);
    try {
      const [healthData, dashboardData, ticketData, alertData, honeypotData] = await Promise.all([
        fetchHealth(),
        fetchDashboard(),
        fetchTickets(),
        fetchAlerts(),
        fetchHoneypotEvents(),
      ]);
      setHealth(healthData);
      setDashboard(dashboardData);
      setTickets(ticketData);
      setAlerts(alertData);
      setHoneypotEvents(honeypotData);
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
    if (!showSafetyNotice || !safetyModalRef.current) return undefined;

    const focusableElements = Array.from(
      safetyModalRef.current.querySelectorAll("button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])"),
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    firstElement?.focus();

    function handleKeyDown(event) {
      if (event.key !== "Tab" || focusableElements.length === 0) return;

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showSafetyNotice]);

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
    const nextMessages = [...ragMessages, { role: "user", text: userQuestion }];
    setRagMessages(nextMessages);
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

  async function handleTakeAlert(alertId) {
    setAlertLoadingId(alertId);
    setAlertStatus({ type: "idle", message: "" });

    try {
      await takeAlert(alertId);
      setAlertStatus({ type: "success", message: "Alert preso in carico." });
      await loadData();
    } catch (error) {
      setAlertStatus({ type: "error", message: error.message });
    } finally {
      setAlertLoadingId(null);
    }
  }

  async function handleCloseAlert(alertId) {
    setAlertLoadingId(alertId);
    setAlertStatus({ type: "idle", message: "" });

    try {
      await closeAlert(alertId);
      setAlertStatus({ type: "success", message: "Alert chiuso." });
      await loadData();
    } catch (error) {
      setAlertStatus({ type: "error", message: error.message });
    } finally {
      setAlertLoadingId(null);
    }
  }

  async function handleUpdateAlert(alertId, payload) {
    setAlertLoadingId(alertId);
    setAlertStatus({ type: "idle", message: "" });

    try {
      await updateAlert(alertId, payload);
      setAlertStatus({ type: "success", message: "Alert aggiornato." });
      await loadData();
    } catch (error) {
      setAlertStatus({ type: "error", message: error.message });
    } finally {
      setAlertLoadingId(null);
    }
  }

  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) || null;
  const averageRisk = dashboard?.average_risk_score ?? 0;
  const humanHandoffCount = tickets.filter((ticket) => ticket.human_handoff).length;
  const activeAlertCount = alerts.filter((alert) => alert.status !== "Chiuso").length;

  return (
    <main className="app-shell">
      {showSafetyNotice && (
        <div className="safety-overlay" role="dialog" aria-modal="true" aria-labelledby="safety-title">
          <section className="safety-modal" ref={safetyModalRef}>
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
          <div className="view-tabs" role="tablist" aria-label="Sezioni del portale">
            <button
              className={activeView === "listen" ? "active" : ""}
              role="tab"
              aria-selected={activeView === "listen"}
              type="button"
              onClick={() => setActiveView("listen")}
            >
              Ascolto
            </button>
            <button
              className={activeView === "internal" ? "active" : ""}
              role="tab"
              aria-selected={activeView === "internal"}
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
              <button className="icon-button" onClick={loadData} aria-label="Aggiorna la dashboard" title="Aggiorna la dashboard">
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
          activeAlertCount={activeAlertCount}
          alertLoadingId={alertLoadingId}
          alerts={alerts}
          alertStatus={alertStatus}
          dashboard={dashboard}
          followUpLoading={followUpLoading}
          handleGenerateReport={handleGenerateReport}
          handleSeedSamples={handleSeedSamples}
          handleSaveFollowUp={handleSaveFollowUp}
          handleTakeAlert={handleTakeAlert}
          handleCloseAlert={handleCloseAlert}
          handleUpdateAlert={handleUpdateAlert}
          loading={loading}
          reportLoading={reportLoading}
          reportStatus={reportStatus}
          sampleLoading={sampleLoading}
          sampleStatus={sampleStatus}
          selectedTicket={selectedTicket}
          selectedTicketId={selectedTicketId}
          setSelectedTicketId={setSelectedTicketId}
          followUpStatus={followUpStatus}
          honeypotEvents={honeypotEvents}
          tickets={tickets}
          weeklyReport={weeklyReport}
          humanHandoffCount={humanHandoffCount}
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
  activeAlertCount,
  averageRisk,
  alertLoadingId,
  alerts,
  alertStatus,
  dashboard,
  followUpLoading,
  handleGenerateReport,
  handleSeedSamples,
  handleSaveFollowUp,
  handleTakeAlert,
  handleCloseAlert,
  handleUpdateAlert,
  loading,
  reportLoading,
  reportStatus,
  sampleLoading,
  sampleStatus,
  selectedTicket,
  selectedTicketId,
  setSelectedTicketId,
  followUpStatus,
  honeypotEvents,
  tickets,
  weeklyReport,
  humanHandoffCount,
}) {
  return (
    <>
      <section className="kpi-grid">
        <KpiCard icon={TicketPlus} label="Segnalazioni" value={dashboard?.total_tickets ?? 0} />
        <KpiCard icon={Gauge} label="Rischio medio" value={averageRisk.toFixed(2)} />
        <KpiCard icon={AlertTriangle} label="Alto rischio" value={dashboard?.high_risk_tickets ?? 0} />
        <KpiCard icon={ShieldCheck} label="Alert attivi" value={activeAlertCount} />
      </section>

      <section className="ops-tools panel">
        <div>
          <p className="eyebrow">Ambiente operativo</p>
          <h2>Registro interno pulito</h2>
          <p>
            L'area interna mostra le segnalazioni registrate e i report aggregati generati dal backend.
            La distinzione principale è tra ascolto, ponte umano e intervento immediato.
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

      <AlertPanel
        alertLoadingId={alertLoadingId}
        alerts={alerts}
        onCloseAlert={handleCloseAlert}
        onTakeAlert={handleTakeAlert}
        onUpdateAlert={handleUpdateAlert}
        status={alertStatus}
      />

      <HoneypotPanel events={honeypotEvents} />

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
          <Distribution title="Aree operative" data={dashboard?.operational_area_counts || {}} />
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
            aria-describedby="assistant-message-hint"
            maxLength={600}
            placeholder="Scrivi quello che sta succedendo…"
            required
          />
          <small id="assistant-message-hint">Puoi inviare anche un segnale breve come Rosa.</small>
        </label>
        <button className="primary-button" type="submit" disabled={ragLoading || ragQuestion.trim().length < MIN_ASSISTANT_MESSAGE_CHARS}>
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

  const trimmedContext = trimAtWordBoundary(
    recentContext,
    Math.max(0, MAX_ASSISTANT_CONTEXT_CHARS - currentQuestion.length - 80),
  );
  return `Contesto breve della conversazione:\n${trimmedContext}\n\nNuovo messaggio della persona:\n${currentQuestion}`;
}

function createSignalCode() {
  if (window.crypto?.randomUUID) {
    return `RS-${window.crypto.randomUUID().slice(0, 8).replaceAll("-", "").toUpperCase()}`;
  }

  const bytes = new Uint8Array(4);
  if (window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(bytes);
  } else {
    return "RS-CRYPTO";
  }

  return `RS-${Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}`;
}

function trimAtWordBoundary(text, maxLength) {
  if (text.length <= maxLength) return text;
  const trimmed = text.slice(0, maxLength);
  const lastBreak = Math.max(trimmed.lastIndexOf(" "), trimmed.lastIndexOf("\n"));

  return `${trimmed.slice(0, lastBreak > 40 ? lastBreak : maxLength).trim()}...`;
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
            <span>{formatDateTime(weeklyReport.generated_at)}</span>
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

function AlertPanel({ alertLoadingId, alerts, onCloseAlert, onTakeAlert, onUpdateAlert, status }) {
  const activeAlerts = alerts.filter((alert) => alert.status !== "Chiuso");
  const closedAlerts = alerts.filter((alert) => alert.status === "Chiuso").slice(0, 3);

  return (
    <section className="alert-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Presa in carico umana</p>
          <h2>Alert in arrivo</h2>
        </div>
        <AlertTriangle size={22} />
      </div>

      {status.message && (
        <p className={`notice ${status.type}`}>
          {status.type === "success" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {status.message}
        </p>
      )}

      {activeAlerts.length === 0 ? (
        <p className="empty-state">Nessun alert attivo. I casi con ponte umano compariranno qui.</p>
      ) : (
        <div className="alert-list">
          {activeAlerts.map((alert) => (
            <article className={`alert-card alert-${alert.status === "Nuovo" ? "new" : "progress"}`} key={alert.id}>
              <div className="alert-card-header">
                <span className={`risk risk-${alert.risk_score}`}>Rischio {alert.risk_score}/5</span>
                <span className="status-pill status-attivo">{alert.status}</span>
              </div>
              <h3>{alert.title}</h3>
              <p>{alert.summary}</p>
              <dl>
                <div>
                  <dt>Area</dt>
                  <dd>{alert.operational_area}</dd>
                </div>
                <div>
                  <dt>Fonte</dt>
                  <dd>{alert.source}</dd>
                </div>
                <div>
                  <dt>Ticket</dt>
                  <dd>{alert.ticket_id ? `#${alert.ticket_id}` : "Non collegato"}</dd>
                </div>
                <div>
                  <dt>Creato</dt>
                  <dd>{formatDateTime(alert.created_at)}</dd>
                </div>
              </dl>
              <div className="alert-actions">
                {alert.status === "Nuovo" ? (
                  <button
                    className="primary-button"
                    type="button"
                    disabled={alertLoadingId === alert.id}
                    onClick={() => onTakeAlert(alert.id)}
                  >
                    <ShieldCheck size={18} />
                    Prendi in carico
                  </button>
                ) : (
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={alertLoadingId === alert.id}
                    onClick={() =>
                      onUpdateAlert(alert.id, {
                        status: "In carico",
                        operator_label: alert.operator_label || "Operatore demo",
                        internal_note: alert.internal_note || "Presa in carico confermata.",
                      })
                    }
                  >
                    <ClipboardList size={17} />
                    Aggiorna nota
                  </button>
                )}
                <button
                  className="secondary-button"
                  type="button"
                  disabled={alertLoadingId === alert.id}
                  onClick={() => onCloseAlert(alert.id)}
                >
                  Chiudi
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {closedAlerts.length > 0 && (
        <details className="closed-alerts">
          <summary>Ultimi alert chiusi</summary>
          {closedAlerts.map((alert) => (
            <p key={alert.id}>
              #{alert.id} · {alert.title} · {alert.operational_area}
            </p>
          ))}
        </details>
      )}
    </section>
  );
}

function HoneypotPanel({ events }) {
  return (
    <section className="honeypot-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Sicurezza staging</p>
          <h2>Eventi honeypot</h2>
        </div>
        <ShieldCheck size={22} />
      </div>
      {events.length === 0 ? (
        <p className="empty-state">Nessun percorso-esca intercettato.</p>
      ) : (
        <div className="honeypot-list">
          {events.slice(0, 6).map((event) => (
            <article className="honeypot-event" key={event.id}>
              <div>
                <span className={`risk risk-${event.risk_score}`}>Rischio {event.risk_score}/5</span>
                <strong>{compactUntrustedText(`${event.method} ${event.path}`, 120)}</strong>
              </div>
              <dl>
                <div>
                  <dt>Motivo</dt>
                  <dd>{event.reason}</dd>
                </div>
                <div>
                  <dt>IP hash</dt>
                  <dd>{event.ip_hash}</dd>
                </div>
                <div>
                  <dt>User agent</dt>
                  <dd>{compactUntrustedText(event.user_agent, 160) || "Non disponibile"}</dd>
                </div>
                <div>
                  <dt>Ora</dt>
                  <dd>{formatDateTime(event.created_at)}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
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
        {ticket.human_handoff && <span className="handoff-pill">{HUMAN_HANDOFF_LABEL}</span>}
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
          <div>
            <dt>Area operativa</dt>
            <dd>{ticket.operational_area}</dd>
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
      <div className="decision-flags">
        <span className="status-pill status-anteprima">{ticket.operational_area}</span>
        {ticket.human_handoff && <span className="handoff-pill">{HUMAN_HANDOFF_LABEL}</span>}
        {ticket.suspected_misuse && <span className="misuse-pill">Possibile abuso/test</span>}
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
        <div>
          <dt>Area operativa</dt>
          <dd>{ticket.operational_area}</dd>
        </div>
        <div>
          <dt>Tono rilevato</dt>
          <dd>{ticket.emotional_tone || "Non determinato"}</dd>
        </div>
        <div>
          <dt>Confidenza</dt>
          <dd>
            Urgenza {formatConfidence(ticket.urgency_confidence)} · Abuso {formatConfidence(ticket.misuse_confidence)}
          </dd>
        </div>
      </dl>
    </article>
  );
}

function formatConfidence(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function formatDateTime(value) {
  if (!value) return "-";
  const hasTimezone = /(?:z|[+-]\d{2}:\d{2})$/i.test(value);
  const parsed = new Date(hasTimezone ? value : `${value}Z`);

  return Number.isNaN(parsed.getTime()) ? "-" : parsed.toLocaleString();
}

function compactUntrustedText(value, maxLength) {
  const text = String(value || "").replace(/\s+/g, " ").trim();

  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 3).trim()}...`;
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
            <th>Area</th>
            <th>Rischio</th>
            <th>Percorso</th>
            <th>Umano</th>
            <th>Follow-up</th>
            <th>Creata</th>
            <th scope="col"><span className="sr-only">Azioni</span></th>
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
              <td>{ticket.operational_area}</td>
              <td>
                <span className={`risk risk-${ticket.risk_score}`}>{ticket.risk_score}/5</span>
              </td>
              <td>{ticket.escalation}</td>
              <td>{ticket.human_handoff ? "Sì" : "No"}</td>
              <td>{ticket.follow_up_status}</td>
              <td>{formatDateTime(ticket.created_at)}</td>
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
