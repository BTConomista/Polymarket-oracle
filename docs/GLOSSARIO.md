# Glossario — i termini del progetto in una riga

I termini ricorrono ovunque nel [DIARIO](DIARIO.md), nel [README](../README.md) e
nella [rosa dei modelli](PANCHINA.md), ma erano definiti solo dove nascono. Qui
ognuno ha 1-2 righe e la fase che lo introduce. Ordine tematico.

Aggiornato alla **Fase 140** (5 leghe: Serie A, Premier, La Liga,
Bundesliga, Ligue 1). Dove una definizione è stata smentita da una fase
successiva la voce lo dice, con la forma del §1.4 (si marca, non si cancella).

## Il modello dei gol

- **Dixon-Coles (DC)** — il modello di base (Dixon & Coles, 1997): due Poisson
  per i gol di casa e ospite con tassi `λ, μ` in log-scala (attacco − difesa +
  vantaggio-casa), più una correzione sui 4 punteggi bassi e il decadimento
  temporale. Scritto da zero in `src/models/dixon_coles.py`. *(Fase 0-1)*
- **λ, μ (lambda, mu)** — i gol attesi di casa (λ) e ospite (μ). Da loro si
  costruisce la **matrice dei punteggi** `P(gol_casa=i, gol_ospite=j)`, da cui
  ogni mercato è una somma di celle (coerenza garantita). *(Fase 0)*
- **ρ (rho)** — la correzione Dixon-Coles che alza/abbassa i 4 punteggi bassi
  (0-0, 1-0, 0-1, 1-1) rispetto alla Poisson indipendente. `ρ=−0.06` è la
  costante **universale, mai ritarata**: lo sweep congiunto ρ×θ più ampio mai
  fatto la conferma su Serie A/Premier/Liga (i guadagni dell'asse ρ erano «θ
  sotto mentite spoglie»); l'audit a 5 leghe ha provato un ρ pooled diverso, ma
  al θ di produzione il segno si capovolge — ρ e θ sono **sostituti quasi
  perfetti**, quindi «il ρ ereditato −0.06 è innocuo». *(Fasi 1, 81, 100)*
- **γ (gamma)** — il vantaggio-casa globale, auto-fittato dal DC (più alto in
  Liga, più basso in Serie A). *(Fase 1, 55)*
- **blend gol/xG (α)** — il tasso di una squadra è una media pesata di gol reali
  e **xG** (expected goals, gol attesi dalla qualità dei tiri): `α=0.75` gol,
  0.25 xG. L'xG è il meccanismo di mean-reversion (la "fortuna" regredisce).
  *(Fase 4b)*
- **δ (delta), prior neopromosse** — il bersaglio dello shrinkage per le squadre
  senza storico (neopromosse), sotto la media: `δ = ln(gol_lega/gol_promosse)`,
  per-lega su tutte e 5 le leghe — **0.23** Serie A / **0.33** Premier / **0.22**
  La Liga / **0.28** Bundesliga / **0.19** Ligue 1 (`src/config.py`,
  `LEAGUE_CONFIGS`). *(Fasi 7, 55, 100)*
- **shrinkage / emivita** — regolarizzazione (shrinkage 1.5: tira le forze verso
  la media) e memoria temporale (emivita 365g: quanto pesano le partite vecchie).
  *(Fase 2b, 4d)*
- **φ35, φ(|λ−μ|)** — il boost dei pareggi condizionato all'**equilibrio** della
  partita: `φ(λ,μ) = φ0·exp(−κ·|λ−μ|)`, alza i pareggi quando le due squadre sono
  pari-livello. Il miglior risultato sul pareggio. **Attiva solo in Serie A**
  (φ0=0.30, κ=1.5, `MARKET_ENGINE`): in Premier l'ottimo è (0,0), in Liga è
  misurata positiva ma resta in **panchina** (φ0~0.3-0.7), in Bundesliga e
  Ligue 1 è **bocciata**. *(Fasi 35, 39, 80, 81, 100)*

