# Implementazioni operative Rosa Segnale

Documento tecnico sintetico sulle implementazioni aggiunte per preparare Rosa Segnale a un flusso con ascolto, triage e successiva presa in carico umana.

## Stato del sistema

Stato attuale: prototipo operativo locale.

Uso previsto in questa fase:

- demo tecnica
- test di flusso su browser e telefono in rete locale
- validazione del modello operativo
- preparazione a un presidio umano
- preparazione a interlocuzione con soggetti territoriali e istituzionali

Uso non previsto in questa fase:

- servizio pubblico reale
- servizio di emergenza
- sostituzione di 112, 1522, centri antiviolenza, supporto medico, psicologico o legale
- raccolta di dati reali o identificativi
- disponibilità 24/7 garantita

## Obiettivo tecnico

Preparare la piattaforma a distinguere tra:

- richiesta di ascolto e orientamento
- richiesta che necessita di persona reale
- richiesta con possibile pericolo immediato
- richiesta fuori ambito o uso improprio

La finalità è rendere il backend utilizzabile come base per:

- dashboard interna
- turnazione operatori
- alert operativi
- report anonimi e aggregati
- successivo protocollo di presa in carico territoriale

## Aree operative introdotte

Sono state aggiunte aree operative esplicite nel modello dati.

Valori:

- `Ascolto e orientamento`
- `Ponte umano`
- `Intervento immediato`
- `Supporto territoriale`
- `Non operativo`

Utilità:

- separare i messaggi di comprensione da quelli urgenti
- distinguere la risposta del bot dalla necessità di una persona reale
- preparare filtri e priorità nella dashboard interna
- preparare report aggregati leggibili da soggetti non tecnici

Preparazione per:

- coda alert
- presa in carico da operatore
- smistamento per rischio
- turni di presidio
- protocolli di escalation

File coinvolti:

- `backend/app/models.py`
- `backend/app/repository.py`
- `backend/app/triage_rules.py`
- `backend/app/ai_providers.py`
- `frontend/src/main.jsx`

## Flag operativo `human_handoff`

È stato aggiunto il campo:

```text
human_handoff: bool
```

Significato:

- `true`: il caso richiede o può richiedere passaggio a persona reale
- `false`: il caso può restare in ascolto/orientamento automatico o non operativo

Utilità:

- evidenziare i casi da non lasciare solo al bot
- preparare una coda operatori
- ridurre il rischio che richieste sensibili restino senza contatto umano

Preparazione per:

- dashboard “richiede persona reale”
- assegnazione operatore
- presa in carico
- tracciamento stato alert

## Flag operativo `suspected_misuse`

È stato aggiunto il campo:

```text
suspected_misuse: bool
```

Significato:

- `true`: possibile test, abuso, scherzo esplicito o richiesta fuori ambito
- `false`: richiesta operativa o non chiaramente abusiva

Utilità:

- non saturare una futura coda operatori con test evidenti
- mantenere prudenza sui messaggi ambigui
- distinguere “aiuto” breve da cazzeggio esplicito

Regola di cautela:

- messaggi brevi come `aiuto`, `non posso parlare`, `lui sta tornando` non vengono scartati
- messaggi esplicitamente scherzosi o non pertinenti possono essere marcati come non operativi

Preparazione per:

- rate limiting operativo
- revisione manuale dei falsi positivi
- protezione del presidio umano

## Nuove categorie di triage

Sono state aggiunte categorie per violenze non fisiche o meno visibili.

Nuove categorie:

- `Controllo coercitivo`
- `Violenza economica`
- `Violenza verbale`
- `Contesto chiuso o istituzionale`

Utilità:

- riconoscere richieste non legate solo all’emergenza fisica
- trattare controllo del telefono, isolamento e limiti agli spostamenti come segnali operativi
- includere violenza economica e verbale
- non minimizzare situazioni senza aggressione fisica

Preparazione per:

- ascolto precoce
- orientamento verso persona reale
- orientamento verso 1522 o centro antiviolenza
- reportistica su forme di violenza non emergenziale

## Controllo coercitivo

Il sistema riconosce segnali come:

- telefono tolto
- telefono disponibile solo per poco tempo
- impossibilità di scrivere o chiamare liberamente
- controllo degli spostamenti
- impossibilità di uscire liberamente
- isolamento da famiglia, amiche o amici
- permanenza in casa, comunità o contesto chiuso
- uscita possibile solo per commissioni

Classificazione prevista:

