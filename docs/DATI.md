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
>
> ⚠️ **Ri-contato di nuovo alla Fase 137**, perché i gol all'intervallo (Fase
> 133) hanno portato lo schema da 38 a **40 colonne**: 16.111 × 40 =
> **644.440 celle** e **7.355 NaN**, di cui 7.304 sono sempre la chiusura O/U
> 2017-19. I due NaN in più sono le due celle di intervallo dell'unica partita
> che non le ha (Union Berlin-Bochum), quindi le residue non-O/U passano da 49
> a **51**. Sono i numeri validi oggi; quelli del capoverso sopra restano come
> traccia di come ci si è arrivati.

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
squadra canonicalizzati via `sources.TEAM_ALIASES` (**265** alias, di cui 104 per
le due leghe nuove, verificati per identità). Gli ultimi **9** sono quelli di
**Smarkets** (Fase 128, passo P1 del test prospettico): la borsa da cui arrivano
quote e fixture 2026-27 scrive `Köln`, `Málaga`, `PSG`, `Man Utd`,
`Nottm Forest`, `Troyes AC` — e i nomi delle **5 esordienti** (Elversberg,
Santander, Le Mans, più Coventry e Hull che combaciano già) sono stati **letti
dai file di seconda divisione dello stesso provider**, non dedotti (R5).
⚠️ Vanno **riverificati** al primo file 2627 vero: se football-data usasse una
grafia diversa da quella dei suoi file di seconda divisione, il join dei
risultati salterebbe in silenzio.

⚠️ **Gli alias di Smarkets sono DOPPI, e apposta** (Fase 130). Fra il 30 e il
31/07/2026 la borsa ha rinominato **40 eventi su 49**, passando dai nomi
formali (`AS Roma vs ACF Fiorentina`) a quelli brevi (`Roma vs Fiorentina`).
`TEAM_ALIASES` copre **entrambe** le convenzioni: inseguire l'ultima
significherebbe accorgersi del cambio la volta in cui è troppo tardi — e il
momento in cui il join deve funzionare è l'ora prima del calcio d'inizio.
La chiave **stabile** resta però `event_id`, non il nome: gli alias sono la
seconda linea. Un test (`test_ogni_nome_mai_visto_nell_archivio_si_aggancia`)
enumera **tutti** i nomi mai comparsi nell'archivio a ogni esecuzione della
suite, così il prossimo rinominamento rompe i test e non la raccolta.


### Le 40 colonne, per gruppo

> 🆕 **Fase 133**: aggiunte `home_goals_ht` e `away_goals_ht` — i **gol
> all'intervallo**, presi da `HTHG/HTAG` di football-data (la stessa fonte dei
> gol finali). Coprono **16.111/16.111** partite con un'unica eccezione
> dichiarata: **Union Berlin-Bochum 14/12/2024**, dove la fonte non ha
> l'intervallo (è la partita del caso R1) e la cella resta **vuota** invece di
> essere inventata. Dtype `Int64` nullable. Servono alla pista 6-bis (modello a
> due stadi): sono `post`, quindi mai usabili per prevedere la partita che li ha
> prodotti — la loro forma d'uso è come **stato** del secondo tempo, non come
> feature del primo.
>
> 🔧 **Fase 137**: nascono ora dentro `loader._normalize`, cioè nella pipeline
> di produzione, e non più solo da `scripts/aggiungi_gol_intervallo.py`. Alla
> Fase 133 le due colonne erano state scritte sugli snapshot **già fatti**:
> corretto una volta sola, perché il ramo `build_database.py --refresh`
> ricostruisce lo snapshot da zero e le avrebbe **cancellate**, riportando la
> lega a 38 colonne senza che nulla protestasse (nessun modulo sotto `src/` le
> nominava). Verificato che il percorso nuovo riproduce quello vecchio:
> **32.222/32.222 celle identiche** sulle 5 leghe, dtype compreso.

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
| assenze (STIMA, suffisso `_est`) | `home/away_absent_count_est, home/away_absent_value_est` | Transfermarkt + rose Understat | 100% di celle piene fino al 2024-25 (è una **stima dichiarata**, vedi §4) · ⚠️ **2025-26: piena ma VUOTA** — la fonte infortuni è congelata a settembre 2025, quindi da ottobre il valore è `0.0` = "non lo so", non "nessun assente". **Non usarla come covariata su quella stagione**: vedi §4-quater |
| congestione | `home/away_rest_days_full, home/away_midweek_europe` | openfootball + snapshot | **100%** (Fase 68: gli esordi sono radicati coi calendari 'preludio' — massima serie 2016-17 + seconde serie) |

---

## 1-bis · I buchi, tutti quanti — e quelli che non sembrano buchi

Censimento completo, ri-contato sugli snapshot di HEAD (Fase 101-ter, ricalcolato
alla Fase 104 e di nuovo alla **Fase 137** dopo l'arrivo delle due colonne di
intervallo): **7.355 celle vuote su 644.440** (16.111 × **40** colonne), cioè
l'**1,14%** (1,1413% esatto). Ma il numero da solo inganna: il **99,3%** è **un
buco solo**, la chiusura O/U del 2017-19 (7.304 celle = 3.652 partite × 2
colonne), che non esiste alla fonte per nessuna delle cinque leghe (§5). Tolto
quello restano **51 celle**, ognuna con un nome e una causa:

| cosa | dove | perché |
|---|---|---|
| 11 linee O/U di apertura = **22 celle** | 3 La Liga, 6 Bundesliga, 2 Ligue 1 (2017-19) | overround impossibile alla fonte (fino a 1.339): svuotate dal guard bilaterale di `loader._pick_market_odds`. **Tutte e 11 hanno una stima dichiarata** in `data/estimates/ou_open_corrotte_2017_19.csv` dalla Fase 101-ter (le 3 La Liga erano rimaste indietro perché il guard le ha svuotate DOPO la produzione della stima: chiuso) |
| 1 linea O/U di apertura = **2 celle** | Bayern-Hoffenheim 24/08/2018 | assente alla fonte; coperta dalla stessa stima |
| 7 celle quota | Torino-Fiorentina 10/01/2022 (5: O/U + 1X2 di apertura), Verona-Genoa 19/10/2020 (2: O/U di apertura) | partite rinviate, quote mai aperte. Ri-verificato Fase 104 scaricando di nuovo i CSV grezzi live da football-data.co.uk: TUTTE le colonne di chiusura (`*C`) sono piene, tutte le colonne di apertura sono NaN — non un dato mancante per errore, è che il mercato ha aperto dopo il cutoff di raccolta di football-data per il recupero |
| 16 celle xG/stile | 2 partite (vedi §1), 8 colonne ciascuna | fonte non consolidata / record segnaposto. Ri-verificato Fase 104 (vedi `docs/MANUALE_SOPRAVVIVENZA.md`: il mirror Understat era morto, corretto l'endpoint ufficiale) con un download LIVE: Holstein Kiel-Bochum ha ancora il record segnaposto identico, Nantes-Toulouse è ancora `isResult=False` su Understat a oltre due mesi dalla partita — nessuno dei due si è risolto col tempo |
| 2 celle tiri in porta | Union Berlin-Bochum 14/12/2024 | statistiche assenti alla fonte. Ri-verificato Fase 104 con un download live del CSV grezzo football-data: colonne HST/AST ancora vuote |
| **2 celle gol all'intervallo** | Union Berlin-Bochum 14/12/2024 | la **stessa** partita, e per la stessa ragione: è il caso R1 (sospesa al 78', **1-1 sul campo**, **0-2 assegnato** dal tribunale sportivo). football-data ne registra il verdetto in `FTHG`/`FTAG` ma lascia `HTHG`/`HTAG` in bianco, perché un intervallo di una partita mai finita non è un risultato. Restano `<NA>` dichiarati (Fase 133; nate in `loader._normalize` dalla Fase 137) |

*(22 + 2 + 7 + 16 + 2 + 2 = 51, cioè esattamente 7.355 − 7.304.)*

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

> ⚠️ **Attenzione a non scambiare l'accordo fra fonti per una conferma.**
> Un secondo controllo (30/07/2026, contro **openfootball**, CC0) ha mostrato
> che openfootball e `games.csv` **concordano fra loro al 100%** — comprese
> queste due partite, dove **entrambe riportano il verdetto del tribunale**.
> Non sono quindi una verifica indipendente della regola R1: **il nostro
> snapshot è l'unico dei tre a portare il risultato del campo**. È una scelta
> consapevole del progetto, non un disallineamento da sanare.

### Altre due anomalie trovate confrontando con openfootball (30/07/2026)

**1. Nantes-Toulouse, 17/05/2026 (Ligue 1 2025-26) — ✅ RISOLTA (31/07/2026):
il nostro 0-0 è REALE e CORRETTO, non un "finto pieno".** La riga era stata
lasciata aperta il 30/07 perché quattro fonti interne concordavano solo sul
fatto che qualcosa non tornava, senza dire cosa fosse successo davvero. Una
ricerca su fonti di stampa esterne (Goal.com, Yahoo Sports, TribalFootball,
Flashscore, *Le Journal Toulousain*, `centpourcent.com`, sito ufficiale LFP)
ricostruisce i fatti:

