# Test prospettico — giornata 1, stagione 2026-27 (5 leghe: Serie A, Premier, La Liga, Bundesliga, Ligue 1)

> **Stato: APERTO — ma il congelamento è FATTO (01/08/2026).** Le previsioni
> del **Modello 1** delle **48 partite** della giornata 1 di tutte e 5 le leghe
> sono congelate in `experiments/prospettico_2026_27_m1.csv` (26 mercati Tier 1
> per partita), con lo **scoring già scritto** e i **criteri pre-registrati**
> — tutto **due settimane prima** del primo calcio d'inizio. Resta da fare:
> il **Modello 2** dalle quote di chiusura (si esegue a ridosso del fischio) e
> lo **scoring** a risultati acquisiti. Lo stato passo per passo è in **§5.1**.
>
> ⚠️ Il §2 qui sotto è l'**anteprima illustrativa** del 2026-07-23 — 7 partite
> Premier *plausibili*, non ufficiali. Resta come documento storico e **non si
> riscrive**: le previsioni vere sono quelle del CSV, non quelle della tabella.
>
> ⚠️ **Allargato a 5 leghe all'audit della Fase 101.** Il documento nasceva a 3
> leghe perché Bundesliga e Ligue 1 non erano ancora in produzione; ora lo sono
> (16.111 partite, `LEAGUE_CONFIGS` e `MARKET_ENGINE` complete), quindi non c'è
> ragione di lasciarle fuori dal gold standard. L'anteprima illustrativa del §2
> resta com'era — è congelata e non si riscrive, e di fatto copre la **sola
> Premier** (Serie A e La Liga erano slot vuoti già a 3 leghe) — ma il
> **protocollo del §3 e la checklist del §5 valgono per tutte e cinque**.
>
> **Le date di inizio** (fonte unica: `newseason.md` §1, `start_date` degli
> eventi outright Smarkets scaricati il 25/07/2026, da riverificare a inizio
> agosto): **La Liga 16 agosto**, **Premier e Ligue 1 21 agosto**, **Serie A 22
> agosto**, **Bundesliga 28 agosto**. La scadenza vera del congelamento è quindi
> il **16 agosto**.

## 1 · Perché questo test

È il **gold standard** della validazione: si congelano le previsioni **prima**
del calcio d'inizio e si controllano **dopo**. Nessun senno di poi è possibile —
a differenza di ogni backtest (dove i dati passati sono già noti). Il progetto
insegue dati prospettici dalla Fase 14; ora che il motore market-implied è
validato su ogni asse — **5 leghe**, apertura e chiusura, 2017-2026 (Fasi
26/75/76 sulle 3 storiche, dove batte il DC-da-gol su 13/14 mercati; **15/15**
nelle due nuove; **25/25** partendo dall'apertura) — ha senso puntarlo su
partite **davvero mai viste**: la prossima stagione.

L'idea: al primo turno 2026-27, per ogni partita, produrre **due** previsioni —
il Dixon-Coles da solo (Modello 1) e il market-implied dalle quote di chiusura
reali (Modello 2) — e, a risultati acquisiti, **scorarle** (log-loss, Brier) per
lega e per mercato, controllando anche la **calibrazione** (le probabilità
dichiarate corrispondono alle frequenze reali?).

## 2 · Anteprima illustrativa (congelata 2026-07-23) — SOLO Modello 1 (DC)

> ⚠️ **Due delle premesse di questo paragrafo sono CADUTE** (verificato il
> 27/07/2026, audit di questa sessione — stesso riquadro del §4). Il testo
> resta com'era — è
> un'anteprima **congelata** il 2026-07-23 e non si riscrive a posteriori — ma
> va letto sapendo che:
> - **`WebFetch` non è più bloccato**: la rete è tornata raggiungibile alla
>   Fase 100 (200 da football-data.co.uk, understat, transfermarkt, Kaggle,
>   footiqo, `gamma-api.polymarket.com`, `api.smarkets.com`; e in questa
>   sessione anche huggingface e jsdelivr). Vedi il riquadro del §4 e
>   `docs/MANUALE_SOPRAVVIVENZA.md` §1. **I calendari ufficiali 2026-27 sono
>   quindi recuperabili**: non è più un vincolo, è un compito (§5);
> - **le quote NON sono più tutte irraggiungibili**: gli **outright** si
>   prendono da Polymarket e Smarkets (le previsioni outright 2026-27 sono
>   infatti **già congelate**, `prospettico_2026_27_outright.json`, 2026-07-25).
>   Resta vero il pezzo che serve al Modello 2: le quote **1X2 + O/U di singola
>   partita** non hanno ancora un canale verificato — è la casella aperta del
>   §5, non un fatto acquisito.

⚠️ **Non è il test scorato.** È ciò che si può produrre *oggi* dalla sessione di
sviluppo, con questi limiti **dichiarati**:
- ~~i **calendari** 2026-27 non sono verificabili in modo affidabile da qui
  (`WebFetch` bloccato; gli snippet di ricerca su stagioni future sono
  speculativi — mescolavano squadre di Championship)~~ **premessa caduta, vedi
  il riquadro sopra**: le partite qui sotto restano comunque **plausibili, non
  ufficiali**, perché nessuno ha ancora verificato i fixture veri;
- i **dati si fermano a 2025-26** → le forze delle squadre sono "vecchie" di
  un'estate di mercato (nuovi acquisti/cessioni non pesati);
- ~~**niente quote** raggiungibili da qui~~ → **niente Modello 2**
  (market-implied) *in questa anteprima*: al 2026-07-23 non c'erano quote 1X2/OU
  per-partita in mano. Solo il DC-da-solo;
- l'anteprima è generata con la **config giusta per lega** (`LEAGUE_CONFIGS`,
  δ Premier 0.33) via `scripts/_run_prospettico_2627.py`. **Da Fase 83-bis anche
  `predict.py` è per-lega** (`--league premier_league` usa δ=0.33 ecc.): il
  "passo 2" del Modello 1 è chiuso, il tool ufficiale può ora produrre M1 per
  ogni lega. ~~Resta per-contesto solo il θ del router nel path market-implied
  (M2): per Premier il M2 andrà prodotto con `dp_theta` neutro.~~ **Chiuso dalla
  Fase 92-bis**: anche il M2 è per-lega, `predict.py --league <lega>` prende
  θ/φ0/κ/sharpen da `src.config.MARKET_ENGINE` — nessun passo manuale.

