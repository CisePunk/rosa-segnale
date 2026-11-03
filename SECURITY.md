# Security

Rosa Segnale è un prototipo didattico e non deve essere usato in produzione senza una revisione di sicurezza dedicata.

Il progetto tratta scenari potenzialmente sensibili. Per questo motivo deve essere eseguito, testato e dimostrato solo con dati fittizi, simulati o anonimizzati.

Il threat model del progetto è documentato in [docs/threat-model.md](docs/threat-model.md).

## Segnalazione vulnerabilità

Per segnalare vulnerabilità o problemi di sicurezza, usare preferibilmente il sistema di segnalazione privata di GitHub, se abilitato nel repository, oppure contattare direttamente il maintainer del progetto.

Non aprire issue pubbliche contenenti dettagli sfruttabili, chiavi API, log sensibili, screenshot identificabili, database locali o esempi riconducibili a persone reali.

Non inserire mai nel repository:

- chiavi API;
- file `.env`;
- file `key.env`;
- database locali;
- log contenenti testi sensibili;
- screenshot reali;
- conversazioni identificabili;
- dati personali o sanitari;
- esempi con minori reali o persone riconoscibili.

## Ambito tecnico

Il progetto include alcune misure minime utili per una demo locale, come separazione tra vista pubblica e area interna, fallback locale, configurazione tramite `.env` e Basic Auth obbligatoria sulle route interne.

Queste misure non sono sufficienti per un uso reale o pubblico.

## Requisiti minimi prima di un uso reale

Prima di rendere il servizio accessibile al pubblico servono almeno:

- quick exit e cautele lato dispositivo per persone che usano telefoni condivisi o sorvegliati;
- autenticazione robusta per l'area interna;
- autorizzazioni basate su ruoli;
- gestione sicura delle sessioni;
- protezione CSRF/CORS adeguata al contesto di deploy;
- rate limit e protezione da abuso delle API;
- validazione e sanitizzazione degli input;
- gestione sicura dei segreti;
- deploy HTTPS;
- cifratura dei dati sensibili a riposo;
- cifratura dei dati in transito;
- audit log non modificabile;
- logging sicuro senza esposizione di dati sensibili;
- backup, monitoraggio e alerting;
- dependency scanning;
- controllo delle vulnerabilità note nelle librerie;
- protezione da prompt injection e abuso del provider AI;
- policy su quali dati possono essere inviati al provider AI;
- revisione della knowledge base e workflow di modifica controllato;
- separazione tra ambiente di sviluppo, test e produzione;
- test di sicurezza prima della pubblicazione.

## Provider AI

Se il provider OpenAI o un altro provider AI è attivo, il testo inserito dall'utente può essere inviato al servizio configurato.

Prima di un uso reale è necessario definire controlli specifici per:

- minimizzazione del contenuto inviato;
- esclusione di dati identificativi non necessari;
- gestione dei prompt;
- gestione degli output;
- limiti di lunghezza e consumo;
- protezione contro prompt injection;
- tracciabilità delle chiamate;
- trattamento di errori e fallback;
- policy di logging.

## Area interna

L'area interna non deve essere esposta pubblicamente senza autenticazione robusta, autorizzazioni granulari, audit accessi e protezione delle route.

La Basic Auth serve solo per una demo locale o controllata. Non deve essere considerata una misura sufficiente per un servizio reale.

## Dati locali

Durante lo sviluppo possono essere generati database, report, log e file temporanei.

Questi file devono restare locali, non versionati e non pubblicati.

Prima di condividere il codice verificare sempre che non siano presenti:

- `triage.db`;
- file dentro `reports/` contenenti casi reali;
- log applicativi;
- `.env`;
- `key.env`;
- `.venv`;
- `node_modules`;
- `dist`;
- cache o file temporanei.

## Controllo CVE del 29 giugno 2026

Verifiche eseguite:

```text
Controlli totali: 53
Backend tests: 50 OK
Frontend build: OK
npm audit --audit-level=moderate: 0 vulnerabilities
pip-audit --timeout 60: No known vulnerabilities found
```

CVE e advisory analizzate e mitigate:

| Pacchetto | Advisory/CVE | Rilevanza nel codice attuale | Mitigazione |
|-----------|--------------|------------------------------|-------------|
| `starlette 1.2.1` | `PYSEC-2026-249` | Bassa: l'app usa input JSON validati da Pydantic e non basa il flusso su `request.form()` | Vincolo esplicito `starlette>=1.3.1` in `backend/requirements.txt` |
| `starlette 1.2.1` | `PYSEC-2026-248` | Bassa: la logica honeypot usa `request.url.path` e `request.url.query`, non `hostname` o `netloc` come fonte di fiducia | Vincolo esplicito `starlette>=1.3.1` in `backend/requirements.txt` |
| `msgpack 1.1.2` | `GHSA-6v7p-g79w-8964` | Tooling/dev: dipendenza transitiva usata da strumenti di audit/cache, non dal runtime applicativo | Virtualenv locale aggiornato a `msgpack 1.2.1` |
| `pip 26.0.1` | `PYSEC-2026-196` | Ambiente di sviluppo: package manager, non distribuito con l'app | Virtualenv locale aggiornato a `pip 26.1.2` |
| `pip 26.0.1` | `CVE-2026-3219` | Ambiente di sviluppo: package manager, non distribuito con l'app | Virtualenv locale aggiornato a `pip 26.1.2` |
| `pip 26.0.1` | `CVE-2026-6357` | Ambiente di sviluppo: package manager, non distribuito con l'app | Virtualenv locale aggiornato a `pip 26.1.2` |

Patch versionata applicata:

```text
backend/requirements.txt -> aggiunto starlette>=1.3.1
```

## Controllo CVE del 3 novembre 2026

Verifiche eseguite:

```text
Backend tests: 55 OK, anche su copia pulita con Python 3.12
Frontend build: OK
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

Advisory analizzate e mitigate:

| Pacchetto | Advisory/CVE | Rilevanza nel codice attuale | Mitigazione |
|-----------|--------------|------------------------------|-------------|
| `certifi 2026.5.20` | `PYSEC-2026-4320` | Alta: protegge il collegamento HTTPS verso OpenAI; conteneva una CA compromessa | Minimo `certifi>=2026.10.18`, installata 2026.10.23 |
| `anyio 4.13.0` | `PYSEC-2026-4024`, `PYSEC-2026-4025` | Bassa: l'app non usa domini internazionalizzati né process pool | Minimo `anyio>=4.14.2`, installata 4.16.0 |
| `vite 8.0.16`, `postcss`, `nanoid`, `source-map-js` | `GHSA-rq7h-c2jc-7f22`, `GHSA-9jrq-w75r-8gcw` e correlate | Sviluppo e build: non finiscono nel pacchetto servito | `npm audit fix`, Vite 8.3.5 |
| `urllib3`, `filelock`, `msgpack`, `pip` | Vedi `pip-audit` | Strumenti di sviluppo, non usati dall'app in esecuzione | Virtualenv locale aggiornato |

Le versioni esatte verificate sono in `backend/requirements.lock`, usato dal Dockerfile.

## Pentest locale del 3 novembre 2026

Eseguito su una copia isolata, con database temporaneo e AI simulata, usando `bandit`, `schemathesis`, `sqlmap` e prove manuali. Non è un penetration test professionale né una verifica in produzione.

Nessuna injection SQL, XSS eseguibile, path traversal, aggiramento dell'autenticazione o esecuzione di comandi. Corretti:

| Problema | Correzione |
|----------|------------|
| Tentativi di password illimitati sull'area interna | Blocco per IP: 8 errori in 15 minuti, 15 minuti di blocco |
| Limite dell'assistente aggirabile con `X-Forwarded-For` | Si legge l'ultimo valore, aggiunto dal proxy, e solo con `TRUST_PROXY_HEADER` |
| Nessun tetto alla spesa AI | 200 richieste al minuto, poi risposte dalle fonti locali |
| CSRF con POST senza corpo | Rifiuto delle origini non ammesse sui metodi di scrittura |
| Corpi di richiesta illimitati | Massimo 1 MB |
| Eventi honeypot illimitati e IP falsificabile | Massimo 5.000 eventi, stessa lettura dell'IP del resto dell'app |
| Errori 500 con numeri enormi, Unicode spezzato, NaN | Risposta 422, senza ripetere il testo ricevuto |
| Header di sicurezza assenti | Aggiunti alle risposte dell'API |
| Segreti deboli non segnalati, `/docs` pubblico | `SECURITY_STRICT=true` blocca l'avvio e spegne la documentazione API |

Restano da fare prima di un uso reale: header di sicurezza sul frontend e HTTPS tramite reverse proxy, ruoli e audit accessi, cifratura a riposo, quick exit, prova della prompt injection con il modello reale.

## Limite di responsabilità tecnica

Questo repository non fornisce garanzia di sicurezza per ambienti reali.

L'uso operativo richiede una revisione professionale del codice, dell'architettura, del deploy, dei flussi privacy, delle integrazioni AI e delle procedure organizzative.
