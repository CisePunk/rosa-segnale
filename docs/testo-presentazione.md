# Testo breve di presentazione

Rosa Segnale è un prototipo didattico sviluppato come progetto finale Python e AI.

L'idea nasce dall'esigenza di trasformare una traccia tecnica in un flusso più vicino a un contesto reale di ascolto: le richieste di aiuto non arrivano sempre in forma ordinata, possono essere brevi, ambigue o interrotte.

Il portale ha due livelli: una vista pubblica di ascolto e una vista interna per gestione, revisione e reportistica.

Nella vista Ascolto, la persona non vede dati tecnici, KPI, report o registri interni. Trova solo risorse rapide, come 112, 1522 e YouPol, insieme a un punto di ascolto AI.

Il chatbot usa OpenAI per generare una risposta empatica e naturale. La base di conoscenza interna non viene mostrata come testo copiato, ma serve a orientare la risposta verso il passo più utile: emergenza, centro antiviolenza, supporto legale qualificato, supporto sanitario o servizi competenti.

Nell'Area interna, invece, si vede la parte gestionale e tecnica del progetto. Qui sono presenti il triage orientativo delle segnalazioni, il livello di rischio, i percorsi suggeriti, il registro interno, il follow-up operativo, la tracciabilità del modello e i report aggregati.

Il registro interno parte vuoto e mostra solo le segnalazioni inserite. Ogni caso può essere selezionato, commentato con una nota interna e aggiornato con uno stato di follow-up.

Dal punto di vista tecnico, il backend è sviluppato in Python con FastAPI, Pydantic e SQLite. Il frontend è realizzato con React e Vite. La parte AI usa OpenAI tramite provider configurabile, il modello predefinito gpt-4o-mini, una base di conoscenza interna, regole di sicurezza e fallback locale.

Il backend genera automaticamente un report settimanale con KPI aggregati e permette di rigenerarlo anche manualmente.

Il metodo di sviluppo è stato human-in-the-loop: progettazione umana, prompt mirati, generazione assistita, audit riga per riga, test automatici, test manuali per scene, cross-review multi-modello e revisione tecnica esterna. Le dipendenze sono state verificate anche con `npm audit` e `pip-audit`.

Rosa Segnale non vuole sostituire servizi reali di emergenza, supporto medico, psicologico o legale. Per questo la vista pubblica contiene un avviso chiaro e il codice è presentato come prototipo didattico, non come servizio pronto per la produzione.

Il codice è rilasciato con licenza MIT. Questo significa che associazioni, enti del terzo settore, sportelli di ascolto, centri antiviolenza e progetti civici possono usarlo e adattarlo gratuitamente.

Prima di un uso reale, però, servono revisioni privacy, sicurezza, legali e operative. Servono anche procedure supervisionate, personale formato, gestione sicura dei dati, autenticazione, cifratura, audit log, deploy HTTPS e test di sicurezza.

In sintesi, Rosa Segnale dimostra come Python e AI possano essere usati non solo per classificare dati, ma per costruire un flusso più responsabile: ascolto, orientamento, triage orientativo, tracciabilità e reportistica.