**Premier League — previsione DC (as_of 2026-08-15, dati fino a 2025-26):**

| partita | 1 | X | 2 | Over 2.5 | GG |
|---|--:|--:|--:|--:|--:|
| Newcastle–Liverpool | 34.1% | 26.5% | 39.5% | 64.0% | 68.1% |
| Man City–Bournemouth | 65.1% | 20.9% | 14.0% | 61.7% | 57.7% |
| Brighton–Aston Villa | 41.3% | 28.1% | 30.6% | 54.2% | 60.4% |
| Fulham–Chelsea | 33.5% | 29.5% | 37.0% | 52.1% | 59.2% |
| Brentford–Tottenham | 48.6% | 25.3% | 26.1% | 61.1% | 64.4% |
| Everton–Crystal Palace | 38.9% | 31.4% | 29.7% | 41.4% | 50.5% |
| Nott'm Forest–Leeds | 45.1% | 28.0% | 26.9% | 51.0% | 57.1% |

Dati grezzi (λ,μ e tutti i mercati): `experiments/prospettico_2026_27_dc.csv`.
Serie A e La Liga: calendari non reperiti in modo affidabile → **slot vuoti**,
da riempire coi fixture ufficiali (§5).

**Come leggerla, onestamente.** Sono previsioni *ragionevoli* di un modello che
non ha ancora visto il mercato 2026-27 né i trasferimenti estivi. Ci si aspetta
che il DC-da-solo sia **battuto dal mercato** (α\*=0, dimostrato ovunque): il
valore del test non è "vincere", è **misurare quanto** perde e se resta ben
calibrato su dati mai visti — e, quando ci saranno le quote, mostrare che il
market-implied riproduce il mercato ed estende ai mercati non quotati.

## 3 · Il protocollo del test VERO (da eseguire vicino al calcio d'inizio)

Per ciascuna delle **5** leghe, giornata 1:
1. **Fixture ufficiali** (fonte: lega/Wikipedia, verificati).
2. **Modello 1 — DC**: `scripts/_run_prospettico_2627.py` oppure, ora che è
   per-lega, `predict.py --league <lega>` (config δ/γ giusta), congelato PRIMA
   del kickoff.
3. **Modello 2 — market-implied**: raccogliere le **quote di chiusura** reali
   (1X2 + O/U 2.5) di ogni match e invertirle (`predict.py --odds …` /
   `price_markets`). Da fare vicino al calcio d'inizio. **Nessun passo manuale**:
   dalla Fase 92-bis `predict.py --league <lega>` prende θ/φ0/κ/sharpen da
   `src.config.MARKET_ENGINE` — motore con θ=1.225 per la Serie A, **liscio**
   (θ neutro, φ0=0) per Premier, Liga, Bundesliga e Ligue 1.
4. **Baseline**: frequenza storica dell'esito (già nota) per riferimento.
5. **Dopo il full-time**: risultati reali → log-loss/Brier per mercato e per
   lega, di Modello 1, Modello 2 e baseline; controllo di calibrazione
   (reliability diagram). Registrare un run `source=prospettico_2627` in
   `runs.jsonl`. Aspettativa dichiarata: Modello 2 ≈ mercato; Modello 1 peggio;
   nessun edge di ROI (non si simula denaro — §CLAUDE.md).

