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

## Workflow di sviluppo

Il progetto è stato costruito con una pipeline human-in-the-loop: architettura umana, prompt mirati, generazione AI assistita, lettura e audit riga per riga, test manuali per scene, test automatici, cross-review multi-modello e revisione tecnica esterna. Le competenze maturate in quattro anni di lavoro con LLM e automazioni AI sono state applicate specificando contesto, vincoli, criteri di accettazione e casi limite per componenti circoscritti, refactoring, test, privacy, prompt injection, CVE, bias e instradamento delle emergenze. Idea, struttura, priorità di rischio e risultato finale restano responsabilità umana. Dettagli: [docs/workflow-sviluppo.md](docs/workflow-sviluppo.md).

## Avviso importante

Il sistema è un prototipo didattico.
Non sostituisce servizi di emergenza, centri antiviolenza, supporto medico, psicologico o legale.
In caso di pericolo immediato, chiamare il 112.
Per supporto antiviolenza e antistalking in Italia, contattare il 1522, servizio pubblico gratuito attivo 24 ore su 24.

Le prove devono usare solo dati fittizi o anonimizzati.
Non inserire nomi, indirizzi, numeri di telefono, screenshot reali, conversazioni identificabili o dettagli che possano ricondurre a persone reali.

Il codice non è pronto per la produzione reale senza ulteriori revisioni professionali.

## Funzionalità

- vista pubblica Ascolto
- area interna per back office e revisione
- triage orientativo delle segnalazioni
- risk score orientativo
- percorsi suggeriti
- punto di ascolto AI con base di conoscenza
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
- logging provider/modello/timestamp

## Stack

Backend: Python, FastAPI, Pydantic, SQLite, OpenAI API, python-dotenv, Uvicorn.

Frontend: React, Vite, lucide-react, CSS custom.

AI: OpenAI tramite provider configurabile, modello predefinito `gpt-4o-mini`, base di conoscenza interna, fallback locale e regole di sicurezza.

## Architettura

Frontend React su porta 5173.

Backend FastAPI su porta 8000.

Base di conoscenza interna.

Report automatici e tracciabilità lato backend.

## Viste dell'applicazione

### Ascolto

Vista pensata per la persona che cerca orientamento.
Mostra solo risorse rapide, avviso di sicurezza e assistente conversazionale.
Non mostra KPI, report, provider, registro segnalazioni o dettagli tecnici.
La vista pubblica non espone casi, dashboard, provider AI o log interni.

Il punto di ascolto usa OpenAI per generare una risposta empatica e modulata.
La base di conoscenza interna non viene mostrata come testo copiato: serve a indirizzare verso il passo più utile, per esempio 112, 1522, centro antiviolenza, supporto legale qualificato o servizi competenti.

Risorse rapide:

- 112
- 1522
- YouPol

### Area interna

Vista pensata per docente, revisione tecnica o back office.
Contiene dashboard, report settimanale, registro segnalazioni, classificazione, follow-up operativo e tracciabilità.
Non carica casi precompilati: il registro mostra solo le segnalazioni inserite dall'utente.

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

Non caricare mai `.env`, `key.env`, `.venv`, `node_modules`, `dist` o database locali su GitHub.

L'integrazione OpenAI è configurabile tramite `.env` locale. Se la chiamata AI non è disponibile, il backend usa un fallback locale per mantenere la demo utilizzabile.

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
- test di sicurezza e revisione prima del deploy.

Queste attività possono essere progettate e implementate su richiesta, adattando Rosa Segnale alle esigenze reali dell'organizzazione che vuole utilizzarlo.

## Presentazione

Un testo breve da leggere o adattare per spiegare il progetto si trova in:

[docs/testo-presentazione.md](docs/testo-presentazione.md)

## Stato

- backend compilato
- health check OK
- integrazione OpenAI configurabile tramite `.env` locale
- fallback locale disponibile se la chiamata AI non riesce
- 43 test automatici OK alla verifica del 10 giugno 2026 (triage rules, chat policy, assistant provider, auth)
- dipendenze verificate con `npm audit` e `pip-audit` al 9 giugno 2026, senza vulnerabilità note rilevate
- revisione tecnica esterna qualificata completata
- punto di ascolto AI funzionante
- campo messaggio vuoto all'apertura, senza frase pre-compilata
