# Studio dedicato — Premier League e La Liga

Il repo è nato ed è cresciuto sulla Serie A (Fasi 0-52); Premier e Liga sono
entrate nelle Fasi 53-57 e sono state validate "in blocco" (tracer, ri-taratura,
market-implied multi-mercato). Questo file è il **quaderno di studio dedicato**
alle due leghe: cosa sappiamo dei loro dati, in cosa differiscono dalla Serie A,
quali leve sono state testate per-lega e con che esito, e il **piano ragionato**
dei prossimi test. Va aggiornato a ogni fase che tocca Premier/Liga (stessa
regola del CLAUDE.md §2: le decisioni nel DIARIO, i run in `runs.jsonl`, qui la
**visione d'insieme per-lega**).

Ultimo aggiornamento: **Fase 101-ter** (27/07/2026). Il corpo incorpora la
**Fase 92-bis** (§6-quinquies: il motore per-lega passa in config) e la
**Fase 100** (§6-sexies: le due leghe rimisurate dentro il bakeoff a 5).

> 📌 **Nota storica.** Fino alla Fase 101-bis questo quaderno aveva un riquadro
> che dichiarava il proprio arretrato: il corpo era fermo alla Fase 82 mentre
> Fase 92-bis e Fase 100 avevano già toccato entrambe le leghe. L'arretrato è
> stato colmato alla Fase 101-ter (rilievo `docs/AUDIT_FASI_80_100.md` §4
> punto 13). Le fonti restano `docs/audit_5_leghe/` per la Fase 100 e la voce
> di diario della Fase 92-bis.

**Le due leghe non vivono più in un progetto a 3.** Da Bundesliga e Ligue 1
(Fase 100) i confronti utili sono a **cinque**: dove serve, le tabelle di questo
file riportano anche le due leghe nuove, perché è lì che si vede se un tratto di
Premier o Liga è una singolarità o una famiglia (esempio: il θ — la Premier sta
con Bundesliga e Ligue 1 a ≈1.08-1.10, la Liga con la Serie A a ≈1.24).

---

## 1 · I dati che abbiamo (identici alla Serie A, per costruzione)

Snapshot congelati `data/{premier_league,la_liga}_matches.csv` (Fase 54, bundle
utente in `files/` + `scripts/build_league_snapshot.py`), **stesso schema** della
Serie A, 9 stagioni 2017-18 → 2025-26, 3.420 partite per lega:

| blocco dati | copertura PL | copertura Liga | note |
|---|--:|--:|---|
| risultati + 1X2 chiusura | 100% | 100% | chiusura = solo colonne `*C*` genuine (Fase 73) |
| 1X2 apertura | 100% | 100% | Pinnacle pre-match (`PS*`) preferito |
| O/U 2.5 chiusura | 77.8% | 77.8% | **manca 2017-19** (buco Fase 73, identico SA); stima E3 in `data/estimates/`, dalla Fase 100 **pooled a 5 leghe** (vedi sotto) |
| O/U 2.5 apertura | 100% | 100% | `BbAv` riclassificata apertura reale (Fase 73) |
| xG/npxG/PPDA/deep (Understat) | 100% | 100% | riconciliazione nomi verificata per identità (Fase 54) |
| squad_value | 100% | 100% | fonte player-scores + celle Transfermarkt reali (Fase 70: 13 celle 2025-26 sulle 3 leghe storiche; il registro `data/squad_value_2526_transfermarkt.csv` ne elenca oggi **16**, tutte Bundesliga e Ligue 1 — rettifica Fase 101) |
| assenze (stima) | 100% | 100% | stessa fonte terza della Serie A |
| congestione vera (`rest_days_full`, `midweek_europe`) | 100% | 100% | calendari coppe/Europa (Fase 59) — testata come covariata e **bocciata** (F79 su PL/Liga, F100 su 5 leghe su 5) |
| GG/NG quotato **negli snapshot** | 0% | 0% | football-data non lo fornisce |
| GG/NG quotato, **fonte esterna** (1xBet via footiqo, 2017-20) | 1.102 partite appaiate | 1.139 partite appaiate | ⚠️ dato REALE ma **fuori** dagli snapshot: sta in `data/ricerca_esterna/`, è un solo book (vedi §6-sexies.4) |

> ⚠️ **PREMESSA CADUTA (Fase 100).** ~~«Il GG/NG non ha quote nei dati, quindi è
> l'unico mercato dove non possiamo dimostrare l'efficienza del mercato».~~ Le
> quote di **chiusura** GG/NG esistono: book 1xBet via footiqo, **5.337 partite
> 2017-20 su 5 leghe** (Premier 1.102, La Liga 1.139 — fonte
> `docs/audit_5_leghe/numeri/ggng_contro_quote.json`, blocco `D1_per_lega`).
> Non sono state integrate negli snapshot (un solo book), ma sono bastate a
> misurare il tetto: §6-sexies.4.

**La stima della chiusura O/U 2017-19 è cambiata alla Fase 100.** Lo stimatore
E3 resta **pooled**, ma il fit è ora su **12.457** partite e **5 leghe**
(era 7.978 su 3), e l'errore dichiarato è quello del **regime d'uso** (fit su
stagioni successive a quelle stimate), non più quello di interpolazione:
`data/estimates/README.md` dà **~0.014** come MAE del regime d'uso; in
interpolazione la Premier sta a **0.0122** e la Liga a **0.0115**
(`docs/audit_5_leghe/09_chiusura_buchi.md` §3-bis). Il pooled a 5 batte il
pooled a 3 con CI conclusivo (Δ MAE −0.00026, CI [−0.00030, −0.00022]) e il
**per-lega è bocciato per questo uso** (+0.00104, CI [+0.00072, +0.00136]):
il ribaltamento che sembrava premiarlo era un artefatto del protocollo di
interpolazione. Il file `ou_close_2017_19.csv` contiene ora **3.638 righe** su
5 leghe (760 Premier, 756 La Liga).

**Config ufficiale per-lega**, due mappe distinte in `src/config.py`:

- `LEAGUE_CONFIGS` (Fase 57) — identica alla Serie A tranne il prior
  neopromosse: **δ Premier 0.33** (`ln(1.419/1.022)`), **δ Liga 0.22**
  (`ln(1.291/1.038)`), contro 0.23 in Serie A, 0.28 in Bundesliga e 0.19 in
  Ligue 1. γ (vantaggio-casa) auto-fittato dal DC.
- `MARKET_ENGINE` (Fase 92-bis) — le costanti del **motore market-implied**:
  per Premier e Liga tutto neutro (`dp_theta=None`, `phi0=0`, `kappa=0`,
  `sharpen_1x2=False`), cioè **motore LISCIO**. Dettaglio in §6-quinquies.

## 2 · Cosa sappiamo già (sintesi delle fasi cross-lega)

| fase | esito in una riga |
|---|---|
| 53 (tracer market-side) | θ>1 ovunque ma «decresce con la liquidità» (PL 1.07 < Liga 1.10 < SA 1.21) — *lettura poi FALSIFICATA dalla F100, §6-sexies.1*; **dp_lvl non batte la chiusura fuori SA**; draw-bias NON si replica in PL (pareggi SOVRA-prezzati, w_D=0.93), mezza replica in Liga |
| 55 (EDA) | Liga la più "casalinga" (γ 0.272), PL più gol e più dispersione; δ promosse PL 0.33 ≫ SA/Liga; mercato PL il più liquido (margine 4.3%) |
| 56 (tracer DC) | il DC Serie A non ritarato batte la baseline su entrambe; gap col mercato: PL +0.0207 > SA +0.0165 ≈ Liga +0.0162 *(tutti PRE-fix del prior della Fase 92 — vedi la nota ✱ del §3-bis)* |
| 57 (ri-taratura) | iperparametri PIATTI (emivita 730 peggiora ovunque); adottato solo δ per-lega; **il gap è informazione, non calibrazione** |
| 59-60 | colmati i gap dati: congestione vera, squad_value, assenze anche PL/Liga |
| 75 (apertura 2017-19) | market-implied dall'apertura: 17/20 mercati, trans-epoca e trans-lega; θ cresce nel tempo (per-contesto) |
| 76 (chiusura 2019-26) | market-implied batte il DC-da-gol su **13/14 mercati su tutte e 3 le leghe**, senza ritarare ρ=−0.06: la MATRICE è universale |
| 79-82 | le leve per-lega, una per una: §6 (φ35 e congestione), §6-bis (GG/NG), §6-ter (mega-sweep), §6-quater (verifica diretta) |
| **92-bis** | il motore per-lega **entra in config** (`MARKET_ENGINE`): `predict.py` smette di applicare a PL/Liga le costanti della chiusura Serie A. Costo verificato in Premier: **+0.0025** di log-loss 1X2 — §6-quinquies |
| **100** | entrambe rimisurate dentro il bakeoff a 5 leghe: tracer, ri-taratura, motore, φ35, Shin, GG/NG contro quote vere, beat-the-close, covariate — §6-sexies |

**Il quadro**: il *motore* (market-implied → matrice DC) è universale; le
*costanti di affinamento* (θ, dp_lvl) e i *bias sfruttabili* (draw-bias, tilt)
sono idiosincratici per lega. Quindi il lavoro per-lega utile non è ri-derivare
il motore (fatto), ma decidere **leva per leva** cosa vale su PL/Liga.

## 3 · EDA dedicata (Fase 79) — le tre dimensioni che decidono i prossimi test

Numeri da `scripts/_run_fase79_eda_pl_liga.py` (run `fase79_eda_pl_liga`).

### 3a · Struttura del pareggio per fascia di equilibrio (|pH−pA| devig, quartili)

P(pari) **reale − mercato** per fascia (n=855 per cella):

| fascia | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| equilibrate | **+0.032** | −0.009 | **+0.022** |
| medio-basse | +0.011 | +0.011 | +0.003 |
| medio-alte | −0.003 | −0.016 | +0.008 |
| sbilanciate | −0.010 | −0.013 | −0.018 |

**Lettura.** Il draw-bias di mercato della Serie A (pareggi sotto-prezzati
nelle partite equilibrate) esiste anche in Liga (+0.022, coerente col ROI
pari-equilibrio +3.6% P81 della Fase 53) e **NON esiste in Premier** (−0.009:
semmai il mercato inglese li sovra-prezza — coerente con w_D=0.93 e col ROI
−5.4% della Fase 53). Tre leghe, tre repliche indipendenti dello stesso schema:
*il pareggio è il punto dove i mercati differiscono di più*.
Attenzione però: questo è il bias del MERCATO. La φ35 corregge il deficit del
MODELLO (Poisson-DC sotto-stima i pareggi delle equilibrate): quel deficit può
esistere anche dove il mercato non sbaglia — lo decide il fit per-lega (§5, test A).

### 3b · Congestione — la Premier è un'altra categoria

| | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| partite con riposo ≤3g (casa) | 14.0% | **21.6%** | 18.3% |
| … a dicembre | 15.0% | **36.3%** | 21.7% |
| partite dopo midweek europeo (casa) | 8.9% | **14.2%** | 10.2% |
| gol casa: riposo ≤3g vs >3g | 1.57 / 1.44 | 1.73 / 1.50 | 1.53 / 1.45 |
| gol casa: dopo-midweek vs no | 1.72 / 1.44 | 1.82 / 1.51 | 1.71 / 1.44 |

**Lettura.** La Premier gioca a riposo corto il 50% in più della Serie A, e a
dicembre (Boxing Day, niente pausa) più di UNA PARTITA SU TRE è a riposo ≤3g.
Il differenziale descrittivo dei gol è POSITIVO (più gol dopo midweek/riposo
corto) ma è **confuso con la forza**: giocano in Europa i club forti. È
esattamente il motivo per cui serve la covariata dentro il modello (che
controlla per la forza), non la statistica grezza. In Serie A la covariata era
nel rumore (−0.0004, Fase 4e-bis); se paga da qualche parte, è nella lega col
triplo di esposizione (test B). *(Esito: non paga — §6, e la F100 lo ha esteso a
5 leghe su 5, §6-sexies.5.)*

### 3c · Vantaggio-casa nel tempo (γ_t per stagione)

- **Serie A**: 0.09–0.21, in calo tendenziale (2425/2526: 0.09/0.10).
- **Premier**: **volatile** — 0.29 (1718) → **0.01 (2021, COVID)** → 0.29 (2223)
  → 0.06 (2425) → 0.22 (2526). Il crollo COVID fu quasi totale e il recupero
  oscilla.
- **La Liga**: **alto e stabile** — 0.18–0.34, perfino nel COVID (0.18) resta
  sopra il γ medio Serie A; 2526 al massimo (0.34).

**Lettura.** Conferma della Fase 55 con la dimensione temporale in più: il γ
Liga è un tratto strutturale (non un artefatto di un'epoca), quello Premier
è la fonte di rumore più grossa tra le tre leghe. Il DC lo fitta con
l'emivita 365g, che media ~2 stagioni: nelle stagioni-anomalia Premier
(2021, 2425) il fit arriva in ritardo per costruzione. Il "γ dinamico" resta
però chiuso per test in SA (Fasi 47/48: l'effetto si sgonfia con più dati);
riaprirlo per la Premier richiederebbe un CI conclusivo lì — annotato come
pista condizionale, non come test immediato.

## 3-bis · LE DIFFERENZE CON LA SERIE A, in un colpo d'occhio

La tabella-sintesi di TUTTO ciò che è stato misurato finora sulle leghe
(fonte tra parentesi). È la mappa per ragionare sui prossimi modelli: dove la
riga è uniforme il fenomeno è "del calcio" (versione generale possibile,
principio §1.9); dove diverge è per-lega (mai copiare i numeri, §7). Le due
colonne di destra (Bundesliga, Ligue 1) sono riempite dove la Fase 100 ha
misurato la stessa quantità: servono a dire se un tratto di PL/Liga è una
singolarità o una famiglia.

| dimensione | Serie A | Premier | La Liga | Bundes. | Ligue 1 | universale? |
|---|--:|--:|--:|--:|--:|:--|
| γ vantaggio-casa (F55) | 0.150 | 0.185 | **0.272** | — | — | ❌ per-lega (auto-fittato dal DC) |
| γ_t stabilità (F79-EDA) | in calo | **volatile** (0.01 COVID, 0.06 nel 2425) | **alto e stabile** | — | — | ❌ |
| pareggi % (F55) | 26.0% | **23.4%** | 26.5% | — | — | ❌ la "firma inglese" |
| δ neopromosse (F55/57/100) | 0.23 | **0.33** | 0.22 | 0.28 | 0.19 | ❌ per-lega (in config) |
| gol/partita · Over% (F55) | 2.72 · 52% | **2.84 · 54%** | **2.58 · 47%** | — | — | ❌ |
| Var/Media gol (F55) | 1.06 | **1.11** | 1.05 | — | — | ❌ |
| corr xG-gol (F55) | 0.61 | 0.64 | 0.62 | — | — | ✅ xG di pari qualità |
| emivita/shrinkage/α ottimi (F57/F100) | 365/1.5/0.75 | uguali | uguali | uguali | uguali | ✅ **iperparametri DC generali, 5 leghe su 5** |
| margine book (F100, 7 stagioni) | 4.87% | **4.27%** | 4.75% | 4.76% | 5.02% | ❌ liquidità: PL il più liquido, L1 il meno |
| gap DC vs mercato (F56/F100) | +0.0165 ✱ | **+0.0207** ✱ | +0.0162 ✱ | +0.0181 | +0.0190 | ~ stesso ordine in 5 leghe su 5 |
| θ sotto-dispersione MLE (F53 → F100) | **1.21 → 1.232** | 1.07 → **1.085** | 1.10 → **1.242** | 1.080 | 1.103 | ❌ **due famiglie**: latine ≈1.24, PL/BL/L1 ≈1.08-1.10 |
| θ OPERATIVO del router (F81, da griglia+lfo) | ⚽ 1.225 | **1.0 (liscio)** | 🪑 **~1.2** (in panchina, non in config) | ❌ 1.0 | ❌ 1.0 | ❌ ma SA≈Liga: le latine convergono |
| φ0 del mercato, LOSO 7 stagioni (F100) | 0.2433 | **0.0341** | 0.2461 | 0.1827 | 0.0000 | ❌ e corr(θ, φ0) = **+0.755**: θ e deficit-pareggio sono la stessa cosa |
| dp_lvl batte la chiusura (F52/53 → F100) | **sì (CI)** | no (+0.0010, nel rumore) | no (−0.0010, nel rumore) | **no, CI CONTRO** | no | ❌ idiosincrasia SA (e serve tilt **e** θ: §6-sexies.3) |
| draw-bias mercato equilibrate (F79-EDA) | **+0.032** | **−0.009 (opposto)** | +0.022 | — | — | ❌ segno NON universale |
| w_D ricalibrato della chiusura (F100) | > 1 | < 1 | **0.978** | 1.089 | 0.981 | ❌ segno sparso: la tassonomia «latine/inglesi» su w_D **non esiste** |
| deficit-pareggio del DC: φ0 fittato (F35/79) | 0.39 | **0.00 (bound)** | 0.39 | — | — | ❌ tratto LATINO, assente in PL |
| ROI pari-equilibrio (F40/53 → F100, 7 stagioni) | +4.7% (P83) → +3.15% | **−5.4% → −3.82%** | +3.6% (P81) → +1.90% | +5.04% | −7.82% | ❌ mai conclusivo in **nessuna** lega (F100) |
| congestione riposo ≤3g (F79-EDA) | 14% | **22% (36% a dic.)** | 18% | — | — | ❌ ma covariata = rumore su **5/5** (F79+F100) |
| profilo fine-stagione tasso-ospite (F80) | ~1.0 (adattivo) | **×1.10 (boost)** | **×0.915 (CALO)** | — | — | ❌ segno opposto: in Liga il vantaggio-casa non crolla nel finale |
| catena GG/NG migliore (F50/80) | φ35+k34 (P 97%) | **liscio** (nulla paga) | **φ35 sola (CI<0, P 99%)** | — | — | ❌ stessa cassetta degli attrezzi, assemblaggio per-lega |
| calibrazione del mercato (F82) | tilt casa/pari ±0.02 | **quasi perfetta** (ECE fino a 0.003) | GG −0.036 (raddrizzato dal router θ) | — | — | ❌ le mis-calibrazioni sono i bias per-lega noti |
| hit-rate 1X2 modello (F82) | 54.2% (=mercato) | 55.3% (=mercato) | 54.3% (=mercato) | — | — | ✅ si indovina quanto il mercato, ovunque |
| market-implied batte il DC-da-gol (F76 → F100, 15 mercati) | 13/14 → 14/15 | 13/14 → **14/15** | 13/14 → **15/15** | 15/15 | 15/15 | ✅ **il motore è universale** (ρ=−0.06 unico) |
| pari/dispari imprevedibile (F26/75/76/100) | sì | sì | sì | sì | sì | ✅ irriducibile ovunque (**6 repliche**) |

> ✱ **PRE-fix del prior (Fase 92).** I tre gap +0.0165 / +0.0207 / +0.0162 sono
> le misure della Fase 56, prese **prima** del fix del prior della Fase 92; la
> Fase 100 ha rifatto lo stesso tracer sulle 5 leghe con la stessa finestra
> (6 stagioni 2020-21 → 2025-26) e ha ritrovato **gli stessi valori alla quarta
> cifra**, aggiungendo i CI95: SA +0.0165 [+0.0107, +0.0225], **PL +0.0207
> [+0.0138, +0.0275]**, **Liga +0.0162 [+0.0103, +0.0225]**
> (`docs/audit_5_leghe/06_tranche3.md`, passo 2). Al codice di HEAD lo stesso
> backtest **in Serie A** dà **+0.0167** (modello 0.979890 / mercato 0.963191,
> ri-eseguito il 27/07/2026): è il numero-bandiera attuale del progetto. Il
> corrispondente valore post-fix **non è stato rimisurato per Premier e Liga**:
> i loro gap qui sopra restano PRE-fix, e vanno letti così. Il confronto fra le
> leghe non cambia — sono tutte sulla stessa base.

**Sintesi in tre righe.** (1) Tutto ciò che è *struttura* (matrice DC,
market-implied, iperparametri del fit, xG) trasferisce così com'è. (2) Tutto
ciò che è *livello* (γ, δ, gol, θ) è per-lega ma o è auto-fittato o è già in
config. (3) Tutto ciò che è *bias sfruttabile* (draw-bias, sotto-dispersione,
dp_lvl) è idiosincratico — e la Premier non ne ha nessuno: è la lega dove il
book sbaglia meno e il modello serve solo a prezzare i mercati non quotati.
*(La spiegazione «perché è il mercato più liquido» è però **caduta** alla
Fase 100: la liquidità non predice il θ — §6-sexies.1.)*

## 4 · Ragionamento: quali modelli/valori usare oggi su PL/Liga

Stato per-mercato (dalla rosa PANCHINA.md; aggiornato dopo Fase 92-bis e 100):

- **Con quote 1X2+O/U** (il caso d'uso principale): **market-implied puro**,
  ρ=−0.06, per TUTTI i mercati sui gol — su PL/Liga **senza** router θ,
  **senza** dp_lvl, **senza** φ35 famiglia-pareggio.
  In pratica: su PL/Liga il listino si prezza con la matrice market-implied
  *liscia*; ogni affinamento Serie A resta SPENTO. Dalla **Fase 92-bis** questo
  non è più una raccomandazione scritta a mano ma lo **stato del codice**:
  `src.config.MARKET_ENGINE["premier_league"|"la_liga"]` ha tutte le costanti
  neutre e `scripts/predict.py` le legge (§6-quinquies).
  ⚠️ Attenzione alla differenza fra le due leghe: in **Premier** il liscio è
  l'ottimo **misurato** (F81: valli centrate sul riferimento su ogni asse;
  F79: la φ35 peggiora); in **Liga** il liscio è una **scelta prudenziale** —
  θ≈1.2 (F81) e φ35-sola sul GG (F80) sono misurate positive ma stanno in
  panchina, e la regola del progetto è che una voce in panchina resta off.
- **Senza quote** (fallback): DC + blend xG con `LEAGUE_CONFIGS` (δ 0.33/0.22).
- **Stime dati mancanti**: E3 pooled per la chiusura O/U 2017-19 — dalla
  Fase 100 fittato su **5 leghe** e 12.457 partite, con errore dichiarato nel
  regime d'uso (§1); stimatore squad_value ibrido (F66), oggi a 0 righe attive.

## 5 · Piano dei test per-lega (in ordine di costo/beneficio)

| # | leva | perché / aspettativa onesta | stato |
|---|---|---|---|
| A | **φ35 per-lega** (equilibrio-pareggio, path DC) | unica cella ⬜ del motore titolare; EDA 3a: il deficit-modello può esserci anche dove il mercato non sbaglia; su PL possibile φ0≈0 (il fit stesso è la risposta) | ❌ **bocciata su entrambe (F79, §6)**; ri-testata sul path market-implied dalla F100: **nel rumore in tutte e 5 le leghe**, Serie A compresa (§6-sexies.2) |
| B | **covariate congestione** rest_full/midweek | colonne pronte (F59), mai testate fuori SA; PL la lega più esposta (3a); in SA erano rumore | ❌ **rumore ovunque (F79, §6)**; F100: `rest_full` è rumore su **5 leghe su 5**, e nemmeno il dato di congestione *corretto* lo salva (§6-sexies.5) |
| C | GG/NG φ35+knee34 sul market-implied per-lega | panchina #1: la promozione è condizionata proprio al "riappare su PL/Liga"; ~~il GG/NG è il mercato senza tetto dimostrato~~ **PREMESSA CADUTA (F100)**: il tetto ora è misurato (§6-sexies.4); **dopo la F79 il prior su PL è sfavorevole** (φ0→0), su Liga plausibile | ✅ **fatto (F80, §6-bis): Liga φ35 CI<0; PL nulla; k34 solo-SA** |
| D | Devig di Shin per-lega nel motore | direzione già confermata 3/3 leghe (F53); è candidato GENERALE, costo = migrazione fonte unica | 🟡 **misurato (F100)**: conclusivo in **La Liga** su entrambi i protocolli (−0.0008 LOSO, −0.0009 LFO) e in SA LFO; **nel rumore in Premier**. Il pooled a 5 non regge a cluster di lega → resta fuori dalla fonte unica (§6-sexies.6) |
| E | Ricalibrazione w_D/w_A per-lega della chiusura | segno OPPOSTO tra PL e SA/Liga (F53 + EDA 3a): mai pooled, solo per-lega; servono più stagioni | 🟡 **ridimensionata (F100)**: con w_D Liga = **0.978** la tassonomia «latine w_D>1 / inglesi w_D<1» **non esiste** (segno sparso su 5 leghe); e sul path DC la leva peggiora, in Ligue 1 con CI conclusivo. Il bias per classe non è stabile nemmeno **nel tempo** dentro la stessa lega (±0.03 stagione su stagione) |
| F | γ dinamico per la Premier | EDA 3c: γ_t Premier volatile; ma architettura chiusa in SA (F47/48) | condizionale (solo con un meccanismo nuovo) |

Regole invariate: una leva alla volta, CI95<0 per adottare, run in
`runs.jsonl`, aspettativa dichiarata PRIMA del test.

## 6 · Risultati dei test per-lega (Fase 79)

Run `fase79_leve_per_lega` (48 backtest walk-forward, 2021→2526, config
ufficiale per-lega, bootstrap B=10.000). Dettaglio completo nel
[DIARIO, Fase 79](DIARIO.md).

**Δ log-loss 1X2 vs base (positivo = peggiora); mercato rif. PL 0.9623, Liga 0.9681:**

| leva | Premier (base 0.9830) | La Liga (base 0.9843) | esito |
|---|--:|--:|:--|
| φ35 equilibrio-pareggio | +0.0006 (P 7%) | +0.0002 (P 43%) | ❌ entrambe |
| covariata `rest_full` | +0.0005 (P 9%) | +0.0003 (P 26%) | ❌ entrambe |
| covariata `midweek` | +0.0001 (P 38%) | +0.0001 (P 39%) | ❌ entrambe |

**Il risultato strutturale (più informativo dei Δ):**

- **Premier: φ0 sbatte sul bound zero in 4/6 stagioni** (media 0.052). Il
  deficit-pareggio del DC **non esiste** in Premier — il modello lì
  sovra-stima già i pareggi delle equilibrate (reale 0.246 vs base 0.268;
  la φ spinge nel verso sbagliato, 0.277). Con l'EDA §3a e la Fase 53 fanno
  **tre conferme indipendenti** (mercato, frequenze, fit del modello):
  ogni leva-pareggio va tenuta lontana dalla Premier.
- **La Liga: fit quasi identico alla Serie A** (φ0≈0.39, κ≈4.1 vs 0.39/3.6
  della F35) e deficit reale (equilibrate: 0.321 vs 0.294) — il
  deficit-pareggio è un **tratto delle leghe latine**. Ma la φ sovra-corregge
  (0.344) e il log-loss non paga; κ sul bound 5.0 in 4/6 (mal-identificato).
- **Congestione**: β_rest_full PL −0.019 (direzione sensata, 5/6 negativo) ma
  peggiora out-of-sample; Liga instabile (+0.053…−0.040). Il **β_midweek
  stabile della SA (−0.020, 6/6) non si replica** (PL −0.001 alterno, Liga
  +0.008 segno opposto). Rumore anche nella lega più congestionata: il fit
  pesato nel tempo assorbe già l'effetto.

**Conseguenza operativa (aggiorna §4):** confermato in pieno — su PL/Liga il
listino si prezza col market-implied **liscio** e il fallback DC resta con la
sola config `LEAGUE_CONFIGS`; nessuna leva Serie A si accende fuori casa.
*(Aggiornamento F80: per la Liga la famiglia GG/pareggio guadagna una leva
propria — vedi §6-bis.)*

## 6-bis · La catena GG/NG per-lega (Fase 80) — il primo CI conclusivo fuori dalla Serie A

Run `fase80_ggng_mi_league` (12 run, 3 leghe × 4 varianti; SA rifatta sulla
stessa finestra 1920→2526 come riferimento). Δ GG/NG vs motore liscio,
bootstrap B=10.000 (* = CI95 esclude lo zero):

| variante | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| φ35 | −0.0003 (P 95%) | +0.0001 (P 16%) | **−0.0006 (P 99%)*** |
| k34 (nudge-μ) | −0.0012 (P 97%) | −0.0002 (P 62%) | **+0.0008 (P 2%) peggiora*** |
| φ35+k34 | **−0.0014 (P 97%)** | −0.0002 (P 62%) | +0.0002 (P 28%) |

**Le tre catene GG/NG (una per lega):**

| lega | catena migliore | costanti (medie LFO) |
|---|---|---|
| Serie A | market-implied → k34 → φ35 (Fase 50, riconfermata qui) | φ0 0.16-0.20, κ 1.5 |
| Premier | market-implied **liscio** (nessuna leva paga) | — (fit sui bound: φ0 0.68→0.00) |
| La Liga | market-implied → **φ35 sola** | **φ0 ≈ 0.32, κ ≈ 2.9** (stabili 5/6 fit) |

**Perché il k34 tradisce in Liga**: il profilo di fine stagione del
tasso-ospite è **invertito** — boost-38ª 0.915 (l'ospite segna MENO nel
finale) contro 1.10 della Premier e ~1.0 della Serie A. Coerente col γ_t
alto e stabile dell'EDA §3c: in Spagna il vantaggio-casa non crolla nelle
ultime giornate. Applicare la costante Serie A lì spinge nel verso sbagliato
(+0.0008 con CI>0): l'esempio da manuale del §7 ("mai copiare i numeri").

**Onestà**: il CI<0 della Liga è su test pre-dichiarato, direzionale e su lega
quasi vergine — ma è il primo risultato lì: prudenza multiple-testing (F17) =
in **panchina alta**. La condizione di promozione «quando `predict.py` diventa
per-lega» è **soddisfatta** (Fase 92-bis: il tool è per-lega su entrambi i
modelli); resta l'altra metà, cioè la **conferma su stagioni nuove**
(2026-27+). *(Aggiornamento F100: sul giudice esterno — le quote GG/NG vere di
1xBet — nessuna leva GG/NG paga in nessuna lega, §6-sexies.4.)*

## 6-ter · Il mega-sweep delle costanti (Fase 81) — le curve di risposta per lega

Run `fase81_mega_sweep_mi` (12) + `fase81_joint_rho_theta` (2): 63 varianti
per lega (ρ×11 con ri-inversione, θ×10, φ0×κ×**37**, knee×5) su 6 mercati, con
il **selettore walk-forward "lfo"** come guardia di onestà (sceglie la costante
solo dal passato). Dettaglio nel [DIARIO, Fase 81](DIARIO.md).
*(Le combinazioni φ0×κ sono **37**, non 31: `[(0,0)] + 6×6` — rettifica della
Fase 101; 11+10+37+5 = 63, il totale era già giusto.)*

**Le costanti operative del motore, lega per lega (stato dopo la F81):**

| costante | Serie A | Premier | La Liga |
|---|---|---|---|
| ρ | −0.06 (universale, confermato dal check congiunto) | −0.06 | −0.06 |
| θ router | ⚽ 1.225 (riconf.: cs −0.0078 lfo CI<0) | ❌ 1.0 — la curva è piatta | 🪑 **~1.2** (cs −0.0069*, 1X2 −0.0023*, GG −0.0025*, lfo CI<0 — **ribalta la F53**) |
| φ pareggio/GG | ⚽ router (F41/44) | ❌ 0 su tutta la griglia | 🪑 (0.7, 0.5): GG lfo −0.0019* |
| nudge-μ | 🪑 k34 solo GG (−0.0012*) | ❌ none | ❌ none (profilo invertito) |

**Le tre lezioni della fase:**
1. **La Premier è già al suo ottimo su ogni asse** (valli centrate sul
   riferimento, 63 varianti): il motore liscio non è un ripiego, è il
   modello giusto per il mercato più liquido.
2. **θ-da-mercati ≠ θ-da-punteggi**: la F53 bocciò il router-Liga col θ da
   MLE sui punteggi (1.097); l'ottimo sui MERCATI è ~1.2 — con quello il
   router paga anche in Liga. Le costanti operative si scelgono con
   griglia+selettore sui mercati, mai con la sola verosimiglianza.
   > ⚠️ **Precisata dalla Fase 100.** Il divario 1.097 vs ~1.24 **non** è tutto
   > «metrica»: il 1.097 è la **media di 8 fit MLE a finestra espandente**
   > (riprodotta 1.103), mentre un fit **pooled** sulle stesse 9 stagioni dà
   > 1.199 e sulle 7 stagioni con chiusura O/U reale 1.242. Due terzi del
   > divario sono l'**aggregazione dello stimatore**, un terzo la finestra
   > (il 2017-19 è davvero un'epoca a θ basso: 1.062 anche con la chiusura
   > 1xBet reale). E la frase «la griglia stima meglio dell'MLE» è una
   > tautologia: sul risultato esatto la griglia ricade sul θ MLE entro mezzo
   > passo in 5 leghe su 5. La formulazione giusta è **«mercati diversi
   > vogliono θ diversi»**.
3. **Una leva, non due**: ρ molto negativo sembrava aiutare, ma il check
   congiunto ρ×θ mostra che era θ sotto mentite spoglie (a θ ottimo, ρ
   oltre −0.06 peggiora il ris. esatto di +0.009/+0.012). ρ=−0.06 resta
   l'unica costante davvero universale del motore.

## 6-quater · La verifica diretta (Fase 82): siamo calibrati, e il router raddrizza la Liga

Run `fase82_verifica_predizioni` (3): calibrazione (bias, ECE) e hit-rate su
19 mercati binari + 1X2 + multigol + risultato esatto. Sintesi cross-lega:

- **le probabilità sono giuste**: |bias|≤0.02-0.03 e ECE 0.004-0.04 quasi
  ovunque; sul risultato esatto il top-pick indovina il 12-15% dichiarando
  il 12-14% (confidenza onesta);
- **hit-rate = mercato** su tutte e 3 le leghe (1X2 54-55% vs baseline
  40-45%); pari/dispari resta un coin-flip;
- le mis-calibrazioni residue sono i **bias per-lega noti** (SA tilt
  casa/pari; PL quasi perfetta; Liga GG −0.036) e il **router θ della F81
  le raddrizza in Liga** (GG bias −0.036→−0.008, ECE 0.036→0.012):
  conferma della F81 su una metrica indipendente dal log-loss;
- il path DC senza quote indovina un filo meno (1X2 52.9-53.5%): la
  gerarchia market-implied > DC vale anche in hit-rate.

> ⚠️ **Ridimensionata dalla Fase 100 su un fianco.** L'audit di calibrazione a
> 5 leghe ha mostrato che l'indicatore usato per dire «i prezzi sono onesti
> nella FORMA» (r = ECE / ECE_null95) **non ha potenza**: su dati generati da
> una verità storta fino a 11,8 punti percentuali quell'indicatore dichiara
> comunque «affidabile». Con un test potente (ricalibrazione logistica, Wald su
> b=1) la pendenza è **b > 1 in 10 celle su 12**, cioè prezzi troppo compressi
> verso il tasso base — Serie A 1X2-casa b=1.182 (p=0.002), Serie A clean sheet
> casa 1.264 (p=0.003). Quel test è stato fatto su Bundesliga, Ligue 1 e Serie A
> di controllo: **su Premier e Liga non è ancora stato rifatto** (casella
> aperta). Ciò che regge della F82 è il resto: dove la quota esiste siamo
> calibrati **quanto il book**, e il bias è in larga parte *ereditato* dal
> mercato, non prodotto da noi.

## 6-quinquies · Fase 92-bis — il motore per-lega esce dai documenti ed entra in `src/config.py`

Fino alla Fase 92-bis il quaderno diceva «su PL/Liga tenere spenta ogni leva
Serie A» (§4) ma **il codice non lo faceva**: `scripts/predict.py` applicava a
tutte le leghe le costanti tarate sulla chiusura Serie A (θ=1.225,
θ_DC=1.138, φ0=0.30, κ=1.5, `sharpen_1x2=True`), benché la mappa per-lega
fosse già stata misurata alle Fasi 79/81. Era il caso peggiore per un progetto
che si è dato la regola §7 «mai copiare i numeri fra leghe»: la regola era
scritta e violata dallo strumento che l'utente usa davvero.

**Il costo, misurato in Premier** (voce di diario Fase 92-bis):

| | log-loss 1X2 |
|---|--:|
| motore col router Serie A | 0.9665 |
| **motore liscio** | **0.9640** |
| mercato (riferimento) | 0.9639 |

**+0.0025** di log-loss, e **+2.7 pp** di pareggio previsto sopra il
realizzato. Il danno viene dalla **φ35**, non dal θ — coerente con la F79
(in Premier il DC sovra-stima già i pareggi equilibrati) e con la F81 (φ\*=0 su
tutta la griglia).

### 📐 Il modello in dettaglio

Nessuna matematica nuova: cambia **quali costanti** riceve la funzione di
pricing della Fase 44/52 (verificata in `src/models/market_implied.py`):

```
d = mi.price_markets(lam, mu, rho, phi0, kappa, dp_theta)
```

Prima erano costanti di modulo tarate sulla Serie A; ora vengono da una mappa
per-lega (`src/config.py`, `MARKET_ENGINE` + `market_engine()`):

```
MARKET_ENGINE[lega] = {dp_theta, dp_theta_dc, phi0, kappa, sharpen_1x2}
market_engine(lega)  ->  default LISCIO: {None, None, 0.0, 0.0, False}
```

Il ragionamento sul valore di ogni voce, per le due leghe di questo quaderno
(§2-bis: perché *quel* numero):

- **Premier** — `dp_theta=None`, `phi0=0.0`, `kappa=0.0`, `sharpen_1x2=False`.
  Non è prudenza: è **misura**. La F81 trova l'ottimo di ogni asse già sul
  riferimento (ρ\*=−0.06, θ\*≈1, φ\*=0, 63 varianti) e la F79 misura che la φ35
  **peggiora**. La Fase 100 lo conferma da fuori: θ MLE 1.085, valle sul
  risultato esatto profonda −0.0012 (contro −0.0081 in Serie A).
- **La Liga** — stesse costanti neutre, ma **per scelta, non per misura**:
  θ≈1.2 (F81) e φ35-sola sul GG (F80) sono misurate positive e stanno in
  **panchina**; la regola del progetto è che una voce in panchina resta OFF di
  default. Chi volesse accenderle deve prima promuoverle in `PANCHINA.md` con
  una conferma su stagioni nuove.
- *(Serie A, per contrasto: `dp_theta=1.225`, `dp_theta_dc=1.138` dalla Fase 52,
  `phi0=0.30`, `kappa=1.5` dalle Fasi 39/44, `sharpen_1x2=True` dalla Fase 51.
  Bundesliga e Ligue 1 hanno voce esplicita dalla Fase 101, neutra e
  **misurata**: router θ negativo su 0/25 mercati in entrambe.)*

**Conseguenza per questo quaderno:** la frase «ogni affinamento Serie A va
tenuto SPENTO» del §4 non è più una raccomandazione da ricordare a mano — è lo
stato del codice, e un test verifica che `MARKET_ENGINE` e `LEAGUE_CONFIGS`
elenchino le stesse leghe. Il residuo «rendere per-lega il θ del router» che
compariva nei prossimi passi del progetto è **chiuso**.

## 6-sexies · Fase 100: cosa cambia per Premier e Liga

La Fase 100 non è nata per queste due leghe — è l'audit a 5 leghe con
l'ingresso di Bundesliga e Ligue 1 — ma le ha **rimisurate tutte e due dentro
lo stesso apparato**, con protocolli spesso più severi di quelli originali.
Fonte integrale: `docs/audit_5_leghe/` (report 6, 9, 10, 11) e i JSON in
`docs/audit_5_leghe/numeri/`. Qui solo ciò che tocca PL/Liga.

### 1 · «θ decresce con la liquidità» è FALSIFICATA

Era la lezione della Fase 53, e stava in questo file come spiegazione del
perché la Premier non ha leve sfruttabili. Su 5 leghe non regge:

| | Serie A | Premier | La Liga | Bundesliga | Ligue 1 |
|---|--:|--:|--:|--:|--:|
| margine book (7 stagioni) | 4.87% | **4.27%** | 4.75% | 4.76% | **5.02%** |
| θ MLE (pooled, stesse stagioni) | 1.232 | 1.085 | 1.242 | 1.080 | 1.103 |

La Ligue 1 ha il margine **più alto** (book meno competitivo) e θ **basso**; la
Bundesliga ha margine da Serie A e θ da Premier. corr(θ, margine) = **+0.299**
sulle 5 leghe — segno *opposto* a quello previsto, e la correlazione di rango
fra margine mediano e θ MLE è **+0.10**: la liquidità **non predice** il θ.

Quello che regge al posto suo: **θ e deficit-pareggio sono la stessa cosa vista
da due angoli**, corr(θ, φ0) = **+0.755**. Le leghe si dividono in due famiglie
nette — «latine» θ ≈ 1.24 (Serie A, **La Liga**), dove la sotto-dispersione è
forte, e θ ≈ 1.08-1.10 (**Premier**, Bundesliga, Ligue 1) dove non lo è. La
Premier non è sola: ha due compagne di famiglia, e nessuna delle tre è la più
liquida.

### 2 · La φ35 sul path market-implied: nel rumore in tutte e 5 le leghe

Passo 5 del report 6 (parametri leave-one-season-out, 6 stagioni, mai
in-sample):

| lega | φ0 LOSO | 1X2 senza φ | 1X2 con φ | guadagno (CI95) | verdetto |
|---|---|--:|--:|--:|---|
| serie_a | 0.235 – 0.370 | 0.9642 | 0.9628 | +0.00135 [−0.0010, +0.0038] | nel rumore |
| **premier_league** | **0.000 – 0.026** | 0.9622 | 0.9623 | −0.00014 [−0.0003, +0.0000] | nel rumore |
| **la_liga** | **0.198 – 0.423** | 0.9688 | 0.9685 | +0.00031 [−0.0016, +0.0023] | nel rumore |

Il **segno** è quello giusto (Premier ≈ 0, Liga latina) e replica il quadro del
§6/§6-ter; ma su questo percorso la φ35 **non è conclusiva in nessuna lega,
Serie A compresa**. Non è una smentita della leva (nel progetto è documentata
su percorsi e finestre diversi): è la constatazione che con ~2.000 partite per
lega un guadagno atteso di 1-1.5 millesimi è **sotto la soglia di risoluzione**.
Chi vorrà promuoverla deve allargare la finestra o cambiare metrica, non
ri-fittare gli stessi dati.

### 3 · Perché il beat-the-close è solo Serie A: servono DUE ingredienti

La scomposizione della correzione dei livelli in **tilt** (parte asimmetrica,
bias-casa, a scala invariata) e **scala** (parte simmetrica) è il risultato più
utile del blocco, e spiega finalmente il «no» di Premier e Liga:

| lega | θ MLE | **tilt** | **scala** | dp solo | tilt solo | dp+tilt |
|---|--:|--:|--:|--:|--:|--:|
| **serie_a** | **1.232** | **−0.0270** | −0.0006 | −0.0010 | +0.0002 | **−0.0020 ✓** |
| **la_liga** | 1.242 | **+0.0023** | −0.0042 | −0.0012 | +0.0007 | −0.0010 |
| **premier** | 1.085 | **−0.0164** | −0.0074 | +0.0002 | +0.0009 | +0.0009 |

Serve **l'interazione** di θ ≈ 1.23 *e* tilt ≈ −0.027: da soli, in Serie A, θ
dà −0.0010 (non conclusivo) e il tilt +0.0002 (nulla); insieme −0.0020
(conclusivo, 7/7 stagioni). La **Liga ha il θ ma non il tilt** (+0.0023, segno
sbagliato); la **Premier ha il tilt ma non il θ**. Ognuna ha metà della ricetta,
e mezza ricetta non cucina niente.

Test primario `dp_lvl` vs chiusura devigata (Δ > 0 = la chiusura è migliore,
selettore leave-one-season-out): **Premier +0.0010 [−0.0001, +0.0022], 3/7
stagioni; La Liga −0.0010 [−0.0022, +0.0003], 5/7** — entrambe **nel rumore**,
contro il −0.0020 [−0.0036, −0.0003] della Serie A (7/7). E il ROI a quote di
chiusura reali, strategia EV>0, walk-forward: **Premier −8,11% [−19,50%,
+3,90%] su 969 scommesse**, contro un −5,36% del «puntare TUTTO» — cioè seguire
i value bet non è meglio che scommettere alla cieca.

### 4 · Il GG/NG contro le quote VERE — la premessa cade, il tetto c'è

Le quote di chiusura GG/NG (1xBet via footiqo, 2017-20) hanno reso misurabile
ciò che il progetto dichiarava non misurabile. Su **Premier 1.102** e
**La Liga 1.139** partite appaiate (JSON `ggng_contro_quote.json`,
`D1_per_lega`):

| lega | log-loss del book | baseline in-sample | p medio del book | frequenza reale GG |
|---|--:|--:|--:|--:|
| premier_league | **0.6868** | 0.6926 | 0.5264 | 0.5082 |
| la_liga | **0.6835** | 0.6922 | 0.5174 | 0.4943 |
| *(pool 5 leghe)* | *0.6840* | *0.6921* | — | *0.5233* |

Sul pool il mercato GG/NG **è informativo** (Δ −0.00814, CI [−0.01164,
−0.00464]) ma vale **un terzo** dell'O/U 2.5 dello stesso book e costa 1,7 punti
di margine in più. Il nostro miglior prezzo lo **pareggia** (6 varianti su 6 con
CI a cavallo dello zero) e il **DC perde di netto** (+0.01036 [+0.00632,
+0.01454]; encompassing α\*=0.060, con α\*=0 nel 70% dei fit → il book lo
ingloba, come sull'1X2 alla Fase 16).

Due cose per queste due leghe in particolare:

- **il bias di livello del book ha segno per-lega**: la Liga **sovra**-prezza il
  GG di **+2,3 punti** (0.5174 contro 0.4943), la Premier di **+1,8**
  (0.5264 contro 0.5082), mentre la Serie A lo **sotto**-prezza di 1,3. È la
  stessa lezione del draw-bias: il segno non è universale;
- **nessuna leva GG/NG paga contro il giudice esterno**, su nessuno dei due
  fronti del §1.9: la ricalibrazione-μ dà premier +0.00025 e la_liga −0.00017
  (nessun CI conclusivo), la φ(|λ−μ|) è nel rumore, la ricalibrazione Platt del
  prezzo del book **peggiora con CI conclusivo** sul fronte per-lega. E il
  vantaggio (minuscolo) del nostro prezzo sul book **cambia segno fra leghe**
  — Δ vs book, con Δ<0 = il nostro prezzo nominalmente meglio: premier
  −0.00034, la_liga −0.00129, ma Serie A **+0.00138**. Un effetto che non regge
  il cambio di lega non è un effetto.

Perimetro da dichiarare per intero: vale per **un book**, **tre stagioni** e con
una soglia di risoluzione di 1,3 millesimi. Non dimostra che il GG/NG di *tutto
il mercato* sia efficiente; dimostra che il GG/NG di 1xBet nel 2017-20 non è
battuto da niente di ciò che abbiamo. Il valore residuo resta quello dichiarato
altrove: **prezzarlo calibrato dove il book non lo quota**, non batterlo dove
lo quota.

### 5 · Le covariate: `rest_full` è rumore su 5 leghe su 5

La bocciatura del §6 (test B) è stata estesa: sul path DC standalone le sei
covariate (rest, midweek, midweek **ricostruito col dato di coppa corretto**,
squad_value, absence) danno **12 Δ su 14 peggiorativi** in Bundesliga e
Ligue 1, e `rest_full` è ora rumore su **5 leghe su 5**. Il dato migliore non
salva la covariata: il confronto diretto fra `midweek_europe` bucato e corretto
dà +0.000048 e −0.000094, entrambi con CI che contengono lo zero. La lezione che
ne esce vale anche per la Premier, la lega più congestionata: **misurare bene la
congestione non la fa funzionare** — il fit pesato nel tempo assorbe già
l'effetto, e il difetto del dato non era la ragione del fallimento.

Corollario da mettere agli atti, dal caso `squad_value`: **la stabilità del
segno di un β non è evidenza di valore predittivo incrementale** (6/6 stagioni
dello stesso segno, β +0.056 e +0.095, e la covariata peggiora comunque).

### 6 · Devig di Shin: conclusivo in Liga, nel rumore in Premier

Quarta e quinta replica del confronto Shin vs moltiplicativo, ora su 5 leghe e
12.459 partite. Sul pool: log-loss 1X2 −0.00034 [−0.00068, +0.0000] (p=0.052,
nel rumore); Brier −0.00021 [−0.00039, −0.00001] conclusivo **ma il CI tocca lo
zero se il bootstrap è a cluster di lega** [−0.000414, −0.0000008]. Per lega,
ΔBrier: la_liga **−0.00054**, serie_a −0.00038, ligue_1 −0.00009,
**premier_league +0.00002**, bundesliga +0.00003 — migliorano 3 leghe su 5, e
sono le latine. Nel lavoro sul beat-the-close Shin batte il moltiplicativo con
**CI conclusivo in La Liga su entrambi i protocolli** (−0.0008 LOSO, −0.0009
LFO) ed è nel rumore in Premier.

**Lettura onesta:** Shin è *probabilmente* un filo meglio, e **nelle leghe
latine lo è in modo conclusivo**; ma il pooled non regge a un bootstrap che
rispetti la struttura dei dati e il log-loss — la metrica ufficiale — resta a
p=0.052. Non basta per toccare la fonte unica delle metriche (leva D del §5).

### 7 · Il resto, in breve

- **Ri-taratura**: curve piatte **5 leghe su 5** (emivita 730 peggiora ovunque,
  shrinkage e δ nel rumore). Gli iperparametri del DC sono di fatto **generali**;
  i δ per-lega restano adottati per motivazione strutturale, dichiarando che il
  guadagno misurato è nel rumore.
- **Motore**: market-implied batte il DC-da-gol su **14/15** mercati in Premier
  e **15/15** in Liga (contro 14/15 in Serie A). L'unico mercato dove vince la
  baseline è, in ogni lega, il **pari/dispari**: sesta replica.
- **Fronte generale (§1.9)**: per-lega vs pooled resta **non deciso** su tutte e
  cinque le leve testate; il conteggio di celle che sembrava premiare il pooled
  (73-8, e il denominatore giusto dà 59-8: 4 dei 25 mercati sono complementi
  esatti di altri 4) **esce identico da leghe rimescolate a caso** — misurava
  solo che il selettore pooled ha quattro volte più dati di selezione. Da
  rifare con selettore walk-forward.
- **Power-devig**: bocciato anche fuori dalla Serie A (in Bundesliga peggiora
  con CI conclusivo).

## 7 · Prossimi passi / dati che sbloccherebbero altro

1. ~~**Handicap asiatico** come terzo vincolo d'inversione~~ — **CHIUSO
   NEGATIVO (Fase 86)**: l'AH correla **0.9952** con λ−μ già ricavata da
   1X2+O/U, quindi non porta informazione nuova. Resta valido come **benchmark**
   Tier 2 (Fase 88: **pareggio in Brier** col mercato sharp — Brier del router
   0.2040 contro 0.2041, 7.437 partite × 3 leghe; ΔBrier −0.000136 [−0.000362,
   +0.000083]. *(La validazione del listino della Fase 98 dà 0.2044 vs 0.2044 su
   un campione diverso, n=6.839: due run, non una contraddizione.)*
   ⚠️ **Rettifica Fase 101**: l'affermazione «α\*=0 su un mercato NUOVO» non era
   mai stata calcolata; rifatta sugli stessi 7.437 casi dà **α\* ≈ +1.08**, con
   IC95 che **esclude** lo zero — il router è una *traduzione* delle stesse quote
   1X2+O/U, non un previsore indipendente, quindi lì l'encompassing non ha il
   significato che ha nella F16. La conclusione onesta resta «pareggio in
   Brier».)
2. **Chiusura O/U 2017-19** (PISTE #19): lo stesso buco riguarda **tutte e 5**
   le leghe, e la caccia al dato vero è **CHIUSA (Fase 100)**. Il dato esiste
   (1xBet via footiqo, `data/ricerca_esterna/`) ma **non è stato inserito**: è
   un solo book e come proxy della media multi-book è peggiore della stima
   (MAE 0.0156 contro 0.012). Le vie alternative sono chiuse per verifica
   diretta: football-data non pubblica la chiusura prima del 2019-20,
   BetExplorer l'ha ritirata, OddsPortal è escluso dal proprio `robots.txt`.
   Resta in piedi la stima E3 pooled a 5 leghe (§1).
3. **Paper-trading draw-bias**: SOLO Serie A (e forse Liga); su PL il segno è
   opposto — ogni strategia-pareggio va tenuta lontana dalla Premier. *(La F100
   aggiunge che il ROI pari-equilibrio non è conclusivo in **nessuna** delle 5
   leghe, Liga +1.90% compresa: è un'idea da testare in avanti, non un edge
   misurato.)*
4. **Seconde serie** (PISTE #12): il prior δ individualizzato vale doppio in
   Premier, dove δ=0.33 è il più grande delle 5 leghe e le promosse più
   eterogenee (Championship: da Luton a Leicester).
5. **Le caselle rimaste aperte su queste due leghe** (dalla Fase 100, che le ha
   misurate su Bundesliga/Ligue 1 e non su PL/Liga):
   - il **test di forma con potenza** sulla calibrazione (pendenza b della
     ricalibrazione logistica) — fatto su BL, L1 e Serie A, mai su PL/Liga
     (§6-quater, riquadro);
   - **Tier 2 e Tier 3** (handicap asiatico, Halftime, Second Half, risultato
     esatto) sono coperti e validati **sulle 3 leghe storiche**, quindi anche su
     Premier e Liga; restano scoperti ovunque **HT/FT congiunto, le
     combinazioni e il live**;
   - la **conferma su stagioni nuove** (2026-27+) delle due voci di panchina
     della Liga (θ≈1.2 del router, φ35-sola sul GG): è l'unica condizione di
     promozione rimasta, ora che il tool è per-lega (§6-quinquies).
