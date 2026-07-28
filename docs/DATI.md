# Catalogo dei dati — tutto ciò che il progetto ha a disposizione

Questo documento è la **mappa unica di tutti i dati** del progetto: cosa c'è,
da dove viene, quanto copre, e — sezione più importante — **cosa è dato reale e
cosa è STIMA**. Va aggiornato ogni volta che i dati cambiano (nuova fonte,
nuova colonna, nuova stima). Ultimo aggiornamento: **Fase 100** (5 leghe).

> ⚠️ **Allineamento — stato dopo l'audit della Fase 101.** I buchi dichiarati in
> questo banner sono stati colmati: `data/ricerca_esterna/` (86 file) è ora in
> §4, i 5 calendari di club in §3, le 5 stime in §5, e il censimento dei buchi
> (§1-bis) è ricalcolato **dopo** il guard (7.359, non 7.353). **Resta fuori**
> `data/correzioni_dichiarate.csv` (37 righe, registro R3), che non ha una
> scheda propria: è citato dove serve (§1-bis, §4-bis) ma andrebbe descritto una
> volta sola. Elenco puntuale in `docs/AUDIT_FASI_80_100.md` §4.

> Regola d'oro del progetto: **mai un numero inventato spacciato per dato**.
> Dove un dato manca, o resta `NaN` (dichiarato), oppure viene stimato e
> pubblicato **separatamente** con l'etichetta di stima (vedi [§5](#5--stime-dichiarate-dataestimates)).

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
| tiri in porta | `home_sot, away_sot` | football-data | 100% |
| **quote chiusura** | `odds_home/draw/away, odds_over25/under25` | football-data (vedi §2) | 1X2: ~100% (−2 righe dichiarate: Alaves-Sociedad 14/10/2017 e Bayern-Hannover 04/05/2019, entrambe senza `PSC*` alla fonte) · O/U: ~77% (**chiusura assente nel 2017-19 su tutte e 5 le leghe**, vedi §5) |
| **quote apertura** | `odds_*_open` (5 colonne) | football-data (vedi §2) | 1X2: ~100% · O/U: ~100% (dalla Fase 73 l'apertura O/U 2017-19 è reale, `BbAv`) |
| xG | `home/away_xg, home/away_npxg` | Understat | 100% meno **2 partite dichiarate**: Nantes-Toulouse 17/05/2026 (Ligue 1, `isResult=false`) e Holstein Kiel-Bochum 09/02/2025 (Bundesliga, **record segnaposto**: vedi §4-bis) |
| stile | `home/away_ppda, home/away_deep` | Understat | come sopra |
| valore rosa | `home/away_squad_value` | **player-scores** (Transfermarkt via Kaggle, Fase 67) + **29** celle 2025-26 da Transfermarkt diretto (13 alla Fase 70 sulle 3 leghe storiche + 16 all'audit delle 5 leghe — 5 Bundesliga, 11 Ligue 1, in `data/squad_value_2526_transfermarkt.csv`, regola R2; vedi §4) | **100% su TUTTE le stagioni, incluse la 2025-26** — zero NaN residui |
| assenze (STIMA, suffisso `_est`) | `home/away_absent_count_est, home/away_absent_value_est` | Transfermarkt + rose Understat | 100% (ma è una **stima dichiarata**, vedi §4) |
| congestione | `home/away_rest_days_full, home/away_midweek_europe` | openfootball + snapshot | **100%** (Fase 68: gli esordi sono radicati coi calendari 'preludio' — massima serie 2016-17 + seconde serie) |

---

## 1-bis · I buchi, tutti quanti — e quelli che non sembrano buchi

Censimento completo (ricalcolato all'audit della Fase 101, **dopo** il guard
bilaterale: era 7.353 prima): **7.359 celle vuote su 612.218**, cioè l'1,20%. Ma
il numero da solo inganna: il **99,25%** è **un buco solo**, la chiusura O/U del
2017-19 (7.304 celle), che non esiste alla fonte per nessuna delle cinque leghe
(§5). Tolto quello restano **55 celle**, ognuna con un nome e una causa:

| cosa | dove | perché |
|---|---|---|
| 11 linee O/U di apertura = **22 celle** | 3 La Liga, 6 Bundesliga, 2 Ligue 1 (2017-19) | overround impossibile alla fonte (fino a 1.339): svuotate dal guard bilaterale di `loader._pick_market_odds` |
| 1 linea O/U di apertura = **2 celle** | Bayern-Hoffenheim 24/08/2018 | assente alla fonte |
| 2 terne 1X2 di chiusura = **6 celle** | Alaves-Sociedad, Bayern-Hannover | colonne `PSC*` vuote nel grezzo — un dato REALE esterno esiste (github.com/iredchuk/soccer-bookmaker-odds, chiusura media-di-mercato: 3.40/3.34/2.15 e 1.03/18.43/43.88, MAE 0.0060 contro 0.0160 della stima) ed è **registrato ma NON inserito**, perché viene da un provider diverso dal resto della colonna. Verdetto e numeri in `data/estimates/celle_residue.csv` (caso A) |
| 7 celle quota | Torino-Fiorentina 10/01/2022 (5: O/U + 1X2 di apertura), Verona-Genoa 19/10/2020 (2: O/U di apertura) | partite rinviate, quote mai aperte |
| 16 celle xG/stile | 2 partite (vedi §1), 8 colonne ciascuna | fonte non consolidata / record segnaposto |
| 2 celle tiri in porta | Union Berlin-Bochum 14/12/2024 | statistiche assenti alla fonte |

*(22 + 2 + 6 + 7 + 16 + 2 = 55, cioè esattamente 7.359 − 7.304.)*

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
- **i conteggi tiri di football-data non sono confrontabili fra stagioni**: in
  Serie A la somma passa da 5.359 (2017-18) a 4.269 (2018-19) e torna a 5.326
  (2021-22), con tutte le righe popolate. Non è un buco: è un cambio di raccolta
  a monte. Poco rilevante oggi (il blend usa l'xG, non i tiri), ma va saputo.

---

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
- **Un'eccezione 1X2 (Fase 73):** La Liga **Alaves-Sociedad 14/10/2017** non ha
  la chiusura Pinnacle (`PSC*` vuote nel grezzo, unico caso su 2.280): dalla
  Fase 73 la sua chiusura 1X2 resta NaN (niente più fallback pre-match) e
  l'apertura reale `PS*` è ora valorizzata. La stima di apertura 1X2 della Fase
  69 per questa riga è stata **ritirata** (l'apertura reale c'è).
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
| football-data (Serie A, CSV originali completi) | `data/football_data_raw/` (versionata) | ✅ congelata; il sito originale **è tornato raggiungibile** (200, verificato alla Fase 100: le due leghe nuove sono state scaricate direttamente) |
| football-data (Premier/Liga) | `files/football_data_*_bundle.json` (caricati a mano, Fase 54) | ✅ congelata |
| Understat (xG + rose giocatori) | `files/understat_*_bundle.json` (Premier/Liga); Serie A: **solo lo snapshot** | ⚠️ il mirror per-stagione è **sparito** (Fase 14): le rose Serie A NON sono rigenerabili — `--enrich`/ri-matching valgono solo per Premier/Liga finché non viene caricato un bundle Understat Serie A (come Fase 54) |
| **player-scores** (valutazioni complete + presenze/rose, 5 leghe) | `files/player_scores/*.csv.gz` (versionati; import via **workflow GitHub Actions** `.github/workflows/import_dataset.yml` — il runner ha rete libera, l'ambiente cloud no) | ✅ fonte UFFICIALE dei valori rosa dalla Fase 67 (CC0, `dcaribou/transfermarkt-datasets`); rigenerabile: push di `.github/import-dataset-trigger` |
| Transfermarkt (datalake `salimt`) | mirror GitHub, cache `data/raw/` (~106 MB, non versionata) | ✅ raggiungibile; dalla Fase 67 usato SOLO per gli infortuni (`absent_*_est`) — per i valori rosa e' superato da player-scores |
| Transfermarkt diretto (pagine di competizione per stagione) | recupero MANUALE (Fase 70 e audit delle 5 leghe), non rigenerabile da script: `transfermarkt.com/.it/.us` **era** bloccato dal proxy quando il recupero è stato fatto e oggi **risponde 200** (verificato alla Fase 100, vedi il banner di `docs/MANUALE_SOPRAVVIVENZA.md`); il recupero resta manuale perché la pagina utile è quella di competizione filtrata per stagione | ✅ usato per **29** celle `squad_value` 2025-26 sotto soglia (13 + 16; le 16 con la scala misurata contro player-scores nella colonna `rapporto_TM_su_playerscores_mediano_lega` di `data/squad_value_2526_transfermarkt.csv`, regola R2); **non** la pagina profilo club (mostra il valore LIVE di oggi) ma `.../{lega}/startseite/wettbewerb/{codice}/saison_id/{anno}` (tabella per-club di quella stagione) |
| openfootball (coppe/Europa) | cache `data/raw/fixtures_*` | ✅ raggiungibile |
| **1xBet via `footiqo.com`** (quote di CHIUSURA 1X2 + O/U + GG/NG, 2017-20, 5 leghe) | `data/ricerca_esterna/footiqo_*.json` (18 file) + `footiqo_gol_*.json` (10) + manifest e validazioni | ✅ dato esterno REALE, **NON integrato** negli snapshot: è un solo book, e come proxy della media multi-book è peggiore della stima (MAE 0.0156 contro 0.012) — vedi [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md) |
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
> `data/correzioni_dichiarate.csv` con `stato = applicata`: portarle a
> `ritirata` e rigenerare gli snapshot rimette il `NaN`. Il verdetto originale
> e le misure che l'hanno motivato restano in
> `data/estimates/celle_residue.csv` (caso A) e in
> `docs/audit_5_leghe/numeri/caccia_quote_singole.md` §3.5.

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
| `ou_open_corrotte_2017_19.csv` (**12 righe**: 7 Bundesliga + 3 La Liga + 2 Ligue 1) | l'**apertura** O/U 2.5 delle linee svuotate dal guard bilaterale (overround fino a 1.339) e di Bayern-Hoffenheim 24/08/2018, assente alla fonte | bakeoff di 26 varianti, k-fold k=5 su 3.643 partite della stessa epoca con la linea integra: vince una regressione che usa anche la **scaletta di chiusura 1xBet** (il metodo storico, solo-1X2 + debias costante, si fermava a 0.0267) | **MAE 0.0143** (0.0197 col miglior metodo che usa la sola informazione di apertura). ⚠️ Limite specifico: il vincitore usa una quota di **chiusura** per stimare un'**apertura**. ✅ **Le 3 La Liga sono coperte dalla Fase 101-bis**: la stima è stata rigenerata e le bersaglio, che si auto-selezionano, sono passate da 9 a 12. Le 9 righe preesistenti sono risultate **identiche a meno di 0.000000** — il fit non cambia, perché l'insieme di valutazione (3.640 partite con la linea integra) è lo stesso: sono state aggiunte 3 righe, non ri-stimate le vecchie |
| `celle_residue.csv` (**32 righe**: 6 caso A, 8 B, 8 C, 10 D) | niente — è il **registro di NON-stima**: quali celle restano vuote e perché non conviene stimarle (errore sopra soglia, fonte non consolidata, o dato reale disponibile ma da un provider diverso) | per ogni cella: valore proposto, metodo, errore atteso e alternativa, così la sessione successiva non ci riprova da capo | — (non è una stima pubblicata: è la prova che non stimare è la scelta giusta) |

Accesso da codice: `loader.read_ou_close_estimates()`. Rigenerazione: ogni file
dal suo script — `build_estimates.py` per i primi tre,
`stima_ou_open_bakeoff.py` e `stima_celle_residue.py` per gli ultimi due (vedi
[`data/estimates/README.md`](../data/estimates/README.md) §4).

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
  quelle stagioni (coperta dalla stima `ou_close_2017_19.csv`); la caccia al
  dato vero di chiusura è **CHIUSA dalla Fase 100** → il dato esiste (book 1xBet
  via footiqo, 3.652/3.652 partite, in `data/ricerca_esterna/`) ma **non è stato
  inserito**: è un solo book e come proxy della media multi-book è peggiore
  della stima (MAE 0.0156 contro 0.012). Dettaglio:
  **[CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md)**.
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
| **mercati** | campione (5 leghe, entrambe le fonti); **retrocessione** e Top 2/3/4/5/6 + top-half (**solo Smarkets**); qualificazioni europee (solo Polymarket) |
| **si scrive con** | `python scripts/archive_outrights.py` (idempotente sulla data) |
| **documentazione d'uso** | `data/outright_snapshots/README.md` |

**Tre avvertenze che valgono come semantica del dato** (per estese, il README
della cartella):

1. **`settled_share ≥ 0.9` NON è una previsione**: è la coda di una stagione
   già conclusa. Il 25/07/2026 tutti i mercati «qualify for UEFA …» erano
   riferiti alla stagione **appena finita**, non al 2026-27.
2. **`exclusive=False` non va rinormalizzato**: retrocessione e Top-N sono
   binari **indipendenti**; la somma vale legittimamente ~3 o ~4. Solo campione
   e capocannoniere sono a vincitore unico e hanno un `overround`.
3. **`book="partial"` / `price_side="ask_only"`**: il libro ha un lato solo.
   L'`best_ask` è un **tetto** al valore equo, non un prezzo, e `prob` è
   vuota. Anche col mid, uno **spread largo** lo rende poco significativo
   (visto: bid 0.1% / ask 10.0% → «mid 5.05%» che non vuol dire nulla):
   filtrare sullo spread prima di usarlo in un'analisi.

**Nomi squadra: NON normalizzati.** L'archivio conserva i nomi **grezzi** di
ciascuna fonte («Inter Milan» su Polymarket, «Inter Milano» su Smarkets,
«Inter» da noi). È deliberato: una normalizzazione non validata produrrebbe
join silenziosamente sbagliati, e i nomi sono stringhe stabili che si possono
mappare retroattivamente in qualsiasi momento. L'unica mappa esistente e
verificata a mano è `SMARKETS_TO_OURS` in
`scripts/_run_fase97_relegation_market.py` (Premier, 20 su 20). **Chi aggiunge
una lega deve costruire la sua**, non affidarsi a un match approssimato.

---

## 6 · Come si rigenera tutto (riproducibilità)

```bash
# Serie A
python scripts/_restore_raw_cache.py          # data/football_data_raw/ -> data/raw/
python scripts/build_database.py              # DB dallo snapshot (offline)
python scripts/build_database.py --refresh-odds   # ricalcola le 10 colonne quota
python scripts/build_database.py --fixtures   # calendario club + congestione
python scripts/build_database.py --enrich     # xG/rose/assenze (rete: TM)

# Premier League / La Liga (dai bundle in files/, offline salvo dove indicato)
python scripts/build_league_snapshot.py                    # snapshot base
python scripts/build_league_snapshot.py --refresh-odds     # quote
python scripts/build_league_snapshot.py --fixtures         # congestione (rete: openfootball)
python scripts/build_league_snapshot.py --enrich           # rose/assenze (rete: TM)

# Stime dichiarate
python scripts/build_estimates.py             # data/estimates/ (offline)
```

Ogni backtest/analisi è registrato in `experiments/runs.jsonl` con l'impronta
dei dati usati; le decisioni e il perché sono nel [diario](DIARIO.md).

Conoscenza operativa sull'ambiente (rete, strumenti, GitHub Actions) in
[MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md); idee di miglioramento
dei modelli dai dati disponibili-ma-non-usati in [PISTE.md](PISTE.md).
