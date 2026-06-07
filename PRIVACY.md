# Privacy

Rosa Segnale tratta un tema sensibile e deve essere usato in demo solo con dati fittizi, simulati o anonimizzati.

Questo documento non è un'informativa privacy completa. È una nota di cautela per l'uso del prototipo in ambiente didattico, locale o dimostrativo.

Non inserire nel sistema:

- nomi o cognomi reali;
- indirizzi;
- numeri di telefono;
- email personali;
- screenshot reali;
- conversazioni identificabili;
- dati sanitari reali;
- informazioni su minori reali;
- dettagli familiari, lavorativi o territoriali che possano ricondurre a persone reali;
- qualunque contenuto che permetta di identificare direttamente o indirettamente una persona.

## Dati trattati nel prototipo

Nel normale uso demo il sistema può trattare testi inseriti manualmente dall'utente, classificazioni orientative, risk score, percorsi suggeriti, timestamp, report e log tecnici.

Il prototipo deve essere usato solo con scenari inventati o anonimizzati.

Il database locale, i report generati, i log e gli eventuali file `.env` non devono essere pubblicati, condivisi o caricati su repository pubblici.

## Provider AI

Quando il provider OpenAI è attivo, il testo inviato al punto di ascolto o alla classificazione può essere trasmesso al provider AI configurato.

Prima di un uso reale è necessario definire una policy chiara su:

- quali dati possono essere inviati al provider AI;
- quali dati non devono mai essere inviati;
- base giuridica del trattamento;
- tempi di conservazione;
- misure di sicurezza;
- eventuali trasferimenti extra UE;
- accordi con fornitori e responsabili del trattamento;
- gestione di log, prompt, output e dati tecnici;
- procedure di cancellazione e accesso ai dati.

Per ridurre il rischio, un uso reale dovrebbe prevedere minimizzazione preventiva, anonimizzazione o pseudonimizzazione dove possibile, e filtri per evitare l'invio non necessario di dati identificativi o particolarmente sensibili.

## Uso reale

Prima di rendere il servizio accessibile al pubblico servono almeno:

- informativa privacy completa;
- definizione del titolare del trattamento;
- eventuale nomina di responsabili e sub-responsabili del trattamento;
- consenso o altra base giuridica adeguata;
- valutazione dei dati particolari eventualmente trattati;
- minimizzazione dei dati raccolti;
- tempi di retention e procedure di cancellazione;
- gestione dei diritti degli interessati;
- valutazione d'impatto sulla protezione dei dati, se necessaria;
- revisione legale e operativa;
- revisione tecnica di sicurezza;
- procedure per casi urgenti, minori, autolesionismo, gravidanza, violenza, stalking e situazioni sanitarie;
- policy chiara su accessi interni, ruoli, audit e tracciabilità;
- verifica dei testi, dei flussi e dei messaggi generati dall'AI da parte di professionisti qualificati.

## Limite del prototipo

Rosa Segnale non è un servizio di emergenza, non è un centro antiviolenza, non fornisce consulenza medica, psicologica o legale e non sostituisce personale qualificato.

Il codice può essere adattato per un uso reale solo dopo adeguate verifiche privacy, legali, tecniche, operative e di sicurezza.
