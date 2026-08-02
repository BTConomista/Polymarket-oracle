# Playbook — come si aggiunge (e si studia) una lega nuova

Questo file è la **procedura operativa** per portare il progetto su un
campionato nuovo (Eredivisie, Primeira Liga, Championship…). Distilla il metodo
effettivamente seguito **due volte**:

- **Premier League e La Liga** (Fasi 53-57 dati/tracer/ri-taratura; Fasi 79-80
  studio dedicato e leve per-lega) — l'onboarding da cui il playbook è nato;
- **Bundesliga e Ligue 1** (Fase 100) — il primo onboarding fatto *seguendo*
  questo file dall'inizio alla fine, e che ne ha cambiato tre pezzi: i dati si
  **scaricano** invece di arrivare come bundle, quindi si può **verificare lo
  snapshot contro la fonte-madre** (Passo 0-bis, nuovo); le **regole sui dati
  sporchi R1-R7** (CLAUDE.md §5-bis) sono nate lì e vanno applicate qui; e le
  mappe per-lega da riempire non sono solo `LEAGUE_CONFIGS` (Passo 3-bis, nuovo).

E le regole date dall'utente: *studiare a fondo i dati prima di modellare,
provare gli STESSI modelli su ogni lega, farsi dire dai backtest quali costanti
divergono, e tenere sempre aggiornati diario/registri/rose*. Chi apre questo
file davanti a una lega nuova deve poter procedere senza reinventare nulla.

Regola madre (CLAUDE.md §7): **le formule sono universali, i numeri no.**
Una lega nuova è una modifica di *configurazione* (voce in `LEAGUE_CONFIGS`,
`sources.LEAGUES`, alias, spareggi), mai di codice del modello.

**Aspettativa realistica, prima di cominciare:** su 5 leghe su 5 **il modello
trasferisce e l'edge no** (dettaglio in «Cosa aspettarsi»). Una lega nuova è
un'occasione per *replicare* — e per misurare quali costanti sono di lega —
non per aspettarsi un vantaggio economico che nelle altre non c'è.

---

## Passo 0 — Procurare e congelare i dati

### 0.1 · Fonti

Risultati+quote in formato football-data.co.uk e xG Understat, stesse stagioni
delle leghe esistenti (oggi 2017-18 → 2025-26). **Dalla Fase 100 la rete è
aperta**: football-data.co.uk e understat.com rispondono 200 (elenco completo e
aggiornato degli host raggiungibili in `docs/MANUALE_SOPRAVVIVENZA.md` §1).
Quindi:

- **via normale (oggi)**: `python scripts/fetch_sources.py --leagues <lega>`
  scarica i CSV football-data e i JSON Understat
  (`GET /getLeagueData/{Lega}/{anno}` con header `X-Requested-With:
  XMLHttpRequest` — **obbligatorio**, senza risponde 404) e registra in un
  **manifest** URL, timestamp UTC, byte e **SHA256** di ogni file. La
  provenienza non è un optional: è ciò che rende possibile il Passo 0-bis.
  ⚠️ I grezzi finiscono in `data/fonti/`, che è **in `.gitignore`** (~135 MB):
  ciò che resta versionato è il **manifest**, non i file. Conseguenza: la
  rigenerazione di uno snapshot richiede prima `fetch_sources.py`, cioè la
  rete — a differenza di Premier/Liga, i cui bundle in `files/` sono versionati
  e permettono la rigenerazione offline.
- **fallback storico**: bundle JSON caricati dall'utente in `files/` +
  `scripts/build_league_snapshot.py` (pattern Fase 54, Premier/Liga), o workflow
  GitHub Actions d'import (pattern Fase 67). Da usare **solo** se la fonte torna
  irraggiungibile: col bundle il Passo 0-bis livello B non è eseguibile.

### 0.2 · Snapshot congelato

`scripts/build_new_snapshot.py` → `data/<lega>_matches.csv` versionato, **stesso
schema a 40 colonne** delle altre leghe, **nomi e ordine compresi** (lo verifica
`tests/test_league_snapshots.py::test_schema_identico_tra_leghe`; l'ordine
divergente è stato una nostra anomalia reale, audit Report 1 §4.6).

Lo script **riusa il codice di produzione senza toccarlo** — `loader._normalize`
(risultati + le 10 colonne quota con la politica Fase 73),
`understat.parse_season_xg`, `player_scores.add_squad_values`,
`transfermarkt.add_absences`, `fixtures.*` — con la lega nuova **registrata a
runtime** (`scripts/nuove_leghe.registra()`) finché il lavoro è isolato; poi le
voci si spostano in `src/data/sources.py`, `src/config.py`,
`src/data/player_scores.py` (Passo 3-bis). Nessuna riga di modello cambia.

Risultato ottenuto sulle due leghe della Fase 100:

| file | partite | stagioni | squadre | colonne |
|---|--:|--:|--:|--:|
| `data/bundesliga_matches.csv` | 2.754 | 9 | 29 | 38 |
| `data/ligue_1_matches.csv` | 3.097 | 9 | 30 | 38 |

### 0.3 · Riconciliazione nomi (il bug classico)

`scripts/riconcilia_nomi.py`: estrarre TUTTI i nomi squadra da **ogni** fonte
(football-data = canonica, Understat, openfootball, player-scores) e
confrontarli **per identità**, mai per ordinamento; alias in
`sources.TEAM_ALIASES`. Il builder deve **fallire rumorosamente** se per una
qualsiasi stagione l'insieme delle squadre football-data ≠ l'insieme Understat.
Obiettivo: **copertura xG ~100%, zero righe orfane**; i test anti
quasi-duplicato devono passare. (Fase 100: 103 alias nuovi — 53 Bundesliga, 50
Ligue 1 — di cui 92 effettivamente esercitati dalle fonti, gli altri 11
varianti difensive; zero orfane su 4 fonti × 9 stagioni.)

