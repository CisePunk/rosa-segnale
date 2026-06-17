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
        ip_hash=_hash_ip(_client_ip(request)),
        user_agent=request.headers.get("user-agent", "")[:300],
        query_present=bool(request.url.query),
    )


def _client_ip(request: Request) -> str:
    forwarded_headers = (
        request.headers.get("cf-connecting-ip"),
        request.headers.get("x-real-ip"),
        request.headers.get("x-forwarded-for", "").split(",")[0].strip(),
    )

    for value in forwarded_headers:
        if value:
            return value

    return request.client.host if request.client else "unknown"


def _hash_ip(ip_address: str) -> str:
    salt = os.getenv("HONEYPOT_HASH_SALT", "rosa-segnale-local-honeypot")
    return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()[:24]