## Le distribuzioni della coda

- **double-Poisson (dp) / θ (theta)** — una Poisson "concentrata": si eleva la
  PMF a θ e si rinormalizza mantenendo la media. **θ>1 = sotto-dispersione**
  (code più leggere): i gol dati i tassi del mercato oscillano ~10% meno di una
  Poisson. È il **router v3** (θ=1.225 mercato / 1.138 DC in Serie A). Il θ è
  **per-contesto**, non universale: le leghe si dividono in due famiglie —
  «latine» θ≈1.24 (Serie A 1.232, La Liga 1.242), dove la sotto-dispersione è
  forte e sfruttabile, e Premier/Bundesliga/Ligue 1 θ≈1.08-1.10 (1.085 / 1.080 /
  1.103), dove **non paga** (valle in-sample −0.0012/−0.0017 contro −0.0081).
  *(Fasi 51, 52, 75, 81, 100)*
- **sotto-dispersione / sovra-dispersione** — la varianza dei gol è *minore*
  (sotto) o *maggiore* (sovra) della media (che per la Poisson pura sono uguali).
  Il calcio dati i tassi del mercato è **sotto-disperso**. *(Fase 51)*
- **COM-Poisson** — Conway-Maxwell-Poisson, `p(x) ∝ aˣ/(x!)ᵛ`. **Non è un modello
  a parte né una famiglia alternativa**: la double-Poisson mean-preserving del
  router *è* una COM-Poisson con ν=θ (dimostrato dalla forma di `_dp_pmf` e
  verificato numericamente — coincidono a ≤5e-06 sull'exact-score log-loss e a
  ≤2e-05 sulle code). Conseguenza: la Fase 85 **non** è una conferma indipendente
  del θ, ed è la stessa curva riscritta con un'altra lettera; su griglia fine
  l'argmin è **θ=1.18** (Δ −0.00027, IC95 [−0.00083, +0.00027]: nel rumore), non
  1.225. *(Fasi 85, 101, 101-bis)*
- **binomiale negativa (NB)** — distribuzione sovra-dispersa: bocciata sui gol
  (non sono sovra-dispersi dati i tassi) e **conclusiva ma trascurabile** sui
  conteggi (corner Δ +0.00103 [+0.00062, +0.00143]; i gialli di Serie A sono
  addirittura sotto-dispersi, 0.901, e la NB collassa da sola sulla Poisson).
  *(Fasi 27, 98)*

## Le quote e il mercato

- **devig / devigging** — togliere il **margine** (vig) del bookmaker dalle quote
  per ottenere le probabilità implicite "pulite" (somma 1). Il **devig
  moltiplicativo** (le probabilità grezze riscalate a somma 1) è la fonte unica
  del progetto; il **devig di Shin** (assume trader informati) è migliore ma in
  panchina. *(Fase 1, 52-ter)*
- **overround / margine (vig)** — quanto la somma delle probabilità implicite
  supera 1: è il margine del book (~5% sull'1X2, ~2.7% sull'handicap asiatico).
- **power-devig** — il devig alternativo `p_i ∝ (1/o_i)^{1/η}`, con η tarato sul
  log-loss 1X2 passato (η≈0.895-0.909: accentua i favoriti). **Bocciato**: sul
  GG/NG vale −0.0003 con CI che include lo zero, non è mai utile in nessuna
  variante, e resta bocciato anche sulle due leghe nuove. *(Fasi 38, 50, 100)*
- **market-implied** — il **motore di pricing**: inverte le quote 1X2+O/U nei
  λ,μ del mercato (`implied_lambda_mu`) e ne deriva ogni mercato dalla matrice
  DC. È il titolare quando ci sono le quote. *(Fase 24, 26)*
- **router (v3), `price_markets`** — la logica che, dai λ,μ, prezza ogni mercato
  con la forma giusta: double-Poisson (θ) sui marginali + φ35 sulla
  famiglia-pareggio. La mappa lega→motore vive in `src.config.MARKET_ENGINE`:
  Serie A col router, **Premier, Liga, Bundesliga e Ligue 1 col motore LISCIO**
  (θ=None, φ0=0) — stato **misurato**, non prudenziale. *(Fasi 44, 52, 101)*