**Due alias sono stati trovati da controlli INDIRETTI, non da un elenco** — e
sono il tipo di cosa che un confronto di liste non vede:

- `player_scores` fallisce rumorosamente sui club non agganciati → 5 nomi
  formali tedeschi (`1.FC Köln`, `1.FSV Mainz 05`, …);
- `Havre AC` (nome usato nei file di Ligue 2) è emerso perché **Le Havre
  risultava senza alcuna partita precedente al suo esordio**: senza quell'alias
  mancava tutto lo storico di seconda serie e il riposo della prima gara era
  `NaN`. Da qui un **controllo ora sistematico**: *ogni squadra deve avere
  partite precedenti al proprio esordio* (5 leghe, 0 eccezioni).

### 0.4 · Dati ausiliari

Pattern Fasi 59-60: calendario completo di club (coppe+Europa →
`rest_days_full`, `midweek_europe`), `squad_value` (player-scores), assenze.
Semantica quote apertura/chiusura: SOLO colonne `*C*` genuine come chiusura
(regola Fase 73).

- ⚠️ **openfootball non ha uno schema unico**: la Francia usa
  `france/{stagione}_fr1.txt` (stagione nel **nome del file**, non in una
  cartella), che la costante `OPENFOOTBALL_DOMESTIC_URL` non esprime — serve un
  builder per lega. Aspettarsi che la prossima lega ne richieda un altro.
- Dove la fonte primaria non copre si usa una **fonte secondaria dichiarata**
  con la scala misurata contro la primaria dove entrambe esistono (**regola
  R2**): è il caso di `squad_value` 2025-26 da Transfermarkt. Mai innestarla in
  silenzio: la colonna che mescola due misure va dichiarata a chi la usa.

### 0.5 · Documentare i dati

Aggiornare **`docs/DATI.md`** (catalogo dati) con coperture, semantica e
**lacune dichiarate** (regola R4: si dichiarano anche quando non sono errori).
Le lacune tipiche di una lega nuova, tutte già viste:

| lacuna | dettaglio | effetto |
|---|---|---|
| chiusura O/U 2017-19 | assente a monte, 5 leghe su 5 | copertura O/U di chiusura 77.78% (Bundesliga) e 75.46% (Ligue 1); lo stimatore E3 si estende alla lega nuova |
| coppa nazionale | openfootball non copre tutte le stagioni | `midweek_europe` **falso 0** per chi giocò la coppa |
| Europa/Conference 2025-26 | file assenti in openfootball, vale per tutte le leghe | falso 0 nella stagione in corso |
| partite non acquisite dalla fonte xG | `isResult=false` | `NaN` dichiarato |

Sullo **stimatore E3** della chiusura O/U 2017-19 vale una precisazione pagata
alla Fase 100: l'errore da dichiarare **non** è il ~0.012 misurato in
*interpolazione* (fit che vede stagioni prima e dopo), perché quella stima non
si usa mai così — la chiusura 2017-19 non esiste, quindi i coefficienti possono
venire solo da stagioni successive. Nel regime d'uso l'errore misurato è
**0.0143 in Bundesliga e 0.0125 in Ligue 1**. Si dichiara quello.

## Passo 0-bis — Verificare lo snapshot contro la FONTE-MADRE *(nuovo, Fase 100)*

Passo **nuovo** e **obbligatorio quando i dati si scaricano**: con i bundle
manuali non era eseguibile, ed è per questo che non esisteva. Fino alla Fase 100
il progetto aveva verificato i dati *contro sé stessi* (coerenza interna, range,
duplicati); il controllo che conta è un altro: **lo snapshot corrisponde alla
fonte a monte?**

Quattro livelli, dal più debole al più forte
(`scripts/audit_snapshots.py` per A-B-C, `scripts/audit_anomalie.py` per D):

| livello | cosa verifica |
|---|---|
| **A. interno** | schema, duplicati, girone all'italiana, range, copertura, coerenza gol↔risultato, overround, nomi squadra |
| **B. esterno** | confronto **riga per riga** con la fonte ri-scaricata; le 10 colonne quota **ri-derivate** col codice di produzione (`loader._odds_from_raw`) |
| **C. indipendente** | i gol secondo una **fonte terza** (Understat) contro quelli dello snapshot |
| **D. avversariale** | «e se la fonte fosse sbagliata?»: margini impossibili, incoerenza 1X2↔O/U, fisica (gol > tiri in porta), impronte-quota duplicate, riposo, xG impossibile, **xG segnaposto** |

Esito da pretendere (ottenuto sulle 5 leghe, 16.111 partite): **0 differenze**
su gol, date, tiri, 10 colonne quota e 8 colonne xG; i gol confermati dalla
fonte indipendente su 16.109 partite su 16.110 appaiate (l'unica difformità è
il risultato assegnato a tavolino, R1).

### Le regole sui dati sporchi (CLAUDE.md §5-bis) — dove si applicano

Sono nate **da questo onboarding**, una per una, pagate con un errore vero. La
numerazione **canonica** è quella di `CLAUDE.md` §5-bis, ed è quella usata qui;
la versione estesa con i casi istruiti è in `docs/audit_5_leghe/REGOLE.md`, che
però conserva la numerazione del cantiere (lì R4 = isolamento del cantiere,
R5 = «le anomalie si dichiarano», R6 = procedura per una riga corrotta, e non
esistono le voci «finto pieno» e «intervalli/potenza»). Non confondere le due.

