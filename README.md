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
| **1X2** | log-loss | 0.9890 | 1.0851 | **0.9784** |
| **1X2** | Brier | 0.5907 | 0.6579 | **0.5830** |
| **O/U 2.5** | log-loss | 0.7056 | 0.6896 | **0.6996** |
| **O/U 2.5** | Brier | 0.2560 | 0.2482 | **0.2530** |

_Configurazione: shrinkage = 1.5, emivita = 730g (vedi Fase 2b). Il modello è
validato su **tre** stagioni (2023-24, 2024-25, 2025-26): le conclusioni sono
stabili, non rumore di una singola stagione._

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
ha ancora un vantaggio sul mercato. **Non usare questo modello per scommettere
soldi veri.**

### Analisi degli errori — Fase 2a (`scripts/analyze.py`)

Prima di aggiungere feature, abbiamo analizzato *dove* il modello perde contro il
mercato. Risultati principali:

- **Sulla media il modello è ben calibrato** (nessun bias sistematico, nemmeno sui
  pareggi): il vantaggio del mercato è nella **discriminazione** delle singole
  partite, non nella calibrazione media.
- **Bug trovato e corretto**: la stagione di test chiamava il Verona "Hellas
  Verona" mentre le stagioni di training usavano "Verona" → il modello lo trattava
  come squadra sconosciuta, producendo predizioni assurde. Risolto con una mappa
  di normalizzazione nomi (`TEAM_ALIASES` in `sources.py`).
- **Dove il modello perde di più** (log-loss, gap col mercato): partite con
  **neopromosse** (gap +0.037, doppio della media) e **inizio stagione**
  (+0.030). Radice comune: dati storici scarsi o datati → stime inaffidabili.
  Questi sono i bersagli prioritari del feature engineering (Fase 2b).

### Feature engineering — Fase 2b (in corso)

Primo intervento: **shrinkage** (regolarizzazione verso la media della lega),
tarato con `scripts/tune.py` su due stagioni. Poiché la penalità è
fissa mentre il contributo dei dati cresce col numero di partite, l'effetto è
**automaticamente più forte sulle squadre con pochi dati** — proprio i punti
deboli individuati.

Risultato (log-loss 1X2, media 2024-25 + 2025-26; più basso = meglio):

| shrinkage | media | gap col mercato |
|---:|---:|---:|
| 0.0 (base) | 0.9918 | +0.026 |
| **1.5** (scelto) | **0.9879** | **+0.022** |
| Mercato | 0.9654 | — |

Migliora **entrambe** le stagioni e riduce il divario col mercato di ~15%. In
particolare il gap sull'**inizio stagione** scende da +0.030 a +0.022 e quello
sulle **neopromosse** da +0.037 a +0.030: l'intervento colpisce i bersagli
previsti.

Secondo intervento: **taratura dell'emivita** del decadimento temporale (quanto
peso dare alle partite recenti), su tre stagioni. Risultato (log-loss 1X2 medio):

| emivita | media | note |
|---:|---:|---|
| 90g | 0.9935 | troppo reattiva, rumorosa |
| 180g (prima) | 0.9863 | |
| 365g | 0.9834 | |
| **730g** (scelta) | **0.9829** | memoria ~2 stagioni |
| Mercato | 0.9658 | |

Lezione: in Serie A le rose restano stabili anno su anno, quindi una **memoria
lunga** (~2 stagioni) batte il peso aggressivo sulle ultime partite. Con la
configurazione finale (emivita 730g, shrinkage 1.5) il divario medio col mercato
scende da +0.026 (Dixon-Coles puro) a **+0.017**: circa un terzo del divario
recuperato solo con la taratura, senza informazione nuova.

Qui il modello basato sui **soli gol** è vicino al suo tetto: per avvicinarsi
ancora al mercato serve informazione nuova (forma, xG, indisponibili), non altro
tuning.

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
python scripts/analyze.py           # analizza gli errori del backtest
python scripts/tune.py    # tara lo shrinkage su piu' stagioni
python -m pytest                    # esegue i test
```

Opzioni utili del backtest:

```bash
python scripts/backtest.py --half-life-days 120   # decadimento più reattivo
python scripts/backtest.py --test-season 2425     # testa un'altra stagione
```

## Roadmap (idee, non impegni)

1. ✅ **Fase 1** — tracer bullet: Dixon-Coles + backtest su Serie A.
2. ✅ **Fase 2a** — analisi degli errori: capito dove il modello perde (neopromosse,
   inizio stagione) e corretto il bug dei nomi squadra.
3. **Fase 2b — feature engineering** per colmare il divario col mercato, partendo
   dai punti deboli individuati (priori per neopromosse, riduzione
   dell'overconfidence su dati scarsi; poi forma recente, xG, ecc.).
4. **Predizioni su partite future** (non solo backtest): serve una fonte per il
   calendario delle prossime giornate.
5. **Estensione** a nuovi campionati (già predisposto in `sources.py`).
6. **Integrazioni** con piattaforme esterne (Polymarket, exchange, …).

## Note sui dati

L'ambiente di sviluppo cloud non raggiunge direttamente `football-data.co.uk`
(policy di rete), quindi si usa un mirror su GitHub con **lo stesso formato**.
Girando il progetto in locale è sufficiente sostituire `BASE_URL` in
`src/data/sources.py` con l'URL ufficiale.
