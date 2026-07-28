# Regole sui dati sporchi — versione estesa (nata nel cantiere delle 5 leghe)

Regole **decise dall'utente durante l'audit delle 5 leghe**. Sono state
**promosse a regole di progetto**: la loro forma sintetica e vincolante vive in
**`CLAUDE.md` §5-bis**. Questo file resta perché contiene il *perché*, i casi che
le hanno insegnate e le prove — cose che in `CLAUDE.md` non ci stanno.

Ogni regola dice: *cosa* si fa, *perché*, e *come si applica in pratica*.

> *(Nota storica: l'intestazione originale diceva «vivono qui perché il cantiere
> è isolato; quando i due filoni verranno uniti, vanno aggiunte alle regole
> generali del progetto». L'unione è avvenuta — vedi l'appendice in fondo — e
> con essa la rinumerazione qui sotto.)*

---

## ⚠️ Nota di rinumerazione (leggila prima di citare una sigla)

Alla promozione in `CLAUDE.md` §5-bis **la numerazione è cambiata**: la regola di
isolamento del cantiere è decaduta (il cantiere non esiste più) e sono state
aggiunte due regole nuove. Risultato: **le sigle R4, R5 e R6 significano cose
diverse a seconda di dove le leggi.**

**La numerazione VIGENTE è quella di `CLAUDE.md` §5-bis**, ed è quella usata dai
titoli di questo file. La sigla del cantiere è riportata fra parentesi in ogni
titolo, perché **gli script migrati dal cantiere citano ancora quella**.

### Tabella di corrispondenza

| sigla del **cantiere** (storica) | sigla **VIGENTE** (`CLAUDE.md` §5-bis) | regola | dove la citano gli script |
|---|---|---|---|
| R1 | **R1** | Il dato è quello del CAMPO, non quello del tribunale | `scripts/applica_correzioni.py:1`, `scripts/audit_snapshots.py:77,345`, `scripts/stima_sot_understat.py:525` |
| R2 | **R2** | Valore rosa da Transfermarkt dove la primaria non copre | `scripts/applica_squad_value_tm.py:1,9` |
| R3 | **R3** | Nessuna modifica a mano ai dati: registro + script idempotente | `scripts/applica_correzioni.py:1,36`, `scripts/audit_snapshots.py:77,89` |
| R5 | **R4** | Un'anomalia si dichiara anche quando NON è un errore | — |
| R6 | **R5** | Procedura per una riga che sembra corrotta (5 passi) | `scripts/stima_ou_corrotte.py:1`, `scripts/stima_ou_open_bakeoff.py:853,937,1001`, `scripts/cerca_segnaposto.py:570` |
| *(non esisteva)* | **R6** | Il buco peggiore non è il `NaN`: è il finto pieno | — |
| *(non esisteva)* | **R7** | Ogni statistica di testa vuole il suo intervallo, ogni «non c'è effetto» la sua potenza | — |
| **R4** | *(decaduta)* | Isolamento del cantiere — vedi l'appendice in fondo | `scripts/applica_correzioni.py:33`, `scripts/tranche3_tracer.py:17`, `scripts/nuovo_mercato_campione.py:238`, `scripts/stima_sot_understat.py:56`, `scripts/stima_celle_residue.py:40,1022`, `scripts/leve_dc_panchina.py:42,185,719` |

**Regola pratica per chi legge un «R*n*» in uno script**: gli script sopra
elencati sono stati scritti *nel cantiere* e usano la **numerazione storica**.
Un `R4` in un docstring di quegli script è l'**isolamento**, non «l'anomalia si
dichiara»; un `R6` è la **procedura sulle righe corrotte**, non il «finto pieno».
**Il codice e i documenti nuovi devono usare la numerazione vigente**, e quando
citano una sigla in un contesto ambiguo conviene scriverla per esteso
(«R5 vigente / ex R6 del cantiere»).

### Attenzione agli omonimi (sigle `R*n*` che non c'entrano nulla)

Tre script usano `R*n*` in un **altro spazio dei nomi**, e non si riferiscono a
queste regole:

- `scripts/stima_sot_understat.py` — `R1…R8` sono le **regole candidate di
  ricostruzione del tiro in porta** da Understat (`R1 = Goal + SavedShot`, ecc.);
