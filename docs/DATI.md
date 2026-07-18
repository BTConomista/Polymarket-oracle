# Catalogo dei dati — tutto ciò che il progetto ha a disposizione

Questo documento è la **mappa unica di tutti i dati** del progetto: cosa c'è,
da dove viene, quanto copre, e — sezione più importante — **cosa è dato reale e
cosa è STIMA**. Va aggiornato ogni volta che i dati cambiano (nuova fonte,
nuova colonna, nuova stima). Ultimo aggiornamento: **Fase 67**.

> Regola d'oro del progetto: **mai un numero inventato spacciato per dato**.
> Dove un dato manca, o resta `NaN` (dichiarato), oppure viene stimato e
> pubblicato **separatamente** con l'etichetta di stima (vedi [§5](#5--stime-dichiarate-dataestimates)).

---

## 1 · Gli snapshot partita (la fonte di verità)

Tre file **versionati in git** — chi clona il repo ha esattamente gli stessi
dati, senza rete (offline-first, §5 del CLAUDE.md):

| file | partite | stagioni | colonne |
|---|--:|--:|--:|
| `data/serie_a_matches.csv` | 3420 | 9 (2017-18 → 2025-26) | 38 |
| `data/premier_league_matches.csv` | 3420 | 9 | 38 |
| `data/la_liga_matches.csv` | 3420 | 9 | 38 |

Lo **schema è identico** su tutte e tre le leghe (dalla Fase 60). Chiave di
partita in tutto il progetto: `(season, home_team, away_team)`, nomi squadra
canonicalizzati via `sources.TEAM_ALIASES`.

### Le 38 colonne, per gruppo

| gruppo | colonne | fonte | copertura |
|---|---|---|---|
| partita | `date, season, league, home_team, away_team` | football-data | 100% |
| esito | `home_goals, away_goals, result` | football-data | 100% |
| tiri in porta | `home_sot, away_sot` | football-data | 100% |
| **quote chiusura** | `odds_home/draw/away, odds_over25/under25` | football-data (vedi §2) | 100% |
| **quote apertura** | `odds_*_open` (5 colonne) | football-data (vedi §2) | 1X2: ~100% · O/U: 77.8% (**manca 2017-19**, vedi §5) |
| xG | `home/away_xg, home/away_npxg` | Understat | 100% |
| stile | `home/away_ppda, home/away_deep` | Understat | 100% |
| valore rosa | `home/away_squad_value` | **player-scores** (Transfermarkt via Kaggle, Fase 67; vedi §4) | **100% su tutte le stagioni concluse** (3 leghe); buchi onesti solo nella 2025-26 in corso (48-81%) → stime in §5 |
| assenze (STIMA, suffisso `_est`) | `home/away_absent_count_est, home/away_absent_value_est` | Transfermarkt + rose Understat | 100% (ma è una **stima dichiarata**, vedi §4) |
| congestione | `home/away_rest_days_full, home/away_midweek_europe` | openfootball + snapshot | ~99.5% (NaN solo alla prima partita nota di una squadra) |

---

## 2 · Semantica delle quote: apertura vs chiusura (leggere PRIMA di usarle)

Due istantanee per mercato: **apertura** (`*_open`, raccolta giorni prima
della partita, tipicamente il venerdì) e **chiusura** (al calcio d'inizio, lo
stimatore di mercato più efficiente). La provenienza **cambia con la
stagione** — questa tabella vale per tutte e 3 le leghe:

| stagioni | chiusura 1X2 | apertura 1X2 | chiusura O/U | apertura O/U |
|---|---|---|---|---|
| 2017-18, 2018-19 | **Pinnacle** (`PSC*`, Fase 61) | **Pinnacle** (`PS*`) | media pre-match (`BbAv`) ⚠️ *timing apertura* | **ASSENTE** → stima in §5 |
| 2019-20 → 2025-26 | media di ~10 book (`AvgC*`) | media pre-match (`Avg*`) | media chiusura (`AvgC>2.5`) | media pre-match (`Avg>2.5`) |

Note importanti:
- Nel 2017-19 la coppia apertura/chiusura 1X2 è **Pinnacle→Pinnacle** (margine
  ~2.5%, più basso della media ~4.9%): CLV pulito, stesso book.
