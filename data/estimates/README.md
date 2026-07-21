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

**Perché.** In quelle 2 stagioni (Serie A, Premier League, La Liga)
football-data pubblica **una sola linea O/U** (media pre-match): la chiusura
O/U non esiste nei dati, mentre l'1X2 ha sia apertura sia chiusura (Pinnacle,
Fase 61). Il file colma il buco con una stima.

**Come (Fasi 62/62-bis).** Regressione in spazio logit della chiusura O/U su
(linea O/U pre-match + movimento 1X2 apertura→chiusura), fittata pooled su
7.978 partite 2019-20+ dove la chiusura vera esiste. Convalidata walk-forward:

| errore atteso | valore |
|---|---|
| MAE vs chiusura vera (prob.) | **~0.012** |
| correlazione col movimento vero della linea | 0.75–0.86 |
| quota del movimento NON catturabile | ~35-45% (notizie puro-totali, ignote all'1X2) |

**Limiti dichiarati.**
- I coefficienti sono fittati su stagioni **successive** a quelle stimate
  (unico dato possibile): accettabile per un benchmark storico, non per
  predizione.
- Nel 2017-19 le linee input sono Pinnacle/BbAv; il fit usa le medie `Avg`.
- La colonna è `p_over25_close_est` (probabilità devigata stimata);
  `P(Under) = 1 − P(Over)`.

### `squad_value_2017_26.csv` — valore rosa stimato per le celle mancanti

**Perché (ridimensionato dalla Fase 67).** Con la fonte player-scores i valori
rosa REALI coprono il 100% delle stagioni concluse: restano **13 celle**, tutte
della stagione in corso 2025-26 (valutazioni di inizio stagione ancora
incomplete nel dataset per alcune neopromosse/club). Erano 73 prima della
Fase 67: 60 stime sono state SOSTITUITE da dati reali.

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

**Perché.** Oltre al buco sistemico O/U 2017-19 (le fonti non hanno mai
avuto quella colonna in quelle 2 stagioni — piano di raccolta dati dedicato
in [`docs/CACCIA_OU_2017_19.md`](../../docs/CACCIA_OU_2017_19.md), NON
questo file), restano 3 partite "sparse" senza apertura vera, isolate in
stagioni altrimenti complete: 2 di 1X2 (il grezzo non l'ha mai avuta, o la
maschera anti-contaminazione l'ha scartata perché non abbinabile a una
chiusura dello stesso book — vedi `docs/PISTE.md` §5) e 1 di O/U (stagione
2020-21, isolata).

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
- Per Alaves-Sociedad (14/10/2017) esiste un valore Pinnacle grezzo mai
  validato (3.52/3.55/2.20, scartato dalla maschera anti-contaminazione
  perché senza chiusura Pinnacle abbinata): la stima (`p_home≈0.287`) è
  vicina ma non identica (raw devigato `p_home≈0.278`) — coerenza reciproca,
  non conferma indipendente della verità.
- Ogni riga stima SOLO il mercato che le manca davvero (colonne dell'altro
  mercato vuote se quella partita aveva già l'apertura vera).

Documentazione completa dei dati e delle stime: **[docs/DATI.md](../../docs/DATI.md)**.