- categoria: `Controllo coercitivo`
- area operativa: `Ponte umano`
- `human_handoff: true`
- rischio minimo: alto nei casi di telefono/spostamenti controllati

Utilità:

- intercettare persone che hanno finestre brevi per scrivere
- evitare risposte lunghe o inutili in contesti di sorveglianza
- preparare un canale umano più discreto

## Violenza economica

Il sistema riconosce segnali come:

- controllo dei soldi
- accesso negato a conto, bancomat o spese
- impedimento a lavorare
- dipendenza economica forzata
- obbligo di chiedere denaro

Classificazione prevista:

- categoria: `Violenza economica`
- area operativa: `Ponte umano`
- `human_handoff: true`

Utilità:

- trattare la dipendenza materiale come forma di rischio
- orientare verso centro antiviolenza, 1522 o supporto territoriale
- separare il bisogno economico dalla semplice richiesta pratica

## Violenza verbale e psicologica

Il sistema riconosce segnali come:

- insulti
- umiliazioni
- urla
- svalutazione
- frasi come “non vali niente”
- gaslighting
- “mi fa sentire pazza”

Classificazione prevista:

- categoria: `Violenza verbale`
- area operativa: `Ascolto e orientamento` o `Ponte umano`
- `human_handoff: true` quando la richiesta indica bisogno di supporto reale

Utilità:

- non ridurre la violenza a aggressione fisica
- dare cornice alla persona che scrive per capire
- facilitare passaggio a persona reale quando la situazione appare ripetuta o controllante

## Prompt e risposta dell’assistente

Il prompt del punto di ascolto è stato riallineato.

Nuove istruzioni operative:

- distinguere ascolto, ponte umano e intervento immediato
- riconoscere controllo coercitivo
- riconoscere violenza economica
- riconoscere violenza verbale e psicologica
- rispondere in modo breve se telefono o comunicazione possono essere controllati
- proporre persona reale quando utile
- non promettere disponibilità 24/7 se non dichiarata
- non dichiarare invii automatici ad autorità

Utilità:

- evitare risposte solo emergenziali
- trattare anche casi lenti, ambigui o normalizzati
- preparare una futura integrazione con presidio umano

File coinvolti:

- `backend/app/assistant_provider.py`
- `backend/app/knowledge.py`

## Knowledge base interna

Sono state aggiunte fonti interne su:

- controllo coercitivo
- ponte umano
- violenza economica
- violenza verbale

Utilità:

- migliorare retrieval e risposta locale
- rendere il fallback più aderente al dominio
- ridurre dipendenza dal solo modello esterno

Preparazione per:

- risposte più coerenti anche senza OpenAI
- audit dei contenuti di indirizzamento
- estensione verso fonti territoriali verificate

## Persistenza SQLite

Sono state aggiunte colonne migrabili nella tabella `tickets`:

```text
operational_area
human_handoff
suspected_misuse
```

La migrazione avviene tramite `ALTER TABLE` se le colonne non esistono.

Utilità:

- compatibilità con database già esistenti
- nessuna cancellazione dei ticket precedenti
- preparazione a dashboard e report operativi

File coinvolto:

- `backend/app/repository.py`

## Dashboard interna

La dashboard è stata aggiornata per mostrare:

- numero di casi con ponte umano
- area operativa del caso
- badge `Richiede persona reale`
- badge `Possibile abuso/test`
- distribuzione per area operativa

Utilità:

- visibilità immediata dei casi da non lasciare al bot
- separazione tra ascolto e intervento
- base per una futura coda operatori

Preparazione per:

- stato `Nuovo`
- stato `In carico`
- assegnazione operatore
- chiusura caso
- report per periodo e area operativa

File coinvolti:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`

## Sistema alert interno

È stato aggiunto un primo sistema alert per la presa in carico umana.

Componenti implementati:

- modello `Alert`
- tabella SQLite `alerts`
- endpoint `POST /alerts`
- endpoint `GET /alerts`
- endpoint `PATCH /alerts/{id}`
- endpoint `PATCH /alerts/{id}/take`
- endpoint `PATCH /alerts/{id}/close`
- creazione automatica alert da ticket con `human_handoff: true`
- pannello frontend `Alert in arrivo`

Stati alert:

- `Nuovo`
- `In carico`
- `Chiuso`

Campi principali:

```text
ticket_id
source
title
summary
risk_score
operational_area
status
operator_label
internal_note
created_at
taken_at
closed_at
```

Utilità:

- separare i casi operativi dal registro generale
- rendere visibili i casi che richiedono persona reale
- permettere presa in carico esplicita
- evitare che un caso con `human_handoff` resti solo nel flusso bot

Preparazione per:

- notifica operatori
- turni
- assegnazione nominale
- audit log di presa in carico
- SLA di risposta
- integrazione Telegram, Signal o altro canale esterno

File coinvolti:

- `backend/app/models.py`
- `backend/app/repository.py`
- `backend/app/main.py`
- `frontend/src/api.js`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/tests/test_alerts.py`