- la partita — ultima giornata, Nantes già retrocesso, Toulouse senza
  obiettivi di classifica — è stata **interrotta definitivamente al 22'**
  sullo 0-0, dopo un'invasione di campo con fumogeni dei tifosi del Nantes in
  protesta per la retrocessione (arbitro Stéphanie Frappart, decisione presa
  dal prefetto per motivi di sicurezza);
- la **Commissione Disciplinare della LFP ha omologato il risultato di
  0-0** il 27/05/2026 — cioè il punteggio al momento dell'interruzione,
  **esattamente lo stesso meccanismo** del caso Montpellier-Saint-Étienne qui
  sopra (regola **R1**: il campo, non il tribunale) — con sanzioni a carico
  del Nantes (una gara a porte chiuse + due turni di chiusura della curva
  Loire), non sul risultato.

**Quindi il nostro 0-0 è la regola R1 che funziona una terza volta**, non
un'anomalia da correggere. E questo spiega anche le altre tre osservazioni,
che sembravano indizi di corruzione ed erano invece la conseguenza naturale
di una partita durata 22 minuti anziché 90:

| fonte | cosa diceva (30/07) | perché è coerente, non sospetto |
|---|---|---|
| openfootball | `[cancelled]`, senza risultato | openfootball marca "cancelled" ogni gara non arrivata a fine regolare — non distingue un rinvio da un'interruzione a punteggio omologato |
| football-data | 0-0 con 2+2 tiri, 3+5 falli, 2+2 corner, 0 cartellini | erano etichettate "impossibili per 90′" **sotto l'assunzione sbagliata** che la gara fosse durata 90′: per **22 minuti** di gioco sono numeri del tutto plausibili |
| Understat | nessun xG (`isResult=False`) | Understat non processa le gare interrotte anzitempo — coerente con la classificazione già esistente in questo file (riga "xG", §1) come dato mancante dichiarato, non un errore |
| dataset Kaggle | zero presenze/eventi/formazioni | stesso motivo: il pipeline di raccolta esclude le gare non completate |

**Nessuna correzione ai dati**: il valore in snapshot (0-0) resta quello
giusto. L'unico intervento fatto qui è la ricerca esterna che chiude la
domanda lasciata aperta il 30/07 — chiusa per regola **R4** (anomalia
dichiarata anche quando non è un errore), non per regola R6.

**2. Montpellier-Saint-Étienne, 16/03/2025 (Ligue 1) — anomalia SENZA errore.**
Sospesa all'88′ per incidenti e assegnata **0-2**: openfootball la marca
`[awarded]`. Qui però il risultato assegnato **coincide con quello del campo al
momento della sospensione**, quindi non c'è nulla da correggere e il nostro dato
è giusto. Dichiarata per la regola **R4** (un'anomalia si scrive anche quando
non è un errore). L'inventario completo dei marcatori di openfootball sui 45
file di campionato è esattamente **3 `[awarded]` e 102 `[cancelled]`**.

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

> ### ⚠️ DECISIONE APERTA (31/07/2026): la catena della licenza su Transfermarkt
>
> **Non è un fatto già deciso: è una domanda da portare all'utente.** Emersa dalla
> caccia all'event data (`docs/CACCIA_EVENT_DATA.md` §3) e **ri-verificata a mano**
> in questa sessione, non riferita:
>
> ```
> $ curl -A "ClaudeBot" https://www.transfermarkt.com/robots.txt
> License: https://www.transfermarkt.de/license.xml
> ...
> User-agent: ClaudeBot          User-agent: Claude-SearchBot     User-agent: anthropic-ai
> Disallow: /                    Disallow: /                      Disallow: /
>
> $ curl -A "ClaudeBot" https://www.transfermarkt.com/license.xml
> <rsl xmlns="https://rslstandard.org/rsl">
>   <content url="/"><license><prohibits type="usage">ai-all</prohibits></license></content>
> </rsl>
> ```
>
> **Cosa questo significa e cosa NON significa** — la distinzione conta, perché il
> rilievo è facile da sovrastimare:
> - il `robots.txt` regola **il nostro crawling di transfermarkt.com**, e quel
>   crawling **non è mai avvenuto**: i dati arrivano da una ridistribuzione di terzi
>   su Kaggle (`dcaribou/transfermarkt-datasets`), più 29 celle recuperate a mano.
>   Da solo, quindi, **non decide** l'uso a valle;
> - il `license.xml` è invece una **riserva sull'USO** (`prohibits usage: ai-all`),
>   machine-readable secondo lo standard RSL, su **tutto** il sito. È il tipo di
>   riserva contemplata dall'art. 4(3) della Direttiva 2019/790 (art. 70-quater
>   L.633/41). **Questo tocca l'uso a valle, non solo il crawling**;
> - il **diritto sui generis** sulla banca dati resta di Transfermarkt: la CC0
>   dichiarata da `dcaribou` copre la propria compilazione, **non** può concedere
>   ciò di cui il dichiarante non è titolare. È lo schema che il progetto ha già
>   applicato **5 volte** per scartare altrettanti dataset («fonte avvelenata»).
>
> **Perché è delicato**: questa fonte non è un candidato, è **in produzione dalla
> Fase 67** — è la sorgente ufficiale di `home/away_squad_value` (§1), e i suoi file
> sono versionati in `files/player_scores/`. Il precedente interno (Premier League
> API e bundesliga.com, entrambe chiuse «per licenza, non per rete») porterebbe alla
> stessa conclusione anche qui.
>
> **Nessuna azione presa.** Tenere la fonte è legittimo, ma sarebbe una **decisione
> consapevole di rischio**, non un fatto tecnico — e come tale va scritta qui invece
> di restare implicita. *(Regola R4: un'anomalia si dichiara anche quando non è un
> errore.)*
>
> Nella tabella qui sotto la riga `player-scores` dice «CC0» senza questa riserva:
> la dicitura va corretta **qualunque** sia la decisione. Stesso testo in
> `files/README.md`.