## 4 · Vincoli ambientali (perché il test non si chiude in un colpo)

> ⚠️ **SUPERATA dalla Fase 100** (verificato 27/07/2026, audit di questa
> sessione): la rete **è tornata raggiungibile** — non è più vero che
> `WebFetch` sia bloccato del tutto. La Fase 100 ha recuperato realmente
> **3.045 righe di calendario coppe da Wikipedia via fetch**, e
> `gamma-api.polymarket.com` / `api.smarkets.com` sono raggiungibili e
> documentate come fonti di quote prospettiche reali fin dalla Fase 78/97
> (vedi `docs/MANUALE_SOPRAVVIVENZA.md` §1-bis/§2-bis e
> `scripts/fetch_polymarket_open.py` / `scripts/fetch_smarkets_outrights.py`
> per gli outright). Resta vero che quelle due API quotano **outright**, non
> le quote 1X2/O/U di singola partita che servono al Modello 2: per quelle
> resta da verificare un canale diretto (siti di quote 1X2/O/U bot-blocked,
> non ancora ritestati con la rete riaperta) — il paragrafo sotto descrive lo
> stato di **prima** della Fase 100, conservato come riferimento storico.

Dalla sessione di sviluppo cloud (stato **prima** della Fase 100): `WebFetch`
era bloccato del tutto (403 anche su Wikipedia, bug noto —
`docs/MANUALE_SOPRAVVIVENZA.md`); i siti di quote (oddschecker, ecc.)
bloccano i bot; gli snippet di ricerca non davano quote decimali pulite né
fixture affidabili di stagioni future. Quindi le **quote reali andavano
raccolte per un canale diverso** vicino al kickoff:
- **GitHub Actions** (runner con rete libera, pattern Fase 67), oppure
- una **sessione browser reale** (Cowork, pattern Fase 70),
- o inserite a mano dall'utente in un piccolo bundle in `files/`.

## 4-bis · Quanta POTENZA ha questo test (Fase 98) — il vincolo di disegno

Il calcolo è stato fatto sui dati veri (6.840 partite = 3 leghe × 6 stagioni ×
380, differenze appaiate per-partita, `scripts/_run_prospective_power.py`).
Controllo di validità superato: gap 1X2 pooled **+0.0179**, che riproduce il
**+0.0165** noto *(PRE-fix Fase 92; al codice di HEAD il gap 1X2 Serie A è
**+0.0167**, log-loss 0.9799 contro 0.9632 del mercato — la differenza non
cambia nulla nell'ordine di grandezza né nelle conclusioni sotto)*.

**Buona notizia**: le partite sono **indipendenti** — autocorrelazione di ordine
1 +0.007, ICC ≈ 0, **DEFF = 1.00**. Non c'è penalità da clustering (per giornata
o per stagione): ogni partita raccolta conta per una.

**Cattiva notizia**: il rapporto segnale/rumore è **1:8,5** (sd delle differenze
0.1527 contro un gap di 0.0179). Da cui:

| campione | potenza sul gap col mercato | verdetto |
|---|--:|---|
| **30 partite** (1 giornata × 3 leghe) | **9,8%** | MDE 0.0781 (= 4,4× il gap misurato +0.0179; 4,7× il +0.0165 di riferimento): **non conclude mai** |
| 380 (1 stagione, 1 lega) | 62,5% | sotto-dimensionato |
| **574** | **80%** | ≈ 19 giornate su 3 leghe |
| 1140 (1 stagione × 3 leghe) | 97,7% | il disegno giusto |

⚠️ **Questa tabella è calcolata su 3 leghe** (6.840 partite appaiate, Fase 98) e
**non è stata rifatta** dopo l'ingresso di Bundesliga e Ligue 1. Cambia solo il
rapporto giornate↔partite, non il segnale/rumore.

**L'aritmetica del rapporto, esplicita** (squadre verificate sugli snapshot,
stagione 2025-26: Serie A 20, Premier 20, La Liga 20, Bundesliga 18, Ligue 1 18):

```
partite per giornata, 3 leghe = 20/2 + 20/2 + 20/2                 = 30
partite per giornata, 5 leghe = 20/2 + 20/2 + 20/2 + 18/2 + 18/2   = 48
soglia 80%  -> 574 / 30 = 19,1 giornate (3 leghe)
            -> 574 / 48 = 12,0 giornate (5 leghe)
soglia baseline (184) -> 184 / 30 = 6,1 giornate | 184 / 48 = 3,8 giornate
1 stagione intera, 5 leghe = 380·3 + 306·2 = 1.752 partite (era 1.140 su 3)
```

