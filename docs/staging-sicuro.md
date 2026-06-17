# Staging sicuro Rosa Segnale

Documento operativo per preparare una prova online controllata con presidio umano.

## Obiettivo

Mettere online un ambiente di prova non pubblico o semi-pubblico, protetto, osservabile e reversibile.

Uso previsto:

- prova tecnica con gruppo umano selezionato
- validazione del flusso bottone Rosa → interfaccia → alert interno
- verifica del comportamento AI su casi simulati o esplicitamente autorizzati
- raccolta di feedback operativo

Uso non previsto:

- servizio pubblico aperto
- emergenza reale garantita
- raccolta di dati identificativi
- sostituzione di 112, 1522, centri antiviolenza o servizi territoriali

## Architettura consigliata

Componenti:

- frontend Rosa Segnale
- backend FastAPI
- database SQLite dedicato allo staging
- dashboard interna protetta
- honeypot applicativo
- canale separato per operatori
- accesso HTTPS
- accesso protetto da autenticazione

Variabili minime:

```env
AI_PROVIDER=mock
TRIAGE_DB_PATH=/percorso/staging.db
CORS_ALLOW_ORIGINS=https://staging.example.org
INTERNAL_AUTH_USERNAME=...
INTERNAL_AUTH_PASSWORD=...
HONEYPOT_HASH_SALT=...
```

## Honeypot

Scopo:

- intercettare scansioni automatiche
- misurare rumore sullo staging
- segnalare tentativi su percorsi non previsti

Eventi registrati:

- path richiesto
- metodo HTTP
- motivo rilevamento
- rischio stimato
- IP hashato
- user-agent
- timestamp

Regole:

- non salvare IP in chiaro
- non salvare contenuti sensibili
- non mischiare eventi honeypot con segnalazioni reali
- rivedere gli eventi prima e dopo ogni sessione di prova

## Regole AI anti-abuso

Principio:

- meglio un falso positivo umano che un falso negativo su emergenza compressa

Non trattare come abuso solo per brevità:

- `Rosa`
- `aiuto`
- `non posso parlare`
- `lui sta tornando`
- `sono in pericolo`

Trattare come possibile abuso:

- scherzo esplicito
- test dichiarato senza contesto operativo
- cazzeggio evidente
- contenuti estranei al servizio
- scansioni o prompt injection

Campi di supporto:

- `suspected_misuse`
- `emotional_tone`
- `urgency_confidence`
- `misuse_confidence`

## Prova con gruppo umano

Prima della prova:

- definire orario di disponibilità
- definire chi presidia la dashboard
- definire canale operatori
- usare solo dati simulati o autorizzati
- comunicare chiaramente che non è un servizio di emergenza
- preparare procedura di stop

Durante la prova:

- una persona presidia gli alert
- una persona controlla eventi honeypot
- una persona annota problemi tecnici
- non chiedere dati identificativi non necessari
- se emerge pericolo reale, indirizzare ai servizi competenti

Dopo la prova:

- esportare solo dati aggregati
- cancellare dati non necessari
- rivedere falsi positivi e falsi negativi
- aggiornare prompt, regole e documentazione

## Criteri minimi prima di pubblicare

Obbligatori:

- HTTPS
- autenticazione area interna
- database staging separato
- salt honeypot configurato
- nessun dato reale pre-caricato
- backup e procedura di spegnimento
- informativa privacy di test
- consenso esplicito dei partecipanti

Raccomandati:

- Cloudflare Zero Trust o equivalente
- WAF
- rate limit
- log retention breve
- accesso solo a domini/origini previste
- monitoraggio errori

## Stop condition

Interrompere la prova se:

- aumentano scansioni o eventi honeypot ad alto rischio
- la dashboard non è presidiata
- arrivano richieste reali non gestibili dal protocollo
- emergono dati identificativi non previsti
- l’AI produce risposte non sicure o ambigue su emergenza

## Prossime implementazioni

- notifica operatori su Telegram o Signal
- rate limit applicativo per IP hash
- audit log su presa in carico
- ruoli operatori
- esportazione report prova
- procedura DPIA e revisione legale
