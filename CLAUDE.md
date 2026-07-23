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
- [ ] **Commit + push** — messaggio chiaro (cosa e perché), **su `main`**
  (regola §3-bis: si pusha SEMPRE E SOLO su `main`). Non lasciare mai lavoro non
  committato: il container è effimero.

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

- **REGOLA (decisione utente, luglio 2026): si pusha SEMPRE E SOLO su
  `main`.** Ogni sessione lavora e committa direttamente su `main`
  (`git checkout main`, pull all'inizio, push alla fine di ogni blocco di
  lavoro). Se l'ambiente assegna un branch `claude/...`, NON usarlo: i
  commit vanno su `main`.
- **Creare un nuovo branch SOLO se esplicitamente richiesto** dall'utente:
  niente branch "per prudenza" o per separare un sotto-task.
- Storia: fino alla Fase 82 si lavorava su branch di sessione (`claude/...`)
  poi confluiti; il branch `claude/premier-liga-analysis-nqwa5c` è stato
  rinominato/ricopiato in `main` ed è deprecato.

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
docs/STUDIO_PREMIER_LIGA.md   quaderno di studio dedicato a Premier e La Liga:
                 dati, differenze strutturali vs Serie A, stato dei test
                 per-lega e piano ragionato; aggiornare a ogni fase che
                 tocca le due leghe (Fase 79+)
docs/PLAYBOOK_NUOVA_LEGA.md   procedura operativa per aggiungere una lega
                 nuova (passi 0-5, finestre di backtest, lezioni acquisite,
                 checklist): da seguire per ogni campionato futuro
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

> Questa sezione è un **istantanea sintetica** dello stato attuale. Il racconto
> completo e sempre aggiornato vive in `docs/DIARIO.md` (con un **indice per
> archi narrativi** in testa) e nella tabella «Tutti gli esperimenti» del
> `README.md`; la rosa dei modelli in `docs/PANCHINA.md`. Aggiorna QUESTA
> istantanea quando cambia lo stato di fondo, non a ogni fase.

**Dove siamo (Fase 83).** Il progetto è passato da "un modello Dixon-Coles sui
gol" a **due motori complementari**, su **3 leghe** (Serie A, Premier, La Liga,
9 stagioni ciascuna):

1. **Dixon-Coles gol+xG** (`src/models/dixon_coles.py`) — il predittore
   *standalone*, senza quote: config per-lega in `src/config.py`
   (emivita 365g, shrinkage 1.5, blend xG α=0.75, δ neopromosse 0.23/0.33/0.22),
   + la **φ(|λ−μ|)** della Fase 35 sulla famiglia-pareggio. Batte nettamente le
   baseline ma **non il mercato** (gap 1X2 +0.0165 in Serie A; ordine simile
   nelle altre leghe).
2. **Market-implied** (`src/models/market_implied.py`) — il *motore di pricing*:
   inverte le quote 1X2+O/U nei λ,μ del mercato e ne deriva **ogni mercato Tier
   1** dalla matrice DC. Batte il DC-da-gol su 13/14 mercati su tutte e 3 le
   leghe (Fasi 26/76). È il **titolare** quando ci sono le quote; il DC è il
   fallback senza quote.

**Le scoperte che reggono.** (a) Il mercato di **chiusura ingloba il modello**
(α\*=0 ovunque, Fase 16): non lo si batte in ROI — **non usare per scommettere
soldi veri**. (b) I gol dati i tassi del mercato sono **sotto-dispersi**
(double-Poisson θ≈1.2): `sharpen_1x2` batte la chiusura devigata in log-loss con
CI conclusivo (non in ROI), ed è il **router v3** adottato (`price_markets`,
θ 1.225 mercato / 1.138 DC). Ma è una proprietà della **chiusura Serie A** (meno
liquida): non replica su Premier/Liga (Fase 53). (c) Il θ del router è
**per-contesto** (lega × epoca): ~1.2 in Serie A/Liga, ~1 in Premier, e cresce
nel tempo (Fasi 75/81). (d) Il **valore residuo** è prezzare *calibrato* i ~17
mercati che il book non quota (GG/NG, risultato esatto, multigol, total-squadra…)
e le **correzioni per-lega** (φ35 famiglia-pareggio, θ router); la Fase 82 ha
verificato per via diretta che l'oracolo è **calibrato e indovina quanto il
mercato** (non di più).

**Cosa è chiuso (non riproporre senza informazione nuova).** Tutti i dati
INTERNI sono esplorati (gol/xG/npxG/PPDA/deep/valore-rosa/assenze/riposo/forma/
stakes: ridondanti o rumore, Fasi 4c-33); GBM bespoke per-mercato (bocciato
4 volte); Poisson bivariato, copule di Frank, ensemble emivite, draw-inflation,
ρ dinamico, zero-inflazione, Rue-Salvesen, GAS/state-space (tutti chiusi per
test o per argomento); più-storia-batte-meno (Fase 25). Il tetto è
**informativo**, non architetturale.

**Prossimi passi (idee, non impegni).** In ordine di rapporto valore/costo,
dettaglio in `docs/PISTE.md`:
- **uso pratico**: `scripts/predict.py` è il tool (DC senza quote / market-implied
  con `--odds`), reso **per-lega** alla Fase 83-bis (M1); resta da rendere
  per-lega il θ del router nel path market-implied (M2 Premier con θ neutro);
- **test prospettico 2026-27** (Fase 78, stato APERTO): previsioni congelate
  prima del kickoff e scorate dopo — il gold standard, da completare al primo
  turno con quote reali (`experiments/prospettico_2026_27.md`);
- **informazione DAVVERO nuova** (formazioni ufficiali pre-partita, quote
  live/di apertura raccolte prospetticamente): l'unica leva non ancora esaurita;
- **mercati non ancora coperti** (Tier 2 handicap asiatico, Tier 3 HT/FT e tempi).

---

## 7. Portare il modello su un'altra lega (Premier, ecc.) — NON copiare i numeri

**La procedura completa e collaudata (passi 0-5, EDA, tracer, ri-taratura,
motore, leve della rosa, scelta delle finestre di backtest, checklist) vive in
`docs/PLAYBOOK_NUOVA_LEGA.md`** — scritta dopo l'onboarding di Premier e Liga
(Fasi 53-57, 79-80): per ogni lega futura si parte da lì. Qui sotto i principi.

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