| regola | dove si applica in questo playbook |
|---|---|
| **R1** dato del CAMPO, non del tribunale | livello C: una difformità fra due fonti sul risultato è quasi sempre questo. Caso istruito: Union Berlin-Bochum 14/12/2024, 1-1 sul campo (partita giocata per intero), 0-2 a tavolino → snapshot a 1-1. **Caso per caso, mai una regola automatica** |
| **R2** fonte secondaria dichiarata | Passo 0.4 (dati ausiliari), con la scala misurata dove le due fonti coesistono |
| **R3** nessuna modifica a mano | ogni correzione vive in `data/correzioni_dichiarate.csv` e si applica **solo** con `scripts/applica_correzioni.py`, che verifica il valore-prima cella per cella e si ferma se non combacia |
| **R4** dichiarare le anomalie anche quando NON sono errori | l'output del livello D va scritto **tutto** (es. 74 righe con gol > tiri in porta: sono autogol, non errori) |
| **R5** procedura per una riga che sembra corrotta | quando un controllo scatta: spiegare → diagnosticare con informazione indipendente → cercare il dato vero → stimare solo se non esiste → registrare, errori compresi |
| **R6** il buco peggiore è il **finto pieno** | ⚠️ vedi sotto: è la trappola specifica di questo passo |
| **R7** ogni statistica di testa ha il suo intervallo | Passi 2-5, ogni test |

### ⚠️ R6, la trappola specifica dell'onboarding: il «finto pieno»

Un dato mancante e dichiarato è innocuo. Il pericolo è il valore che *sembra*
una misura e non lo è — e **nessun confronto snapshot-contro-fonte lo vede,
perché il dato coincide con la fonte: è la fonte a non avere il dato.**

Due casi, entrambi emersi con l'onboarding di Bundesliga e Ligue 1 (il secondo
riguarda tutte e 5 le leghe):

1. **xG segnaposto** (Holstein Kiel-Bochum 09/02/2025): Understat non ha mai
   acquisito la partita — lista tiro-per-tiro vuota su entrambi i lati — e al
   posto della misura ha scritto `xG = 2.0 / 2.0`, **interi identici ai gol**;
   `ppda` con contatori a zero, `deep = 0/0`. Un xG «normalissimo» e falso.
   1 caso su 16.111.
2. **1.603 celle `midweek_europe` a 0** per partite di coppa che il calendario
   non copriva: uno zero che significava «non lo so».

E il caso **opposto**, che insegna a non correggere di fretta
(R5 passo 1): Bielefeld-Leverkusen 21/11/2020, `xG = 0` per una squadra che
aveva **segnato**. Sembrava impossibile; non lo era — 0 tiri e il gol era un
**autogol** del portiere avversario. Il dato era giusto, era il controllo a
essere cieco: **falso positivo ritirato**.

### I due guard entrati in produzione — vanno verificati sulla lega nuova

1. **Overround bilaterale** (`loader._pick_market_odds`, `ORR_MAX = 1.12`):

   ```
   orr = Σ 1/quota_i        # su TUTTE le quote dello stesso mercato
   scarta il mercato IN BLOCCO se  orr < 1.0  (arbitraggio)  oppure  orr > 1.12
   ```

   Il guard della Fase 58 copriva solo il lato `< 1`; una media multi-book con
   il 28% di margine è altrettanto impossibile e passava. `ORR_MAX = 1.12` non è
   a occhio: nell'era `Avg` il massimo mai osservato su 12.457 righe è
   **1.0765**, quindi la soglia sta ~6σ oltre la mediana sana e 4 punti sopra
   quel massimo. Ri-derivando tutte e 10 le colonne quota delle 5 leghe col
   codice di produzione, il guard cambia **6 celle** (La Liga 2018-19, overround
   fino a 1.283) e **zero** altrove su 16.111 partite. Test:
   `test_overround_impossibilmente_alto_scartato`,
   `test_nessun_margine_impossibile_negli_snapshot`.
2. **xG segnaposto** (`audit_anomalie.check_xg_segnaposto`): candidati =
   `deep = 0` su *entrambe* le squadre (filtro economico: 4 casi su 16.111, e un
   segnaposto lo soddisfa sempre); verdetto = **lista tiri vuota** mentre gol o
   tiri in porta esistono. Esito: 1 segnaposto, 3 candidati legittimi. Test:
   `test_xg_segnaposto_scartato`.

## Passo 1 — Conoscere la lega PRIMA di modellare (EDA)

Due batterie standard, entrambe scriptate:

- **EDA base** (`scripts/eda_nuove_leghe.py`, generalizza il pattern Fase 55 a
  tutte le leghe insieme): esiti H/D/A, gol, Over%, γ=ln(casa/ospite),
  Var/Media, δ=ln(gol_lega/gol_promosse), autocorr delle forze, corr xG-gol,
  margine book, edge mercato vs baseline. Gira sulle 5 leghe **insieme**, così
  la lega nuova si legge sempre per confronto; serve anche come ulteriore
  validazione dei dati (numeri strutturalmente impossibili si vedono qui).
- **EDA struttura** (pattern Fase 79, `_run_fase79_eda_pl_liga.py`):
  1. **pareggio per fascia di equilibrio** (reale−mercato per quartile di
     |pH−pA| devig) → dice subito se la lega è "latina" (deficit-pareggio,
     come SA/Liga) o "inglese" (assente/invertito);
  2. **congestione** (riposo ≤3g, dicembre, midweek europeo);
  3. **γ_t per stagione** (stabilità del vantaggio-casa, crollo COVID).

