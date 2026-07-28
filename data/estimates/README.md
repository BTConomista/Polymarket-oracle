# ⚠️ `data/estimates/` — STIME di modello, NON dati di mercato

> **Stato dei cinque file (ri-contato riga per riga alla Fase 101-ter):**
>
> | file | righe | attivo? |
> |---|--:|---|
> | `ou_close_2017_19.csv` | **3.638** | ✅ stima attiva, 5 leghe |
> | `ou_open_corrotte_2017_19.csv` | **12** | ✅ stima attiva (era 9 fino alla Fase 101-ter) |
> | `open_sparse_1x2_ou.csv` | **2** | ✅ stima attiva (era 3 fino alla Fase 73) |
> | `celle_residue.csv` | **32** | registro di NON-stima (6 caso A, 8 B, 8 C, 10 D) |
> | `squad_value_2017_26.csv` | **0** | ❌ nessuna stima attiva dalla Fase 70 |
>
> ⚠️ **Nessuna stima `squad_value` attiva dalla Fase 70**: le ultime 13 celle
> sono state sostituite da dato REALE (Transfermarkt) e il file CSV è a 0
> righe. La sezione dedicata resta il metodo storico, valido se il buco si
> riaprisse.

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
4. Ogni file è **rigenerabile**, ognuno dal suo script, e ha la provenienza
   registrata in `experiments/runs.jsonl`: `ou_close_2017_19.csv`,
   `open_sparse_1x2_ou.csv` e `squad_value_2017_26.csv` con
   `python scripts/build_estimates.py`; `ou_open_corrotte_2017_19.csv` con
   `python scripts/stima_ou_open_bakeoff.py` (richiede scikit-learn);
   `celle_residue.csv` con `python scripts/stima_celle_residue.py`.

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
dove la chiusura vera esiste (era 7.978 su 3 leghe fino alla Fase 100). Il
numero è ri-derivabile: sono le righe con 1X2 e O/U completi sia in apertura sia
in chiusura, cioè 2.658 Serie A + 2.660 Premier + 2.660 La Liga + 2.142
Bundesliga + 2.337 Ligue 1 = **12.457**. Convalidata walk-forward:

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

**Perché 3.638 e non 3.652** (la finestra 2017-19 conta 3.652 partite sulle 5
leghe). Mancano **14 righe**, tutte spiegate, e l'elenco è ri-derivabile con un
anti-join fra il CSV e gli snapshot:

- **12** senza la linea O/U di **apertura**, che è l'input della regressione
  (11 svuotate dal guard bilaterale + Bayern-Hoffenheim 24/08/2018, assente alla
  fonte). La loro apertura è stimata a parte, in
  `ou_open_corrotte_2017_19.csv`;
- **2** che al momento della generazione non avevano la **chiusura 1X2**, l'altro
  input: Alaves-Sociedad 14/10/2017 e Bayern-Hannover 04/05/2019.

> 📌 **Residuo aperto, piccolo ma concreto.** Quelle 2 righe **ora la chiusura
> 1X2 ce l'hanno** — è dato reale da provider secondario, inserito alla Fase
> 101-bis (`docs/DATI.md` §4). Rigenerando la stima coprirebbe **3.640** righe
> invece di 3.638. Non è stato fatto qui: rigenerare una stima pubblicata
> richiede il controllo prima/dopo e una riga di registro, non una modifica di
> documentazione.

### `squad_value_2017_26.csv` — valore rosa stimato per le celle mancanti

**Perché (ridimensionato dalla Fase 67, azzerato dalla Fase 70).** Con la fonte
player-scores i valori rosa REALI coprono il 100% delle stagioni concluse; le
ultime 13 celle 2025-26 sono state recuperate da Transfermarkt alla Fase 70
(regola R2, fonte secondaria dichiarata), quindi **il file è vuoto: 0 righe di
stima attiva**. Erano 73 prima della Fase 67 e 13 prima della Fase 70. Il file
resta versionato (con la sua intestazione) perché la procedura sotto è la
ricetta da riusare se un buco si riapre.

