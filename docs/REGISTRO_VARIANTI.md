# Registro delle varianti — previsioni prospettiche con TUTTO ciò che abbiamo

> **Cos'è questo file.** La lista **completa** di ogni modello, leva, covariata,
> architettura e costante che il progetto abbia mai sperimentato, e lo stato
> della sua **previsione prospettica** su ognuna delle cinque leghe. È il
> registro che le sessioni successive aggiornano: una riga si sposta da ⬜ a ✅
> quando le sue previsioni sono prodotte e congelate.
>
> **Da dove nasce.** Richiesta dell'utente (11/08/2026): *«usare proprio tutti,
> ma tutti i modelli/piste che abbiamo anche solo sperimentato, usando anche
> tutto quello che abbiamo in panchina o in tribuna per vari motivi (compreso
> IC che contiene 0, proprio tutti i motivi), provando anche tutte le
> variabili/costanti che abbiamo sperimentato. […] è un punto molto delicato
> del progetto, è importante che ne rimanga una traccia ben visibile»*.
>
> **Perché ha senso.** Una casella 🪑 dice *«migliorativo ma non conclusivo»*:
> è una domanda rimasta aperta, non una risposta. Un ❌ misurato su una lega non
> è un ❌ sulle altre (principio §1.10 del `CLAUDE.md`). Il fuori campione
> pre-registrato è l'unico giudice che non si può ingannare: **fargli vedere
> tutto costa quasi niente e può ribaltare una panchina.**
>
> **Rapporto con gli altri file.** `docs/PANCHINA.md` resta la fonte canonica
> dello **stato scientifico** di un modello; questo registro traccia la
> **produzione delle previsioni**. Sono due cose diverse: una variante può
> essere ❌ in PANCHINA e ✅ qui (previsioni prodotte, in attesa di verdetto
> fuori campione). Il piano che li tiene insieme è
> [`docs/CHIUSURA_FASE_1.md`](CHIUSURA_FASE_1.md).
>
> **Stato**: APERTO · **creato** 11/08/2026 · **0 varianti congelate su ~300**.

---

## 0 · Leggere prima di eseguire

### 0.1 · Il disegno: walk-forward per giornata, non una profezia di agosto

C'è una differenza che vale tutta la validità del lavoro.

| disegno | cos'è | quanto vale |
|---|---|---|
| **(a) profezia pre-stagione** | ad agosto si prevedono tutte le 380 partite fino a maggio, senza mai aggiornare | debole per partita: a maggio staresti usando le forze di luglio. È in sostanza il simulatore di stagione |
| **(b) walk-forward per giornata** ⭐ | prima di **ogni** giornata si prevede quella giornata, con il modello addestrato su tutto ciò che si sa fino a lì | è il disegno standard del progetto, accumula potenza, ed è ciò che «prevedere prima che giochino» significa davvero |

**Si fa (b).** Il calendario serve a sapere *quali* partite prevedere e *entro
quando*, non a prevederle tutte oggi.

**(a) si produce comunque, e gratis**: basta eseguire tutto una volta con
taglio dati al 14/08 e archiviare l'esito. È l'istantanea «cosa pensavamo ad
agosto», interessante da sola e a costo zero. Va archiviata come **artefatto
separato**, mai mescolata alle previsioni walk-forward.

### 0.2 · ⭐ La scadenza si scioglie — ed è la cosa più importante di questa pagina

La preoccupazione era: *entro il 14 agosto non facciamo in tempo a preparare
tutto*. **Vero, e non serve.**

Nel disegno walk-forward, una variante dev'essere congelata solo **prima delle
partite su cui verrà giudicata**. Quindi:

> Una variante registrata prima della **giornata 5** è pre-registrata a tutti
> gli effetti, e viene scorata sulle giornate **5→38**. Ha meno partite, non
> meno validità.

L'unica cosa che deve essere pronta entro il **14 agosto** è ciò che vuoi
giudicare **dalla giornata 1**. Tutto il resto può entrare mano a mano — a
patto che il registro dica **da quale giornata è entrato**, e che quella data
sia **verificabile in git** (il commit che aggiunge la riga è la prova).

