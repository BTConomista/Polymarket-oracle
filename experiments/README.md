# Registro degli esperimenti

Questa cartella contiene il **log strutturato e verificabile** dei backtest
eseguiti, più gli **artefatti congelati** delle fasi che ne producono (JSON/CSV).
Serve a rendere i risultati **replicabili** e **controllabili** anche in futuro,
da noi o da terzi/AI esterne: chiunque deve poter ricostruire come è stato
ottenuto un numero.

## Cosa c'è in questa cartella

| file | cosa contiene |
|---|---|
| `runs.jsonl` | **il registro**: un record JSON per riga, uno per run (formato sotto) |
| `prospettico_2026_27.md` | il test prospettico 2026-27 (Fase 78) — **APERTO**, è il gold standard |
| `prospettico_2026_27_dc.csv` | anteprima DC congelata il 2026-07-23 (λ,μ + mercati, `note=anteprima_illustrativa`) |
| `prospettico_2026_27_outright.json` | previsioni outright **congelate il 2026-07-25** (`fonte_prezzi`, `nota`, `leghe`) |
| `fase89_season_champion.json` | backtest del simulatore di stagione (chiavi `backtest`, `report`, `pred_2627`) |
| `fase89bis_anatomy.json` | anatomia del simulatore (`anatomy`, `temperature`, `drift`) |
| `fase91_positions.json` | mercati posizionali top-4/retrocessione (`rows`, `report`) |
| `fase93_discrimination.csv` | deficit di discriminazione **per partita** (5.083 righe) — input riutilizzabile |
| `fase93_discrimination.json` | le stesse fette aggregate (per squilibrio, disaccordo, lega, stagione, …) |
| `fase94_drift.json` | griglia della deriva di forza in-stagione (chiavi = `drift_sd` provati) |
| `listino_validazione.json` | validazione del listino (`meta`, `livelli`, `folds`, `handicap_asiatico_dettaglio`, …) |

Tutti sono versionati in git: sono parte del valore del progetto, non artefatti
temporanei.

---

## `runs.jsonl` — il formato REALE

Un record JSON per riga (formato JSON Lines), aggiunto in append da
`scripts/backtest.py`, `scripts/tune.py` e dagli script di fase
(`scripts/_run_*.py`, riconoscibili dal campo `config.source`, es.
`fase7_promosse`, `fase11_combo`, `fase12a_ensemble`, `fase13_form`; regola
dall'audit di Fase 15: **nessuna analisi senza run nel registro** — vedi però i
limiti dichiarati in fondo). Il record è costruito da
`src/evaluation/experiment_log.py::make_record` e scritto da `append_run`.