Le 5 leghe già misurate (finestra 9 stagioni), da usare come metro di paragone:

| lega | gare | gol/gara | casa% | pari% | ospite% | over2.5% | γ | Var/Media | δ promosse | corr(xG,gol) | margine 1X2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| serie_a | 3420 | 2.719 | 41.2% | 26.0% | 32.7% | 52.0% | 0.150 | 0.978 | 0.229 | 0.607 | 4.35% |
| premier_league | 3420 | 2.839 | 44.1% | 23.4% | 32.5% | 54.4% | 0.185 | 0.963 | 0.329 | 0.635 | 3.82% |
| la_liga | 3420 | 2.582 | 45.3% | 26.5% | 28.2% | 47.1% | 0.272 | 1.038 | 0.218 | 0.621 | 4.26% |
| bundesliga | 2754 | 3.122 | 43.7% | 24.9% | 31.4% | 60.3% | 0.216 | 0.962 | 0.277 | 0.644 | 4.27% |
| ligue_1 | 3097 | 2.742 | 43.3% | 25.3% | 31.4% | 52.2% | 0.202 | 1.006 | 0.188 | 0.631 | 4.41% |

**Il prior si dichiara QUI, prima di qualunque fit** — e poi si verifica. Fase
100: dall'EDA del deficit-pareggio era stato scritto *«in Ligue 1 aspettarsi
φ0 ≈ 0; in Bundesliga un φ0 piccolo e positivo»*; misurato al Passo 2b,
**Ligue 1 φ0 = 0.0000** e **Bundesliga φ0 = 0.1827**. Previsione registrata in
anticipo e confermata: l'EDA è uno strumento di *pronostico*, non solo di
descrizione.

### Le particolarità strutturali: cercarle prima, non dopo

Ogni lega ne ha, e rompono i conteggi che assumono la Serie A:

- **numero di squadre**: la Bundesliga ne ha 18 → **306 gare/stagione**, non
  380. Ogni conteggio che assume 380 va parametrizzato;
- **dimensione che cambia dentro la finestra dati**: la Ligue 1 è passata da 20
  a 18 squadre nel 2023-24 (380 gare fino al 2022-23, 306 dopo);
- **stagioni anomale**: la Ligue 1 2019-20 fu **cancellata** per COVID
  (30/04/2020): 279 gare su 380, ultima l'8 marzo; PSG e Strasburgo ne giocarono
  27 invece di 28. Usabile ma **strutturalmente corta**;
- **regole di classifica**: vedi Passo 3-bis, sono un dato di lega.

**Output obbligatorio**: la sezione della lega nel **quaderno di studio** e la
**riga nella tabella «differenze in un colpo d'occhio»**, con la colonna
"universale?" compilata. Run EDA in `runs.jsonl`.

> ⚠️ **Residuo aperto dichiarato.** Il quaderno di studio oggi esiste solo per
> Premier e Liga (`docs/STUDIO_PREMIER_LIGA.md`). Per Bundesliga e Ligue 1 il
> materiale equivalente vive negli **11 report dell'audit**:
> `docs/audit_5_leghe/03_nuove_leghe.md` (dati + EDA + δ),
> `06_tranche3.md` (passi 2-5) e `10_modelli_nuove_leghe.md` (la rosa messa
> alla prova). Non è stato consolidato in un `docs/STUDIO_*.md` dedicato. Con
> 5+ leghe la forma «un file per lega» va decisa una volta per tutte.

## Passo 2 — Tracer bullet (il modello COSÌ COM'È)

Prima di ritarare qualsiasi cosa (§1.1 e §1.3 del CLAUDE.md):

- **DC config Serie A** (o della lega più simile) walk-forward sulla lega nuova
  (pattern Fase 56, oggi `scripts/tranche3_tracer.py`): deve battere la
  baseline; misurare il gap col mercato. **Aspettativa: +0.015…+0.021** — e
  finora si è sempre avverata.
- **Tracer market-side** (pattern Fase 53, `scripts/tranche3_market_tracer.py`;
  niente port del DC, bastano chiusura e risultati): θ (sotto-dispersione),
  tilt λ/μ, draw-bias w_D/w_A, φ0, ROI pari-equilibrio.

Misure disponibili come metro (walk-forward, 6 stagioni di test 2020-21 →
2025-26, stessa finestra e stesso codice per tutte):

| lega | partite | 1X2 modello | baseline | mercato | **gap vs mercato** | CI95 |
|---|--:|--:|--:|--:|--:|---|
| serie_a | 2.280 | 0.9797 | 1.0849 | 0.9632 | +0.0165 | [+0.0107, +0.0225] |
| premier_league | 2.280 | 0.9831 | 1.0695 | 0.9623 | +0.0207 | [+0.0138, +0.0275] |
| la_liga | 2.280 | 0.9843 | 1.0689 | 0.9681 | +0.0162 | [+0.0103, +0.0225] |
| bundesliga | 1.836 | 0.9919 | 1.0722 | 0.9738 | **+0.0181** | [+0.0109, +0.0253] |
| ligue_1 | 2.058 | 1.0041 | 1.0750 | 0.9851 | **+0.0190** | [+0.0121, +0.0258] |

*(La riga Serie A di questa tabella — 0.9797 / +0.0165 — è **PRE-fix Fase 92**:
è il valore che il walk-forward produceva al momento della misura, ed è servito
da controllo di riproducibilità dell'apparato. Il numero-bandiera del progetto
al codice di HEAD è **0.9799 / +0.0167**, rimisurato alla Fase 101.)*

Il tracer market-side sulle stesse 5 leghe (7 stagioni 2019-20 → 2025-26, tutte
quelle con chiusura O/U reale, ogni parametro fittato leave-one-season-out):

