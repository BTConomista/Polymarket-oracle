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
   - ~~alcuni mercati sono più promettenti di altri: il **GG/NG non ha quote nei
     dati**, quindi è l'unico dove non possiamo dimostrare l'efficienza del
     mercato — l'unico con "spazio" non ancora chiuso. Priorità lì.~~
     **PREMESSA CADUTA (integrazione delle 5 leghe).** Le quote GG/NG di
     chiusura sono state trovate — un book (1xBet) che football-data non
     contiene, **5.337 partite del 2017-20** su tutte e 5 le leghe (la finestra
     2017-19 della caccia O/U ne conta 3.652) — e la domanda
     è stata misurata invece che rimandata. Risposta: **il mercato GG/NG è
     informativo** (log-loss 0.6840 contro 0.6921 di baseline, CI conclusivo)
     anche se vale **un terzo** dell'O/U 2.5 dello stesso book e costa 1,7 punti
     di margine in più; **il nostro miglior prezzo lo pareggia e non lo batte**
     (6 varianti su 6 con CI a cavallo dello zero); **il DC perde di netto**
     (+0.0104, CI [+0.0063, +0.0145]) e il test di encompassing mostra che il
     book lo **ingloba** (α\*=0 nel 70% dei fit — esattamente come la Fase 16
     sull'1X2). Nessuna leva aiuta su nessuno dei due fronti (§1.9).
     **Lo "spazio" non era una proprietà del mercato: era la nostra ignoranza.**
     Va trattato come gli altri mercati derivati, non come una frontiera.
     ⚠️ **RETTIFICA (01/08/2026, censimento delle fonti).** Qui c'era scritto
     che «il GG/NG resta interessante perché il book non lo quota nelle
     stagioni recenti». **È falso**, e lo era già dal 28/07: la Fase 106 aveva
     scaricato i file footiqo fino al 2024-25 senza che nessuno se ne
     accorgesse. Misurato ora: **14.358 righe** con entrambi i lati della quota
     di chiusura GG/NG (`xbetCloseBTTSY`/`N`), distribuite su **tutti e nove
     gli anni 2017→2025** (909 / 1.808 / 1.823 / 1.569 / 1.988 / 1.690 / 1.920
     / 1.717 / 934). Le conclusioni qui sopra restano valide **ma sono misurate
     sulle sole 5.337 partite del 2017-20**: le altre **8.981 non sono mai
     state aperte da una riga di codice**, e sono la verifica fuori campione
     — regime porte chiuse 2020-21 compreso — che il progetto non ha ancora
     fatto.
   - **Mercati standard = Tier 1** (d'ora in poi): 1X2, O/U 1.5/2.5/3.5, GG/NG,
     doppie chance, total-squadra (casa/ospite O0.5/1.5), clean sheet, vince-a-zero,
     scarto ≥2, multigol, risultato esatto. Ogni backtest/analisi li copre tutti
     (`scripts/_run_markets_bakeoff.py`, `derive_markets`). Il **Tier 2**
     (handicap asiatico) è **coperto e confrontato** con una quota esterna
     (Fase 88) — esito onesto: **pareggio** in Brier col mercato sharp, non
     vittoria (§6); il **Tier 3** è coperto per Halftime, Second Half e risultato
     esatto (Fase 96/98). Restano scoperti: HT/FT congiunto, le combinazioni, e
     il live (Tier 3+) — per cui serve prima il modello a due stadi del secondo
     tempo (residuo aperto della Fase 96/99).
   - **Esito del bakeoff (Fase 41):** il "portafoglio di specialisti" NON è 20
     modelli bespoke — **collassa a UN motore**: il **market-implied** è il migliore
     su 19/20 mercati Tier 1 (il DC-da-gol non vince mai), perché i mercati sono
     proiezioni della stessa matrice e i λ,μ del mercato battono i nostri ovunque.
     L'unico "specialista" aggiuntivo è la **φ(|λ−μ|)** (Fase 35/39) sulla
     famiglia-pareggio. Regola operativa: **market-implied quando ci sono le
     quote 1X2+O/U; DC come fallback senza quote** — con la φ35 **solo dove è
     misurata utile**, cioè in Serie A: su Premier e Liga peggiora (Fase 79) e
     applicarla lì era un bug del tool, corretto alla Fase 101. Le leve attive
     per lega stanno in `src.config.MARKET_ENGINE`. Il **Poisson bivariato** (Fase 42,
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
     del motore restano dichiaratamente per-lega (§7). Il port su Premier/Liga e'
     stato poi COMPLETATO (Fasi 54-57): snapshot congelati e config per-lega in
     LEAGUE_CONFIGS; il seguito vive in docs/STUDIO_PREMIER_LIGA.md. (I due θ
     citati qui sono quelli *pubblicati* dalla Fase 53; l'audit a 5 leghe li ha
     poi rimisurati con uno stimatore pooled e le leghe si dividono in due
     famiglie — vedi §6 e docs/audit_5_leghe/10_modelli_nuove_leghe.md.)
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
10. **⭐ Un risultato negativo vale SOLO per i dati su cui è stato misurato**
    (decisione utente, 02/08/2026 — apre la **Fase 2** del progetto).
    Le Fasi 0-136 hanno cercato l'edge dentro un insieme di dati ristretto e
    **aggregato per squadra-partita**: gol, xG, quote, riposo, valore rosa.
    Molte piste sono state chiuse lì, ed è giusto che restino chiuse *per
    quella domanda*. Ma «il riposo non predice» è stato misurato come covariata
    di squadra sul risultato: **non dice niente** su «questo giocatore ha
    volato venti ore ed è sceso in campo con due giorni di recupero».
    Sono dati diversi, granularità diversa, domanda diversa.
    Quindi, d'ora in poi:
    - un esito negativo si cita **con il perimetro su cui è stato ottenuto**
      («nullo su dati di squadra 2017-25»), mai come «chiuso» in astratto;
    - **non si rifiuta un dato nuovo citando un modello vecchio** costruito su
      meno informazione e più grossolana. Si può prevedere che il segnale sia
      debole — ma è una previsione da misurare, non un verdetto già emesso;
    - vale anche al contrario: la nuova granularità **non sospende** il metodo.
      Restano l'intervallo di confidenza (R7), la validazione su più stagioni
      (§1.7), la disponibilità temporale (R8) e l'onestà sui limiti (§1.6).
      Più dati significa più occasioni di trovare un pattern che non c'è.
    Il rischio che questa regola corregge è **asimmetrico**: riaprire una pista
    chiusa costa un esperimento; non riaprirla costa non sapere mai.

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
- [ ] **Test** — mantieni `pytest` verde (**1.468 verdi** al 08/08/2026); aggiungi
  un test per ogni nuova funzionalità del modello/pipeline.
- [ ] **Dati e termini** — se l'esperimento ha toccato i DATI (colonne nuove,
  correzioni, stime), aggiorna `docs/DATI.md` (catalogo di tutto ciò che
  esiste, reale o stimato) e il registro `data/correzioni_dichiarate.csv`
  (regola R3, §5-bis); se ha introdotto un **termine** nuovo, aggiungi la voce
  in `docs/GLOSSARIO.md` con la fase che lo introduce.
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

**Regola aggiunta dalla Fase 92 (deduzioni da misure indirette).** Quando una
fase deduce «il problema è X» da una misura indiretta (un mercato derivato, un
proxy, un confronto), la deduzione va scritta come **identità o scomposizione
esatta**, non come ragionamento in prosa. Motivo: per 80 fasi il progetto ha
letto al contrario il proprio dato-chiave sul gap, perché il passaggio da
«gap del mercato 12 ≈ 0» a «sappiamo prezzare chi vince» non era mai stato
messo in formule — e `P(12)=1−P(X)` lo rende falso per identità. Una
scomposizione che ricompone a sei decimali non si può leggere al contrario.

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
python scripts/backtest.py --league premier_league   # altra lega (default: serie_a)
python scripts/analyze.py              # analisi errori del backtest
python scripts/tune.py --sweep shrinkage --values 0 1 1.5 3       # tuning iperparametro
python scripts/markets.py              # listino multi-mercato
python scripts/predict.py Inter Juventus                          # uso pratico: DC senza quote
python scripts/predict.py Inter Juventus --odds 2.10 3.30 3.60 1.85 1.95  # market-implied
python -m pytest                       # test (1.468 verdi al 08/08/2026)
```

⚠️ `build_database.py --league X --refresh` ha scritto la lega X **sopra** lo
snapshot Serie A fino alla Fase 101 (bug distruttivo, corretto lì): se un giorno
lo snapshot di una lega sembra contenerne un'altra, la causa storica è quella.

Config "ufficiale" del modello: vive in **`src/config.py`** (`LEAGUE_CONFIGS`),
**unico punto di verità** (§7), da cui `backtest.py` e `tune.py` leggono i default
— non è incisa negli script né nella classe `DixonColesModel` (che resta neutra).
Per la **Serie A**: **emivita 365g, shrinkage 1.5, shots_blend 0.75, blend_signal
xg, promoted_prior δ=0.23** (blend gol/xG reale, Fase 4b; emivita ri-tarata a 365g
in Fase 4d; prior di cold-start neopromosse adottato in Fase 7/8). Le altre quattro
leghe hanno **gli stessi valori tranne δ**: Premier 0.33, La Liga 0.22 (Fase 57),
Bundesliga 0.28, Ligue 1 0.19 (Fase 100/101). Le costanti del **motore
market-implied** stanno nella mappa gemella `MARKET_ENGINE` (θ del router, φ0, κ,
`sharpen_1x2`): la Serie A è l'unica con le correzioni attive, le altre quattro
escono col **motore LISCIO** (Fase 92-bis/101). Se cambi un valore, aggiorna README
e diario.

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
- **Verificato (27/07/2026)**: i tre branch `claude/…` rimasti su `origin`
  (`audit-ultimi-20-step-gzwro2`, `premier-liga-analysis-nqwa5c`,
  `verify-data-import-leagues-468euv`) sono tutti **antenati di `main`** —
  `git rev-list --count origin/main..origin/<branch>` dà **0** su tutti e tre.
  Sono davvero confluiti: non c'è niente da ripescare lì dentro.

---

## 4. Mappa del repo (dove sta cosa)

```
src/config.py    iperparametri PER LEGA (LEAGUE_CONFIGS) = fonte unica (§7); nuova
                 lega = nuova voce, non codice. Mappa gemella MARKET_ENGINE
                 (lega -> costanti del motore market-implied) e DRIFT_SD (deriva
                 di forza in-stagione, Fase 94)
src/data/        sources.py (URL/stagioni/alias), loader.py (offline-first),
                 database.py (snapshot CSV + SQLite), understat.py (xG/npxG/PPDA/
                 deep), player_scores.py (valori rosa, Fase 67), transfermarkt.py
                 (valori e assenze), fixtures.py (calendario di club -> congestione
                 vera, Fase 4c/4e)
src/models/      dixon_coles.py (il modello: _fit_counts, blend, predizione,
                 draw_balance Fase 35 = phi(|lam-mu|))
                 market_implied.py (Fase 24/26: inverte le quote 1X2+O/U ->
                 lambda,mu del mercato -> matrice DC -> ogni mercato sui gol;
                 derive_markets = tutti i mercati da una matrice; price_markets
                 Fase 44 = routing forma per-mercato; btts_season Fase 48
                 = nudge stagionale GG/NG di fine stagione, off di default)
                 market_denoise.py (Fase 38/Punto 4: power-devig + recal cross-stagione)
                 bivariate_poisson.py (Fase 42: correlazione esplicita λ3; perde vs φ35)
                 copula_scores.py (Fase 43: copula di Frank, dip. flessibile; tetto = φ35)
                 season_sim.py (Fase 89: simulazione Monte Carlo di una STAGIONE
                 intera -> mercato CAMPIONE; classifica con spareggi UFFICIALI
                 per lega, h2h in SA/Liga, DR in Premier)
                 player_stats.py (97 statistiche per GIOCATORE-partita, 3 leghe)
                 smarkets_archive.py (Fase 136: elenca e legge gli snapshot
                 Smarkets, .json storici e .json.gz nuovi. ultimo_listino_completo()
                 e' quello che serve: «l'ultimo file» puo' essere un giro di
                 chiusura con una lega sola)
                 coppe.py + coupe_de_france.py (Fase 138: le COPPE NAZIONALI
                 2025-26, 6 tornei / 5 paesi. Il punteggio di games.csv SOMMA
                 I RIGORI su 68 partite su 458: qui e' ricostruito dagli eventi
                 e verificato contro openfootball, 42/42 identiche)
                 team_stats.py (Fase 131: 45 statistiche per SQUADRA-partita divise
                 in PERIODI -- Totale/1T/2T, 5 leghe 2025-26, 1.752 partite. E' il
                 primo dato che separa i due tempi: serve alla pista 6-bis, il
                 modello a due stadi. team_form(periodo=) e' l'unica forma sicura R8)
                 allenatori.py (Fase 140: IL DATABASE ALLENATORI, strato 1, da
                 games.csv. load_partite = una riga per partita-club; panchine()
                 = i mandati; esperienza_prima() = la forma sicura R8.
                 ⚠️ Tre trappole MISURATE, non ipotesi: il nome NON e'
                 un'identita' -- conflitti_identita() dimostra 11 omonimi col
                 test "nessuno allena due club lo stesso giorno", 2 nel
                 perimetro; manager_name e' CHI SEDEVA IN PANCHINA quella
                 partita, non chi era in carica (836 mandati su 13.810 sono un
                 vice per una gara: usa ricuci=True); l'esperienza e' VISIBILE
                 AL DATASET, non globale. E clubs.coach_name NON va usata:
                 e' l'allenatore corrente, trappola R8)
src/evaluation/  metrics.py (Brier/log-loss/devig), analysis.py (analisi errori),
                 markets.py (valutazione multi-mercato di un backtest),
                 calibration.py (temperature scaling post-hoc, Fase 6),
                 experiment_log.py (compute_metrics = FONTE DI VERITA' unica; registro)
scripts/         build_coppe_2526 (la raccolta coppe, Fase 138),
                 aggancia_coppe (i TRE PONTI delle raccolte di coppa: squadre->
                 club_id, partite->game_id, giocatori->player_id. L'ordine
                 conta: agganciata la partita, i candidati per un giocatore
                 scendono a 18-23 e il nome basta -- 25%->97,5%, Fase 139-bis),
                 verifica_aggancio_coppe (il controllo di COMPLETEZZA: ogni
                 riga raccolta e' in una tabella di aggancio? 27.624 righe,
                 99,5% risolto, Fase 139-ter),
                 verifica_incrocio_coppe (la domanda DIVERSA: non «quante righe
                 sono agganciate» ma «questa PARTITA ha tutti i blocchi
                 insieme». Le due danno numeri diversi -- 99% per foglio, 51%
                 per partita -- e la seconda e' quella che decide se un modello
                 si puo' addestrare. --partita <game_id> fa il join completo su
                 una sola partita, Fase 139-octies),
                 registra_raccolta_coppa_diretta (la porta d'ingresso delle
                 raccolte manuali di COPPA: verifica e CONFRONTA con la fonte
                 automatica partita per partita, Fase 139),
                 download_data, build_database, backtest, analyze, tune, calibrate,
                 markets (multi-mercato), analyze_gap (anatomia del gap col mercato),
                 predict (il TOOL d'uso: DC senza quote, market-implied con --odds),
                 build_league_snapshot (snapshot Premier/Liga dai bundle in files/),
                 build_new_snapshot (snapshot Bundesliga/Ligue 1, scaricati),
                 registra_raccolta_diretta / registra_raccolta_squadra_diretta
                 (le due porte d'ingresso dei dati diretta.it: per giocatore e per
                 squadra; verificano PRIMA di accettare e scrivono il manifesto),
                 build_estimates + verifica_stime (le stime dichiarate, §5),
                 applica_correzioni (registro R3, idempotente), audit_snapshots +
                 audit_anomalie + cerca_segnaposto (i controlli dell'audit),
                 fetch_polymarket_open / fetch_smarkets_outrights / archive_outrights
                 (quote outright live), scrape_betexplorer (Fase B, vedi
                 docs/BETEXPLORER_SCRAPER.md), _run_*.py (uno per esperimento:
                 e' cosi' che ogni numero del diario resta ri-calcolabile, Fase 15)
experiments/     runs.jsonl (registro replicabile) + README (formato)
                 fase93_discrimination.csv: deficit di discriminazione per
                 PARTITA (5.083 righe, Fase 93) — input riutilizzabile per
                 affettare il gap in altri modi senza rifare 18 backtest
                 fase89/91/94*.json, listino_validazione.json: artefatti delle
                 fasi corrispondenti
                 prospettico_2026_27* : le previsioni CONGELATE del test
                 prospettico (Fase 78, APERTO)
data/            coppe_2526/ (COPPE NAZIONALI 2025-26: 662 partite, 18.566 righe
                 di formazione, 8.177 eventi col minuto. 204 partite senza
                 formazione, dichiarate. Leggere il suo README PRIMA di usare
                 il punteggio)
                 {serie_a,premier_league,la_liga,bundesliga,ligue_1}_matches.csv
                 (SNAPSHOT congelati, versionati — schema IDENTICO, ordine
                 colonne compreso: lo verifica test_schema_identico_tra_leghe.
                 40 colonne: dalla Fase 133 ci sono anche home_goals_ht /
                 away_goals_ht, i gol all'INTERVALLO — 16.111/16.111 partite,
                 un solo buco dichiarato)
                 club_fixtures[_{lega}].csv (calendario di club completo)
                 correzioni_dichiarate.csv (registro R3: ogni correzione ai dati,
                 con valore-prima, motivo, fonte, chi ha deciso e quando)
                 estimates/ (SOLO stime dichiarate, §5 — regole nel suo README)
                 football_data_raw/ (CSV grezzi football-data della Serie A)
                 ricerca_esterna/ (fonti esterne dell'audit: JSON footiqo, i
                 calendari di coppa per lega, manifest con sha256 e URL)
                 outright_snapshots/ (prezzi outright live, uno per giorno)
                 squad_value_2526_transfermarkt.csv (fonte secondaria, regola R2)
                 football.db (SQLite, rigenerabile, NON versionato)
files/           dati GREZZI versionati: i bundle football-data/Understat di
                 Premier e Liga (Fase 54, input di build_league_snapshot) e il
                 dataset player_scores (valori rosa, Fase 67). Nati perche' la
                 rete era bloccata; la rete e' tornata (Fase 100) ma i bundle
                 RESTANO — sono la fonte congelata di quelle due leghe e piu' di
                 uno script li legge. Vedi files/README.md
worldcup/        esperimento Mondiali, SEPARATO e a bassa fiducia (ancora vuoto):
                 modello giocattolo, non un test del motore
.github/         workflow (e file-trigger) di scraping/import: betexplorer,
                 import_dataset, kaggle-ou-probe
docs/DIARIO.md   narrazione passo-passo con ragionamento (le decisioni e il perché)
docs/GLOSSARIO.md  ogni termine del progetto in 1-2 righe, con la fase che lo
                 introduce; dove una definizione è caduta la voce lo dice
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
docs/PIANO_DATABASE_GIOCATORI.md   bozza (29/07/2026, richiesta utente):
                 database giocatore per giocatore (minuti, formazioni,
                 gol/assist, event data, affaticamento da nazionale) ESTESA
                 lo stesso giorno ad arbitri e allenatori (club/nazionali,
                 incl. competizioni europee) — cosa raccogliere in ordine di
                 costo, schema proposto, fonti valutate/verificate (games.csv
                 di davidcariboo/player-scores da' arbitro+allenatore al
                 >99,7% anche su CL/EL/Conference), idee d'uso NON ancora
                 decise. Pista 21 di PISTE.md; nessun dato ancora importato
docs/betfair_api/  COPIA DI LAVORO della documentazione API Betfair (78 pagine
                 dall'Exchange API su Atlassian + la Historical Data API), con
                 fonte e data dichiarate in testa a OGNI file. Ri-generabile con
                 scripts/fetch_betfair_docs.py. Esiste perche' la Fase 109-bis ha
                 pagato un bug (campo `img`) per non aver letto la specifica
                 prima di scrivere il parser: leggerla e' un passo, non un extra
docs/CENSIMENTO_FONTI.md   censimento a 13 agenti di TUTTE le fonti (01/08/2026):
                 ~1.100 campi, cosa usiamo e cosa no, con la colonna che conta —
                 mai-provato contro gia-bocciato. 12 occasioni dopo il filtro, e
                 9 affermazioni FALSE o non ri-calcolabili trovate nei nostri
                 stessi documenti (fra cui il f=0.4396 usato sui cartellini, dove
                 il vero e 0.3200)
docs/MANUALE_SOPRAVVIVENZA.md   conoscenza operativa dell'ambiente (rete
                 raggiungibile, limiti degli strumenti MCP, fatti su GitHub
                 Actions, fonti esterne valutate/scartate)
docs/CACCIA_OU_2017_19.md   piano dedicato per l'ultimo buco dati reale (O/U
                 di CHIUSURA 2017-19; l'apertura e' dato reale dalla Fase 73).
                 CHIUSO alla Fase 100: il dato esiste (1xBet via footiqo) ma NON
                 e' stato inserito — un solo book, peggiore della stima come
                 proxy della media multi-book
docs/BETEXPLORER_SCRAPER.md   lo scraper della Fase B di quella caccia
                 (`scripts/scrape_betexplorer.py` + workflow GitHub Actions)
docs/audit_5_leghe/   gli 11 report integrali dell'audit a 5 leghe (Fase 100) +
                 REGOLE.md + numeri/ (i JSON grezzi dietro ogni tabella).
                 Verbale esteso di cio' che il DIARIO riassume
docs/AUDIT_FASI_80_100.md   verbale dell'audit delle ultime 20 fasi (Fase 101):
                 ogni rilievo con evidenza, stato (corretto / da decidere) e
                 rimando al punto del repo
lavoro_aperto.md (RADICE) INDICE unico del lavoro aperto: Fase 78, le 17 piste
                 ancora aperte, le caselle vuote della PANCHINA (134 dopo
                 l'ingresso di Bundesliga e Ligue 1: la matrice e' passata da 4
                 a 6 colonne; erano 138 prima che la riga COM-Poisson uscisse
                 dalla matrice alla Fase 101), Tier 2/3,
                 i tre punti operativi e il brainstorming sulla routine
                 (aggiornamento giornaliero, movimento quote, notizie e
                 formazioni). NON e' una fonte di verita': se diverge da
                 PISTE/PANCHINA, hanno ragione loro
newseason.md     (RADICE, file DEPERIBILE) piano operativo per l'inizio della
                 stagione 2026-27 + brainstorming su fonti nuove e automazione.
                 Contiene cio' che NON si recupera dopo il calcio d'inizio
                 (previsioni congelate, traiettoria delle quote, formazioni).
                 Da archiviare a stagione avviata: cio' che sopravvive va
                 spostato in PISTE/DIARIO/MANUALE
tests/           test unitari (1.468 verdi al 08/08/2026), fra cui i guardiani
                 strutturali: schema identico fra le 5 leghe, e MARKET_ENGINE
                 che elenca le stesse leghe di LEAGUE_CONFIGS
                 test_metrics.py (Fase 137): i VALORI esatti di Brier/log-loss/
                 devig, calcolati a mano. Esiste perche' brier_1x2 non aveva un
                 solo riferimento in tests/ e log_loss_1x2 solo asserzioni
                 relazionali, che sopravvivono a una formula sbagliata purche'
                 monotona. Ogni numero del progetto passa di li'
```

---

## 5. Convenzioni sui dati

- **Offline-first**: la pipeline legge lo **snapshot congelato** della lega
  (`data/{serie_a,premier_league,la_liga,bundesliga,ligue_1}_matches.csv`,
  versionati). Si scarica dalle fonti solo con `--refresh`/`force_download`. Così
  i backtest sono riproducibili identici. Vale anche ora che la rete è tornata
  raggiungibile (Fase 100): la raggiungibilità non cambia la regola, lo snapshot
  resta la fonte dei backtest.
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

### 5-ter · RACCOGLIERE TUTTO (decisione utente, 01/08/2026)

**La regola.** Quando una fonte offre un dato, lo si **prende**, anche se oggi
non serve e anche se non si vede a cosa possa servire. *«Magari un domani
potrebbe esserlo. I dati prendiamoli, poi se non li usiamo è un altro conto.»*
Raccogliere e usare sono due decisioni separate, e la prima non richiede di
saper rispondere alla seconda.

**Perché è una regola e non un'inclinazione.** Un dato non raccolto al momento
giusto spesso **non è più recuperabile**: le quote si muovono e non tornano
indietro, le formazioni si sanno un'ora prima, un sito cambia struttura, un
file caricato a mano vive in una cartella temporanea. Il costo di tenere una
colonna in più è disco; il costo di non averla presa è la domanda che non si
potrà mai fare.

**L'unica eccezione, e come si applica.** Si può lasciare fuori solo un dato
**proprio inutile o assurdo** — e il caso tipico è uno solo: il **duplicato
esatto e algoritmico**, cioè una vista che si rigenera dall'altra in poche
righe (verificato a zero celle divergenti, non a occhio). In ogni caso:
⚠️ **si chiede SEMPRE conferma all'utente prima di escludere qualcosa.**
Non è una decisione da prendere da soli, nemmeno quando sembra ovvia.

**Si conserva l'ORIGINALE come consegnato**, non solo la versione normalizzata.
Dove il file di lavoro è generato da noi (una conversione, un reshape, una
selezione di colonne), l'originale è **l'unico modo per accorgersi di un bug
nella conversione**: senza, un errore nostro diventa indistinguibile dal dato.
*(Caso: le statistiche di squadra 2025-26 — di tre leghe su cinque esisteva
solo l'`.xlsx`, e il CSV l'abbiamo prodotto noi. Archiviati gli originali,
`originale_squadra.xlsx` in ogni raccolta: 11 MB, e la fedeltà della nostra
conversione è ora verificabile — misurata, 569.700 celle, 0 divergenti.)*

**Cosa questa regola NON rilassa.** Raccogliere di più non abbassa nessuna delle
soglie che valgono sul dato raccolto:
- la **provenienza** va dichiarata (R2) e la posizione di licenza pure;
- nessuna **modifica a mano**, mai (R3);
- un dato in più è anche un **finto pieno** in più da cercare (R6): più colonne
  raccogliamo, più zeri-che-significano-«non lo so» possono entrare;
- ogni colonna dichiara la propria **disponibilità temporale** (R8) — raccogliere
  un dato `post` non lo rende utilizzabile per prevedere la partita che l'ha
  prodotto;
- **raccolto ≠ usato**: un dato inserito e mai letto da nessun modello è uno
  stato legittimo e va scritto come tale in `docs/DATI.md`, non nascosto.

---

## 5-bis. Regole sui dati sporchi (non negoziabili)

Nate durante l'audit riga-per-riga delle 5 leghe, pagate tutte con un errore
vero. Valgono per ogni dato che entra nel progetto.

**R1 · Il dato è il risultato del CAMPO, non quello del tribunale.** Dove una
partita è stata riassegnata a tavolino, lo snapshot registra ciò che è successo
in campo: i mercati si regolano sul fischio finale, ed è quello il processo che
il modello stima. Ogni caso analogo va istruito **singolarmente** — mai una
regola automatica — e registrato. *(Caso: Union Berlin-Bochum 14/12/2024, 1-1
sul campo, 0-2 assegnato dal tribunale sportivo.)*

**R2 · Dove la fonte primaria non copre, si usa una fonte secondaria
dichiarata**, con la scala misurata contro la primaria dove entrambe esistono —
mai innestata in silenzio. *(Caso: valori rosa 2025-26 da Transfermarkt.)*

**R3 · Nessuna modifica a mano ai dati, mai.** Ogni correzione vive in un
registro (cosa, perché, fonte, chi ha deciso, quando) e viene applicata da uno
script **idempotente** che verifica il valore-prima cella per cella e si ferma
se non corrisponde. Un numero cambiato a mano è un numero che nessuno potrà più
spiegare.

**R4 · Un'anomalia si dichiara anche quando NON è un errore.** Metà delle cose
trovate in un audit sono legittime e sorprendenti: vanno scritte lo stesso,
altrimenti la sessione dopo le ri-trova e le "corregge".

**R5 · Procedura per una riga che sembra corrotta**, in quest'ordine:
  1. **spiegare prima di accusare** — l'impossibilità fisica va verificata sul
     dato più fine della *stessa* fonte, mai dedotta da una regola generale.
     *(Lezione pagata: un xG di 0.00 con un gol segnato sembrava impossibile;
     il dato tiro-per-tiro mostrava 0 tiri e un autogol avversario. Il dato era
     giusto, era il controllo a essere cieco.)*
  2. **diagnosticare con informazione indipendente** — un'altra colonna, un'altra
     fonte, un altro mercato della stessa partita;
  3. **cercare il dato vero**, e cercarlo davvero: prima dentro la fonte (altri
     formati, altre colonne), poi fuori, rispettando i `robots.txt`;
  4. **stimare solo se il dato vero non esiste**, con errore misurato dove la
     verità esiste e una baseline onesta di confronto;
  5. **registrare tutto, errori compresi** — le correzioni ritirate restano nel
     registro con il motivo, altrimenti la sessione dopo le rifà.

**R6 · Il buco peggiore non è il `NaN`: è il finto pieno.** Un dato mancante e
dichiarato è innocuo. Il pericolo è il valore che *sembra* una misura e non lo
è: un segnaposto della fonte, uno zero che significa "non lo so", una colonna
copiata da un'altra epoca. Nessun confronto snapshot-contro-fonte lo vede,
perché il dato **coincide** con la fonte. Si scopre solo scendendo al livello
più fine (il tiro-per-tiro sotto l'xG aggregato) o incrociando fonti
indipendenti. Ogni audit deve cercarli esplicitamente. *(Casi trovati: un xG
segnaposto su 16.110 partite; 1.603 celle `midweek_europe` a 0 per partite di
coppa che il calendario non copriva.)*

**R7 · Ogni statistica di testa deve avere il suo intervallo, e ogni "non c'è
effetto" la sua misura di potenza.** In cinque casi su sette, in una verifica
avversariale sistematica, il difetto non era il numero ma la statistica scelta
per raccontarlo: un conteggio di celle che non distingue il vero dal placebo, un
ECE senza intervallo letto come conferma, una dicotomia fra "significativo" e
"non significativo" mai testata come differenza.

**R8 · Ogni dato porta con sé il MOMENTO in cui diventa noto.** Un dato non è
solo un valore: è un valore **e** l'istante da cui è disponibile. Nella stessa
tabella convivono per natura dati noti **prima** del fischio d'inizio (arbitro
designato, formazione ufficiale, meteo previsto, quote, valore rosa) e dati che
esistono **solo dopo** (minuti giocati, gol, cartellini, xG, possesso). Usare i
secondi per prevedere la partita che li ha prodotti è **look-ahead**: l'errore
più facile da commettere e più difficile da vedere, perché il numero è giusto —
è il *momento* a essere sbagliato. Quindi:
  - ogni colonna di ogni tabella dichiara la propria **disponibilità
    temporale**: `pre` (nota prima del fischio), `post` (esiste solo a partita
    finita), `statico` (anagrafica che non dipende dalla partita);
  - una feature di backtest può usare **solo** colonne `pre` della partita in
    corso, oppure colonne `post` di partite **precedenti** (ed è questa la forma
    normale: "quanti gol ha fatto *finora*", mai "quanti ne fa oggi");
  - dove una tabella mescola i due tipi — è normale che lo faccia — la
    separazione vive nella **documentazione della colonna**, non nella testa di
    chi scrive il codice.

*(La distinzione non nasce oggi: esisteva già come «retrospettivo ≠
prospettico» in `data/stagione_2026_2027/README.md` §3-bis, ma solo in quel file
e solo a livello di blocchi di dati, mai colonna per colonna. La Fase 92 ha
scoperto che la regola anti-look-ahead del progetto **non aveva nemmeno un
test**; il fronte del database giocatori — dove ~30 campi nuovi mescolano i due
tipi — l'ha resa una regola generale.)*

---

## 6. Stato corrente e prossimi passi

> Questa sezione è un **istantanea sintetica** dello stato attuale. Il racconto
> completo e sempre aggiornato vive in `docs/DIARIO.md` (con un **indice per
> archi narrativi** in testa) e nella tabella «Tutti gli esperimenti» del
> `README.md`; la rosa dei modelli in `docs/PANCHINA.md`. Aggiorna QUESTA
> istantanea quando cambia lo stato di fondo, non a ogni fase.

**Dove siamo (istantanea aggiornata alla Fase 101-ter + integrazione delle 5 leghe).**
Il progetto è passato da "un modello Dixon-Coles sui gol" a **due motori
complementari**, su **5 leghe** (Serie A, Premier, La Liga, **Bundesliga,
Ligue 1**), 9 stagioni ciascuna, **16.111 partite**:

1. **Dixon-Coles gol+xG** (`src/models/dixon_coles.py`) — il predittore
   *standalone*, senza quote: config per-lega in `src/config.py`
   (emivita 365g, shrinkage 1.5, blend xG α=0.75, δ neopromosse
   0.23/0.33/0.22/**0.28/0.19**),
   + la **φ(|λ−μ|)** della Fase 35 sulla famiglia-pareggio — attiva **solo dove è
   misurata utile** (Serie A; le altre quattro leghe girano col motore liscio,
   `src.config.MARKET_ENGINE`). Batte nettamente le
   baseline ma **non il mercato** (gap 1X2 +0.0167 in Serie A — valore al codice
   di HEAD, dopo il fix del prior della Fase 92; il +0.0165 delle fasi
   precedenti è PRE-fix; ordine simile nelle altre leghe).
2. **Market-implied** (`src/models/market_implied.py`) — il *motore di pricing*:
   inverte le quote 1X2+O/U nei λ,μ del mercato e ne deriva **ogni mercato Tier
   1** dalla matrice DC. Batte il DC-da-gol su 13/14 mercati sulle 3 leghe
   storiche (Fasi 26/76) e su **15/15** nelle due nuove; funziona anche
   partendo dall'**apertura** (25/25 mercati contro il DC). È il **titolare**
   quando ci sono le quote; il DC è il fallback senza quote.

**Le due leghe nuove non hanno cambiato le conclusioni: le hanno replicate.**
Il DC batte la baseline e non il mercato (gap +0.0181 e +0.0190, dentro la
forchetta delle altre); le curve di ri-taratura sono piatte 5 leghe su 5; e
**nessuna leva del mercato si replica**: router θ negativo (0/25 mercati),
φ(|λ−μ|) e power-devig bocciati, beat-the-close chiuso (in Bundesliga
*peggiora* con CI conclusivo). Il θ divide le leghe in due famiglie — "latine"
≈1.24 dove la sotto-dispersione paga, e Premier/Bundesliga/Ligue 1 ≈1.08-1.10
dove non paga. Il tetto è **informativo**, e ora è misurato su 5 campionati.

**⚠️ Diagnosi CORRETTA alla Fase 92 (era invertita per 80 fasi).** Il gap col
mercato **NON** «vive quasi tutto nel pareggio»: la scomposizione esatta
(chain rule, ricompone a 6 decimali) dice **12% massa-pareggio / 88%
discriminazione casa-ospite** in Serie A (5.5/94.5 in Premier, 15/85 in Liga).
L'errore era logico: `P(12)=1−P(X)` è un'identità, quindi il mercato «12» —
usato come prova che «chi vince» fosse a posto — misura ESATTAMENTE la massa del
pareggio. Conseguenza: le leve sul pareggio (12b, 18, φ35) rendevano poco perché
aggredivano il 12%. Cercare l'informazione mancante nella **discriminazione**.

**Le scoperte che reggono.** (a) Il mercato di **chiusura ingloba il modello**:
α\*=0 sull'1X2 (Fase 16) e sul GG/NG (α\* medio 0.060, α\*=0 nel 70% dei fit —
audit 5 leghe). Non lo si batte in ROI: la config ufficiale dà **ROI −15.8% su
866 scommesse** (6 stagioni, rimisurato al codice di HEAD alla Fase 101-bis) —
**non usare per scommettere soldi veri**. ⚠️ «α\*=0 *ovunque*» sarebbe però
troppo: sull'handicap asiatico α\* = **1.08**, con IC bootstrap che **esclude**
lo zero (il test non era mai stato eseguito nella Fase 88; rifatto alla Fase 101).
(b) I gol dati i tassi del mercato sono **sotto-dispersi** (double-Poisson θ≈1.2):
`sharpen_1x2` batte la chiusura devigata in log-loss con CI conclusivo (non in
ROI), ed è il **router v3** adottato (`price_markets`, θ 1.225 mercato / 1.138 DC
— su griglia fine l'argmin sarebbe θ=1.18, ma la differenza è nel rumore, Δ
−0.00027 IC95 [−0.00083, +0.00027], Fase 101: il valore in config resta 1.225).
Ma è una proprietà della **chiusura Serie A** (meno liquida): non replica su
Premier/Liga (Fase 53). (c) Il θ del router è **per-contesto** (lega × epoca):
~1.2 in Serie A/Liga, ~1 in Premier, e cresce nel tempo (Fasi 75/81). (d) Il
**valore residuo** è prezzare *calibrato* i ~17 mercati che il book non quota
(risultato esatto, multigol, total-squadra… e il GG/NG, per cui una quota di
chiusura esiste solo nel 2017-20 di un book, §1.8) e le **correzioni per-lega**
(φ35 famiglia-pareggio, θ router); la Fase 82 ha verificato per via diretta che
l'oracolo è **calibrato e indovina quanto il mercato** (non di più).

**Una famiglia di mercati NUOVA (Fase 89).** Il mercato **campione di stagione**
(outright) è il primo che NON si deriva dalla matrice di una partita: dipende da
380 partite congiuntamente + la regola di classifica, quindi va **simulato**
(`src/models/season_sim.py`, Monte Carlo di 20.000 stagioni). Batte le baseline
(log-loss 1.1994 contro 1.4293 della più forte — persistenza dalla classifica su
2 stagioni: guadagno +0.2299, IC95% [+0.0108,+0.4542], 14/24 stagioni, e il
vantaggio è **quasi tutto Premier**) ma è **sovra-confidente** (dichiara 60.1%
sul favorito, ne azzecca 41.7%): mancano
l'incertezza dei parametri e la loro evoluzione in-season — e la sovra-confidenza
è stata **confermata dall'esterno** dal primo confronto con un mercato outright
vero (Fase 95, prezzi live Polymarket: ordinamento in accordo, corr 0.95-0.98, ma
troppa massa sul favorito). Va letto sapendo che a n=24 il risultato è **fragile
alla specificazione della baseline** (Fase 98) e che l'outright **non è testabile
prospetticamente** (servirebbero 57 stagioni-lega). Non esistono quote
outright storiche → «battiamo il mercato» NON è testabile all'indietro. È una
pista **ricorrente**: si riprezza a ogni inizio stagione (promemoria operativo in
`docs/PISTE.md` §4-bis). Lo strumento per le quote live è
`scripts/fetch_polymarket_open.py` (Polymarket è raggiungibile dall'ambiente).

**Le famiglie FUORI dalla matrice dei gol (Fasi 96-99).** Corner e cartellini
sono un processo **diverso** dai gol (non ridondante) e sono prezzabili
walk-forward sulle 3 leghe storiche; i mercati **Tier 3** (Halftime, Second Half,
risultato esatto) si ottengono ri-scalando i tassi con la frazione di gol nel
primo tempo, **misurata** (f = 0.4396 [0.4338, 0.4458], primo tempo
Poisson-compatibile, tempi quasi indipendenti) e battono la baseline con IC
conclusivo. Il **Tier 2** (handicap asiatico) è l'**unico** mercato del listino
validato contro una quota esterna e indipendente: Brier 0.2044 vs 0.2044 — il
router **pareggia** col mercato sharp (ΔBrier −0.000136 [−0.000362, +0.000083],
IC a cavallo dello zero: «pareggio», non «vittoria» — formulazione rettificata
alla Fase 101). Su queste famiglie le correzioni
di forma (binomiale negativa, Fase 98) e di centro (correzione di livello, Fase
99) valgono il terzo decimale o meno: **il tetto informativo vale anche qui**.
Il residuo vivo è uno solo, ed è localizzato: il **secondo tempo è mal
calibrato** mentre il primo, che passa per lo stesso codice, non lo è → è
**game-state**, e chiede un modello a due stadi (1T indipendente → 2T
condizionato al punteggio dell'intervallo). È anche il primo mattone dell'in-play.

**Due regole di metodo nate qui, valide ovunque.** (1) Ogni feature
*moltiplicativa* va confrontata col suo **controllo di solo livello**, altrimenti
si misura la deriva del modello base e la si attribuisce alla feature (Fase 98:
l'85% del guadagno apparente dell'arbitro era livello). (2) Un bias misurato su
un **pool** non autorizza una correzione **prospettica**: prima si misura se
**persiste** (autocorrelazione fra fold, con CI). Fase 99: il bias di livello dei
conteggi non persiste (10/18 stesso segno) e correggerlo **peggiora** con IC
conclusivo in 5 celle su 8. **Misurato ≠ prevedibile.**

**Cosa è chiuso (non riproporre senza informazione nuova).** Tutti i dati
INTERNI sono esplorati (gol/xG/npxG/PPDA/deep/valore-rosa/assenze/riposo/forma/
stakes: ridondanti o rumore, Fasi 4c-33); GBM bespoke per-mercato (bocciato
4 volte); Poisson bivariato, copule di Frank, ensemble emivite, draw-inflation,
ρ dinamico, zero-inflazione, Rue-Salvesen, GAS/state-space (tutti chiusi per
test o per argomento); coda-forma a 1 e 2 parametri (Fasi 85-87);
più-storia-batte-meno (Fase 25). Il tetto è **informativo**, non architetturale.
⚠️ La **COM-Poisson** della Fase 85 non è una famiglia alternativa da riaprire:
è la **stessa double-Poisson riparametrizzata** (`dp(θ) ≡ COM-Poisson(ν=θ)`
mean-matched — coincidono a ≤5e-06 sull'exact-score log-loss e ≤2e-05 sulle
code), quindi **non** è una conferma indipendente di nulla (rettifica Fase 101).

**Prossimi passi (idee, non impegni).** In ordine di rapporto valore/costo,
dettaglio in `docs/PISTE.md`:
- **uso pratico**: `scripts/predict.py` è il tool (DC senza quote / market-implied
  con `--odds`), reso **per-lega** su ENTRAMBI i modelli: M1 alla Fase 83-bis,
  M2 (θ/φ0/κ/sharpen del router) alla **Fase 92-bis** con la mappa
  `src.config.MARKET_ENGINE` — Premier e Liga escono col motore LISCIO. Dalla
  **Fase 101** anche Bundesliga e Ligue 1 hanno la loro voce esplicita (motore
  liscio, stato MISURATO e non solo prudenziale: router θ negativo su 0/25
  mercati in entrambe), e un test verifica che `MARKET_ENGINE` e
  `LEAGUE_CONFIGS` elenchino le stesse leghe. Nessun residuo aperto sul M2;
- **test prospettico 2026-27** (Fase 78, stato APERTO): previsioni congelate
  prima del kickoff e scorate dopo — il gold standard, da completare al primo
  turno con quote reali (`experiments/prospettico_2026_27.md`). ⚠️ Con la
  potenza misurata alla Fase 98 va gestita l'aspettativa: **una giornata su 3
  leghe vale il 9,8% di potenza**, e per l'80% sull'1X2 servono **574 partite**
  (2.254 sul GG/NG, 2.988 sull'O/U 2.5). È un test che si accumula, non che si
  chiude in un weekend;
- **informazione DAVVERO nuova** (formazioni ufficiali pre-partita, quote
  live/di apertura raccolte prospetticamente): l'unica leva non ancora esaurita —
  e dalla Fase 100 la rete è tornata raggiungibile, quindi raccoglierla costa
  meno di prima (elenco aggiornato delle fonti che rispondono in
  `docs/MANUALE_SOPRAVVIVENZA.md` §1);
- **mercati non ancora coperti**: HT/FT congiunto, le combinazioni e il live —
  il Tier 2 (handicap asiatico) e il Tier 3 di base sono già coperti (Fasi 88/96/98).

---

## 7. Portare il modello su un'altra lega (Premier, ecc.) — NON copiare i numeri

**La procedura completa e collaudata (passi 0-5, EDA, tracer, ri-taratura,
motore, leve della rosa, scelta delle finestre di backtest, checklist) vive in
`docs/PLAYBOOK_NUOVA_LEGA.md`** — scritta dopo l'onboarding di Premier e Liga
(Fasi 53-57, 79-80) e ri-usata per Bundesliga e Ligue 1 (Fase 100): per ogni lega
futura si parte da lì. Qui sotto i principi.

Le **formule** del modello sono universali; gli **iperparametri no**. Vivono in un
**unico punto di verità**, `src/config.py` (`LEAGUE_CONFIGS`), da cui `backtest.py`
legge i default: `emivita 365g`, `shrinkage 1.5`, `blend α=0.75`, `blend_signal xg`
— uguali su tutte e 5 le leghe — e `promoted_prior δ`, che è invece **per-lega**
(0.23 Serie A / 0.33 Premier / 0.22 Liga / 0.28 Bundesliga / 0.19 Ligue 1: l'unico
numero che l'evidenza ha davvero separato). La classe `DixonColesModel` ha default **neutri** (nessun
decadimento/shrinkage): la lega-specificità non è mai incisa nel modello. Aggiungere
una lega = **aggiungere una voce in `LEAGUE_CONFIGS`**, non toccare il codice.
Trasferire i numeri della Serie A uncritically lascerebbe il modello **sub-ottimo**:
prima di dichiarare un modello "buono" su una nuova lega, **ri-tara e ri-motiva ogni
numero** (regola §2-bis), perché ognuno dipende dai dati di *quella* lega:

- **δ (prior neopromosse)**: `δ = ln(gol_lega / gol_promosse)` — va ricalcolato. In
  Premier le promosse sono notoriamente più deboli → δ probabilmente **maggiore** di
  0.23. Copiare 0.23 sotto-correggerebbe. *(Confermato: Premier δ = ln(1.419/1.022)
  = 0.33. Ma attenzione al caso opposto — la **Ligue 1** ha δ=0.19, il più basso del
  campione: le promosse francesi sono le meno deboli. Il δ per-lega si adotta per
  MOTIVAZIONE STRUTTURALE, non per guadagno misurato: sulle 5 leghe il guadagno in
  log-loss è nel rumore, `src/config.py` lo dichiara riga per riga.)*
- **emivita / shrinkage**: dipendono dalla stabilità delle rose e dal rumore del
  segnale nella lega. Una lega con più turnover → emivita più corta.
- **α del blend gol/xG**: dipende dalla qualità/copertura dell'xG di quella lega.
- **vantaggio-casa `γ`**: differisce per lega (e, come emerso nelle Fasi 9-bis/30,
  **non è costante** nemmeno *dentro* una stagione — vedi audit).

Ogni ri-taratura è una fase a sé, con blocco 📐 e riga nel registro. Non esiste "il
modello": esiste *il modello tarato per la lega X*.

**Premier League e La Liga sono state aggiunte per prime (Fasi 54-57).** Dati
grezzi caricati a mano come bundle in `files/` — *all'epoca* la rete era bloccata
(dalla Fase 100 non lo è più: vedi `docs/MANUALE_SOPRAVVIVENZA.md` §1) → snapshot
congelati `data/{premier_league,la_liga}_matches.csv` via
`scripts/build_league_snapshot.py`.
Config in `LEAGUE_CONFIGS`: **identiche alla Serie A tranne δ** (Premier 0.33, Liga
0.22 — ri-tarato, ipotesi §7 confermata). Esito cross-lega: **il modello è
trasferibile** (DC+xG batte la baseline, gap col mercato dello stesso ordine, la
ri-taratura è piatta = tetto informativo universale) **ma l'edge no** (Fase 53: la
sotto-dispersione decresce con la liquidità del mercato, il tilt e il draw-bias non
si replicano — il beat-the-close è idiosincratico della chiusura Serie A). γ
(vantaggio-casa, molto più forte in Liga) è auto-fittato dal DC, non in config.

**Bundesliga e Ligue 1 sono state aggiunte dopo** (Fase 100), con la stessa
procedura ma **senza bundle manuali**: il provider era tornato raggiungibile,
quindi i dati si scaricano (`scripts/fetch_sources.py` +
`scripts/build_new_snapshot.py`, non `build_league_snapshot.py`, che legge i
bundle) e sono stati **verificati riga per riga contro la fonte** (0 differenze
su gol/date/tiri/quote/xG). δ per-lega 0.28 e 0.19; tutto il resto identico —
curve di ri-taratura piatte, 5 leghe su 5. Esito: il modello trasferisce, l'edge
no. Il dettaglio in `docs/DIARIO.md` e in `docs/audit_5_leghe/`; le regole sui
dati sporchi nate da quel lavoro in §5-bis.

**Non usare il modello per scommettere soldi veri allo stato attuale.**
