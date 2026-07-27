> ⚠️ **Nessuna stima `squad_value` attiva dalla Fase 70**: le ultime 13 celle
> sono state sostituite da dato REALE (Transfermarkt) e il file CSV è a 0
> righe. Quanto segue resta il metodo storico, valido se il buco si
> riaprisse.

# ⚠️ `data/estimates/` — STIME di modello, NON dati di mercato

Questa cartella contiene **stime prodotte dai nostri modelli** per dati che le
fonti **non hanno**. Sono deliberatamente tenute **fuori dagli snapshot**
(`data/*_matches.csv`) e pubblicate come **probabilità** (mai come quote, così
è impossibile scambiarle per prezzi di un bookmaker).

## Regole d'uso (non negoziabili)

1. **Non farci troppo affidamento.** Sono ricostruzioni statistiche con un
   errore atteso misurato e dichiarato — utili come *benchmark di analisi*,
   NON come verità di mercato.
2. **Ogni analisi che le usa deve dichiararlo** esplicitamente (nel diario e
   nel registro `runs.jsonl`).
3. **Mai** copiarle dentro le colonne quota degli snapshot, né usarle per
   simulare scommesse/ROI (non esiste una quota reale a cui "scommettere").
4. Ogni file è **rigenerabile** con `python scripts/build_estimates.py` e ha
   la sua provenienza registrata in `experiments/runs.jsonl`.

## Contenuto

### `ou_close_2017_19.csv` — chiusura O/U 2.5 stimata, stagioni 2017-18 / 2018-19

**Perché.** In quelle 2 stagioni (tutte e 5 le leghe: Serie A, Premier League,
La Liga, Bundesliga, Ligue 1 — **3.638 righe**)
football-data pubblica **una sola linea O/U** (`BbAv`, Betbrain media): dalla
Fase 73 sappiamo che è un'**apertura** reale (pre-match, negli snapshot come
`odds_over25_open`), non una chiusura. La chiusura O/U non esiste nei dati,
mentre l'1X2 ha sia apertura sia chiusura (Pinnacle, Fase 61). Il file colma il
buco della **chiusura** con una stima.

**Come (Fasi 62/62-bis; imbattuta in Fasi 72/73).** Regressione in spazio logit
della chiusura O/U su (linea O/U **di apertura** + movimento 1X2
apertura→chiusura), fittata pooled su **12.457** partite 2019-20+ e **5 leghe**
dove la chiusura vera esiste (era 7.978 su 3 leghe fino alla Fase 100).
Convalidata walk-forward:

