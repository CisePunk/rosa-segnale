# Threat model - Rosa Segnale

**Metodologia:** STRIDE (sicurezza) + LINDDUN (privacy)

**Ambito:** prototipo dimostrativo. Questo documento non sostituisce un assessment professionale, una revisione legale o una DPIA formale; documenta le ipotesi di rischio che guidano architettura, test e cautele progettuali, e definisce i requisiti minimi per un eventuale passaggio a uso pubblico.

## 1. Contesto e premessa di dominio

Rosa Segnale è un portale di triage assistito da AI per situazioni difficili: violenza, stalking, separazioni conflittuali e situazioni che possono coinvolgere minori. Questa premessa cambia radicalmente il modello di minaccia rispetto a un'applicazione web generica.

1. **L'avversario principale può essere vicino alla persona che cerca aiuto.** In un contesto di violenza domestica, l'attore più probabile e pericoloso può essere una persona fisicamente vicina alla vittima, con accesso diretto o coercitivo al suo dispositivo.
2. **Il danno non è solo informatico.** Una fuga di dati, una traccia nel browser o una risposta di triage sbagliata possono tradursi in danno fisico alla persona. Il safety risk e il security risk qui coincidono.
3. **I dati possono essere ad altissimo rischio privacy.** Il sistema può trattare informazioni riconducibili a categorie particolari ex art. 9 GDPR, dati su minori, salute, violenza, relazioni familiari o situazioni personali vulnerabili. Qualunque uso oltre la demo richiede una valutazione privacy strutturata e, con alta probabilità, una DPIA ai sensi dell'art. 35 GDPR.

## 2. Descrizione del sistema e trust boundary

### 2.1 Flusso dei dati

```text
[Browser utente] --(testo libero, vista Ascolto)--> [Backend FastAPI]
                                                        |
                                  +---------------------+---------------------+
                                  |                     |                     |
                          [Provider AI]          [DB locale]          [Area interna]
                          (prompt/output)   (segnalazioni, note,    (dashboard, registro,
                                             classificazioni)        report)
```

### 2.2 Trust boundary identificati

| ID | Confine | Cosa lo attraversa | Perché è critico |
|----|---------|-------------------|------------------|
| TB1 | Dispositivo utente <-> applicazione | Testo libero, cronologia, cache, sessione | Il dispositivo può essere condiviso, controllato o sorvegliato dal maltrattante |
| TB2 | Backend <-> provider AI | Prompt contenenti testo dell'utente, output del modello | Dati sensibili possono uscire dal perimetro applicativo verso una terza parte, con retention e giurisdizione proprie |
| TB3 | Vista pubblica <-> area interna | Autenticazione, autorizzazione | Separa la superficie anonima dal registro segnalazioni, che è uno degli asset più sensibili |
| TB4 | Knowledge base interna <-> contesto del modello | Contenuti KB inseriti nel prompt | Chi modifica la KB può influenzare il comportamento dell'assistente |
| TB5 | Applicazione <-> filesystem locale | DB, log, report, file temporanei, `.env` | Persistenza non controllata di dati sensibili e segreti |

## 3. Asset da proteggere

In ordine di criticità:

1. Incolumità e anonimato della persona che usa la vista Ascolto.
2. Testi inseriti nella vista Ascolto e ogni dato che permetta di ricollegarli a una persona identificabile.
3. Registro segnalazioni, classificazioni, risk score, percorsi suggeriti e note interne.
4. Correttezza della logica di escalation verso 112, 1522 o YouPol nei casi ad alto rischio.
5. Prompt e output scambiati con il provider AI.
6. Credenziali, chiavi API e variabili `.env`.
7. Database locale, report, log applicativi e file temporanei.
8. Integrità della knowledge base interna.

## 4. Attori di minaccia