Le **percentuali di potenza in colonna restano quelle misurate su 3 leghe**:
ri-calcolarle sulle 5 è un lavoro aperto (il gap pooled e la sd cambierebbero,
perché cambia il mix di leghe), **non un numero da dedurre a mente**.

Gerarchia netta fra i bersagli: contro la **baseline** bastano **184** partite
(6 giornate su 3 leghe, ~4 su 5); contro il **mercato** ne servono **574**
sull'1X2, **2.254** sul GG/NG, **2.988** sull'O/U 2.5.

*(Nota sul GG/NG: nella Fase 98 il riferimento del GG/NG era il **motore
market-implied**, non un mercato reale, perché nei dati non c'erano quote GG/NG.
Quella premessa è **caduta alla Fase 100** — le quote GG/NG di chiusura esistono
per il 2017-20, 1xBet via footiqo, 5.337 partite su 5 leghe — ma il numero qui
sopra resta quello misurato contro il market-implied e **non va riletto** come
«contro il book».)*

### 📐 Il modello in dettaglio — da dove escono questi numeri

Formule copiate riga per riga da `scripts/_run_prospective_power.py`
(`summarize`, `n_star`, `power_at`), test appaiato a due code al 5%:

```
d_i     = logloss_modello_i − logloss_riferimento_i        (differenza APPAIATA)
DEFF    = max(1, (SE_bootstrap_a_cluster / SE_iid)^2)      # cluster = giornata / stagione
sd_eff  = sd(d) · sqrt(DEFF)
SE(n)   = sd_eff / sqrt(n)
MDE(n)  = (z_0.975 + z_0.80) · SE(n) = 2.8016 · SE(n)
n*      = ( 2.8016 · sd_eff / |δ| )^2
potenza(n) = Φ(ncp − z_0.975) + Φ(−ncp − z_0.975),  ncp = |δ| · sqrt(n) / sd_eff
```

**Perché ogni numero vale quello che vale:**
- `z_0.975 = 1.9600` (due code al 5%) e `z_0.80 = 0.8416` (potenza 80%) sono le
  costanti del disegno, non scelte: **K = 2.8016** è la loro somma;
- `DEFF = 1.00` **non è un'assunzione**: è misurato (bootstrap a cluster su
  giornata e stagione), e coincide col fatto che acf1 = +0.007 e ICC ≈ 0. Quindi
  `sd_eff = sd(d) = 0.1527` — nessuna penalità da clustering;
