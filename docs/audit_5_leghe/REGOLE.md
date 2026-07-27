# Regole del cantiere

Regole **decise dall'utente durante questo lavoro**. Vivono qui perché il
cantiere è isolato; quando i due filoni verranno uniti, **vanno aggiunte alle
regole generali del progetto** (`CLAUDE.md`), non riscritte da capo.

Ogni regola dice: *cosa* si fa, *perché*, e *come si applica in pratica*.

---

## R1 · Il dato è quello del CAMPO, non quello del tribunale

**Regola.** Quando un risultato ufficiale differisce da quello ottenuto sul
campo per una decisione amministrativa (giustizia sportiva, penalizzazioni,
omologazioni, punteggi assegnati a tavolino), **si usa il risultato del campo**.
Ciò che è successo in tribunale non riguarda il modello.

**Perché.** Il progetto stima la probabilità di **eventi di gioco**, e i mercati
si regolano sul risultato **al fischio finale**, non su una sentenza successiva.
Un punteggio assegnato non è una realizzazione del processo che il modello
descrive: darlo in pasto al fit insegnerebbe qualcosa che il calcio non ha
prodotto.

**Come si applica — CASO PER CASO, mai una regola automatica.** Ogni caso va
istruito singolarmente: cosa è successo, quanto si è giocato, quali dati
esistono, quale fonte dice cosa. Solo dopo si decide e si registra. Il motivo è
che i casi non si somigliano: una partita giocata per intero e poi riassegnata è
diversa da una sospesa al 30′ e ripresa un mese dopo, che è diversa da una mai
disputata.

**Registro obbligatorio.** Ogni intervento vive in
[`data/correzioni_dichiarate.csv`](../../data/correzioni_dichiarate.csv), una riga per
cella modificata, con: partita, colonna, valore prima, valore dopo, **motivo**,
**fonte**, stato (`applicata`/`proposta`), chi ha deciso e quando. Le correzioni
si applicano **solo** con `scripts/applica_correzioni.py`, che verifica il
valore-prima di ogni cella e si ferma se non combacia: nessuna modifica a mano,
nessun numero che appare senza tracciamento.

**Casi già istruiti:** vedi `04_decisioni.md` §1 (Union Berlin-Bochum
14/12/2024: partita giocata per intero, 1-1 sul campo, 0-2 a tavolino → si usa
1-1).

---

## R2 · Valore rosa: si prende da Transfermarkt dove la fonte primaria non copre

**Regola.** Le celle `squad_value` che la fonte primaria (player-scores) non
pubblica — perché la copertura delle valutazioni è sotto la soglia dell'85% dei
minuti — si riempiono con il **valore Transfermarkt** della pagina di
competizione filtrata per stagione. È un dato reale e pubblico, non una stima.

**Perché.** Meglio un numero vero con una scala dichiarata che un buco. Il
precedente del progetto (recupero manuale di 13 celle) è stato **verificato in
questa sessione**: i valori combaciano con la pagina Transfermarkt.

**Il caveat che va SEMPRE dichiarato.** Le due grandezze non coincidono:

- *player-scores* (primaria): somma, sui giocatori con ≥1′ giocato in
  campionato, dell'ultima valutazione ≤ 1 settembre dell'anno di inizio;
- *Transfermarkt*: valore aggregato della rosa registrata per quella stagione.

Rapporto misurato TM / nostro-al-1-settembre:

| lega | 2018-19 | 2021-22 | 2025-26 |
|---|--:|--:|--:|
| serie_a | 1.353 | **1.033** | 1.055 |
| premier_league | 1.171 | **1.004** | 1.077 |
| la_liga | 1.302 | **1.003** | 1.118 |
| bundesliga | 1.392 | **1.012** | 1.161 |
| ligue_1 | 1.439 | **1.204** | 1.473 |

Due cose, verificate e non presunte:

1. **La pagina Transfermarkt filtrata per stagione è STORICA, non odierna.** Se
   mostrasse i valori di oggi, il rapporto con il nostro valore ricalcolato *con
   le valutazioni odierne* sarebbe ~1.00: invece è 1.14–6.67 (es. La Liga
   2018-19: 6.67). Nessuna contaminazione dal futuro.