| lega | margine book | θ | tilt λ | tilt μ | φ0 | ROI pari-equilibrio |
|---|--:|--:|--:|--:|--:|--:|
| serie_a | 4.87% | 1.232 | −0.028 | +0.026 | 0.2433 | +3.15% |
| premier_league | 4.27% | 1.085 | −0.024 | +0.009 | 0.0341 | −3.82% |
| la_liga | 4.75% | 1.242 | −0.002 | −0.007 | 0.2461 | +1.90% |
| bundesliga | 4.76% | **1.080** | +0.019 | +0.022 | **0.1827** | +5.04% |
| ligue_1 | 5.02% | **1.103** | −0.010 | +0.022 | **0.0000** | −7.82% |

**Aspettativa sul θ**: due famiglie, non un continuo — «latine» (Serie A, La
Liga) ≈1.24 dove la sotto-dispersione paga, e Premier/Bundesliga/Ligue 1
≈1.08-1.10 dove non paga. **Non** si predice dalla liquidità del book (vedi
«Cosa aspettarsi» §2). Il ROI pari-equilibrio non è mai risultato conclusivo:
tutti i CI95 attraversano lo zero, +5.04% della Bundesliga compreso.

## Passo 3 — Ri-taratura per-lega degli iperparametri DC

Una leva alla volta (§1.2), le altre ferme al default (pattern Fase 57, oggi
`scripts/tranche3_ritaratura.py`):

- **δ neopromosse**: SEMPRE ricalcolato.

  ```
  δ = ln( gol_medi_per_squadra_gara_della_lega / gol_medi_per_gara_delle_NEOPROMOSSE )
  ```

  Neopromossa = squadra presente in una stagione e assente in quella precedente
  (la prima stagione dei dati non ha un «prima»: esclusa). È l'unico
  iperparametro finora davvero per-lega:

  | lega | δ | derivazione |
  |---|--:|---|
  | serie_a | 0.23 | ln(1.360/1.081) = 0.2292 |
  | premier_league | 0.33 | ln(1.419/1.022) = 0.3286 |
  | la_liga | 0.22 | ln(1.291/1.038) = 0.2179 |
  | **bundesliga** | **0.28** | ln(1.5608/1.1834) = 0.2768 (17 neopromosse, 578 gare-squadra) |
  | **ligue_1** | **0.19** | ln(1.3710/1.1358) = 0.1882 (19 neopromosse, 670 gare-squadra) |

  Si adotta per **motivazione strutturale** anche con CI non conclusivo
  (precedente: Fasi 7/17/57). Onestà obbligatoria: il guadagno misurato
  dell'adozione su Bundesliga e Ligue 1 è **+0.0001 e +0.0000** di log-loss,
  cioè nulla — mai spacciarlo per un miglioramento. La Ligue 1 è il caso
  istruttivo: il suo δ va nella direzione **opposta** a tutte le altre (le
  promosse francesi sono le meno deboli del campione) e il modello non se ne
  accorge: la leva è reale, la sua ampiezza è sotto la risoluzione del test.
- **emivita / shrinkage / α blend**: griglia minima {365,730} × {1.5,3} ×
  {0.75}. Aspettativa: **curve piatte** — successo su **5/5 leghe**, il tetto è
  informativo. L'emivita a 730 giorni *peggiora* in tutte (nel rumore): i 365
  giorni restano. Se una lega desse curve NON piatte sarebbe una scoperta:
  documentarla a fondo prima di adottare.
- **γ vantaggio-casa NON si tara**: lo fitta il DC dai dati.
- Nuova voce in `LEAGUE_CONFIGS` con blocco 📐 per ogni numero (§2-bis).

## Passo 3-bis — Le mappe per-lega da riempire *(nuovo, lezione della Fase 100/101)*

`LEAGUE_CONFIGS` **non è l'unica** mappa per-lega. L'integrazione di Bundesliga
e Ligue 1 ne ha lasciate indietro due, e la seconda è entrata in produzione
senza un test che la coprisse. Elenco da percorrere tutto:

| mappa | dove | cosa contiene |
|---|---|---|
| `LEAGUES`, `UNDERSTAT_LEAGUES`, `UEFA_COUNTRY_CODE`, `SECOND_TIER_NAMES`, `DOMESTIC_CUP_COMPETITIONS`, `OPENFOOTBALL_DOMESTIC_REPO`, `TEAM_ALIASES` | `src/data/sources.py` | fonti, calendari, alias |
| `COMPETITION_IDS` | `src/data/player_scores.py` | id competizione del valore rosa |
| `LEAGUE_CONFIGS` | `src/config.py` | iperparametri DC (δ e il resto) |
| `MARKET_ENGINE` | `src/config.py` | lega → motore del market-implied (θ/φ0/κ/sharpen del router). Premier, Liga, **Bundesliga e Ligue 1** escono col motore **liscio** |
| `TIEBREAK_RULES` | `src/models/season_sim.py` | criteri di spareggio ufficiali, dopo i punti |

### Le regole di spareggio sono un dato di lega, non un dettaglio

Servono al mercato **campione di stagione** (`season_sim`) e vanno prese dal
**regolamento ufficiale**, non indovinate. Quelle in produzione:

```python
TIEBREAK_RULES = {
    "serie_a":        ("h2h", "gd", "gf"),
    "la_liga":        ("h2h", "gd", "gf"),
    "premier_league": ("gd", "gf"),
    "bundesliga":     ("gd", "gf", "h2h"),   # DFL-Spielordnung §2 c.3 lett. c)
    "ligue_1":        ("gd", "h2h", "gf"),   # LFP Reglement, art. 518 ter
}
```

