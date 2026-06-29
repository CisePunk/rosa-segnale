# Rosa Segnale

## Descrizione

Portale di ascolto, primo orientamento e triage non diagnostico basato su Python, FastAPI, React, OpenAI e base di conoscenza interna.

## Origine del progetto

Adattamento della traccia "progetto finale Python e AI".
La struttura tecnica richiesta è stata mantenuta:

- classificazione
- retrieval da knowledge base
- risposta generata con AI
- report
- tracciabilità

L'idea è nata dall'esigenza di trasformare una traccia generica in qualcosa di più vicino a un contesto reale di ascolto e rischio. L'architettura, le scelte di flusso, la separazione tra vista pubblica e area interna, la mancata geolocalizzazione, i percorsi rapidi e le cautele sui dati sono decisioni progettuali umane, costruite prima della generazione del codice.

Il progetto è nato come prototipo didattico e si è evoluto in una base tecnica pensata per essere riusata, adattata e donata ad associazioni, centri antiviolenza, sportelli di ascolto, enti del terzo settore e realtà territoriali.

Implementazioni operative recenti: [docs/implementazioni-operative.md](docs/implementazioni-operative.md).

Preparazione staging sicuro: [docs/staging-sicuro.md](docs/staging-sicuro.md).

Screenshot dimostrativi: [docs/screenshots](docs/screenshots).

## Avviso importante

Rosa Segnale è nato come prototipo didattico, ma si è evoluto in una base tecnica per un progetto civico riusabile.

Il codice è pensato per essere studiato, adattato e donato ad associazioni, centri antiviolenza, sportelli di ascolto, enti del terzo settore e realtà territoriali che vogliano sviluppare strumenti digitali di primo orientamento, triage e presa in carico umana.

Le prove vanno eseguite con dati fittizi o anonimizzati.

Per pericolo immediato: 112.
Per supporto antiviolenza e antistalking in Italia: 1522.

Il progetto include già logiche per ascolto, ponte umano, alert interni, honeypot di staging, violenza economica, violenza verbale, controllo coercitivo e scenari con minori.

Un uso reale richiede revisione privacy, sicurezza applicativa, procedure operative, persone formate e validazione con soggetti competenti.

## Funzionalità

- vista pubblica Ascolto
- area interna per operatori e revisione
- triage orientativo delle segnalazioni
- risk score orientativo
- percorsi suggeriti
- punto di ascolto con base di conoscenza e provider AI configurabile
- regole di sicurezza post-classificazione con soglie minime di rischio
- gestione messaggi brevi e ambigui ("aiuto", "lui sta tornando", "non posso parlare")
- percorso silenzioso per chi non può parlare o telefonare
- gestione esplicita di gravidanza, minorenne come soggetto scrivente, isolamento sociale, armi, separazione recente
- risposta dedicata a richieste di cancellazione della chat
- riferimenti territoriali siciliani (mappatura 1522, rete D.i.Re.)
- Telefono Amico Italia: 02 2327 2327, indicato dal sito ufficiale come attivo tutti i giorni dalle 9 alle 24 alla verifica del 10 giugno 2026
- report aggregati
- report settimanale automatico
- follow-up operativo sui casi registrati
- alert interni per ponte umano
- honeypot applicativo per staging controllato
- segnali di giudizio AI: tono rilevato, confidenza urgenza, confidenza uso improprio
- categorie aggiunte per controllo coercitivo, violenza economica, violenza verbale e contesto chiuso o istituzionale
- base predisposta per evoluzioni su violenza che coinvolge minori
- logging provider/modello/timestamp

## Stack

Backend: Python, FastAPI, Pydantic, SQLite, OpenAI API opzionale, python-dotenv, Uvicorn.

Frontend: React, Vite, lucide-react, CSS custom.

AI: provider configurabile, modello predefinito `gpt-4o-mini`, base di conoscenza interna, fallback locale e regole di sicurezza.

## Architettura

Frontend React su porta 5173.

Backend FastAPI su porta 8000.

Base di conoscenza interna.

Report automatici e tracciabilità lato backend.

## Viste dell'applicazione

### Ascolto

Vista pubblica per richieste di orientamento. Mostra risorse rapide, avviso di sicurezza e assistente conversazionale. Non espone KPI, report, provider, registro segnalazioni o log interni.

Il punto di ascolto usa la base di conoscenza interna e un provider AI configurabile. Il fallback locale mantiene il flusso disponibile anche senza chiamate esterne.