| fonte | dove | stato |
|---|---|---|
| football-data (Serie A, CSV originali completi) | `data/football_data_raw/` (versionata, 9 file) | ✅ congelata; il sito originale **è tornato raggiungibile** (200, verificato alla Fase 100: le due leghe nuove sono state scaricate direttamente) |
| football-data (Premier/Liga) | `files/football_data_*_bundle.json` (caricati a mano, Fase 54) | ✅ congelata |
| football-data + Understat (**Bundesliga/Ligue 1**) | scaricate al volo da `scripts/fetch_sources.py` in `data/fonti/` — **non versionata** (135 MB, in `.gitignore`) | ⚠️ **le uniche due leghe senza fonte grezza congelata in repo**: ciò che è versionato è lo *snapshot* (§1) più le **90 impronte SHA256** del manifest (riga in fondo a questa tabella), che permettono di ri-scaricare e verificare l'identità bit-a-bit, non di lavorare offline sul grezzo |
| Understat (xG + rose giocatori) | `files/understat_*_bundle.json` (Premier/Liga); Serie A: **solo lo snapshot** | ⚠️ il mirror per-stagione è **sparito** (Fase 14): le rose Serie A NON sono rigenerabili — `--enrich`/ri-matching valgono solo per Premier/Liga finché non viene caricato un bundle Understat Serie A (come Fase 54) |
| ⭐ **diretta.it / Flashscore** (97 statistiche + rating **per giocatore-partita**) — **5 raccolte**: tutte e cinque le leghe modellate, 2025-26 | `files/diretta_{lega}_{stagione}/` (versionate; Serie A 11.894 + Premier 11.492 + Liga 11.953 + Bundesliga 9.617 + **Ligue 1 9.536** = **54.303 righe**, ognuna col proprio `manifesto.json`) | ⚠️ **il primo dato Tier B del progetto**, e l'unico con una **posizione di licenza dichiaratamente NON risolta**: dato a monte di **Opta**, raccolto **a mano** dall'utente (niente scraping), inserito su sua decisione consapevole fra il 31/07 e il **10/08/2026**. **Non rivendichiamo alcuna licenza.** Copertura: Serie A 379/380, Premier e Liga **380/380**, Bundesliga e Ligue 1 **306/306** di campionato (+ 2 e + 4 partite di spareggio, colonna `Fase`, escluse per default da `load_player_matches`). Join e coerenza gol verificati contro i nostri snapshot: **4.114 controlli, 4.114 passati**, su **1.751 partite**. Tutte le colonne statistiche sono `post` (regola R8). ⚠️ **`Gol concessi` e' INDIVIDUALE** — i gol presi mentre quel giocatore era in campo, non il totale di squadra: sommarla sulla rosa da' ~11× i gol subiti (Fase 145). ⚠️ **Una riga a 0 minuti** in tutto il dataset (Ali Youssef, Lorient-Nantes g.20): e' una lacuna della fonte, non un giocatore rimasto fuori — dichiarata per nome nel manifesto (`righe_con_zero_minuti`), e la stessa riga perde anche il cartellino che la cronaca le attribuisce (Fase 146). Bundesliga e Ligue 1 portano anche **4 fogli in piu'** — elenco partite, formazioni (panchinari compresi), cambi, eventi di cronaca ⚠️ **incompleta per costruzione**. Leggere `files/diretta_serie_a_2526/README.md` |
| ⭐ **diretta.it / Flashscore** (45 statistiche **per squadra-partita, divise in PERIODI**) — **5 raccolte**, tutte le leghe 2025-26 | `files/diretta_{lega}_{stagione}/squadra_per_partita.csv.gz` (versionate, 604 KB in tutto; **10.512 righe** di campionato = 3.504 squadra-partita × 3 periodi, + 38 righe di spareggio; ognuna col proprio `manifesto_squadra.json`) | ⚠️ **stessa fonte e stessa posizione di licenza NON risolta** del dato per giocatore (riga sopra); consegnato dall'utente il 01/08/2026. **È il primo dato del progetto che separa i due tempi** (Totale / 1° tempo / 2° tempo): serve al residuo aperto delle Fasi 96/99. Verificato contro football-data.co.uk, **fonte indipendente**: join **3.504/3.504**, risultato **3.504/3.504**, additività dei periodi **137.124/137.124** celle, conteggi 97,7-99,7% con scarto medio ~0. Gol per periodo dedotti vs `HTHG/HTAG`: **98,3%** (1T) e **97,9%** (2T), scarto **sempre ≤ 0**. ⚠️ Quattro cose da sapere prima di usarlo: il **vuoto è uno ZERO** (fino al 94% di NaN su 3 colonne); le righe **`Fase == 'Play-off'`** non sono campionato ed è la colonna `Fase`, mai la data, a separarle; **una partita è incompleta e sembra completa** (Nantes-Tolosa 17/05/2026, `Totale` == `1° tempo`); `Risultato squadra` ed `Esito` sono **`post` anche sulle righe di periodo** → **il punteggio all'intervallo NON è nel dataset**. Tutte le 45 metriche sono `post` (R8). ⭐ Dal 01/08/2026 ogni raccolta conserva anche **`originale_squadra.xlsx`, il file come consegnato** (regola §5-ter del `CLAUDE.md`: raccogliere tutto, e tenere l'originale perché un bug nella nostra conversione sia visibile) — fedeltà misurata, 569.700 celle e 0 divergenti. Leggere `files/README_statistiche_squadra.md` |
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

## 4-quater · La colonna PIENA e VUOTA: le assenze nel 2025-26

Trovato l'11/08/2026 aprendo `main` per un controllo di routine sulla stagione
appena chiusa. È il caso **R6** in forma pura — *il buco peggiore non è il
`NaN`: è il finto pieno* — e merita una sezione perché nessuno dei controlli
che il progetto già esegue lo vedeva.

**Il fatto.** `home/away_absent_count_est` è piena al **100%** su tutte e nove
le stagioni: zero `NaN`, anche nel 2025-26. Ma il valore che `add_absences`
scrive quando la fonte non conosce nessun infortunio **non è `NaN`, è `0.0`**
(`src/data/transfermarkt.py`, `counts[side].append(float(len(absent)))` — la
lista vuota dà zero). Un conteggio di celle non-nulle non può distinguere
*«nessuno è infortunato»* da *«non so chi è infortunato»*.

**Come si vede lo stesso.** Non guardando quante celle sono piene, ma
**quante volte il conteggio SALE**. Una fonte infortuni viva fa salire spesso
il numero di indisponibili di una squadra: arrivano infortuni nuovi. Una fonte
ferma può solo farlo scendere — i vecchi guariscono e nessuno li rimpiazza.

```
passo(squadra, t) = absent_count_est(squadra, t) − absent_count_est(squadra, t−1)
% sale = #{passi > 0} / #{passi}          su tutte le squadre-partita di una stagione
```

| stagione | passi | sale | % sale | % righe a 0 |
|---|--:|--:|--:|--:|
| 2017-18 → 2024-25 | ~3.400/anno | ~840-1.015 | **23,6% → 29,2%** | 7,3% → 14,6% |
| **2025-26** | 3.408 | **55** | **1,6%** | **83,5%** |

E dentro il 2025-26 il taglio ha una data:

| mese | passi | sale | % sale | media assenti |
|---|--:|--:|--:|--:|
| 2025-08 | 156 | 35 | 22,4% | 2,18 |
| 2025-09 | 306 | 20 | 6,5% | 0,97 |
| **2025-10 → 2026-05** | 2.946 | **0** | **0,0%** | 0,30 → 0,01 |

**Zero salite in otto mesi consecutivi**, su 2.946 passi. Non è un calcio
senza infortuni: è il dump infortuni di Transfermarkt fermo a **settembre
2025**. Quello che si osserva dopo è la coda dei soli infortuni iniziati prima
del taglio, che guariscono uno alla volta — da cui il decadimento monotono
della media da 2,18 a 0,01.

**Cosa NON è.** Non è un bug del codice: `add_absences` fa esattamente ciò che
dice. Non è un difetto che sporca le previsioni: `covariates` è `()` di default
(`scripts/backtest.py`), quindi nessun backtest ufficiale legge questa colonna.

**Perché conta lo stesso, e molto.** È una trappola armata per chi verrà dopo.
Chiunque provi `--covariates absence` sul 2025-26 misurerebbe il nulla e ne
concluderebbe *«le assenze non predicono»* — un risultato negativo su una
colonna vuota, esattamente ciò che il principio §1.10 del CLAUDE.md vieta di
scrivere senza il suo perimetro. La verifica costa un comando:

```bash
python scripts/_run_stato_2526.py    # blocco 2 = questa tabella
```

**Cosa serve per ripararla.** Ri-scaricare il dump infortuni con
`force=True` una volta che la fonte è tornata avanti (`_load_injuries`), e
ricostruire la colonna. Finché non succede, il 2025-26 va trattato come
**assenze non disponibili**, non come *«stagione senza assenti»*.

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
| **perimetro** | dalla **Fase 142**: i 5 campionati **+ coppe nazionali dei 5 paesi + UEFA per club + seconde divisioni**. Misurato l'08/08: 158 partite esposte (58+52+48) su 865 che il listino espone. ⚠️ La colonna si chiama `lega` ma contiene anche `coppa_italia`, `serie_b`, `ucl_qual`: **si filtra su `fascia`** (`campionato`/`coppa`/`seconda`), non su `lega` |
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

**⚠️ Un file può essere legittimamente PARZIALE (Fase 141), e lo dichiara.**
Fino all'08/08/2026 un guasto di rete su una partita faceva perdere l'intero
giro: un `HTTP 503` alla 22ª partita di 58 ha buttato **7.870 righe già
raccolte**, mai scritte. Ora il giro sopravvive e salva ciò che ha — quindi
chi rilegge deve poter distinguere «quel mercato non era quotato» da «quel
mercato non è arrivato». Due campi lo dicono, e **vanno letti prima di usare
il file**:

| campo | significato |
|---|---|
| `leghe_senza_partite_esposte` | (dal 01/08) le nostre leghe con zero partite nel listino — tipicamente uno slug rinominato a monte |
| `partite_incomplete` | (dal 08/08) una voce per partita non raccolta o raccolta a metà: `mercati_persi` vale `"tutti"` oppure il numero di mercati caduti, con il motivo (`HTTPError…`, budget esaurito) |

Vuoti entrambi = raccolta completa di tutto ciò che era in finestra. **Un
congelamento per il test prospettico non si fa su un file che li ha pieni.**
Un giro che non raccoglie *nessuna* riga, invece, non scrive alcun file: un
archivio non deve mai contenere un silenzio che sembra un dato (R6).

**⚠️ `fascia`: il campo con cui si filtra (Fase 142).** Dal perimetro allargato
il file **non contiene solo campionati**. `lega` è rimasta la colonna storica
(l'archivio già scritto la usa) ma porta anche `coppa_italia`, `league_cup`,
`ucl_qual`, `serie_b`… Chi raggruppa per `lega` credendo di avere campionati
mette Vicenza-Catania fra le partite di Serie A **e non riceve nessun errore**.

| `fascia` | cosa contiene |
|---|---|
| `campionato` | i 5 modellati. **È il filtro da usare** per tutto ciò che parla di Serie A/Premier/Liga/Bundesliga/Ligue 1 |
| `coppa` | Coppa Italia, League Cup, supercoppe, UEFA per club (e Copa del Rey, DFB-Pokal, Coupe de France quando compariranno) |
| `seconda` | Serie B, Championship, Liga 2, 2.Bundesliga, Ligue 2 |

I file **precedenti alla Fase 142 non hanno il campo**: sono tutti e soli
campionati, quindi l'assenza vale `campionato` — è così che
`ultimo_listino_completo()` continua a leggere l'archivio storico.

Tre campi nuovi nei metadati dicono che cosa quel giro *poteva* contenere:
`perimetro` (le coppie fascia/lega raccolte), `partite_per_fascia` e
**`fuori_perimetro`** — il radar: le competizioni dei nostri paesi o UEFA che
il listino esponeva e che non abbiamo preso. Non è un errore se non è vuoto:
è l'unico posto dove si vedrà una coppa nuova comparire con un nome che non
avevamo previsto.

**Costo dell'archivio, dichiarato.** 454 byte per riga misurati. Il lungo
raggio vale ~149 KB/giorno (~45 MB a stagione); il **denso in-season** è la
voce pesante e porta il totale nell'ordine dei **250-300 MB** versionati per
stagione. ⚠️ **Rimisurato alla Fase 142**: col perimetro allargato e il listino
pieno il giro di lungo raggio è passato da 593 KB a **~1,3 MB** (158 partite
invece di 58), quindi l'ordine di grandezza per la stagione va rivisto verso
l'alto — resta una cifra da **decidere**, non da subire. È una cifra da **decidere** (leve: frequenza del cron, esclusione del
risultato esatto anche dal denso), non da subire.

---

## 5-ter-bis · Quote IN-PLAY (`data/smarkets_live/`) — Fase 143

Prezzi raccolti **a partita in corso**. Specifica completa nel README della
cartella: **`data/smarkets_live/README.md`**. Qui solo ciò che serve al catalogo.

| | |
|---|---|
| **fonte** | Smarkets, stessa API del 5-ter, ma `state=live` |
| **perimetro** | lo stesso del pre-partita (5 campionati + coppe + UEFA + seconde divisioni + **amichevoli delle nostre 96 squadre**, Fase 149), più il **perimetro di PROVA** che riempie il carico fino a 25 partite e scrive altrove (Fase 148) |
| **granularità riga** | (istante, partita, mercato, contratto) — un file per **sessione** contiene decine di giri |
| **cadenza** | nucleo (1X2, O/U 2.5, GG/NG, risultato esatto) ogni **2 min**; listino pieno (~103 mercati) ogni **15 min** |
| **si scrive con** | `python scripts/fetch_smarkets_live.py`; automazione `.github/workflows/smarkets-live.yml` (sentinella ogni 30 min) |
| **disponibilità (R8)** | ⚠️ `post` rispetto al calcio d'inizio, `pre` rispetto al minuto successivo. Un prezzo al 67' **non** è utilizzabile per prevedere la stessa partita da fermo: è utilizzabile per prevedere ciò che accade **dopo** il 67' |

**⚠️ Perché è una cartella separata e non un file in più nel 5-ter.** Un prezzo
in-play **conosce il punteggio**, uno pre-partita no: non sono confrontabili
riga per riga. Nella stessa cartella, ogni lettore dell'archivio pre-partita —
`ultimo_listino_completo()` per primo — li leggerebbe come la stessa cosa
**senza dare errore**.

**Il campo `stato_mercato` (nuovo, Fase 143):** `live` / `settled` / `halted`.
Esiste anche nel 5-ter, dove vale sempre `live`. In-play distingue «prezzo
assente perché il mercato è già deciso» da «prezzo assente perché non c'è
liquidità» — due stati opposti che senza questo campo sono lo stesso `None`.
`halted` è il mercato **sospeso**: l'istante in cui sta succedendo qualcosa.

**Il punteggio si ricostruisce ma NON è nel file.** `gol = ⌈max linea O/U
settled⌉` e `(casa, fuori) = minimo componentwise dei punteggi ancora quotati`
sono due stimatori indipendenti che concordano (verificati su una partita,
08/08/2026). Restano una **regola da validare** su partite a risultato noto:
finché non lo è, il file contiene ciò che l'API ha detto e nient'altro (§5).

**Le AMICHEVOLI delle nostre squadre (Fase 149).** È l'unica voce del
perimetro decisa da **chi gioca** e non da **dove**: `club-friendlies` contiene
tutto il calcio amichevole del pianeta, quindi il filtro è sui nomi delle 96
squadre dei 5 campionati (`data/squadre_smarkets_2026_27.json`). Queste righe
portano `fascia = "amichevole"` — valore **nuovo**, accanto a
campionato/coppa/seconda — perché una precampionato non è una partita di
campionato né per formazioni né per motivazione, e un modello deve poterla
**escludere con un filtro** invece di trovarsela dentro `coppa`.

⚠️ **Non usare `nome_smarkets` dell'anagrafica 2026-27 per riconoscerle.**
Misurato l'11/08/2026: coincide col nome vero di Smarkets **32 volte su 96**
(`Juventus Turin` contro `Juventus`, `AS Roma` contro `Roma`). Entrambi gli
insiemi hanno 96 elementi, quindi nessun conteggio di celle piene lo rivela:
è il **finto pieno** della R6, e si vede solo incrociando le due fonti.

---

## 5-ter-ter · Quote IN-PLAY di PROVA (`data/smarkets_prova/`) — Fase 148

Stessa pipeline del 5-ter-bis, **cartella diversa e destino diverso**.
Specifica nel README della cartella: **`data/smarkets_prova/README.md`**.

| | |
|---|---|
| **fonte** | Smarkets, `state=live`, tutto ciò che è **fuori** dal nostro perimetro |
| **perché esiste** | il nostro perimetro gioca 3-7 h al giorno contro le 5-14 di tutto il calcio: senza carico vero l'infrastruttura in-play non si prova |
| **quanto carico aggiunge** | **zero**: riempie fino al tetto di 25 partite già esistente, `max(0, 25 − |nostre|)` |
| **volume misurato (10-11/08/2026, 24 h)** | 100.883 righe, 56 partite-sessione, 28 competizioni |
| **stato** | 🟡 raccolto e **mai letto da nessun modello**, ed è lo stato voluto (§5-ter: raccolto ≠ usato) |

⚠️ **NON usare per stimare niente.** Non è un campione casuale del calcio: è un
campione **di comodo**, scelto in base a quando l'infrastruttura aveva bisogno
di lavorare — cioè il peggior criterio di selezione possibile per una stima.

---

## 5-ter-quater · I nomi Smarkets delle nostre squadre (`data/squadre_smarkets_2026_27.json`) — Fase 149

| | |
|---|---|
| **cosa** | i 96 nomi con cui Smarkets chiama le squadre dei 5 campionati modellati (20+20+20+18+18) |
| **si scrive con** | `python scripts/costruisci_squadre_smarkets.py` — **generato, mai a mano** (R3) |
| **da dove** | dall'archivio `data/smarkets_matches/`, righe con `fascia == "campionato"`: è la fonte che parla di sé, non una traduzione né una stima |
| **disponibilità (R8)** | `statico` (anagrafica di nomi) |
| **usato da** | `scripts/fetch_smarkets_matches.py` per riconoscere le amichevoli delle nostre squadre |
| **limite dichiarato** | copre le squadre **già viste** in archivio; una squadra mai comparsa non c'è, e la sua amichevole resta fuori dal perimetro. Si chiude ri-eseguendo il generatore |

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

## 5-quinquies · Carriere dei calciatori (`data/carriere_wikipedia/`) — Fasi 127-132

Il **database carriere**: una riga per giocatore-club-stagione, da **due fonti in
una tabella sola** (non due strati — `src/data/careers.py`, colonna `fonte`).

| file | cos'è | licenza |
|---|---|---|
| `tappe.csv.gz` | il deliverable: ~202.000 tappe su ~21.600 giocatori | **CC BY-SA 4.0** (Wikipedia) |
| `esiti_riepilogo.csv` | l'esito di **ogni** tentativo, anche negativo (§1.4) | CC BY-SA 4.0 |
| `wikidata_qid.csv.gz` | 24.413 `player_id` → Q-id, estratti dalla cache HTML | CC0 |
| `verdetti_wikidata.csv.gz` | il verdetto d'identità su 477 casi dubbi (Fase 132) | **CC0** (Wikidata) |
| `esiti.jsonl`, `verdetti_wikidata.jsonl` | file di LAVORO (resumabilità), **non versionati** | — |

⏱️ **R8.** `anno_da`/`anno_a`/`presenze`/`gol` di una tappa sono **`post`** rispetto
alle partite di quella tappa, e **`pre`** rispetto a qualunque partita successiva.
L'unico accesso sicuro è **`careers.career_before(as_of)`**, che taglia con `<`
stretto: usare `load_database()` per costruire una feature di backtest è
look-ahead. `player_id`, `club_id` e la data di nascita sono **`statico`**.

### Le colonne d'identità: quale dice cosa

Tre colonne, e **non sono ridondanti** — confonderle è il modo più facile di
leggere male il file:

| colonna | chi l'ha scritta | valori |
|---|---|---|
| `identita` | il **verdetto finale**, quello su cui filtrare | `confermata_data`, `confermata_club`, `confermata_wikidata`, `quarantena`, `non_verificata` |
| `identita_wikipedia` | il giudizio della verifica HTML, **prima** di Wikidata | incl. `respinta` |
| `identita_wikidata` / `forma_discrepanza` | il verdetto Wikidata e la **forma** dello scarto | `confermata`/`smentita`/`indeterminato`; `senza_struttura`, `scambio_giorno_mese`, … |

⚠️ **`respinta` non compare mai in `identita`**, per costruzione: Wikidata può
ribaltare una respinta (17 casi), e una riga *dentro* il database che continuasse
a dichiararsi esclusa sarebbe un **finto pieno (R6)** — un valore che sembra una
misura e non lo è più. Nessun confronto snapshot-contro-fonte se ne accorgerebbe,
perché il dato coincide con ciò che l'ha prodotto; se ne accorgerebbe solo il
primo che filtra su quella colonna, con una risposta sbagliata e nessun motivo di
sospettarla. Il giudizio originale resta leggibile in `identita_wikipedia`.

### Cosa NON c'è dentro

- **5 giocatori rimossi** perché la pagina era di un'altra persona (forma senza
  struttura **e** oltre tre anni di scarto): Olaizola, Lazaridis, Nilson Júnior,
  Bruno Alves, Ballantyne. Le loro tappe restano in `esiti.jsonl`, che serve a
  sapere *chi* era. ⚠️ **Ballantyne è al bordo**: 1.105 giorni contro una soglia
  di 1.098, coi vicini a 1.004 e 1.261 — quel caso lo decide il taglio, non i
  dati. Gli altri quattro stanno a 3.116+.