| errore atteso | valore |
|---|---|
| MAE vs chiusura vera (prob.), **regime d'uso** (fit su stagioni successive) | **~0.014** (0.0143 Bundesliga, 0.0125 Ligue 1) |
| MAE in *interpolazione* (fit che vede anche stagioni precedenti) | ~0.012 — è il numero storicamente pubblicato, ma **non** è il regime in cui la stima viene usata |
| correlazione col movimento vero della linea | 0.75–0.86 |
| quota del movimento NON catturabile | ~35-45% (notizie puro-totali, ignote all'1X2) |

**Limiti dichiarati.**
- I coefficienti sono fittati su stagioni **successive** a quelle stimate
  (unico dato possibile): accettabile per un benchmark storico, non per
  predizione.
- Nel 2017-19 la linea O/U di input è `BbAv` (Betbrain media, apertura reale —
  Fase 73); il fit usa le medie `Avg`. Il movimento 1X2 è Pinnacle (`PS→PSC`).
- La colonna è `p_over25_close_est` (probabilità devigata stimata);
  `P(Under) = 1 − P(Over)`.

### `squad_value_2017_26.csv` — valore rosa stimato per le celle mancanti

**Perché (ridimensionato dalla Fase 67, azzerato dalla Fase 70).** Con la fonte
player-scores i valori rosa REALI coprono il 100% delle stagioni concluse; le
ultime 13 celle 2025-26 sono state recuperate da Transfermarkt alla Fase 70
(regola R2, fonte secondaria dichiarata), quindi **il file è vuoto: 0 righe di
stima attiva**. Erano 73 prima della Fase 67 e 13 prima della Fase 70. Il file
resta versionato (con la sua intestazione) perché la procedura sotto è la
ricetta da riusare se un buco si riapre.
> Nota di allineamento (audit Fase 101): con le 5 leghe le celle recuperate a
> mano da Transfermarkt sono **16**, non 13 — vedi
> `data/squad_value_2526_transfermarkt.csv`.

**Come (Fase 66).** Stimatore ibrido, scelto con leave-one-out e
leave-TEAM-out sulle 467 celle note:
- `anchored` (37 celle): regressione pooled su rendimento stagionale + valore
  della STESSA squadra nelle stagioni adiacenti → **errore mediano ~17%**;
- `regression` (36 celle): solo rendimento (pts/gara, diff. reti, diff. xG,
  promossa), per-lega — per le squadre senza NESSUNA stagione nota (es.
  Lazio) → **errore mediano ~29%, p90 ~75%**.

**⚠️ Limiti (più severi della stima O/U).**
- L'errore è GRANDE: usare come **ordine di grandezza**, mai come valore
  puntuale. Il metodo e l'errore atteso sono dichiarati **riga per riga**.
- Code pesanti: per squadre fortemente sovra/sotto-performanti rispetto al
  valore reale della rosa (es. il Getafe quinto nel 2018-19) l'errore può
  superare il 100% — la regressione deduce il valore dal rendimento, e chi
  rende più di quanto vale viene sovrastimato per costruzione.
- La feature `squad_value` è comunque **bocciata come covariata** del modello
  (Fase 4c/11): queste stime servono alla completezza del dato, non ci si
  aspetta alcun guadagno predittivo.

### `open_sparse_1x2_ou.csv` — apertura stimata per le partite sparse (Fase 69)

**Perché.** Oltre al buco sistemico O/U 2017-19 (le fonti non hanno la
**chiusura** O/U di quelle 2 stagioni — piano dedicato in
[`docs/CACCIA_OU_2017_19.md`](../../docs/CACCIA_OU_2017_19.md), NON questo
file), restano **2 partite "sparse"** senza apertura vera, isolate in stagioni
altrimenti complete: Torino-Fiorentina (recupero, 1X2+O/U) e Verona-Genoa
(O/U isolata, 2020-21). *(Erano 3: dalla Fase 73 Alaves-Sociedad 14/10/2017 ha
l'apertura 1X2 reale `PSH` — prima oscurata dal masking — e non serve più
stimarla; la sua stima è stata ritirata.)*

**Come (bakeoff, richiesta utente).** 5 metodi confrontati con 5-fold CV su
**tutte** le coppie apertura/chiusura reali dei 3 snapshot (10.258 per il
1X2, 7.978 per l'O/U: praticamente ogni altra partita del progetto):
identità (apertura≈chiusura), regressione lineare pooled, regressione in
**spazio logit pooled**, regressione lineare per-lega, blend identità+logit.
La logit pooled vince o pareggia ovunque; il per-lega non migliora
abbastanza da giustificare la complessità in più (curva piatta, ~0.0002);
il blend è **peggiore** di entrambi i singoli metodi (mai usarlo qui).

| errore atteso (MAE 5-fold, probabilità) | valore |
|---|---|
| 1X2 (3 esiti insieme: home+draw fittati, away rinormalizzato) | **~0.016** |
| O/U 2.5 | **~0.020** |

Molto più affidabile della stima `squad_value` (17-29%): il rapporto
apertura↔chiusura è quasi un'identità (β≈0.93-0.97, corr 0.96-0.99 sulle
coppie reali) — il movimento di linea è per lo più rumore piccolo, non un
pattern da modellare in modo complesso.

**Limiti dichiarati.**
- I coefficienti sono fittati su **tutte** le coppie reali (comprese quelle
  successive alle date stimate): accettabile per riempire un buco storico
  isolato, non per una predizione live.
- *(Fase 73)* Alaves-Sociedad (14/10/2017) è **uscita** da questo file: il suo
  `PSH` Pinnacle pre-match (3.52/3.55/2.20) è ora l'apertura 1X2 **reale** dello
  snapshot (prima oscurato dal masking, quando la sua chiusura era il falso
  `BbAvH`). Ha però ora una chiusura 1X2 mancante (nessun `PSC`, unico caso su
  2.280): non stimata (1 riga, movimento 1X2 quasi tutto rumore — Fase 69).
- Ogni riga stima SOLO il mercato che le manca davvero (colonne dell'altro
  mercato vuote se quella partita aveva già l'apertura vera).


### `ou_open_corrotte_2017_19.csv` — apertura O/U per le 9 linee corrotte

**Perché.** Nove partite del 2017-19 (6 Bundesliga, 2 Ligue 1, 1 assente alla
fonte) non hanno l'apertura O/U: la loro linea aveva un overround impossibile
(fino a 1.339) ed è stata svuotata dal guard bilaterale di
`loader._pick_market_odds`. Sono l'unico buco di *apertura* rimasto.

**Come.** Bakeoff di 26 varianti, k-fold k=5 su 3.643 partite della stessa epoca
con la linea integra. Il metodo storico (inversione del solo 1X2 nei tassi +
debias costante leave-one-league-out, MAE 0.0267) **non era al suo tetto**: il
suo limite non è l'inversione ma il **bias costante**, perché il bias dipende dal
totale atteso. Vincitore: una regressione che usa anche la **scaletta di
chiusura 1xBet** trovata durante l'audit (MAE **0.0143**). Il miglior metodo che
usa la sola informazione di apertura arriva a 0.0197.

**⚠️ Limite specifico:** il vincitore usa una quota di **chiusura** per stimare
un'**apertura**. Resta una stima dell'apertura, non l'apertura — e il file lo
dichiara riga per riga.

### `celle_residue.csv` — il censimento delle celle che restano vuote

Non è una stima di mercato: è il **registro delle celle che NON si stimano**, con
la prova che non stimarle è la scelta giusta (errore sopra soglia, o fonte non
consolidata). Serve perché la sessione successiva non ci riprovi da capo.

Documentazione completa dei dati e delle stime: **[docs/DATI.md](../../docs/DATI.md)**.