- `δ = 0.0179` è il gap 1X2 pooled **misurato**, non un'ipotesi ottimistica;
- da cui `n* = (2.8016 · 0.1527 / 0.0179)² = 571` ≈ le **574** partite della
  tabella (la piccola differenza è l'arrotondamento di sd e δ a 4 decimali);
- `MDE(30) = 2.8016 · 0.1527 / √30 = 0.0781`, cioè **4,4×** il gap misurato:
  con una giornata l'unico effetto rilevabile sarebbe quattro volte più grande
  di quello che esiste davvero.

**Limite dichiarato**: la potenza assume che il gap resti **costante**. È una
stima **ottimistica** se il modello degrada o il mercato migliora — ed entrambe
le cose sono successe in passato (il θ del router cresce nel tempo, Fasi 75/81).

**Conseguenze operative su questo test:**

1. **la giornata 1 da sola non può concludere nulla** contro il mercato. Va
   trattata per quello che è: il **collaudo del protocollo** (fixture veri,
   quote reali, congelamento, scoring) — non la prova.
2. **il bersaglio realistico della giornata 1 è la baseline**, non il mercato:
   con 30 partite (48 su 5 leghe) nemmeno quella conclude (servono 184), ma la
   direzione è leggibile e i turni si accumulano in fretta — 4 giornate su 5
   leghe, 6 su 3.
3. **si scora l'1X2 per primo**: dà potenza **4-5×** prima di GG/NG e O/U.
   Riportare gli altri mercati va bene, ma dichiarando che sono
   sotto-dimensionati.
4. **il piano va esteso a ~19 giornate su 3 leghe — ~12 su 5** (≈ metà stagione
   o meno) per una prima conclusione onesta sul mercato, e a una stagione intera
   per il 97,7%. Cioè: questo file resta APERTO per mesi, per costruzione.
5. **l'outright NON è testabile qui**: servirebbero ~57 stagioni-lega, 3 leghe in
   una stagione danno **9,8%** di potenza (vedi Fase 98 e `docs/PISTE.md` §4-bis).
   Con 5 leghe si raccolgono 5 stagioni-lega l'anno invece di 3: cambia poco,
   resta **non testabile prospetticamente** — non «perdente».

---

## 5 · «DA RIPETERE / COMPLETARE PIÙ AVANTI» — checklist ESEGUIBILE

> 🔄 **Aggiornamento 01/08/2026 (Fase 127).** Due caselle di questo paragrafo
> sono chiuse e una data è cambiata.
>
> - **Canale quote per-partita: ✅ RISOLTO** (Fasi 115/116/118). Smarkets
>   espone 1X2 + O/U 2.5 + GG/NG delle 5 leghe, e
>   `.github/workflows/smarkets-prematch.yml` raccoglie 4 volte al giorno da
>   28/07. L'archivio è `data/smarkets_matches/`.
> - **Fixture ufficiali: ✅ li dà la stessa fonte** — l'API espone ~1 giornata
>   per lega con data e ora. Restano da **verificare contro una seconda fonte**
>   (openfootball): «ciò che è quotato» non è per definizione «la giornata
>   intera».
> - **La prima partita è il 15 agosto, non il 16**: `spain-la-liga`
>   Alaves–Getafe, 15/08 17:30 UTC (letto dal listino, non dagli outright).
>   **La scadenza del congelamento è il 14 agosto.**
> - ⚠️ **Lezione pagata lo stesso giorno**: la Liga era uscita dalla raccolta
>   **in silenzio** dal 31/07 perché Smarkets ha rinominato lo slug
>   (`spain-laliga` → `spain-la-liga`) e la guardia scattava solo a 5 leghe su
>   5 mancanti (Fase 127). Corretto. Da qui in avanti, **prima di ogni
>   congelamento si controlla che tutte e 5 le leghe siano nell'ultimo file**,
>   non che il file esista.
>
> **Restano aperte**, in ordine di dipendenza: (1) la **mappa nomi
> Smarkets → nostri** — bloccante sia per M1 sia per M2; (2) il congelamento
> **M1** sui fixture veri (`scripts/_run_prospettico_2627.py` ha ancora
> `FIXTURES` hardcoded su 7 partite Premier); (3) lo **script di scoring**;
> (4) i **criteri pre-registrati**. Più una decisione: il regime denso gira
> ogni 6h, quindi la «chiusura» del M2 può essere vecchia fino a 6 ore — o si
> infittisce il cron nelle finestre di partita, o lo si dichiara.

**Date di inizio** (fonte unica `newseason.md` §1, `start_date` degli eventi
outright Smarkets scaricati il 25/07/2026, **da riverificare a inizio agosto**):
La Liga **16/8**, Premier e Ligue 1 **21/8**, Serie A **22/8**, Bundesliga
**28/8**. **La scadenza vera del congelamento è il 16 agosto** — non fine mese,
non l'inizio della Serie A. Da fine luglio 2026 sono meno di tre settimane.
*(⚠️ rettifica 01/08: il listino per-partita dice **15/8** per la Liga — vedi il
riquadro sopra. Le date qui restano quelle degli outright, come dichiarato.)*

Cosa esiste già, per non rifarlo:

| pezzo | stato | dove |
|---|---|---|
| previsioni **outright** congelate | ✅ fatto il **2026-07-25**, ma **3 leghe** (`serie_a`, `premier_league`, `la_liga`) | `experiments/prospettico_2026_27_outright.json` |
| anteprima **DC per-partita** | ⚠️ **illustrativa**, 7 partite Premier plausibili, congelata 2026-07-23 | `experiments/prospettico_2026_27_dc.csv` |
| motore **per-lega** su M1 e M2 | ✅ chiuso (Fasi 83-bis e 92-bis) | `predict.py --league <lega>`, `src.config.MARKET_ENGINE` |
| **quote 1X2 + O/U per-partita** | ✅ **risolto** (Fasi 115-118): Smarkets, 4 giri al giorno dal 28/07 | `data/smarkets_matches/`, `.github/workflows/smarkets-prematch.yml` |
| **fixture ufficiali** 2026-27 | ✅ **li dà la stessa fonte** (lega, squadre, data, ora); da verificare contro openfootball | l'ultimo file di `data/smarkets_matches/` |
| **mappa nomi Smarkets → nostri** | ❌ **manca — è il collo di bottiglia** (P1) | `src/data/sources.py` (`TEAM_ALIASES`) |
| **script di scoring** | ❌ non esiste (P4) | — |

### 5.1 · COSA FARE ORA — lista ordinata per dipendenza (agg. 01/08/2026, Fase 127)

> **Come si legge.** I passi sono in ordine di **dipendenza**, non di
> importanza: P1 sblocca P2 e P3, e senza P3 non c'è test. La colonna
> «scadenza» è vera: il **14 agosto** è la vigilia di Alaves–Getafe, la prima
> partita della stagione. Ciò che non è congelato entro quella sera non è più
> una previsione, per definizione.
>
> **Quanto manca a ogni cosa lo dice il calendario, non questo file**: al
> 01/08 sono **13 giorni** a P3, il resto viene dopo il fischio.

| # | passo | sblocca | scadenza | stato |
|---|---|---|---|---|
| **P1** | **mappa nomi Smarkets → nostri** | P2, P3, P5 | 7 ago | ✅ **fatto 01/08** (Fase 128) |
| **P2** | `_run_prospettico_2627.py` legge i fixture veri | P3 | 10 ago | ✅ **fatto 01/08** (Fase 129) |
| **P3** | **congelamento M1 (DC)**, 5 leghe, commit datato | il test | **14 ago** | ✅ **congelato 01/08** — `prospettico_2026_27_m1.csv`, 48 partite, 26 mercati |
| **P4** | **script di scoring**, scritto prima dei risultati | P7 | 14 ago | ✅ **fatto 01/08** — `_run_prospettico_scoring.py`, 56 test |
| **P5** | **M2** dall'ultimo snapshot pre-kickoff | il confronto col mercato | a ogni giornata | ⏳ **pronto a partire**: P1 e D1 chiusi, si esegue dopo il fischio |
| **P6** | criteri **pre-registrati** | l'onestà del test | prima di P3 | ✅ **fissati 01/08** (qui sotto + docstring dello scoring) |
| **P7** | risultati reali → scoring → run + fase di diario | la conclusione | dopo il full-time | ❌ |

**P1 · La mappa nomi è il vero collo di bottiglia.** Smarkets scrive
`Inter Milan`, `AC Milan`, `Nottm Forest`, `Köln`, `Le Mans FC`,
`Racing Santander`: nomi che i nostri snapshot non conoscono. Va costruita
**a mano e verificata una per una** contro `TEAM_ALIASES`
(`src/data/sources.py`) — è un bug già capitato due volte («Hellas Verona» →
«Verona», Fase 5; `Manchester Utd` che fermava un join a 544/760, Fase 122).
⚠️ **Metà delle neopromosse non esiste negli snapshot** (Coventry, Hull,
Ipswich, Le Mans, Troyes, Paris FC, Elversberg, Paderborn, Schalke, Racing
Santander, Málaga, Elche…): lì il DC gira sul **prior δ** della lega, e la
cosa va **dichiarata partita per partita** nel CSV congelato, non lasciata
implicita. Un nome non mappato dev'essere un **errore rumoroso**, mai una
partita saltata in silenzio (è la lezione della Fase 127, pagata due giorni fa).

**P2 · Lo script di congelamento ha ancora i fixture incisi nel codice.**
`scripts/_run_prospettico_2627.py` contiene `FIXTURES` e `AS_OF` hardcoded:
**7 partite di Premier, plausibili e non ufficiali**. Vanno sostituiti dalla
lettura dell'ultimo file di `data/smarkets_matches/` (che ha lega, squadre,
data e ora vere). Alternativa manuale, se P2 slitta:
`python scripts/predict.py --league <lega> --date <YYYY-MM-DD> "<casa>" "<ospite>"`,
48 volte.

