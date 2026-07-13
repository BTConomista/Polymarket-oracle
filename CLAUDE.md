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
  6. **lezione / cosa ne consegue**.
- [ ] **README — «Registro completo dei risultati»** (OBBLIGATORIO, SEMPRE).
  Il README contiene una sezione **«Registro completo dei risultati — ogni analisi,
  in un colpo d'occhio»**: è il punto UNICO e accessibile dove **chiunque** deve
  poter vedere i numeri chiave di **OGNI** backtest e analisi, senza leggere il
  diario o il codice. **Dopo ogni esperimento significativo — positivo, negativo o
  "nel rumore" — aggiungi lì la riga corrispondente** (nella tabella degli
  esperimenti e, se serve, nelle tabelle del gap/evoluzione). Nessuna analisi può
  restare fuori da questo registro. Se cambia la config ufficiale, aggiorna anche
  la riga di stato e la roadmap.
- [ ] **Test** — mantieni `pytest` verde; aggiungi un test per ogni nuova
  funzionalità del modello/pipeline.
- [ ] **Commit + push** — messaggio chiaro (cosa e perché), sul branch di
  sviluppo. Non lasciare mai lavoro non committato: il container è effimero.

Regola pratica: **il registro `runs.jsonl`** cattura *ogni* run (dati grezzi); **il
diario** cattura le *decisioni e il perché* (narrazione); il **README** è lo stato
*corrente* sintetico E il **«Registro completo dei risultati» leggibile da tutti** —
va **sempre** aggiornato: chiunque apra il README deve vedere l'esito di ogni analisi.

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

## 4. Mappa del repo (dove sta cosa)

```
src/data/        sources.py (URL/stagioni/alias), loader.py (offline-first),
                 database.py (snapshot CSV + SQLite)
src/models/      dixon_coles.py (il modello: _fit_counts, blend, predizione)
src/evaluation/  metrics.py (Brier/log-loss/devig), analysis.py (analisi errori),
                 calibration.py (temperature scaling post-hoc, Fase 6),
                 experiment_log.py (compute_metrics = FONTE DI VERITA' unica; registro)
scripts/         download_data, build_database, backtest, analyze, tune, calibrate,
                 markets (multi-mercato), analyze_gap (anatomia del gap col mercato)
experiments/     runs.jsonl (registro replicabile) + README (formato)
data/            serie_a_matches.csv (SNAPSHOT congelato, versionato)
                 football.db (SQLite, rigenerabile, NON versionato)
docs/DIARIO.md   narrazione passo-passo con ragionamento
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
ottimale. Conferma la Fase 2b (memoria lunga). **Prossimo bivio:** Fase 26
(market-implied esteso a TUTTI i mercati sui gol, nessun dato nuovo serve), dati
davvero nuovi, uso pratico (predittore GG/NG condizionato alle quote), o
cross-lega.

**Non usare il modello per scommettere soldi veri allo stato attuale.**
