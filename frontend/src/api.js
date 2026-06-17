const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000");
const DEFAULT_TIMEOUT_MS = 10000;
const ASSISTANT_TIMEOUT_MS = 30000;

function normalizeApiBaseUrl(value) {
  const parsedUrl = new URL(value);

  if (import.meta.env.PROD && parsedUrl.protocol !== "https:" && !isLocalOrLanHost(parsedUrl.hostname)) {
    throw new Error("In produzione pubblica VITE_API_BASE_URL deve usare HTTPS.");
  }

  return parsedUrl.origin;
}

function isLocalOrLanHost(hostname) {
  return (
    hostname === "localhost"
    || hostname === "127.0.0.1"
    || hostname.startsWith("192.168.")
    || hostname.startsWith("10.")
    || /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
  );
}

async function request(path, options = {}) {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(fetchOptions.headers || {}),
      },
      ...fetchOptions,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(await safeErrorMessage(response));
    }

    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Richiesta scaduta. Riprova tra poco.");
    }

    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

async function safeErrorMessage(response) {
  const text = await response.text();

  if (import.meta.env.PROD) {
    return `Operazione non riuscita. Codice errore ${response.status}.`;
  }

  try {
    const payload = text ? JSON.parse(text) : null;

    if (Array.isArray(payload?.detail)) {
      return payload.detail
        .map((item) => `${item.loc?.join(".") || "field"}: ${item.msg}`)
        .join(" | ");
    }

    if (payload?.detail) {
      return String(payload.detail);
    }
  } catch {
    if (text) return text;
  }

  return `Request failed with status ${response.status}`;
}

export function fetchHealth() {
  return request("/health");
}

export function fetchDashboard() {
  return request("/dashboard");
}

export function fetchTickets() {
  return request("/tickets");
}

export function fetchAlerts() {
  return request("/alerts");
}

export function fetchHoneypotEvents() {
  return request("/security/honeypot-events");
}

export function updateAlert(alertId, payload) {
  return request(`/alerts/${alertId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function takeAlert(alertId) {
  return request(`/alerts/${alertId}/take`, {
    method: "PATCH",
  });
}

export function closeAlert(alertId) {
  return request(`/alerts/${alertId}/close`, {
    method: "PATCH",
  });
}

export function seedSampleTickets() {
  return request("/sample-data/seed", {
    method: "POST",
  });
}

export function updateTicketFollowUp(ticketId, payload) {
  return request(`/tickets/${ticketId}/follow-up`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function askAssistant(question) {
  return request("/assistant/answer", {
    method: "POST",
    timeoutMs: ASSISTANT_TIMEOUT_MS,
    body: JSON.stringify({
      question,
      top_k: 3,
    }),
  });
}

export function fetchWeeklyReport() {
  return request("/reports/weekly");
}