- **dp_lvl / `sharpen_1x2`** — la lettura "affinata" della chiusura: corregge i
  livelli dei tassi impliciti + double-Poisson. Batte la chiusura devigata in
  **log-loss** 1X2 (non in ROI), proprietà della chiusura Serie A. *(Fase 51)*
- **chiusura vs apertura** — le quote **di chiusura** (poco prima del kickoff)
  sono lo stimatore più efficiente; quelle **di apertura** sono meno affilate.
  L'affinamento open→close vale ~+0.0020 sull'1X2. *(Fase 14)*
- **Pinnacle** — il bookmaker "sharp" (più efficiente, margine basso), usato come
  benchmark duro (colonne `PS*`/`PSC*`). *(Fase 61, PISTE #9)*
- **Polymarket / Smarkets** — le due **borse** (non bookmaker) raggiungibili che
  quotano gli outright di stagione, e sono **complementari**: entrambe quotano il
  campione di tutte e 5 le leghe, e Smarkets aggiunge ciò che Polymarket non ha
  mai — la **retrocessione** (solo Premier) e i piazzamenti (Premier, Liga,
  Ligue 1). Anche la liquidità è speculare, non «migliore» in assoluto per una
  delle due: sulla **Premier** Smarkets ha spread **0.11pp** contro un overround
  Polymarket del **+5.8%**; in **Serie A** Smarkets è illiquida (spread ~5-11pp)
  e resta utilizzabile solo Polymarket (overround **+7.1%**). Le due concordano
  fra loro a **0.13pp di scarto mediano** su 62 coppie di squadre. Archivio
  versionato in `data/outright_snapshots/`. *(Fasi 95, 97)*

## Le metriche e i metodi

- **log-loss / Brier** — misure di calibrazione delle probabilità (più basse =
  meglio). Il log-loss penalizza forte gli errori sicuri; il Brier è quadratico.
  Calcolate SEMPRE via `experiment_log.compute_metrics` (fonte unica).
- **walk-forward / LFO (leave-future-out)** — per ogni giornata si riallena il
  modello usando **solo** le partite già avvenute, poi si predice: nessun
  look-ahead. È l'idioma di validazione del progetto. *(Fase 1)*
- **baseline (in-sample / ex-ante)** — il predittore banale (frequenza storica
  dell'esito). *In-sample* usa la stagione di test stessa (leggermente troppo
  forte); *ex-ante* solo le stagioni precedenti (l'unica giocabile). *(Fase 15)*
- **encompassing / α\*** — il test che chiede se il modello ha informazione
  *propria* oltre al mercato: si fitta `α·modello + (1−α)·mercato`. **α\*=0
  ovunque** sui mercati-partita = il mercato di chiusura ingloba completamente il
  modello (non lo si batte in ROI). ⚠️ Attenzione a dove NON è stato calcolato:
  la Fase 88 lo dichiarava sull'handicap asiatico senza averlo mai fatto, e
  rifacendolo dà α\*=1.082 con IC95 bootstrap che **esclude** lo zero — perché il
  router non è un previsore indipendente dal mercato AH, ma una traduzione degli
  stessi λ,μ (vedi «handicap asiatico»). *(Fasi 16, 88, 101-bis)*
- **CLV (closing line value)** — quanto si guadagna/perde rispetto alla linea di
  chiusura: il metro d'oro dell'edge. Negativo per il modello, e **conclusivo**:
  −0.0022 [−0.0033, −0.0012], 45,7% di scommesse con CLV positivo. *(Fasi 14, 98)*
- **gap (col mercato)** — la differenza di log-loss tra modello e mercato di
  chiusura (1X2: +0.0167 in Serie A al codice di HEAD, log-loss 0.9799 contro
  0.9632; +0.0165 / 0.9797 era il valore PRE-fix del prior, Fase 92). **L'88%
  vive nella discriminazione casa/ospite, solo il 12% nella massa del pareggio**
  — la lettura opposta della Fase 9 era invertita, vedi la correzione nella Fase
  92. *(Fasi 9, 92, 101-bis)*
- **ROI / value-bet** — il rendimento simulato scommettendo dove il modello vede
  "valore". **−15.8%** su 6 stagioni e **866** scommesse alla quota media di
  chiusura (per stagione da −4.7% a −23.0%): non si batte il margine. Al
  **best-price** cross-book la perdita si riduce ma resta negativa. *(Fasi 15,
  86, 101-bis)*
- **CI bootstrap / P(aiuta)** — intervallo di confidenza appaiato (per-stagione)
  su un Δ; `P(aiuta)` = probabilità che la leva migliori. Un CI che include lo
  zero = non conclusivo. *(Fase 17)*
- **IC a grappoli (bootstrap a grappoli)** — quando le righe dentro una stagione
  **non sono indipendenti** (le squadre in top-4 sono esattamente 4, le retrocesse
  esattamente 3: un errore su una ne implica uno opposto su un'altra) si
  ricampionano le **stagioni**, non le righe. L'iid sottostima la varianza: sul
  guadagno **top-4** contro la persistenza l'IC passa da [+0.0037, +0.0502] a
  **[−0.0006, +0.0522]** (effetto
  di disegno DEFF=1.29) — abbastanza da fargli attraversare lo zero. *(Fase 92-bis)*
- **test dei segni** — il test binomiale bilaterale sul numero di stagioni in cui
  una variante è migliore: regge dove l'IC non regge (top-4 **19/24, p=0.0066**,
  Fase 91) e serve a verificare i verdetti dichiarati a spanne (top-4 peggiore in
  **18/24** con σ uniforme, p=0.0227, Fase 94). *(Fasi 91, 92-bis, 94)*
- **ECE (Expected Calibration Error)** — `Σ_fasce (n_fascia/n)·|media(p) −
  media(y)|` su 10 fasce equispaziate: quanto la probabilità dichiarata si
  discosta dalla frequenza osservata. ⚠️ Va letto **col suo intervallo**: il
  «siamo meglio calibrati del mercato» della Fase 93 è **declassato** (IC95
  [−0.00135, +0.00049], e il segno si inverte passando a 50 e 100 fasce).
  *(Fasi 91, 93, 101-bis)*
- **deriva di livello / controllo di solo livello** — il bias di media che il
  modello accumula in walk-forward sui conteggi (Premier cartellini −0.201,
  Serie A corner +0.352). Regola di metodo nata qui: ogni feature
  *moltiplicativa* va confrontata col suo **controllo di solo livello**,
  altrimenti si misura la deriva del modello base e la si attribuisce alla
  feature (l'85% del guadagno apparente dell'arbitro era livello). E **misurato
  ≠ prevedibile**: il bias non persiste fra fold (10/18 stesso segno) e
  correggerlo **peggiora** con IC conclusivo in 5 celle su 8. *(Fasi 98, 99)*

## I mercati (listino)

- **1X2** — esito: 1 (casa), X (pari), 2 (ospite). **Doppia chance**: 1X/X2/12.
  ⚠️ `P(12) = 1 − P(X)` è un'**identità**: il mercato «12» misura esattamente la
  massa del pareggio, non «chi vince» (è l'errore di lettura corretto alla Fase 92).
- **O/U (Over/Under)** — più/meno di N gol totali (linea standard 2.5).
- **GG/NG (BTTS)** — entrambe le squadre segnano (GG) o no (NG). ~~Era «l'unico
  mercato senza quote nei dati, quindi l'unico con spazio non ancora chiuso».~~
  **PREMESSA CADUTA (Fase 100)**: le quote GG/NG di chiusura esistono (book
  **1xBet** via footiqo, **5.337 partite 2017-20** su 5 leghe), il mercato è
  **informativo** (log-loss 0.6840 contro 0.6921 di baseline, CI conclusivo), il
  nostro miglior prezzo lo **pareggia** (6 varianti su 6 con CI a cavallo dello
  zero) e il **DC perde** (+0.0104 [+0.0063, +0.0145]; il book lo ingloba, α\*=0
  nel 70% dei fit). *(Fase 100)*
- **Tier 1/2/3** — i mercati per priorità: **Tier 1** = standard (1X2, O/U, GG/NG,
  doppie chance, total-squadra, clean sheet, scarto≥2, multigol, risultato
  esatto); **Tier 2** = handicap asiatico; **Tier 3** = HT/FT e per-tempo. *(§1.8
  del CLAUDE.md)*
- **handicap asiatico (AH)** — l'esito con un handicap a gol sulla favorita;
  prezza direttamente la **supremazia** λ−μ (ma è ridondante *come input*
  dell'inversione, corr 0.995 con λ−μ). È l'**unico** mercato del listino
  validato contro una quota esterna e indipendente (chiusura AH devigata,
  Pinnacle dove presente, 7.437 partite):
  Brier del router **0.2040** contro 0.2041 del mercato. La formulazione corretta
  è **«pareggio in Brier col mercato sharp»** (ΔBrier −0.000136, IC95
  [−0.000362, +0.000083]) — non «α\*=0 su un mercato nuovo», che non fu mai
  calcolato (vedi «encompassing»). *(Fasi 86, 88, 101-bis; PISTE #5)*
- **Tier 3 dal ri-scalamento 1T/2T** — Halftime, Second Half e risultato esatto
  si ottengono ri-scalando i tassi con la **frazione di gol nel primo tempo**,
  misurata: `f = 0.4396` [0.4338, 0.4458], primo tempo Poisson-compatibile,
  tempi quasi indipendenti. Battono la baseline con IC conclusivo (HT +0.0537,
  2T +0.0578, esatto +0.1940). *(Fase 98)*
- **game-state** — l'effetto del punteggio corrente sul comportamento delle
  squadre. È il nome del **residuo vivo** del progetto: il **secondo tempo è mal
  calibrato** (pareggio 0.3671 dichiarato contro 0.3427 reale) mentre il primo
  passa per **lo stesso codice** ed è calibrato a <0.006 → non è
  normalizzazione, è game-state. Chiede un modello a **due stadi** (1T
  indipendente → 2T condizionato al punteggio dell'intervallo), che è anche il
  primo mattone dell'in-play. *(Fase 98; pista aperta in PISTE #6-bis, e #18 per
  l'in-play vero e proprio)*
- **nudge stagionale** — la piccola correzione GG/NG di fine stagione (giornate
  35-38), opt-in, off di default. *(Fase 48)*

## La stagione intera: i mercati outright

- **mercato campione di stagione / outright** — la famiglia di mercati che **non
  si deriva dalla matrice di una singola partita**: campione, top-4,
  retrocessione, piazzamenti. Dipendono da **380 partite congiuntamente** più la
  regola di classifica, quindi vanno **simulati**, non derivati. *(Fase 89)*
- **`season_sim` / simulazione Monte Carlo di stagione** —
  `src/models/season_sim.py`: si fitta il DC alla data della prima partita
  (nessun dato futuro), si generano le 380 matrici dei punteggi, si campionano
  **20.000 stagioni** intere e si compila la classifica con gli **spareggi
  ufficiali per lega** (scontri diretti in Serie A/Liga, differenza reti in
  Premier). Batte la baseline più forte (log-loss **1.1994** contro **1.4293**
  della persistenza su 2 stagioni) ma è **sovra-confidente**: dichiara 60.1% sul
  favorito e ne azzecca 41.7%. Due proprietà non ovvie: l'**ordine del calendario
  è irrilevante** (con forze costanti contano solo gli incontri, non la
  sequenza), e gli **spareggi non sono pedanteria** (parità in vetta nel 5.1%
  delle stagioni simulate). Non esistono quote outright storiche → «battiamo il
  mercato» **non è testabile all'indietro**. ⚠️ **Ridimensionato dalla Fase 98**:
  il confronto è **fragile alla specificazione della baseline** — una griglia
  diversa dà **1.3816** invece di 1.4293, ed è *instabilità LOO a n=24*, non una
  «baseline meglio tarata» — e l'outright non è testabile nemmeno in avanti
  (servirebbero **57 stagioni-lega**). Resta «fragile», non «perdente».
  *(Fasi 89, 98)*
- **deriva di forza in-stagione** — la varianza che manca al simulatore: le forze
  sono stimate a inizio stagione e tenute ferme per dieci mesi, quindi la
  classifica simulata esce **compressa** (la dispersione reale supera la simulata
  in 21 stagioni su 24). Misurata su 480 squadre-stagione confrontando il fit di
  inizio con quello di fine, e **non è uniforme**: neopromosse sd **0.299**,
  tutte le altre **0.157**. In produzione `DRIFT_SD = {promoted: 0.30, other:
  0.16}` (`src/config.py`), iniettata come `attacco +ε/2, difesa −ε/2` (la forza
  netta si sposta di ε, il livello-gol della lega no). **Adozione per-mercato**:
  ⚽ retrocessione (+0.0095, IC95 [+0.0020, +0.0180]; calibrazione delle
  neopromosse da +6.1pp a +2.8pp), nulla sul campione (+0.0017, 9/24), ❌ top-4
  (peggiora in 17/24, ECE da 0.0140 a 0.0203 — *era già calibrato*). Confermata
  poi da due metri **esterni**: i prezzi Polymarket sul campione (Fase 95-bis) e
  la retrocessione Premier di Smarkets (MAE 8.84pp → **7.32pp**, Fase 97).
  *(Fasi 94, 95-bis, 97)*
- **coda a zero** — il difetto strutturale del simulatore all'altro capo della
  classifica: senza incertezza **sui parametri** (solo sui risultati) le squadre
  forti ricevono P(retrocessione) esattamente **0.0%** dove il mercato dà 7.6% e
  1.1% — e uno zero su un evento non impossibile costa log-loss infinito se
  accade. Pista aperta. *(Fase 97)*
- **KL(noi‖mercato)** — il metro degli outright quando l'esito non c'è ancora:
  `Σ p_noi·log(p_noi/p_mkt)`, che penalizza proprio l'eccesso di massa dove il
  mercato non la mette. Contro Polymarket sul campione 2026-27: **0.181** Serie A
  / **0.242** Premier / **0.056** Liga; con la deriva scende dove eravamo
  sovra-confidenti (−0.0360, −0.0382) e **sale** dove eravamo già allineati
  (+0.0179 Liga). Regola che ne esce: *l'incertezza aggiunta paga solo dove manca
  davvero*. ⚠️ «più vicino al mercato» non è «più corretto». *(Fasi 95, 95-bis)*

## I dati: qualità, buchi e stime

- **snapshot congelato** — `data/{lega}_matches.csv`, versionati e con schema
  identico (ordine delle colonne compreso): la pipeline è **offline-first** e li
  legge sempre, così i backtest sono riproducibili identici. Si riscarica dalle
  fonti solo con `--refresh`. *(CLAUDE.md §5)*
- **stima dichiarata** — un dato di mercato mancante ricostruito coi modelli, che
  vive solo in `data/estimates/` come **probabilità** (mai come quota) con errore
  dichiarato, mai usato per simulare ROI. Catalogo completo in [DATI.md](DATI.md).
  *(Fase 62-bis)*
- **E3** — lo **stimatore della chiusura O/U 2.5** dove il dato non esiste
  (2017-19, tutte e 5 le leghe): una regressione logit **pooled cross-lega**
  ```
  logit(p_close) = β0 + β1·logit(p_open) + β2·Δlogit(H) + β3·Δlogit(D) + β4·Δlogit(A)
  ```
  cioè la linea O/U **di apertura** più il **movimento 1X2** apertura→chiusura
  (Δlogit). Vinse il bakeoff della Fase 62-bis (MAE 0.0117 contro 0.0132 di M4) e
  ha poi resistito a **8 leve ortogonali** (interazioni, calendario, ridge, GBM,
  dispersione). Errore dichiarato oggi: **MAE ~0.014 nel regime d'uso** (fit su
  stagioni successive, l'unico possibile) e ~0.012 in interpolazione; fit pooled
  su 12.457 partite e 5 leghe. *(Fasi 62-bis, 72, 73, 100)*
- **grana (o grano) di una tabella** — che cosa è **una riga**: una partita,
  una squadra in una partita e in un periodo, un giocatore in una partita, un
  evento, una posizione. Non è un dettaglio di impaginazione ma
  **informazione**: lo stesso dato al grano sbagliato non perde niente e
  diventa scomodo (le 4,77 M di posizioni dentro una cella sono un pacchetto da
  spacchettare; al loro grano sono righe che si filtrano e si uniscono), e ciò
  che è scomodo non viene usato. Ogni tabella di
  `data/stagione_2025_2026/` dichiara la propria nel manifesto.
  *(Fasi 159, 159-ter)*
- **`match_uid`** — la chiave unica di una partita nel database 2025-26:
  `competizione | data ISO | casa normalizzata | trasferta normalizzata`. È una
  **stringa costruita**, e da qui la trappola: non è mai nulla, quindi
  `notna()` su di essa dà sempre 100% e non misura niente. L'aggancio si misura
  per **appartenenza** all'insieme delle chiavi di `partite.csv.gz` — la
  differenza fra le due formulazioni valeva 27.841 puntatori pendenti.
  *(Fasi 159, 159-quater)*
- **porta d'ingresso** — `partite.csv.gz`: la tabella al grano di partita da cui
  si entra nella cartella della stagione e a cui tutte le altre si uniscono.
  Dev'essere **l'universo** delle partite, non il sottoinsieme comodo: quattro
  spareggi di Ligue 1 esistevano in una sola raccolta, e senza una riga lì le
  loro 303 righe di statistiche restavano appese a una chiave inesistente.
  *(Fase 159-ter)*
- **finestra di un coefficiente** — l'insieme di stagioni che un indice
  cumulativo somma. Il coefficiente UEFA pubblicato ne somma cinque e l'ultima
  è la **26/27**: per una partita del 2025-26 è futuro (R8), su 80 club su 410
  con punti già assegnati. Il file porta due finestre col nome che dice quale.
  ⚠️ Il **pavimento** del 20% (il `MAX` con la quota di federazione) è una
  proprietà *della finestra*, non del club: togliere una stagione può farlo
  mordere dove prima non mordeva. *(Fase 159-quater)*
- **segnaposto / "finto pieno"** — il buco peggiore non è il `NaN` (dichiarato, e
  quindi innocuo) ma il valore che **sembra** una misura e non lo è: un
  segnaposto della fonte, uno zero che significa «non lo so». Nessun confronto
  snapshot-contro-fonte lo vede, perché **coincide** con la fonte: si trova solo
  scendendo al dato più fine (il tiro-per-tiro sotto l'xG) o incrociando fonti
  indipendenti. Casi trovati: **1 xG segnaposto su 16.110 partite** (ora
  intercettato da `understat._e_segnaposto`) e **1.603** celle `midweek_europe` a
  zero per partite di coppa non coperte dal calendario. È la regola **R6** del
  protocollo. *(Fase 100, CLAUDE.md §5-bis)*
- **`ORR_MAX`** — il guard **bilaterale** sull'overround in `src/data/loader.py`:
  calcolato `orr = Σ 1/quota_i` su tutte le quote dello stesso mercato, il
  mercato viene scartato **in blocco** se `orr < 1.0` oppure `orr > ORR_MAX =
  1.12`. La soglia è motivata dai dati: nell'era `Avg` il massimo mai osservato
  su 12.457 righe è **1.0765**, quindi 1.12 sta 4 punti percentuali sopra e non
  può scartare una riga buona. Effetto reale: **11 righe / 22 celle** svuotate su
  16.111 partite (3 La Liga, 6 Bundesliga, 2 Ligue 1). *(Fase 100)*
- **regole sui dati sporchi (R1-R7)** — le sette regole non negoziabili nate
  dall'audit riga-per-riga: R1 il dato è il risultato del **campo**, non del
  tribunale; R2 fonte secondaria **dichiarata** e con la scala misurata; R3
  **nessuna modifica a mano**, mai (registro + script idempotente); R4
  un'anomalia si dichiara **anche quando non è un errore**; R5 la procedura per
  una riga che sembra corrotta (spiegare prima di accusare); R6 il **finto
  pieno**; R7 ogni statistica di testa vuole il suo **intervallo** e ogni «non
  c'è effetto» la sua **potenza**. *(Fase 100, CLAUDE.md §5-bis)*

- **mandato (panchina)** — un periodo continuo in cui lo *stesso* allenatore
  guida lo *stesso* club, ricavato tagliando la timeline del club dove cambia
  il nome. Due passaggi dello stesso allenatore nello stesso club sono **due**
  mandati: l'intervallo grezzo (prima e ultima partita di quel nome lì) direbbe
  che Allegri è al Milan dal 2010 al 2026. *(Fase 140,
  `src/data/allenatori.py`)*
- **interruzione (pattern A → X → A)** — un «mandato» di poche partite con lo
  stesso allenatore prima e dopo: quasi sempre un **vice in panchina** per una
  gara (squalifica, malattia, turno di coppa), non un cambio. Sono 836 su
  13.810, e contarle come mandati sovrastima i cambi in panchina del 18,7%.
  `panchine(ricuci=True)` le riassorbe senza perdere le partite. *(Fase 140)*
- **conflitto di identità** — due allenatori diversi dietro lo stesso nome. Si
  dimostra con un test di **impossibilità fisica**, senza fonti esterne:
  nessuno allena due club lo stesso giorno. Ne esistono 11 nel dataset globale,
  2 nel nostro perimetro (`michel` sono Míchel Sánchez e Míchel González).
  Si **dichiarano**, non si risolvono: servirebbe uno strato d'identità
  esterno. *(Fase 140)*
- **esperienza visibile al dataset** — le partite precedenti che la fonte
  *mostra*, che non sono la carriera: `games.csv` per le top-5 comincia il
  2012-08-10, quindi Ancelotti «esordisce» nel 2012. Il nome lungo esiste
  apposta, per non poter scrivere «esperienza globale». ⚠️ Il flag `censurata`
  vede solo la censura **temporale**; quella di **copertura** (chi ha allenato
  dove la fonte non guarda) non è rilevabile dall'interno. *(Fase 140; il
  gemello per i giocatori è `censored_left` in `careers.py`)*

## Convenzioni del progetto

- **titolare / panchina / bocciato** — lo stato di un modello nella
  [rosa](PANCHINA.md): in config ufficiale / migliorativo ma non attivato /
  scartato. *(Fase 64-65)*
- **due fronti (per-lega / generale)** — ogni modello si valuta sia ritarato
  sulla singola lega sia in versione unica cross-lega (pooled). *(Fase 65)*
- **blocco 📐** — la sezione «Il modello in dettaglio» obbligatoria in ogni fase
  del diario: la formula esatta (verificata contro il codice) e il ragionamento
  numerico su ogni costante. *(CLAUDE.md §2-bis)*
- **«PREMESSA CADUTA» / «⚠️ SUPERATA dalla Fase N»** — le due forme con cui il
  repo marca ciò che è stato smentito. Le affermazioni cadute **non si
  cancellano**: si barrano (`~~così~~`) o si incorniciano, con accanto cosa è
  vero adesso. Il valore del repo è che si vede cosa si credeva prima e perché è
  caduto (§1.4: documenta anche i risultati negativi). *(CLAUDE.md §1.4)*
