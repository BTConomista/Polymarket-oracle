# Catalogo dei dati — tutto ciò che il progetto ha a disposizione

Questo documento è la **mappa unica di tutti i dati** del progetto: cosa c'è,
da dove viene, quanto copre, e — sezione più importante — **cosa è dato reale e
cosa è STIMA**. Va aggiornato ogni volta che i dati cambiano (nuova fonte,
nuova colonna, nuova stima). Ultimo aggiornamento: **Fase 101-ter** (5 leghe).

> ⚠️ **Allineamento — stato dopo l'audit delle Fasi 101/101-bis/101-ter.** Tutti
> i buchi di catalogo che l'audit aveva rilevato sono colmati:
> `data/ricerca_esterna/` (86 file) è in §4, i 5 calendari di club in §3, le 5
> stime in §5, e `data/correzioni_dichiarate.csv` — che il banner precedente
> dichiarava ancora «fuori» — ha ora la sua scheda in **§4-ter** (43 righe, non
> 37: il registro è cresciuto con le correzioni dell'integrazione). Elenco
> puntuale dei rilievi in `docs/AUDIT_FASI_80_100.md` §4.
>
> **Il censimento dei buchi (§1-bis) è stato ri-contato sugli snapshot di HEAD e
> vale 7.353**, non 7.359. Non è un ritorno al numero pre-guard: il 7.359
> post-guard era corretto *prima* che la Fase 101-bis inserisse le **6 celle 1X2
> di chiusura** con dato reale (§4). I due movimenti si compensano per caso
> (+6 dal guard bilaterale su La Liga, −6 dall'inserimento), e le residue non-O/U
> passano da 55 a **49**. Conteggio rifatto con `pandas` su
> `data/*_matches.csv`: 16.111 righe × 38 colonne = 612.218 celle, 7.353 NaN.

> Regola d'oro del progetto: **mai un numero inventato spacciato per dato**.
> Dove un dato manca, o resta `NaN` (dichiarato), oppure viene stimato e
> pubblicato **separatamente** con l'etichetta di stima (vedi [§5](#5--stime-dichiarate-dataestimates)).

> ⏱️ **Seconda regola d'oro, aggiunta il 30/07/2026 (regola R8 del
> `CLAUDE.md`): ogni dato porta con sé il momento in cui diventa noto.**
> Un valore giusto usato *prima* che esistesse è look-ahead — l'errore più
> difficile da vedere, perché il numero è corretto ed è il momento a essere
> sbagliato. Ogni colonna è quindi `pre` (nota prima del fischio d'inizio),
> `post` (esiste solo a partita finita) o `statico` (anagrafica). Negli
> snapshot partita di §1 la ripartizione è netta e vale la pena averla in
> mente leggendo tutto il resto del catalogo:
>
> | tipo | colonne degli snapshot |
> |---|---|
> | `pre` | tutte le **quote** (apertura e chiusura), `date`, `season`, squadre; il **valore rosa** (foto al 1° settembre) e le **assenze stimate** |
> | `post` | gol, gol primo tempo, tiri, tiri in porta, falli, corner, cartellini, **xG/npxG/PPDA/deep** |
> | derivate da `post` **di partite precedenti** (quindi legittime) | `rest_days`, `rest_days_full`, `midweek_europe` |
>
> Il caso da tenere d'occhio è l'xG: è la colonna più preziosa del progetto
> ed è `post` — nel Dixon-Coles entra sempre e solo come storia delle
> partite **già giocate** (`src/models/dixon_coles.py`), mai della partita da
> prevedere. Il fronte del database giocatori (`PIANO_DATABASE_GIOCATORI.md`)
> aggiunge ~30 campi nuovi che mescolano i tre tipi: lì la marcatura è
> obbligatoria colonna per colonna.

---

## 1 · Gli snapshot partita (la fonte di verità)

**Cinque** file **versionati in git** — chi clona il repo ha esattamente gli
stessi dati, senza rete (offline-first, §5 del CLAUDE.md):

| file | partite | stagioni | colonne | note |
|---|--:|--:|--:|---|
| `data/serie_a_matches.csv` | 3420 | 9 (2017-18 → 2025-26) | 38 | |
| `data/premier_league_matches.csv` | 3420 | 9 | 38 | |
| `data/la_liga_matches.csv` | 3420 | 9 | 38 | |
| `data/bundesliga_matches.csv` | **2754** | 9 | 38 | 18 squadre → 306 partite/stagione |
| `data/ligue_1_matches.csv` | **3097** | 9 | 38 | 380 fino al 2022-23, 306 dal 2023-24 (riforma), **279 nel 2019-20** (campionato cancellato per COVID: dato reale, non un buco) |

Lo **schema è identico** su tutte e cinque le leghe — stesse colonne **e stesso
ordine**. L'affermazione era imprecisa fino all'integrazione delle 5 leghe:
Premier e Liga avevano le 5 colonne `*_open` in posizione 15-19 e la Serie A in
29-33. Riordinate; e ora lo verifica `test_schema_identico_tra_leghe`.

Chiave di partita in tutto il progetto: `(season, home_team, away_team)`, nomi
squadra canonicalizzati via `sources.TEAM_ALIASES` (234 alias, di cui 104 per le
due leghe nuove, verificati per identità).

### Le 38 colonne, per gruppo

| gruppo | colonne | fonte | copertura |
|---|---|---|---|
| partita | `date, season, league, home_team, away_team` | football-data | 100% |
| esito | `home_goals, away_goals, result` | football-data | 100% |
| tiri in porta | `home_sot, away_sot` | football-data | 100% meno **1 partita dichiarata**: Union Berlin-Bochum 14/12/2024 (statistiche assenti alla fonte → 2 celle `NaN`). *(Questa riga diceva «100%» secco: corretto alla Fase 101-ter, era in contrasto con la riga xG dello stesso blocco, che la formula giusta ce l'aveva.)* |
| **quote chiusura** | `odds_home/draw/away, odds_over25/under25` | football-data (vedi §2) + **6 celle da provider secondario** | 1X2: **100%, zero NaN sulle 5 leghe** (verificato per identità: `isna().sum()` = 0 su `odds_home/draw/away` in tutti e cinque gli snapshot). Le 2 righe senza `PSC*` alla fonte — Alaves-Sociedad 14/10/2017 e Bayern-Hannover 04/05/2019 — sono state colmate alla Fase 101-bis con **dato REALE** di un provider diverso (6 celle, regola R2: riquadro in §4) · O/U: **77,3%** (3.652 righe su 16.111 senza chiusura: **assente nel 2017-19 su tutte e 5 le leghe**, vedi §5) |
| **quote apertura** | `odds_*_open` (5 colonne) | football-data (vedi §2) | 1X2: ~100% · O/U: ~100% (dalla Fase 73 l'apertura O/U 2017-19 è reale, `BbAv`) |
| xG | `home/away_xg, home/away_npxg` | Understat | 100% meno **2 partite dichiarate**: Nantes-Toulouse 17/05/2026 (Ligue 1, `isResult=false`) e Holstein Kiel-Bochum 09/02/2025 (Bundesliga, **record segnaposto**: vedi §4-bis) |
| stile | `home/away_ppda, home/away_deep` | Understat | come sopra |
| valore rosa | `home/away_squad_value` | **player-scores** (Transfermarkt via Kaggle, Fase 67) + **29** celle 2025-26 da Transfermarkt diretto (13 alla Fase 70 sulle 3 leghe storiche + 16 all'audit delle 5 leghe — 5 Bundesliga, 11 Ligue 1, in `data/squad_value_2526_transfermarkt.csv`, regola R2; vedi §4) | **100% su TUTTE le stagioni, incluse la 2025-26** — zero NaN residui |
| assenze (STIMA, suffisso `_est`) | `home/away_absent_count_est, home/away_absent_value_est` | Transfermarkt + rose Understat | 100% (ma è una **stima dichiarata**, vedi §4) |
| congestione | `home/away_rest_days_full, home/away_midweek_europe` | openfootball + snapshot | **100%** (Fase 68: gli esordi sono radicati coi calendari 'preludio' — massima serie 2016-17 + seconde serie) |

---

## 1-bis · I buchi, tutti quanti — e quelli che non sembrano buchi

Censimento completo, ri-contato sugli snapshot di HEAD (Fase 101-ter, ricalcolato
alla Fase 104 — vedi nota sotto): **7.353 celle vuote su 612.218**, cioè l'**1,20%**
(1,2010% esatto). Ma il numero da solo inganna: il **99,3%** è **un buco solo**,
la chiusura O/U del 2017-19 (7.304 celle = 3.652 partite × 2 colonne), che non
esiste alla fonte per nessuna delle cinque leghe (§5). Tolto quello restano
**49 celle**, ognuna con un nome e una causa:

| cosa | dove | perché |
|---|---|---|
| 11 linee O/U di apertura = **22 celle** | 3 La Liga, 6 Bundesliga, 2 Ligue 1 (2017-19) | overround impossibile alla fonte (fino a 1.339): svuotate dal guard bilaterale di `loader._pick_market_odds`. **Tutte e 11 hanno una stima dichiarata** in `data/estimates/ou_open_corrotte_2017_19.csv` dalla Fase 101-ter (le 3 La Liga erano rimaste indietro perché il guard le ha svuotate DOPO la produzione della stima: chiuso) |
| 1 linea O/U di apertura = **2 celle** | Bayern-Hoffenheim 24/08/2018 | assente alla fonte; coperta dalla stessa stima |
| 7 celle quota | Torino-Fiorentina 10/01/2022 (5: O/U + 1X2 di apertura), Verona-Genoa 19/10/2020 (2: O/U di apertura) | partite rinviate, quote mai aperte. Ri-verificato Fase 104 scaricando di nuovo i CSV grezzi live da football-data.co.uk: TUTTE le colonne di chiusura (`*C`) sono piene, tutte le colonne di apertura sono NaN — non un dato mancante per errore, è che il mercato ha aperto dopo il cutoff di raccolta di football-data per il recupero |
| 16 celle xG/stile | 2 partite (vedi §1), 8 colonne ciascuna | fonte non consolidata / record segnaposto. Ri-verificato Fase 104 (vedi `docs/MANUALE_SOPRAVVIVENZA.md`: il mirror Understat era morto, corretto l'endpoint ufficiale) con un download LIVE: Holstein Kiel-Bochum ha ancora il record segnaposto identico, Nantes-Toulouse è ancora `isResult=False` su Understat a oltre due mesi dalla partita — nessuno dei due si è risolto col tempo |
| 2 celle tiri in porta | Union Berlin-Bochum 14/12/2024 | statistiche assenti alla fonte. Ri-verificato Fase 104 con un download live del CSV grezzo football-data: colonne HST/AST ancora vuote |

*(22 + 2 + 7 + 16 + 2 = 49, cioè esattamente 7.353 − 7.304.)*

> ⚠️ **SUPERATA dalla Fase 101-bis** — una sesta riga stava in questa tabella:
>
> ~~«2 terne 1X2 di chiusura = **6 celle** | Alaves-Sociedad, Bayern-Hannover |
> colonne `PSC*` vuote nel grezzo — un dato REALE esterno esiste ma è
> **registrato e NON inserito**»~~
>
> **Non sono più un buco: le 6 celle sono state inserite** con il dato reale di
> `github.com/iredchuk/soccer-bookmaker-odds` (chiusura media-di-mercato:
> 3.40/3.34/2.15 e 1.03/18.43/43.88, MAE 0.0060 contro 0.0160 della stima che
> avremmo prodotto noi), via `data/correzioni_dichiarate.csv` +
> `scripts/applica_correzioni.py` (R3), con la provenienza da provider
> secondario dichiarata nel riquadro di §4 (R2) e reversibile dal registro
> (§4-ter). Il verdetto in `data/estimates/celle_residue.csv` (caso A) è ora
> `ESEGUITA alla Fase 101-bis`. **Verificato live nello snapshot alla Fase 104**:
> le due terne non sono più NaN.
>
> Il censimento sopra (7.353/49) è **già** al netto di questa correzione. La
> vecchia cifra **7.359/55** — con le 6 celle ancora contate come buco — era
> rimasta stampata qui per errore dopo l'inserimento, nonostante il diario e
> `docs/AUDIT_FASI_80_100.md` dichiarassero già la correzione chiusa: è l'unico
> movimento che spiega il passaggio da 55 residue a 49.

**E i buchi che NON sono `NaN`** — la categoria pericolosa, perché un valore che
*sembra* una misura non lo dichiara mai:

- ~~**`midweek_europe` = 0 quando invece si giocava**: il calendario di club
  viene da openfootball, che non copre tutte le coppe. Censite **1.603 celle**
  a zero che dovrebbero essere 1, e ~1.700 valori di riposo sbagliati di
  conseguenza (lacune: Europa/Conference League 2025-26 su tutte e 5 le leghe,
  DFB-Pokal 2016-18, Coupe de France quasi ovunque). Non ancora corretto: le
  righe di recupero esistono ma la fonte (Wikipedia) non è primaria.~~
  **CHIUSO alla Fase 103**: `scripts/integra_calendari_coppa.py` ha unito le
  3.045 righe recuperate da Wikipedia ai calendari di club esistenti
  (`club_fixtures*.csv`) e ricalcolato `rest_days_full`/`midweek_europe` sulle
  5 leghe. I 1.603 falsi zero (236/251/454/180/482 per lega) e le 1.700
  partite col riposo corretto conseguente (314/282/407/189/508) sono stati
  verificati contro l'oracolo già pubblicato in `celle_residue.csv` **prima**
  di scrivere: combaciano a cella esatta, zero regressioni. Wikipedia resta
  fonte **secondaria dichiarata** (verificata su 114 righe contro una terza
  fonte indipendente, openligadb.de, alla Fase 100: 0 non confermate).
- **un xG segnaposto** su 16.110 partite (§4-bis), ora intercettato da un guard.
- **due linee O/U di apertura anomale che il guard NON svuota**, e restano piene
  (dichiarate in `data/estimates/celle_residue.csv`, caso D):
  – **Leganes-Getafe 07/12/2018** (La Liga), `2.89/1.50` → overround **1.0127**:
  anomalo *per difetto*, cioè sotto l'intervallo sano, quindi fuori dal
  perimetro di un tetto superiore (`ORR_MAX = 1.12`);
  – **Dortmund-Hannover 26/01/2019** (Bundesliga), `1.34/2.87` → overround
  **1.0947**: sopra il massimo mai osservato nell'era `Avg` (1.0765) ma sotto
  la soglia del guard. Alzare o abbassare `ORR_MAX` è una decisione di merito
  **non ancora presa**: finché non lo è, le celle restano piene e dichiarate.
- **i conteggi tiri di football-data non sono confrontabili fra stagioni**: in
  Serie A la somma passa da 5.359 (2017-18) a 4.269 (2018-19) e torna a 5.326
  (2021-22), con tutte le righe popolate. Non è un buco: è un cambio di raccolta
  a monte. Poco rilevante oggi (il blend usa l'xG, non i tiri), ma va saputo.

---

## 1-ter · Prezzo reale e stima insieme, senza confonderli (Fase 114)

`loader.ou_close_probability(matches)` restituisce **P(Over 2.5) di chiusura
per ogni partita** con la provenienza dichiarata riga per riga:

| colonna | contenuto |
|---|---|
| `p_over25_close` | probabilità devigata (NaN se ignota) |
| `p_over25_close_fonte` | `reale` \| `stima` \| `assente` |

Copertura sulle 5 leghe: **12.459 reale + 3.638 stima + 14 assente = 99,9%**.
Serve al motore **market-implied**, che senza chiusura O/U non gira: passa da
12.459 a **16.097 partite utilizzabili** (+29%), cioè le stagioni 2017-18 e
2018-19 smettono di essere cieche per il titolare.

**Le regole restano intatte, ed è il punto**: la stima resta una
**probabilità** e non viene *mai* scritta in una colonna quota (un test lo
verifica per mutazione), ogni riga dichiara cosa è, e chi non vuole stime
passa `usa_stime=False` e vede il buco vero. Le righe `stima` **non vanno
usate per ROI/CLV** (§5).

## 1-quater · Le due partite «a tavolino»: perché il nostro risultato diverge da Transfermarkt (30/07/2026)

**Dichiarate per la regola R4** («un'anomalia si dichiara anche quando NON è
un errore»): in due partite su 16.111 il nostro snapshot riporta un risultato
**diverso** da quello di Transfermarkt, e in entrambi i casi **il nostro è
quello giusto** secondo la regola **R1** (il dato è il risultato del CAMPO,
non quello del tribunale sportivo — è il risultato su cui si regolano i
mercati, ed è il processo che il modello stima).

| partita | nostro dato | Transfermarkt | cos'è successo |
|---|:--:|:--:|---|
| **Union Berlin-Bochum**, 14/12/2024 (Bundesliga) | **1-1** | 0-2 | correzione **già applicata** il 24/07/2026 e registrata in `data/correzioni_dichiarate.csv` (3 righe): gara sospesa al 92' per un accendino lanciato sul portiere, ripresa e finita 1-1; il 2-0 è una riassegnazione del DFB |
| **Verona-Roma**, 19/09/2020 (Serie A) | **0-0** | 3-0 | **nessuna correzione applicata, e nessuna serve**: la nostra fonte (football-data) riporta nativamente il risultato del campo. Il 3-0 è l'assegnazione a tavolino per la posizione irregolare di un giocatore in distinta |

**Perché è importante averlo scritto qui.** Chiunque, in futuro, confronti i
nostri snapshot con Transfermarkt (o con `games.csv` del dataset
`davidcariboo/player-scores`) troverà queste due divergenze e sarà tentato di
"correggerle". **Non vanno corrette**: sono la regola R1 che funziona. Il
caso Verona-Roma è emerso proprio da un controllo di questo tipo, eseguito il
30/07/2026 su tutte e 16.111 le partite
(`docs/PIANO_DATABASE_GIOCATORI.md` §6-bis): 16.109 risultati identici, e le
uniche 2 differenze sono queste.

## 2 · Semantica delle quote: apertura vs chiusura (leggere PRIMA di usarle)

Due istantanee per mercato: **apertura** (`*_open`, raccolta giorni prima
della partita, tipicamente il venerdì) e **chiusura** (al calcio d'inizio, lo
stimatore di mercato più efficiente). La provenienza **cambia con la
stagione** — questa tabella vale per tutte e 5 le leghe:

| stagioni | chiusura 1X2 | apertura 1X2 | chiusura O/U | apertura O/U |
|---|---|---|---|---|
| 2017-18, 2018-19 | **Pinnacle** (`PSC*`, Fase 61) | **Pinnacle** (`PS*`) | **ASSENTE** → stima in §5 | **Betbrain media** (`BbAv>2.5`, Fase 73) |
| 2019-20 → 2025-26 | media di ~10 book (`AvgC*`) | media pre-match (`Avg*`) | media chiusura (`AvgC>2.5`) | media pre-match (`Avg>2.5`) |

Note importanti:
- Nel 2017-19 la coppia apertura/chiusura 1X2 è **Pinnacle→Pinnacle** (margine
  ~2.5%, più basso della media ~4.9%): CLV pulito, stesso book.
- **Il buco O/U 2017-19 è sulla CHIUSURA, non sull'apertura (chiarito Fase 73).**
  L'unica linea O/U che le fonti pubblicano per quelle stagioni è `BbAv>2.5`
  (Betbrain media): il `notes.txt` di football-data la dichiara raccolta "Friday
  afternoons / Tuesday afternoons" = **pre-match = apertura** (verificato: stesso
  timing di `PS*`, l'apertura 1X2; margine ~1.055 ≈ apertura `Avg`, non chiusura
  `AvgC`; e nel 2017-19 il suffisso `C` esiste solo per l'1X2 Pinnacle, mai per
  l'O/U — nessuna colonna di chiusura O/U). Prima della Fase 73 quella linea era
  messa nello slot **chiusura** (`odds_over25`) e l'apertura lasciata a NaN,
  l'esatto contrario del vero. Dalla Fase 73: `odds_over25_open` = `BbAv` (dato
  **REALE**), `odds_over25` (chiusura) = **NaN** (dato mancante → stima in §5).
- **Politica quote (semplificata Fase 73):** la CHIUSURA prende solo colonne di
  chiusura genuine (`AvgC*/B365C*/PSC*`), NaN se non esistono; l'APERTURA prende
  solo colonne pre-match (`Avg*/PS*/BbAv*/B365*`). I due insiemi sono
  **disgiunti** → apertura e chiusura non coincidono mai per costruzione, niente
  masking (prima la chiusura ripiegava sulla pre-match e l'apertura veniva
  oscurata: la fonte dell'inversione O/U 2017-19). Overround < 1 (arbitraggio
  impossibile) → ripiego in blocco sul livello successivo (Fase 58).
- **Due eccezioni 1X2 (Fase 73, chiuse alla Fase 101-bis):** nella finestra
  Pinnacle del 2017-19 (3.652 partite sulle 5 leghe) **due** righe non hanno la
  chiusura Pinnacle — `PSC*` vuote nel grezzo: La Liga **Alaves-Sociedad
  14/10/2017** e Bundesliga **Bayern-Hannover 04/05/2019**. Dalla Fase 73 la
  loro chiusura 1X2 non ripiegava più sul pre-match (niente masking) e restava
  NaN, mentre l'apertura reale `PS*` veniva valorizzata; la stima di apertura
  1X2 della Fase 69 per Alaves-Sociedad è stata **ritirata** (l'apertura reale
  c'è). Dalla **Fase 101-bis** anche la *chiusura* di entrambe è un dato reale,
  preso però da un **provider secondario dichiarato** (R2): vedi il riquadro in
  §4. Oggi le 5 leghe hanno **zero righe senza chiusura 1X2**.
- Devig: **sempre** via `metrics.devig_1x2` / `devig_binary` (fonte unica).

---

### ⚠️ Anomalia nota: Udinese-Roma 25/04/2024 (Serie A 2023-24)

La partita fu **sospesa il 14/04/2024 sull'1-1** (malore in campo) e **ripresa
il 25/04** per gli ultimi ~19 minuti. Il dato è **fedele alla fonte** (football-data
riporta davvero `AvgCD` 1.72), ma le **quote di chiusura prezzano la ripresa**,
non la partita intera: la P(pareggio) devigata vale **0.558**, contro un massimo
di 0.372 su tutte le altre 10.259 partite del progetto. L'**apertura** sulla
stessa riga è invece normale (0.291), e lo scarto apertura→chiusura di 0.267 è il
più grande dell'intero dataset (il secondo è 0.167).

Conseguenza: quella riga accoppia un **prezzo condizionato a uno stato di gioco**
con un **esito full-match**, e falsa nella direzione a noi favorevole ogni
confronto «beat-the-close». Impatto misurato (audit Fase 90): sostituendola con
l'apertura, il log-loss della chiusura devigata passa da 0.962456 a 0.962261
(+0.000194), cioè ~9-12% dell'edge di `sharpen_1x2` della Fase 51 (0.0016) — che
resta dello stesso segno. **Da escludere (o usare l'apertura) in ogni analisi
beat-the-close.**

## 3 · Calendari di club (congestione vera)

Una riga per (squadra, partita di club, qualsiasi competizione) — alimentano
`rest_days_full` / `midweek_europe`:

| file | righe | competizioni oltre il campionato |
|---|--:|---|
| `data/club_fixtures.csv` (Serie A) | 12156 | Champions (9 stagioni, + qual.), Europa L. (+ qual.), Conference (+ qual.), Coppa Italia + **preludio**: Serie A 2016-17, Serie B 1617→2425 (Fase 68); dalla Fase 103 anche Supercoppa Italiana, UEFA Super Cup, Mondiale per club (righe recuperate da Wikipedia, `sources.EXTRA_CUP_COMPETITIONS`) |
| `data/club_fixtures_premier_league.csv` | 12520 | idem UEFA + **FA Cup, EFL Cup** + preludio: Premier 2016-17, Championship 1617→2425; dalla Fase 103 anche FA Community Shield, UEFA Super Cup, Mondiale per club |
| `data/club_fixtures_la_liga.csv` | 12779 | idem UEFA + **Copa del Rey** + preludio: Liga 2016-17, Segunda 1617→2425; dalla Fase 103 anche Supercopa de España, UEFA Super Cup, Mondiale/Intercontinentale per club |
| `data/club_fixtures_bundesliga.csv` | 10701 | Champions (1718→2526), Europa L., Conference, **DFB-Pokal** + preludio: Bundesliga 2016-17, 2. Bundesliga 1617→2425; dalla Fase 103 anche DFL-Supercup, UEFA Super Cup, Mondiale per club |
| `data/club_fixtures_ligue_1.csv` | 11718 | Champions (1718→2526, + qual.), Europa L., Conference, **Coupe de France** + preludio: Ligue 1 2016-17, Ligue 2 1617→2425; dalla Fase 103 anche Coupe de la Ligue, Trophée des Champions, UEFA Super Cup, Mondiale/Intercontinentale per club |

Copertura openfootball (produzione, invariata dalla Fase 59) + **3.045 righe
recuperate da Wikipedia alla Fase 103** (`scripts/integra_calendari_coppa.py`,
`data/ricerca_esterna/fixtures_*.csv`): riempiono le lacune di Europa/Conference
League 2025-26 su tutte e 5 le leghe, DFB-Pokal/Copa del Rey/Coupe de France
dove openfootball è parziale, e aggiungono competizioni mai modellate prima
(supercoppe nazionali, Supercoppa UEFA, Mondiale/Intercontinentale per club,
Coupe de la Ligue). Non rigenerabili da script (il recupero Wikipedia è
one-off, vedi `caccia_calendari.md` Appendici A/B): se si rilancia
`build_database.py --fixtures`/`build_league_snapshot.py --fixtures` senza
rifare `integra_calendari_coppa.py`, queste righe **scompaiono di nuovo**
(openfootball resta la fonte di produzione, invariata).

Dove una competizione non è coperta, `rest_days_full` degrada verso il valore
solo-campionato (mai in direzione sbagliata) e `midweek_europe` può essere un
falso 0: lacune **dichiarate**, nessun numero inventato.

---

## 4 · Fonti grezze congelate e loro limiti

| fonte | dove | stato |
|---|---|---|
| football-data (Serie A, CSV originali completi) | `data/football_data_raw/` (versionata, 9 file) | ✅ congelata; il sito originale **è tornato raggiungibile** (200, verificato alla Fase 100: le due leghe nuove sono state scaricate direttamente) |
| football-data (Premier/Liga) | `files/football_data_*_bundle.json` (caricati a mano, Fase 54) | ✅ congelata |
| football-data + Understat (**Bundesliga/Ligue 1**) | scaricate al volo da `scripts/fetch_sources.py` in `data/fonti/` — **non versionata** (135 MB, in `.gitignore`) | ⚠️ **le uniche due leghe senza fonte grezza congelata in repo**: ciò che è versionato è lo *snapshot* (§1) più le **90 impronte SHA256** del manifest (riga in fondo a questa tabella), che permettono di ri-scaricare e verificare l'identità bit-a-bit, non di lavorare offline sul grezzo |
| Understat (xG + rose giocatori) | `files/understat_*_bundle.json` (Premier/Liga); Serie A: **solo lo snapshot** | ⚠️ il mirror per-stagione è **sparito** (Fase 14): le rose Serie A NON sono rigenerabili — `--enrich`/ri-matching valgono solo per Premier/Liga finché non viene caricato un bundle Understat Serie A (come Fase 54) |
| **player-scores** (valutazioni complete + presenze/rose, 5 leghe) | `files/player_scores/*.csv.gz` (versionati; import via **workflow GitHub Actions** `.github/workflows/import_dataset.yml` — il runner ha rete libera, l'ambiente cloud no) | ✅ fonte UFFICIALE dei valori rosa dalla Fase 67 (CC0, `dcaribou/transfermarkt-datasets`); rigenerabile: push di `.github/import-dataset-trigger` |
| Transfermarkt (datalake `salimt`) | mirror GitHub, cache `data/raw/` (~106 MB, non versionata) | ✅ raggiungibile; dalla Fase 67 usato SOLO per gli infortuni (`absent_*_est`) — per i valori rosa e' superato da player-scores |
| Transfermarkt diretto (pagine di competizione per stagione) | recupero MANUALE (Fase 70 e audit delle 5 leghe), non rigenerabile da script: `transfermarkt.com/.it/.us` **era** bloccato dal proxy quando il recupero è stato fatto e oggi **risponde 200** (verificato alla Fase 100, vedi il banner di `docs/MANUALE_SOPRAVVIVENZA.md`); il recupero resta manuale perché la pagina utile è quella di competizione filtrata per stagione | ✅ usato per **29** celle `squad_value` 2025-26 sotto soglia (13 + 16; le 16 con la scala misurata contro player-scores nella colonna `rapporto_TM_su_playerscores_mediano_lega` di `data/squad_value_2526_transfermarkt.csv`, regola R2); **non** la pagina profilo club (mostra il valore LIVE di oggi) ma `.../{lega}/startseite/wettbewerb/{codice}/saison_id/{anno}` (tabella per-club di quella stagione) |
| openfootball (coppe/Europa) | cache `data/raw/fixtures_*` | ✅ raggiungibile |
| **1xBet via `footiqo.com`** (quote di CHIUSURA 1X2 + O/U + GG/NG, 2017-25, 5 leghe) | `data/ricerca_esterna/footiqo_*.json` (43 file: 18 dalla Fase 100 + 25 dalla Fase 106, stagioni 2017-18→2024-25) + `footiqo_gol_*.json` (10) + manifest, validazioni e `footiqo_confronto_multistagione_fase106.json` | ✅ dato esterno REALE, **NON integrato** negli snapshot: è un solo book, e come proxy della media multi-book è peggiore della stima nel confronto onesto (MAE 0.0156 contro ~0.014 regime d'uso), ma il numero **non è stabile su 6 stagioni** (Fase 106: 0.0096-0.0192, peggio nell'era porte-chiuse) — vedi [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md) |
| **Wikipedia (calendari di coppa)** | `data/ricerca_esterna/fixtures_*.csv` (50 file, **3.045 righe**) | ⚠️ fonte NON primaria, verificata su una terza fonte indipendente (openligadb.de, Fase 100): righe di recupero per il falso 0 di `midweek_europe` (§1-bis) — **applicate alla Fase 103** in `club_fixtures*.csv`/negli snapshot delle 5 leghe |
| **iredchuk/soccer-bookmaker-odds** (chiusura 1X2) | usato per **6 celle**, in 2 partite | ⚠️ **provider SECONDARIO, dichiarato (R2)** — l'unico punto degli snapshot dove una cella-quota non viene da football-data. Vedi il riquadro qui sotto |
| **manifest delle fonti dell'audit** | `data/ricerca_esterna/manifest_fonti_audit.json` | ✅ 90 impronte SHA256 (45 CSV football-data + 45 JSON Understat-lega). Le chiavi sono nella forma `cantiere/data/fonti/…`: per confrontarle con quelle che `scripts/fetch_sources.py` scrive oggi va tolto il prefisso `cantiere/` |

> ### ⚠️ Le 6 celle 1X2 di provenienza NON-football-data (Fase 101-bis)
>
> Due partite, sei celle, e sono **le uniche** dello schema in cui una quota non
> viene dalla fonte primaria:
>
> | partita | quote inserite (H/X/A) | overround |
> |---|---|--:|
> | bundesliga 1819 · **Bayern Munich–Hannover** · 04/05/2019 | 1.03 / 18.43 / 43.88 | 1.0479 |
> | la_liga 1718 · **Alaves–Sociedad** · 14/10/2017 | 3.40 / 3.34 / 2.15 | 1.0586 |
>
> **Perché sono state inserite invece di restare `NaN`.** Il dato è **reale**,
> non stimato: viene dal dataset `iredchuk/soccer-bookmaker-odds`, identificato
> per via statistica come **chiusura media-di-mercato** (due test indipendenti,
> entrambi con CI conclusivo) e **confermato da una seconda fonte del tutto
> indipendente**. È 2,8 volte più preciso della stima che avremmo prodotto noi
> (MAE 0.0060 contro 0.0160 su probabilità devigata), e la nostra stima
> indipendente cade a −0.0008…+0.0056 dal dato reale: conferma reciproca.
>
> **Il costo, detto chiaro.** Per queste due partite la colonna cambia
> *semantica*: non è più «media football-data» ma «chiusura media di un altro
> aggregatore». Su 16.111 partite è irrilevante per qualunque metrica, ma è il
> tipo di cosa che va scritta, non lasciata implicita (R2 e R6).
>
> **Come si torna indietro.** Le righe stanno in
> `data/correzioni_dichiarate.csv` (scheda in **§4-ter**) con
> `stato = applicata`: portarle a `ritirata` e rigenerare gli snapshot rimette
> il `NaN`. Il verdetto originale e le misure che l'hanno motivato restano in
> `data/estimates/celle_residue.csv` (caso A, ora marcato `ESEGUITA`) e in
> `docs/audit_5_leghe/numeri/caccia_quote_singole.md` §3.5.
>
> **Verifica per identità** (rifatta alla Fase 101-ter): `isna().sum()` su
> `odds_home/draw/away` vale **0** su tutti e cinque gli snapshot, e i valori in
> tabella coincidono cella per cella con quelli letti da `data/*_matches.csv`
> (overround ricalcolati: 1.0586 e 1.0479).

**Limiti noti dei dati reali** (dichiarati, non aggirati):
- `squad_value`: pubblicato solo se i giocatori valutati coprono ≥85% dei
  minuti della squadra, altrimenti `NaN` (fonte player-scores, Fase 67). Le **29**
  celle della stagione 2025-26 sotto soglia (13 sulle 3 leghe storiche + 16 su
  Bundesliga e Ligue 1; valutazioni di inizio stagione non ancora complete a
  monte) sono state colmate con dati REALI presi
  direttamente da Transfermarkt (Fase 70 e audit delle 5 leghe, vedi diario per fonti e metodo):
  **nessun `NaN` residuo**, nessuna stima più necessaria per questa colonna.
- `absent_*_est`: già una **stima dichiarata** nel nome (rosa ricostruita dai
  minutaggi Understat + storico infortuni TM): usarla come indicazione, non
  come verità di formazione.
- O/U 2017-19: vedi §2 e §5.
- `rest_days_full`: **nessun `NaN` residuo** (Fase 68).

---

## 4-bis · Il record SEGNAPOSTO, e il guard che lo intercetta

Un caso solo, ma insegna una categoria intera. **Holstein Kiel-Bochum
09/02/2025** (Bundesliga) aveva `xG 2.0 / 2.0`: plausibile, e **identico alla
fonte** — nessun confronto snapshot↔fonte poteva accorgersene. Ma la lista
tiro-per-tiro di Understat è **vuota su entrambi i lati**, mentre football-data
conta 3+6 tiri in porta. La fonte non ha mai acquisito la partita e ha scritto
valori di comodo: xG = gol esatti, npxG = gol meno un rigore forfettario, `ppda`
`att=0 def=0`, `deep` 0, previsione degenere 0/1/0.

Le celle sono ora **`NaN` dichiarato**, e `understat._e_segnaposto` intercetta il
caso in ingresso richiedendo **tutte** le firme insieme — così su 16.110 partite
accende una riga sola e lascia intatte le tre partite davvero sterili con
`deep = 0`.

Cercato con **nove firme indipendenti** (xG intero uguale ai gol, cifre povere,
forecast degenere, ppda nulla, deep zero, xPts intero, rigore finto, history
mancante, xG zero con tiri) su tutte le 16.110 partite: **una sola riga**
positiva, che ne accende 7 su 9. Prova di potenza con 500 segnaposto piantati
artificialmente: la batteria li riscopre tutti. Limite dichiarato: riscopre i
segnaposto *totali*, non le degradazioni parziali (con xG residuo al 90% ne
riscopre lo 0,2%).

---

## 4-ter · Il registro delle correzioni (`data/correzioni_dichiarate.csv`)

La regola **R3** del CLAUDE.md — *nessuna modifica a mano ai dati, mai* — ha un
solo modo di essere rispettata: ogni cella che differisce dalla fonte deve
esistere in un registro, con il *cosa*, il *perché*, la *fonte*, *chi* ha deciso
e *quando*. Questo file è quel registro; lo applica
`scripts/applica_correzioni.py`, che è **idempotente** e verifica il
`valore_prima` cella per cella prima di scrivere (se non corrisponde, si ferma
senza toccare nulla).

**Contenuto oggi: 43 righe** (contate con `pandas`; erano 31 all'audit della
Fase 101 e 37 nella dichiarazione precedente di questo documento).

| stato | righe | cosa sono |
|---|--:|---|
| `applicata` | **39** | 22 celle O/U di apertura svuotate dal guard bilaterale (11 linee, §1-bis) · 6 celle 1X2 di chiusura inserite da provider secondario (§4) · 6 celle xG/npxG/deep di Holstein Kiel-Bochum portate a `NaN` (record segnaposto, §4-bis) · 3 celle di Union Berlin-Bochum (`home_goals`, `away_goals`, `result`: il risultato del **campo** 1-1, regola R1, non lo 0-2 del tribunale) · 2 celle di Bielefeld-Leverkusen (**ripristino** del valore originale dopo un ritiro, vedi sotto) |
| `ritirata` | **2** | `home_xg` / `home_npxg` di **Bielefeld-Leverkusen 21/11/2020**: una correzione **sbagliata**, tenuta nel registro col motivo. Un xG di 0.00 con un gol segnato sembrava impossibile; il dato tiro-per-tiro (`understat.com/getMatchData/15207`) mostra 0 tiri e un **autogol** del portiere avversario. È il caso da cui nasce la regola R5.1 |
| `proposta` | **2** | `home_sot` / `away_sot` di Union Berlin-Bochum: il dato esiste in Understat ma **non** viene applicato — la definizione di «tiro in porta» non è identica a quella di football-data, e mescolare due definizioni in una cella è peggio di un `NaN` dichiarato. Registrata perché il dato esiste, se un giorno si decidesse di usarlo |

Due letture non ovvie del registro, entrambe volute:

1. **le righe `ritirata` non si cancellano.** Restano con il motivo per esteso,
   altrimenti la sessione successiva rifà lo stesso errore (principio §1.4:
   documenta anche i risultati negativi). Il ripristino del valore originale è
   una riga `applicata` *in più*, non una cancellazione: il registro è un
   giornale, non uno stato.
2. **una riga `proposta` non è una decisione rimandata**: è una decisione presa
   in negativo, scritta nel campo `motivo`. L'unico appunto legittimo — già
   rilevato dall'audit — è che l'etichetta più onesta sarebbe `respinta`.

---

## 5 · ⚠️ STIME dichiarate (`data/estimates/`)

Dove un dato di mercato **non esiste nelle fonti**, il progetto può stimarlo
coi propri modelli — ma la stima vive **fuori dagli snapshot**, in
`data/estimates/`, come **probabilità** (mai quote: impossibile confonderla
con un prezzo). Regole complete in [`data/estimates/README.md`](../data/estimates/README.md);
le tre che contano:

1. **non farci troppo affidamento** — l'errore atteso è misurato e dichiarato;
2. **ogni analisi che le usa lo dichiara** (diario + `runs.jsonl`);
3. **mai** dentro le colonne quota degli snapshot, **mai** per simulare ROI.

### Stime attualmente pubblicate

| file | cosa stima | metodo | errore atteso (validato walk-forward) |
|---|---|---|---|
| `ou_close_2017_19.csv` (**3638 righe, 5 leghe**) | la **chiusura O/U 2.5** delle stagioni 2017-18/2018-19, assente nelle fonti su tutte e cinque le leghe (l'**apertura** O/U di quelle stagioni è invece REALE — `BbAv`, Fase 73 — negli snapshot: `odds_over25_open`) | regressione logit della chiusura su (linea O/U **di apertura** + movimento 1X2 open→close), fit pooled su **12.457** partite 2019-20+ e **5 leghe** (il pooled a 5 batte quello a 3 con CI conclusivo: le due leghe nuove migliorano la stima anche per le tre storiche) | **MAE ~0.014 nel REGIME D'USO**, ~0.012 in interpolazione — e conta il primo: la chiusura O/U del 2017-19 non esiste, quindi i coefficienti vengono per forza da stagioni SUCCESSIVE, e in quel regime l'errore è 15-25% più alto. Corr col movimento vero 0.75-0.86; ~35-45% del movimento resta incatturabile |
| `squad_value_2017_26.csv` (**0 righe** — erano 73 alla Fase 66, 13 alla Fase 67; **svuotato alla Fase 70**: le ultime 13 sostituite da dati REALI Transfermarkt) | ormai nessuna: file mantenuto vuoto e rigenerabile (`build_estimates.py` produce 0 righe se non ci sono buchi) | ibrido validato LOO/leave-team-out (Fase 66), storico se il buco dovesse riaprirsi in futuro | — (nessuna stima attiva) |
| `open_sparse_1x2_ou.csv` (**2 righe**, Fase 69; era 3, −1 alla Fase 73) | l'**apertura** (1X2 e/o O/U) delle partite sparse senza apertura vera, fuori dal buco sistemico O/U 2017-19 | bakeoff (5 metodi, 5-fold CV su 10.258/7.978 coppie reali): vince la regressione in **spazio logit pooled** (chiusura→apertura); nessun blend migliora | **MAE ~0.016** (1X2, 3 esiti) / **~0.020** (O/U) — molto più affidabile della (ex) stima squad_value; rapporto apertura↔chiusura quasi identità (corr 0.96-0.99) |
| `ou_open_corrotte_2017_19.csv` (**12 righe**: 7 Bundesliga + 3 La Liga + 2 Ligue 1) | l'**apertura** O/U 2.5 delle linee svuotate dal guard bilaterale (overround fino a 1.339) e di Bayern-Hoffenheim 24/08/2018, assente alla fonte | bakeoff di 26 varianti, k-fold k=5 sulle partite della stessa epoca con la linea integra (**3.640** oggi; erano 3.643 quando la stima copriva 9 righe): vince `M5g logit~scaletta1xBet+1X2ap` **per-lega**, una regressione che usa anche la **scaletta di chiusura 1xBet** (il metodo storico, solo-1X2 + debias costante, si fermava a 0.0267) | **MAE 0.0143** (0.0197 col miglior metodo che usa la sola informazione di apertura, `M4 logit-bias su (T,D) quad`). ⚠️ Limite specifico: il vincitore usa una quota di **chiusura** per stimare un'**apertura**. ✅ **Le 3 La Liga sono coperte dalla Fase 101-ter**: la stima è stata rigenerata e le bersaglio, che si auto-selezionano, sono passate da 9 a 12, con le 9 preesistenti **identiche a meno di 0.000000** (vedi il riquadro in `data/estimates/README.md`) |
| `celle_residue.csv` (**32 righe**: 6 caso A, 8 B, 8 C, 10 D — conteggio verificato con `value_counts()` sulla colonna `caso`) | niente — è il **registro di NON-stima**: quali celle restano vuote e perché non conviene stimarle (errore sopra soglia, fonte non consolidata, o dato reale disponibile ma da un provider diverso) | per ogni cella: valore proposto, metodo, errore atteso e alternativa, così la sessione successiva non ci riprova da capo | — (non è una stima pubblicata: è la prova che non stimare è la scelta giusta). ⚠️ **Il caso A non è più «non stimare»: è `ESEGUITA alla Fase 101-bis`** — le 6 celle 1X2 di chiusura sono state inserite col dato reale (§4). Casi B e C: `NON STIMABILE → resta NaN dichiarato` (xG/stile: MAE fuori campione 0,45 gol contro una sd di 0,89, l'errore è metà del segnale). Caso D: i «finti pieni», di cui 3 righe chiuse dal guard, 2 lasciate piene e dichiarate (§1-bis) e 5 righe `midweek_europe` **chiudibili senza stima** (236 + 251 + 454 + 180 + 482 = 1.603 celle a zero falso) |

Accesso da codice: `loader.read_ou_close_estimates()`. Rigenerazione: ogni file
dal suo script — `build_estimates.py` per i primi tre,
`stima_ou_open_bakeoff.py` e `stima_celle_residue.py` per gli ultimi due (vedi
[`data/estimates/README.md`](../data/estimates/README.md) §4).

> 📌 **Residuo aperto (piccolo, concreto, verificato alla Fase 101-ter).** La
> stima `ou_close_2017_19.csv` copre **3.638** righe delle **3.652** della
> finestra. Le 14 mancanti sono tutte spiegate — 12 senza la linea O/U di
> *apertura* (l'input della regressione) e **2 che al momento della generazione
> non avevano la chiusura 1X2**: Alaves-Sociedad 14/10/2017 e Bayern-Hannover
> 04/05/2019. Quelle 2 righe **ora la chiusura 1X2 ce l'hanno** (dato reale
> inserito alla Fase 101-bis, §4): rigenerando, la stima passerebbe a **3.640**
> righe. Non è stato fatto in sede di documentazione — rigenerare una stima
> pubblicata vuole il controllo prima/dopo e una riga di registro.

### Candidati FUTURI a stima (promemoria, richiesti dall'utente)

Da valutare **solo** con lo stesso protocollo (backtest di fedeltà su dati
dove la verità esiste → errore atteso dichiarato → pubblicazione separata):

- ~~**`squad_value` mancante**~~ → **CHIUSO CON DATO REALE (Fase 66→70)**: le
  73 celle stimate alla Fase 66 sono scese a 13 con la fonte player-scores
  (Fase 67) e infine a **0** con un recupero manuale diretto da Transfermarkt
  (Fase 70): nessuna stima attiva, `squad_value_2017_26.csv` è vuoto.
- ~~**apertura O/U 2017-19**~~ → **NON era un buco (chiarito Fase 73)**: l'unica
  linea O/U del 2017-19 (`BbAv`) è un'**apertura reale** (pre-match), prima
  erroneamente messa nello slot chiusura. Dalla Fase 73 è nella colonna giusta
  (`odds_over25_open`), dato reale. Resta un buco solo la **chiusura** O/U di
  quelle stagioni (coperta dalla stima `ou_close_2017_19.csv`). La caccia al dato
  vero di chiusura è **CHIUSA dalla Fase 100**, e il documento dedicato si apre
  con la stessa parola: il dato **esiste** (chiusura del book **1xBet** via
  `footiqo.com`, **3.652 partite su 3.652** della finestra, copertura 100% su
  tutte e 10 le coppie lega-stagione, in `data/ricerca_esterna/`) e **non è
  stato inserito**. Il motivo è la parte che conta, ed è una decisione di
  merito, non una rinuncia: gli snapshot dal 2019-20 contengono la **media
  multi-book**, mentre 1xBet è **un solo book**; come proxy di quella media è
  *peggiore della stima che già avevamo* (MAE **0.0156** contro **~0.014** del
  regime d'uso — non 0.012, che è il numero ottimistico "in interpolazione": la
  correzione vale anche qui, non solo nella riga Fase 100 del README) e
  inserirlo creerebbe una **rottura di regime a metà colonna**.
  **Fase 106**: il confronto ripetuto su 6 stagioni (2019-20 → 2024-25, non solo
  una) mostra che il numero **non è stabile nel tempo** — il MAE di footiqo
  varia fra 0.0096 e 0.0192, peggiore nell'era porte-chiuse 2020-22 e migliore
  dal 2022-23 in poi (nelle ultime 2 stagioni batterebbe perfino la stima). Non
  cambia la decisione — il 2019-20 resta il proxy più vicino al 2017-19, e lì la
  stima vince ancora — ma la rende **meno granitica** di come suonava.
  Quello che resta aperto è solo la chiusura O/U 2017-19 **come media
  multi-book**, che non esiste da nessuna parte — e le Fasi 105/107/108 l'hanno
  ricercata altre tre volte, sempre negativo.
  Dettaglio: **[CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md)**.
- ~~**quote O/U/1X2 di apertura mancanti sparse**~~ → **FATTO (Fase 69)**: le
  **2 partite sparse** (Torino-Fiorentina recupero 1X2+O/U; Verona-Genoa O/U
  isolata 2020-21) sono stimate in `open_sparse_1x2_ou.csv` (vedi tabella
  sopra). *(Erano 3: dalla Fase 73 Alaves-Sociedad ha l'apertura 1X2 reale e la
  sua stima è stata ritirata.)* Un tentativo di ricerca esterna diretta
  (BetExplorer/OddsPortal da IP italiano) non ha trovato nulla per il blocco
  geo/ADM — vedi
  `docs/MANUALE_SOPRAVVIVENZA.md`.
- ~~eventuali linee di mercati mai pubblicati (GG/NG storico): molto più
  incerto, servirebbe una validazione esterna.~~ → **validato (Fase 100)**: le
  quote GG/NG di chiusura esistono per il 2017-20 (1xBet, 5.337 partite su 5
  leghe) e il mercato è risultato informativo (log-loss 0.6840 contro 0.6921 di
  baseline). Restano fuori dagli snapshot per la stessa ragione dell'O/U: un
  solo book.

---

## 5-bis · Quote OUTRIGHT di stagione (`data/outright_snapshots/`) — Fase 97

Dati di **mercato reali** (non stime), **versionati**, raccolti in avanti nel
tempo. Sono l'unica cosa in repo che nasce da un fetch LIVE e viene comunque
congelata: senza archivio, i prezzi di oggi sparirebbero col container.

**A cosa servono.** Il simulatore di stagione (Fase 89) non ha mai potuto
dimostrare «battiamo il mercato» perché **non esistono quote outright
storiche** raggiungibili. All'indietro non si rimedia; in avanti sì, una
istantanea alla volta.

| | |
|---|---|
| **fonti** | Polymarket (Gamma API) + **Smarkets** (API v3 pubblica) — entrambe **borse**, non bookmaker |
| **file** | `YYYY-MM-DD.json` (completo) + `history.csv` (formato lungo: data × fonte × lega × mercato × squadra) |
| **mercati** | campione (5 leghe, entrambe le fonti — le **uniche** righe confrontabili fra le due); **retrocessione** (solo Premier) e Top 2/3/4/5/6 + top-half: **solo Smarkets**; qualificazioni europee: **solo Polymarket** (UECL su 4 leghe — non Bundesliga; UCL/UEL solo Ligue 1). **Capocannoniere: mai quotato** da nessuna delle due |
| **si scrive con** | `python scripts/archive_outrights.py` (idempotente sulla data; `--only polymarket\|smarkets`, `--date`, `--from-dump`, `--show`) |
| **stato dell'archivio** | **2 istantanee** (`2026-07-25.json`, `2026-07-26.json`) e **930 righe** in `history.csv` — 465 per data, di cui **211 Polymarket** e **254 Smarkets** (conteggio `pandas`). È un archivio appena nato: cresce solo in avanti |
| **documentazione d'uso** | `data/outright_snapshots/README.md` |

**Tre avvertenze che valgono come semantica del dato** (per estese, il README
della cartella):

1. **`settled_share ≥ 0.9` NON è una previsione**: è la coda di una stagione
   già conclusa. Il 25/07/2026 tutti i mercati «qualify for UEFA …» erano
   riferiti alla stagione **appena finita**, non al 2026-27 (`settled_share`
   0.950 su Serie A, Premier e La Liga). L'**unica** riga dell'archivio con
   `settled_share = 0.000` è la retrocessione Premier di Smarkets.
2. **`exclusive=False` non va rinormalizzato**: qualificazioni, retrocessione e
   Top-N sono binari **indipendenti**; la somma vale legittimamente ~3 o ~4.
   Solo campione e capocannoniere sono a vincitore unico e hanno un `overround`
   — e il **capocannoniere non è mai stato quotato** da nessuna delle due fonti
   nelle istantanee raccolte finora.
3. **`book="partial"` / `price_side="ask_only"`**: il libro ha un lato solo.
   L'`best_ask` è un **tetto** al valore equo, non un prezzo, e `prob` è
   vuota — al 25/07/2026 sono **139 righe Smarkets su 254**. Anche col mid, uno
   **spread largo** lo rende poco significativo: il caso peggiore è
   *Nottingham Forest — retrocessione Premier*, `best_bid` 0.0010 e `best_ask`
   0.100, cioè un «mid 5.05%» con uno spread di 9,9 punti che non vuol dire
   nulla. **Filtrare sullo spread prima di usarlo in un'analisi.**

**Nomi squadra: NON normalizzati.** L'archivio conserva i nomi **grezzi** di
ciascuna fonte («Inter Milan» su Polymarket, «Inter Milano» su Smarkets,
«Inter» da noi). È deliberato: una normalizzazione non validata produrrebbe
join silenziosamente sbagliati, e i nomi sono stringhe stabili che si possono
mappare retroattivamente in qualsiasi momento. L'unica mappa esistente e
verificata a mano è `SMARKETS_TO_OURS` in
`scripts/_run_fase97_relegation_market.py` (Premier, 20 su 20). **Chi aggiunge
una lega deve costruire la sua**, non affidarsi a un match approssimato.

---

## 5-ter · Quote PRE-PARTITA di borsa (`data/smarkets_matches/`) — Fasi 116/118

Dati di **mercato reali** (non stime), **versionati**, raccolti in avanti.
Stessa logica del 5-bis — ciò che non si congela prima del calcio d'inizio è
perso — ma sulla **singola partita** invece che sulla stagione.

**A cosa servono.** Due cose che il progetto non ha mai potuto fare:
(a) il **test prospettico** della Fase 78 (previsioni congelate prima del
fischio, scorate dopo — il gold standard mai eseguito); (b) la **pista C**,
cioè validare contro una quota esterna i ~17 mercati che il progetto prezza e
non ha mai confrontato con nessuno (GG/NG, risultato esatto, multigol,
total-squadra…). Finora l'**unico** mercato del listino validato esternamente
era l'handicap asiatico (Fase 88).

| | |
|---|---|
| **fonte** | **Smarkets** (API v3 pubblica, senza chiave né account) — una **borsa**, non un bookmaker |
| **file** | `YYYY-MM-DDTHH-MM-SS.json`, uno per esecuzione. I **secondi** nel nome non sono un vezzo: i due regimi possono cadere nello stesso minuto e si sovrascriverebbero in silenzio (Fase 118) |
| **granularità riga** | (partita, mercato, contratto) con `p_banco`, `p_puntatore`, `p_mid`, `lato`, `spread`, `vol_banco`, `vol_puntatore` |
| **prezzi** | **PROBABILITÀ 0-1**, mai quote decimali. Sulle coppie complementari il mid somma ~1.003 (overround quasi nullo di una borsa) |
| **mercati** | *denso*: 1X2, GG/NG, O/U 1.5/2.5/3.5, **risultato esatto**. *Lungo raggio*: solo 1X2 + O/U 2.5 + GG/NG (quelli che il motore consuma) |
| **si scrive con** | `python scripts/fetch_smarkets_matches.py` (`--entro-ore`, `--tutte-le-esposte`, `--solo-principali`, `--tutti-i-mercati`, `--dry-run`) |
| **automazione** | `.github/workflows/smarkets-prematch.yml` — **denso** ogni 6 h (entro 72 h dal via), **lungo raggio** 1×/giorno (tutto l'esposto). Piano gratuito, costo €0 |

**I due regimi, e perché sono due.** Misurato il 28/07/2026: Smarkets espone
**una giornata per lega** (~48 partite delle nostre 5). Col solo regime denso
non si sarebbe raccolto **nulla fino al 12 agosto**, mentre il listino
dell'esordio è già quotato e già si muove — 18 giorni di traiettoria
irrecuperabili. Il lungo raggio li prende; esclude il risultato esatto perché
è ~24 righe su 30 per partita, ed è proprio il mercato più sottile lontano dal
via (libro a due lati sul **59%** delle righe a tre settimane, contro l'**85%**
dei principali).

**Avvertenze di semantica** (le stesse tre del 5-bis valgono qui):

1. **`p_mid` può mancare** (`lato` dice perché): a listino sottile un contratto
   può avere un lato solo o nessuno. Al 28/07/2026 sono **49 righe su 336**.
   Sono marcate, **non riempite**: un mid inventato sarebbe un finto pieno (R6).
2. **Con un lato solo il «mid» non è un prezzo**: è un tetto (o un pavimento).
   **Filtrare sullo spread** prima di usare le righe in un'analisi.
3. **Nomi squadra non normalizzati**, come nel 5-bis: l'archivio conserva i
   nomi grezzi di Smarkets («Inter Milano»). Chi farà il join con gli snapshot
   dovrà costruire e **verificare a mano** la sua mappa.

**Controllo di plausibilità (Fase 118).** Il raccoglitore **fallisce** invece
di uscire verde se il listino ricevuto è vuoto, o se non contiene nessuna delle
5 leghe. Senza, «off-season» e «l'API non ci parla più» darebbero lo stesso
esito — zero righe e un workflow verde — e si raccoglierebbe il nulla per mesi.
La soglia è misurata: il 28/07, nel giorno più vuoto dell'anno, il listino
aveva **709 eventi calcio su 101 competizioni** con tutte e 5 le nostre
presenti (9-10 partite ciascuna).

**Costo dell'archivio, dichiarato.** 454 byte per riga misurati. Il lungo
raggio vale ~149 KB/giorno (~45 MB a stagione); il **denso in-season** è la
voce pesante e porta il totale nell'ordine dei **250-300 MB** versionati per
stagione. È una cifra da **decidere** (leve: frequenza del cron, esclusione del
risultato esatto anche dal denso), non da subire.

---

## 5-quater · Stagione 2026-27, raccolta quotidiana (`data/stagione_2026_2027/`) — Fasi 119/120

Cartella **nuova**, con una sua specifica completa: **`data/stagione_2026_2027/README.md`**.
Qui solo ciò che serve al catalogo; per il *perché* e la lista dei dati, quel file.

| | |
|---|---|
| **cos'è** | raccolta **prospettica** per la stagione 2026-27: anagrafica di partenza + stato quotidiano |
| **assi** | `giornaliero/` (append-only, **immutabile**: «cosa sapevamo il giorno D») e `club/<PAESE>/<slug>/` (identità stabile + viste rigenerabili) |
| **stato** | anagrafica delle **96 squadre** scritta (Fase 120); il livello giornaliero è **specificato, non ancora implementato** |
| **si scrive con** | `python scripts/build_stagione_anagrafica.py` |
| **fonti** | elenco iscritte da `data/smarkets_matches/`; attributi da `davidcariboo/player-scores` (Kaggle, **CC0**) |

**⚠️ Tre avvertenze che sono semantica del dato, non note a margine.**

1. **I valori di mercato sono PROVVISORI.** Fotografia del **27/02/2026**: non
   contengono il mercato estivo 2026. Ogni file porta `provvisorio: true` e
   `data_valore`. Vanno sostituiti appena esiste il dato di agosto (decisione
   dell'utente, 28/07/2026).
2. **`copertura` va letta prima di ogni altro campo**: `completa` (82 squadre),
   `stantia` (10 — record fermo all'ultima stagione in massima serie, es.
   Málaga 2017) o `assente` (4 — mai in prima divisione nel periodo coperto:
   Elversberg, Coventry, Racing Santander, Le Mans). I buchi sono **tutti
   neopromosse**, cioè proprio le squadre su cui il modello applica il prior δ.
3. **`valore_rosa_eur` è `null` quando la rosa non è completa**, e non è
   pigrizia: sulle squadre stantie il residuo è di 1-8 giocatori su ~30, e
   sommarli dava **«Frosinone 0.8 M€» su 1 giocatore di 31** — un errore di tre
   ordini di grandezza, sempre con lo stesso segno. Non è una stima imprecisa,
   è **un'altra quantità** (R6). Stessa logica per `rosa_n`, che sta accanto a
   `squad_size_ufficiale` e **non** lo sostituisce (scarto mediano +6).

**Nomi squadra: alias espliciti, mai match approssimato.** Ogni
`anagrafica.json` porta `alias` con il nome di ciascuna fonte. I 21 casi che la
normalizzazione non risolve sono in `ALIAS` dentro lo script, **verificati a
mano uno per uno**: le regole stanno in `data/stagione_2026_2027/club/README.md`.

**Rose vere (Fase 121): `rosa_wikipedia.json` accanto all'anagrafica.**
`scripts/fetch_rose_wikipedia.py` scrive, per i club coperti, la rosa da
it.wikipedia (CC BY-SA, API ufficiale). Serve perché il dataset CC0 è fermo a
**febbraio** e non conosce il mercato estivo.

- `rosa_prima_squadra_n` conta i giocatori **col numero di maglia**;
  `rosa_n` include i **giovani aggregati** (che nella fonte hanno `n=` vuoto).
  Sono due quantità diverse e vanno usate come tali: al Napoli 26 e 47.
- `aggiornata_al_dichiarato` è la data che **la voce dichiara**, non quella del
  nostro scarico: è quella che dice se il dato è fresco.
- **Copertura misurata: 41/96** (Serie A 18/20, Premier 12/20, La Liga 6/20,
  Ligue 1 3/18, Bundesliga 2/18). Le altre 55 richiedono le Wikipedia locali.
  Dove il file non c'è, **non c'è**: nessuna rosa stimata.

**Giornaliero (Fase 122): `giornaliero/AAAA-MM-GG/`.**
`raccolta.json` (record con `tipo`, `fonte`, `raccolto_utc`) e `fonti.json`
(**ogni** fetch tentato, anche fallito). Il meteo di una partita oltre i **16
giorni** di orizzonte è `fuori_orizzonte`, che è un non-evento dichiarato e non
un buco. Coordinate degli stadi in `_anagrafica/stadi.json` (90 su 94).

---

## 6 · Come si rigenera tutto (riproducibilità)

Le tre famiglie di leghe hanno **tre percorsi diversi**, per ragioni storiche
(§4): la Serie A da grezzi congelati, Premier/Liga dai bundle, Bundesliga/Ligue 1
dalla rete. Lo *schema d'arrivo* è però lo stesso per tutte e cinque.

```bash
# Serie A — grezzi congelati in repo
python scripts/_restore_raw_cache.py          # data/football_data_raw/ -> data/raw/
python scripts/build_database.py              # DB dallo snapshot (offline)
python scripts/build_database.py --refresh-odds   # ricalcola le 10 colonne quota
python scripts/build_database.py --fixtures   # calendario club + congestione
python scripts/build_database.py --enrich     # xG/rose/assenze (rete: TM)

# Premier League / La Liga — dai bundle in files/ (offline salvo dove indicato)
python scripts/build_league_snapshot.py                    # snapshot base
python scripts/build_league_snapshot.py --refresh-odds     # quote
python scripts/build_league_snapshot.py --fixtures         # congestione (rete: openfootball)
python scripts/build_league_snapshot.py --enrich           # rose/assenze (rete: TM)

# Bundesliga / Ligue 1 — nessun bundle: le fonti si riscaricano (RETE richiesta)
python scripts/fetch_sources.py --leagues bundesliga ligue_1   # -> data/fonti/ + manifest SHA256
python scripts/build_new_snapshot.py                           # snapshot 38 colonne + calendari
python scripts/build_new_snapshot.py --leagues bundesliga      # una sola lega
python scripts/build_new_snapshot.py --step core               # solo base + xG

# Correzioni dichiarate (§4-ter) — SEMPRE dopo aver rigenerato uno snapshot
python scripts/applica_correzioni.py --dry-run   # mostra cosa cambierebbe
python scripts/applica_correzioni.py             # applica (idempotente, R3)

# Stime dichiarate
python scripts/build_estimates.py             # data/estimates/ (offline)
python scripts/stima_ou_open_bakeoff.py       # ou_open_corrotte_2017_19.csv (richiede scikit-learn)
python scripts/stima_celle_residue.py         # celle_residue.csv

# Mercati outright (§5-bis) — fetch LIVE, va rifatto in avanti, non all'indietro
python scripts/archive_outrights.py           # data/outright_snapshots/ (rete)
```

⚠️ **`applica_correzioni.py` non è opzionale.** Uno snapshot rigenerato dalla
fonte *senza* passare dal registro perde le 39 correzioni applicate — fra cui il
risultato di campo di Union Berlin-Bochum (R1) e le 6 celle 1X2 di chiusura. Lo
script verifica il `valore_prima` cella per cella e si ferma se non corrisponde,
quindi eseguirlo due volte è innocuo; **non** eseguirlo non lo è.

Ogni backtest/analisi è registrato in `experiments/runs.jsonl` con l'impronta
dei dati usati; le decisioni e il perché sono nel [diario](DIARIO.md).

Conoscenza operativa sull'ambiente (rete, strumenti, GitHub Actions) in
[MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md); idee di miglioramento
dei modelli dai dati disponibili-ma-non-usati in [PISTE.md](PISTE.md).
