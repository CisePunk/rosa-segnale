import hashlib
import os
from dataclasses import dataclass

from fastapi import Request


TRAP_PATHS = {
    "/admin",
    "/administrator",
    "/login",
    "/wp-admin",
    "/wp-login.php",
    "/xmlrpc.php",
    "/phpmyadmin",
    "/.env",
    "/debug",
    "/server-status",
    "/actuator/env",
}

SUSPICIOUS_TOKENS = (
    ".env",
    "wp-",
    "phpmyadmin",
    "xmlrpc",
    "cgi-bin",
    "actuator",
    "server-status",
    "debug",
    "select%20",
    "union%20",
    "../",
    "%2e%2e",
    "<script",
)


@dataclass(frozen=True)
class HoneypotMatch:
    path: str
    method: str
    reason: str
    risk_score: int
    ip_hash: str
    user_agent: str
    query_present: bool


def inspect_request(request: Request) -> HoneypotMatch | None:
    path = request.url.path
    lowered = path.lower()
    query = request.url.query.lower()
    combined = f"{lowered}?{query}" if query else lowered

    if lowered in TRAP_PATHS:
        reason = "trap_path"
        risk_score = 4
    elif any(token in combined for token in SUSPICIOUS_TOKENS):
        reason = "suspicious_pattern"
        risk_score = 3
    else:
        return None

    return HoneypotMatch(
        path=path[:300],
        method=request.method[:12],
        reason=reason,
        risk_score=risk_score,
        ip_hash=_hash_ip(client_ip(request)),
        user_agent=request.headers.get("user-agent", "")[:300],
        query_present=bool(request.url.query),
    )


def client_ip(request: Request) -> str:
    # Dietro un reverse proxy, request.client.host e' l'IP DEL PROXY: un secchio solo
    # per tutti. TRUST_PROXY_HEADER va impostata SOLO se davanti c'e' un proxy fidato:
    # altrimenti l'header lo scrive chi fa la richiesta e si falsifica a piacere.
    intestazione = (os.getenv("TRUST_PROXY_HEADER") or "").strip().lower()
    if intestazione:
        grezzo = request.headers.get(intestazione)
        if grezzo:
            # L'ULTIMO valore: lo aggiunge il proxy. I primi li manda il client, e
            # prendendo quelli il freno si aggirava cambiando header a ogni richiesta.
            ultimo = grezzo.split(",")[-1].strip()
            if ultimo:
                return ultimo
    return request.client.host if request.client else "unknown"


def _hash_ip(ip_address: str) -> str:
    salt = (os.getenv("HONEYPOT_HASH_SALT") or "").strip()
    # Senza un sale segreto questo campo NON anonimizza niente: gli IPv4 sono
    # quattro miliardi, e con il sale noto si invertono per forza bruta in
    # pochi secondi. Il valore di ripiego stava scritto nel repository, che e'
    # pubblico: valeva come sale quanto nessun sale. Meglio non registrare
    # l'indirizzo che registrarlo credendolo protetto.
    if not salt:
        return "senza-sale"
    return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()[:24]