La Ligue 1 è un **terzo ordine distinto** da entrambi quelli già presenti: la
differenza reti viene prima degli scontri diretti (come in Premier) ma gli
scontri diretti vengono prima dei gol fatti (come in Serie A). Aspettarsi che la
lega successiva ne porti un quarto.

> ⚠️ **Lezione pagata.** Bundesliga e Ligue 1 sono entrate in produzione con le
> tuple giuste ma **senza test**: `test_tiebreak_rules_per_league` asseriva solo
> `serie_a[0]`, `la_liga[0]`, `premier_league[0]` e il default, e nessun test
> nominava le due leghe nuove — **uno scambio fra le due tuple passava la
> suite**. Corretto dall'audit (Fasi 101/101-bis) con
> `test_tiebreak_rules_tuple_complete` (tuple complete, 5 leghe) e
> `test_tiebreak_distingue_bundesliga_da_ligue_1` (caso costruito: la
> Bundesliga premia i gol fatti, la Ligue 1 gli scontri diretti). Stessa storia
> per `MARKET_ENGINE`, che copriva 3 leghe su 5: ora un test verifica che
> `MARKET_ENGINE` e `LEAGUE_CONFIGS` **elenchino le stesse leghe**.
>
> Regola che ne esce: **ogni mappa per-lega vuole un test di copertura** (le
> chiavi coincidono con `LEAGUE_CONFIGS`) **e**, dove il valore è una tupla
> ordinata, un test che ne distingua il *comportamento* — non solo il primo
> elemento.

## Passo 4 — Il motore market-implied sulla lega

- **Multi-mercato dalla chiusura** (pattern Fase 76, `scripts/tranche3_mercati.py`):
  l'inversione 1X2+O/U → (λ,μ) → matrice → mercati Tier 1, **senza ritarare
  ρ=−0.06**. Aspettativa: batte il DC-da-gol quasi ovunque. Misurato:

  | lega | partite | batte il DC-da-gol | batte la baseline |
  |---|--:|--:|--:|
  | serie_a | 2.280 | 14/15 | 14/15 |
  | premier_league | 2.280 | 14/15 | 14/15 |
  | la_liga | 2.280 | 15/15 | 14/15 |
  | **bundesliga** | 1.836 | **15/15** | 14/15 |
  | **ligue_1** | 2.058 | **15/15** | 14/15 |

  La matrice è universale su **5/5 leghe**. Se non accade, fermarsi e capire
  (probabile problema dati). L'unico mercato dove la baseline vince è, in ogni
  lega, il **pari/dispari**.
- Il motore funziona anche partendo dall'**apertura**: 25/25 mercati contro il
  DC-da-gol su entrambe le leghe nuove (conteggio di **segni**; i mercati con
  CI95 che esclude lo zero sono 18/25 e 21/25, e i 25 mercati sono proiezioni
  della stessa coppia (λ,μ): valgono 1-2 gradi di libertà, non 25 conferme
  indipendenti). Sui **totali** la chiusura resta conclusivamente migliore.
- **MAI copiare le costanti di AFFINAMENTO**: θ del router, dp_lvl, φ35, nudge
  stagionale sono **per-contesto** (lega × epoca — Fasi 53/75/79/80/100). Ognuna
  va rifittata leave-future-out sulla lega, con **aspettativa dichiarata PRIMA**
  e il FIT stesso trattato come risultato (esempi: φ0=0.00 in Premier e in
  Ligue 1 = il deficit-pareggio non esiste; boost-38ª 0.915 in Liga = il profilo
  di fine stagione è invertito).
- **Corollario misurato alla Fase 100:** θ **non è una costante di lega, è una
  scala della fonte dei tassi** — θ_DC < θ_apertura < θ_chiusura in 11
  stagioni-lega su 12, tutti e sei i gradini conclusivi. Ogni volta che cambia
  la fonte dei tassi (modello, apertura, chiusura, blend) **il θ del router va
  rifittato su quella fonte, non ereditato**.

## Passo 5 — Le leve della rosa, cella per cella

La matrice di `docs/PANCHINA.md` ha una colonna per la lega nuova: ogni cella
`⬜` è un test potenziale. Ordine di priorità:

1. leve **titolari** del motore nelle altre leghe (φ35 famiglia-pareggio,
   router θ) — decidono la configurazione operativa della lega e la voce in
   `MARKET_ENGINE`;
2. leve in **panchina** la cui promozione è condizionata a "riappare su
   un'altra lega";
3. covariate/ricalibrazioni a costo zero (colonne già nello snapshot).

Per ogni test: config ufficiale per-lega, walk-forward (default 6 stagioni di
test), bootstrap appaiato B=10.000, regola CI95<0, prior dall'EDA dichiarato
prima. **L'esito atteso più comune è la bocciatura** — va scritta comunque,
vale quanto un successo. Il conto aggiornato:

| onboarding | esito |
|---|---|
| Fase 79 (Premier, Liga) | 4/4 leve bocciate |
| Fase 80 | 1 leva su 3 leghe |
| **Fase 100 (Bundesliga, Ligue 1)** | router θ **0/25 mercati** con CI conclusivo in entrambe (e 2 / 4 mercati conclusivamente *peggiorati*); φ(\|λ−μ\|) nel rumore (peggiora la doppia 1X in Bundesliga); power-devig **peggiora con CI conclusivo** in Bundesliga; ricalibrazione per-classe e devig di Shin nel rumore; **6 covariate su 6** bocciate sul path DC; beat-the-close **chiuso** (§ sotto) |

