# Honeybot Rosa Segnale

Il nostro honeybot è un honeypot applicativo.

Non dialoga con l’intruso.
Osserva richieste sospette allo staging e registra eventi tecnici minimi.

## Funzionamento

Ogni richiesta che arriva al backend FastAPI passa dal middleware in:

```text
backend/app/main.py
```

Il middleware chiama:

```text
inspect_request()
```

nel file:

```text
backend/app/honeypot.py
```

Se il percorso richiesto è una trappola, oppure contiene pattern sospetti, viene registrato un evento.

## Percorsi trappola

Esempi:

```text
/wp-login.php
/.env
/admin
/phpmyadmin
/xmlrpc.php
/debug
```

## Pattern sospetti

Esempi:

```text
../
%2e%2e
<script
union%20
select%20
```

## Dati salvati

Gli eventi vengono salvati nella tabella SQLite:

```text
honeypot_events
```

Campi salvati:

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

## Privacy

L’indirizzo IP non viene salvato in chiaro.

Viene trasformato in hash usando:

```text
HONEYPOT_HASH_SALT
```

Questo permette di riconoscere accessi ripetuti senza conservare direttamente l’indirizzo IP.

## Esempio

Se qualcuno prova ad aprire:

```text
https://staging-rosa.it/wp-login.php
```

il backend risponde normalmente con errore 404.

Dietro registra un evento simile:

```text
path: /wp-login.php
reason: trap_path
risk_score: 4
ip_hash: ...
user_agent: ...
```

## Dashboard

Gli eventi sono visibili nella dashboard interna nel pannello:

```text
Eventi honeypot
```

## Stato attuale

Il honeybot è un sensore.

Non blocca ancora automaticamente gli accessi sospetti.

## Prossimo passo

Collegare il honeybot a:

```text
rate limit
notifica tecnica
blocco automatico degli IP hash ricorrenti
WAF o Cloudflare Zero Trust
```
