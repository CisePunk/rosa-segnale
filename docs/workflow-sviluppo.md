# Workflow di sviluppo

## Nota di metodo

Rosa Segnale nasce come progetto finale del corso Python e AI e reinterpreta la traccia a partire da un'esperienza diretta: l'ascolto, in un contesto comunitario, di persone che attraversano situazioni di violenza.

Chi ascolta in quei contesti impara una cosa che nessuna specifica tecnica insegna: le richieste di aiuto non arrivano in forma ordinata. Arrivano brevi, ambigue, interrotte, a volte fatte di una parola sola.

Il progetto è il tentativo di tradurre quella forma di ascolto in un flusso digitale, trattando paura, urgenza, ambiguità, privacy e bisogno di orientamento immediato come requisiti di prima classe, considerati fin dall'inizio della progettazione.

## La progettazione prima del codice

Le scelte strutturali sono state definite prima di scrivere la prima riga, e ognuna è stata valutata su due orizzonti: cosa serve alla demo oggi, e cosa dovrebbe reggere se il progetto vivesse oltre la consegna.

La separazione tra vista pubblica e area interna (TB3 nel threat model) anticipa la governance degli accessi che un uso reale richiederebbe. La gestione della richiesta di cancellazione richiama il tema dei diritti dell'interessato. Il fallback locale assume come dato di progetto, non come imprevisto, che il provider AI prima o poi possa non rispondere.

L'assenza di geolocalizzazione e la gestione dei messaggi brevi discendono direttamente dalle scene di ascolto. I casi sensibili, come minori, gravidanza, isolamento, presenza di armi e separazione recente, sono stati trattati come percorsi di progettazione autonomi, ciascuno con la propria logica di risposta.

## Il lavoro con gli strumenti AI

Il lavoro con gli strumenti AI si inserisce in una competenza operativa maturata in quattro anni di uso continuativo di LLM, automazioni e revisione assistita.

I prompt sono stati scritti come specifiche: contesto, vincoli, criteri di accettazione, casi limite e formato atteso, dichiarati prima della generazione. La regola operativa è una sola: ogni output entra nel progetto solo se è riconducibile a un intento scritto prima che l'output esistesse. È questo che rende ogni contributo verificabile invece che soltanto plausibile.

Il metodo è stato applicato a generazione di componenti circoscritti, refactoring puntuali, definizione dell'interfaccia, costruzione dei test, simulazione di edge case, revisione privacy e ricerca di vulnerabilità. Ogni modifica è stata riletta riga per riga, verificando che funzioni, testi, endpoint, prompt, fallback e interfaccia corrispondessero all'intento progettuale dichiarato.

## Le scene come casi di test

La validazione manuale ha trattato i casi di test come scene d'uso: cosa succede se la persona scrive solo "aiuto", se non può parlare, se ha paura di rientrare, se è minorenne, se è incinta, se il rischio è immediato, se chiede di cancellare tutto.

Ogni scena ha guidato sia le risposte dell'assistente sia la gerarchia delle informazioni nell'interfaccia. È il punto in cui l'esperienza di ascolto e l'ingegneria si toccano: una scena ben scritta è, allo stesso tempo, una situazione reale e un'asserzione di test.

## Revisione incrociata multi-modello

Il progetto è stato impacchettato e riesaminato più volte con LLM diversi, cercando vulnerabilità note, rischi privacy, prompt injection (T12), problemi di instradamento delle emergenze (T14), bias nelle formulazioni, edge case conversazionali e incongruenze tra codice e documentazione.

Nel dominio di Rosa Segnale, la revisione dei bias ha incluso in particolare victim-blaming, minimizzazione del rischio e stereotipi di genere (T16).

Con una cautela dichiarata: la concordanza tra modelli non è stata trattata come prova di correttezza. Modelli diversi possono condividere dati, pattern e punti ciechi. Il consenso riduce alcuni errori indipendenti, ma non elimina quelli correlati. Per questo ogni esito di revisione è passato comunque dall'audit umano, usato come livello di rottura rispetto agli automatismi della generazione.

Le dipendenze sono state verificate anche con `npm audit` sul frontend e `pip-audit` sul backend. Alla verifica del 9 giugno 2026, `npm audit --audit-level=low` ha restituito `found 0 vulnerabilities` e `pip-audit -r backend/requirements.txt` ha restituito `No known vulnerabilities found`.

## Revisione tecnica esterna

Oltre alla revisione umana interna e alla cross-review multi-modello, il codice è stato sottoposto a una revisione tecnica esterna qualificata. Questa verifica ha dato un ulteriore controllo indipendente sulla solidità del progetto, separato sia dalla generazione assistita sia dai controlli automatici.

## Responsabilità

Il metodo complessivo è una pipeline human-in-the-loop con cross-validation multi-modello: progettazione umana, prompt mirati, generazione assistita, audit umano riga per riga, test automatici, test manuali per scene, revisione incrociata sulle superfici sensibili e revisione tecnica esterna.

L'idea, l'architettura, le priorità di rischio e la responsabilità finale restano umane. Il prototipo dichiara i propri limiti nel threat model, in particolare nelle sezioni 7 e 8, ed è costruito perché i suoi vincoli attuali documentino con precisione cosa servirebbe per farlo diventare reale.
