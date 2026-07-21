# Protocollo di lavoro — istruzioni per l'AI (e per chiunque contribuisca)

Questo file definisce **come si lavora su questo progetto** e soprattutto **cosa
scrivere/aggiornare ogni volta**. Una sessione AI in questa repo lo legge
all'avvio: seguilo. Lo scopo è che il metodo, i risultati e il ragionamento non si
perdano mai tra una sessione e l'altra, e che tutto resti replicabile da terzi.

Se aggiorni il modo di lavorare, aggiorna **anche questo file**.

---

## 1. Principi metodologici (non negoziabili)

1. **Tracer bullet prima dei moduli** — prima una fetta verticale reale
   end-to-end, poi si raffina.
2. **Una cosa alla volta, e si misura** — cambia un solo fattore per esperimento;
   altrimenti non sai *cosa* ha funzionato.
3. **Testa la versione economica di un'idea prima di investire** — non costruire
   infrastrutture costose su assunzioni non verificate.
4. **Documenta anche i risultati negativi** — valgono quanto quelli positivi.
5. **Riproducibilità** — ogni numero dev'essere rifacibile da terzi (stesso
   codice, stessi dati, stessa config).
6. **Onestà sui limiti** — ci sono soldi veri in gioco: niente promesse di edge,
   sempre le avvertenze quando il modello non batte il mercato.
7. **Valida su più stagioni** — mai concludere da una sola stagione (rumore).
   Default: 3+ stagioni; per conclusioni importanti, 6.
