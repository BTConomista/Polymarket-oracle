# Glossario — i termini del progetto in una riga

I termini ricorrono ovunque nel [DIARIO](DIARIO.md), nel [README](../README.md) e
nella [rosa dei modelli](PANCHINA.md), ma erano definiti solo dove nascono. Qui
ognuno ha 1-2 righe e la fase che lo introduce. Ordine tematico.

## Il modello dei gol

- **Dixon-Coles (DC)** — il modello di base (Dixon & Coles, 1997): due Poisson
  per i gol di casa e ospite con tassi `λ, μ` in log-scala (attacco − difesa +
  vantaggio-casa), più una correzione sui 4 punteggi bassi e il decadimento
  temporale. Scritto da zero in `src/models/dixon_coles.py`. *(Fase 0-1)*
- **λ, μ (lambda, mu)** — i gol attesi di casa (λ) e ospite (μ). Da loro si
  costruisce la **matrice dei punteggi** `P(gol_casa=i, gol_ospite=j)`, da cui
  ogni mercato è una somma di celle (coerenza garantita). *(Fase 0)*
- **ρ (rho)** — la correzione Dixon-Coles che alza/abbassa i 4 punteggi bassi
  (0-0, 1-0, 0-1, 1-1) rispetto alla Poisson indipendente. `ρ=−0.06` è risultato
  universale sulle 3 leghe. *(Fase 1, 81)*
- **γ (gamma)** — il vantaggio-casa globale, auto-fittato dal DC (più alto in
  Liga, più basso in Serie A). *(Fase 1, 55)*
- **blend gol/xG (α)** — il tasso di una squadra è una media pesata di gol reali
  e **xG** (expected goals, gol attesi dalla qualità dei tiri): `α=0.75` gol,
  0.25 xG. L'xG è il meccanismo di mean-reversion (la "fortuna" regredisce).
  *(Fase 4b)*
- **δ (delta), prior neopromosse** — il bersaglio dello shrinkage per le squadre
  senza storico (neopromosse), sotto la media: `δ = ln(gol_lega/gol_promosse)`,
  per-lega (0.23 SA / 0.33 PL / 0.22 Liga). *(Fase 7, 55)*
- **shrinkage / emivita** — regolarizzazione (shrinkage 1.5: tira le forze verso
  la media) e memoria temporale (emivita 365g: quanto pesano le partite vecchie).
  *(Fase 2b, 4d)*
- **φ35, φ(|λ−μ|)** — il boost dei pareggi condizionato all'**equilibrio** della
  partita: `φ(λ,μ) = φ0·exp(−κ·|λ−μ|)`, alza i pareggi quando le due squadre sono
  pari-livello. Il miglior risultato sul pareggio. *(Fase 35)*

## Le distribuzioni della coda

- **double-Poisson (dp) / θ (theta)** — una Poisson "concentrata": si eleva la
  PMF a θ e si rinormalizza mantenendo la media. **θ>1 = sotto-dispersione**
  (code più leggere): i gol dati i tassi del mercato oscillano ~10% meno di una
  Poisson. È il **router v3** (θ=1.225 mercato / 1.138 DC). *(Fase 51, 52, 85)*
- **sotto-dispersione / sovra-dispersione** — la varianza dei gol è *minore*
  (sotto) o *maggiore* (sovra) della media (che per la Poisson pura sono uguali).
  Il calcio dati i tassi del mercato è **sotto-disperso**. *(Fase 51)*
- **COM-Poisson** — la dispersione "principiata" a un parametro ν (Conway-Maxwell-
  Poisson): provata sulla coda, **pareggia la dp ma non la batte**. *(Fase 85)*
- **binomiale negativa (NB)** — distribuzione sovra-dispersa: bocciata, i gol NON
  sono sovra-dispersi dati i tassi. *(Fase 27)*

## Le quote e il mercato

- **devig / devigging** — togliere il **margine** (vig) del bookmaker dalle quote
  per ottenere le probabilità implicite "pulite" (somma 1). Il **devig
  moltiplicativo** (le probabilità grezze riscalate a somma 1) è la fonte unica
  del progetto; il **devig di Shin** (assume trader informati) è migliore ma in
  panchina. *(Fase 1, 52-ter)*