⚠️ **È l'unica disciplina non negoziabile di tutto il registro.** Una variante
aggiunta *dopo* aver visto come sono andate le partite su cui viene scorata non
è una previsione: è una descrizione. La colonna `entrata_dalla_giornata` e il
commit git sono ciò che separa le due cose.

### 0.3 · Una cosa alla volta — perché non sono 2^60

«Tutte le varianti» non può significare tutte le **combinazioni**: con ~60 leve
sarebbero 2⁶⁰. Significa **una leva alla volta a partire dalla configurazione
ufficiale** — che è il principio §1.2 del `CLAUDE.md` (*«cambia un solo fattore
per esperimento, altrimenti non sai cosa ha funzionato»*).

```
N varianti = 1 (baseline ufficiale) + N leve accese una per volta
           + un piccolo insieme di combinazioni DICHIARATE in anticipo
```

Le combinazioni ammesse sono solo quelle dove ci si aspetta **interazione** e va
misurata, e vanno elencate qui prima di essere eseguite (§7). Oggi ce n'è una
sola nota: **θ + φ35** in La Liga — perché sono correzioni potenzialmente
sostitutive e sommarle attribuirebbe due volte lo stesso guadagno.

Conto: **~60 varianti per lega, ~300 in tutto.** Tante, ma è una lista finita e
per metà è già eseguibile con un flag esistente (colonna «come»).

### 0.4 · Il perimetro dei dati — e una correzione

La regola dell'utente è giusta: *usare i dati generali che quei modelli
usavano, non quelli di dettaglio arrivati dopo*. Ma la sua formulazione
(*«credo prima usassimo solo gol, risultati e cose così»*) è **più stretta del
vero**, e applicarla alla lettera azzopperebbe il modello ufficiale.

Cosa usano davvero i modelli della Fase 1:

| modello | dati che usa |
|---|---|
| **Dixon-Coles ufficiale** | gol **+ xG** — il blend è `shots_blend=0.75`, `blend_signal="xg"` dalla Fase 4b. L'xG **è** nel modello ufficiale, non è un extra |
| **market-implied** | quote **1X2 + O/U** (chiusura; e apertura nella variante F75) |
| **simulatore di stagione** | le forze del DC + il calendario + le regole di classifica |
| **conteggi corner/cartellini** | corner e cartellini aggregati per squadra-partita |
| **Tier 3** | gol all'intervallo (16.110/16.111 partite) |
| **la coda testata e quasi tutta bocciata** | npxG, tiri in porta, valore rosa, assenze aggregate, forma, luck, PPDA, deep completions, riposo, congestione, stakes, arbitro, proxy formazioni |

**Il confine giusto non è «solo gol»: è «aggregato per squadra-partita».** Tutto
ciò che sta nella tabella sopra è dentro, anche se una parte è stata raccolta
dopo. Fuori restano i dati della Fase 2:

❌ statistiche per **giocatore** (54.303 righe) · formazioni ufficiali e
probabili · carriere · allenatore come individuo · coppe e UEFA · meteo ·
notizie e infortuni nominativi · **quote in-play**.

⚠️ E resta la regola **R8**: una previsione della giornata *g* può usare solo
dati noti **prima** del fischio di *g*. Che un dato sia «della Fase 1» non lo
rende automaticamente disponibile in tempo.

### 0.5 · La regola di promozione — decisa PRIMA, non dopo

Con ~300 flussi di previsione, **qualcosa vincerà per caso**. Va messo in conto
adesso:

1. **Il primario resta uno solo**: configurazione ufficiale contro baseline,
   log-loss 1X2, pooled. Non cambia perché il registro cresce.
2. Tutto il resto è una **famiglia secondaria pre-registrata**, con controllo
   FDR (Benjamini-Hochberg) **dentro** la famiglia.
3. **Nessuna promozione da una sola vittoria.** Una variante entra in config
   solo se vince **e replica** — su un'altra lega, o su una seconda stagione.
   È la regola §1.7 del progetto (mai concludere da una stagione sola), qui
   applicata al fuori campione.
4. **Le vittorie si riportano tutte, anche quelle non promosse**, con la loro
   posizione nella classifica FDR. Nascondere i quasi-vincenti è come nascondere
   i perdenti.

### 0.6 · Cosa serve prima di partire

