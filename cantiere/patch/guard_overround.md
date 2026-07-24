# Proposta di patch — guard sull'overround TROPPO ALTO

**Non applicata**: il lavoro di questa sessione non tocca `src/`. Da valutare
all'integrazione. Motivazione completa: `cantiere/report/01_audit_dati.md` §4.1.

## Il problema

`src/data/loader._pick_market_odds` (Fase 58) protegge da **un solo lato**:

```python
if sum(1.0 / v for v in picks.values()) < 1.0:      # overround < 1 = arbitraggio
    ... ripiego in blocco sul livello successivo, altrimenti NaN
```

Un overround **impossibilmente alto** passa invece indisturbato. Nei dati ce ne
sono **11 casi**, tutti nella linea O/U pre-match delle stagioni 2017-19
(sorgente `BbAv`, Betbrain): overround fino a **1.339**, cioè il 34% di margine
su un mercato binario. Diagnosi (Report 1 §4.1): in ogni caso il **lato Under**
è incompatibile con l'1X2 della stessa partita — le due quote non appartengono
alla stessa linea.

## La soglia, e perché

Distribuzione dell'overround O/U su tutte e 5 le leghe:

| epoca | n | mediana | p99.9 | max |
|---|--:|--:|--:|--:|
| 2017-19 (`BbAv`) | 3.651 | 1.0553 | 1.28 | **1.339** |
| 2019-20+ (`Avg`) | 12.457 | 1.0511 | 1.0757 | **1.0765** |

Nell'era sana il massimo assoluto su 12.457 righe è **1.0765**. Una soglia a
**1.12** sta ~6 deviazioni oltre la mediana e oltre 4 punti percentuali sopra il
massimo mai osservato in condizioni normali: non può scartare una riga buona.
Stesso ragionamento per l'1X2 (3 vie): massimo osservato 1.080.

## La modifica

```python
# src/data/loader.py
ORR_MAX = 1.12   # margine impossibile per una media multi-book (audit 2026-07):
                 # ~6 sigma oltre la mediana sana; il massimo mai osservato
                 # nell'era Avg (12.457 righe, 5 leghe) e' 1.0765.

def _pick_market_odds(row, targets, preference):
    picks = {t: _pick_odds(row, preference[t]) for t in targets}
    if all(pd.notna(v) for v in picks.values()):
        orr = sum(1.0 / v for v in picks.values())
        if orr < 1.0 or orr > ORR_MAX:          # <-- unica riga cambiata
            retry = {t: _pick_odds(row, preference[t][1:]) for t in targets}
            orr_r = (sum(1.0 / v for v in retry.values())
                     if all(pd.notna(v) for v in retry.values()) else None)
            if orr_r is not None and 1.0 <= orr_r <= ORR_MAX:
                picks = retry
            else:
                picks = {t: float("nan") for t in targets}
    return picks
```

## Effetto atteso

- **11 celle** su 15.788 partite (0.07%) passano da valore impossibile a **NaN
  dichiarato**: 3 La Liga, 6 Bundesliga, 2 Ligue 1, tutte in `odds_over25_open`/
  `odds_under25_open` del 2017-19;
- **3 stime** di `data/estimates/ou_close_2017_19.csv` spariscono da sole
  (`build_estimates.py` salta le righe senza input): erano fuori bersaglio di
  6-10 punti di probabilità, contro un MAE dichiarato di 0.012;
- nessun'altra riga cambia: verificato che nell'era `Avg` nessuna riga supera
  la soglia.

## Test da aggiungere

```python
def test_overround_impossibile_scartato():
    """Un mercato binario con margine impossibile non entra nello snapshot."""
    row = pd.Series({"Avg>2.5": 1.53, "Avg<2.5": 1.59})   # overround 1.28
    picks = loader._pick_market_odds(
        row, ["odds_over25_open", "odds_under25_open"], loader._ODDS_PREFERENCE_OPEN)
    assert all(pd.isna(v) for v in picks.values())
```

## Verifica dopo l'applicazione

```bash
python scripts/build_database.py --refresh-odds        # Serie A
python scripts/build_league_snapshot.py --refresh-odds # Premier/Liga
python scripts/build_estimates.py                      # le 3 stime cadono
python cantiere/scripts/audit_anomalie.py              # atteso: 0 margini impossibili
```
