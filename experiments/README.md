# Registro degli esperimenti

Questa cartella contiene il **log strutturato e verificabile** di tutti i backtest
eseguiti. Serve a rendere i risultati **replicabili** e **controllabili** anche in
futuro, da noi o da terzi/AI esterne: chiunque deve poter ricostruire come è stato
ottenuto un numero.

## `runs.jsonl`

Un record JSON per riga (formato JSON Lines), aggiunto in append ad ogni run di
`scripts/backtest.py` e `scripts/tune.py`, e dagli script di fase (`scripts/_run_*.py`,
riconoscibili dal campo `config.source`, es. `fase7_promosse`, `fase11_combo`,
`fase12a_ensemble`, `fase13_form`; regola dall'audit di Fase 15: **nessuna
analisi senza run nel registro**). Ogni record contiene:

| campo | significato |
|---|---|
| `timestamp` | data/ora UTC del run |
| `git_commit` | commit del codice usato (per riprodurre lo stesso software) |
| `data_fingerprint` | impronta SHA dei dati usati (per accorgersi se la fonte a monte è cambiata) |
| `config` | configurazione: campionato, stagione di test, emivita, shrinkage, shots_blend, ... |
| `metrics` | metriche calcolate: log-loss/Brier di modello, mercato e baseline (1X2 e O/U); ROI value-bet |

### Come rileggere il log

```python
import json
runs = [json.loads(l) for l in open("experiments/runs.jsonl")]
# es. tutti i backtest della stagione 2025-26 ordinati per log-loss 1X2
#
# NB: il registro NON e' omogeneo — accanto ai backtest ci sono tuning, sweep e
# run diagnostici con config e metriche diverse. Su 747 run, 182 non hanno
# `test_season` e 174 non hanno `x2_model_logloss`: si accede sempre con .get(),
# mai con la parentesi quadra. (Lo snippet precedente usava le quadre e
# sollevava KeyError alla prima riga senza quella chiave.)
r = [x for x in runs if x.get("config", {}).get("test_season") == "2526"
     and "x2_model_logloss" in x.get("metrics", {})]
r.sort(key=lambda x: x["metrics"]["x2_model_logloss"])
```

### Replicabilità

Per riprodurre esattamente un record: fare `git checkout <git_commit>`, verificare
che `data_fingerprint` coincida (i dati grezzi si riscaricano con
`scripts/download_data.py`), e rilanciare il backtest con la stessa `config`.
Se il `data_fingerprint` non coincide, la fonte dati a monte è cambiata: è il
segnale che serve congelare i dati (vedi l'idea del database interno nel README).

Il file è versionato in git: è parte del valore del progetto, non un artefatto
temporaneo.