Risorse rapide:

- 112
- 1522
- YouPol

### Area interna

Vista interna per gestione e revisione. Contiene dashboard, report settimanale, registro segnalazioni, classificazione, follow-up operativo, alert umani, eventi honeypot e tracciabilità.

Gli alert vengono creati quando il triage individua un caso che richiede ponte umano. L'operatore può prendere in carico, aggiornare e chiudere l'alert.

Gli eventi honeypot registrano richieste sospette allo staging, come percorsi `/wp-login.php`, `/.env`, `/admin` o pattern di scansione. Gli IP non vengono salvati in chiaro, ma trasformati in hash.

Il backend genera automaticamente un report settimanale in `reports/weekly_report_latest.md`.
L'intervallo predefinito è 7 giorni ed è configurabile con:

```env
AUTO_WEEKLY_REPORT_INTERVAL_SECONDS=604800
TRIAGE_DB_PATH=triage.db
REPORTS_DIR=../reports
```

Il report può essere rigenerato anche manualmente dalla UI interna o con:

```bash
python3 scripts/generate_weekly_report.py
```

Le route interne possono essere protette con Basic Auth impostando entrambe le variabili:

```env
INTERNAL_AUTH_USERNAME=replace_with_internal_username
INTERNAL_AUTH_PASSWORD=replace_with_internal_password
```

Se le variabili non sono presenti, l'area interna resta aperta per la demo locale.

### Confine pubblico / interno

La route `/assistant/answer` è pubblica nella demo: applica policy locale e rate limit prima del retrieval e della risposta AI.

Le route operative interne, incluse ticket, alert, dashboard, report e preview triage, passano da `require_internal_auth`. In locale la protezione è opzionale tramite Basic Auth. In produzione va sostituita o rafforzata con autenticazione per ruoli, sessioni sicure, audit accessi e rate limit dedicato.

## Base di conoscenza interna

Undici fonti tematiche embedded nel backend, usate per il retrieval e per generare le risposte:

- Emergenza immediata 112
- Paura di rientrare e piano di sicurezza
- Numero antiviolenza 1522
- Stalking e controllo
- Documentazione e supporto legale
- Supporto medico e sanitario
- Supporto emotivo e autolesionismo
- Gravidanza e violenza
- Utente minorenne
- Riferimenti territoriali Sicilia
- Privacy e minimizzazione
- Controllo coercitivo e ponte umano
- Violenza economica e verbale

## Geolocalizzazione

Il portale non usa la geolocalizzazione del browser, per scelta deliberata.

La richiesta di geolocalizzazione del browser può essere visibile a chi guarda lo schermo, può lasciare tracce nelle impostazioni del dispositivo o del browser e non è necessaria per la logica applicativa.

In caso di emergenza immediata, la persona viene indirizzata al 112. Dove supportato dal dispositivo, dalla rete e dalla centrale competente, i sistemi di emergenza possono usare tecnologie di localizzazione come AML (Advanced Mobile Location). Per l'orientamento ai servizi territoriali, il sistema rimanda al 1522, che dispone di una mappatura aggiornata dei servizi antiviolenza.

## Prova suggerita

Frasi utili per provare il punto di ascolto:

- aiuto
- lui sta tornando
- non posso parlare
- non sono sola
- Sono in centro e un uomo mi segue.
- Ho paura a tornare a casa e non so a chi rivolgermi.
- Ho screenshot dei messaggi, non so come conservarli.
- Sono incinta e ho paura di lui.
- Ho diciassette anni e ho paura a casa.
- Mi ha allontanata dalla mia famiglia e non mi lascia vedere le mie amiche.
- Ci siamo lasciati e non accetta che sia finita.
- Ha una pistola in casa.
- Cancella tutto.

## Configurazione AI

La chiave OpenAI va inserita solo in un file locale non versionato:

```bash
cd backend
cp .env.example .env
```