8. **Il bersaglio è la predizione del SINGOLO mercato, non un modello unico
   "bello".** L'obiettivo del progetto è stimare bene le probabilità di *ogni*
   evento (1X2, Over/Under, GG/NG, doppie chance…), preso uno per uno. Finora
   c'è **un solo modello** (Dixon-Coles) da cui si derivano tutti i mercati
   dalla stessa matrice dei punteggi: ha il pregio della **coerenza interna**
   (P(1X)=P(1)+P(X) vale sempre) ma **non è un obbligo**. Un modello può essere
   ottimo su un mercato e mediocre su un altro — è già successo (Fase 5: il DC
   è forte su 1X2/1X/2X ma **peggio della baseline su GG/NG**, perché cattura
   male la *correlazione* dei punteggi). Quindi:
   - **valuta e seleziona i modelli PER MERCATO**, non solo sul log-loss 1X2
     aggregato. Un modello che vince sul GG/NG ma perde sull'1X2 è comunque una
     vittoria *su quel mercato*;
   - è legittimo che la config "ufficiale" diventi un **portafoglio di
     specialisti** — un `dict {mercato: modello_migliore}` — invece di un modello
     unico. Metti in conto che così si **perde la coerenza tra mercati** (le
     probabilità di modelli diversi non si sommano più in modo consistente): è
     un trade-off da fare **consapevolmente**, accettabile se il bersaglio è la
     bontà per-caso e non un prezzo arbitrage-free su tutti i mercati insieme;
   - alcuni mercati sono più promettenti di altri per un modello nuovo: il
     **GG/NG non ha quote nei dati** (football-data non le include), quindi è
     l'unico dove non possiamo dimostrare l'efficienza del mercato — l'unico con
     "spazio" non ancora chiuso dai risultati Fasi 14/16/20. Priorità lì.
   - **Mercati standard = Tier 1** (d'ora in poi): 1X2, O/U 1.5/2.5/3.5, GG/NG,
     doppie chance, total-squadra (casa/ospite O0.5/1.5), clean sheet, vince-a-zero,
     scarto ≥2, multigol, risultato esatto. Ogni backtest/analisi li copre tutti
     (`scripts/_run_markets_bakeoff.py`, `derive_markets`). Tier 2 (handicap
     asiatico) e Tier 3 (HT/FT, tempi → fondazione live) in futuro.
   - **Esito del bakeoff (Fase 41):** il "portafoglio di specialisti" NON è 20
     modelli bespoke — **collassa a UN motore**: il **market-implied** è il migliore
     su 19/20 mercati Tier 1 (il DC-da-gol non vince mai), perché i mercati sono
     proiezioni della stessa matrice e i λ,μ del mercato battono i nostri ovunque.
     L'unico "specialista" aggiuntivo è la **φ(|λ−μ|)** (Fase 35/39) sulla
     famiglia-pareggio. Regola operativa: **market-implied + φ35 quando ci sono le
     quote 1X2+O/U; DC come fallback senza quote.** Il **Poisson bivariato** (Fase 42,
     5° modello) è stato implementato e **perde** vs la φ35 (l'equilibrio |λ−μ| batte
     la correlazione globale λ3, che peggiora i totali). Il **ML bespoke per singolo
     mercato è stato testato e CHIUSO (Fase 50-quater)**: perde su ogni mercato e su
     entrambi i path, anche con la predizione dell'engine tra le feature. La miglior
     stima GG/NG (opt-in, non conclusa) è: market-implied → ricalibrazione-μ
     walk-forward → φ(|λ−μ|) (Fase 50, GG 0.6810); il nudge stagionale della Fase 48
     vale SOLO sul path DC (il mercato prezza già il finale — Fase 50-bis).
     **Fase 51:** i gol dati i tassi del mercato sono **SOTTO-dispersi** (double-
     Poisson θ≈1.2 — l'asse che la binomiale negativa della Fase 27 non copriva);
     `sharpen_1x2` (θ + livelli dei tassi) **batte la chiusura devigata sull'1X2 in
     log-loss con CI conclusivo** (0.9609 vs 0.9625, 7/7 stagioni) ma NON in ROI
     (affinamento ≪ margine). Rue-Salvesen, zero-inflazione, GBM-pareggio e recal
     O/U: testati e chiusi (Fase 51). **Fase 52:** la dp e' robusta e generale
     (θ uniforme nel contesto; presente nell'APERTURA, θ_open=1.218 — e l'open
     affinato VALE la chiusura grezza; regge sui tassi DC, θ_DC=1.138) ma il suo
     perimetro e' la famiglia-esiti: l'O/U 2.5 NON si batte (il devig binario resta
     il migliore) e la tripla GG satura. Contro il devig di Shin (migliore del
     moltiplicativo) l'edge dp_lvl scende a −0.0009 (93%, non concluso). **Router
     v3 ADOTTATO** (`price_markets(dp_theta)`: dp su tutto il listino, mai peggiore,
     5 CI conclusivi; θ=1.225 mercato / 1.138 DC). Lo state-space e' chiuso PER
     TEST (GAS perde dal DC batch, +0.0027). **Fase 53 (tracer cross-lega, bundle
     utente in files/):** θ>1 anche su Premier (1.069) e La Liga (1.097) ma
     DECRESCE con la liquidità; tilt e draw-bias NON si replicano (Premier:
     pareggi sovra-prezzati, ROI pari-equilibrio −5.4%); **dp_lvl non batte la
     chiusura fuori dalla Serie A** anche rifittata → il beat-the-close è una
     proprietà della chiusura Serie A (meno liquida), non del calcio. Le costanti
     del motore restano dichiaratamente per-lega (§7). Aperto: port completo DC
     su Premier/Liga coi bundle Understat (Fase 53-bis).
9. **Ogni modello si sviluppa su DUE FRONTI e si traccia nella rosa (Fase 65).**
   Per ogni modello/leva vanno considerate e valutate DUE versioni:
   - **per-lega**: costanti/iperparametri ritarati sulla singola lega (es. DC
     Serie A con δ=0.23, DC Premier con δ=0.33);
   - **generale**: versione unica cross-lega (pooled/universale — es. lo
     stimatore E3 pooled della Fase 62-bis, che ha BATTUTO le versioni
     per-lega; o gli iperparametri del DC, di fatto generali dopo la Fase 57).
   Nessuno dei due fronti è "quello giusto" a priori: si misura (a volte vince
   il pooled, a volte il segno NON è universale — es. draw-bias, Fase 53).
   Lo stato di ogni modello su ogni fronte (titolare/panchina/bocciato/mai
   testato) vive nella **matrice di `docs/PANCHINA.md`** ("la rosa dei
   modelli"), da aggiornare a ogni esperimento.

---

## 2. Cosa scrivere OGNI VOLTA (checklist di aggiornamento)

Dopo **ogni backtest / tuning / esperimento significativo**, prima di chiudere:

- [ ] **Registro esperimenti** — verifica che il run sia finito in
  `experiments/runs.jsonl` (backtest.py e tune.py lo fanno in automatico:
  config + metriche + commit git + impronta dati + timestamp). Se hai fatto un
  esperimento "a mano", registralo comunque via `experiment_log.append_run`.
- [ ] **Diario di bordo** (`docs/DIARIO.md`) — se l'esperimento ha prodotto una
  *decisione* o una *scoperta* (non ogni singola run), aggiungi/aggiorna una voce
  con questa struttura:
  1. **obiettivo** della fase;
  2. **ragionamento / ipotesi**;
  3. **alternative** considerate;
  4. **scelta** e perché;
  5. **risultato** (numeri, anche se negativo);
  6. **lezione / cosa ne consegue**;
  7. **📐 Il modello in dettaglio (OBBLIGATORIO, vedi §2-bis)** — la/le formula/e
     esatta/e coinvolte e il ragionamento numerico sul *perché* ogni variabile o
     iperparametro assume quel valore.
- [ ] **README — «Registro completo dei risultati»** (OBBLIGATORIO, SEMPRE).
  Il README contiene una sezione **«Registro completo dei risultati — ogni analisi,
  in un colpo d'occhio»**: è il punto UNICO e accessibile dove **chiunque** deve
  poter vedere i numeri chiave di **OGNI** backtest e analisi, senza leggere il
  diario o il codice. **Dopo ogni esperimento significativo — positivo, negativo o
  "nel rumore" — aggiungi lì la riga corrispondente** (nella tabella degli
  esperimenti e, se serve, nelle tabelle del gap/evoluzione). Nessuna analisi può
  restare fuori da questo registro. Se cambia la config ufficiale, aggiorna anche
  la riga di stato e la roadmap.
- [ ] **Rosa dei modelli** (`docs/PANCHINA.md`) — il registro di TUTTI i
  modelli in tre stati (⚽ titolari / 🪑 panchina / ❌ bocciati) su DUE fronti
  (per-lega e generale, principio 9). Dopo ogni esperimento che tocca lo stato
  di un modello: aggiorna la cella della matrice (lega × fronte) e la voce
  della sezione corrispondente (numeri, motivo, attivazione, condizioni di
  promozione); modello nuovo → riga nuova; promozione/bocciatura → voce
  spostata di sezione, archivio in fondo con data e motivo. Il file deve
  restare SEMPRE allineato.
- [ ] **Test** — mantieni `pytest` verde; aggiungi un test per ogni nuova
  funzionalità del modello/pipeline.
- [ ] **Piste** (`docs/PISTE.md`) e **manuale di sopravvivenza**
  (`docs/MANUALE_SOPRAVVIVENZA.md`) — se l'esperimento apre, prova o chiude
  una pista dati→modello, aggiorna la voce corrispondente in PISTE.md (anche
  l'esito negativo, principio §1.4); se scopri un fatto operativo nuovo
  sull'ambiente (rete, strumenti, GitHub Actions), aggiungilo al manuale.
- [ ] **Commit + push** — messaggio chiaro (cosa e perché), sul branch di
  sviluppo. Non lasciare mai lavoro non committato: il container è effimero.

Regola pratica: **il registro `runs.jsonl`** cattura *ogni* run (dati grezzi); **il
diario** cattura le *decisioni e il perché* (narrazione); il **README** è lo stato
*corrente* sintetico E il **«Registro completo dei risultati» leggibile da tutti** —
va **sempre** aggiornato: chiunque apra il README deve vedere l'esito di ogni analisi.

---

## 2-bis. STANDARD «formule + ragionamento» (NON negoziabile, vale SEMPRE)

Ogni fase del diario e ogni spiegazione di modello **deve** contenere un blocco
**«📐 Il modello in dettaglio»** che rende esplicito ciò che prima restava
implicito. Non basta la narrazione del *cosa*: serve il *come* (la matematica) e il
*perché quel numero*. Requisiti minimi del blocco:

1. **La formula esatta**, in un blocco di codice, **verificata riga per riga contro
   il codice sorgente** (`src/…`) — mai a memoria, mai inventata. Se una fase non
   introduce nuova matematica, richiama la formula rilevante già definita altrove
   (es. "blend: vedi Fase 3") e spiega come si applica qui.
2. **Il ragionamento numerico sul valore di ogni variabile/iperparametro.** Non
   "δ ≈ 0.23" ma "δ = ln(1.36/1.08) = 0.230, il log del rapporto-gol osservato".
   Se un valore è scelto per griglia/ottimizzazione, dillo e spiega il compromesso
   (bias-varianza, ecc.); se è fittato, indica come e su quali dati.
3. **Onestà esplicita dove un numero NON è ri-derivabile** dai dati/registro: si
   scrive che non lo è (es. l'"87%" della Fase 2a), non lo si inventa né lo si
   lascia sottinteso.
4. **Coerenza col registro**: ogni numero citato deve essere ricalcolabile da
   `runs.jsonl` o da uno script `_run_*` (regola Fase 15).

Questo standard è retroattivo (tutte le fasi 0-33 lo rispettano) e prospettico:
**nessuna fase futura è "chiusa" senza il suo blocco 📐.** Lo stesso vale quando si
porta il modello su un'altra lega: le formule non cambiano, ma il *ragionamento sul
perché di ogni numero* va rifatto per i dati di quella lega (vedi §7).

---

## 3. Come si esegue (comandi principali)

```bash
python scripts/build_database.py       # (ri)costruisce il DB dallo snapshot (offline)
python scripts/build_database.py --fixtures  # calendario di club completo + congestione vera (Fase 4e)
python scripts/build_database.py --refresh   # riscarica dalle fonti, aggiorna lo snapshot
python scripts/backtest.py             # backtest walk-forward (registra il run)
python scripts/backtest.py --test-season 2425 --shots-blend 0.5   # varianti
python scripts/analyze.py              # analisi errori del backtest
python scripts/tune.py --sweep shrinkage --values 0 1 1.5 3       # tuning iperparametro
python -m pytest                       # test
```

Config "ufficiale" corrente del modello (default in `backtest.py`): **emivita
365g, shrinkage 1.5, shots_blend 0.75, blend_signal xg, promoted_prior 0.23**
(blend gol/xG reale, Fase 4b; emivita ri-tarata a 365g in Fase 4d; prior di
cold-start neopromosse adottato in Fase 7/8). Se la cambi, aggiorna README e diario.

---

## 3-bis. Git — branch di lavoro

- **Commit e push SOLO sull'ultimo branch di lavoro usato nella sessione**
  (quello su cui si è già committato/lavorato, es. `claude/data-review-2hu63v`).
- **Creare un nuovo branch SOLO se esplicitamente richiesto** dall'utente. In
  assenza di indicazioni, si resta sul branch corrente: niente branch nuovi
  "per prudenza" o per separare un sotto-task.

---

## 4. Mappa del repo (dove sta cosa)

```
src/config.py    iperparametri PER LEGA (LEAGUE_CONFIGS) = fonte unica (§7); nuova
                 lega = nuova voce, non codice
src/data/        sources.py (URL/stagioni/alias), loader.py (offline-first),
                 database.py (snapshot CSV + SQLite)
src/models/      dixon_coles.py (il modello: _fit_counts, blend, predizione,
                 draw_balance Fase 35 = phi(|lam-mu|))
                 market_implied.py (Fase 24/26: inverte le quote 1X2+O/U ->
                 lambda,mu del mercato -> matrice DC -> ogni mercato sui gol;
                 price_markets Fase 44 = routing forma per-mercato; btts_season Fase 48
                 = nudge stagionale GG/NG di fine stagione, off di default)
                 market_denoise.py (Fase 38/Punto 4: power-devig + recal cross-stagione)
                 bivariate_poisson.py (Fase 42: correlazione esplicita λ3; perde vs φ35)
                 copula_scores.py (Fase 43: copula di Frank, dip. flessibile; tetto = φ35)
src/evaluation/  metrics.py (Brier/log-loss/devig), analysis.py (analisi errori),
                 calibration.py (temperature scaling post-hoc, Fase 6),
                 experiment_log.py (compute_metrics = FONTE DI VERITA' unica; registro)
scripts/         download_data, build_database, backtest, analyze, tune, calibrate,
                 markets (multi-mercato), analyze_gap (anatomia del gap col mercato)
experiments/     runs.jsonl (registro replicabile) + README (formato)
data/            serie_a_matches.csv (SNAPSHOT congelato, versionato)
                 football.db (SQLite, rigenerabile, NON versionato)
docs/DIARIO.md   narrazione passo-passo con ragionamento (le decisioni e il perché)
docs/DATI.md     catalogo di TUTTI i dati (reali e stimati): copertura, semantica
                 quote, fonti, stime dichiarate — aggiornare a ogni modifica dati
docs/PANCHINA.md la rosa dei modelli: titolari/panchina/bocciati × 2 fronti (§1.9)
docs/PISTE.md    idee dato/architettura -> modello NON ancora provate, per costo
                 crescente; aggiornare quando una pista si apre/prova/chiude
docs/MANUALE_SOPRAVVIVENZA.md   conoscenza operativa dell'ambiente (rete
                 raggiungibile, limiti degli strumenti MCP, fatti su GitHub
                 Actions, fonti esterne valutate/scartate)
docs/CACCIA_OU_2017_19.md   piano dedicato per l'ultimo buco dati reale (O/U
                 apertura 2017-19)
tests/           test unitari
```

---

## 5. Convenzioni sui dati

- **Offline-first**: la pipeline legge lo **snapshot congelato**
  (`data/serie_a_matches.csv`, versionato). Si scarica dalle fonti solo con
  `--refresh`/`force_download`. Così i backtest sono riproducibili identici.
- **Fonte configurabile in un punto solo** (`src/data/sources.py`): URL, stagioni,
  alias dei nomi squadra (`TEAM_ALIASES` — es. "Hellas Verona" → "Verona": bug
  reale già capitato, attenzione ai nomi quando si aggiunge una fonte).
- **Aggiungere una nuova fonte/feature**: normalizza nello schema interno del
  loader, aggiorna lo snapshot/DB, e allinea i nomi squadra/partita tra le fonti
  (join per data + squadre). Fai guidare lo schema dai dati reali, non da ipotesi.
- **Metriche**: calcolale SEMPRE via `experiment_log.compute_metrics` (fonte
  unica), mai reimplementarle altrove.
- **STIME dichiarate** (Fase 62-bis): dove un dato di mercato NON esiste nelle
  fonti, può essere stimato coi nostri modelli ma vive SOLO in
  `data/estimates/` (mai nelle colonne quota degli snapshot), come
  PROBABILITÀ (mai quote), con errore atteso validato in backtest e
  dichiarato. Ogni analisi che usa una stima lo dichiara; mai usarle per
  simulare ROI. Regole in `data/estimates/README.md`; catalogo completo di
  tutti i dati (reali e stimati) in **`docs/DATI.md`** — da aggiornare a ogni
  modifica dei dati. Stimare ALTRI dati mancanti (es. squad_value Liga) è un
  lavoro futuro previsto: stesso protocollo (backtest di fedeltà prima).

---

## 6. Stato corrente e prossimi passi

Vedi `docs/DIARIO.md` per la storia completa e `README.md` per lo stato sintetico.
In breve: modello Dixon-Coles sui soli gol, tarato; **batte le baseline ma non il
mercato**; i tiri in porta grezzi non aiutano (verificato su 6 stagioni).
**Fase 4a-4e completate:** dati arricchiti (xG/npxG/PPDA/deep, valori rosa,
assenze); config ufficiale = blend gol/**xG reale** (α=0.75) + emivita ri-tarata
a **365g** (Fase 4d: col blend xG conviene memoria piu' corta). npxG≈xG; valori
rosa, assenze e riposo-solo-SerieA (anche in combo) **non aiutano** out-of-sample
(gia' impliciti in gol+xG, o confusi con la forza): il modello e' al **tetto
pratico** dei dati attuali. Esiste un layer covariate (off di default) per dati
futuri davvero indipendenti (es. calendario di club completo per la congestione).
**Fase 4e:** aggiunto il **calendario di club completo** (coppe+Europa via
openfootball) → colonne `home/away_rest_days_full` e `home/away_midweek_europe`
nello snapshot + tabella grezza `data/club_fixtures.csv`. E' la **congestione
vera** (il proxy solo-lega non la vedeva). **Fase 4e-bis:** validata la covariata
`rest_full` walk-forward (2020-25): inverte il segno del proxy solo-lega ma il
guadagno e' nel rumore (−0.0004 medio) → covariata off di default.
**Fase 6:** ricalibrazione confidenza (temperature scaling, `scripts/calibrate.py`):
il modello e' un po' **sottoconfidente** (T≈0.94, robusto) ma il guadagno e'
trascurabile (−0.0003) → non entra nella config; modulo `src/evaluation/calibration.py`
per l'uso pratico. **Fase 7:** **prior di cold-start neopromosse**
(`--promoted-prior`, δ≈0.23 stimato leave-future-out): sposta il bersaglio dello
shrinkage sotto la media per le squadre senza storico. **Miglior guadagno interno**
(−0.0011 medio, −0.0039 sulle partite delle promosse, 5/6 stagioni): **ADOTTATO
nella config ufficiale** (δ=0.23). **Fase 8 (ultimo giro economico, NEGATIVO):**
ri-taratura shrinkage col prior = curva **piatta** 0.75-1.5 (leve ortogonali,
nessun guadagno); vantaggio-casa per-squadra = **persistenza anno-su-anno r≈0.00**
(solo rumore stagionale, non generalizza) → niente da spremere.
**Fase 9:** anatomia del gap col mercato (`scripts/analyze_gap.py`): gap 1X2 medio
+0.0165, **quasi tutto nel PAREGGIO** (il mercato 12 senza pari e' gia' a livello
mercato); varia per stagione (peggio COVID 2020-21) e a U per forza-squadra.
**Fase 10:** ricalibrazione per-classe 1X2 (`scripts/_run_class_recal.py`):
conferma robusta casa-sovrastimata/pari-sottostimato ma guadagno nel rumore
(−0.0005) → off. **Fase 11:** griglia combinazioni feature off-di-default
(`scripts/_run_combo_analysis.py`): **nessuna combo utile** (squad_value peggiora,
absence/rest_full rumore; l'unico effetto additivo e' la ricalibrazione gia' nota).
**Fase 12:** ensemble emivite (blend 180+730 = −0.0006, borderline) e il **cambio
di classe** — modello a **diagonale inflazionata** (`--draw-inflation`, Fase 12b):
alza i pareggi oltre la correzione DC, fittato sui punteggi. Migliora la
calibrazione del pareggio ma il log-loss guadagna solo −0.0004 (3/6): *quanti*
pareggi capitano e' rumore. **Il pareggio e' quasi-casuale per tutti (mercato
incluso)** → il gap non e' cattiva modellazione ma info che il mercato ha. 7
esperimenti convergono: **tetto REALE**, non solo pratico. draw_inflation off di
default. **Fase 13:** stato di forma (`add_form`, covariata `form`,
`scripts/_run_form.py`): la forma NON predice l'errore del modello (corr +0.035) e
come covariata peggiora (+0.0002) → gia' catturata dal fit pesato nel tempo,
nessun pattern nascosto (8 esperimenti convergenti). **Fase 14 (linea di APERTURA + CLV,
NEGATIVO):** snapshot esteso con le quote pre-chiusura `*_open` (CSV originali
football-data congelati in `data/football_data_raw/`; il mirror storico di sources.BASE_URL e'
SPARITO da GitHub → `--refresh` senza fonte a monte;
`scripts/_restore_raw_cache.py` ricostruisce la cache). Il modello NON batte
nemmeno l'apertura (gap 1X2 +0.0146, 6/6 stagioni; affilamento open→close solo
+0.0020) e il CLV e' negativo (−0.0028, 45%>0; ROI@open −17.3%): i dissensi del
modello dalla linea del venerdi' sono rumore. "Scommetti presto" e' chiusa;
resta non testabile solo l'apertura vera (serve raccolta prospettica di quote). **Fase 15 (audit dei calcoli):** ogni numero di
README/DIARIO ricalcolato dal registro; formule tutte corrette, walk-forward
pulito, backtest ufficiale riprodotto identico. UN errore vero trovato e
corretto: il ROI del value betting era **−15.7%** (media 6 stagioni, config
ufficiale), non il −8.5% (valore Fase 1) rimasto nel README. Corrette sbavature
(O/U 0.6885, ~86%, baseline 1.0834, tabella 2b del diario) e dichiarati i limiti:
baseline in-sample (ex-ante onesta: 1.0860/0.6961, battuta comunque), costanti
RECAL_W/δ fisso col senno di poi negli script 10-12, gap identico su stagioni
pulite (+0.0164) e di tuning (+0.0166) → nessun overfitting di selezione.
Registrate nel registro le run mancanti (Fasi 11/12a/13); regola: **nessuna
analisi senza run in `runs.jsonl`**. **Fase 15-bis:** matrice gap per mercato ×
stagione (`scripts/_run_gap_markets.py`): il 12 (no pari) e' a livello mercato
in OGNI stagione (−0.0021…+0.0050), il costo del pareggio e' strutturale
(1X/2X +0.008…+0.018 sempre), l'O/U e' il mercato piu' volatile (−0.0031…
+0.0168: il gap medio +0.0069 ha poca sostanza operativa). **Fase 16
(encompassing, definitivo):** blend α·modello+(1−α)·mercato walk-forward
(`scripts/_run_encompassing.py`): **α*≈0 ovunque, perfino in-sample** → il
mercato di chiusura ingloba completamente il modello, nessuna informazione
propria da combinare (converge col CLV negativo della Fase 14). **Fase 17
(CI bootstrap):** bootstrap appaiato B=10.000
(`scripts/_run_gap_uncertainty.py`): gap 1X2 +0.0165 [+0.0106,+0.0225] e O/U
+0.0069 [+0.0022,+0.0116] REALI; gap 12 +0.0020 [−0.0006,+0.0046]
statisticamente zero; Δ prior −0.0010 [−0.0025,+0.0004] probabile (~93%) ma
non conclusivo — resta adottato per coerenza e motivazione strutturale, va
dichiarato "probabilmente utile". Disciplina multiple-testing: dopo ~30 test
sulle stesse 6 stagioni, un CI che sfiora lo zero = "non concluso".
**Fase 18 (rho dinamico, NEGATIVA con regola pre-dichiarata):** correzione sui
punteggi bassi per-partita (`--dynamic-rho`): rho_slope instabile (cambia
segno, sbatte sui bound) e Δ +0.0003 [−0.0007,+0.0013] → off; terza e ultima
via strutturale sul pareggio chiusa (dopo Fasi 10 e 12b). **Fase 19 (potenza
sul prior):** finestra estesa alle stagioni 1819/1920 (mai usate) → 8
stagioni: Δ prior −0.0013 [−0.0026,+0.0001], P(aiuta) 96.5% (97% sulle
promosse); entrambe le stagioni nuove confermano → prior confermato, etichetta
da "probabile" a "molto probabile, formalmente non concluso".
**Fase 20 (anatomia dei residui):** regressione del residuo del modello su 11
covariate pre-partita, incluse tre di estremità mai provate
(`scripts/_run_residuals.py`): R² 0.0055 = **rumore** (vs 0.0051 da feature
casuali) → nessun segnale nascosto oltre la forma. MA emerge l'**adverse
selection**: il gap vs mercato cresce col dissenso modello-mercato (r=+0.18;
quartile alto +0.0539 vs basso +0.0009) → i "value bet" del modello sono i
suoi errori. E' il meccanismo del ROI negativo, coerente con Fase 16 (α*=0) e
Fase 14 (CLV<0). **Prossima direzione (Fase 21+): MODELLI NUOVI, valutati
PER MERCATO** (vedi principio 8). Non piu' tweak al Dixon-Coles ma famiglie
diverse — es. gradient boosting/logistico che predicono un mercato DIRETTAMENTE
(senza matrice dei punteggi), o modelli a punteggio con miglior correlazione
(bivariato Poisson, negative-binomial) per il GG/NG. Regola: giudica ogni
candidato mercato per mercato; la config ufficiale puo' diventare un portafoglio
di specialisti; **priorita' al GG/NG** (l'unico mercato senza quote nei dati,
quindi senza tetto di efficienza dimostrato). Restano validi anche **dati
davvero nuovi** e **uso pratico**. **Fase 21 (primo modello nuovo):** gradient
boosting sul GG/NG (`scripts/_run_gbm_btts.py`, sklearn extra "models"). Il GBM
grezzo perde (+0.0280) ma e' quasi tutto mis-calibrazione: **calibrato (Platt)
pareggia il DC** (+0.0047, CI [−0.0019,+0.0113]) ma non lo batte, e **nessuno
batte la baseline** → convergenza sul tetto, non fallimento del modello. Il
GG/NG e' quasi-impredicibile come il pareggio. LEZIONE METODOLOGICA: per ogni
modello nuovo, valuta SEMPRE anche la versione calibrata (il log-loss punisce la
sovra-confidenza; senza il controllo si conclude il falso). Il principio "un
modello per mercato" resta valido; questo mercato non cede. **Fase 22 (sweep
GBM completo):** 6 mercati (1X2, O/U, GG/NG, 1X, 2X, 12) × 3 feature-set
(cov / dc / dc+cov) × calibrazione (`scripts/_run_gbm_sweep.py`). Il GBM **non
batte il DC su NESSUN mercato** e allarga il gap col mercato (CI<0 escluso su
5/6; GG/NG pareggia a livello baseline); rende al meglio quando usa SOLO le
feature del DC (aggiungere covariate peggiora). Conclusione forte: il **tetto e'
INFORMATIVO, non architetturale** — la forma del Dixon-Coles non e' il collo di
bottiglia, lo sono i dati pre-partita. Testate 2 famiglie di modelli su 6
mercati: nessuno cede. Per un edge serve **informazione nuova**, non un modello
nuovo. **Fase 23 (GBM modello+mercato):** dato al GBM anche le quote di chiusura
come feature (`scripts/_run_gbm_market.py`, encompassing NON-lineare):
sull'1X2 il GBM-con-mercato resta a 0.9996 — **peggio del DC da solo** (0.9797)
e lontano dal mercato (0.9632), P(batte mercato)=0%. Il mercato e' una previsione
quasi-ottima e un ensemble di alberi la degrada; il mercato come feature aiuta il
GBM rispetto a se stesso ma non basta. Ridurre il gap a ~0 si puo' solo copiando
il mercato (lineare, gia' Fase 16); batterlo NO, con nessun metodo. Il GBM e' lo
strumento sbagliato per combinare modello+mercato. **Fase 24 (DC calcolato DAL
mercato — PRIMO risultato positivo):** invertire le quote 1X2+O/U per ricavare i
lambda,mu IMPLICITI nel mercato (che li stima meglio di noi) e derivarci il GG/NG
con la matrice del DC (`scripts/_run_dc_from_market.py`). Sui mercati con quote
riproduce il mercato (banale); il valore e' derivare il GG/NG, che il book NON
prezza: 0.6853 (con rho) vs DC-da-gol 0.6898 vs baseline 0.6871 -> **batte
entrambi** (Δ vs DC -0.0033, CI [-0.0072,+0.0005], P=95.7%, 6/6 stagioni; prima
cosa a battere la baseline sul GG/NG). Onesta': CI sfiora lo zero (molto
probabile, non concluso), guadagno modesto, non verificabile vs un'ipotetica
linea GG/NG, e RICHIEDE le quote 1X2+O/U al momento della predizione. LEZIONE: la
leva vera e' l'INFORMAZIONE (qui quella del mercato su un mercato non prezzato),
non l'architettura; il GG/NG "specialista" (principio 8) diventa
mercato-implicito -> matrice DC -> P(GG), non il DC-da-gol. **Fase 25 (finestra dei dati):** aggiunti al backtest
``train_window_days`` (taglio netto) e ``drop_train_seasons``; sweep sulla config
ufficiale (`scripts/_run_window.py`). Tagliare le stagioni vecchie PEGGIORA
(finestra 3 stag +0.0011, 2 stag +0.0019, e di piu' sulle recenti +0.0035);
perfino escludere la stagione COVID anomala costa +0.0007. Piu' storia batte
meno: rose stabili anno su anno, l'emivita 365g gia' gestisce la recency in modo
ottimale. Conferma la Fase 2b (memoria lunga). **Fase 26 (market-implied su TUTTI
i mercati sui gol — il risultato piu' forte):** modulo
`src/models/market_implied.py` (inversione 1X2+O/U -> lambda,mu del mercato ->
matrice DC -> ogni mercato) + sweep (`scripts/_run_market_implied.py`). Batte il
DC-da-gol su 13 mercati su 14 (CI95<0 su 12) e la baseline su 13 su 14; guadagni
maggiori sui mercati ricchi (risultato esatto -0.0309, multigol, total-squadra).
Solo il pari/dispari non migliora (quasi-casuale). Strade: rho -0.06 aiuta poco;
servono 1X2 E O/U (l'O/U aggiunge); blend coi nostri lambda,mu PEGGIORA (mercato
puro meglio, conferma Fase 16). E' un MOTORE di pricing coerente per ogni mercato
sui gol, condizionato alle quote 1X2+O/U; non verificabile vs ipotetiche linee di
quei mercati. **Fase 27 (forma dei punteggi):** i lambda,mu vengono dal mercato,
ma la forma della distribuzione e' nostra; fittata walk-forward
(`scripts/_run_shape.py`, modulo esteso con inflazione diagonale + binomiale
negativa). La forma della Fase 26 (Poisson + rho -0.06) e' gia' ottima: rho
fittato ~ fisso (nessun guadagno), phi diagonale minuscolo e non conclusivo,
binomiale negativa RIGETTATA (nb_size->Poisson: i gol con lambda dal mercato non
sono over-dispersi). Il market-implied ha toccato il tetto anche sulla forma; per
spingere oltre servirebbero PIU' input di mercato (altre linee O/U, handicap) che
lo snapshot non ha. **Fase 28 (errore per giornata):** log-loss modello e mercato
per momento della stagione (`scripts/_run_matchday.py`). Il finale (giornate
32-38) e' molto piu' difficile per ENTRAMBI (log-loss ~0.96 -> ~1.02): le ultime
giornate sono ballerine per chiunque (casualita' irriducibile). Il gap raddoppia
verso la fine (+0.0124 a meta' -> +0.0258 nel finale), indizio che il mercato
prezzi la posta in palio meglio di noi, MA non conclusivo (Δ gap late-vs-resto
+0.0104, CI [-0.0196,+0.0395], 240 partite ad alta varianza). **Prossimo bivio:**
Fase 29. **Fase 29 (posta in palio, NEGATIVA):** feature "dead rubber" derivata
dalla classifica (`scripts/_run_stakes.py`, euristica 3×gare-rimaste). I dead
rubber sono rari (0.5% entrambe, 4.3% almeno una) e NON spiegano il finale: sul
campione affidabile nessun effetto (Δ gap dead-live -0.012, CI [-0.058,+0.035]),
e la direzione e' negativa (il modello e' semmai migliore nei dead rubber).
Cercare dati esterni sulla motivazione probabilmente non aiuta. **Fase 30
(pattern dentro la stagione):** anatomia per periodo
(`scripts/_run_season_patterns.py`). Il finale piu' difficile NON e' entropia
(esiti non piu' bilanciati); due cambi strutturali reali (giornate 32-34 tese e
bloccate; 35-38 col VANTAGGIO-CASA che crolla, casa 40%->36% e trasferta
31%->38%); nessun pattern-gap robusto (correlazioni ~0, gap fine-inizio positivo
solo 3/6 stagioni). Candidato concreto emerso: attenuare il vantaggio-casa nelle
ultime giornate (come nel COVID, Fase 9), piu' promettente della motivazione ma
marginale. **Fase 31 (posta in palio corretta, 8 stagioni — RIBALTA la 29):** la Fase 29
sbagliava ai due estremi (una retrocessa contata come "in lotta salvezza", una
campione come "in corsa titolo"). Definizione corretta (DECISA = nessuna corsa
aperta, inclusi retrocessa/campione) su 8 stagioni (`scripts/_run_stakes2.py`):
il segnale e' l'ASIMMETRIA di motivazione -- "una decisa, una in corsa" ha gap
+0.057 (3x il +0.017 di "entrambe in corsa"), CI esclude lo zero; "entrambe
decise" niente. Escludendo le partite con >=1 decisa il gap scende (+0.0188 ->
+0.0172): su di esse il modello va PEGGIO del mercato (il mercato prezza la
motivazione, noi usiamo la forza stagionale). Primo LEAD azionabile dai dati
interni. Onesta': campioni piccoli (133/76/44/23) e molti test -> indizio forte,
non prova. METODO: un classificatore sbagliato ai bordi (Fase 29) ribaltava la
conclusione. **Fase 32 (validazione covariata stakes su DC e GBM):** covariata `stakes`
(1=decisa/0=in corsa, `loader.add_stakes`, `--covariates stakes`, off di default)
testata walk-forward su entrambi i modelli (`scripts/_run_stakes_cov.py`). Sulle
partite mismatch (n=99) la direzione e' CONFERMATA su entrambi: DC -0.0022, GBM
-0.0127 (il GBM la cattura ~6x meglio, l'effetto e' non-lineare); ma nessuno e'
conclusivo (CI includono lo zero, il GBM per un pelo). Non adottata (regola CI<0)
ma e' il LEAD interno piu' credibile: direzione giusta su due architetture,
meccanismo chiaro, ≠ dai "residui=rumore" delle Fasi 13/20. Serve piu' campione.
Se si usera', il GBM e' il veicolo giusto. **Fase 33 (ultime covariate interne, RIDONDANTI):** PPDA/deep (tattica) e
finishing-luck (gol-xG rolling, mean-reversion), mai provate prima
(`loader.add_style_luck`, covariate `ppda`/`deep`/`luck`, off di default,
`scripts/_run_style_luck.py`). Sul DC: ppda/deep peggiorano appena (+0.0009),
luck effetto ESATTAMENTE ZERO (il blend gol/xG e' gia' il meccanismo di
mean-reversion); GBM estrae un capello (-0.0022, 81%) non conclusivo e
irrilevante. Con la Fase 33 i DATI INTERNI SONO COMPLETAMENTE ESPLORATI (tutto lo
snapshot testato): tetto informativo confermato. Ogni altro guadagno richiede
INFORMAZIONE NUOVA o un avversario meno efficiente. **Prossimo bivio:** piu'
stagioni/cross-lega per lo stakes, uso pratico (tool di predizione, la
culminazione naturale), o dati davvero nuovi (formazioni, quote live).

---

## 7. Portare il modello su un'altra lega (Premier, ecc.) — NON copiare i numeri

Le **formule** del modello sono universali; gli **iperparametri no**. Vivono in un
**unico punto di verità**, `src/config.py` (`LEAGUE_CONFIGS`), da cui `backtest.py`
legge i default: `emivita 365g`, `shrinkage 1.5`, `blend α=0.75`, `blend_signal xg`,
`promoted_prior δ=0.23`. La classe `DixonColesModel` ha default **neutri** (nessun
decadimento/shrinkage): la lega-specificità non è mai incisa nel modello. Aggiungere
una lega = **aggiungere una voce in `LEAGUE_CONFIGS`**, non toccare il codice.
Trasferire i numeri della Serie A uncritically lascerebbe il modello **sub-ottimo**:
prima di dichiarare un modello "buono" su una nuova lega, **ri-tara e ri-motiva ogni
numero** (regola §2-bis), perché ognuno dipende dai dati di *quella* lega:

- **δ (prior neopromosse)**: `δ = ln(gol_lega / gol_promosse)` — va ricalcolato. In
  Premier le promosse sono notoriamente più deboli → δ probabilmente **maggiore** di
  0.23. Copiare 0.23 sotto-correggerebbe.
- **emivita / shrinkage**: dipendono dalla stabilità delle rose e dal rumore del
  segnale nella lega. Una lega con più turnover → emivita più corta.
- **α del blend gol/xG**: dipende dalla qualità/copertura dell'xG di quella lega.
- **vantaggio-casa `γ`**: differisce per lega (e, come emerso nelle Fasi 9-bis/30,
  **non è costante** nemmeno *dentro* una stagione — vedi audit).

Ogni ri-taratura è una fase a sé, con blocco 📐 e riga nel registro. Non esiste "il
modello": esiste *il modello tarato per la lega X*.

**Premier League e La Liga sono state aggiunte (Fasi 54-57).** Dati grezzi caricati
a mano come bundle in `files/` (rete bloccata) → snapshot congelati
`data/{premier_league,la_liga}_matches.csv` via `scripts/build_league_snapshot.py`.
Config in `LEAGUE_CONFIGS`: **identiche alla Serie A tranne δ** (Premier 0.33, Liga
0.22 — ri-tarato, ipotesi §7 confermata). Esito cross-lega: **il modello è
trasferibile** (DC+xG batte la baseline, gap col mercato dello stesso ordine, la
ri-taratura è piatta = tetto informativo universale) **ma l'edge no** (Fase 53: la
sotto-dispersione decresce con la liquidità del mercato, il tilt e il draw-bias non
si replicano — il beat-the-close è idiosincratico della chiusura Serie A). γ
(vantaggio-casa, molto più forte in Liga) è auto-fittato dal DC, non in config.

**Non usare il modello per scommettere soldi veri allo stato attuale.**
