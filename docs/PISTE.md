# Piste aperte — dati disponibili, ipotesi di miglioramento e perché

Questo file è per le **revisioni future**: ogni voce è una pista
*dato/architettura → ipotesi di modello*, con lo stato del dato (già in
snapshot / nei grezzi non estratto / da procurare / da raccogliere nel
tempo) e la fase del diario che la motiva. L'obiettivo: chi apre questo
file deve trovare non "cosa manca" ma **"cosa potrei provare dopo, con che
cosa, e perché potrebbe funzionare"**. La parte operativa (rete, strumenti,
Actions) sta nel [MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md).
**Va aggiornato quando una pista si apre, si prova o si chiude** (anche
l'esito negativo si scrive, principio §1.4). Ultimo aggiornamento:
**Fase 101-ter** (piste 16 e 19 chiuse dalla Fase 100; α\* della Fase 88 e
COM-Poisson della Fase 85 rettificati dall'audit; piste 6-bis e 6-ter aperte
dai residui delle Fasi 96-98); **29/07/2026** — pista **21** aperta (database
giocatore per giocatore, richiesta utente; **estesa lo stesso giorno** ad
arbitri e allenatori, club e nazionali, con estensione alle coppe europee;
piano dedicato [`PIANO_DATABASE_GIOCATORI.md`](PIANO_DATABASE_GIOCATORI.md)).
⚠️ La pista **20** (Opta/WhoScored/Flashscore/SofaScore, chiusa negativa il
28/07/2026) è ancora **da integrare** da `cantiere_opta_flashscore/` e non
compare ancora qui sotto: la 21 non dipende dalla 20, i numeri non collidono.

## 0 · ⚠️ DOVE CERCARE, dopo la correzione della Fase 92

La Fase 92 ha ribaltato la diagnosi che orientava le piste: il gap col mercato è
**88% discriminazione casa/ospite, 12% massa del pareggio** (Premier 94.5/5.5,
Liga 85/15). Tutte le piste qui sotto vanno riordinate con questa lente:

- **cercare informazione che distingua CHI VINCE fra due squadre**, non che
  aggiusti la massa del pareggio. Le leve-pareggio hanno un tetto di guadagno
  pari al 12% del gap, e sono già state spremute (Fasi 12b e 18, più la φ35 —
  sono numeri di **fase**, non di pista);
- il fatto che il mercato ci batta soprattutto sulla discriminazione è coerente
  con l'ipotesi «il mercato sa cose sulla singola partita che noi non sappiamo»
  (formazioni, motivazione, notizie): è la direzione già indicata come l'unica
  non esaurita, ma ora è **misurata**, non congetturata;
- ~~una diagnostica utile e mai fatta: su quali partite si concentra il deficit~~
  **FATTA (Fase 93)**, e il risultato restringe molto la caccia:
  - il deficit è **informazione, non calibrazione** (scomposizione di Murphy).
    L'unico termine **conclusivo** è la **risoluzione**: +0.00981
    [+0.00747, +0.01246] a favore del mercato. **Nessuna mappa di
    ricalibrazione può chiudere questo gap** — non provarci più, è misurato;
    > ⚠️ **RETTIFICATA dall'audit (Fase 101).** Due formulazioni della prima
    > stesura erano troppo forti e vanno lette così:
    > (a) ~~«siamo perfino meglio calibrati del mercato» (0.00083 contro
    > 0.00125)~~ → **non conclusivo**: IC95 [−0.00135, +0.00049] a cavallo
    > dello zero, e il **segno si inverte** passando a 50 e 100 fasce. Sotto
    > calibrazione perfetta il termine vale già 0.00083 al p95: **entrambi
    > sono al pavimento di rumore**. La conclusione operativa («nessuna
    > ricalibrazione chiude il gap») non cambia — anzi si rafforza;
    > (b) ~~«104% informazione, −4% calibrazione»~~ → le due quote sono
    > normalizzate su **0.0094**, cioè il **44%** del deficit di **0.0215**
    > che la frase nomina: il restante **56% resta non attribuito**
    > (residuo di discretizzazione). Non è «il deficit spiegato al 100%».
  - **sui mismatch siamo quasi alla pari** (divario di risoluzione −0.00198);
    **sulle partite equilibrate il mercato stacca** (−0.00793, quattro volte
    tanto). L'informazione che manca è quella che decide le partite in bilico;
  - la forbice **si allarga durante la stagione** (−0.00829 nelle prime 5
    giornate → −0.00991 dalla 26ª): il mercato accumula informazione più in
    fretta di noi;
  - quindi il bersaglio non è "informazione sulle partite" ma **informazione
    sulle partite EQUILIBRATE della seconda metà di stagione**. Qualunque fonte
    nuova va valutata prima di tutto lì, dove il divario è massimo.

## 0-bis · Indice di stato (chi è aperto, chi è chiuso, dove sta scritto)

Tabella di servizio, aggiunta alla Fase 101-ter: serve a non ri-aprire ciò che
è già stato chiuso, e a non perdere ciò che è rimasto aperto a metà. **Non è
una fonte di verità**: se diverge dalla voce estesa qui sotto, ha ragione la
voce.

| # | pista | stato | dove |
|---|---|---|---|
| 1 | scontri diretti (H2H), puntati sui totali/GG | 🟢 aperta, mai provata | §1 |
| 2 | covariate anche nel sotto-modello xG | 🟢 aperta, mai provata | §1 |
| 3 | denoising cross-partita dei λ,μ impliciti | 🟢 aperta, mai provata | §1 |
| 4 | motore market-implied multi-mercato fuori Serie A | ✅ chiusa **positiva** (F76) | §1 |
| 4-bis | θ del router come funzione del MARGINE | 🟠 **mezza chiusa**: la versione per-lega è **falsificata** (F100); resta la per-partita | §1 |
| 4-ter | coda a due parametri (isotonica / mistura) | ❌ chiusa **negativa** (F87) | §1 |
| 4-quater | dispersione per-squadra (θ_team) | ❌ chiusa **negativa** (F86-bis) | §1 |
| 5 | handicap asiatico | ❌ chiusa come **input** (F86) · ✅ **benchmark Tier 2** validato (F88, rettificato F101) | §2 |
| 6 | primo tempo → Tier 3 | ✅ chiusa **positiva** (F98) su **3 leghe su 5** — con residuo, → 6-bis | §2 |
| 6-bis | **modello a due stadi del 2° tempo (game-state)** | 🟢 **aperta — il residuo vivo del progetto** | §2 |
| 6-ter | **HT/FT congiunto e combinazioni** | 🟢 aperta (le combinazioni sono a costo quasi nullo) | §2 |
| 7 | corner/cartellini (statistiche partita) | ✅ aperta e **produttiva** (F96/98) su **3 leghe su 5**; arbitro ❌ chiuso | §2 |
| 7-bis | correzione di LIVELLO dei conteggi | ❌ chiusa **negativa** (F99) | §2 |
| 8 | quota massima (best-price) → ROI realistico | 🟠 parziale (F86: 1X2 2025-26 rifatto, resta negativo) | §2 |
| 9 | Pinnacle puro come benchmark singolo-book | 🟢 aperta, mai fatta | §2 |
| 10 | formazioni ufficiali | 🟠 **surrogato storico bocciato** (F98); resta la raccolta a T−1h | §3 |
| 11 | `transfers.csv` → shock di gennaio | 🟢 aperta, mai provata | §3 |
| 12 | seconda serie → prior neopromosse individualizzato | 🟢 aperta (si incrocia con la F91: δ dipende dall'orizzonte) | §3 |
| 13 | meteo pre-partita | 🟢 aperta, fonte mai cercata | §3 |
| 14 | bundle Understat Premier/Liga | ✅ chiusa **positiva** (F54-57) | §3 |
| 15 | altre linee O/U (multi-linea) | 🟢 aperta — **una fonte candidata ora c'è ed è in repo** (1xBet/footiqo, 2017-20) | §3 |
| 16 | GG/NG quotato + aperture vere | ✅ **premessa caduta** (F100); resta solo la raccolta prospettica | §4 |
| 17 | paper-trading del draw-bias | 🟢 aperta, ma **indebolita**: il ROI pari-equilibrio non è conclusivo in nessuna delle 5 leghe (F100) | §4 |
| 18 | dati in-play | 🟢 aperta — ma prima va chiusa la 6-bis, che costa nulla | §4 |
| 19 | quote O/U 2017-19, chiusura vera | ✅ chiusa (F100): **trovata e NON inserita** | §4 |
| §4-bis | mercato **campione di stagione** (+ top-4 e retrocessione) | 🔁 **ricorrente**: si riprezza ogni estate. 🟢 sotto-pista nuova: **rifarlo su 5 leghe** (24 → ~40 stagioni-lega, un run) | §4-bis |
| 21 | database giocatore/arbitri/allenatori | 🟢 **appena aperta (29/07/2026), bozza** — nessun dato ancora importato, ma la fonte per arbitri/allenatori è già verificata (`games.csv`, >99,7% di copertura anche sulle coppe UEFA), vedi [`PIANO_DATABASE_GIOCATORI.md`](PIANO_DATABASE_GIOCATORI.md) | §3 |

**Conteggio** (con questa tassonomia): **13 piste aperte piene** (1, 2, 3,
6-bis, 6-ter, 9, 11, 12, 13, 15, 17, 18, 21), **5 parziali o con residuo** (4-bis,
7, 8, 10, 16), **8 chiuse** (4, 4-ter, 4-quater, 5 come input, 6, 7-bis, 14,
19), più la ricorrente §4-bis. Le due voci 6-bis/6-ter sono state aggiunte alla
Fase 101-ter scorporando residui che erano descritti dentro altre voci e quindi
non contati da nessuna parte (prima erano **15** fra aperte e parziali); la 21
è nuova del 29/07/2026 e non deriva da uno scorporo.

## 1 · Piste che non richiedono nuovi dati (feature engineering / architettura)

Le più economiche: nessuna rete, nessun import — solo codice sugli snapshot
già in repo. Da provare per prime (principio §1.3, "versione economica").

### 1. Scontri diretti (head-to-head) tra le due squadre
**Dato**: già nello snapshot — è una query sullo storico delle partite tra
le stesse due squadre (ultimi 5-10 precedenti), zero dati nuovi.
**Ipotesi**: nessuna fase del diario la menziona **come feature** (verificato
alla Fase 68: zero occorrenze di "scontri diretti"/"head-to-head"/"H2H"; ri-
verificato alla Fase 101-ter: le occorrenze comparse dopo sono **tutte** le
regole di **spareggio** in classifica di `season_sim.py` — `TIEBREAK_RULES`,
Fasi 89/100 — che sono un *dato di regolamento*, non una covariata. La pista
resta intatta) — un vuoto sorprendente. È concettualmente diverso dalla "forma"
già bocciata
(Fase 13: punti/gara recenti, ridondante col fit pesato nel tempo): cattura
un **match-up specifico** (es. una squadra soffre sistematicamente un certo
avversario/stile), non il momento di forma generale. Non è coperto dalle
bocciature esistenti.
**Rischio onesto**: piccoli campioni per coppia (poche stagioni comuni,
specie cross-serie A/B per neopromosse), possibile overfitting; da testare
con shrinkage forte verso zero, come ogni covariata debole (Fase 13/33).
**Angolo più promettente (non 1X2)**: puntarla sui **TOTALI/GG**, non
sull'1X2. Sull'1X2 sarà quasi certamente ridondante (catturato dalla forza,
come la forma). Ma coppie che producono sistematicamente più/meno gol totali
o GG di quanto predicono i λ,μ marginali sarebbero un **accoppiamento
specifico della coppia** che il modello marginale (e il market-implied)
ignora per costruzione — ed è proprio il mercato dove il DC è debole
(correlazione/GG, Fase 5). Distinto dalla correlazione **globale** già
bocciata (bivariato λ3 Fase 42, copula Fase 43): qui è **per-coppia**.

### 2. Covariate anche nel sotto-modello xG, non solo nei gol
**Dato**: nessuno nuovo — è un cambio di architettura.
**Ipotesi**: l'audit Fase 34 nota di passaggio che "le covariate entrano
SOLO nel sotto-modello dei gol, non in quello del segnale (xG): con
α=0.75 il loro effetto sul tasso *blendato* è diluito" — mai seguita.
Potrebbe far riemergere covariate borderline già in panchina (`rest_full`,
`midweek_europe`, Δ≈−0.0004, PANCHINA.md #9/#12) che erano deboli forse
*per la diluizione*, non perché nulle.

### 3. Denoising cross-partita dei λ,μ impliciti (market-implied)
**Dato**: nessuno nuovo — architettura del motore.
**Ipotesi**: Fase 34: "il market-implied inverte ogni partita in modo
indipendente: nessun denoising cross-partita (es. shrinkage stagionale dei
λ,μ impliciti per squadra), mai tentato". Diverso dal denoising
cross-*stagione* già chiuso (Fase 38, bias sistematici): qui si
aggregano/shrinkano i tassi impliciti della stessa squadra su partite
ravvicinate per ridurre il rumore della singola inversione. Candidato sui
mercati "ricchi" (risultato esatto, multigol) dove la Fase 26 mostra i
guadagni maggiori — senza toccare la φ35 già ottimizzata.

### 4. Motore market-implied multi-mercato su Premier/Liga
**Dato**: già negli snapshot (quote 1X2+O/U Premier/Liga esistono).
**Ipotesi**: PANCHINA.md nota ✱1 lo segnala esplicitamente come **primo
candidato del fronte per-lega**: "la struttura è la stessa, le costanti
(ρ, θ, φ) vanno riviste per lega" — mai backtestato multi-mercato fuori
Serie A (solo il tracer 1X2 della Fase 53). È il motore **più forte** del
progetto (batte 13/14 mercati in Serie A, Fase 26): portarlo altrove è
lavoro di ri-taratura, non di raccolta dati.
**CHIUSA, positiva (Fase 76).** Sul 2017-19 dall'apertura (Fase 75) 17/20
mercati; e ora sul **2019-26 dalla CHIUSURA** (Fase 76) il motore batte il
DC-da-gol su **13/14 mercati su tutte e 3 le leghe** (Serie A/Premier/Liga),
identico alla Serie A della Fase 26, **senza ritarare ρ**. La struttura è
universale (solo gli input sono per-lega). Unica eccezione trans-lega: il
pari/dispari (quasi-casuale). Il θ del router NON si trasferisce (per-contesto,
lega × epoca). Resta da testare per-lega solo la **φ35** sulla famiglia-pareggio
(PANCHINA ✱2).

### 4-bis. θ del router come FUNZIONE del margine, non costante per-lega
**Dato**: nessuno nuovo — l'overround (margine) di ogni partita si calcola
dalle quote 1X2 e O/U 2.5 già in snapshot.
**Ipotesi (unifica due fasi)**: oggi θ (double-Poisson) è una **costante
per-contesto** scelta a griglia (Fase 81; con 5 leghe: «latine» Serie A/Liga
≈1.24, Premier/Bundesliga/Ligue 1 ≈1.08-1.10, Fase 100).
Due fasi ne spiegano la variazione con la stessa causa mai operazionalizzata:
la **Fase 53** ("θ decresce con la liquidità della lega") e la **Fase 75**
("θ cresce nel tempo: linee sempre più informative"). Ma liquidità-di-lega ed
epoca hanno un **osservabile comune per-partita: il margine** delle quote di
quella partita. Ipotesi: θ è funzione monotòna decrescente del margine (linee
più affilate → residuo-gol più sotto-disperso → θ più alto). Se regge, le
costanti per-lega × epoca **collassano in UNA curva universale θ(margine)** che
si adatta anche *dentro* la lega (big-match a basso margine vs partita minore) —
la "versione generale" che il principio §1.9 predilige.
**Test economico**: `_run_theta_margin.py` — bina le partite per margine
(quintili), fitta θ via MLE sui punteggi realizzati (`fit_theta`, Fase 51) per
bin, pooled sulle leghe (3 all'apertura della pista, **5** oggi); verifica se θ(bin) è monotòno e se una curva
θ(margine) batte out-of-sample le costanti per-lega dentro `price_markets`
(selettore lfo, su risultato esatto + 1X2 + GG). Disciplina multiple-testing
(Fase 17): la finestra è iper-testata.
**Rischio onesto**: se piatto, il margine non è il driver (Fase 53/75 restano
fenomenologiche) — negativo comunque prezioso. È anche il modo giusto di
**ri-verificare la monotonìa temporale della Fase 75**, che oggi poggia
sull'estremo iniziale di **2 sole stagioni** (1718/1819): sostituisce "epoca"
(2 punti) con "margine" (continuo, tutte le partite). Costo BASSO, un run.
**🟠 MEZZA CHIUSA (Fase 100): la versione PER-LEGA è falsificata, la
per-partita no.** L'audit a 5 leghe ha testato esattamente questa ipotesi al
livello di lega (`scripts/nuovo_fronte_generale.py`, funzioni
`covariata_margine` / `f_regressione`): **«θ decresce con la liquidità del
mercato» è FALSA come covariata** — la correlazione di rango fra margine
mediano del book e θ MLE è **+0.10** (attesa negativa), e un pooled a due
famiglie predetto dal margine **non batte mai** il pooled semplice. Le due
famiglie di θ esistono (latine ≈1.24 · Premier/Bundesliga/Ligue 1 ≈1.08-1.10)
ma **non sono predicibili dal margine**: la Ligue 1 ha il margine più alto del
campione (5.02%) e θ **basso** (1.103), la Bundesliga ha margine da Serie A
(4.76% vs 4.87%) e θ da Premier. Fonte: `docs/audit_5_leghe/10_modelli_nuove_leghe.md`
§10 e `docs/PLAYBOOK_NUOVA_LEGA.md`.
**Cosa resta davvero aperto**: la versione **per-partita** — binare le partite
per margine *dentro* la lega (quintili) e vedere se θ varia lì. Il test fatto
usa **5 punti** (una covariata per lega): non falsifica la versione continua,
la rende solo meno probabile. Priorità **bassa**: l'ipotesi che la motivava
(la liquidità) è caduta, quindi la per-partita è ormai una pesca senza
meccanismo. Se si fa, va fatta con la disciplina multiple-testing della Fase 17.

### 4-ter. Coda a DUE parametri: la "tensione di profondità" dei totali (Fase 85)
**Dato**: nessuno nuovo — forma della distribuzione dei gol, sugli stessi λ,μ
del mercato (cache `outputs/implied_lammu_cache.csv`).
**Ipotesi**: la Fase 85 ha mostrato che la coda dei gol è **sotto-dispersa** (la
Poisson sovra-stima i totali alti) e che la double-Poisson θ la corregge. MA
**un solo parametro di dispersione non calibra ogni profondità della coda**:
Over 3.5 vuole θ≈1.35, Over 4.5 θ≈1.10.
> ⚠️ **RETTIFICA (Fase 101), due punti.**
> 1. La «COM-Poisson» provata qui **è la dp stessa** riparametrizzata (`_dp_pmf`
>    dà `q_k ∝ a^k/(k!)^θ`, cioè la COM-Poisson con ν=θ, entrambe mean-matched:
>    coincidono a **≤5e-06** sull'exact-score log-loss e **≤2e-05** sulle code, a
>    ogni θ della griglia). Non è mai stata la prova che una forma a un parametro
>    non basta — era la dp confrontata con sé stessa a un θ diverso, e **non è
>    una conferma indipendente** di nulla.
> 2. ~~«l'exact-score log-loss ha il minimo ESATTAMENTE a θ=1.225»~~ è un
>    artefatto della griglia grossolana `{1, 1.1, 1.225, 1.35, 1.5}`: su griglia
>    **fine** l'argmin è **θ=1.18** (Δ **−0.00027**, IC95 [−0.00083, +0.00027] —
>    **nel rumore**). Cade quindi anche la qualifica di «conferma indipendente»
>    della costante del router: il θ=1.225 di produzione resta giustificato dalla
>    **Fase 52 sui mercati**, non da questo minimo.

La prova vera che un parametro non basta resta l'incoerenza fra le profondità
(θ≈1.35 per l'Over 3.5, θ≈1.10 per l'Over 4.5). Serve un **secondo parametro di
forma della coda**. Due vie
economiche: (a) **ricalibrazione isotonica per-soglia dei mercati-totale**
(Over 1.5/2.5/3.5/4.5) fittata walk-forward — corregge ogni profondità
separatamente, validata su calibrazione (ECE) non log-loss; (b) **mistura di due
Poisson** per il regime "partita da tanti gol" (peso π su un λ più alto) — un
parametro in più che allarga la coda dove serve senza spostare il centro.
**Test economico**: la cache rende gli esperimenti istantanei; riusa
`scripts/_run_tail_analysis.py`. Valore atteso: piccolo sul log-loss aggregato
(la dp è già al tetto) ma reale sui **mercati di coda specifici** (Over 4.5,
risultato esatto ad alto punteggio, multigol 4+) che il book quota male —
proprio gli esiti meno probabili. Onestà: è calibrazione, non informazione
(α\*=0 vale anche in coda).
**Perché era rimasta aperta**: la Fase 51/52 hanno adottato UN θ (sul
centro/listino); la Fase 85 ha misurato la coda direttamente ma non aveva ancora
provato la correzione a due parametri. La via a due parametri era l'unica non
ancora provata quando questa pista fu aperta (la «COM-Poisson» non contava: era
la dp — vedi la rettifica sopra).
**CHIUSA (Fase 87): entrambe le vie riprodotte, nessuna adottabile.** (a)
l'**isotonica per-soglia** (PAVA walk-forward) **peggiora il log-loss OOS su tutte
e 4 le soglie** (Over 1.5 +0.0150 … Over 4.5 +0.0109): il router è già calibrato
sui totali, ricalibrare aggiunge solo rumore. (b) la **mistura di due Poisson**
ha un guadagno **in-sample** (s≈0.15, −0.0006) ma **OOS non conclusivo** (Δ
−0.00042, CI95 [−0.0015,+0.0006], P 78.6%) e con **segno ribaltato sulle stagioni
recenti** (2024-25 +0.0014, 2025-26 +0.0013: aiutava l'era porte-chiuse, danneggia
il calcio di oggi). `scripts/_run_tail_two_param.py`. **Seconda** conferma
indipendente — dopo θ_team (F86-bis); la F85 non conta, era la dp
riparametrizzata (F101) — che **la coda dei gol è al tetto della
forma**: il singolo θ del router è quanto di meglio senza informazione nuova.

### 4-quater. Dispersione per-squadra: un θ_team per gli esiti rari (LEAD, Fase 86)
**Dato**: nessuno nuovo — sugli stessi λ,μ del mercato + i risultati storici.
**Ipotesi (corregge un audit)**: la Fase 86 ha trovato — riproducendo a mano un
finding che un revisore aveva dichiarato negativo — che la **volatilità-sorpresa**
di una squadra (std del residuo `diff-reti − (λ−μ)` di mercato) **persiste**
stagione→stagione (corr +0.25 grezza, **+0.20 controllata per la forza**, fuori
dalla banda nulla). E la direzione è sfruttabile: classificando le partite per
volatilità-sorpresa **passata** (OOS), le squadre ad **alta** volatilità sono
predette meglio da **θ=1.10** (coda più pesante) vs θ=1.225 dei gruppi basso/medio,
sul risultato esatto. È la prima crepa nel "θ uniforme" (F52-quater aveva escluso
θ per volume/equilibrio/coda, **mai per identità-squadra**), ed è esattamente sul
tema degli **esiti meno probabili**: gli upset delle squadre volatili si prevedono
meglio con una coda più pesante.
**Test pieno ESEGUITO → CHIUSA, negativa (Fase 86-bis).** Il walk-forward è stato
fatto: per ogni stagione test si fitta il θ ottimo per terzile di volatilità-
sorpresa **passata** sui dati precedenti e lo si applica al futuro. Su **5.690
partite OOS** il θ_team **peggiora** il risultato esatto: exact-LL 2.8222 vs
2.8212 del θ globale (**Δ +0.00096**). I θ di gruppo fittati sono **instabili**
anno-su-anno (l'alto va 1.0→1.1), quindi non trasferiscono. La persistenza (+0.20)
è reale ma **troppo rumorosa per essere monetizzata da un θ per-squadra**. È
l'ennesima conferma del tetto informativo (α\*=0), ora *nella coda e per-squadra*:
nessuna sotto-struttura del θ (volume/equilibrio/coda F52-quater; per-squadra
F86-bis) batte il θ globale OOS. `scripts/_run_team_dispersion.py` (sez.
walk-forward). Lead 🔎 → ❌.

## 2 · Piste nei dati grezzi già scaricati, mai estratte

Nessuna rete: le colonne sono nei CSV football-data congelati in
`data/football_data_raw/`, serve solo estenderne l'estrazione in
`loader.py`.

### 5. Handicap asiatico → terzo vincolo per l'inversione market-implied
**Dato**: colonne AH (linea + prezzi, apertura E chiusura), **7/9
stagioni** (2019-20+).
**Ipotesi**: la Fase 27 chiuse la taratura della forma dicendo
esplicitamente che "per spingere oltre servirebbero PIÙ input di mercato
(altre linee O/U, handicap)"; ripreso in Fase 44. L'handicap è un vincolo
su **λ−μ** (asimmetria) che 1X2+O/U (livello+somma) non fissa bene: terzo
vincolo → inversione più precisa → migliora il motore attivo su tutto il
listino. Tier 2 dichiarato (principio §1.8). **L'unica pista di questa
sezione che può migliorare direttamente il titolare**: priorità massima
tra le "grezzo non estratto".
**Come input di inversione: CHIUSA (negativa, Fase 86).** Il diagnostico
economico è stato eseguito: la supremazia implicita nella linea AH di chiusura
correla **0.9952** con λ−μ già ricavata da 1X2+O/U (2.660 partite Serie A;
`AH ≈ 0.94·(λ−μ)`). L'AH è **la stessa supremazia ripackagata** → un'inversione
a 3 vincoli **non aggiungerebbe informazione**. Coerente coi fatti-chiusi (α\*=0).
**Come benchmark Tier 2: APERTO e VALIDATO (Fase 88).** Usato non come input ma
come **prezzo esterno sharp** contro cui misurare la calibrazione del router sulla
copertura del margine: su **7.437 partite × 3 leghe** il Brier del router è
**indistinguibile** da quello del mercato AH (0.2040 vs 0.2041, corr modello-
mercato 0.91) — dai soli λ,μ del 1X2+O/U il motore eguaglia il mercato che quota
l'AH. `scripts/_run_ah_benchmark.py`. È **l'unico mercato del listino validato
contro una quota esterna e indipendente** (nel listino walk-forward della Fase 98
lo stesso confronto dà Brier **0.2044 vs 0.2044**, setup diverso).
> ⚠️ **SUPERATA dalla Fase 101** la formula con cui il risultato era stato
> raccontato. ~~«È α\*=0 su un mercato nuovo (il margine)»~~: **l'encompassing
> non era mai stato calcolato**. Calcolato (ora dentro `_run_ah_benchmark.py`,
> Fase 101-ter) sugli stessi 7.437 casi dà **α\* = +1.082** [+0.143, +2.026] —
> IC che **esclude lo zero**, cioè l'opposto di α\*=0. Il motivo è strutturale e
> va dichiarato: il router **non è un previsore indipendente** dal mercato AH,
> è una *traduzione* delle stesse quote 1X2+O/U, quindi il test di encompassing
> qui non ha il significato che ha nella Fase 16.
> **La conclusione onesta, e resta interessante, è il PAREGGIO in Brier col
> mercato sharp**: ΔBrier (modello−mercato) **−0.000136** [−0.000362, +0.000083];
> col protocollo walk-forward della Fase 16 il blend **non batte** il mercato
> fuori campione (n=**6.297**, Δ **−0.000064** [−0.000271, +0.000139]). Nota di
> fragilità emersa rifacendo il conto: **il protocollo di stima di α cambia il
> SEGNO** del Δ (pooled −0.000064 vs per-lega +0.000011, entrambi nel rumore);
> lo script stampa ora entrambe le varianti.

Resta da fare (facoltativo): estrarre l'AH nel loader per esporlo nel tool e
prezzare handicap/scarto anche dove servono operativamente.

### 6. Primo tempo (HTHG/HTAG/HTR) → mercati Tier 3 e fondazione live
**Dato**: **9/9 stagioni**.
**Ipotesi**: mercati HT/FT e per-tempo (Tier 3, principio §1.8) con lo
stesso motore market-implied riscalato sul tempo; propedeutico alla pista
18 (in-play).
**ESITO (Fase 98) — APERTA E PRODUTTIVA, con un residuo localizzato.** La
fondazione è **misurata, non assunta**: frazione di gol nel primo tempo
**f = 0.4396** [0.4338, 0.4458] (SA 0.4365 / PL 0.4464 / LL 0.4356), primo tempo
Poisson-compatibile (dispersione 0.9857) e tempi quasi indipendenti (+0.0485) →
il ri-scalamento `λ_1T = f·λ` è **lecito**. Tre mercati nuovi battono la
baseline con IC conclusivo su 6.840 partite: Halftime **+0.0537**
[+0.0461,+0.0612], Second Half **+0.0578**, risultato esatto **+0.1940**.
**Il residuo è la pista viva**: il **secondo tempo è mal calibrato**
(pareggio 0.3671 dichiarato vs 0.3427 reale) mentre il primo passa per *lo
stesso codice* ed è calibrato a <0.006 → non è normalizzazione, è **game-state**
(il punteggio all'intervallo cambia il modo di giocare). Prossimo passo: modello
a **due stadi** (1T indipendente → 2T condizionato al punteggio dell'intervallo).
Costo BASSO, e ha il pregio di essere il primo residuo *localizzato e
non-artefatto* trovato da parecchie fasi. → **la pista scorporata è la 6-bis**.

### 6-bis. Modello a DUE STADI del secondo tempo (game-state) — 🟢 il residuo vivo
**Dato**: **nessuno nuovo da procurare**, ma attenzione a dove sta: HTHG/HTAG/HTR
**non sono negli snapshot** (`data/*_matches.csv` non ha colonne di primo tempo)
— stanno nei grezzi, ed è da lì che la Fase 98 li legge: Serie A da
`data/football_data_raw/`, Premier e Liga dai bundle in `files/`. Per
Bundesliga e Ligue 1 vanno scaricati (rete aperta, vedi §6) oppure presi, per il
solo 2017-19, dai file già in repo `data/ricerca_esterna/footiqo_gol_*.json`
(`htHomeTeamGoals`/`stHomeTeamGoals`, **3.652 righe su 5 leghe** — verificato
contando i file).
**Perché esiste questa pista** (scorporata dalla 6 alla Fase 101-ter: era
descritta in coda alla 6 e alla 18, quindi non contata da nessuna parte). Il
residuo della Fase 98 è **localizzato e non-artefatto**: il **secondo tempo è
mal calibrato** (pareggio dichiarato **0.3671** contro **0.3427** reale) mentre
il **primo tempo passa per lo stesso identico codice** ed è calibrato a
**<0.006**. Se fosse un problema di normalizzazione o di forma, sbaglierebbero
entrambi. Quindi è **game-state**: il punteggio all'intervallo cambia il modo di
giocare (chi è sotto attacca, chi è sopra si chiude), e un modello che tratta i
due tempi come indipendenti non può vederlo.

**📐 Il modello in dettaglio — cosa fa oggi e cosa cambierebbe.**
Oggi (Fase 98, `scripts/_run_polymarket_tier3.py:481-485` e `403-410`):

```
f      = (Σ gol 1T) / (Σ gol finali)          # misurata, non assunta
M_1T   = score_matrix(f·λ,      f·μ,      ρ=−0.06, dp_theta=θ)
M_2T   = score_matrix((1−f)·λ,  (1−f)·μ,  ρ=−0.06, dp_theta=θ)
P(1/X/2 del tempo) = (tril(M), trace(M), triu(M))
```

I due tempi sono **marginali indipendenti**: `M_2T` non dipende da come è finito
il primo. Il modello a due stadi sostituisce la seconda riga con una
**condizionata** al punteggio dell'intervallo `(h,a)`:

```
λ_2T = (1−f)·λ · g_home(h−a)      μ_2T = (1−f)·μ · g_away(h−a)
```

con `g_home, g_away` funzioni del **vantaggio all'intervallo** (una sola
variabile di stato, per non fittare aria: 5 livelli, |h−a| ≥ 2 accorpati), da
stimare **train-only** e validare walk-forward.

**Perché i numeri sono ragionevoli.** `f = 0.4396` [0.4338, 0.4458]
(SA 0.4365 / PL 0.4464 / LL 0.4356) e il primo tempo è **Poisson-compatibile**
(dispersione 0.9857), i tempi **quasi indipendenti** (+0.0485) — cioè
l'assunzione che il modello a due stadi rompe è *quasi* vera in media, ma
sbaglia **condizionatamente** allo stato: è esattamente il profilo di un
effetto di game-state, non di forma.
**Rischio onesto**: la mis-calibrazione da spiegare vale ~2,4 punti percentuali
sul pareggio del 2T; con 5 livelli di stato e 6.840 partite il rischio di
fittare rumore è reale. Va misurato per-mercato (§1.8) e con il **controllo di
solo livello** (regola di metodo della Fase 98): una costante moltiplicativa sul
2T, senza stato, è il benchmark da battere — se il guadagno è tutto lì, non è
game-state.
**Costo BASSO** (nessuna rete, nessun fit nuovo del DC) e **valore doppio**: è
il primo mattone dell'in-play (pista 18) e la condizione preliminare dell'HT/FT
congiunto (pista 6-ter). **È il residuo aperto più concreto del progetto.**

### 6-ter. HT/FT congiunto e mercati COMBINAZIONE
**Dato**: nessuno nuovo (HT/FT: gli stessi HTHG/HTAG della 6; combinazioni:
niente affatto, si leggono dalla matrice che già calcoliamo).
**Perché esiste questa pista** (aperta alla Fase 101-ter): sono i mercati che
`CLAUDE.md` §1.8 elenca come **ancora scoperti** dopo le Fasi 96/98 — «restano
scoperti: HT/FT congiunto, le combinazioni, e il live (Tier 3+)» — ma che non
avevano una voce qui. Sono due lavori di costo molto diverso:
- **combinazioni** (es. «1 & Over 2.5», «X & Under 2.5», «GG & Over 2.5»):
  **costo quasi nullo**. Sono somme di celle della **stessa** matrice dei
  punteggi che `derive_markets` (`src/models/market_implied.py:130`) già
  costruisce — `M[(i>j) & (i+j>=3)].sum()` e simili. Nessuna matematica nuova,
  nessun dato nuovo: è un'estensione del dizionario dei mercati più il suo
  backtest walk-forward nel listino (`_run_listino_validazione.py`). Caveat da
  dichiarare: il routing per-mercato della Fase 44 usa **due matrici diverse**
  (τ pura per i totali, φ35 per esiti/pareggio) — una combinazione esito×totale
  sta a cavallo delle due famiglie, quindi va deciso *esplicitamente* da quale
  matrice si prende, e la scelta va misurata, non assunta;
- **HT/FT congiunto** (1/1, 1/X, … 2/2): **richiede prima la 6-bis**. Il
  congiunto è per definizione P(risultato 1T, risultato finale), e con i due
  tempi indipendenti si otterrebbe moltiplicando le due marginali — cioè
  esattamente l'assunzione che la Fase 98 ha già mostrato **rotta** sul secondo
  tempo. Prezzare l'HT/FT prima di aver chiuso il game-state significherebbe
  propagare quella mis-calibrazione su nove esiti invece che su tre.
**Aspettativa onesta**: nessuna delle due porta **informazione** nuova (il tetto
informativo, α\*≈0, vale anche qui). Portano **copertura di listino**: sono
mercati che il book quota e noi no. Il valore è lo stesso dei ~17 mercati
non quotati della Fase 82 — prezzare *calibrato* dove il book non arriva.

### 7. Statistiche partita (corner, tiri totali, falli, cartellini)
**Dato**: 9/9 stagioni, all'apertura della pista mai estratte (solo i tiri in
porta furono testati e bocciati, Fase 2/3 — quelli sono un segnale diverso e già
chiuso). Oggi corner e cartellini sono letti dai grezzi da
`scripts/_run_outside_matrix.py::load_raw` — **ma solo per 3 leghe**: Serie A da
`data/football_data_raw/` (che contiene solo i CSV Serie A) e Premier/Liga dai
bundle utente in `files/`. **Non stanno negli snapshot** (`data/*_matches.csv`
non ha colonne corner/cartellini/primo-tempo).
**Ipotesi**: i corner come proxy di pressione offensiva mai testato; i
mercati corner/cartellini sono un listino a sé che il motore non copre.
Aspettativa onesta: bassa sul migliorare 1X2/O/U (tetto informativo, Fasi
20-22), più sensata come **nuovi mercati** da prezzare.
**ESITO (Fasi 96/98) — APERTA, ed è la famiglia più promettente rimasta.** Il
processo dei conteggi è **diverso** da quello dei gol (non ridondante) e i
mercati corner/cartellini sono prezzabili walk-forward. La forma **binomiale
negativa** (Fase 98) è la giusta — i conteggi sono SOVRA-dispersi, l'opposto dei
gol (Fase 27) — ma il guadagno è **conclusivo e trascurabile** (corner +0.00103,
cartellini +0.00088). **La leva vera scoperta qui è un'altra**: la **deriva di
livello** (vedi pista 7-bis) — che la **Fase 99 ha però misurato e bocciato**.
**Chiuso**: l'**arbitro** come feature moltiplicativa (Fase 98) — il dato
`Referee` esiste solo in Premier (3420/3420, 0/3420 in SA e Liga) e nessun IC
esclude lo zero; l'85% del guadagno apparente era **solo livello**. Il segnale
esiste ma è sovra-esteso ~2.5× (`b = 0.401` [+0.096,+0.706]) e vale il 3.7%
della varianza: non ripescabile senza una modellazione dell'evoluzione temporale
del tasso di un arbitro.
**🟢 Sotto-pista aperta (Fase 101-ter): estendere i conteggi a 5 leghe.** Nella
matrice della PANCHINA le celle Bundesliga e Ligue 1 del «modello di conteggio»
e della «binomiale negativa» sono ⬜ (`docs/PANCHINA.md` righe 118-119): la
famiglia è misurata su 3 leghe su 5. Non è un limite di modello ma di **dato
grezzo**: `data/football_data_raw/` contiene solo la Serie A e non esistono
bundle per le due leghe nuove. Ma **la rete non è più bloccata** (Fase 100:
football-data.co.uk risponde 200), quindi i CSV `D1`/`F1` con `HC/AC/HY/AY` si
scaricano e il resto è già scritto. Costo BASSO, e serve a dire se il processo
dei conteggi è universale o per-lega (principio §1.9) — oggi non lo sappiamo.
Stessa osservazione vale per la pista 6 (Tier 3: `docs/PANCHINA.md` riga 121, ⬜
su entrambe le leghe nuove) e, con essa, per la 6-bis.

### 7-bis. Correzione di LIVELLO dei conteggi — ❌ **CHIUSA NEGATIVA (Fase 99)**
**Dato**: nessun dato nuovo — è una costante train-only sopra il modello di
conteggio della Fase 96.
**Perché**: tre fronti della Fase 98 che non si parlavano hanno misurato lo
stesso difetto — bias di media walk-forward **Premier cartellini −0.201**,
**Serie A corner +0.352**, **listino corner +0.117** su tutte e quattro le
soglie. L'**emivita 365g non insegue la deriva temporale dei conteggi** (i
cartellini crescono, i corner calano), e il bias residuo è ciò che *causa* i
3 peggioramenti conclusivi della NB e le 3 uniche linee non conclusive del
listino.
**Valore atteso (Fase 98)**: sui cartellini Premier la sola costante di livello
valeva **−0.00308** contro i **−0.00041** dell'arbitro al netto del livello —
cioè **7,5×**, non 5× — e un ordine di grandezza più del passaggio Poisson→NB.
Era indicata come il miglior rapporto valore/costo aperto.
*(⚠️ rettifica aritmetica dell'audit, Fase 101, `PISTE-5x-arbitro`: 0.00308 /
0.00041 = **7,5**. Il «5×» che girava nei documenti confronta il livello con un
terzo numero — l'**incremento marginale** dell'arbitro SOPRA il livello,
**−0.00056** sull'Over 3.5 — e vale 5,5. I tre numeri escono dal blocco
CONTROLLO di `scripts/_run_referee_feature.py`: «BASE × c_fold (SOLO livello)
−0.00308», «BASE × f_arb/c_fold (SOLO arbitro) −0.00041», «+ARBITRO vs
SOLO-livello su O3.5 −0.00056».)*
**ESITO (Fase 99) — ❌ NEGATIVO, il lead era falso.** Implementata e misurata
(`scripts/_run_counts_level.py`, 7.050 partite OOS, 21 fold): **cinque**
stimatori walk-forward (`c_oos`, `c_last2`, `c_last`, `c_trend`) più la versione
**alla radice** (emivita scelta fold per fold sul solo passato). Nessuno
migliora; **5 celle su 8 peggiorano con IC conclusivo**; l'emivita walk-forward
è un lancio di moneta (−0.00004 corner, −0.00034 cartellini, P>0 = 0.48 e 0.33).
**Causa**: il bias di fold **non persiste** — corr(bias_t, bias_{t−1}) +0.2299
[−0.2544,+0.6715] sui corner e +0.1915 [−0.3446,+0.5830] sui cartellini,
**10/18 stesso segno**, con sd del bias per fold **2,6×** (corner) e **10×**
(cartellini) il bias pooled. Il «bias costante su tutte le linee» era costante
*fra le linee*, non *nel tempo*.
**Due lezioni che restano** (e valgono oltre questa pista):
1. un bias sulla **media** non è un bias sulle **probabilità** — i cartellini
   sovrastimano di +0.042 conteggi ma i mercati erano già calibrati
   (+0.0047/−0.0034/+0.0008) e la correzione li ha **guastati**;
2. **regola di metodo**: un bias misurato su un *pool* non autorizza una
   correzione *prospettica* — prima si misura se **persiste** (autocorrelazione
   fra fold, con CI). Stessa forma della Fase 86-bis (θ per-squadra: persiste ma
   non è sfruttabile) e del controllo-di-livello della Fase 98.
Riaprirla richiede **informazione nuova** (una covariata che spieghi *perché* una
stagione ha più cartellini: regolamento, direttive arbitrali, VAR), non un
estimatore migliore.

### 8. Quota massima (MaxC*/Max*) → ROI realistico
**Dato**: 7/9 stagioni.
**Ipotesi**: ogni ROI finora usa la quota media → sottostima quanto un
utente reale otterrebbe col best-price. Rifare le simulazioni chiave
(Fasi 14/40/51) al best-price è un test economico che può cambiare le
conclusioni operative (in meglio: il margine effettivo si riduce).
**ESITO PARZIALE (Fase 86)**: il ROI 1X2 2025-26 rifatto al best-price coerente
resta **negativo** (−2.4% a soglia .05, −9.7% a .03). Restano non rifatte le
simulazioni delle Fasi 14/40/51.

### 9. Pinnacle puro (PS*/PSC*) come benchmark singolo-book
**Dato**: 8/9 stagioni piene (2025-26 ~52%).
**Ipotesi**: il book più efficiente come bersaglio invece della media
multi-book — avversario più duro e pulito (niente rumore da book
ricreativi). Utile per ri-testare il beat-the-close (Fase 52) contro un
avversario più serio. (Betfair Exchange BFE*: solo 2/9 stagioni, futuro.)
**Test ad alto valore epistemico (mai fatto)**: ri-verificare l'**unico
edge del progetto** — `dp_lvl` batte la chiusura devigata in log-loss 1X2
(Fase 51/52, CI conclusivo) — contro **Pinnacle puro devigato con Shin**
(`metrics.devig_shin` esiste, `PSC*` in snapshot), non contro la media
multi-book + devig moltiplicativo. La Fase 51 stessa avverte che parte
dell'edge potrebbe essere il margine grezzo del devig moltiplicativo, non
sotto-dispersione vera. Due esiti, entrambi da dichiarare: `dp_lvl`
sopravvive → l'edge è più solido del dichiarato; svanisce → downgrade onesto.
La Fase 53 ha testato `dp_lvl` cross-*lega* (bocciato fuori SA) ma **mai
cross-avversario**: è la caveat auto-dichiarata e mai onorata. Costo BASSO.

## 3 · Piste che richiedono una fonte esterna nuova

### 10. Formazioni ufficiali (`game_lineups.csv`) → assenze VERE
**Dato**: l'upstream player-scores che già importiamo contiene anche
`game_lineups.csv` (~349 MB), `game_events.csv` — mai importati (il
workflow scarica solo i 4 file dei valori). A portata di una riga in più
in `WANTED`.
**Ipotesi**: sono la voce "dati davvero nuovi" della roadmap (README #27).
Le assenze della Fase 4 erano stimate da fonte terza e non aiutavano; con
le formazioni vere si calcola la **forza della formazione schierata**
(valore/minuti dei titolari effettivi vs rosa piena). Attenzione al
timing: le formazioni escono ~1h prima del fischio → utilizzabili solo
contro le quote di **chiusura**.
**ESITO (Fase 98) — il SURROGATO è bocciato, la pista vera resta aperta.** Il
proxy storico (undici attesi ricostruiti dai minuti, disponibilità del nucleo,
continuità dell'undici) è stato testato su 9.159 partite: la parte che
"funziona" **non è nuova** (correla **+0.9603** col valore rosa, già bocciato
F4c/F11; +0.898 col logit del DC) e fuori campione dà +0.00136
[−0.00086,+0.00350], 2/4 stagioni; la parte concettualmente nuova è **nulla
ovunque**, e **sul bersaglio della Fase 93** (equilibrate, seconda metà) tutti
gli IC attraversano lo zero con |r| ≤ 0.034 contro il deficit. Dettaglio di
sanità: la disponibilità correla **−0.1227** col logit della chiusura → **il
mercato le assenze le prezza già**.
**Conseguenza**: resta aperta **solo** la versione che conterebbe — la
**formazione ufficiale a T−1h, raccolta prospetticamente**. Questo esperimento
non è un argomento contro quella raccolta: è un argomento **a favore**, perché
esclude la scorciatoia storica.

### 11. `transfers.csv` → shock di gennaio
**Dato**: nello stesso upstream player-scores (pista 10).
**Ipotesi**: il mercato invernale cambia le rose infra-stagione; il nostro
`squad_value` è una foto al 1° settembre. Mai modellato. Da incrociare con
la Fase 31 (motivazione): gennaio ridistribuisce anche gli obiettivi.

### 12. Risultati di seconda serie → prior neopromosse individualizzato
**Dato**: la Fase 68 ha già scaricato le seconde serie (Serie B,
Championship, Segunda, 1617→2425 via openfootball) ma **solo per il
calendario/riposo**, non per i punteggi — che sono nello stesso file.
**Ipotesi**: oggi il prior δ (Fase 7) è un numero fisso uguale per ogni
neopromossa; la Fase 7 stessa nota il limite: "il 2023-24 peggiora perché
quel trio di promosse (Genoa/Cagliari/Frosinone) era più vicino alla
media — il prior le sotto-stima". Stimare una forza di partenza per
neopromossa dal suo rendimento reale (punti/gara, differenza reti)
nell'ultima stagione di B/Championship/Segunda userebbe un dato già in
casa, nello stesso formato dei file coppa già parsati.
**Da aggiornare a 5 leghe**: con Bundesliga e Ligue 1 servono anche 2.
Bundesliga e Ligue 2, che la Fase 68 **non** ha scaricato (δ per-lega oggi:
0.23 / 0.33 / 0.22 / **0.28** / **0.19**, `src/config.py`).
**Si incrocia con la Fase 91** (dettaglio e numeri in §4-bis, voce «il prior δ
dipende dall'ORIZZONTE di predizione»): il δ attuale è tarato sul **log-loss
della singola partita** e, propagato su 38 giornate, risulta **troppo severo**,
con la mis-calibrazione dei mercati posizionali **tutta sulle neopromosse**. Un
prior *individualizzato* per neopromossa è una risposta possibile a entrambi i
problemi — quello di partita e quello di stagione — e va valutata
**per-mercato** (§1.8), non in blocco.

### 13. Meteo pre-partita
**Dato**: da procurare (mai cercata una fonte).
**Ipotesi**: nel chiudere il capitolo "dati interni esauriti" la Fase 4c
lascia il layer covariate "riutilizzabile per dati futuri davvero
indipendenti (es. formazioni ufficiali last-minute, **meteo**,
motivazione)" — formazioni e motivazione sono state poi effettivamente
attaccate (piste 10, Fase 31); il meteo no, mai. È l'unico segnale
esplicitamente indicato come "davvero indipendente" (non ricavabile da
gol/xG storici) mai perseguito.

### 14. Bundle Understat Premier/Liga → port completo del DC
**Dato**: bundle utente in `files/` (Fase 53), xG cross-lega.
**Ipotesi**: la Fase 53-bis è dichiarata aperta nel CLAUDE.md — completare
il port del DC con blend xG su Premier/Liga e ri-validare il two-front
(principio §1.9).
**CHIUSA, positiva (Fasi 54-57)**: snapshot congelati con xG al 100%,
config per-lega in `LEAGUE_CONFIGS` (δ 0.33/0.22), DC+xG batte la baseline
su entrambe; la ri-taratura degli altri iperparametri è piatta. Lo studio
dedicato delle due leghe continua in `docs/STUDIO_PREMIER_LIGA.md`.

### 15. Altre linee O/U (multi-linea) per vincolare meglio λ,μ
**Dato**: ~~da procurare; nessuna fonte candidata nota, va cercata da zero~~ —
resta vero che **football-data.co.uk NON le fornisce** (solo la 2.5), a
differenza dell'handicap (pista 5, quello sì presente).
> ⚠️ **AGGIORNATA alla Fase 101-ter: una fonte candidata ORA ESISTE, ed è già
> in repo.** I file 1xBet raccolti dalla Fase 100 (`data/ricerca_esterna/
> footiqo_{lega}_{stagione}.json`) contengono la **scaletta O/U completa** —
> chiavi `xbetCloseOver05/15/25/35/45` e i rispettivi `Under`, più `1FT/XFT/2FT`
> e `BTTSY/BTTSN`. Verificato contando i file: **5.377 righe di quote** su
> 5 leghe × 3 stagioni (2017-18, 2018-19, 2019-20; Bundesliga 306/stagione,
> Ligue 1 2019-20 troncata a 279 dal COVID) — le stesse su cui la Fase 100
> misura il GG/NG dopo gli scarti (5.337). Collaterale utile alle piste 6/6-bis:
> gli altri file (`footiqo_gol_*.json`) danno gol di **primo e secondo tempo**
> per **tutte e 5** le leghe, **3.652 righe** sul 2017-19 (`htHomeTeamGoals`,
> `stHomeTeamGoals`, …), cioè anche per Bundesliga e Ligue 1, dove i grezzi
> football-data non sono in repo.
> **Limiti da dichiarare prima di usarli** (le stesse ragioni per cui la pista
> 19 non è stata inserita negli snapshot): è **un solo book**, copre **solo il
> 2017-20**, e non è una media multi-book. Per un test di *architettura*
> («l'inversione a 3+ vincoli è più precisa?») questo basta — non serve che sia
> il prezzo di consenso, serve che sia una scaletta **coerente** dello stesso
> book, e la monotonìa della scaletta è stata verificata dalla Fase 100. Per
> entrare in produzione, no.

**Ipotesi**: Fase 27 e Fase 44 dichiarano il bisogno due volte ("più
input di mercato — altre linee O/U, handicap — che lo snapshot non ha")
per vincolare meglio l'inversione.
**📐 Cosa cambierebbe, esattamente.** Oggi `implied_lambda_mu`
(`src/models/market_implied.py:109-127`) minimizza già ai **minimi quadrati**
```
e(λ,μ) = (qH−pH)² + (qD−pD)² + (qA−pA)² + (qO−pO)²      # qO = Over 2.5
```
su **2** incognite, con ρ **fisso** («il mercato 1X2+O/U non lo vincola», dice
il docstring) e la **forma** (Poisson, o dp con θ globale) **assunta**. Quindi
il guadagno delle linee in più NON è «passare da esatto a sovra-determinato» —
lo è già. È che le quattro linee aggiuntive vincolano una cosa che oggi nessun
input vincola: la **forma della distribuzione dei gol totali**, partita per
partita. Due usi concreti, entrambi nuovi:
1. **stimare θ per-partita dalla scaletta** invece di imporre la costante
   globale del router (θ=1.225 mercato / 1.138 DC), e verificare se il θ
   per-partita così ottenuto è quello che serve — è il modo diretto di
   rispondere alla domanda della pista 4-bis senza passare dal margine;
2. usare il **residuo** della scaletta come diagnostica: se con λ,μ,θ non si
   riesce a stare dentro tutte e 5 le linee, la forma a un parametro è
   falsificata *sul singolo prezzo di mercato*, non solo sui punteggi
   realizzati (che è ciò che la Fase 85 può fare oggi).
**Rischio onesto**: l'esito più probabile è che non cambi nulla sull'1X2 —
la pista 5 ha già mostrato che un terzo vincolo (l'handicap) era **la stessa
informazione ripackagata** (corr 0.9952 con λ−μ). La differenza è che l'O/U
multi-linea vincola la **coda**, non la supremazia: è l'unico input di mercato
che tocca la dimensione dove la Fase 85/87 hanno trovato una tensione
(θ≈1.35 sull'Over 3.5 contro θ≈1.10 sull'Over 4.5, pista 4-ter). Costo
BASSO-MEDIO: il dato c'è, serve solo il join e una `implied_lambda_mu`
multi-vincolo.

### 21. Database giocatore/arbitri/allenatori — 🟢 appena aperta (29/07/2026), bozza
**Richiesta dell'utente**: il calcio è un gioco di squadra, ma ogni giocatore
incide più o meno di un altro. Raccogliere, per ogni giocatore: minuti
giocati a partita (titolare/subentrato, minuto di ingresso/uscita), gol,
assist, e — dove possibile — tocchi, passaggi, dribbling, interventi
difensivi; l'affaticamento da minuti consecutivi (inclusa la nazionale); i
gol subiti per portiere. **Estesa lo stesso giorno** a due fronti collegati:
un database **arbitri**, e un database **allenatori** (ipotesi: lo stile di
una squadra sotto un allenatore tende a ripetersi quando l'allenatore cambia
squadra) — per club **e** nazionali, con richiesta esplicita di estendere
l'analisi club anche alle **competizioni europee**.
**Dato**: **estende le piste 10 e 11**, non le duplica, e verificato **oggi
scaricando per davvero** il dataset upstream (non a memoria). Lo stesso CC0
già importato per i valori di rosa (`dcaribou/transfermarkt-datasets`, Fase
67) contiene: `appearances.csv` (**già scaricato** in `files/`,
minuti/gol/assist/cartellini per giocatore-partita — più ricco di quanto le
piste 10/11 supponessero); `games.csv`/`club_games.csv` (24+11 MB, **non
ancora importati**) con **arbitro e allenatore per partita, con >99,7% di
copertura**, sulle 5 leghe **e su Champions/Europa/Conference League** (incl.
qualificazioni) 2017-2025 — sblocca da solo l'estensione europea richiesta;
e `game_lineups.csv`/`game_events.csv` (pista 10, 487 MB insieme) per
titolare/panchina/minuto esatto dei cambi. Il portiere non richiede alcuna
fonte in più (si deriva da lineup + risultato).
**Il fronte arbitri non è nuovo**: il progetto ha già misurato che l'arbitro
vale quanto il fattore campo sui cartellini e persiste fra stagioni (Fase
125/126, `data/stagione_2026_2027/README.md` §4-bis) usando esattamente
`games.csv`; questa pista **struttura** quel lavoro (tabella versionata)
invece di rifarlo.
**Restano scoperti**: le statistiche "event/advanced" per i giocatori
(tocchi, passaggi, dribbling, contrasti — "Tier B", nessuna fonte pulita
nota oggi: Opta commerciale, WhoScored/SofaScore/FBref/Flashscore chiusi da
una sessione dedicata del 28/07/2026, verbale in
`cantiere_opta_flashscore/`, non ancora integrato come pista 20 in questo
file; StatsBomb open data e API-Football mai verificati per questo uso); lo
**stile di gioco** (possesso/tiri/xG) nelle coppe europee, perché Understat
copre solo le 5 leghe domestiche; e l'affaticamento/gli allenatori da
**nazionale** nelle finestre FIFA regolari (qualificazioni, amichevoli,
Nations League) — nessuna fonte mai cercata, stesso stadio della pista
13/meteo (i tornei finali, Europei/Mondiali/Copa América/Coppa
d'Africa/Coppa d'Asia, SONO coperti da `games.csv`, ma non bastano per il
caso d'uso "fatica durante la stagione").
**Ipotesi**: se un'informazione a livello di singolo giocatore aiuta, punta
nella stessa direzione già misurata dalla Fase 92/93 (il gap col mercato è
soprattutto discriminazione casa/ospite nelle partite equilibrate di seconda
metà stagione) — ma è un'ipotesi, non una certezza; il surrogato storico
della formazione schierata è già bocciato (Fase 98) e questo piano non lo
riapre con la stessa scorciatoia, propone di rifarlo con dati VERI. Per
l'allenatore, il disegno proposto (stessa persona, squadre diverse) è più
diretto del test già validato per l'arbitro (stessa persona, stagioni
diverse) nell'isolare il suo contributo da quello della rosa.
**Piano completo**: [`PIANO_DATABASE_GIOCATORI.md`](PIANO_DATABASE_GIOCATORI.md)
(cosa raccogliere in ordine di costo, bozza di schema, come dividerlo fra più
agenti, idee d'uso non ancora decise, rischi, e un **controllo finale su
Wikipedia** — §6-bis, richiesta utente — per verificare con una fonte
indipendente che arbitri/allenatori/giocatori derivati da `games.csv` siano
giusti, con campione dichiarato e soglia di allarme, prima di fidarsene per
il modeling). **Stato**: nessun dato ancora importato nel repo, nessun
codice scritto — il primo passo proposto (non ancora eseguito, e col
miglior rapporto valore/costo) è importare `games.csv`/`club_games.csv` e
fare un tracer bullet su una sola lega-stagione.

## 4 · Piste di raccolta prospettica (richiedono mesi, non giorni)

### 16. GG/NG quotato + aperture vere — ✅ **CHIUSA nella premessa (Fase 100)**
**Dato**: ~~NON esiste in nessun archivio (verificato); solo raccolta da oggi in
avanti~~ → **esiste**: la chiusura GG/NG di 1xBet (via footiqo) copre **5.337
partite** (2017-20, 5 leghe; la finestra 2017-19 della caccia O/U — pista 19 —
ne conta 3.652), e lo **stesso book** quota l'O/U 2.5 sulle stesse partite, il
che permette il confronto fra i due mercati a parità di book e di campione.
**Ipotesi caduta**: il GG/NG NON è «l'unico mercato senza tetto di efficienza
dimostrato». Misurato: il mercato GG/NG **è informativo** (log-loss 0.6840 contro
0.6921 di baseline LOSO, CI conclusivo) benché valga **un terzo** dell'O/U 2.5
dello stesso book; il nostro miglior prezzo lo **pareggia** (6 varianti su 6 con
CI a cavallo dello zero); il **DC perde** (+0.01036, IC95 [+0.00632, +0.01454])
e il book lo **ingloba** (α\* = 0.060, con α\*=0 nel **70%** dei fit — la stessa
firma della Fase 16 sull'1X2). Il GG/NG costa anche **1,7 punti di margine in
più** dell'O/U dello stesso book (overround 1.0461 contro 1.0295). Nessuna leva
aiuta. Numeri: `docs/audit_5_leghe/11_ggng.md` e
`numeri/ggng_contro_quote.json`.
**Perché NON si riapre la caccia storica**: le quote esistono, sono state
misurate, e il verdetto è quello sopra. Riproporre «il GG/NG è lo spazio non
ancora chiuso» significa ripetere un errore già pagato: lo spazio non era una
proprietà del mercato, era la nostra ignoranza.
**Cosa resta aperto**: solo la raccolta **prospettica** — il book non quota il
GG/NG nelle stagioni recenti, e le "aperture vere" (prima quota pubblicata, non
il venerdì di football-data) restano l'unico test rimasto della Fase 14. Il
motivo però non è più «non abbiamo quote»: è «non abbiamo quote *recenti*».
**🟢 CANALE APERTO E IN FUNZIONE dal 28/07/2026** (Fasi 116/118): il GG/NG è
uno dei tre mercati del regime di lungo raggio di
`scripts/fetch_smarkets_matches.py` (cron in `.github/workflows/smarkets-prematch.yml`,
archivio in `data/smarkets_matches/`, semantica in `docs/DATI.md` §5-ter). Le
quote di borsa **non sono le stesse** di un bookmaker — niente margine da
devigare, e c'è lo spread banco/puntatore al suo posto: il confronto con la
misura di 1xBet va fatto **dichiarando** questa differenza, non ignorandola. La
pista resta aperta finché non ci sono partite **giocate** da scorare: la prima
è il **15 agosto**.

### 17. Paper-trading della strategia draw-bias
**Dato**: nessuno nuovo — modello e storia già esistono; manca il
campione **fuori-sample futuro**.
**Ipotesi**: Fase 40, testuale: "merita raccolta prospettica (tracciare
stake reali su questa sola strategia, con soglia pre-registrata, per 1-2
stagioni) prima di qualsiasi conclusione. È l'unico posto dove il mercato
mostra una crepa e noi abbiamo lo strumento per vederla." È l'unica
strategia a ROI positivo mai trovata (+4.7% Serie A P83%, +3.6% Liga P81%)
ma non conclusiva per varianza campionaria — diversa dalla pista 16 perché
qui serve solo tempo, non un nuovo tipo di dato.
**⚠️ INDEBOLITA dall'audit a 5 leghe (Fase 100), ma non chiusa.** Con Bundesliga
e Ligue 1 il ROI pari-equilibrio **non è conclusivo in NESSUNA delle 5 leghe**
(tutti i CI attraversano lo zero), Bundesliga compresa nonostante il **+5,04%**
di stima puntuale, e la **Ligue 1 è a −7,82%** (`docs/PANCHINA.md` §archivio;
`docs/audit_5_leghe/06_tranche3.md` §4). Il segno quindi **non è universale**:
positivo in Serie A (+4,7%) e Liga (+3,6%), negativo in Premier (−5,4%, Fase 53)
e Ligue 1. **Conseguenza operativa**: se si fa il paper-trading, va fatto su
**una sola lega dichiarata prima** (la Serie A, dov'è nato) e con soglia
pre-registrata — usarlo su tutte e 5 sarebbe già la selezione post-hoc che il
progetto vieta (Fase 17). Sulla durata serve realismo: il CI del +4,7% è
**[−4,9%, +14,4%]** su 6 stagioni di Serie A, cioè una stagione di
paper-trading non stringe quasi nulla.

### 18. Dati in-play (quote minuto per minuto)
**Dato**: da raccogliere — progetto di raccolta dati, non backtest.
**Ipotesi**: Fase 0 (design): "per il live basterà condizionare la stessa
distribuzione al minuto e al punteggio" — mai realizzata. Fase 44: "l'
in-play è l'avversario più morbido — ma nessuno dei due è nei dati". Il
modello è già scritto per generalizzarci (matrice condizionabile); manca
solo il dato. Indicato come l'avversario meno efficiente più credibile,
mai nemmeno abbozzato.
**Aggiornamento (Fase 98)**: la **fondazione** ora c'è (pista 6: f=0.4396
misurata, primo tempo Poisson-compatibile, tempi quasi indipendenti) e con essa
il primo pezzo di in-play *offline* — la mis-calibrazione del secondo tempo
**è** un effetto di game-state, cioè esattamente ciò che un modello live deve
catturare. Prima di raccogliere quote minuto-per-minuto conviene chiudere il
modello a due stadi sui dati che già abbiamo: costa nulla e dice se il
condizionamento al punteggio produce segnale. → dalla Fase 101-ter quel lavoro
ha una voce propria, la **pista 6-bis**: è il **prerequisito** di questa, ed è
l'unica delle due che non richiede raccolta.

### 19. Quote O/U 2017-19 — CHIUSURA vera — ✅ **CHIUSA (Fase 100): trovata, e NON inserita**
**Esito (Fase 100)**: il dato **esiste** — `footiqo.com` pubblica il book
**1xBet**, che football-data non contiene: **3.652 partite su 3.652**, copertura
100%, validato come chiusura vera (corr **0.9977** con la chiusura Pinnacle
contro 0.9909 con l'apertura; riproduce il movimento 1X2 partita per partita;
margine e ultima cifra da book vero). **Non è stato inserito**, ed è una
decisione da NON rifare da capo, per **due** motivi entrambi misurati:
1. è **un solo book**, mentre le colonne di chiusura dal 2019-20 contengono una
   **media multi-book**: inserirlo creerebbe una **rottura di regime a metà
   colonna** (overround 1.035 contro 1.054, bias **+0.0088** verso l'Over);
2. come **proxy della media multi-book** è **peggiore della stima** che già
   abbiamo: sulla stagione 2019-20, dove esistono entrambi, MAE **0.0156**
   contro ~**0.012** della stima E3 in interpolazione (~**0.014** nel regime
   d'uso, che è il confronto onesto).
   *(Non è che il dato sia cattivo in sé: contro l'**apertura reale** è
   conclusivamente migliore, Δ log-loss −0.00229 [−0.00423, −0.00035]; contro la
   **stima E3** è indistinguibile, −0.00021 [−0.00278, +0.00243]. È inutile
   proprio perché la stima lo pareggia già.)*

**Fasi 105/106/107 — tre ri-tentativi, tutti negativi** (richiesta utente).
Nessuna fonte multi-book nuova: Wayback Machine, dataset nuovi, siti nuovi,
ri-verifica dal vivo di betexplorer, ricerca partita-per-partita (Fase 108: non
scala). E il confronto MAE, **ripetuto su 6 stagioni** invece che su una
(2019-20 → 2024-25), mostra che **non è stabile nel tempo**: oscilla fra 0.0096
e 0.0192, ed è peggiore nell'era porte-chiuse 2020-22. Non cambia la decisione,
ma la rende **meno granitica** di come era stata scritta.

Vive in `data/ricerca_esterna/`, fuori dagli snapshot, come **dato di verifica e
di ricerca**. Lezione: «non esiste» ≠ «non esiste dove ho cercato» — l'errore
delle due cacce precedenti era l'asse di ricerca (si cercava chi ri-esporta
football-data, ereditandone il buco).
**Dato**: piano dedicato (CHIUSO): [CACCIA_OU_2017_19.md](CACCIA_OU_2017_19.md).

<details><summary>Storico pre-Fase 100 (perché la caccia sembrava chiusa)</summary>

**Stato (Fase 73)**: il buco si è **dimezzato**. L'**apertura** O/U 2017-19 NON
mancava: l'unica linea (`BbAv`) è un'apertura reale, prima mal etichettata come
chiusura, ora nella colonna giusta (`odds_over25_open`, dato reale). Resta da
procurare solo la **chiusura** O/U (2.280 celle). Fase A (dataset già pronti su
Kaggle/GitHub/HF) e Fase B (scraping BetExplorer) **chiuse negative** —
confermato per ispezione diretta. La stima di chiusura (E3 pooled, Fase 62-bis)
è stata spremuta al massimo con 4 leve (Fase 72) + la dispersione max-vs-media
sbloccata dalla correzione (Fase 73): **8 leve ortogonali respinte**, E3 resta
il tetto pratico. **Non è un buco chiuso per sempre**: solo le vie economiche
note oggi sono esaurite.
**Da riprovare in futuro** (promemoria esplicito, richiesta utente):
ri-tentare la Fase A periodicamente (nuovi dataset compaiono nel tempo su
Kaggle/GitHub/HF — non ripartire dai 6 già controllati, cercarne con fonte
diversa da football-data.co.uk); valutare la Fase D (OddsPortal headless con
login) se emerge un modo a basso rischio di gestire le credenziali; valutare
fonti a pagamento se il progetto passa a un uso più operativo. Dettagli
completi (numeri, candidati testati, criteri di accettazione) in
`CACCIA_OU_2017_19.md` e nel diario (Fasi 71-72).
</details>

## 4-bis · Il mercato CAMPIONE DI STAGIONE — da riprendere OGNI anno, a inizio stagione

> **Perché sta qui e non fra le piste chiuse**: è l'unica pista del progetto con
> una **finestra temporale ricorrente**. Non è "da provare una volta": è un
> mercato che **si riapre ogni estate** e va riprezzato prima del via. Aperto
> con la **Fase 89**.

**Lo stato (Fase 89).** Il simulatore esiste ed è validato:
`src/models/season_sim.py` + `scripts/_run_fase89_season_champion.py`. Monte
Carlo di 20.000 stagioni dalle matrici del DC, spareggi ufficiali per lega.
Batte la baseline più forte (persistenza dalla classifica su 2 stagioni) di
**+0.2299**, IC95% [+0.0108,+0.4542], 14/24 stagioni — conclusivo per un soffio
e con il vantaggio **concentrato in Premier** (+0.57; SA +0.12, Liga +0.004 nel
rumore). È inoltre **sovra-confidente** (dichiara 60.1% sul favorito, ne azzecca
41.7%).

> **⚠️ Aggiornamento Fase 98 — quanto è solido quel "+0.2299".** Cambiando la
> griglia su cui la baseline di persistenza tara (β, w₂) in leave-one-out, la
> baseline passa da 1.4293 a **1.3816** e l'IC del guadagno **include lo zero**
> ([−0.3750, +0.0114]). Non è una smentita: la griglia della Fase 89 è un
> **superset** di quella alternativa sull'asse w₂ e produce comunque il risultato
> *peggiore*, il che è la firma dell'**instabilità della selezione LOO con
> n = 24**, non di una taratura migliore. La lettura onesta è: **il risultato
> della Fase 89 è fragile alla specificazione della baseline**, e il segno
> dipende da una scelta arbitraria. Coerente col calcolo di potenza della stessa
> fase: per concludere sull'outright servirebbero **~57 stagioni-lega**, mentre
> 3 leghe in una stagione danno **9,8% di potenza** (misura fatta con **3**
> leghe: con 5 il numero sale, ma **non è stato ricalcolato**). L'outright va dichiarato
> **non testabile prospetticamente** — non «perdente». Ragione in più per
> archiviare i prezzi ogni anno (punto 2 qui sotto): l'unica via per costruire
> il campione che serve.

> **🆕 AGGIORNAMENTO Fase 101-ter — c'è una via ALL'INDIETRO per la potenza, e
> costa un run.** Il backtest della Fase 89 vive su **24 stagioni-lega** perché
> le leghe erano **3**. Oggi sono **5**, e il simulatore le regge già: le regole
> di spareggio ufficiali di Bundesliga e Ligue 1 sono in
> `src/models/season_sim.py` (`TIEBREAK_RULES`: bundesliga `("gd","gf","h2h")`,
> ligue_1 `("gd","h2h","gf")` — un terzo set distinto, verificato contro DFL e
> LFP dalla Fase 100). Rilanciare la Fase 89 su 5 leghe porta il campione da
> **24 a ~40** stagioni-lega senza aspettare un anno: è **+16 osservazioni**
> contro le **+3** che ogni stagione nuova regala. Non basta a raggiungere le
> ~57 richieste, e va dichiarato che non è indipendente dal lavoro già fatto
> (le 24 restano dentro), ma è di gran lunga il modo più economico di stringere
> gli IC di questa famiglia — e ricade sul mercato campione, sul top-4 e sulla
> retrocessione insieme. Costo BASSO, un run.

> **Stagione 2026-27: il piano datato vive in [`newseason.md`](../newseason.md)**
> (radice del repo, file deperibile) — checklist con le date, sondaggi di
> fonti nuove e proposta di automazione. Questa sezione resta la regola
> permanente; quel file è l'esecuzione di quest'anno.

**⚠️ PROMEMORIA OPERATIVO — a ogni inizio stagione (luglio/agosto):**

1. **rilanciare** `python scripts/_run_fase89_season_champion.py` (≈2 minuti)
   dopo aver aggiornato `PROMOTED_2627` con le rose reali della nuova stagione;
2. **archiviare i prezzi outright** con **`python scripts/archive_outrights.py`**
   (Fase 97): un comando, **due fonti** (Polymarket + Smarkets), output
   **versionato** in `data/outright_snapshots/` (`YYYY-MM-DD.json` +
   `history.csv`). È l'unico modo per costruire, nel tempo, lo storico di quote
   outright che oggi ci manca (vedi §4 "raccolta prospettica"). Rieseguirlo
   nello stesso giorno è idempotente. **Non serve più congelare a mano.**
   → **Cadenza minima: una istantanea a metà agosto (prima del via) e una a
   stagione conclusa**; quelle spontanee sono in più e non costano nulla.
   Copertura al 25/07/2026 e trappole d'uso: `data/outright_snapshots/README.md`;
3. **scorare a maggio** la previsione dell'anno prima. Ogni stagione aggiunge
   **3 osservazioni** (una per lega) al campione da 24: è lento, ma è l'unico
   modo per far crescere la potenza statistica su questo mercato.

**📌 APPUNTO ESPLICITO (richiesta utente, luglio 2026): rifare questo lavoro sul
«2027 Champion» dopo aver avanzato con le fasi successive.** La previsione della
Fase 89 per il 2026-27 (Inter 66.8%, Arsenal 44.8%, Barcellona 62.4%) è stata
prodotta col simulatore **nella sua prima versione**, che si sa essere
sovra-confidente. Quando le prossime fasi avranno affrontato la **varianza
mancante** (sotto), la previsione 2026-27 va **ricalcolata e confrontata** sia
coi prezzi Polymarket di allora sia con quella di oggi: il confronto fra le due
versioni dirà quanto valeva la correzione — e la stagione 2026-27 sarà ancora in
corso o appena conclusa, quindi **scorabile**. È l'occasione migliore che il
progetto avrà per misurare un miglioramento su questo mercato, e va colta prima
che la stagione finisca.

**⚠️ AGGIORNAMENTO Fase 89-bis — la diagnosi è più precisa di così.** L'anatomia
dei 24 errori mostra che il modello **azzecca 8/8 quando il titolo resta e 2/16
quando cambia mano** (negli errori il campione uscente si riconferma 0/14), ma
che il campione vero è nel nostro **top-3 nel 96% dei casi** e che P(top-2) e
P(top-3) sono **già calibrate** (−3.5pp e +3.7pp). L'errore è **tutto nella
spartizione fra i due-tre leader**: 10/19 = 52.6% (lancio di moneta) dichiarando
71.6% (media di p₁/(p₁+p₂)). Quindi la correzione da cercare **non è più informazione**, ma un
**appiattimento della spartizione interna al gruppo di testa**.

**La leva 3 qui sotto (valore rosa) è stata TESTATA e BOCCIATA (Fase 89-bis)**:
log-loss 1.2384 contro 1.1994 del base, e 2/16 sulle stagioni di cambio esattamente
come il base. Il β è sempre positivo (+0.115) ma il segnale è già nei gol/xG: la
bocciatura delle Fasi 4c/66-70 **si trasferisce** all'outright, contrariamente a
quanto ipotizzato qui sotto. Resta valido il caveat che il dato è rilevato al 1º
settembre (il test era quindi favorevole alla covariata, e perde lo stesso).

**⚠️ AGGIORNAMENTO Fase 97 — la deriva regge a una verifica ESTERNA, ma il
residuo ha cambiato natura.** Smarkets quota la **retrocessione** Premier
(Polymarket no, in nessuna lega): primo confronto della correzione F94 con un
prezzo di mercato vero. MAE **8.84 → 7.32pp** con la deriva (9.68 → 8.11
filtrando i libri troppo larghi), corr 0.935: la deriva era stata tarata su una
statistica *interna* (dispersione della classifica) e migliora anche contro un
prezzo che non aveva mai visto. **Ma restano +19.6pp** di eccesso sulle
neopromosse, e lo scarto è **redistribuzione, non scala**: sovra-prezziamo le
promosse (Ipswich +36.5pp, Coventry +26.2pp) e sotto-prezziamo il resto della
coda (Sunderland −11.9, Leeds −7.9, Crystal Palace −7.4), con somme che
coincidono (2.92 contro 2.85 ≈ 3 retrocesse). Il residuo **non è più «varianza
mancante»**: è **sicurezza mal riposta su QUALI** squadre scendono — lo stesso
difetto della spartizione fra i leader, all'altro capo della classifica.

**🆕 PISTA APERTA (Fase 97) — la coda a ZERO: incertezza sui PARAMETRI, non sui
risultati.** Nella stessa misura, diamo **0.0%** di retrocessione a Man City e
Liverpool; il mercato dà **7.6%** e 1.1% (Man City con libro stretto, bid 6.9% /
ask 8.3%). Un modello che dichiara zero su un evento non impossibile prende
log-loss infinito se accade. La causa è strutturale: il simulatore campiona
l'incertezza dei **risultati** (e ora, con la deriva, quella dell'**evoluzione**)
ma **non quella delle stime**: le forze del DC sono trattate come note. Test
economico: ricampionare `(attack, defense)` dalla loro varianza asintotica (o via
bootstrap sulle partite) una volta per stagione simulata, esattamente come già si
fa per la deriva — l'infrastruttura `build_cdfs(shift=...)` di `season_sim.py`
c'è già e non va toccata, cambia solo *da dove* si estrae lo shift. Costo BASSO.
Bersaglio: le code (retrocessione delle forti, titolo delle non-favorite), dove
oggi mettiamo massa **esattamente nulla**. Rischio onesto: potrebbe gonfiare
tutte le probabilità e peggiorare il centro, come è già successo al top-4 con la
deriva (F94) — si misura per-mercato (§1.8), non si adotta in blocco.

**Quantità nuova da usare (Fase 89-bis)**: la **deriva di forza in-stagione**
misurata su 480 squadra-stagione vale **σ=0.189**, il **44%** della dispersione
fra squadre (0.434), con correlazione pre/post 0.903. È la varianza che il
simulatore ignora, ed è ora un numero, non un'ipotesi: si può iniettare
direttamente, senza tarare nulla sui 24 esiti (la taratura post-hoc è già
fallita, Fase 89).

**DUE COSE CHE L'AUDIT (Fase 90) HA VISTO E NOI NO:**

- **`rank` è già lì e lo buttiamo via.** `simulate_season` calcola la matrice
  delle posizioni di ogni stagione simulata e restituisce solo P(campione). Da
  quella matrice escono **P(top-4)** e **P(retrocessione)** — mercati veri, e
  soprattutto **480 osservazioni binarie** in tutto (24 stagioni-lega × 20
  squadre) invece delle 24 di cui ci lamentiamo. Zero modellistica nuova: è la
  via più economica per dare potenza statistica a questa famiglia di mercati.
  **FATTO (Fase 91)**, con un caveat da non perdere: ~~«il top-4 batte la
  persistenza, entrambi conclusivi»~~ è **RITIRATO** — l'IC a grappoli del
  guadagno top-4 è **[−0.0006, +0.0522]** e **include lo zero**. A reggere è il
  **test dei segni** (**19/24**, p=**0.0066**). Le 480 osservazioni danno
  potenza *apparente*: sono **a grappoli** (20 squadre della stessa stagione
  sono lo stesso esperimento), e vanno trattate come tali.
- **Un benchmark di mercato per l'outright è costruibile.** Diciamo che
  «battiamo il mercato non è testabile all'indietro» perché mancano le quote
  outright storiche: vero alla lettera, ma il **parere del mercato sulle forze**
  c'è in ogni stagione (le quote 1X2+O/U di ogni partita, invertibili col motore
  titolare; 21 stagioni-lega su 24 hanno la copertura). Simulare la stagione con
  i λ,μ del mercato dà l'avversario che ci manca. Non è il prezzo outright vero,
  e va dichiarato — ma è molto più di niente.

**⚠️ ATTENZIONE sulla deriva:** dei 0.189 misurati, circa il **38% in varianza è
rumore di stima** (la deriva vera è ≈0.14-0.15). Le leve 1 e 2 qui sotto
catturano in parte la stessa quantità: **non vanno sommate**.

**NUOVA PISTA (Fase 91) — il prior δ dipende dall'ORIZZONTE di predizione.**
Sui mercati posizionali la mis-calibrazione è **tutta sulle neopromosse**
(dichiarato 54.7% di retrocessione, realizzato 48.6%; il resto della lega è
calibrato a +1.1pp — valori dell'artefatto `experiments/fase91_positions.json`
dopo il fix del prior della Fase 92; il 58.7%/+1.8pp della prima stesura è
PRE-fix). Il δ attuale (0.23 / 0.33 / 0.22 / **0.28** / **0.19** — Serie A,
Premier, Liga, Bundesliga, Ligue 1, `src/config.py`) fu tarato sul **log-loss
della singola partita** (Fasi 7/57/100): lì è ottimo, ma propagato su 38 giornate la
penalizzazione si accumula e diventa troppo severa. È la prima costante ufficiale
del progetto che si scopre **dipendente dall'orizzonte**. Test proposto: ritarare
δ sul bersaglio stagionale (P(retrocessione) delle neopromosse, 72 osservazioni)
tenendo quello attuale per i mercati di partita, e verificare che il top-4 — oggi
calibrato — non peggiori. Costo: una griglia su δ × 24 stagioni-lega, ~30 minuti.

**STATO DOPO LA FASE 94.** La leva 1 (incertezza dei parametri) e' stata
provata nella forma piu' fondata — la **deriva di forza in-stagione**, misurata
e non postulata — con esito **parziale e per-mercato**: adottata sulla
retrocessione (IC esclude lo zero, calibrazione delle neopromosse da +6.1pp a
+2.8pp), nulla sul campione, **dannosa sul top-4** (che era gia' calibrato).
Due lezioni da portarsi dietro:
- la deriva **non e' uniforme**: neopromosse σ 0.299 contro 0.157 di tutte le
  altre. Qualunque futura iniezione di varianza va differenziata, altrimenti
  perturba troppo le squadre forti;
- **aggiungere incertezza a una previsione gia' calibrata la peggiora sempre**.
  Prima di iniettare varianza su un mercato, guardare l'ECE che ha oggi.

**IL RESIDUO, ora quantificato.** Anche col σ misurato la compressione della
classifica si chiude solo in parte (83° percentile → ~76°); chiuderla tutta
richiederebbe σ≈0.28, oltre la deriva fisica, e a quel livello il danno supera
il beneficio. Quindi **manca ancora qualcosa**, e il candidato è la
**correlazione fra partite**: le squadre attraversano periodi (serie positive e
negative) mentre il simulatore le tratta come indipendenti date le forze.
Test economico proposto: misurare l'autocorrelazione dei residui per squadra
lungo la stagione sui dati che gia' abbiamo, e se e' positiva iniettarla come
componente AR nella simulazione. Nessun dato nuovo.

**Le tre leve da provare, in ordine di costo (nessuna richiede dati nuovi):**

1. **Incertezza dei parametri** (la più promettente, §1.3 "versione economica"):
   oggi le forze sono un punto-stima tenuto fisso. Bootstrap delle partite di
   training → rifit → simulazione con forze diverse a ogni replica. Allarga la
   distribuzione **nella direzione giusta** e non richiede modellistica nuova.
   Costo: il fit costa ~3s, quindi 100 repliche ≈ 5 minuti per stagione-lega.
2. **Deriva delle forze in-season**: un random walk sulle forze per giornata
   (una sola σ da tarare). Attenzione: fa **cadere** la proprietà "l'ordine del
   calendario è irrilevante" (Fase 89), quindi servirebbe il calendario vero.
3. ~~**Mercato estivo**~~ **— BOCCIATA (Fase 89-bis), vedi sopra**: è la variabile che il confronto col mercato addita a dito
   (Milan 2.9% nostro vs 11.6%, Man United 0.7% vs 11.0%). `squad_value` è già
   negli snapshot ed è **aggiornato a inizio stagione**: usarlo come covariata
   nel fit pre-stagionale è diverso dal test già bocciato sulle singole partite
   (Fasi 4c/66-70), perché lì l'informazione dai risultati era fresca, qui è
   vecchia di tre mesi. **Non è coperto da quelle bocciature.**

**Il limite che resta comunque.** Non esistono quote outright **storiche**: si
può dimostrare "battiamo le baseline", non "battiamo il mercato". Solo la
raccolta prospettica del punto 2 può cambiarlo, e serviranno anni.

## 5 · Fatti misurati che condizionano il modeling futuro

- **Cambio di livello della fonte squad_value (+3-5%)**: sulle 456 celle
  in comune, rapporto nuovo/vecchio mediano SA 1.043, PL 1.027, Liga
  1.055 (rose leggermente più ampie via appearances + vintage più
  recente). Se si ri-testa `squad_value` come covariata, il livello non è
  confrontabile col passato: usare solo la nuova fonte, mai mischiare.
- **Regime d'errore dello stimatore F66** (esempio Lazio, stima→reale,
  M€): 1718 200→177, 1819 185→**337**, 1920 390→285, 2021 330→368, 2122
  305→325, 2223 275→271, 2324 271→275, 2425 418→**239**, 2526 284→270.
  Mediana ~15% ma code ±45-75%: il regime dichiarato (~29% mediano, p90
  75%) è reale — le stime valgono per analisi aggregate, MAI per feature
  per-partita.
- **Le 13 celle squad_value 2025-26 — CHIUSE (Fase 70)**: coperture player-
  scores insufficienti al 18/7/2026 (Bologna 79%, Como 82%, Cremonese 70%,
  Parma 64%, **Pisa 33%**, Udinese 80% · Leeds 72%, Sunderland 80% · Celta
  78%, Elche 56%, Espanol 59%, Levante 45%, **Oviedo 34%**; soglia 85%), ma
  recuperate con dato REALE preso direttamente da Transfermarkt (pagine di
  competizione per stagione, non il profilo-club che mostra il valore live)
  prima che il backfill a monte le chiudesse da sole. Scarto vs la stima
  Fase 66 mediano 22.5% (range −43%…+77%, coerente col regime d'errore
  dichiarato: conferma che la stima era onesta, non che fosse precisa
  cella-per-cella).
- **Alaves-Sociedad 14/10/2017 — chiusura 1X2 mancante (aggiornato Fase 73).**
  Nel grezzo PSH/PSD/PSA (Pinnacle pre-match) = 3.52/3.55/2.20 sono presenti,
  ma PSCH/PSCD/PSCA (Pinnacle chiusura) sono vuote — l'unico caso su 2.280
  partite (2017-19, 3 leghe). **Prima della Fase 73**: la chiusura ripiegava sul
  fallback `BbAvH` (media, ~5.3% margine vs Pinnacle ~2.0% — book diversi, non
  un movimento) e l'apertura era oscurata → la riga sembrava "senza apertura".
  **Dalla Fase 73** (chiusura = solo colonne `*C*` genuine, niente fallback):
  la chiusura 1X2 è onestamente **NaN** e l'apertura reale `PSH` è valorizzata.
  Quindi non è più "senza apertura" (la stima Fase 69 è stata ritirata); le
  manca la **chiusura** 1X2 (1 riga, non stimata: movimento 1X2 quasi tutto
  rumore, Fase 69). Torino-Fiorentina 10/01/2022 (recupero COVID) resta senza
  NESSUNA colonna pre-match → apertura 1X2+O/U stimata (Fase 69).
  Tentativo di ricerca esterna (sessione utente, luglio 2026): BetExplorer
  e OddsPortal da IP italiano reindirizzano a edizioni ADM-compliant
  (`/it/`, `centroquote.it`) che non pubblicano Pinnacle e nascondono lo
  storico apertura/chiusura dietro login — nessun dato recuperato.

## 5-bis · Affinamenti di ragionamento (rigore da irrobustire)

Non sono piste di dati ma punti dove la logica del progetto va tenuta più
netta — emersi dall'audit del luglio 2026 (Fase 84).

- **«α\*=0» e «la chiusura è mis-calibrata» convivono e vanno tenuti
  distinti.** Il progetto conclude "non si batte il mercato" da α\*=0 (Fase
  16/75): il mercato ingloba l'**informazione** del modello. Ma `dp_lvl`
  (Fase 51) mostra che i **prezzi** della chiusura devigata sono *essi stessi*
  mis-calibrati (sotto-dispersi) in modo correggibile — e la Fase 82 lo vede
  come bias residui del devig. Sono due affermazioni diverse: *informazione già
  inglobata* (α=0) ≠ *prezzi ben calibrati*. «Beat-the-close in log-loss senza
  edge di ROI» è esattamente "prezzi mis-calibrati ma nessuna informazione
  nuova da aggiungere". Evitare di fondere le due cose nei testi divulgativi.
- **θ confonde dispersione e temperatura, e il router ne usa UNO solo per tutto
  il listino.** Fase 51-bis/81: sull'1X2 il log-loss migliora monotòno fino a
  θ=1.5 (è **temperatura**: chiusura sotto-confidente ~T=1.10), mentre il
  risultato esatto ha ottimo interno a θ≈1.2 (è **dispersione**). Il router
  adotta θ=1.225 su tutto → sotto-affila la famiglia-1X2. Leva testabile
  (cross-lega mai fatta): separare θ_dispersione≈1.2 sulla matrice + una
  temperatura T sull'output 1X2, per-famiglia-di-mercato.
  **Aggiornamento (Fase 100)**: le due quantità non solo si confondono
  concettualmente, ma **si muovono insieme**: la T del temperature scaling e il
  θ del mercato sono in corrispondenza di rango **perfetta e inversa** sulle 5
  leghe (Spearman **−1.000**, p esatto di permutazione 2/120 = **0.017**) — due
  diagnostiche indipendenti (una sul nostro modello *senza* quote, una sul
  mercato) che sembrano misurare la stessa proprietà latente della lega.
  **Ridimensionamento dichiarato dalla fonte stessa**: 4 delle 5 T sono
  indistinguibili da 1 e 3 dei 5 θ stanno in una valle sei volte più piatta; il
  contenuto reale è la spaccatura a **due gruppi** (latine contro il resto), la
  cui concordanza casuale vale 1/10, non 1/60. **È una pista, non un
  risultato** (`docs/audit_5_leghe/10_modelli_nuove_leghe.md` §12.2).
- **Il devig moltiplicativo è la "fonte unica" ma è un benchmark che il
  progetto stesso sospetta storto.** Ogni gap (**+0.0167** in Serie A al codice
  di HEAD — il +0.0165 che si trova nelle fasi vecchie è **PRE-fix del prior
  della Fase 92**) è vs devig
  moltiplicativo della media multi-book, mentre ~~Shin è meglio su 3/3 leghe~~
  → ⚠️ **ridimensionato dall'audit a 5 leghe (Fase 100)**: sul pooled di 5
  leghe (**12.459** partite) Shin dà log-loss **−0.00034** [−0.00068, +0.0000]
  (p=0.052) e Brier **−0.00021** [−0.00039, −0.00001] — **ma a cluster di lega
  l'IC diventa [−0.000414, −0.0000008]**, cioè tocca lo zero — e **migliora 3
  leghe su 5**, conclusivo solo nelle «latine» (`docs/PANCHINA.md` riga 88 e
  voce 3). Resta il punto di metodo: la migrazione a Shin è **meno urgente** di
  quanto sembrasse, ma il benchmark resta una **scelta**, non un dato di natura.
  Vale, un giorno, una migrazione one-shot documentata a
  Shin (tutti i benchmark ricalcolati nello stesso commit) — o almeno
  dichiarare, accanto a ogni gap chiave, quanto cambia con Shin, così le
  conclusioni non restano ostaggio di una scelta di devig ammessa sub-ottima.

## 6 · Come procurarsi i dati

**⚠️ La premessa di questa sezione è cambiata (Fase 100): la rete NON è più
bloccata.** Rispondono 200, dall'ambiente: football-data.co.uk, understat.com,
transfermarkt.com, Kaggle via `kagglehub`, betexplorer/oddsportal (con i vincoli
dei rispettivi `robots.txt`), footiqo.com, gamma-api.polymarket.com,
api.smarkets.com; e — ri-verificati il 27/07/2026 — huggingface.co,
datasets-server.huggingface.co, data.jsdelivr.com. Restano bloccati solo
`api.github.com` (403 session-scoped) e `pub-*.r2.dev`. Elenco autorevole e
sempre aggiornato: [MANUALE_SOPRAVVIVENZA.md](MANUALE_SOPRAVVIVENZA.md) §1.
Quindi lo scaricamento diretto è la **prima** via da provare; il **workflow
GitHub Actions** che scarica e committa (pattern Fase 67) resta il canale di
riserva per ciò che il proxy blocca ancora.

Mappa aggiornata, pista per pista:
- **piste 5-9** (AH, primo tempo, conteggi, quota massima, Pinnacle): i dati
  sono **nei CSV grezzi in repo**, e basta estenderne l'estrazione in
  `loader.py` — **ma solo per 3 leghe**: `data/football_data_raw/` contiene
  **soltanto la Serie A**, e Premier/Liga arrivano dai bundle in `files/`. Per
  Bundesliga e Ligue 1 vanno scaricati da football-data.co.uk (ora raggiungibile);
- **6-ter, parte combinazioni**: non serve **niente** — è la matrice che il
  motore già calcola;
- **6-bis**: i punteggi del primo tempo, stessa situazione delle 5-9 (vedi la voce);
- **piste 10-11**: una riga in più nel `WANTED` del workflow;
- **pista 13** (meteo): fonte esterna ancora da identificare — è l'unica voce di
  questo elenco senza nemmeno un candidato;
- **pista 15** (O/U multi-linea): ~~fonte da identificare~~ → **una candidata è
  già in repo** (`data/ricerca_esterna/footiqo_*.json`, 1xBet, scaletta O/U
  0.5-4.5, 2017-20); i limiti sono nella voce della pista;
- **piste 16-18**: un workflow cron di raccolta **prospettica** — il canale è già
  pronto e collaudato (`scripts/archive_outrights.py`, Fase 97).

---

*Regola d'oro ereditata dalle Fasi 20-33: il tetto è INFORMATIVO, non
architetturale. Ogni pista qui sopra porta INFORMAZIONE nuova (o
un'architettura non ancora provata su informazione già in casa), mai solo
un rifacimento di ciò che l'audit ha già chiuso.*