| # | serve | stato |
|---|---|---|
| P1 | **Calendari completi 2026-27 delle 5 leghe** | ⏳ **li fornisce l'utente**. Verificato: `data/club_fixtures*.csv` arriva al **2526**, non c'è il 2627. Il listino Smarkets copre solo poche ore avanti. **Serve davvero** |
| P2 | quote 1X2 + O/U per partita | ✅ raccoglitore Smarkets attivo (serve solo alle varianti del motore market-implied) |
| P3 | risultati a fine partita | ⏳ da football-data stagione `2627`, a stagione in corso |
| P4 | uno *harness* unico che prenda una config e sputi le previsioni di una giornata | ⛔ **da scrivere** — è il collo di bottiglia vero, non le singole varianti |

---

## 1 · Lo schema di ogni riga

| colonna | significato |
|---|---|
| **variante** | nome univoco, che diventa il nome della colonna nel file di previsioni |
| **come** | `flag` = eseguibile oggi con un'opzione esistente · `config` = una voce in `src/config.py` · `codice` = va implementato |
| **PANCHINA (SA)** | stato scientifico attuale in Serie A, per vedere cosa stiamo ri-aprendo |
| **SA · PL · LL · BL · L1** | stato della **produzione delle previsioni** per lega |
| **da giornata** | da quale giornata la variante è pre-registrata (si compila al congelamento) |

Stati della produzione: **⬜** da fare · **🔄** in corso · **✅** congelata ·
**➖** non applicabile · **⛔** non eseguibile (manca dato o codice).

---

## 2 · Serie A — si parte da qui

È la lega con più prove fatte, quindi le costanti esistono già tutte e non
vanno ri-tarate: **è il banco di prova dell'infrastruttura**, non della
taratura.

### 2.1 · I motori di base

| variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|
| `base_dc` — Dixon-Coles + xG, config ufficiale | flag | ⚽ | ⬜ | |
| `base_mi_close` — market-implied dalla chiusura | config | ⚽ | ⬜ | |
| `base_mi_open` — market-implied dall'apertura | config | ⚽ | ⬜ | |
| `base_liscio` — market-implied **senza** correzioni | config | — (è il default delle altre 4 leghe) | ⬜ | |

### 2.2 · Iperparametri del Dixon-Coles (una griglia, un fattore alla volta)

Baseline Serie A: `half_life 365 · shrinkage 1.5 · shots_blend 0.75 ·
blend_signal xg · δ 0.23`.

| variante | come | SA | da giornata |
|---|---|---|---|
| `hl_180` · `hl_730` | flag `--half-life-days` | ⬜ ⬜ | |
| `shrink_0` · `shrink_0.75` · `shrink_3` | flag `--shrinkage` | ⬜ ⬜ ⬜ | |
| `blend_0` (solo gol) · `blend_0.5` · `blend_1.0` (solo xG) | flag `--shots-blend` | ⬜ ⬜ ⬜ | |
| `signal_sot` (tiri in porta) · `signal_npxg` | flag `--blend-signal` | ⬜ ⬜ | |
| `prior_0` (nessun prior neopromosse) · `prior_pooled` | flag `--promoted-prior` | ⬜ ⬜ | |
| `window_limitata` | flag `--train-window-days` | ⬜ | |

**13 varianti, tutte eseguibili oggi.** È il blocco da cui partire: nessun
codice nuovo, e mette alla prova l'harness.

### 2.3 · Leve sul path Dixon-Coles

| # | variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|---|
| 20 | `dc_phi35` — φ(\|λ−μ\|) famiglia-pareggio | flag `--draw-balance` | 🪑 F35 | ⬜ | |
| 24 | `dc_diag` — diagonale inflazionata, φ costante | flag `--draw-inflation` | 🪑 F12b | ⬜ | |
| 34 | `dc_rho_dyn` — ρ dinamico per-partita | flag `--dynamic-rho` | ❌ F18 | ⬜ | |
| 22 | `dc_ens_hl` — ensemble emivite 180+730 | codice | 🪑 F12a | ⬜ | |
| 26 | `dc_temp` — temperature scaling post-hoc | codice | 🪑 F6 (T≈0.94) | ⬜ | |
| 23 | `dc_recal_classe` — ricalibrazione per classe | codice | 🪑 F10 | ⬜ | |
| 21 | `dc_nudge_ggng` — nudge GG/NG di fine stagione | config | 🪑 F48 | ⬜ | |
| 42 | `dc_profilo_stag` — profilo stagionale dinamico γ/λ,μ | codice | ❌ F47/48 | ⬜ | |
| 37 | `dc_home_squadra` — vantaggio-casa per squadra | codice | ❌ F8 (r≈0.00) | ⬜ | |
| 38 | `dc_cov_pareggio` — covariate nel canale-pareggio | codice | ❌ F37 | ⬜ | |

