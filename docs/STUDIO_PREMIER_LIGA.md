# Studio dedicato — Premier League e La Liga

Il repo è nato ed è cresciuto sulla Serie A (Fasi 0-52); Premier e Liga sono
entrate nelle Fasi 53-57 e sono state validate "in blocco" (tracer, ri-taratura,
market-implied multi-mercato). Questo file è il **quaderno di studio dedicato**
alle due leghe: cosa sappiamo dei loro dati, in cosa differiscono dalla Serie A,
quali leve sono state testate per-lega e con che esito, e il **piano ragionato**
dei prossimi test. Va aggiornato a ogni fase che tocca Premier/Liga (stessa
regola del CLAUDE.md §2: le decisioni nel DIARIO, i run in `runs.jsonl`, qui la
**visione d'insieme per-lega**).

Ultimo aggiornamento: **Fase 79**.

---

## 1 · I dati che abbiamo (identici alla Serie A, per costruzione)

Snapshot congelati `data/{premier_league,la_liga}_matches.csv` (Fase 54, bundle
utente in `files/` + `scripts/build_league_snapshot.py`), **stesso schema** della
Serie A, 9 stagioni 2017-18 → 2025-26, 3.420 partite per lega:

| blocco dati | copertura PL | copertura Liga | note |
|---|--:|--:|---|
| risultati + 1X2 chiusura | 100% | 100% | chiusura = solo colonne `*C*` genuine (Fase 73) |
| 1X2 apertura | 100% | 100% | Pinnacle pre-match (`PS*`) preferito |
| O/U 2.5 chiusura | 77.8% | 77.8% | **manca 2017-19** (buco Fase 73, identico SA); stima E3 in `data/estimates/` |
| O/U 2.5 apertura | 100% | 100% | `BbAv` riclassificata apertura reale (Fase 73) |
| xG/npxG/PPDA/deep (Understat) | 100% | 100% | riconciliazione nomi verificata per identità (Fase 54) |
| squad_value | 100% | 100% | fonte player-scores + 13 celle Transfermarkt reali (Fase 70) |
| assenze (stima) | 100% | 100% | stessa fonte terza della Serie A |
| congestione vera (`rest_days_full`, `midweek_europe`) | 100% | 100% | calendari coppe/Europa (Fase 59) — **mai testata come covariata fuori SA** |
| GG/NG quotato | 0% | 0% | come SA: football-data non lo fornisce (mercato "libero") |

Config ufficiale per-lega (`src/config.py`, Fase 57): identica alla Serie A
tranne il prior neopromosse — **δ Premier 0.33, δ Liga 0.22** (ricalcolati dai
gol delle rispettive promosse, §2-bis). γ (vantaggio-casa) auto-fittato dal DC.

## 2 · Cosa sappiamo già (sintesi delle fasi cross-lega)

| fase | esito in una riga |
|---|---|
| 53 (tracer market-side) | θ>1 ovunque ma decresce con la liquidità (PL 1.07 < Liga 1.10 < SA 1.21); **dp_lvl non batte la chiusura fuori SA**; draw-bias NON si replica in PL (pareggi SOVRA-prezzati, w_D=0.93), mezza replica in Liga |
| 55 (EDA) | Liga la più "casalinga" (γ 0.272), PL più gol e più dispersione; δ promosse PL 0.33 ≫ SA/Liga; mercato PL il più liquido (margine 4.3%) |
| 56 (tracer DC) | il DC Serie A non ritarato batte la baseline su entrambe; gap col mercato: PL +0.0207 > SA +0.0165 ≈ Liga +0.0162 |
| 57 (ri-taratura) | iperparametri PIATTI (emivita 730 peggiora ovunque); adottato solo δ per-lega; **il gap è informazione, non calibrazione** |
| 59-60 | colmati i gap dati: congestione vera, squad_value, assenze anche PL/Liga |
| 75 (apertura 2017-19) | market-implied dall'apertura: 17/20 mercati, trans-epoca e trans-lega; θ cresce nel tempo (per-contesto) |
| 76 (chiusura 2019-26) | market-implied batte il DC-da-gol su **13/14 mercati su tutte e 3 le leghe**, senza ritarare ρ=−0.06: la MATRICE è universale |

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
triplo di esposizione (test B).

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

La tabella-sintesi di TUTTO ciò che è stato misurato finora sulle tre leghe
(fonte tra parentesi). È la mappa per ragionare sui prossimi modelli: dove la
colonna è uniforme il fenomeno è "del calcio" (versione generale possibile,
principio §1.9); dove diverge è per-lega (mai copiare i numeri, §7).

| dimensione | Serie A | Premier | La Liga | universale? |
|---|--:|--:|--:|:--|
| γ vantaggio-casa (F55) | 0.150 | 0.185 | **0.272** | ❌ per-lega (auto-fittato dal DC) |
| γ_t stabilità (F79-EDA) | in calo | **volatile** (0.01 COVID, 0.06 nel 2425) | **alto e stabile** | ❌ |
| pareggi % (F55) | 26.0% | **23.4%** | 26.5% | ❌ la "firma inglese" |
| δ neopromosse (F55/57) | 0.23 | **0.33** | 0.22 | ❌ per-lega (in config) |
| gol/partita · Over% (F55) | 2.72 · 52% | **2.84 · 54%** | **2.58 · 47%** | ❌ |
| Var/Media gol (F55) | 1.06 | **1.11** | 1.05 | ❌ |
| corr xG-gol (F55) | 0.61 | 0.64 | 0.62 | ✅ xG di pari qualità |
| emivita/shrinkage/α ottimi (F57) | 365/1.5/0.75 | uguali | uguali | ✅ **iperparametri DC generali** |
| margine book (F55) | 4.9% | **4.3%** | 4.8% | ❌ liquidità crescente PL |
| gap DC vs mercato (F56) | +0.0165 | **+0.0207** | +0.0162 | ~ stesso ordine; peggio dove il book è più liquido |
| θ sotto-dispersione MLE (F53) | **1.21** | 1.07 | 1.10 | ❌ decresce con la liquidità |
| θ OPERATIVO del router (F81, da griglia+lfo) | ⚽ 1.225 | **1.0 (liscio)** | **~1.2 (ribalta F53!)** | ❌ ma SA≈Liga: le latine convergono |
| dp_lvl batte la chiusura (F52/53) | **sì (CI)** | no | no | ❌ idiosincrasia SA |
| draw-bias mercato equilibrate (F79-EDA) | **+0.032** | **−0.009 (opposto)** | +0.022 | ❌ segno NON universale |
| deficit-pareggio del DC: φ0 fittato (F35/79) | 0.39 | **0.00 (bound)** | 0.39 | ❌ tratto LATINO, assente in PL |
| ROI pari-equilibrio (F40/53) | +4.7% (P83) | **−5.4%** | +3.6% (P81) | ❌ mai giocare il pari in PL |
| congestione riposo ≤3g (F79-EDA) | 14% | **22% (36% a dic.)** | 18% | ❌ ma covariata = rumore su 3/3 (F79) |
| profilo fine-stagione tasso-ospite (F80) | ~1.0 (adattivo) | **×1.10 (boost)** | **×0.915 (CALO)** | ❌ segno opposto: in Liga il vantaggio-casa non crolla nel finale |
| catena GG/NG migliore (F50/80) | φ35+k34 (P 97%) | **liscio** (nulla paga) | **φ35 sola (CI<0, P 99%)** | ❌ stessa cassetta degli attrezzi, assemblaggio per-lega |
| calibrazione del mercato (F82) | tilt casa/pari ±0.02 | **quasi perfetta** (ECE fino a 0.003) | GG −0.036 (raddrizzato dal router θ) | ❌ le mis-calibrazioni sono i bias per-lega noti |
| hit-rate 1X2 modello (F82) | 54.2% (=mercato) | 55.3% (=mercato) | 54.3% (=mercato) | ✅ si indovina quanto il mercato, ovunque |
| market-implied multi-mercato (F76) | 13/14 | 13/14 | 13/14 | ✅ **il motore è universale** (ρ=−0.06 unico) |
| pari/dispari imprevedibile (F26/75/76) | sì | sì | sì | ✅ irriducibile ovunque |

**Sintesi in tre righe.** (1) Tutto ciò che è *struttura* (matrice DC,
market-implied, iperparametri del fit, xG) trasferisce così com'è. (2) Tutto
ciò che è *livello* (γ, δ, gol, θ) è per-lega ma o è auto-fittato o è già in
config. (3) Tutto ciò che è *bias sfruttabile* (draw-bias, sotto-dispersione,
dp_lvl) è idiosincratico — e la Premier, il mercato più liquido, non ne ha
nessuno: è la lega dove il book sbaglia meno e il modello serve solo a
prezzare i mercati non quotati.

## 4 · Ragionamento: quali modelli/valori usare oggi su PL/Liga

Stato per-mercato (dalla rosa PANCHINA.md, dopo la Fase 76):

- **Con quote 1X2+O/U** (il caso d'uso principale): **market-implied puro**,
  ρ=−0.06, per TUTTI i mercati sui gol — su PL/Liga **senza** router θ (F53:
  non paga), **senza** dp_lvl (F53: bocciato), e — finché il test A non dice
  altro — **senza** φ35 famiglia-pareggio (mai validata lì).
  In pratica: su PL/Liga oggi il listino si prezza con la matrice
  market-implied *liscia*; ogni affinamento Serie A va tenuto SPENTO.
- **Senza quote** (fallback): DC + blend xG con `LEAGUE_CONFIGS` (δ 0.33/0.22).
- **Stime dati mancanti**: E3 pooled per la chiusura O/U 2017-19 (vale per le
  3 leghe, F62-bis), stimatore squad_value ibrido (F66).

## 5 · Piano dei test per-lega (in ordine di costo/beneficio)

| # | leva | perché / aspettativa onesta | stato |
|---|---|---|---|
| A | **φ35 per-lega** (equilibrio-pareggio, path DC) | unica cella ⬜ del motore titolare; EDA 3a: il deficit-modello può esserci anche dove il mercato non sbaglia; su PL possibile φ0≈0 (il fit stesso è la risposta) | ❌ **bocciata su entrambe (F79, §6)** |
| B | **covariate congestione** rest_full/midweek | colonne pronte (F59), mai testate fuori SA; PL la lega più esposta (3a); in SA erano rumore | ❌ **rumore ovunque (F79, §6)** |
| C | GG/NG φ35+knee34 sul market-implied per-lega | panchina #1: la promozione è condizionata proprio al "riappare su PL/Liga"; il GG/NG è il mercato senza tetto dimostrato; **dopo la F79 il prior su PL è sfavorevole** (φ0→0), su Liga plausibile | ✅ **fatto (F80, §6-bis): Liga φ35 CI<0; PL nulla; k34 solo-SA** |
| D | Devig di Shin per-lega nel motore | direzione già confermata 3/3 leghe (F53); è candidato GENERALE, costo = migrazione fonte unica | in attesa (decisione di progetto, non di lega) |
| E | Ricalibrazione w_D/w_A per-lega della chiusura | segno OPPOSTO tra PL e SA/Liga (F53 + EDA 3a): mai pooled, solo per-lega; servono più stagioni | raccolta prospettica |
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
in **panchina alta**, si promuove in config quando riappare su stagioni nuove
(2026-27+) o quando `predict.py` diventa per-lega (debito Fase 78).

## 6-ter · Il mega-sweep delle costanti (Fase 81) — le curve di risposta per lega

Run `fase81_mega_sweep_mi` (12) + `fase81_joint_rho_theta` (2): ~70 varianti
per lega (ρ×11 con ri-inversione, θ×10, φ0×κ×31, knee×5) su 6 mercati, con il
**selettore walk-forward "lfo"** come guardia di onestà (sceglie la costante
solo dal passato). Dettaglio nel [DIARIO, Fase 81](DIARIO.md).

**Le costanti operative del motore, lega per lega (stato dopo la F81):**

| costante | Serie A | Premier | La Liga |
|---|---|---|---|
| ρ | −0.06 (universale, confermato dal check congiunto) | −0.06 | −0.06 |
| θ router | ⚽ 1.225 (riconf.: cs −0.0078 lfo CI<0) | ❌ 1.0 — la curva è piatta | 🪑 **~1.2** (cs −0.0069*, 1X2 −0.0023*, GG −0.0025*, lfo CI<0 — **ribalta la F53**) |
| φ pareggio/GG | ⚽ router (F41/44) | ❌ 0 su tutta la griglia | 🪑 (0.7, 0.5): GG lfo −0.0019* |
| nudge-μ | 🪑 k34 solo GG (−0.0012*) | ❌ none | ❌ none (profilo invertito) |

**Le tre lezioni della fase:**
1. **La Premier è già al suo ottimo su ogni asse** (valli centrate sul
   riferimento, ~70 varianti): il motore liscio non è un ripiego, è il
   modello giusto per il mercato più liquido.
2. **θ-da-mercati ≠ θ-da-punteggi**: la F53 bocciò il router-Liga col θ da
   MLE sui punteggi (1.097); l'ottimo sui MERCATI è ~1.2 — con quello il
   router paga anche in Liga. Le costanti operative si scelgono con
   griglia+selettore sui mercati, mai con la sola verosimiglianza.
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

## 7 · Prossimi passi / dati che sbloccherebbero altro

1. **Handicap asiatico** (PISTE #5): terzo vincolo d'inversione, presente nei
   grezzi PL/Liga 2019+ come in SA — migliorerebbe il motore titolare su tutte
   e tre le leghe insieme.
2. **Chiusura O/U 2017-19** (PISTE #19): stesso buco su tutte e tre le leghe.
3. **Paper-trading draw-bias**: SOLO Serie A (e forse Liga); su PL il segno è
   opposto — ogni strategia-pareggio va tenuta lontana dalla Premier.
4. **Seconde serie** (PISTE #12): il prior δ individualizzato vale doppio in
   Premier, dove δ=0.33 è il più grande e le promosse più eterogenee
   (Championship: da Luton a Leicester).