- ⚠️ Nel 2017-19 la colonna `odds_over25/under25` contiene l'**unica linea O/U
  esistente** nelle fonti: una **pre-match** (timing "apertura") che occupa lo
  slot della chiusura. La chiusura O/U vera **non esiste nei dati** — per le
  analisi che ne hanno bisogno c'è la **stima** (§5).
- Regola anti-contaminazione (Fasi 14/15): `*_open` non ripiega **mai** sulla
  chiusura; overround < 1 (arbitraggio impossibile) → ripiego in blocco sul
  livello di preferenza successivo (Fase 58).
- Devig: **sempre** via `metrics.devig_1x2` / `devig_binary` (fonte unica).

---

## 3 · Calendari di club (congestione vera)

Una riga per (squadra, partita di club, qualsiasi competizione) — alimentano
`rest_days_full` / `midweek_europe`:

| file | righe | competizioni oltre il campionato |
|---|--:|---|
| `data/club_fixtures.csv` (Serie A) | 7676 | Champions (9 stagioni), Europa L. (dal 20-21), Conference (dal 21-22), Coppa Italia (20-21→24-25) |
| `data/club_fixtures_premier_league.csv` | 8335 | idem UEFA + **FA Cup, EFL Cup** (18-19→24-25) |
| `data/club_fixtures_la_liga.csv` | 7669 | idem UEFA + **Copa del Rey** (20-21→24-25) |

Dove una competizione non è coperta, `rest_days_full` degrada verso il valore
solo-campionato (mai in direzione sbagliata) e `midweek_europe` può essere un
falso 0: lacune **dichiarate**, nessun numero inventato.

---

## 4 · Fonti grezze congelate e loro limiti