**P3 · Congelare TUTTO il Tier 1, non solo l'1X2.** L'1X2 si scora per primo
perché dà 4-5× la potenza (§4-bis punto 3), ma gli altri mercati **dopo non si
recuperano**: si congelano lo stesso, dichiarando che sono sotto-dimensionati.
Commit **datato** la sera del 14, prima del fischio.

**P4 · Lo scoring si scrive ORA, non a settembre.** Legge previsioni congelate
+ risultati e produce log-loss/Brier/calibrazione per lega e per mercato, via
`experiment_log.compute_metrics` (fonte unica, §5) e `append_run` con
`config.source = "prospettico_2627"`. Scriverlo dopo aver visto i risultati
significa sceglierne la forma sapendo già l'esito.

**P5 · I risultati veri** arrivano da football-data (stagione `2627`,
provider raggiungibile dalla Fase 100) — **non** da Smarkets, che dà prezzi e
non esiti.

#### Criteri PRE-REGISTRATI (fissati il 01/08/2026, prima di ogni dato — P6)

Scritti anche nel docstring di `scripts/_run_prospettico_scoring.py`, che è
datato in git **prima** di ogni partita 2026-27. Scegliere metrica e baseline
dopo aver visto gli esiti è la forma più facile di look-ahead, e non lascia
traccia.

