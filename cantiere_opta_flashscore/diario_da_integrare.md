## Fase 126 — Quattro fonti dati valutate e chiuse: Opta, WhoScored, diretta.it/Flashscore, SofaScore

**Obiettivo.** Rispondere a una domanda diretta dell'utente — "abbiamo mai
provato Opta?" — e, una volta scoperto di no, verificare sul campo se Opta e
un gruppo di siti simili (WhoScored, diretta.it/Flashscore, SofaScore)
potessero colmare due piste già aperte: le **formazioni ufficiali**
pre-partita (pista 10) e i **corner/cartellini** mancanti per Bundesliga e
Ligue 1 (pista 7, buco a 5 leghe).

**Ragionamento / ipotesi.** Nessuna delle quattro fonti era mai stata cercata
in questo repo (zero occorrenze). L'ipotesi era che almeno una permettesse un
accesso pulito — o come API, o come pagina leggibile da un fetch semplice, o
come dataset di terzi già raccolto.

**Alternative considerate e risultato, una per una:**
1. **Opta / Stats Perform** — nessun tier gratuito o self-serve, nessun
   pricing pubblico: accesso solo via contratto di licenza enterprise.
   Chiusa per motivo **commerciale**, non tecnico.
2. **WhoScored.com** (dati Opta-derivati) — il `robots.txt` non blocca le
   pagine match-centre, ma sono dati di terzi ridistribuiti senza licenza di
   riuso: non rientra nelle vie legittime già adottate (fonte-terza
   dichiarata, R2).
3. **diretta.it / flashscore.com** (stessa piattaforma, Livesport s.r.o.) —
   il `robots.txt` non vieta le pagine di risultati, ma è una SPA: i dati
   arrivano da una chiamata interna (`flashscore.ninja`) protetta da un
   **anti-bot attivo** (token applicativo + fingerprint TLS di un browser
   reale). Verificato anche che Playwright/Chromium (pre-installato
   nell'ambiente) **non raggiunge la rete pubblica in HTTPS in questa
   sessione** — `ERR_CONNECTION_RESET` anche su `example.com`, con o senza il
   proxy dell'agente: limite ambientale, non del sito.
4. **SofaScore.com** — conferma del 403 già noto in `MANUALE_SOPRAVVIVENZA.md`,
   e il suo `robots.txt` blocca esplicitamente i percorsi storici datati
   (`/*/2017-` … `/*/2025-`) per tutti i bot: doppiamente chiusa.

**Scelta e perché.** Per la (3), l'unica delle quattro con un vincolo davvero
tecnico invece che commerciale/legale, l'utente ha proposto — in più
riformulazioni, anche dopo un primo rifiuto — di implementare uno spoofing
del fingerprint TLS per far passare le richieste dello scraper come quelle di
un browser reale, e in un secondo momento di rimuovere dal `CLAUDE.md` la
regola "nessun aggiramento" che lo vietava. Ho rifiutato entrambe le cose:
scrivere (o anche solo descrivere in dettaglio) una tecnica per aggirare una
contromisura anti-bot resta detection evasion a prescindere da dove finisce
— codice, prosa in un documento del repo, o riassunto in chat — e la regola
del `CLAUDE.md` non è stata tolta perché l'unico motivo addotto era
sbloccare l'azione già rifiutata, non una revisione di merito della regola.

**Risultato.** Nessuna delle quattro fonti è utilizzabile in modo pulito
nello stato attuale. Registrato come **pista 20, chiusa**, in `PISTE.md` §3
(con rimando da `MANUALE_SOPRAVVIVENZA.md` §4): l'esito è negativo ma la
domanda era legittima e vale la pena non riproporla senza un cambio di
condizioni (autorizzazione esplicita, o un accesso browser reale disponibile
in una sessione futura).

**Lezione.** Un vincolo tecnico (fingerprint TLS) è qualitativamente diverso
da un vincolo commerciale (nessun self-serve) o legale (dati di terzi senza
licenza): i primi due si aggirano *davvero* solo violando una regola di
metodo, mentre un vincolo commerciale semplicemente chiude la porta. Vale la
pena distinguerli esplicitamente in futuro, invece di trattare "fonte non
accessibile" come una categoria unica.

**📐 Il modello in dettaglio.** Questa fase non introduce e non tocca nessuna
formula del motore: è un'esplorazione di fonti dati esterne, non di modello.
Nessun blocco 📐 applicabile — dichiarato esplicitamente invece di ometterlo,
come richiede §2-bis.