| ID | Attore | Capacità | Motivazione | Probabilità nel dominio |
|----|--------|----------|-------------|-------------------------|
| A1 | Maltrattante con accesso al dispositivo della vittima | Accesso fisico o coercitivo: cronologia, cache, sessioni aperte, notifiche, autofill. Nessuna competenza tecnica richiesta | Controllo, sorveglianza, ritorsione | Alta: attore principale del dominio |
| A2 | Avversario che sonda la logica di triage | Interazione ripetuta con la chat pubblica per capire quali frasi attivano l'escalation | Capire o aggirare il comportamento del sistema, screditare il servizio | Media |
| A3 | Insider con accesso all'area interna | Accesso legittimo a registro, report o knowledge base | Curiosità, conflitto d'interesse, coercizione esterna | Media, con impatto alto |
| A4 | Utente malevolo della chat | Prompt injection diretta, jailbreak, input ostili o volumetrici | Estrarre prompt, generare output dannosi, esaurire quota API | Alta |
| A5 | Provider AI / supply chain | Modello honest-but-curious, retention dei prompt, accessi del personale, subprocessor, giurisdizione | Rischio strutturale quando il provider AI è abilitato | Presente se il provider è attivo |
| A6 | Avversario remoto opportunistico | Scanner, bot, exploit noti su dipendenze, credenziali deboli | Indiscriminata | Media |

## 5. Minacce

Ogni minaccia è mappata su STRIDE (S spoofing, T tampering, R repudiation, I information disclosure, D denial of service, E elevation of privilege) e LINDDUN (L linking, I identifying, N non-repudiation, D detecting, Dd data disclosure, U unawareness, Nc non-compliance).

### TB1 - Dispositivo utente (A1)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T01 | Cronologia, cache, autofill o URL riconoscibile rivelano al maltrattante che la persona ha cercato aiuto | I | D, Dd |
| T02 | Sessione lasciata aperta su dispositivo condiviso espone la conversazione | I | I, Dd |
| T03 | Accesso coercitivo al dispositivo con l'app a schermo | I | D, I |
| T04 | Assenza di una via di uscita rapida: la persona non riesce a chiudere la pagina in modo non sospetto | - | D |

T01-T04 sono minacce a impatto molto alto. Il dato compromesso può non essere soltanto "cosa ha scritto", ma anche "che ha scritto": il solo rilevamento della ricerca di aiuto può esporre a ritorsione.

### TB2 - Provider AI (A5)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T05 | Invio al provider di dati identificativi o particolari non necessari al triage | I | I, Dd, Nc |
| T06 | Retention o uso improprio dei prompt senza base giuridica adeguata | I | Dd, U, Nc |
| T07 | Trasferimento extra-UE o subprocessor non mappati | I | Nc |

### TB3 - Area interna (A3, A6)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T08 | Accesso non autorizzato a dashboard, registro o report tramite autenticazione debole o assente | S, E | Dd |
| T09 | Operatore consulta segnalazioni senza necessità, aggravato dal possibile legame personale tra operatore e persone coinvolte in contesti locali | I | L, I, Dd |
| T10 | Assenza di audit log non modificabile: impossibile dimostrare chi ha visto cosa | R | N |

### TB4 - Knowledge base (A3, A4)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T11 | Injection indiretta via KB: chi modifica la knowledge base può inserire contenuti che finiscono nel contesto del modello | T, E | - |

### Logica di triage e assistente (A2, A4)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T12 | Prompt injection diretta: bypass delle istruzioni di sicurezza, estrazione del prompt, output dannosi | T | Dd |
| T13 | Probing della classificazione tramite interazioni ripetute | I | D |
| T14 | Escalation male instradata: mancato rinvio al 112 in pericolo immediato o gestione debole di messaggi brevi e ambigui | Safety | - |
| T15 | Fallback locale che produce risposte incoerenti o troppo deboli sui casi ad alto rischio | Safety | - |
| T16 | Bias o formulazioni inappropriate su violenza, minori, gravidanza, salute, stalking o separazione | Safety | - |
| T17 | Falso affidamento: l'utente crede che il sistema abbia segnalato la sua situazione a qualcuno, quando non instrada verso nessun servizio reale | Safety | U |
| T18 | Abuso volumetrico: esaurimento quota provider, input troppo lunghi o non necessari | D | - |

### TB5 - Persistenza locale (A3, A6)