### 2.4 · Covariate aggregate

| # | variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|---|
| 44 | `cov_squad_value` | flag `--covariates` | ❌ F4c/11/13/33 | ⬜ | |
| 44 | `cov_absence` | flag `--covariates` | ❌ | ⬜ | |
| 25 | `cov_rest_full` (congestione vera) | flag `--covariates` | 🪑 F4e-bis | ⬜ | |
| — | `cov_rest` (riposo semplice) | flag `--covariates` | ❌ | ⬜ | |
| 44 | `cov_form` | flag `--covariates` | ❌ | ⬜ | |
| 27 | `cov_midweek_europe` | codice | 🪑 F36-bis | ⬜ | |
| 36 | `cov_stakes` (+ router stakes-aware) | codice | ❌ F32/36/45 | ⬜ | |
| 44 | `cov_luck` · `cov_ppda` · `cov_deep` | codice | ❌ | ⬜ ⬜ ⬜ | |
| 43 | `cov_sot_grezzi` (tiri in porta nel blend) | flag `--blend-signal sot` | ❌ F3 | ⬜ | |

⚠️ Le covariate hanno **tre** flag già pronti su cinque (`squad_value`,
`absence`, `rest`, `rest_full`, `form`); le altre vanno scritte. Vale la nota di
efficienza del piano di chiusura: se si vuole risparmiare, si parte da **tre
bundle** (forza / recenti / contesto) e si scende alla singola covariata solo se
un bundle dà segnale.

### 2.5 · Architetture alternative (tutte ❌ in Serie A — è il punto)

| # | variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|---|
| 30 | `alt_bivariato` — Poisson bivariato λ3 | codice (esiste `bivariate_poisson.py`) | ❌ F42 | ⬜ | |
| 31 | `alt_copula` — copula di Frank | codice (esiste `copula_scores.py`) | ❌ F43/50 | ⬜ | |
| 32 | `alt_gas` — GAS / score-driven | codice | ❌ F52-sexies | ⬜ | |
| 33 | `alt_nb` · `alt_zip` · `alt_rue_salvesen` | codice | ❌ F27/51 | ⬜ ⬜ ⬜ | |
| 29 | `alt_gbm` — GBM diretto per mercato | codice | ❌ F21-23/50-quater | ⬜ | |
| 40 | `alt_ensemble` — DC + bivariato + GBM | codice | ❌ F46 | ⬜ | |
| 41 | `alt_blend_mercato` — blend lineare α modello+mercato | codice | ❌ F16 (α\*≈0) | ⬜ | |

> Queste sono esattamente le righe che il piano di chiusura archivierebbe per
> costo-opportunità. **Qui invece entrano**, perché la richiesta è vederle
> girare fuori campione. La differenza di costo è reale e va detta: sono le
> uniche che richiedono codice vero, non un flag.

### 2.6 · Motore market-implied (richiede le quote della partita)

| # | variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|---|
| 3 | `mi_router_theta` — router v3, θ=1.225 | config | ⚽ F52 | ⬜ | |
| 3 | `mi_theta_griglia` — θ ∈ {1.10, 1.18, 1.30} | config | ⚽ (argmin fine 1.18, nel rumore) | ⬜ | |
| 4 | `mi_phi35` — φ0=0.30, κ=1.5 | config | ⚽ F41/44 | ⬜ | |
| 5 | `mi_dp_lvl` — sharpen_1x2 | config | ⚽ F51/52 | ⬜ | |
| 6 | `mi_dp_tilt` — θ + solo tilt | codice | 🪑 (eguaglia dp_lvl, un parametro in meno) | ⬜ | |
| 15 | `mi_devig_shin` | codice | 🪑 F52-ter (P 97%) | ⬜ | |
| 35 | `mi_devig_power` — power-devig / denoising | codice | ❌ F38/50 | ⬜ | |
| 16 | `mi_estremizza_ou` — α ≈ 1.15-1.33 | codice | ⬜ **mai provata in SA** | ⬜ | |
| 17 | `mi_theta_calib` — θ come rimedio di calibrazione | codice | 🪑 (bias GG −0.0292 → +0.0049) | ⬜ | |
| 14 | `mi_recal_classe` — w_D, w_A sul mercato | codice | 🪑 F50-ter | ⬜ | |
| 18 | `mi_rho_libero` — inversione a 3 parametri | codice | 🪑 | ⬜ | |
| 19 | `mi_platt_book` — Platt sul prezzo del book (GG/NG) | codice | ❌ | ⬜ | |
| 13 | `mi_phi35_knee34` — φ35 + knee34 sul GG/NG | codice | 🪑 F50 | ⬜ | |
| 39 | `mi_recal_ou` — ricalibrazione O/U del mercato | codice | ❌ F51-quater | ⬜ | |
| 28 | `mi_temp_su_dp` — temperatura sopra dp_lvl, T=1.056 | codice | 🪑 F52-ter | ⬜ | |
| 51 | `mi_anticipo_movimento` — apertura→chiusura | codice | ❌ F98 (CLV negativo conclusivo) | ⬜ | |

### 2.7 · Le altre famiglie (non derivano dalla matrice dei gol)

| # | variante | come | PANCHINA (SA) | SA | da giornata |
|---|---|---|---|---|---|
| 45 | `cnt_base` — conteggio corner/cartellini | codice | ⚽ F96 | ⬜ | |
| 46 | `cnt_nb` — binomiale negativa sui conteggi | codice | ⚽/❌ | ⬜ | |
| 47 | `cnt_livello` — correzione di livello train-only | codice | ❌ F99 | ⬜ | |
| 49 | `cnt_arbitro` — arbitro come feature moltiplicativa | — | ⬜ **dato assente in SA (0/3420)** | ⛔ | |
| 48 | `t3_riscalamento` — Tier 3 da f=0.4396 | codice | ⚽ F98 | ⬜ | |
| — | `t3_due_stadi` ⭐ — 1T indipendente → 2T condizionato | codice | ⬜ **mai esistito** — il residuo localizzato della F98 | ⬜ | |
| 8 | `out_campione` — simulatore, mercato campione | codice | ⚽ F89 | ⬜ | |
| 9 | `out_posizionali` — top-4 / retrocessione | codice | ⚽ F91 | ⬜ | |
| 10 | `out_deriva` — + deriva di forza in-stagione | config | ⚽/❌/🪑 per mercato | ⬜ | |
| 50 | `proxy_formazioni` — undici attesi storici | codice | ❌ F98 | ⬜ | |

⚠️ **Gli outright non sono testabili prospetticamente** in senso stretto: una
stagione dà **una** osservazione per lega, e servirebbero 57 stagioni-lega
(Fase 98). Si producono e si archiviano — non si conclude niente al 30 giugno.

---

## 3 · Le altre quattro leghe — con un passo in più

Come dice l'utente: oltre a produrre le previsioni, **bisogna verificare che le
costanti vadano bene lì**, perché diverse sono nate in Serie A.

### 3.1 · Il passo in più, in tre domande per ogni costante

Per ogni variante che porta un numero (θ, φ0, κ, T, α, δ, emivita, shrinkage…):

1. **Da dove viene quel numero?** Fittato su questa lega, selezionato
   leave-future-out, pooled, o **copiato dalla Serie A**? La risposta va nella
   colonna `origine_costante` del file di previsioni — non nella testa di chi
   esegue.
2. **Se è copiato, si congelano DUE varianti**: `X_costante_SA` e
   `X_ritarata`. Sono la stessa formula con due numeri: separarle è l'unico
   modo per sapere se a fallire è il modello o la taratura.
3. **La ri-taratura vede solo il passato** (leave-future-out). Tarare sulla
   stagione che poi si usa per giudicare è look-ahead, e a questa scala non si
   noterebbe.