Esempio:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=replace_with_your_local_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=350
AUTO_WEEKLY_REPORT_INTERVAL_SECONDS=604800
TRIAGE_DB_PATH=triage.db
REPORTS_DIR=../reports
```

Opzionale, per proteggere le route interne con Basic Auth:

```env
INTERNAL_AUTH_USERNAME=replace_with_internal_username
INTERNAL_AUTH_PASSWORD=replace_with_internal_password
```

Non caricare `.env`, `key.env`, `.venv`, `node_modules`, `dist` o database locali su GitHub.

L'integrazione OpenAI è configurabile tramite `.env` locale. Il backend include un fallback locale.

## Avvio backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Avvio frontend

```bash
cd frontend
npm install
npm run dev
```

## Demo flow suggerito

1. Avviare backend e frontend.
2. Aprire la vista pubblica di ascolto.
3. Provare messaggi brevi o ambigui, per esempio:
   - `aiuto`
   - `non posso parlare`
   - `lui sta tornando`
4. Verificare la risposta orientativa e le risorse rapide.
5. Aprire l'area interna per controllare dashboard, alert, registro segnalazioni e report.

## Test

```bash
cd backend
python3 -m unittest discover -s tests
```

## Matrice di test

La matrice si trova in:

[docs/matrice-test-triage.md](docs/matrice-test-triage.md)

## Riuso gratuito

Il progetto è rilasciato con licenza MIT.
Associazioni, enti del terzo settore, sportelli di ascolto, centri antiviolenza e progetti civici possono usare e adattare gratuitamente il codice, nel rispetto della licenza e dopo adeguate verifiche privacy, sicurezza e operative.

L'obiettivo non è vendere un prodotto, ma lasciare una base tecnica documentata da cui partire: interfaccia pubblica, dashboard interna, triage orientativo, alert umani, reportistica, honeypot e cautele sui dati.

Il progetto è già predisposto per evoluzioni legate alla violenza su minori, alla presa in carico territoriale e a protocolli operativi supervisionati.

Dettagli:

- [LICENSE](LICENSE)
- [docs/uso-associazioni.md](docs/uso-associazioni.md)
- [docs/workflow-sviluppo.md](docs/workflow-sviluppo.md)
- [docs/threat-model.md](docs/threat-model.md)
- [SECURITY.md](SECURITY.md)
- [PRIVACY.md](PRIVACY.md)

## Cosa manca per un uso reale

Per trasformare Rosa Segnale in servizio operativo servono ulteriori implementazioni, tra cui:

- autenticazione robusta con sessioni, ruoli granulari e audit accessi (la Basic Auth opzionale sulle route interne non è sufficiente per produzione);
- cifratura dei dati sensibili a riposo;
- informative privacy, consenso, retention e procedure GDPR;
- gestione sicura dei segreti e deploy HTTPS;
- rate limit e protezione da abuso delle API;
- logging e audit trail non modificabile;
- backup, monitoring e alerting;
- revisione legale, psicologica e operativa dei testi;
- validazione dei numeri utili e dei riferimenti territoriali;
- policy chiara su quali dati vengono inviati al provider AI;
- procedure supervisionate per pericolo imminente, minori, autolesionismo e casi sanitari;
- test di sicurezza e revisione prima del deploy;
- canale di notifica operatori, per esempio Telegram, Signal o altro strumento scelto dal presidio umano;
- turni operatori, SLA e procedure di escalation;
- blocco automatico o rate limit avanzato sugli eventi sospetti rilevati dall'honeypot;
- ambiente staging HTTPS con accesso protetto;
- adattamento dei flussi per casi che coinvolgono minori, con soggetti qualificati e procedure dedicate.

Queste attività vanno progettate con l'organizzazione che vuole utilizzarlo, in base al territorio, alle persone disponibili, ai protocolli interni e ai soggetti istituzionali coinvolti.

## Presentazione

Un testo breve da leggere o adattare per spiegare il progetto si trova in:

[docs/testo-presentazione.md](docs/testo-presentazione.md)

## Stato

- backend FastAPI attivo su `127.0.0.1:8000`
- frontend Vite attivo su `127.0.0.1:5173`
- provider AI configurabile tramite `.env`
- fallback locale disponibile
- alert interni e honeypot applicativo implementati
- dashboard interna con KPI, alert, follow-up, registro ticket e monitoraggio honeypot
- documentazione tecnica aggiornata in `docs/`
- screenshot dimostrativi in `docs/screenshots/`
- 53 controlli eseguiti alla verifica del 29 giugno 2026
- 50 test backend OK alla verifica del 29 giugno 2026
- frontend build OK alla verifica del 29 giugno 2026
- `npm audit`: 0 vulnerabilità alla verifica del 29 giugno 2026
- `pip-audit`: nessuna vulnerabilità nota alla verifica del 29 giugno 2026