- **~10 quarantene** ancora sospette ma non rimosse: l'evidenza non regge da sola.
- Le 141 quarantene *smentite* da Wikidata **ci sono ancora**, ed è voluto: la
  mediana del loro scarto è **31 giorni** e la forma conserva sempre una
  componente della data — sono **refusi**, non persone diverse. Rimuoverle era la
  trappola (§1.4 del CLAUDE.md: anche il risultato negativo si scrive).

⚖️ **Licenza mista, dichiarata**: le tappe sono CC BY-SA 4.0 (contenuto
Wikipedia), i verdetti e i Q-id sono CC0 (Wikidata). Vedi
`data/carriere_wikipedia/README.md`.

---

## 5-sexies · Coppe nazionali 2025-26 (`data/coppe_2526/`) — Fase 138

**662 partite** su sei coppe e cinque paesi: Coppa Italia (45), FA Cup (123),
EFL Cup/Carabao (93), Copa del Rey (137), DFB-Pokal (63), Coupe de France (201).
Con **18.566 righe di formazione** (titolari + panchina + minuti giocati) e
**8.177 eventi col minuto** (sostituzioni, gol, cartellini, rigori) su 458
partite. Dettaglio completo in `data/coppe_2526/README.md`.

⚠️ **Il difetto della fonte, da conoscere prima di usare il dato.** In
`games.csv` di player-scores il risultato è **sommato ai rigori** su **68
partite (14,8%)**: Braunschweig-Stuttgart risulta `11-12` mentre è finita 4-4
(rigori 8-7). È un **finto pieno** da manuale (R6): sembra un punteggio e non
lo è. Nella nostra raccolta il punteggio è **ricostruito dagli eventi** e vive
in colonne separate — `gol_*_90`, `gol_*_finale`, `rigori_*` — mentre il valore
grezzo della fonte è conservato in `gol_*_dichiarato` (per poter scoprire un
bug nella *nostra* conversione, §5-ter). Resa **448/458 (97,8%)**; i 10 residui
sono marcati `eventi_incompleti`, non corretti a occhio.

