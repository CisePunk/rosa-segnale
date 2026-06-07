const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    const text = await response.text();

    try {
      const payload = text ? JSON.parse(text) : null;

      if (Array.isArray(payload?.detail)) {
        message = payload.detail
          .map((item) => `${item.loc?.join(".") || "field"}: ${item.msg}`)
          .join(" | ");
      } else if (payload?.detail) {
        message = String(payload.detail);
      }
    } catch {
      if (text) message = text;
    }

    throw new Error(message);
  }

  return response.json();
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
    body: JSON.stringify({
      question,
      top_k: 3,
    }),
  });
}

export function fetchWeeklyReport() {
  return request("/reports/weekly");
}
