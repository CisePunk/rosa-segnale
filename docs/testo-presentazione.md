# Presentazione breve

Rosa Segnale è un prototipo web per ascolto, orientamento e triage non diagnostico in contesti di rischio.

Il sistema è diviso in due viste.

La vista pubblica contiene:

- risorse rapide: 112, 1522, YouPol
- avviso di sicurezza
- assistente conversazionale
- codice locale non identificativo
- campo libero per messaggi brevi

L'area interna contiene:

- KPI aggregati
- registro segnalazioni
- classificazione orientativa
- livello di rischio
- area operativa
- alert per presa in carico umana
- follow-up operativo
- eventi honeypot
- report settimanale

Il backend è sviluppato con Python, FastAPI, Pydantic e SQLite.

Il frontend è sviluppato con React, Vite e CSS custom.

La parte AI usa:

- provider configurabile
- modello predefinito `gpt-4o-mini`
- base di conoscenza interna
- fallback locale
- regole di sicurezza post-classificazione

Il triage distingue:

- ascolto e orientamento
- ponte umano
- intervento immediato
- supporto territoriale
- uso non operativo

Sono presenti controlli specifici per:

- messaggi brevi come `Rosa`, `aiuto`, `non posso parlare`
- controllo coercitivo
- violenza economica
- violenza verbale
- stalking e controllo
- presenza di minori
- gravidanza
- armi o minaccia immediata
- richieste fuori ambito o uso improprio

Il progetto include anche un honeypot applicativo per lo staging. Gli eventi sospetti vengono registrati in una tabella separata, con IP hashato e dati tecnici minimi.

Verifiche attuali:

```text
Controlli totali: 53
Backend tests: 50 OK
Frontend build: OK
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

Rosa Segnale è un prototipo tecnico. Un uso reale richiede revisione privacy, sicurezza, legale e operativa.