## Honeypot interno per staging

È stato aggiunto un primo honeypot applicativo per intercettare accessi non coerenti con l’uso previsto dello staging.

Componenti implementati:

- modulo `backend/app/honeypot.py`
- tabella SQLite `honeypot_events`
- middleware FastAPI su ogni richiesta
- endpoint interno `GET /security/honeypot-events`
- pannello frontend `Eventi honeypot`
- test automatici dedicati

Percorsi-esca e pattern monitorati:

- `/admin`
- `/administrator`
- `/login`
- `/wp-admin`
- `/wp-login.php`
- `/xmlrpc.php`
- `/phpmyadmin`
- `/.env`
- `/debug`
- `/server-status`
- `/actuator/env`
- pattern come `../`, `%2e%2e`, `<script`, `union%20`, `select%20`

Dati salvati:

```text
path
method
reason
risk_score
ip_hash
user_agent
query_present
created_at
```

Regola privacy:

- non viene salvato l’indirizzo IP in chiaro
- l’IP viene trasformato in hash breve con salt configurabile
- non vengono salvati contenuti delle conversazioni
- gli eventi honeypot restano separati da ticket e alert

Variabile ambiente:

```env
HONEYPOT_HASH_SALT=valore-lungo-non-pubblico
```

Utilità:

- capire se lo staging pubblico viene scansionato
- distinguere traffico legittimo da rumore tecnico
- preparare una procedura di blocco o chiusura staging
- documentare eventi sospetti durante prove reali controllate

Preparazione per:

- WAF o Cloudflare Zero Trust
- rate limit più severo sugli IP hash ricorrenti
- alert tecnico agli amministratori
- blocco automatico di pattern ad alto rischio
- report sicurezza dello staging

File coinvolti:

- `backend/app/honeypot.py`
- `backend/app/models.py`
- `backend/app/repository.py`
- `backend/app/main.py`
- `frontend/src/api.js`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/tests/test_honeypot.py`

## Segnali di giudizio AI

Sono stati aggiunti campi operativi per rendere più leggibile il giudizio del triage.

Campi:

```text
emotional_tone
urgency_confidence
misuse_confidence
```

Significato:

- `emotional_tone`: sintesi del tono rilevato, ad esempio paura, controllo, confusione, non operativo
- `urgency_confidence`: confidenza numerica sulla possibile urgenza
- `misuse_confidence`: confidenza numerica sul possibile uso improprio

Regola operativa:

- messaggi brevi come `aiuto`, `Rosa`, `non posso parlare`, `lui sta tornando` non devono essere trattati come abuso solo perché hanno poco testo
- il sospetto abuso richiede segnali espliciti di scherzo, test, cazzeggio o contenuto estraneo
- il bottone Rosa mantiene priorità cautelativa perché può arrivare da una persona con pochissimo tempo o sotto controllo

Utilità:

- aiutare l’operatore a capire perché un caso è stato messo in coda
- separare uso improprio esplicito da emergenza compressa
- rendere il comportamento dell’AI più auditabile
- preparare dataset di revisione manuale per affinare il prompt

Preparazione per:

- revisione umana dei falsi positivi
- valutazione qualità del triage
- dataset interno di esempi anonimi
- addestramento o fine tuning futuro solo dopo base legale, consenso e governance dati

## Demo mobile locale

È stata preparata una prova su telefono in rete locale.

Configurazione usata:

```text
Backend: 0.0.0.0:8000
Frontend: 0.0.0.0:5173
Bottone Rosa: 0.0.0.0:5001
```

Esempio IP locale:

```text
http://192.168.1.124:5001
```

Utilità:

- prova da telefono senza pubblicare online
- registrazione demo per presentazione o post tecnico
- verifica del flusso bottone → interfaccia

Preparazione per:

- PWA
- app mobile
- widget o shortcut
- test controllati con stakeholder

Nota:

- la demo mobile locale non è un servizio pubblico
- non usa HTTPS
- non deve raccogliere dati reali
- richiede stessa rete Wi-Fi tra Mac e telefono

## Bottone neutro

Il bottone visibile è stato rinominato da `Aiuto` a `Rosa`.

Utilità:

- ridurre rischio se una persona vicina legge lo schermo
- evitare una parola esplicita in contesti di controllo
- rendere il primo accesso più neutro

Preparazione per:

- modalità discreta
- PWA installabile
- icona neutra su home screen
- futura modalità uscita rapida o schermata neutra

## CORS configurabile

Il backend ora permette origini CORS aggiuntive tramite:

```env
CORS_ALLOW_ORIGINS=http://192.168.1.124:5173
```

Utilità:

- test da telefono
- test su IP LAN
- preparazione ad ambienti staging

File coinvolto:

- `backend/app/main.py`

## Sicurezza e audit

Verifiche eseguite:

```text
Controlli totali: 53
Backend tests: 50 test OK
Frontend build: OK
pip-audit --timeout 60: No known vulnerabilities found
npm audit --audit-level=moderate: found 0 vulnerabilities
```

Data verifica: 29 giugno 2026.

Nota frontend:

- Vite, TypeScript e plugin React sono stati spostati in `devDependencies`
- l’audit runtime non segnala vulnerabilità
- l’audit completo può includere strumenti di build/dev, da trattare separatamente

## Dipendenze frontend

Modifica eseguita:

- `react`, `react-dom`, `lucide-react` restano in `dependencies`
- `vite`, `typescript`, `@vitejs/plugin-react` sono stati spostati in `devDependencies`

Utilità:

- separare runtime e build tooling
- rendere più corretto `npm audit --omit=dev`
- ridurre confusione tra vulnerabilità runtime e vulnerabilità dev

File coinvolti:

- `frontend/package.json`
- `frontend/package-lock.json`

## Stato non ancora implementato

Non sono ancora presenti:

- notifica attiva a operatori
- Telegram bot operatori
- Signal/WhatsApp bridge
- turni operatori
- autenticazione operatori per ruolo
- audit log dedicato alla presa in carico
- SLA di risposta
- protocollo validato con soggetti territoriali
- WAF esterno
- blocco automatico degli IP hash ricorrenti
- ambiente staging pubblico con HTTPS e accesso protetto

## Prossime implementazioni tecniche

Priorità 1:

- assegnazione operatore
- timestamp presa in carico
- nota operativa minima
- canale di notifica operatori
- procedura di prova reale con gruppo umano
- accesso staging protetto
- filtro per area operativa
- filtro per `human_handoff`

Priorità 2:

- notifica operatori su canale esterno
- messaggio senza dati sensibili
- link alla dashboard interna
- rate limiting e anti-abuso dedicati

Priorità 3:

- revisione privacy/GDPR
- DPIA
- policy retention
- cifratura dati sensibili
- deployment HTTPS
- verifica legale e operativa con soggetti qualificati

## Frasi test aggiunte o verificate

Esempi:

```text
Avevo il telefono solo un'ora al giorno e potevo scrivere solo quando uscivo per commissioni.
Mi controlla i soldi e non mi lascia lavorare.
Mi insulta e mi fa sentire pazza, non so se è violenza.
Ahah aiuto lol sto scherzando.
```

Risultati attesi:

```text
Controllo coercitivo | Ponte umano | human_handoff true
Violenza economica | Ponte umano | human_handoff true
Violenza verbale | Ascolto e orientamento | human_handoff true
Fuori ambito | Non operativo | suspected_misuse true
```

## File principali modificati

Backend:

- `backend/app/models.py`
- `backend/app/triage_rules.py`
- `backend/app/ai_providers.py`
- `backend/app/assistant_provider.py`
- `backend/app/knowledge.py`
- `backend/app/repository.py`
- `backend/app/main.py`

Frontend:

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `frontend/src/api.js`
- `frontend/package.json`
- `frontend/package-lock.json`

Test:

- `backend/tests/test_alerts.py`
- `backend/tests/test_triage_rules.py`
- `backend/tests/test_assistant_provider.py`

## Backup prodotti

Backup pre-riallineamento:

```text
backups/rosa-segnale-pre-realign-20260613.zip
```

Backup post-riallineamento:

```text
backups/rosa-segnale-post-realign-20260613.zip
```

Backup demo Flask con fix sicurezza:

```text
backups/prova-flask-rosa-segnale-security-fix-20260613.zip
```
