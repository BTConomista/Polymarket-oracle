# Polymarket Oracle

Motore di stima delle **probabilità reali di eventi sportivi** (calcio),
**indipendente dalle piattaforme** di scommessa.

Il valore del progetto è il **modello di previsione**, non l'integrazione con una
piattaforma specifica. Il motore stima la distribuzione dei gol di una partita; da
quella distribuzione si derivano in modo coerente tutti i mercati (1X2,
Over/Under, ecc.). Solo in un secondo momento il motore potrà essere collegato a
Polymarket, bookmaker, exchange o altri mercati di previsione.

## Stato attuale — Fase 1 (tracer bullet)

Prima pipeline **end-to-end** funzionante su **Serie A**:

`dati storici → modello Dixon-Coles → probabilità 1X2 e Over/Under 2.5 → validazione`

- **Modello**: Dixon-Coles (1997) con decadimento temporale, implementato da zero
  (`src/models/dixon_coles.py`). Stima forza d'attacco/difesa di ogni squadra +
  vantaggio-casa + correzione sui punteggi bassi.
- **Dati**: 9 stagioni di Serie A (2017-18 → 2025-26) in formato football-data.co.uk.
- **Validazione**: backtest walk-forward sulla stagione 2025-26 (riallenamento
  settimanale, **senza look-ahead**), con Brier score e log-loss, confronto contro
  le quote di chiusura dei bookmaker e contro una baseline banale.

### Risultati del backtest (stagione 2025-26, 380 partite)

| Mercato | Metrica | Modello | Baseline | Mercato (chiusura) |
|---|---|---:|---:|---:|
| **1X2** | log-loss | 1.0047 | 1.0851 | **0.9784** |
| **1X2** | Brier | 0.6004 | 0.6579 | **0.5830** |
| **O/U 2.5** | log-loss | 0.7155 | 0.6896 | **0.6996** |
| **O/U 2.5** | Brier | 0.2599 | 0.2482 | **0.2530** |

**Come leggerli** (più bassi = meglio):

- Sull'**1X2** il modello **batte nettamente la baseline** (impara qualcosa di
  reale) e si avvicina al mercato, ma **non lo batte**. È il risultato atteso e
  sano per un primo modello semplice: le quote di chiusura sono lo stimatore più
  efficiente che esista.
- Sull'**Over/Under 2.5** il modello è vicino al mercato ma **non aggiunge valore**
  rispetto a "scommetti sulla frequenza media" (baseline). L'O/U è un mercato
  quasi 50/50, difficile da battere senza feature più ricche.
- La simulazione di *value betting* dà **ROI ≈ -8.5%**: un modello che non batte
  la linea di chiusura **perde soldi** contro il margine del bookmaker. Onesto e
  prevedibile a questo stadio.

**Conclusione**: la pipeline funziona e il modello è valido *come modello*, ma non
ha ancora un vantaggio sul mercato. Il prossimo lavoro (feature engineering) serve
a colmare quel divario. **Non usare questo modello per scommettere soldi veri.**

## Struttura

```
src/
  data/         raccolta e normalizzazione dati (schema interno pulito)
    sources.py    UNICO punto con URL e stagioni (cambiare fonte = 1 riga)
    loader.py     download + parsing + normalizzazione
  models/
    dixon_coles.py   il modello (stima + predizione)
  evaluation/
    metrics.py    Brier, log-loss, devigging quote, baseline
scripts/
  download_data.py   scarica i CSV (cache in data/raw/)
  backtest.py        esegue il backtest walk-forward e stampa il report
tests/              test unitari del modello e delle metriche
worldcup/           esperimento parallelo a bassa priorità (Mondiali)
```

## Come si usa

```bash
pip install -e .            # oppure: pip install numpy pandas scipy pytest

python scripts/download_data.py     # scarica i dati storici (una volta)
python scripts/backtest.py          # esegue il backtest sulla stagione 2025-26
python -m pytest                    # esegue i test
```

Opzioni utili del backtest:

```bash
python scripts/backtest.py --half-life-days 120   # decadimento più reattivo
python scripts/backtest.py --test-season 2425     # testa un'altra stagione
```

## Roadmap (idee, non impegni)

1. ✅ **Fase 1** — tracer bullet: Dixon-Coles + backtest su Serie A.
2. **Predizioni su partite future** (non solo backtest): serve una fonte per il
   calendario delle prossime giornate.
3. **Feature engineering** per provare a colmare il divario col mercato (forma
   recente, xG, indisponibilità giocatori, riposo, ecc.).
4. **Estensione** a nuovi campionati (già predisposto in `sources.py`).
5. **Integrazioni** con piattaforme esterne (Polymarket, exchange, …).

## Note sui dati

L'ambiente di sviluppo cloud non raggiunge direttamente `football-data.co.uk`
(policy di rete), quindi si usa un mirror su GitHub con **lo stesso formato**.
Girando il progetto in locale è sufficiente sostituire `BASE_URL` in
`src/data/sources.py` con l'URL ufficiale.