- **overround / margine (vig)** — quanto la somma delle probabilità implicite
  supera 1: è il margine del book (~5% sull'1X2, ~2.7% sull'handicap asiatico).
- **market-implied** — il **motore di pricing**: inverte le quote 1X2+O/U nei
  λ,μ del mercato (`implied_lambda_mu`) e ne deriva ogni mercato dalla matrice
  DC. È il titolare quando ci sono le quote. *(Fase 24, 26)*
- **router (v3), `price_markets`** — la logica che, dai λ,μ, prezza ogni mercato
  con la forma giusta: double-Poisson (θ) sui marginali + φ35 sulla
  famiglia-pareggio. *(Fase 44, 52)*
- **dp_lvl / `sharpen_1x2`** — la lettura "affinata" della chiusura: corregge i
  livelli dei tassi impliciti + double-Poisson. Batte la chiusura devigata in
  **log-loss** 1X2 (non in ROI), proprietà della chiusura Serie A. *(Fase 51)*
- **chiusura vs apertura** — le quote **di chiusura** (poco prima del kickoff)
  sono lo stimatore più efficiente; quelle **di apertura** sono meno affilate.
  L'affinamento open→close vale ~+0.0020 sull'1X2. *(Fase 14)*
- **Pinnacle** — il bookmaker "sharp" (più efficiente, margine basso), usato come
  benchmark duro (colonne `PS*`/`PSC*`). *(Fase 61, PISTE #9)*

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
  ovunque** = il mercato di chiusura ingloba completamente il modello (non lo si
  batte in ROI). *(Fase 16)*
- **CLV (closing line value)** — quanto si guadagna/perde rispetto alla linea di
  chiusura: il metro d'oro dell'edge. Negativo per il modello. *(Fase 14)*
- **gap (col mercato)** — la differenza di log-loss tra modello e mercato di
  chiusura (1X2: +0.0165 in Serie A). Vive quasi tutto nel pareggio. *(Fase 9)*
- **ROI / value-bet** — il rendimento simulato scommettendo dove il modello vede
  "valore". **−15.7%** alla quota media: non si batte il margine. *(Fase 15)*
- **CI bootstrap / P(aiuta)** — intervallo di confidenza appaiato (per-stagione)
  su un Δ; `P(aiuta)` = probabilità che la leva migliori. Un CI che include lo
  zero = non conclusivo. *(Fase 17)*

## I mercati (listino)

- **1X2** — esito: 1 (casa), X (pari), 2 (ospite). **Doppia chance**: 1X/X2/12.
- **O/U (Over/Under)** — più/meno di N gol totali (linea standard 2.5).
- **GG/NG (BTTS)** — entrambe le squadre segnano (GG) o no (NG).
- **Tier 1/2/3** — i mercati per priorità: **Tier 1** = standard (1X2, O/U, GG/NG,
  doppie chance, total-squadra, clean sheet, scarto≥2, multigol, risultato
  esatto); **Tier 2** = handicap asiatico; **Tier 3** = HT/FT e per-tempo. *(§1.8
  del CLAUDE.md)*
- **handicap asiatico (AH)** — l'esito con un handicap a gol sulla favorita;
  prezza direttamente la **supremazia** λ−μ (ma risulta ridondante col 1X2+O/U,
  corr 0.995). *(Fase 86, PISTE #5)*
- **nudge stagionale** — la piccola correzione GG/NG di fine stagione (giornate
  35-38), opt-in, off di default. *(Fase 48)*

## Convenzioni del progetto

- **titolare / panchina / bocciato** — lo stato di un modello nella
  [rosa](PANCHINA.md): in config ufficiale / migliorativo ma non attivato /
  scartato. *(Fase 64-65)*
- **due fronti (per-lega / generale)** — ogni modello si valuta sia ritarato
  sulla singola lega sia in versione unica cross-lega (pooled). *(Fase 65)*
- **stima dichiarata** — un dato di mercato mancante ricostruito coi modelli,
  che vive solo in `data/estimates/` come probabilità con errore dichiarato, mai
  usato per simulare ROI. *(Fase 62-bis)*
- **blocco 📐** — la sezione «Il modello in dettaglio» obbligatoria in ogni fase
  del diario: la formula esatta (verificata contro il codice) e il ragionamento
  numerico su ogni costante. *(CLAUDE.md §2-bis)*