**Stato del file al 2026-07-27** (misurato: 747 righe, dalla prima del
`2026-07-09T16:42:42+00:00` all'ultima del `2026-07-27T17:54:08+00:00`).

### Campi di primo livello

| campo | presente su | significato |
|---|--:|---|
| `timestamp` | 747/747 | data/ora UTC del run (ISO 8601, secondi) |
| `git_commit` | 747/747 | commit del codice usato (per riprodurre lo stesso software) |
| `data_fingerprint` | **746**/747 | impronta SHA dei dati usati (per accorgersi se la fonte a monte è cambiata) |
| `config` | 747/747 | configurazione del run (dizionario, chiavi variabili — sotto) |
| `metrics` | 747/747 | metriche calcolate (dizionario, chiavi variabili — sotto) |
| `note` | 4/747 | testo libero, aggiunto da alcuni script di fase |
| `phase`, `script` | 1/747 | fase e script d'origine, in un solo record storico (gli altri li mettono dentro `config`) |

L'unico record **senza `data_fingerprint`** è il *primo* backtest del simulatore
di stagione (Fase 89, `config.model = "dixon_coles+montecarlo_stagione"`), scritto
prima che lo script calcolasse l'impronta. Il secondo record della stessa fase ce
l'ha: `_run_fase89_season_champion.py` la costruisce concatenando l'impronta di
ogni lega (`"lega:sha|lega:sha|…"`), perché il run è multi-lega e non parte da un
solo DataFrame. **Quel record non è quindi verificabile contro i dati**: è
l'eccezione, ed è dichiarata.

### `config` — 92 chiavi distinte in tutto il registro

Non esiste un insieme fisso: ogni script mette ciò che serve a riprodursi. Le più
frequenti (conteggio su 747 run):

| chiave | run | significato |
|---|--:|---|
| `source` | 719 | chi ha scritto il record (`tune.py`, `fase26_market_implied`, …) |
| `league` | 677 | lega singola (`serie_a`, `premier_league`, `la_liga`, `bundesliga`, `ligue_1`) |
| `half_life_days`, `shots_blend`, `shrinkage` | 570 | iperparametri del Dixon-Coles |
| `test_season` | 565 | stagione di test (`"2526"`, …) |
| `blend_signal` | 551 | segnale del blend (`xg`/`shots`) |
| `promoted_prior` | 417 | δ di cold-start delle neopromosse (per-lega, `src/config.py`) |
| `covariates` | 255 | covariate attive |
| `variant` | 169 | variante dell'esperimento (es. `ci_summary`) |
| `seasons` | 90 | elenco di stagioni, quando il run non è su una sola |
| `leagues` | 7 | elenco di leghe, per i run multi-lega (`config.league` allora manca) |
| `phase`, `script` | 3 | convenzione più recente (Fasi 89/91/94): fase e script d'origine dentro `config` |

63 run non hanno **né** `league` **né** `leagues` (tuning e diagnostiche che non
sono legate a una lega). **182 run non hanno `test_season`**: è la ragione per cui
si legge sempre con `.get()` (vedi snippet).

### `metrics` — 1.600 chiavi distinte in tutto il registro

Il blocco "canonico" è quello prodotto da `experiment_log.compute_metrics` (fonte
di verità unica per il calcolo delle metriche: log-loss/Brier di modello, mercato
e baseline su 1X2 e O/U 2.5, più ROI value-bet illustrativo). Presenze misurate:

| chiave | run | note |
|---|--:|---|
| `n_matches` | 655 | partite del run |
| `x2_model_logloss` / `x2_model_brier` | 573 / 565 | modello, 1X2 |
| `x2_market_*`, `x2_baseline_*`, `ou_*`, `value_bet_n`, `value_bet_roi_pct` | 547 | il resto del blocco canonico |
| `x2_market_open_*`, `x2_model_open_*`, `ou_*_open_*`, `value_bet_open_*`, `clv_*` | 204 | blocco **linea di apertura** (Fase 14), presente solo se il df ha le colonne `*_open` |

Tutte le altre chiavi (curve di sweep, IC bootstrap, tabelle per-lega, …) sono
specifiche del singolo script di fase: si leggono guardando il record, non
assumendo uno schema.

> ⚠️ **Il registro NON è omogeneo.** Accanto ai backtest ci sono tuning, sweep e
> run diagnostici con `config` e `metrics` diverse. Qualunque codice che lo
> rilegge deve usare `.get()` e filtrare per chiave presente, mai indicizzare
> con le parentesi quadre.

---

## Come rileggere il log

Lo snippet qui sotto è **eseguito e verificato** (rende 100 run al 2026-07-27):

```python
import json

runs = [json.loads(l) for l in open("experiments/runs.jsonl")]

# es. tutti i run della stagione di test 2025-26 che hanno il log-loss 1X2,
# ordinati dal migliore al peggiore.
#
# NB: su 747 run, 182 non hanno `test_season` e 174 non hanno
# `x2_model_logloss`: si accede sempre con .get(), mai con la parentesi quadra.
# (Una versione precedente di questo snippet usava le quadre e sollevava
# KeyError alla prima riga senza quella chiave.)
r = [x for x in runs
     if x.get("config", {}).get("test_season") == "2526"
     and "x2_model_logloss" in x.get("metrics", {})]
r.sort(key=lambda x: x["metrics"]["x2_model_logloss"])

for x in r[:5]:
    print(x["config"].get("source"), x["config"].get("league"),
          round(x["metrics"]["x2_model_logloss"], 4))
```

---

## Replicabilità

Per riprodurre esattamente un record: fare `git checkout <git_commit>`, verificare
che `data_fingerprint` coincida (i dati grezzi si riscaricano con
`scripts/download_data.py`), e rilanciare il backtest con la stessa `config`.
Se il `data_fingerprint` non coincide, la fonte dati a monte è cambiata: è il
segnale che serve congelare i dati (gli snapshot in `data/*_matches.csv` sono
esattamente questo).

**Attenzione al `git_commit`.** Il registro copre commit diversi: un numero
misurato prima del fix del prior della Fase 92 **non** è confrontabile a mente con
uno misurato dopo (è il caso del gap 1X2 Serie A: `+0.0165` PRE-fix, `+0.0167` al
codice di HEAD). Confrontare sempre run dello stesso commit, o rifare la misura.

## Limiti dichiarati del registro

Onestà su cosa il registro **non** copre (principio §1.4 del `CLAUDE.md`:
si documentano anche i buchi):

- l'ultima fase con un `config.source` proprio è **`fase82_verifica_predizioni`**.
  Delle fasi successive solo **89, 91 e 94** hanno lasciato un record (via
  `config.phase`); le altre hanno prodotto **artefatti JSON/CSV in questa
  cartella** invece di righe nel registro. La regola della Fase 15 («nessuna
  analisi senza run») è quindi **rispettata in sostanza ma non nella forma** per
  quelle fasi: i numeri sono ricalcolabili dagli script `_run_*` e dai JSON, non
  interrogabili con una query sul registro. È un debito noto, da sanare
  registrando i run mancanti — non da nascondere;
- le metriche di `compute_metrics` usano una baseline **in-sample** (frequenze
  della stagione di test stessa), mantenuta per continuità con lo storico: è
  documentato nel commento del codice (`experiment_log.compute_metrics`) ed è una
  scelta **conservativa** per il modello;
- il ROI value-bet nel registro è **illustrativo**: un backtest storico
  sovrastima quasi sempre la redditività reale. Non usarlo per decidere di
  scommettere.