**Verificata contro una fonte esterna**: openfootball scrive la stessa partita
già scomposta (`7-8 pen. 4-4 a.e.t. (3-3, 1-1)`). Sulle 42 partite di
DFB-Pokal appaiabili la ricostruzione coincide **42/42 su tutti e sei i campi**,
zero divergenze. openfootball copre però solo la Germania per il 2025-26 e solo
i primi due turni: è un verificatore parziale, non una fonte alternativa.

**Perimetro** (decisione utente 02/08/2026): «da dove entrano i club di seconda
divisione». Il turno d'ingresso è **misurato** — primo turno con un club che
football-data elenca in 2ª divisione 2025-26 — e non copiato da una scheda di
formato: Coppa Italia *Qualifying Round*, FA Cup *Third Round*, Carabao / Copa
del Rey / DFB-Pokal *First Round*, Coupe de France *7° turno*. **577 partite**
nel perimetro; le altre sono **tenute** e marcate `dentro_perimetro = False`.

**Buchi dichiarati.** **204 partite senza formazione**: le 201 di Coupe de
France (player-scores non ha coppe francesi in `competitions.csv`, rilievo già
noto dall'audit fonti) e le **3 finali** — Coppa Italia, FA Cup, DFB-Pokal —
che mancano da `games.csv` pur essendoci 846 partite di maggio 2026 in altre
competizioni, e sono state recuperate da Wikipedia. Sono esattamente le righe
con `game_id` vuoto.

**Disponibilità temporale (R8).** Le **formazioni titolari** sono `pre` (note
circa un'ora prima del fischio, quindi utilizzabili per prevedere anche se qui
sono raccolte a posteriori); **sostituzioni, minuti, gol, cartellini e
risultato** sono `post`. Arbitro, stadio e squadre sono `pre`.

**Stato d'uso: raccolto, non usato.** Nessun modello legge questi dati
(§5-ter: «raccolto ≠ usato» è uno stato legittimo e va scritto).

---

## 5-septies · Coppa Italia 2025-26, raccolta MANUALE (`files/diretta_coppa_italia_2526/`) — Fase 139

La stessa Coppa Italia della §5-sexies, letta a mano da **diretta.it
(Flashscore)** da un collaboratore dell'utente. Non è un doppione: è la
**seconda misura indipendente**, ed è il motivo per cui la raccolta automatica
era stata costruita in una forma confrontabile.

**Esito del confronto** (in `manifesto.json`, ricalcolabile con
`python scripts/registra_raccolta_coppa_diretta.py --cartella …`):

| confronto | esito |
|---|---|
| partite appaiate | **45 / 45** |
| punteggi identici (90', finale, rigori) | **45 / 45** |
| undici iniziali identici | **88 / 88** squadre-partita |

**Cosa aggiunge** rispetto alla fonte automatica: 1.307 righe × **103 metriche
per giocatore** (41 partite su 45 — dove diretta.it non pubblica la sezione le
righe non ci sono); la **sequenza completa dei rigori** (256 eventi, e le 12
partite ai rigori ricompongono 12/12 — mentre nell'automatica la sequenza è
troncata); il **periodo** di ogni evento (1°/2° tempo, supplementari, rigori);
e i titolari della **finale**, che `games.csv` non conteneva.

**Contenuto**: `originale_coppa.xlsx` (come consegnato, §5-ter) + i cinque fogli
esportati in CSV (`partite`, `formazioni_e_cambi`, `eventi`, `stat_giocatori`,
`note`) + `manifesto.json` con tutte le verifiche.
⚠️ `originale_partite.csv` e `originale_formazioni.csv` sono **duplicati esatti**
di due fogli dell'xlsx (verificato cella per cella, 0 divergenti): restano
archiviati perché escludere un dato richiede il consenso dell'utente (§5-ter).

**Disponibilità temporale (R8)**: formazioni titolari e modulo sono `pre`;
risultato, sostituzioni, eventi, rating e le 103 metriche sono `post`.

**Stato d'uso: raccolto, non usato.** Nessun modello legge queste colonne.

⚠️ **Licenza**: il progetto non rivendica alcun diritto su questi dati — vale
la stessa avvertenza delle altre raccolte diretta.it (`files/README.md`).

---

## 5-octies · Gli agganci delle coppe (`data/coppe_2526/aggancio_*.csv`) — Fasi 139-bis → 139-quater

Cinque tabelle-ponte che collegano le **raccolte manuali** di coppa
(`files/diretta_*_2526/`) al resto del database: `aggancio_squadre` (nome
diretta.it → `club_id`), `aggancio_partite` (`ID partita` → `game_id`),
`aggancio_giocatori`, `aggancio_eventi`, `aggancio_statistiche` (nome →
`player_id`). Si rigenerano con `python scripts/aggancia_coppe.py`; la
completezza si controlla con `python scripts/verifica_aggancio_coppe.py`.

⚠️ **I candidati si cercano nel (partita, CLUB), non nella partita** (Fase
139-decies). Cercarli nella partita intera li prende da entrambe le rose, e in
una partita ci sono omonimi: in Navalcarnero-Getafe lo stesso `player_id`
finiva sulle righe di tutte e due le squadre. Corollari misurati:
- il club di una riga viene da `Squadra` dove c'è, **dal `Lato`** dove non c'è
  (`eventi.csv` ha solo quello: prenderlo dal solo `Squadra` faceva crollare gli
  eventi agganciati da 3.639 a 561);
- ⭐ **l'autogol sta sul lato di chi lo SUBISCE** — diretta.it lo registra sul
  lato che ne beneficia, ma il giocatore è dell'altra squadra (stessa
  convenzione della fonte automatica, Fase 138). Senza l'inversione i **35
  autogol** delle sei coppe restano senza `player_id`;
- un `player_id` **non può servire due persone** nella stessa partita: dove due
  nomi lo rivendicano resta vuoto per entrambi (1 caso, «Perez Andoni»/«Perez
  Alex» del Club Portugalete).

⚠️ **Un aggancio incerto resta VUOTO** — mai scelto a caso. Le colonne
`club_id`, `game_id` e `player_id` sono quindi nullable *per progetto*, e la
colonna `metodo` dice come si è arrivati a ciascun `player_id` (`nome`,
`eliminazione`, `rosa_stagionale` — l'ultimo è un vincolo più debole, usato solo
dove la partita non esiste nella fonte automatica).

**Copertura misurata** (05/08/2026: la riga francese e' quella della Fase
139-sexies, le altre cinque sono immutate dalla Fase 139-quater):

| coppa | partite → `game_id` | partite appaiate | squadre → `club_id` | righe formazione → `player_id` |
|---|--:|--:|--:|--:|
| Coppa Italia | 44/45 | 45/45 | 44/44 | 2.130/2.133 (99,9%) |
| DFB-Pokal | 62/63 | 63/63 | 64/64 | 2.514/2.518 (99,8%) |
| EFL Cup | 91/91 | 91/91 | 90/90 | 3.598/3.606 (99,8%) |
| FA Cup | 62/63 | 63/63 | 64/64 | 2.515/2.515 (100%) |
| Copa del Rey | 117/117 | 117/117 | 116/116 | 4.775/5.040 (94,7%) |
| Coupe de France | **0/201** | 161/201 | 33/202 | 932/2.495 (37,4%) |

**Buchi dichiarati, e sono di due tipi diversi.**

1. **Le tre finali** (Coppa Italia, FA Cup, DFB-Pokal): non esistono in
   `games.csv`, quindi non hanno un `game_id` da agganciare. È il `−1` delle
   prime due righe.
2. **La Coupe de France è un caso a sé, e non è un limite del nostro
   aggancio**: la sua fonte automatica è **Wikipedia** (player-scores non ha
   coppe francesi), che non porta né `game_id` né `club_id` né formazioni —
   **0/201 righe** hanno un identificatore. Il ponte manca dalla sponda opposta.
   Le 161 partite *appaiate* servono comunque: è così che se ne verificano i
   punteggi (157/161 identici). I giocatori agganciati lì passano tutti dalla
   **rosa stagionale**, e solo per i club che il registro conosce.
   ⚠️ **Non tutto quel buco era strutturale**, e per due fasi lo abbiamo scritto
   come se lo fosse. Sei club di **Ligue 1** restavano vuoti solo perché
   diretta.it li scrive con l'esonimo italiano («Lione» contro «Olympique
   Lyon»): aggiunti in `club_matching.ALIAS`, i giocatori agganciati sono
   passati da **19,7% a 37,4%**. Nella stessa verifica sono usciti **due falsi
   positivi** — «Red Star» andava al **Red Star Belgrado** e «Lusitanos» all'
   **FC Lusitanos andorrano** — ora bloccati in `NON_AGGANCIARE` (Fase
   139-sexies).