⚠️ Il precedente esiste ed è costato: fino alla Fase 92 `predict.py` applicava a
Premier e Liga le costanti della Serie A benché la mappa per-lega fosse già
misurata — **+0.0025 di log-loss 1X2 in Premier** e pareggio previsto +2.7pp.

### 3.2 · Lo stato di partenza è molto diverso per lega

| lega | celle `⬜` in PANCHINA | motore attuale | cosa aspettarsi |
|---|---|---|---|
| Serie A | **2** su 51 | tutte le correzioni attive | le costanti ci sono già |
| Premier | **23** su 51 | **liscio** — e *misurato* ottimo su ogni asse (F81) | poche ri-tarature, molte prime volte |
| La Liga | **24** su 51 | **liscio**, ma θ e φ35 sono 🪑 **positive e non adottate** | ⭐ la lega con più da guadagnare |
| Bundesliga | **26** su 51 | liscio, router negativo su 0/25 mercati | quasi tutto è prima volta |
| Ligue 1 | **25** su 51 | liscio, idem | quasi tutto è prima volta |

### 3.3 · Le tabelle per lega

Si replicano le tabelle di §2 con la colonna `origine_costante` in più. Vanno
create **a mano a mano che la lega entra**, non tutte adesso: un registro con
300 righe vuote non è una traccia, è rumore. La riga entra quando la variante
è pronta a essere congelata.

**Ordine**: Serie A → La Liga (dove ci sono le due panchine positive) →
Premier → Bundesliga → Ligue 1.

---

## 4 · Avanzamento

| blocco | varianti | ✅ | 🔄 | ⬜ |
|---|---|---|---|---|
| Serie A · motori di base | 4 | 0 | 0 | 4 |
| Serie A · iperparametri DC | 13 | 0 | 0 | 13 |
| Serie A · leve DC | 10 | 0 | 0 | 10 |
| Serie A · covariate | 11 | 0 | 0 | 11 |
| Serie A · architetture alternative | 9 | 0 | 0 | 9 |
| Serie A · motore market-implied | 16 | 0 | 0 | 16 |
| Serie A · altre famiglie | 10 | 0 | 1⛔ | 9 |
| **Serie A · totale** | **73** | **0** | — | **72 + 1⛔** |
| La Liga | da creare | — | — | — |
| Premier League | da creare | — | — | — |
| Bundesliga | da creare | — | — | — |
| Ligue 1 | da creare | — | — | — |

**Ultimo aggiornamento**: 11/08/2026 — registro creato, nessuna variante
congelata.

---

## 5 · Le combinazioni dichiarate

Solo queste, e solo dopo che le componenti sono state congelate da sole.

| combinazione | perché | stato |
|---|---|---|
| `mi_router_theta + mi_phi35` (La Liga) | correzioni potenzialmente **sostitutive**: sommarle attribuirebbe due volte lo stesso guadagno | ⬜ |

Aggiungerne una richiede di scriverla qui **prima** di eseguirla.

---

## 6 · Cosa NON entra, e perché

- **Dati della Fase 2** (§0.4): giocatori, formazioni, allenatori, coppe,
  meteo, notizie, in-play. Non perché non valgano — perché mescolarli
  renderebbe impossibile dire se un guadagno viene dal modello o dal dato
  nuovo.
- **Architetture inventate adesso.** Il registro è chiuso a ciò che il
  progetto ha già sperimentato. Un'idea nuova va in `docs/PISTE.md`, ed è
  Fase 2.
- **Il ROI.** Il progetto non simula denaro (criterio 6 della
  pre-registrazione). Si scora log-loss, Brier e calibrazione.

---

## 7 · Come si aggiorna questo file

1. Si esegue la variante e si producono le previsioni della giornata.
2. Si scrive la riga nel file di previsioni con `variante`,
   `entrata_dalla_giornata`, `origine_costante`.
3. **Si committa prima che la giornata si giochi** — il commit è la prova della
   pre-registrazione, e senza di quello la riga non vale.
4. Si porta la cella da ⬜ a ✅ qui, e si aggiorna la tabella §4.
5. A verdetto ottenuto si aggiorna **`docs/PANCHINA.md`**, che resta la fonte
   canonica dello stato scientifico. Questo file traccia la produzione; quello
   traccia la conoscenza.
