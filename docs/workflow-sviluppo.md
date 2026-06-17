# Workflow di sviluppo

Documento sintetico sul processo seguito per realizzare Rosa Segnale.

## Impostazione

Il progetto parte da una traccia didattica Python e AI e la applica a un caso d'uso più strutturato:

- ascolto iniziale
- triage orientativo
- dashboard interna
- reportistica
- presa in carico umana
- sicurezza dello staging

## Scelte progettuali

Le scelte principali sono state definite prima dell'implementazione:

- separazione tra vista pubblica e area interna
- assenza di geolocalizzazione browser
- minimizzazione dei dati richiesti
- gestione esplicita dei messaggi brevi
- fallback locale se il provider esterno non è disponibile
- tracciabilità di classificazione, rischio, provider e timestamp
- gestione separata di alert, ticket ed eventi honeypot

## Sviluppo

Il lavoro è stato organizzato per moduli:

- backend API
- repository SQLite
- triage e regole di sicurezza
- assistente conversazionale
- dashboard React
- documentazione
- test automatici

Ogni modifica rilevante è stata verificata con test automatici o build del frontend.

## Validazione

Validazioni eseguite:

- test unitari backend
- build frontend
- audit dipendenze frontend
- audit dipendenze backend
- prove manuali su vista pubblica e area interna
- verifica degli endpoint principali

Ultima verifica:

```text
Backend tests: 50 OK
Frontend build: OK
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

Data verifica: 17 giugno 2026.

## Limiti

Rosa Segnale resta un prototipo tecnico.

Per un uso reale servono:

- autenticazione per ruoli
- audit log non modificabile
- cifratura dati sensibili
- gestione sicura dei segreti
- HTTPS
- retention policy
- revisione GDPR
- protocollo operativo con persone formate