3. **Le 265 righe della Copa del Rey** non sono righe mancanti (le due fonti
   hanno lo stesso numero di giocatori per squadra-partita, delta medio +0,02):
   è la convenzione spagnola sui **due cognomi** — «Sanchez Alonso M.» contro
   «Mario Sánchez» — che la regola del sottoinsieme non aggancia. Dichiarata,
   non chiusa.

**Invarianti verificati** (Fase 139-decies, tutti in `tests/test_coppe_query.py`):

| invariante | esito |
|---|--:|
| il giocatore appartiene al club del suo lato | **9.332 / 9.332** |
| eventi coerenti col lato (autogol invertito) | **11.990 / 11.990** |
| un `player_id` = una persona per partita | 0 violazioni |
| righe duplicate nel pannello | 0 |

⚠️ **15 coppie (partita, giocatore) compaiono su ENTRAMBI i lati** negli eventi,
e non è un difetto: sono **15/15** giocatori con un autogol — quello sta sul
lato avversario, il cartellino o la sostituzione sul proprio. Dichiarato per R4,
altrimenti la sessione dopo lo «corregge».

**Disponibilità temporale (R8)**: tutte queste tabelle sono **`statico`** —
sono anagrafica di identità (chi è chi), non misure della partita.

**Stato d'uso: raccolto, non usato.** Nessun modello legge questi agganci.

---

## 5-octies-bis · Statistiche di SQUADRA per periodo delle coppe (`files/diretta_*_2526/stat_squadra.csv`) — Fase 139-quinquies

Il **secondo consegnato** di diretta.it per ogni coppa, complementare al primo:
porta ciò che la raccolta base non aveva — le statistiche di squadra divise per
**periodo**, **35 metriche** per riga (xG, xGOT, possesso, tiri per esito e per
zona, passaggi, cross, contrasti, parate, gol evitati…).

| coppa | righe | partite | Totale / 1° / 2° | Supplementari |
|---|--:|--:|---|--:|
| Coppa Italia | 272 | 45 | 90 / 90 / 90 | 2 |
| DFB-Pokal | 406 | 63 | 126 / 126 / 126 | 28 |
| FA Cup | 406 | 63 | 126 / 126 / 126 | 28 |
| EFL Cup (Carabao) | 546 | 91 | 182 / 182 / 182 | **0** |
| Coupe de France | 476 | **87 / 201** | 174 / 142 / 160 | 0 |
| Copa del Rey | 692 | **114 / 117** | 228 / 196 / 216 | 52 |

**Ci sono tutte e sei**: 2.798 righe, 463 partite.

⚠️ **Lo zero della Carabao non è un dato mancante: è il regolamento.** Dal
2018-19 la EFL Cup va **direttamente ai rigori** in ogni turno tranne la finale
(finita 0-2 nei 90'). Verificato sul dato indipendente: nelle 91 partite non c'è
**un solo evento** oltre il 90°, contro 6/131/142 delle altre tre coppe (R4).

⚠️ **Coupe de France e Copa del Rey hanno la copertura a TRE LIVELLI.** Non è
una colonna: si legge da quante metriche sono piene, e va guardato prima di
usare il dato.

| livello | metriche piene | cosa c'è | dove |
|---|--:|---|---|
| completo | ~27 / 29 | tutto, xG e possesso compresi | Coupe dai 32esimi; Rey dai 1/16 + 15 partite del 2° turno |
| base | 8-10 | tiri, angoli, falli, fuorigioco, rimesse, punizioni, cartellini | Rey: 13 partite del 2° turno |
| solo cartellini | 1-2 | i cartellini e basta | Coupe: 24 partite dei turni 7-8; Rey: 53 del 1° turno |

Le righe del terzo livello esistono **perché** c'è stato un cartellino: il
conteggio combacia con `eventi.csv` **48/48** (Coupe) e **106/106** (Rey). Le
altre colonne sono **vuote**, non zero (R6) — ed è per questo che i periodi non
si bilanciano: la riga di un tempo esiste solo se in quel tempo è successo
qualcosa. Senza statistiche del tutto: 114 partite della Coupe, 3 del Rey.

**Coerenza interna dei periodi, misurata**: le metriche numeriche sono additive
**126/126** (Coupe) e **2.146/2.146** (Rey); quelle a rapporto lo sono su
numeratore e denominatore **252/252** e **720/720**; `Possesso palla`
(percentuale, non additiva) fa 100 fra casa e ospite in **189/189** e
**197/197** gruppi completi.

⭐ **Semantica di `Totale`, stabilita qui e mai verificata prima: è la partita
INTERA, supplementari compresi**, non il 90'. Sulle 102 squadra-partita andate
ai supplementari nelle quattro coppe che ne hanno, `1T + 2T + Suppl = Totale` in
**2.228/2.228** celle, mentre `1T + 2T = Totale` regge solo in 628/2.232. Chi
usa `Totale` come «i 90 minuti» sbaglia su 13-14 partite per coppa.

⚠️ La prima lettura del possesso diceva «49 gruppi su 238 non fanno 100»: era un
`groupby().sum()` che conta i `NaN` come zeri. Righe con possesso 0%: **nessuna**.

⚠️ **La stessa fonte può scrivere un club in due modi fra i due consegnati**:
Copa del Rey, `Ciudad Cieza` nella raccolta base e `Cieza` nel file di
statistiche (stesse 2 partite, stessi 14 giocatori; CD Cieza, `club_id` 56725,
confermato dalla fonte automatica). `coppe_aggancio.sinonimi_squadra` lo accetta
solo per **sottoinsieme di token** e solo se **unico nei due sensi**, lo
**dichiara** nel manifesto, e non riscrive la colonna: canonicalizza la chiave,
non il dato.

**Aggancio**: `data/coppe_2526/aggancio_statistiche_squadra.csv` (`game_id` +
`club_id`). Le righe senza `game_id` sono esattamente quelle della **finale**
che `games.csv` non contiene — 6 per coppa (2 squadre × 3 periodi): 400/406 per
Coppa Italia, Pokal e FA Cup, **546/546 per la Carabao** e **692/692 per la Copa
del Rey**, le due la cui finale la fonte automatica ha. La **Coupe de France** è l'eccezione opposta: **0/476**
con `game_id` e 234/476 con `club_id`, perché la sua fonte automatica è
Wikipedia e non porta identificatori (assenza a monte, §5-octies).

**Lo stesso file porta anche una versione migliore del foglio giocatori**:
stessi valori — verificato, **0 celle divergenti oltre l'arrotondamento su
1.193.504 confrontate** (1.307+1.979+1.974+2.855+1.924+1.437 righe × 104 colonne in comune) —
ma con `ID partita`, che prima mancava, e i decimali per intero invece che
troncati a tre. Il vecchio foglio viene sovrascritto **solo dopo** che la
verifica è tornata; l'originale come consegnato resta in
`originale_statistiche.xlsx` (§5-ter).

**Disponibilità temporale (R8)**: tutte `post` — sono misure della partita. Le
colonne identificative (`Data`, `Casa`, `Ospite`, `Squadra`, `Periodo`) sono
`statico`/`pre`.

⭐ **È il primo dato di COPPA che separa i due tempi**, cioè la forma che serve
al modello a due stadi (residuo aperto delle Fasi 96/99). Per i campionati lo
stesso dato esiste dalla Fase 131.

**Stato d'uso: raccolto, non usato.** Nessun modello legge queste colonne.

⚠️ **Licenza**: vale l'avvertenza delle altre raccolte diretta.it
(`files/README.md`) — il progetto non rivendica alcun diritto su questi dati.

---

## 5-octies-ter · L'incrocio dei dati di coppa (`data/coppe_2526/incrocio_*`) — Fase 139-octies

Risponde alla domanda «per QUESTA partita ho tutto, e si unisce?». Prodotto da
`python scripts/verifica_incrocio_coppe.py --csv`:
`incrocio_per_partita.csv` (una riga per partita del perimetro, un booleano per
blocco) e `incrocio_manifesto.json` (i conteggi).

⚠️ **Tre distinzioni che un conteggio unico confonde**, e per cui lo script
produce quattro tabelle invece di una:

| | |
|---|---|
| **fuori perimetro ≠ buco** | 82 delle 662 partite non sono mai state chieste (decisione utente sul perimetro): al denominatore diventerebbero un difetto immaginario |
| **senza ponte ≠ assente** | sulla chiave `game_id` la Coupe de France è 0 su tutto; sulla **sua** chiave ha 201 partite, 63 con le sostituzioni, 87 con le statistiche di squadra |
| **presente ≠ unibile** | una partita può esserci da entrambe le parti mentre le **persone** non si uniscono: è il join `player_id`, e va misurato a parte |

**Esito** (05/08/2026), sulle **580** partite del perimetro:

| | |
|---|--:|
| incrociabili su TUTTI i blocchi | **299 / 580 (51,6%)** |
| idem, escludendo la Coupe de France | **299 / 379 (78,9%)** |
| EFL Cup / FA Cup / DFB-Pokal / Coppa Italia | 100% · 98,4% · 98,4% · 88,9% |
| Copa del Rey | 37,6% (il First Round non ha statistiche individuali) |
| **titolare → la sua statistica individuale** (`player_id`) | **6.489 / 6.600 (98,3%)** |

**Il meteo non esiste per il 2025-26**: zero su 662, e non è «manca in qualche
partita». L'infrastruttura del progetto (`fetch_stadi_coordinate.py`,
`stagione_2026_2027/giornaliero/`) è **prospettica** — raccoglie la *previsione*
a 16 giorni, che all'indietro non si ricostruisce. Per chiuderlo servirebbero:
le coordinate di **363 stadi su 422** (ne abbiamo 59, che coprono 110 partite),
una fonte storica (`open-meteo.com`, raggiungibile e senza chiave), e la
consapevolezza che il risultato sarebbe un **consuntivo `post`**, non la
previsione `pre` che serve a un modello (R8).

