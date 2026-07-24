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
[`data/correzioni_dichiarate.csv`](data/correzioni_dichiarate.csv), una riga per
cella modificata, con: partita, colonna, valore prima, valore dopo, **motivo**,
**fonte**, stato (`applicata`/`proposta`), chi ha deciso e quando. Le correzioni
si applicano **solo** con `scripts/applica_correzioni.py`, che verifica il
valore-prima di ogni cella e si ferma se non combacia: nessuna modifica a mano,
nessun numero che appare senza tracciamento.

**Casi già istruiti:** vedi `report/04_decisioni.md` §1 (Union Berlin-Bochum
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
[`data/squad_value_2526_transfermarkt.csv`](data/squad_value_2526_transfermarkt.csv).

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

## R5 · Le anomalie si dichiarano, anche quando NON sono errori

**Regola.** Ogni anomalia trovata da un audit va scritta con la prova e
l'impatto quantificato, anche (e soprattutto) quando l'indagine conclude che il
dato è corretto.

**Perché.** «Ho controllato e va bene» senza il numero non vale nulla, e la
prossima sessione rifarà lo stesso controllo da zero. Esempi già in
`report/01_audit_dati.md` §5: le 74 righe con gol > tiri in porta (autogol, non
errori) e i 10 xG a zero legittimi (squadre con zero tiri).
