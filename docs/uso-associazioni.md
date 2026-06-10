# Uso gratuito per associazioni

Rosa Segnale è un prototipo didattico rilasciato con licenza MIT.

Associazioni, enti del terzo settore, sportelli di ascolto, centri antiviolenza e progetti civici possono usare, copiare, adattare e integrare gratuitamente il codice nei propri siti o strumenti interni, nel rispetto della licenza presente nel file `LICENSE`.

Il metodo di sviluppo e il threat model sono documentati in:

- [workflow-sviluppo.md](workflow-sviluppo.md)
- [threat-model.md](threat-model.md)

## Avviso importante

Rosa Segnale non è un servizio pronto per la produzione e non deve essere usato così com'è per gestire casi reali.

Il prototipo non sostituisce:

- il 112;
- il 1522;
- i servizi sanitari;
- il supporto psicologico;
- il supporto legale qualificato;
- i centri antiviolenza;
- il personale formato nella gestione di situazioni di rischio.

Prima di qualunque uso reale sono necessari:

- revisione legale e privacy;
- valutazione di sicurezza applicativa;
- valutazione del rischio per persone che usano dispositivi condivisi o sorvegliati;
- gestione professionale dei dati sensibili;
- consenso informato e informative adeguate;
- integrazione con personale formato;
- procedure chiare per emergenze e casi ad alto rischio;
- verifica dei riferimenti territoriali e dei numeri utili;
- definizione di quali dati possono essere inviati al provider AI;
- revisione dei testi da parte di figure competenti.

Durante test, prove o sviluppo non devono essere inseriti nomi, indirizzi, numeri di telefono, screenshot reali, conversazioni identificabili o altri dati che possano ricondurre a persone reali.

## Implementazioni necessarie per un uso reale

Per usare Rosa Segnale in un sito o servizio realmente accessibile al pubblico, il prototipo deve essere completato con:

- autenticazione, autorizzazioni e ruoli per operatrici e amministratori;
- cifratura dei dati sensibili a riposo e, dove necessario, in transito;
- gestione privacy e GDPR, inclusi consenso, retention, accesso, rettifica e cancellazione dei dati;
- deploy HTTPS;
- gestione sicura delle chiavi API e dei segreti applicativi;
- rate limit e protezione da abuso delle API;
- audit log non modificabile;
- backup, monitoraggio e alerting;
- revisione legale, psicologica, privacy e sicurezza;
- quick exit, gestione cache/browser e cautele lato dispositivo;
- validazione dei riferimenti territoriali;
- procedure operative per emergenze, minori, autolesionismo e casi sanitari;
- test di sicurezza prima della pubblicazione;
- formazione del personale che utilizza l'area interna.

Queste implementazioni possono essere progettate e sviluppate su richiesta, adattando il codice alle esigenze dell'associazione, del centro o del progetto civico che vuole adottarlo.

## Finalità del prototipo

Il codice nasce come progetto finale di corso e come base dimostrativa per mostrare un possibile flusso di:

- ascolto assistito da AI;
- orientamento verso risorse utili;
- triage orientativo non clinico e non operativo;
- follow-up operativo interno;
- reportistica aggregata;
- separazione tra vista pubblica e area interna;
- tracciabilità tecnica del modello, del provider e dei timestamp.

## Licenza

Il progetto è distribuito con licenza MIT.

La licenza consente il riuso, la copia, la modifica e l'integrazione del codice, ma non elimina la responsabilità di chi decide di trasformare il prototipo in un servizio reale.

Ogni organizzazione che adotta Rosa Segnale deve verificare autonomamente la conformità legale, tecnica, privacy e operativa rispetto al proprio contesto.