**Disponibilità temporale (R8)**: `incrocio_per_partita.csv` è **`statico`** —
descrive la copertura delle nostre tabelle, non la partita.

---

## 5-octies-quater · Il pannello interrogabile delle coppe (`src/data/coppe_query.py`) — Fase 139-novies

Non un file di dati: due **viste denormalizzate** costruite al volo, in cui ogni
riga di misura porta con sé le sue dimensioni (competizione, turno, data,
squadra, avversario, **allenatore**, allenatore avversario, **arbitro**,
divisione, modulo, esito).

| vista | righe × colonne | grana |
|---|--:|---|
| `pannello_squadra(periodo="Totale")` | 746 × 59 | partita × squadra × periodo |
| `pannello_giocatore()` | 9.462 × 134 | partita × giocatore |

Rispondono alle due domande poste dall'utente il 05/08/2026:
`statistiche_allenatore(nome, competizione=…)` e
`statistiche_giocatore(giocatore=…, arbitro=…, competizione=…)`.

⚠️ **Il lato è la chiave, ed è l'errore silenzioso.** `partite.csv` ha
`allenatore_casa`/`allenatore_ospite`, la riga di misura ha `Lato`: attaccare
l'allenatore senza guardarlo mette l'avversario su metà delle righe, e i numeri
restano plausibili. Verificato contro un percorso indipendente
(`allenatori.load_partite()`, che legge `games.csv`): **746/746 concordano**, e
i due allenatori non coincidono su nessuna riga — quindi l'errore sarebbe stato
visibile.

⚠️ **La numerosità va guardata prima della media.** `copertura()` la stampa: in
una stagione di coppa la mediana è **2 partite per allenatore** e **1 per
arbitro**; solo 101 allenatori su 350 arrivano a 3 partite, solo 7 arbitri su
207 arrivano a 5. La query risponde sempre, ma una media su due partite non è
una media.

⚠️ **Il nome non è un'identità** (Fase 140): le chiavi normalizzate uniscono le
grafie della stessa persona, non separano due omonimi. Per gli arbitri non
esiste nemmeno un id.

**Fuori dal pannello**: la Coupe de France (niente `game_id`, quindi niente
arbitro/allenatore da attaccare), le partite fuori perimetro, e i **minuti**,
presenti solo sul 51,7% delle righe giocatore — buco della fonte
(`appearances.csv` porta 5.438 righe su 18.566 di formazione), non del join:
ogni riga di statistica trova il suo giocatore, **9.312 su 9.312**.

**Disponibilità temporale (R8)**: le dimensioni sono `pre` (arbitro e allenatore
si sanno prima), le misure `post`. Il pannello **mescola i due tipi per
costruzione** — è una vista di analisi, non una tabella di feature: chi ne
ricava una feature deve prendere le misure da partite **precedenti**.

---

## 5-nonies · Allenatori e arbitri per partita (`files/player_scores/games.csv.gz`) — Fase 140

`games.csv` del dataset `davidcariboo/player-scores` — la **tabella-cardine**
che il progetto aveva già in licenza e non aveva mai importato. **88.958
partite**, 70 competizioni, dal 2006-06-09 al 2026-07-06; il perimetro delle 5
leghe × 9 stagioni ne conta **16.111**, cioè esattamente le righe degli
snapshot congelati. Vintage: Kaggle **versione 674, 4 agosto 2026** (i quattro
file player-scores più vecchi sono del 18 luglio — impatto misurato in
`files/README.md`: **1 partita su 16.111**).

Si legge da `src/data/allenatori.py`; ogni numero di questa sezione si
ricalcola con `python scripts/_run_fase140_allenatori.py`.

### Le colonne, e quando si sanno (R8)

| colonna | ⏱️ | note |
|---|:--:|---|
| `date`, `competition_id`, `season`, `round`, `stadium` | `pre` | |
| `home/away_club_id`, `_name` | `pre` | |
| **`home/away_club_manager_name`** | **`pre`** | l'allenatore si sa da giorni: è uno dei pochi dati davvero `pre` del progetto |
| `referee` | **`pre`** in teoria (designato ~2 giorni prima), ma qui è letto a partita finita | è la stessa colonna che la Fase 125 usava da uno script una tantum |
| `home/away_club_goals`, `_position` | `post` | `club_position` è la classifica **dopo** la giornata: si usa ritardata |
| `attendance`, `home/away_club_formation` | `post` | `attendance` manca nel 13,3% del perimetro (regime porte chiuse compreso) |
| `aggregate` | — | ⚠️ è la **copia letterale** del risultato in 88.958 righe su 88.958: non è il risultato d'andata e ritorno |

### Copertura (perimetro 5 leghe × 9 stagioni)

| | valore |
|---|--:|
| partite | 16.111 |
| club-partita senza allenatore | **2 / 32.222 (99,994%)** |
| celle `referee` mancanti | 6 / 16.111 |
| allenatori distinti (chiavi normalizzate) | 494 |
| mandati, timeline completa | 1.190 |

L'unica partita senza allenatore è **Nantes-Tolosa del 17/05/2026**: le mancano
anche l'arbitro e ogni presenza. È la coda del vintage, non un difetto
sistematico.

### ⚠️ Tre trappole misurate — tutte «finti pieni» (R6)

1. **Il nome non è un'identità.** Non esiste un id-allenatore: solo una stringa
   libera. `normalizza_nome` unisce le due grafie dello stesso uomo (496 grafie
   → 494 chiavi nel perimetro; 7.031 → 6.995 globali) ma **non separa gli
   omonimi**. Il test di impossibilità fisica — nessuno allena due club lo
   stesso giorno — ne trova **11 globali**, di cui **2 nel perimetro**:
   `michel` (Míchel Sánchez e Míchel González: il 2022-10-02 Girona e
   Olympiakos) e `luis castro`. `conflitti_identita()` li elenca; scioglierli
   richiede una fonte di identità esterna, che questo strato non ha.
2. **`manager_name` è chi sedeva in panchina quella partita**, non chi era in
   carica. Il pattern `A → X → A` (vice per una gara: squalifica, malattia,
   turno di coppa) vale **836 mandati su 13.810**, 412 dei quali di una partita
   sola. `panchine()` li marca sempre (`interruzione`) e li riassorbe su
   richiesta (`ricuci=True`).
3. **L'esperienza è visibile al dataset, non globale.** Il file per le top-5
   comincia il **2012-08-10** e i campionati extra-europei entrano nel **2025**:
   Ancelotti «esordisce» in Ligue 1 nel 2012, Mourinho in Liga nel 2012.
   `esperienza_prima()` restituisce `censurata`, e ⚠️ `censurata=False` **non**
   vuol dire esperienza completa (Guardiola: flag False, quattro stagioni al
   Barcellona invisibili).

### Da NON usare

**`clubs.coach_name`** (in `files/player_scores/clubs.csv.gz`, 403/796 non
nulli) è l'allenatore **corrente** del club, senza data. Su una partita del
2019 le attribuisce il tecnico di oggi: trappola R8 pura. `src/data/allenatori.py`
non la legge, e non va letta.

**`club_games.csv.gz`** è un **duplicato esatto e algoritmico** di `games.csv`
(0 celle divergenti su 1.957.076, ricostruito in otto righe). Conservato per la
regola §5-ter, non perché serva; il suo `is_win` è per giunta **lossy** — i
38.604 pareggi sono codificati come le 69.656 sconfitte.

**Stato d'uso: raccolto e strutturato, non usato da nessun modello.**