| ID | Minaccia | STRIDE | LINDDUN |
|----|----------|--------|---------|
| T19 | Dati sensibili persistono in DB locale, report, log, screenshot o file temporanei oltre la necessità | I | Dd, Nc |
| T20 | Esposizione di segreti: `.env`, chiavi API, DB committati o lasciati in cartelle generate | I | Dd |
| T21 | Tensione log/audit: log dettagliati servono alla sicurezza ma moltiplicano i dati personali persistiti | I, R | Dd, Nc |

## 6. Mitigazioni presenti nel prototipo

| Mitigazione | Minacce coperte | Copertura |
|-------------|-----------------|-----------|
| Separazione vista pubblica / area interna | T08 | Parziale |
| Assenza di geolocalizzazione del browser | T01 | Parziale |
| Riferimenti rapidi a 112, 1522, YouPol | T14, T17 | Parziale |
| Regole di sicurezza post-classificazione e knowledge base interna | T12, T14, T16 | Parziale |
| Fallback locale se il provider non è disponibile | T15, T18 | Parziale |
| Basic Auth opzionale sulle route interne | T08 | Solo demo |
| Esclusione dal versionamento di `.env`, DB, report e build | T20 | Buona |
| Test automatici su triage, policy chat, provider e auth | T12, T14, T15 | Buona per il perimetro testato |
| Cross-review multi-modello su prompt, privacy, CVE, injection, bias ed edge case | T12, T16 | Buona come pratica di processo |

Lettura onesta della tabella: le minacce T01-T04 (attore A1, centrale nel dominio) e T09-T11 (insider e knowledge base) non hanno oggi mitigazioni dedicate. Questo è accettabile per un prototipo dimostrativo non esposto a utenti reali; non lo è per qualunque scenario pubblico o operativo.

## 7. Rischi residui e requisiti per uso pubblico

In ordine di priorità:

### Priorità 1 - sicurezza della persona (A1)

- pulsante di uscita rapida (quick exit) che reindirizza a un sito neutro e riduce la riconoscibilità della sessione;
- nessuna persistenza lato client: niente cache delle conversazioni, niente autofill, sessioni a scadenza breve;
- valutazione di URL, titolo pagina e modalità "camuffata" dell'interfaccia, seguendo prassi già usate da servizi anti-violenza;
- avviso esplicito sui rischi di dispositivo condiviso o sorvegliato.

### Priorità 2 - conformità e provider (A5)

- valutazione privacy strutturata e, con alta probabilità, DPIA ex art. 35 GDPR prima di qualunque trattamento reale;
- minimizzazione e, dove possibile, pseudonimizzazione del testo inviato al provider;
- policy formale e DPA con clausole su retention, training e subprocessor;
- revisione legale/privacy e revisione dei testi da parte di figure qualificate del settore anti-violenza.

### Priorità 3 - area interna e insider (A3)

- autenticazione robusta, preferibilmente con MFA;
- autorizzazioni granulari per ruolo;
- audit log non modificabile degli accessi al registro, con revisione periodica;
- workflow di modifica della knowledge base con approvazione a due persone.

### Priorità 4 - robustezza tecnica (A2, A4, A6)

- rate limiting e limiti di lunghezza input;
- contromisure al probing della classificazione, incluse risposte ad alto rischio non distinguibili dall'esterno in modo sistematico e monitoraggio dei pattern anomali;
- cifratura at rest del database;
- logging sicuro con minimizzazione;
- gestione segreti fuori da `.env` in produzione;
- test di sicurezza, incluso pentest, prima del deploy.

### Trasversale

- gestione esplicita delle aspettative: l'interfaccia deve dichiarare cosa il sistema fa e quali limiti ha.

## 8. Limiti di questo documento

Il modello è stato costruito a tavolino, senza pentest, senza revisione da parte di professionisti del settore anti-violenza e senza osservazione di utenti reali. Le probabilità assegnate agli attori sono stime di dominio, non dati. Le minacce di tipo safety richiedono validazione da parte di figure qualificate, come operatrici di centri anti-violenza, psicologi e legali, prima di qualunque uso oltre la demo.