- `scripts/leve_apertura.py:635` — `RICETTE = ("R0", "R1", "R2", "R3", "R4")` sono
  le **ricette di proiezione dell'apertura**;
- `scripts/_run_line_movement.py`, `scripts/stima_celle_residue.py` — `R2` è il
  **coefficiente di determinazione** della regressione.

---

## R1 (cantiere R1) · Il dato è quello del CAMPO, non quello del tribunale

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

**Casi già istruiti:** vedi [`04_decisioni.md`](04_decisioni.md) §1 (Union
Berlin-Bochum 14/12/2024: partita giocata per intero, 1-1 sul campo, 0-2 a
tavolino → si usa 1-1).

---

## R2 (cantiere R2) · Valore rosa: si prende da Transfermarkt dove la fonte primaria non copre

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

## R3 (cantiere R3) · Nessuna modifica a mano ai dati: registro + script, sempre

**Regola.** Nessun valore entra o cambia in uno snapshot per intervento manuale.
Ogni modifica passa da un file-registro (il *cosa* e il *perché*) e da uno script
idempotente (il *come*), che verifica lo stato di partenza e si ferma se non è
quello atteso.

**Perché.** È l'unico modo per cui un terzo, mesi dopo, possa rifare gli stessi
numeri e capire da dove viene ogni cella. Un `df.loc[...] = x` eseguito una volta
in una sessione non è riproducibile e non lascia traccia del motivo.

---

## R4 (cantiere R5) · Le anomalie si dichiarano, anche quando NON sono errori

**Regola.** Ogni anomalia trovata da un audit va scritta con la prova e
l'impatto quantificato, anche (e soprattutto) quando l'indagine conclude che il
dato è corretto.

**Perché.** «Ho controllato e va bene» senza il numero non vale nulla, e la
prossima sessione rifarà lo stesso controllo da zero. Metà delle cose trovate in
un audit sono legittime e sorprendenti: se non le scrivi, la sessione dopo le
ri-trova e le «corregge».

**Esempi già in [`01_audit_dati.md`](01_audit_dati.md) §4.7-§5:** le **74** righe
con `gol > tiri in porta` (autogol, non errori — e zero casi dell'anomalia
opposta, che sarebbe un errore vero) e gli xG a zero, **tutti e 11 legittimi**
(0 tiri confermati sul dato tiro-per-tiro, autogol inclusi). *La versione
precedente di questa pagina diceva «10 xG a zero»: il conteggio del report è 11.*

---