| fonte | dove | stato |
|---|---|---|
| football-data (Serie A, CSV originali completi) | `data/football_data_raw/` (versionata) | ✅ congelata; il sito originale non è raggiungibile dal cloud |
| football-data (Premier/Liga) | `files/football_data_*_bundle.json` (caricati a mano, Fase 54) | ✅ congelata |
| Understat (xG + rose giocatori) | `files/understat_*_bundle.json` (Premier/Liga); Serie A: **solo lo snapshot** | ⚠️ il mirror per-stagione è **sparito** (Fase 14): le rose Serie A NON sono rigenerabili — `--enrich`/ri-matching valgono solo per Premier/Liga finché non viene caricato un bundle Understat Serie A (come Fase 54) |
| **player-scores** (valutazioni complete + presenze/rose, 3 leghe) | `files/player_scores/*.csv.gz` (versionati; import via **workflow GitHub Actions** `.github/workflows/import_dataset.yml` — il runner ha rete libera, l'ambiente cloud no) | ✅ fonte UFFICIALE dei valori rosa dalla Fase 67 (CC0, `dcaribou/transfermarkt-datasets`); rigenerabile: push di `.github/import-dataset-trigger` |
| Transfermarkt (datalake `salimt`) | mirror GitHub, cache `data/raw/` (~106 MB, non versionata) | ✅ raggiungibile; dalla Fase 67 usato SOLO per gli infortuni (`absent_*_est`) — per i valori rosa e' superato da player-scores |
| openfootball (coppe/Europa) | cache `data/raw/fixtures_*` | ✅ raggiungibile |

**Limiti noti dei dati reali** (dichiarati, non aggirati):
- `squad_value`: pubblicato solo se i giocatori valutati coprono ≥85% dei
  minuti della squadra, altrimenti `NaN`. Dalla Fase 67 (fonte player-scores)
  la soglia è quasi sempre superata: i soli `NaN` residui sono 13 celle della
  stagione in corso 2025-26 (valutazioni di inizio stagione non ancora
  complete a monte). **Niente imputazioni** — per quelle 13 c'è la stima (§5).
- `absent_*_est`: già una **stima dichiarata** nel nome (rosa ricostruita dai
  minutaggi Understat + storico infortuni TM): usarla come indicazione, non
  come verità di formazione.
- O/U 2017-19: vedi §2 e §5.
- `rest_days_full`: `NaN` alla prima partita nota di una squadra (fisiologico).

---

## 5 · ⚠️ STIME dichiarate (`data/estimates/`)

Dove un dato di mercato **non esiste nelle fonti**, il progetto può stimarlo
coi propri modelli — ma la stima vive **fuori dagli snapshot**, in
`data/estimates/`, come **probabilità** (mai quote: impossibile confonderla
con un prezzo). Regole complete in [`data/estimates/README.md`](../data/estimates/README.md);
le tre che contano:

1. **non farci troppo affidamento** — l'errore atteso è misurato e dichiarato;
2. **ogni analisi che le usa lo dichiara** (diario + `runs.jsonl`);
3. **mai** dentro le colonne quota degli snapshot, **mai** per simulare ROI.

### Stime attualmente pubblicate

| file | cosa stima | metodo | errore atteso (validato walk-forward) |
|---|---|---|---|
| `ou_close_2017_19.csv` (2279 righe, 3 leghe) | la **chiusura O/U 2.5** delle stagioni 2017-18/2018-19, assente nelle fonti | regressione logit della chiusura su (linea O/U pre-match + movimento 1X2 open→close), fit pooled su 7978 partite 2019-20+ (Fasi 62/62-bis) | **MAE ~0.012** in probabilità; corr col movimento vero 0.75-0.86; ~35-45% del movimento resta incatturabile (notizie puro-totali) |
| `squad_value_2017_26.csv` (**13 righe** — erano 73, 60 sostituite da dati REALI nella Fase 67; tutte 2025-26) | il **valore rosa** delle celle (stagione, squadra) ancora scoperte | ibrido validato LOO/leave-team-out (Fase 66): `anchored` = regressione pooled + valore stagioni adiacenti; `regression` = solo rendimento, per-lega (squadre senza stagioni note) | **mediano ~17%** (anchored) / **~29%, p90 75%** (regression) — ⚠️ ordine di grandezza, code >100% per squadre sovra-performanti; metodo+errore riga per riga |

Accesso da codice: `loader.read_ou_close_estimates()`. Rigenerazione:
`python scripts/build_estimates.py`.

### Candidati FUTURI a stima (promemoria, richiesti dall'utente)

Da valutare **solo** con lo stesso protocollo (backtest di fedeltà su dati
dove la verità esiste → errore atteso dichiarato → pubblicazione separata):

- ~~**`squad_value` mancante**~~ → **FATTO (Fase 66)**: le 73 celle sono ora
  stimate in `squad_value_2017_26.csv` (vedi tabella sopra). Migliorabile solo
  con una fonte valutazioni migliore, non con altro modeling.
- **apertura O/U 2017-19** (l'altra metà del buco di §2): meno utile — la
  linea unica disponibile È già di timing apertura.
- **quote O/U di apertura mancanti sparse** (1 partita 21-22 SA, 1 Liga 17-18).
- eventuali linee di mercati mai pubblicati (GG/NG storico): molto più
  incerto, servirebbe una validazione esterna.

---

## 6 · Come si rigenera tutto (riproducibilità)

```bash
# Serie A
python scripts/_restore_raw_cache.py          # data/football_data_raw/ -> data/raw/
python scripts/build_database.py              # DB dallo snapshot (offline)
python scripts/build_database.py --refresh-odds   # ricalcola le 10 colonne quota
python scripts/build_database.py --fixtures   # calendario club + congestione
python scripts/build_database.py --enrich     # xG/rose/assenze (rete: TM)

# Premier League / La Liga (dai bundle in files/, offline salvo dove indicato)
python scripts/build_league_snapshot.py                    # snapshot base
python scripts/build_league_snapshot.py --refresh-odds     # quote
python scripts/build_league_snapshot.py --fixtures         # congestione (rete: openfootball)
python scripts/build_league_snapshot.py --enrich           # rose/assenze (rete: TM)

# Stime dichiarate
python scripts/build_estimates.py             # data/estimates/ (offline)
```

Ogni backtest/analisi è registrato in `experiments/runs.jsonl` con l'impronta
dei dati usati; le decisioni e il perché sono nel [diario](DIARIO.md).