---

## 5-undecies · Le sette coppe del 13/08/2026 e i coefficienti UEFA (Fase 155)

**Sette raccolte nuove** in `files/`, formato delle raccolte a tre fonti:
`tre_fonti_uefa_champions_league_2526` (281 partite, 82 squadre di cui **23
nostre**, 2 fonti, 294.667 eventi Opta) e le **sei supercoppe**
(`supercoppa_uefa`, `supercoppa_italiana`, `supercopa_espana`,
`community_shield`, `dfl_supercup`, `trophee_des_champions`): 10 partite,
**tutte di squadre nostre**. Italia e Spagna sono a *final four*, non a partita
secca. Conversione dai CSV consegnati verificata **cella per cella, 0
divergenti**. Si leggono con `src/data/tre_fonti.py`.

### ⚠️⚠️ La convenzione sul PUNTEGGIO non si eredita fra raccolte

| raccolta | `Gol casa/trasferta` | colonne derivate | riparazione |
|---|---|---|---|
| Europa League | **somma i rigori** (7 partite) | ❌ assenti | in lettura |
| Conference | **somma i rigori** (6 partite) | ✅ presenti | dall'export |
| Champions | pulito (4 partite ai rigori) | — | nessuna |
| 6 supercoppe | pulito (4 partite ai rigori) | — | nessuna |

Non si deduce dal torneo (sono tutte UEFA), né dalla fonte (è sempre SofaScore),
né dalla presenza dei rigori. **Si misura per raccolta**:
`python scripts/_run_punteggio_coppe.py`; la tabella è `tf.RIGORI_NEL_PUNTEGGIO`.

⚠️ **Applicare la riparazione dove non serve non è innocuo**: sulla finale di
Champions (1-1, rigori 4-3) darebbe **1 − 4 = −3**.

Le prove: `Gol − Rigori` = gol contati negli **eventi** su **14/14** (EL) e
**12/12** (Conference) contro 1/14 e 0/12 del grezzo; sulle **1.334**
squadra-partita senza lotteria `Gol` = eventi **1.334/1.334**; identità dei tempi
**281/281** (Champions) e **10/10** (supercoppe), con 8 partite ai rigori dentro
il campione; e la sottrazione riproduce la colonna derivata della Conference
**12/12**.

⚠️ **Contare i gol negli eventi non è banale**: i rigori **segnati** sono
`Tipo=Gol` con `Sottotipo=penalty`, mentre `Tipo=Rigore` esiste **solo** come
`missed`. Sommarli conterebbe come gol un rigore fallito.

### Le supercoppe: cinque su sei hanno UNA fonte

Solo la Supercoppa UEFA ha SofaScore + WhoScored (e `eventi_opta`). Le altre
cinque portano **19 colonne `(WhoScored)` completamente vuote**: lo schema le
prevede, la consegna non le riempie. `tf.fonti()` dice quali fonti coprono
davvero. Le colonne vuote sono 41-43 in tre famiglie — WhoScored assente, tempi
supplementari non giocati, classifica inesistente in una supercoppa — tutte
dichiarate in `tf.colonne_vuote()`, con un test in **entrambe** le direzioni.

### I coefficienti UEFA — `data/ranking_uefa/`

`coefficienti_uefa_2026-08-12.xlsx` come consegnato (fonte uefa.com, 12/08/2026
19:55). Si legge con **`src/data/ranking_uefa.py`**, mai con `pd.read_excel`.

**Disponibilità temporale: `statico`, ma con una data.** ⚠️ Il file contiene
**due finestre** di coefficiente per federazione (21/22→25/26 e 22/23→26/27) che
decidono due access list diverse. `federazioni()` **non ha un default**: usare il
coefficiente di oggi per prevedere una partita di ieri è look-ahead, perché quel
numero incorpora il risultato che si vuole prevedere (R8).

**A cosa serve davvero**: dà il **paese** a **331** club agganciati, di cui
**168 senza campionato domestico** nel dataset — il buco misurato alla Fase 154.
I 79 non agganciati sono in gran parte le abbreviazioni UEFA dei club *più
grandi* (`Atleti`, `B. Dortmund`, `Bayern München`), che sono già nostri.

⚠️ **Il coefficiente di club non misura sempre il club**:
`MAX(somma 5 stagioni; 20% della federazione)`, verificato **410/410**. Il
pavimento **morde su 146 club (35,6%)**: per loro il numero è una proprietà del
**paese**. `pavimento_attivo()` lo dice riga per riga.

⚠️ **Un aggancio falso trovato da un invariante** («un `club_id`, un paese
solo»): *Bohemians* (Irlanda) e *Bohemians Praha* (Cechia) finivano entrambi sul
`club_id` 715, che è il ceco. Riparato con `ALIAS_PER_PAESE` — e qui la
riparazione è **sicura** perché questa fonte porta il paese: un dato in più che
toglie un errore invece di aggiungerne.

**Stato d'uso: raccolto e strutturato, non usato da nessun modello.**

---

## 5-decies · L'identità di un CLUB in player-scores, e i club fuori dai nostri 5 campionati (Fase 154)

Misurato da `scripts/_run_anatomia_club.py`. La procedura operativa completa —
che cosa si fa quando entra un club che non è nei nostri campionati — sta in
**`docs/CLUB_FUORI_PERIMETRO.md`**; qui restano solo i fatti sulle colonne.

**Due file parlano di club, e non sono intercambiabili.**

| file | righe | disponibilità | contenuto |
|---|---:|---|---|
| `club_names.csv.gz` | 3.173 | statico | il **registro**: `club_id`, `name`, `domestic_competition_id` |
| `clubs.csv.gz` | 796 | statico | il **contesto**: rosa, età media, stadio, valore, `coach_name` |

⚠️ **Le coperture si misurano per COLONNA, non per file.** Nel registro il
**nome** è pieno su 3.173/3.173 (100%), il **campionato domestico** su
**796/3.173 (25,1%)** — e sono esattamente i club che stanno in `clubs.csv`.
Dire «il file giusto è `club_names`» è vero per il nome e falso per la lega.

**`domestic_competition_id` — disponibilità `statico`, e va letto per quello che è.**
Non è «la lega di oggi» né «la lega di quella stagione»: è *l'unico dei 32
campionati coperti in cui quel club è mai apparso*. Misurato: **0 club su 793**
hanno partite in più di un campionato domestico, **0** hanno un'etichetta che
contraddice le proprie partite, e i 39 club che hanno giocato in Serie A sono
etichettati `IT1` tutti e 39, anche con `last_season` 2013. Non mente mai, ma
**non risponde** a «in che serie era nel 2019»: per quello serve `games.csv`.

**Che cosa esiste per un club a seconda di dove gioca.** 3.274 `club_id` hanno
giocato almeno una partita:

| | club | partite | formazioni | presenze gioc. | anagrafica gioc. | `clubs.csv` |
|---|---:|---:|---:|---:|---:|---:|
| nei nostri 5 campionati | 176 | 61.104 | 92,0% | 851.904 | 100% | 176/176 |
| negli altri 27 coperti | 617 | 92.752 | 91,4% | 1.031.384 | 100% | 617/617 |
| **fuori** | 2.481 | 24.060 | 85,6% | 11.062 | 100% | **0**/2.481 |

Fuori perimetro **non mancano i fatti**: mancano l'etichetta di lega e il
contesto. E i 2.481 sono **quattro famiglie**: 109 **nazionali** (vivono nello
stesso spazio dei `club_id`), 104 **orfani** (giocano, non sono nel registro, e
`home_club_name` è vuoto su quelle righe), **1.997** col paese **deducibile dal
dato** perché giocano una coppa nazionale (0 ambiguità su 1.997), **375** senza
alcun paese ricavabile.

⛔ **La lega dei club fuori perimetro non è deducibile**: giocano **0** partite
di campionato domestico. Non è un buco da tappare, è il perimetro della fonte.

**R4 — cinque `competition_id` di `games.csv` non esistono in `competitions.csv`**:
`CGB` (246 partite), `COL1` (200), `KLUB` (156), `POCP` (602), `UKRS` (10).
`COL1` è anche l'unico codice usato come etichetta di lega senza riga
anagrafica: i campionati **usati** sono 32, quelli **anagrafati** 31.

**Aggancio dei nomi (`src/data/club_matching.py`).** Su un universo di 3.339
nomi (registro + 5 snapshot + coppe 2025-26 + Smarkets): **3.279 univoci, 50
ambigui, 10 assenti**. Il pericolo non sono gli ambigui e gli assenti — quelli
si vedono — ma gli **univoci sbagliati** (R6). Due riparati alla Fase 154:
`Espanol` (puntava a un club di Tercera División su 266 partite di La Liga) e
`Red Star FC` (puntava al Belgrado). Misura di controllo indipendente, la
ricomposizione snapshot↔`games.csv` su (data, `club_id` casa, `club_id`
trasferta): **15.839 → 16.105 su 16.111** (98,31% → 99,96%). I **6** residui
sono slittamenti di ±1 giorno con squadre e punteggio identici, e i **2** scarti
di punteggio sono i casi R1 già noti.

**Stato d'uso: usato** — `club_matching` è il ponte fra i nomi delle nostre
fonti e i `club_id` di player-scores (carriere, coppe, Smarkets).

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
python scripts/build_new_snapshot.py                           # snapshot 40 colonne + calendari
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