## R5 (cantiere R6) · Partite con dati corrotti: la procedura (in quest'ordine)

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
| **footiqo.com** | ✅ **funziona** (trovata DOPO la stesura di questa tabella) | pubblica le quote di **chiusura** del book **1xBet** (1X2, O/U 0.5–4.5, **GG/NG**) per stagione: **3.652 partite su 3.652** nel 2017-19 sulle 5 leghe ([`09_chiusura_buchi.md`](09_chiusura_buchi.md) §2). Non è il dato vero della riga corrotta (è un altro book, ed è la chiusura invece dell'apertura) ma è il **predittore** che ha quasi dimezzato l'errore della stima del Passo 4 |
| **FotMob** (pagine HTML) | ✅ raggiungibile | `robots.txt` vieta `/api/*` a noi: usare solo le pagine. ⚠️ l'URL senza frammento `#matchId` rende un'ALTRA partita della stessa coppia — verificare sempre `general.matchTimeUTC` prima di leggere i numeri. ⚠️ il loro xG è un **modello diverso** da Understat: non mescolare i due dentro la stessa colonna |
| **diretta.it / Flashscore** | ⚠️ raggiungibile ma inutile qui | `robots.txt` consente le pagine partita, ma i dati arrivano da feed interni; e le quote storiche vengono dallo stesso gruppo di BetExplorer, che le ha ritirate |
| **BetExplorer** | ❌ | per le stagioni 2017-19 la funzione confronto-quote è stata ritirata: il tab «1X2» è disabilitato e non esiste alcun tab O/U |
| **OddsPortal** | ❌ **vietato** | il `robots.txt` contiene `Disallow: *-2017*`, `*-2018*`…: esattamente le pagine storiche che servirebbero. Non si scrape, punto |
| **Sofascore** | ❌ | risponde 403 anche al `robots.txt`: bloccati a monte |
| **fbref** | ❌ | 403 dal proxy |
| **ricerca web** | ❌ per le quote | i risultati e i marcatori si trovano ovunque; le **quote storiche per singola partita** no |

> Sullo stato della rete fa fede `docs/MANUALE_SOPRAVVIVENZA.md` §1, che è più
> aggiornato di questa tabella: quello che qui era «bloccato» può non esserlo più.

### Passo 4 · Se il dato vero non c'è: stima, con l'errore misurato

Mai lasciare un numero sbagliato «perché tanto è uno solo», e mai inventarne uno.
La stima:

1. usa **solo informazione integra** (nel nostro caso: l'1X2, mai la riga rotta);
2. ha un **errore misurato dove la verità esiste** — stessa epoca, stessa fonte,
   stesse leghe — e confrontato con una baseline banale;
3. è una **probabilità**, non una quota, e vive **fuori dallo snapshot**;
4. dichiara il metodo riga per riga.

**Il caso concreto, in due versioni.** La prima
(`scripts/stima_ou_corrotte.py`): P(Over 2.5) dedotta dall'1X2 di apertura,
debiasata con una correzione fittata leave-one-league-out — **MAE 0.0267** contro
**0.0743** della baseline «media della lega», misurato sulle **3.643** partite
2017-19 con la linea O/U integra ([`07_dati_corrotti.md`](07_dati_corrotti.md)
§4).

> ⚠️ **SUPERATA alla Fase 100.** La stima pubblicata **non è più quella**: un
> bakeoff di 26 varianti ([`09_chiusura_buchi.md`](09_chiusura_buchi.md) §5) ha
> scelto **M5g** (logit(y) ~ scaletta 1xBet + 1X2 di apertura, per-lega), che usa
> il dato footiqo del Passo 3 e scende a **MAE 0.0143** (Δ −0.01240,
> IC95 [−0.01314, −0.01165], conclusivo). Il fattore d'effetto onesto è
> **1,87×**, non «2,6×». E l'errore atteso va **stratificato**: il report 9 §5 lo
> dà a **0.0151** per le 9 righe bersaglio, che hanno il margine del book più
> alto della media (6 su 9 sopra l'88° percentile) — mentre la colonna
> `mae_atteso_strato_simili` del CSV pubblicato, passato nel frattempo a 12
> righe, riporta 0.0143 su tutte. **Divergenza non sciolta: usare il valore più
> prudente.**
>
> Cambiano anche i file. La stima ufficiale è
> [`data/estimates/ou_open_corrotte_2017_19.csv`](../../data/estimates/ou_open_corrotte_2017_19.csv)
> (**12** righe dopo il secondo giro, non 9). Il vecchio
> `data/stime_ou_corrotte.csv` citato qui **non esiste più**: `stima_ou_corrotte.py`
> resta come diagnostico e termine di paragone, e scrive in
> `docs/audit_5_leghe/numeri/stima_ou_corrotte_metodo_storico.csv` — **fuori** da
> `data/estimates/`.

L'ordine di grandezza da tenere a mente resta quello: la stima di apertura è
~2× peggiore della stima di chiusura O/U del progetto (0.012), e va usata
sapendolo.

### Passo 5 · Registra tutto

Riga nel registro delle correzioni con motivo e fonte (R3), e — se una
correzione si rivela sbagliata — **non si cancella**: si marca `ritirata`, si
aggiunge la riga di ripristino e si scrive perché. Il registro deve raccontare
anche gli errori, altrimenti la prossima sessione li rifà. *(Caso: la
«correzione» dell'xG di Bielefeld-Leverkusen, ritirata come falso positivo —
[`07_dati_corrotti.md`](07_dati_corrotti.md).)*

---

## R6 (nuova, non esisteva nel cantiere) · Il buco peggiore non è il `NaN`: è il finto pieno

**Regola.** Un audit non deve cercare solo le celle vuote: deve cercare
esplicitamente i valori che **sembrano** una misura e non lo sono — un
segnaposto della fonte, uno zero che significa «non lo so», una colonna copiata
da un'altra epoca.

**Perché.** Un dato mancante e dichiarato è innocuo: si vede, e chi lo usa lo
sa. Il finto pieno no. Nessun confronto snapshot-contro-fonte lo trova, perché
il dato **coincide** con la fonte: si scopre solo scendendo al livello più fine
(il tiro-per-tiro sotto l'xG aggregato) o incrociando fonti indipendenti.

**I due casi che l'hanno insegnata.**

1. **xG segnaposto** — Holstein Kiel-Bochum 09/02/2025: xG, npxG e `deep` erano
   valori-segnaposto, non misure (la fonte non ha mai acquisito la partita).
   Cercato poi *sul serio* con **9 firme indipendenti** su **16.110** partite
   appaiate a Understat: **1 sola**, quella
   ([`08_buchi.md`](08_buchi.md) §4.1, [`09_chiusura_buchi.md`](09_chiusura_buchi.md)
   §6): quella riga accende **7 firme su 9**, gli altri candidati una sola e sono
   legittimi. Prova di potenza con **500 segnaposto piantati artificialmente**:
   la batteria li riscopre **tutti** — quindi il «1» non è cecità dello
   strumento. Limite dichiarato: riscopre i segnaposto *totali*, non le
   degradazioni parziali (con xG residuo al 90% ne riscopre lo 0,2%). È R7
   applicata a R6: il «non c'è effetto» ha la sua misura di potenza.
2. **`midweek_europe` = 0 quando invece si giocava** — **1.603** celle a zero che
   non dovrebbero esserlo, più **1.700** partite con il riposo calcolato male,
   perché il calendario di club non copriva le coppe
   ([`09_chiusura_buchi.md`](09_chiusura_buchi.md) §7.4). Invisibile a qualunque
   controllo sui `NaN`: la colonna era piena.

---

## R7 (nuova, non esisteva nel cantiere) · Ogni statistica di testa vuole il suo intervallo, ogni «non c'è effetto» la sua potenza

**Regola.** Nessuna affermazione va in testa a un report senza il suo intervallo
di confidenza; e nessun «non c'è effetto» vale senza una misura di **potenza**
che dica se l'effetto si sarebbe visto, qualora ci fosse stato.

**Perché — è la lezione più cara dell'audit.** Nella verifica avversariale
sistematica ([`10_modelli_nuove_leghe.md`](10_modelli_nuove_leghe.md) §15),
**in cinque casi su sette il problema non era il numero ma la statistica scelta
per raccontarlo**: un conteggio di celle che non distingue il vero dal placebo,
un indicatore senza potenza letto come conferma, un ECE senza intervallo, una *z*
anti-monotona nella dimensione dell'effetto, una dicotomia fra «significativo» e
«non significativo» mai testata come differenza. La riproducibilità dei calcoli
era **impeccabile** (delta identici a 1 × 10⁻¹⁶): i difetti erano tutti di
**lettura**.

**Corollari già pagati altrove nel progetto** (Fasi 98-99, `docs/DIARIO.md`):
una feature moltiplicativa va confrontata col suo **controllo di solo livello**;
e un bias misurato su un pool non autorizza una correzione **prospettica** finché
non si misura se **persiste**. *Misurato ≠ prevedibile.*

---

## Appendice · R4 del cantiere (DECADUTA) · Isolamento del cantiere

> ⚠️ **PREMESSA CADUTA all'integrazione.** Il cantiere non esiste più: questa
> regola valeva finché i due filoni erano separati. Resta qui perché **nove
> riferimenti in sei script migrati la citano come «R4»** (vedi la tabella di
> corrispondenza in testa), e senza questo testo quel riferimento non si capisce.
> Nella numerazione vigente **non c'è alcuna R4-isolamento**: `CLAUDE.md` §5-bis
> R4 è tutt'altro.

**Regola (storica).** Tutto resta in `cantiere/`: nessuna numerazione di fase,
nessuna modifica ai documenti condivisi (`DIARIO.md`, `README.md`, `PANCHINA.md`,
`DATI.md`, `experiments/runs.jsonl`) né a `src/`, `data/`, `scripts/`, `tests/`.

**Perché (storico).** Su `main` si lavorava in parallelo: due filoni che toccano
gli stessi file si ostacolano. Le checklist di integrazione nei report restavano
**proposte**.

**Cosa è successo dopo.** L'integrazione (`03d5bec` → `6c9b377`) ha toccato tutte
e cinque le cartelle, e la Fase 101 (`bb6ebe4`) ha riparato i percorsi interni dei
32 script migrati. Le «proposte» sono diventate modifiche vere.
