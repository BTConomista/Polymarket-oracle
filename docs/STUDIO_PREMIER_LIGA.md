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
| A | **φ35 per-lega** (equilibrio-pareggio, path DC) | unica cella ⬜ del motore titolare; EDA 3a: il deficit-modello può esserci anche dove il mercato non sbaglia; su PL possibile φ0≈0 (il fit stesso è la risposta) | **Fase 79, fatto — vedi §6** |
| B | **covariate congestione** rest_full/midweek | colonne pronte (F59), mai testate fuori SA; PL la lega più esposta (3a); in SA erano rumore | **Fase 79, fatto — vedi §6** |
| C | GG/NG φ35+knee34 sul market-implied per-lega | panchina #1: la promozione è condizionata proprio al "riappare su PL/Liga"; il GG/NG è il mercato senza tetto dimostrato | da fare (dopo A: riusa la φ per-lega) |
| D | Devig di Shin per-lega nel motore | direzione già confermata 3/3 leghe (F53); è candidato GENERALE, costo = migrazione fonte unica | in attesa (decisione di progetto, non di lega) |
| E | Ricalibrazione w_D/w_A per-lega della chiusura | segno OPPOSTO tra PL e SA/Liga (F53 + EDA 3a): mai pooled, solo per-lega; servono più stagioni | raccolta prospettica |
| F | γ dinamico per la Premier | EDA 3c: γ_t Premier volatile; ma architettura chiusa in SA (F47/48) | condizionale (solo con un meccanismo nuovo) |

Regole invariate: una leva alla volta, CI95<0 per adottare, run in
`runs.jsonl`, aspettativa dichiarata PRIMA del test.

## 6 · Risultati dei test per-lega (Fase 79)

*(compilato al completamento del run `fase79_leve_per_lega`)*

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