**Il beat-the-close (`sharpen_1x2`) è chiuso fuori dalla Serie A**, e il perché
è la parte utile: la correzione dei livelli si scompone in **tilt** (parte
asimmetrica, bias-casa) e **scala** (parte simmetrica), e l'affinamento della
Serie A è quasi **puro tilt** (−0.0270) con θ≈1.23. Servono **entrambi** gli
ingredienti: da soli θ dà −0.0010 (non conclusivo) e il tilt +0.0002 (nulla),
insieme −0.0020 (conclusivo, 7/7). In Bundesliga il tilt è ≈0 (−0.0014) e tutta
la correzione è scala → peggiora con CI conclusivo (+0.0016 [+0.0004, +0.0027];
walk-forward +0.0026 [+0.0007, +0.0045]; Ligue 1 +0.0020 [+0.0001, +0.0039]).

**E il test che conta per l'utente, il ROI** (quote di chiusura reali, EV > 0,
walk-forward):

| lega | n scommesse | ROI | CI95 | puntare TUTTO (rif.) |
|---|--:|--:|---|--:|
| bundesliga | 427 | **−22,46%** | [−36,79%, −7,10%] | −4,66% |
| ligue_1 | 581 | **−12,90%** | [−23,21%, −2,20%] | −5,74% |
| serie_a | 924 | +0,75% | [−6,86%, +8,61%] | −7,41% |
| premier | 969 | −8,11% | [−19,50%, +3,90%] | −5,36% |

Nelle due leghe nuove seguire i «value bet» del modello perde **3-5 volte più in
fretta** che scommettere alla cieca, con CI conclusivo. Un affinamento di 2
millesimi di log-loss contro un margine del 4,5-5% **non è un edge economico**.

**Se la lega nuova ha un mercato outright** (campione di stagione,
`season_sim`), la baseline da battere non è l'uniforme: è **«vince la rosa più
cara»**. Su Bundesliga e Ligue 1 il simulatore non aggiunge nulla di
dimostrabile contro quella baseline, e sono le due leghe **più prevedibili** del
campione (entropia dell'esito campione 0.349 nats contro 1.311 della Serie A):
il modello *sembra* bravo dove la lega è già decisa, ed è *davvero* utile dove
non lo è.

## Le finestre di backtest (stagioni): come sceglierle

- **Training**: più storia è meglio, sempre (Fase 25: tagliare peggiora;
  l'emivita 365g gestisce già la recency). Non escludere nemmeno il COVID.
- **Test standard**: 6 stagioni (oggi 2021→2526) — abbastanza potenza, e
  CONFRONTABILE con tutti i numeri storici del progetto.
- **Estendere**: si può risalire fin dove i dati reali reggono (1920 per tutto
  ciò che usa la chiusura O/U — Fase 73; 1718 per la sola apertura/1X2, come
  Fase 75). Più stagioni = più potenza sui CI, MA epoche diverse (porte-chiuse,
  θ che cresce nel tempo, cambio di provider delle quote): dichiarare sempre la
  finestra e non mischiare confronti a finestre diverse.
- **Ridurre** (solo recenti): lecito per domande "com'è OGGI la lega", ma i CI
  si allargano — non trarre conclusioni forti da <3 stagioni (§1.7).
- Nei confronti CROSS-lega usare **finestre identiche** per tutte le leghe
  (come la Fase 80: 1920→2526 per tutte e tre, Serie A rifatta apposta; e la
  Fase 100, che ha rifatto le 5 leghe con la stessa finestra e lo stesso codice).
- **Attenzione al numero di partite, non solo di stagioni**: una lega a 18
  squadre dà 306 gare/stagione. Con ~2.100-2.300 partite per lega la **soglia di
  risoluzione** del bootstrap appaiato è **1-2 millesimi di log-loss**: sotto
  quella soglia «non dimostrato» **non** significa «dimostrato nullo» (R7). Va
  scritto ogni volta che si chiude una leva su una lega piccola.

## Cosa aspettarsi (le lezioni già pagate, da non ricomprare)

1. **La struttura trasferisce, l'edge no** — ora **5 leghe su 5**. Il DC batte
   sempre la baseline e non batte mai il mercato, con un gap in una forchetta
   stretta (+0.0162…+0.0207); il market-implied batte il DC-da-gol su 14-15
   mercati su 15 ovunque; le curve di ri-taratura sono piatte. Sotto-dispersione
   sfruttabile, dp_lvl e draw-bias restano idiosincrasie della Serie A.
   **Non c'è nulla di speciale nella Serie A, e non c'è nulla di rotto nelle
   leghe nuove.**
2. ~~**Più il book è liquido, meno c'è da spremere** (margine PL 4.3% → nessun
   bias; SA 4.9% → tutti i bias). Il tracer market-side (Passo 2) anticipa quasi
   tutto.~~
   > ⚠️ **SUPERATA dalla Fase 100.** L'ipotesi «θ decresce con la liquidità»
   > era **pre-registrata** dal progetto ed è stata **falsificata** su 5 leghe:
   > la Ligue 1 ha il margine **più alto** del campione (5.02%) e θ **basso**
   > (1.103); la Bundesliga ha un margine da Serie A (4.76% vs 4.87%) e θ da
   > Premier (1.080 vs 1.085). Correlazione θ↔margine **+0.299** sulle 5 leghe
   > (segno *opposto* a quello previsto, e con n=5 nulla è conclusivo); la
   > correlazione di rango fra margine mediano del book e θ MLE è **+0.10**, e
   > un pooled a due famiglie predetto dal margine non batte mai il pooled
   > semplice.
   > **Quello che regge al suo posto:** θ e il deficit-pareggio sono la stessa
   > cosa vista da due angoli — corr(θ, φ0) = **+0.755** sulle 5 leghe. Un θ>1
   > (gol sotto-dispersi) produce più pareggi e meno punteggi estremi di quanto
   > la matrice del mercato preveda: esattamente ciò che φ(|λ−μ|) corregge. Le
   > due famiglie **esistono** (latine ≈1.24 / le altre ≈1.08-1.10) ma **non
   > sono predicibili dal margine**: vanno misurate. La Bundesliga è l'unico
   > caso intermedio (θ basso, φ0 medio) ed è il posto giusto dove indagare se
   > si vorrà separare i due effetti.
3. **Il pareggio è la dimensione più per-lega che esista**: deficit latino vs
   assenza inglese. Il numero dipende dal **percorso** su cui si fitta, e i due
   non vanno confusi: sul **path DC** φ0 ≈ 0.39 in Serie A e La Liga contro
   0.00 (bound) in Premier (Fasi 35/79); sul **path mercato**, LOSO 7 stagioni
   (Fase 100), φ0 = 0.2433 (SA) / 0.2461 (Liga) / 0.0341 (Premier) / **0.1827
   (Bundesliga)** / **0.0000 (Ligue 1)**. Ogni leva-pareggio va ri-fittata, mai
   copiata. E su percorso market-implied a 6 stagioni la φ35 non è conclusiva
   **in nessuna delle 5 leghe**, Serie A compresa: il segno è giusto nelle
   latine, l'ampiezza è sotto la soglia di risoluzione.
4. **Il pari/dispari non si predice in nessuna lega** — **6 repliche**: non
   prezzarlo con pretese.
5. **Le covariate (congestione, forma, rose…) sono rumore ovunque**: il fit
   pesato nel tempo le assorbe (Fase 100: 6 covariate su 6 bocciate anche sulle
   leghe nuove). Riprovarle su una lega nuova solo con una ragione strutturale
   forte (es. una lega con calendario estremo).
6. **Il dato può essere sbagliato *alla fonte*, e il modo peggiore è il finto
   pieno** (R6). Su una lega appena importata cercarlo **esplicitamente**: è il
   solo difetto che il confronto con la fonte non vede.
7. **Un «non c'è effetto» vale solo con la sua misura di potenza** (R7). Su
   ~2.000 partite per lega la risoluzione è 1-2 millesimi: si scrive «non
   dimostrato», non «dimostrato nullo» — tranne quando il CI **esclude**
   l'effetto atteso, e allora lo si dice (caso raro: il beat-the-close in
   Bundesliga).