> **Nota di allineamento (audit Fase 101, precisata qui).** Le celle 2025-26
> recuperate a mano da Transfermarkt sono in tutto **29**, in due tranche
> distinte e con due depositi distinti — la formulazione precedente («sono 16,
> non 13») le metteva in alternativa, mentre si sommano:
>
> | tranche | celle | dove vive il dato | come si riapplica |
> |---|--:|---|---|
> | Fase 70 (3 leghe storiche) | **13** (6 Serie A, 2 Premier, 5 La Liga) | cablate in `scripts/_apply_fase70_squad_value_real.py` (`REAL_VALUES`) | `python scripts/_apply_fase70_squad_value_real.py` |
> | audit delle 5 leghe (leghe nuove) | **16** (5 Bundesliga, 11 Ligue 1) | `data/squad_value_2526_transfermarkt.csv`, con la scala misurata contro player-scores nella colonna `rapporto_TM_su_playerscores_mediano_lega` (R2) | `python scripts/applica_squad_value_tm.py` |
>
> `scripts/build_squad_values.py` ha una **guardia** che si ferma se un rebuild
> perderebbe celle già presenti: senza, il refill da player-scores le
> riporterebbe a `NaN`, perché stanno sotto la soglia di copertura dell'85%.

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
**tutte** le coppie apertura/chiusura reali degli snapshot *dell'epoca* — 10.258
per il 1X2 e 7.978 per l'O/U, cioè praticamente ogni altra partita del progetto
**quando le leghe erano 3** (Fase 69). ⚠️ Numeri **storici**, non ricontati sulle
5 leghe: la stima non è mai stata rigenerata dopo l'ingresso di Bundesliga e
Ligue 1, perché le 2 righe bersaglio sono entrambe di Serie A e il metodo
vincitore è **pooled**. Rigenerandola oggi il campione sarebbe più ampio (per
confronto: le coppie complete O/U sulle 5 leghe sono 12.457, vedi sopra); non è
stato fatto, e finché non lo è i numeri qui sotto restano quelli di allora.
I 5 metodi:
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
  `BbAvH`). ~~Ha però ora una chiusura 1X2 mancante (nessun `PSC`, unico caso su
  2.280): non stimata (1 riga, movimento 1X2 quasi tutto rumore — Fase 69).~~
  > ⚠️ **SUPERATA due volte.** (a) I casi senza `PSC` **non erano uno** ma
  > **due** sulle 5 leghe (3.652 partite nella finestra Pinnacle, non 2.280):
  > Alaves-Sociedad e Bayern-Hannover 04/05/2019. (b) Da entrambe **non manca
  > più niente**: la chiusura 1X2 è stata inserita alla Fase 101-bis con dato
  > REALE da provider secondario (R2, `docs/DATI.md` §4), quindi non c'è più
  > nulla da stimare — né qui né altrove.