1. **Metrica principale: log-loss sull'1X2. Una sola.** Il Brier e gli altri
   mercati si riportano, ma la conclusione si legge sull'1X2 — l'unico che a
   questi campioni ha potenza (4-5× il GG/NG e l'O/U 2.5, Fase 98).
2. **Bersaglio della prima giornata: la baseline, non il mercato.** Contro il
   mercato servono 574 partite; con 48 la potenza è ~10%.
3. **Successo, in ordine di ambizione**: (a) M1 batte la baseline con IC95%
   che esclude lo zero — serve n ≥ 184, cioè ~4 giornate su 5 leghe; prima si
   riporta il **segno**, non si conclude; (b) M2 riproduce il mercato entro il
   rumore; (c) M1 **calibrato**, ECE < 0.05 sull'1X2 — questo si può guardare
   subito, perché non è un confronto.
4. **Aspettativa dichiarata: M1 perde contro il mercato.** È previsto (α\*=0
   ovunque, Fase 16) e non è un fallimento: il test misura **quanto** perde su
   partite mai viste, e se resta calibrato.
5. **Quante ipotesi**: si dichiara il numero di confronti; l'1X2 pooled è il
   primario, il resto è **esplorativo** e va scritto che lo è.
6. **Niente ROI**: il progetto non simula denaro.
7. **Quale prezzo è usabile per il M2** (aggiunto il 01/08, Fase 130 — prima di
   sapere quali partite ne beneficiano). Il prezzo che usiamo è il **punto
   medio** fra banco e puntatore, e vale come prezzo **solo se il libro è
   stretto**: a 15-27 giorni dal fischio lo spread mediano dell'1X2 è **8 punti
   percentuali**, e in un caso (Angers–Lille, 01/08) banco e puntatore stavano
   a **15.6% e 55.6%** — un "medio" del 35.6% che non è il prezzo di niente.
   Regola dichiarata:
   - si calcola il M2 per **ogni** partita con libro a **due lati** su 1X2 e
     O/U 2.5, e si **registra lo spread** di ogni contratto;
   - l'**analisi primaria** usa solo le partite con spread **≤ 5pp su tutti**
     i contratti che entrano nell'inversione; le altre sono **secondarie** e
     vanno riportate separatamente, mai mescolate;
   - una partita senza libro a due lati al momento della chiusura **non ha
     M2**, e viene scorata **solo M1** — dichiarandolo nel conteggio, non
     lasciandola sparire (R6).

   ⚠️ Il perimetro non è uniforme fra leghe, ed è **misurato**: spread mediano
   1X2 a 15-27 giorni — Premier **0.010**, Liga 0.031, Serie A 0.031,
   Ligue 1 0.056, **Bundesliga 0.104**. Lo stesso ordinamento per liquidità
   della Fase 53. Se il libro non si stringesse a ridosso del fischio, il M2
   sarebbe di fatto un test su Premier/Liga/Serie A: è una **verifica da fare**
   al primo turno, non un'assunzione.

#### Decisioni aperte (non tecniche: vanno prese, non risolte)

- **D1 · Quanto dev'essere «chiusa» la chiusura del M2.** Il regime denso gira
  **ogni 6 ore** (`cron: '17 */6 * * *'`), quindi l'ultimo prezzo prima del
  fischio può essere vecchio fino a 6 h. Due strade: **(a)** infittire il cron
  nelle finestre di partita per avere un T−1h — più fedele a «chiusura», più
  file, più MB; **(b)** tenere così e **dichiarare** che il M2 usa un prezzo a
  T−6h. Nessuna delle due è sbagliata; sceglierne una in silenzio sì.
- **D2 · Che cosa si fa se P1 non chiude in tempo.** Timebox dichiarato: il
  test parte **col solo M1** e lo si scrive, invece di far slittare tutto.
- **D3 · Si congela UNA configurazione o una ROSA di varianti?** (aperta il
  10/08/2026, richiesta utente: *«così noi prevediamo i risultati della
  stagione utilizzando i modelli della fase 1, e molti non sono neanche stati
  sperimentati, soprattutto Premier e Liga»*). Il rilievo è **misurato**: le
  celle `⬜` della PANCHINA sono **2 su 51 in Serie A** e **23-26 nelle altre
  quattro** — per metà delle righe la config di Premier/Liga/Bundesliga/Ligue 1
  non è *scelta*, è **rimasta**. Congelando la sola config ufficiale, la
  stagione passa senza decidere nessuna di quelle celle. La proposta
  (`docs/CHIUSURA_FASE_1.md` §4) è congelare **nove varianti** — la config
  ufficiale più otto candidate che sono tutte **interruttori di
  configurazione**, non codice nuovo: router θ Liga, φ35 Liga, θ+φ35,
  `dp_tilt` Serie A, `dp_tilt` pooled, ensemble emivite, devig di Shin,
  estremizzazione O/U. Costo: un `dict` e una colonna nello scoring. Vincoli
  che restano: il **primario non cambia** (M1 vs baseline, log-loss 1X2,
  pooled) e la rosa è una **famiglia secondaria pre-registrata** con Holm al
  suo interno (criterio 5); e **la config ufficiale non si tocca ora** —
  accendere il router θ in Liga su evidenza da panchina è ciò che lo stato 🪑
  esiste per impedire. ⚠️ Limite dichiarato: con 1.752 partite in una stagione
  ×5 leghe è powered il **solo 1X2 pooled** (n₈₀ = 574); per-lega (380/306) e
  GG/NG (2.254) e O/U 2.5 (2.988) **no** — le varianti per-lega si leggono come
  accumulo, non come verdetto al 30 giugno. **Default se nessuno decide entro
  il 15/08**: si congela la rosa completa, perché il costo è trascurabile e
  l'omissione è irreversibile.

#### Controlli fissi, da rifare a ogni congelamento

- [ ] l'ultimo file di `data/smarkets_matches/` ha
      `leghe_senza_partite_esposte: []` **e** 5 leghe fra le righe. Non basta
      che il file esista: il 31/07 esisteva, pesava 120 KB e non conteneva La
      Liga (Fase 127).
- [ ] le date di inizio non si sono spostate (`fetch_smarkets_outrights.py`,
      oppure il listino per-partita che è più preciso: ha detto **15/8** dove
      gli outright dicevano 16/8).
- [ ] ogni nome squadra dei fixture risolve a un nome canonico.

---

#### Le caselle originali del blocco (aggiornate al 01/08)

- [x] ~~**Canale per le quote 1X2 + O/U per-partita**~~ — ✅ **risolto**
      (Fasi 115/116/118): Smarkets, 4 giri al giorno, archivio in
      `data/smarkets_matches/`.
- [x] ~~**Fixture ufficiali** di giornata 1~~ — ✅ **li dà la stessa fonte**,
      con data e ora. ⚠️ Restano da **verificare contro una seconda fonte**
      (openfootball): l'API espone ciò che è *quotato*, che non è per
      definizione la giornata intera.
- [ ] **Riverificare le date di inizio** delle 5 leghe (si spostano): ri-scaricare
      gli outright con `python scripts/fetch_smarkets_outrights.py` e confrontare
      `start_date`, oppure il calendario ufficiale. Se una data si sposta,
      aggiornare **qui e in `newseason.md` §1** (fonte unica).
- [ ] **Modello 1 (DC) congelato** coi fixture veri (= **P3**). ⚠️ `scripts/_run_prospettico_2627.py`
      ha `FIXTURES` e `AS_OF` **hardcoded** (solo Premier, 7 partite): vanno
      sostituiti con i fixture veri delle 5 leghe prima di rigenerare il CSV.
      In alternativa, partita per partita:
      `python scripts/predict.py --league <lega> --date <YYYY-MM-DD> "<casa>" "<ospite>"`.
      Congelare **tutti i mercati Tier 1**, non solo 1X2 (§4-bis punto 3: l'1X2 si
      scora per primo, ma gli altri si raccolgono lo stesso — dopo non si recuperano).
- [ ] **Estendere l'outright alle 5 leghe** se Polymarket/Smarkets quotano anche
      Bundesliga e Ligue 1 (`scripts/fetch_polymarket_open.py`,
      `scripts/fetch_smarkets_outrights.py`). Se non le quotano, **dichiararlo
      nel JSON**: un buco dichiarato è innocuo, un buco silenzioso no (§5-bis R6).
- [ ] **Script di scoring scritto ORA** (= **P4**), non a settembre (`newseason.md` §5/A1):
      legge le previsioni congelate + i risultati e produce log-loss/Brier/
      calibrazione per lega e per mercato, via
      `experiment_log.compute_metrics` (fonte unica) e `append_run`
      (`config.source = "prospettico_2627"`).
- [ ] **Pre-registrare i criteri** prima di vedere un dato (`newseason.md` §5/A3):
      metrica, soglia di successo, quante ipotesi si testano, e il vincolo del
      §4-bis (con una giornata non si conclude niente contro il mercato).
- [ ] **Congelare tutto PRIMA del calcio d'inizio, con un commit datato.** Una
      previsione prodotta dopo non è una previsione.

### 5.2 · Dopo il full-time

- [ ] Risultati reali → scoring (log-loss/Brier/calibrazione) di M1/M2/baseline,
      per lega e per mercato; **run in `runs.jsonl`** (`source=prospettico_2627`);
      voce nel diario (nuova fase) con i numeri e il blocco 📐.
- [ ] Confrontare l'**anteprima DC del §2** (congelata 2026-07-23, config già
      per-lega) coi risultati reali, dove le partite coincidono: quanto è costata
      l'estate di mercato non vista.
- [ ] **(NON opzionale, Fase 98) estendere a ~574 partite** — ≥19 giornate su 3
      leghe, **~12 su 5** — prima di dichiarare qualsiasi cosa sul confronto col
      mercato: con una sola giornata la potenza è 9,8% (§4-bis).

---

*Aggiornare questo file a ogni passo del test (fixture → previsioni congelate →
risultati → scoring). Finché resta APERTO, il test non è concluso.*