8. **Le regole di classifica e di spareggio sono un dato di lega** e vanno prese
   dal regolamento ufficiale, con un test che ne distingua il comportamento
   (Passo 3-bis).

## Checklist di chiusura

### Dati (una volta, alla fine del Passo 0-bis)

- [ ] snapshot a 40 colonne, **nomi e ordine** identici alle altre leghe
      (`test_schema_identico_tra_leghe`);
- [ ] manifest di provenienza (URL, timestamp, byte, SHA256) dei grezzi;
- [ ] audit livelli A-B-C-D eseguito: **0 differenze** contro la fonte
      ri-scaricata, gol confermati da fonte indipendente;
- [ ] guard **overround bilaterale** (`ORR_MAX = 1.12`) e **xG segnaposto**
      verificati sulla lega nuova, con i rispettivi test verdi;
- [ ] ogni correzione in `data/correzioni_dichiarate.csv` + applicata da
      `scripts/applica_correzioni.py` (R3); **nessuna modifica a mano**;
- [ ] anomalie dichiarate **anche quelle che non sono errori** (R4), e i falsi
      positivi ritirati **con la storia**, non cancellati;
- [ ] `docs/DATI.md`: coperture, semantica, lacune;
- [ ] tutte le **mappe per-lega** del Passo 3-bis riempite, ognuna col suo test
      di copertura (`LEAGUE_CONFIGS`, `MARKET_ENGINE`, `TIEBREAK_RULES`, …).

### Per OGNI esperimento della lega nuova

- [ ] run in `experiments/runs.jsonl` (nessuna analisi senza run);
- [ ] `docs/DIARIO.md`: fase con blocco 📐 (formule verificate sul sorgente +
      perché di ogni numero);
- [ ] `README.md`: riga nel «Registro completo dei risultati»;
- [ ] `docs/PANCHINA.md`: celle della matrice aggiornate (+ voci di dettaglio,
      condizioni di promozione), su **entrambi** i fronti (per-lega e generale,
      §1.9);
- [ ] quaderno di studio della lega: risultati + tabella differenze;
- [ ] intervallo di confidenza su ogni statistica di testa, e misura di potenza
      su ogni «non c'è effetto» (R7);
- [ ] `docs/PISTE.md` / `docs/DATI.md` / questo playbook se cambia il metodo;
- [ ] `pytest` verde; commit + push (container effimero).

---

*Creato alla Fase 80 (luglio 2026), dopo l'onboarding completo di Premier League
e La Liga. **Aggiornato alla Fase 101-ter (27 luglio 2026)** incorporando
l'onboarding di Bundesliga e Ligue 1 (Fase 100), che è il primo ad averlo usato
come procedura: da lì vengono il Passo 0-bis (verifica contro la fonte-madre),
il Passo 3-bis (le mappe per-lega e gli spareggi), le regole R1-R7 e la
falsificazione della lezione §2. Se il metodo cambia (nuove fonti, nuovi passi),
aggiornare QUESTO file oltre al CLAUDE.md: è il punto d'ingresso per ogni lega
futura.*