- Ogni riga stima SOLO il mercato che le manca davvero (colonne dell'altro
  mercato vuote se quella partita aveva già l'apertura vera).


### `ou_open_corrotte_2017_19.csv` — apertura O/U per le 12 linee corrotte

**Perché.** **Dodici** partite del 2017-19 non hanno l'apertura O/U: 6
Bundesliga + 2 Ligue 1 + **3 La Liga** svuotate dal guard bilaterale di
`loader._pick_market_odds` (overround fino a 1.339), più Bayern-Hoffenheim
24/08/2018, assente alla fonte.

Questo file le copre **tutte e dodici** dalla **Fase 101-ter** (commit
`44052d7`). Fino ad allora ne
copriva nove: il guard era stato esteso a La Liga col commit `ec85314`, cioè
*dopo* la produzione della stima, e nessuno l'aveva rigenerata — anche perché
lo script moriva su un `assert len(tg0) == 9` che cablava il conteggio di
allora, mentre le bersaglio si auto-selezionano.

> **Perché rigenerare è stato sicuro, e come lo sappiamo.** Rigenerando, le
> **9 righe preesistenti sono risultate identiche a meno di 0.000000**, e si
> sono aggiunte 3 righe La Liga (Alaves-Real Madrid 0.6222, Eibar-Real Madrid
> 0.6210, Leganes-Betis 0.3820, stesso metodo M5g e stesso MAE atteso 0.0143).
> Non è stata una ri-stima: è stata un'estensione. Il confronto prima/dopo è il
> controllo che rende la cosa verificabile, e va rifatto ogni volta che si
> rigenera una stima pubblicata.
>
> ⚠️ **Precisazione (Fase 101-ter, correzione di una formulazione imprecisa).**
> Si è scritto che «l'insieme di valutazione non è cambiato»: **non è vero**.
> È passato da **3.643** a **3.640** partite, perché le 3 righe La Liga sono
> uscite dalla valutazione ed entrate fra le bersaglio (`n_valutazione` in
> `docs/audit_5_leghe/numeri/stima_ou_open_bakeoff.json`: 3643 nella versione
> del commit `6c9b377`, 3640 in quella di `44052d7`). La ragione vera per cui le
> 9 righe non si muovono è un'altra, ed è più forte: il metodo vincitore
> **`M5g` è per-lega**, quindi il fit delle 9 righe (Bundesliga e Ligue 1) non
> vede *nessuna* riga La Liga — cambiare il campione della Liga non può
> toccarle. Il controllo empirico resta quello che conta: diff delle due
> versioni committate del CSV, 9 righe comuni, scarto massimo **esattamente
> 0.0**.

Le 2 partite "sparse" di Serie A (fuori dal 2017-19) stanno invece in
`open_sparse_1x2_ou.csv`.

**Come.** Bakeoff di 26 varianti, k-fold k=5 sulle partite della stessa epoca con
la linea integra: **3.640** oggi (erano 3.643 quando le bersaglio erano 9 —
la finestra 2017-19 conta 3.652 partite, meno le 12 senza linea di apertura). Il
metodo storico (inversione del solo 1X2 nei tassi + debias costante
leave-one-league-out, MAE 0.0267) **non era al suo tetto**: il suo limite non è
l'inversione ma il **bias costante**, perché il bias dipende dal totale atteso.
Vincitore: `M5g logit~scaletta1xBet+1X2ap` **per-lega**, una regressione che usa
anche la **scaletta di chiusura 1xBet** trovata durante l'audit (MAE
**0.0143**). Il miglior metodo che usa la sola informazione di apertura
(`M4 logit-bias su (T,D) quad`, anch'esso per-lega) arriva a **0.0197**.

**⚠️ Limite specifico:** il vincitore usa una quota di **chiusura** per stimare
un'**apertura**. Resta una stima dell'apertura, non l'apertura — e il file lo
dichiara riga per riga.

### `celle_residue.csv` — il censimento delle celle che restano vuote

Non è una stima di mercato: è il **registro delle celle che NON si stimano**, con
la prova che non stimarle è la scelta giusta (errore sopra soglia, o fonte non
consolidata). Serve perché la sessione successiva non ci riprovi da capo.

**32 righe in 4 casi** (`value_counts()` sulla colonna `caso`):

| caso | righe | colonne | verdetto |
|---|--:|---|---|
| **A** | 6 | `odds_home/draw/away` | ⚠️ **non è più un «non stimare»**: `ESEGUITA alla Fase 101-bis` — il dato REALE è stato inserito nello snapshot via `data/correzioni_dichiarate.csv` + `scripts/applica_correzioni.py` (R3), con la provenienza da provider secondario dichiarata in `docs/DATI.md` (R2). Le 5 leghe hanno ora **zero righe senza chiusura 1X2** |
| **B** | 8 | xG/npxG/ppda/deep | `NON STIMABILE → resta NaN dichiarato`: MAE fuori campione **0,45 gol** contro una sd di **0,89** — l'errore è metà del segnale |
| **C** | 8 | idem | idem (seconda partita) |
| **D** | 10 | `odds_*_open`, `midweek_europe` | i «finti pieni»: 3 righe chiuse dal guard bilaterale, **2 lasciate piene e dichiarate** (Leganes-Getafe overround 1.0127 — anomalo *per difetto*, fuori dal perimetro di un tetto superiore; Dortmund-Hannover 1.0947, sotto `ORR_MAX = 1.12`), 5 righe `midweek_europe` **chiudibili senza stima** (236 + 251 + 454 + 180 + 482 = **1.603** celle a zero falso) |

Documentazione completa dei dati e delle stime: **[docs/DATI.md](../../docs/DATI.md)**.