2. **In una stagione con dati completi le due definizioni COINCIDONO**
   (2021-22: 1.003–1.033 su quattro leghe su cinque). Il divario che si vede
   nel 2025-26 non nasce da Transfermarkt: nasce dal fatto che la fonte
   primaria in quella stagione è **incompleta** (copertura delle valutazioni da
   ~0.99 a 0.84–0.98) e quindi **sotto-conta**. Detto altrimenti: nelle celle
   2025-26 riempite da Transfermarkt il numero è, semmai, *più* corretto di
   quello delle celle vicine prese dalla fonte primaria.

Resta il fatto che la colonna 2025-26 mescola due misure: chi la usa lo deve
sapere, e ogni analisi che ci si appoggia lo dichiara. Il divario del 2018-19
(1.17–1.44) è invece plausibilmente dovuto alle valutazioni più rade dell'epoca
(la finestra di validità di 550 giorni ne scarta di più): non è stato
approfondito perché lì la colonna è già piena di dato primario.

**Come si applica.** `scripts/recupero_squad_value_tm.py` scarica e **valida**
(misura il rapporto sui club dove esistono entrambi i valori);
`scripts/applica_squad_value_tm.py` riempie **solo** le celle vuote e rifiuta di
sovrascrivere un valore esistente. Provenienza riga per riga in
[`data/squad_value_2526_transfermarkt.csv`](../../data/squad_value_2526_transfermarkt.csv).

---

## R3 · Nessuna modifica a mano ai dati: registro + script, sempre

**Regola.** Nessun valore entra o cambia in uno snapshot per intervento manuale.
Ogni modifica passa da un file-registro (il *cosa* e il *perché*) e da uno script
idempotente (il *come*), che verifica lo stato di partenza e si ferma se non è
quello atteso.

**Perché.** È l'unico modo per cui un terzo, mesi dopo, possa rifare gli stessi
numeri e capire da dove viene ogni cella. Un `df.loc[...] = x` eseguito una volta
in una sessione non è riproducibile e non lascia traccia del motivo.

---

## R4 · Isolamento del cantiere (finché non si decide di unire)

**Regola.** Tutto resta in `cantiere/`: nessuna numerazione di fase, nessuna
modifica ai documenti condivisi (`DIARIO.md`, `README.md`, `PANCHINA.md`,
`DATI.md`, `experiments/runs.jsonl`) né a `src/`, `data/`, `scripts/`, `tests/`.

**Perché.** Su `main` si lavora in parallelo: due filoni che toccano gli stessi
file si ostacolano. Le checklist di integrazione nei report restano **proposte**.

---

## R6 · Partite con dati corrotti: la procedura (in quest'ordine)

Quando una riga sembra sbagliata — un margine impossibile, un xG a zero, un
risultato che due fonti raccontano in modo diverso — si segue **questa
sequenza**, mai una scorciatoia. Ogni passo è stato pagato con un errore vero.

### Passo 1 · Prima di dichiararlo un errore, prova a spiegarlo

L'impossibilità «fisica» va verificata sul **dato più fine della STESSA fonte**,
non dedotta da una regola generale. Il caso che ha insegnato la lezione:
Bielefeld-Leverkusen 21/11/2020, `xG = 0` per una squadra che aveva **segnato**.
Sembrava impossibile. Non lo era: il gol era un **autogol** del portiere
avversario, e il Bielefeld non aveva tirato nemmeno una volta. Il dato
tiro-per-tiro (`understat.com/getMatchData/{id}`) lo dice in chiaro; il conteggio
tiri di football-data no, perché quella fonte conta l'autogol come tiro in porta
di chi ne beneficia e Understat no.

→ **Regola: un xG nullo con gol segnati è legittimo se i gol sono autogol.**
   Il controllo automatico deve verificarlo prima di gridare all'errore
   (implementato in `scripts/audit_anomalie.check_xg`).

### Passo 2 · Diagnostica QUALE parte è rotta, con un'informazione indipendente

Non fidarsi della riga sospetta per giudicare sé stessa. Le colonne di una
partita vengono da provider diversi: usane una integra per giudicare l'altra.
Esempio riuscito: le 8 linee O/U con overround impossibile. Invertendo l'**1X2
della stessa partita** nei tassi (λ, μ) e leggendo dalla matrice la P(Over), si
è visto che in tutti i casi il lato **Over** era coerente e il lato **Under** no
→ i due numeri non appartengono alla stessa linea. Senza questo passo si
sarebbe potuto «aggiustare» il lato sbagliato.

### Passo 3 · Prova a procurare il dato VERO (ordine di costo crescente)

Stato verificato a luglio 2026 — aggiornare questa tabella a ogni tentativo:

| fonte | esito | note operative |
|---|---|---|
| **la fonte stessa, ri-scaricata** | primo tentativo sempre | i provider correggono lo storico: vale la pena riscaricare prima di dare per persa una riga |
| **Understat `getMatchData/{id}`** | ✅ **funziona** | dati tiro-per-tiro, con autogol e situazione; header `X-Requested-With: XMLHttpRequest` obbligatorio; l'id sta nel JSON di lega |
| **FotMob** (pagine HTML) | ✅ raggiungibile | `robots.txt` vieta `/api/*` a noi: usare solo le pagine. ⚠️ l'URL senza frammento `#matchId` rende un'ALTRA partita della stessa coppia — verificare sempre `general.matchTimeUTC` prima di leggere i numeri. ⚠️ il loro xG è un **modello diverso** da Understat: non mescolare i due dentro la stessa colonna |
| **diretta.it / Flashscore** | ⚠️ raggiungibile ma inutile qui | `robots.txt` consente le pagine partita, ma i dati arrivano da feed interni; e le quote storiche vengono dallo stesso gruppo di BetExplorer, che le ha ritirate |
| **BetExplorer** | ❌ | per le stagioni 2017-19 la funzione confronto-quote è stata ritirata: il tab «1X2» è disabilitato e non esiste alcun tab O/U |
| **OddsPortal** | ❌ **vietato** | il `robots.txt` contiene `Disallow: *-2017*`, `*-2018*`…: esattamente le pagine storiche che servirebbero. Non si scrape, punto |
| **Sofascore** | ❌ | risponde 403 anche al `robots.txt`: bloccati a monte |
| **fbref** | ❌ | 403 dal proxy |
| **ricerca web** | ❌ per le quote | i risultati e i marcatori si trovano ovunque; le **quote storiche per singola partita** no |

### Passo 4 · Se il dato vero non c'è: stima, con l'errore misurato

Mai lasciare un numero sbagliato «perché tanto è uno solo», e mai inventarne uno.
La stima:

1. usa **solo informazione integra** (nel nostro caso: l'1X2, mai la riga rotta);
2. ha un **errore misurato dove la verità esiste** — stessa epoca, stessa fonte,
   stesse leghe — e confrontato con una baseline banale;
3. è una **probabilità**, non una quota, e vive **fuori dallo snapshot**;
4. dichiara il metodo riga per riga.

Esempio già fatto (`scripts/stima_ou_corrotte.py`, uscita
`data/stime_ou_corrotte.csv`): P(Over 2.5) dedotta dall'1X2 di apertura,
debiasata con una correzione fittata leave-one-league-out.
**MAE 0.0267** contro **0.0743** della baseline «media della lega» — misurato su
3.643 partite 2017-19 dove la linea O/U è integra. Errore ~2× più grande della
stima di chiusura O/U del progetto (0.012): va usata sapendolo.

### Passo 5 · Registra tutto

Riga nel registro delle correzioni con motivo e fonte (R3), e — se una
correzione si rivela sbagliata — **non si cancella**: si marca `ritirata`, si
aggiunge la riga di ripristino e si scrive perché. Il registro deve raccontare
anche gli errori, altrimenti la prossima sessione li rifà.

---

## R5 · Le anomalie si dichiarano, anche quando NON sono errori

**Regola.** Ogni anomalia trovata da un audit va scritta con la prova e
l'impatto quantificato, anche (e soprattutto) quando l'indagine conclude che il
dato è corretto.

**Perché.** «Ho controllato e va bene» senza il numero non vale nulla, e la
prossima sessione rifarà lo stesso controllo da zero. Esempi già in
`01_audit_dati.md` §5: le 74 righe con gol > tiri in porta (autogol, non
errori) e i 10 xG a zero legittimi (squadre con zero tiri).
