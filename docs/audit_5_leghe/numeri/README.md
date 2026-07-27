# `numeri/` — gli artefatti grezzi dietro le tabelle dei report

Ogni file qui è l'**output congelato** della run che ha prodotto un report di
`docs/audit_5_leghe/`. Servono a una cosa sola: permettere a chiunque di
rifare un conto senza ri-eseguire l'audit. Vivevano in `cantiere/out/`.

Le tre `.md` (`caccia_calendari`, `caccia_ou_dataset`, `caccia_quote_singole`)
sono la lettura per un umano del `.json` gemello.

## ⚠️ Congelati al momento del report — non "correggerli" ri-eseguendo

Due artefatti **non riproducono più** i loro numeri se si ri-esegue lo script
oggi. In nessuno dei due casi si tratta di un errore, e in entrambi la versione
da tenere è quella committata (verificato all'audit della Fase 101).

**`eda_5_leghe.json`** — tre valori Bundesliga cambiano ri-eseguendo
`scripts/eda_nuove_leghe.py`:

| valore | artefatto | ri-eseguendo oggi |
|---|--:|--:|
| `gamma` | 0.216 | 0.217 |
| `corr(xG,gol)` | 0.644 | 0.645 |
| deficit-pareggio `Q3` | 0.0132 | 0.0146 |

Causa isolata: la correzione **R1 su Union Berlin-Bochum 14/12/2024** (0-2
assegnato dal tribunale → **1-1 sul campo**, `data/correzioni_dichiarate.csv`),
applicata allo snapshot **dopo** la scrittura di `03_nuove_leghe.md`. Verifica:
`ln(gol_casa/gol_ospite)` su `data/bundesliga_matches.csv` vale 0.217 con l'1-1
e 0.216 rimettendo lo 0-2. L'artefatto resta allineato alla tabella di
`03_nuove_leghe.md:134`.

**`recupero_squad_value_tm.json`** — ri-eseguire
`scripts/recupero_squad_value_tm.py` porta `n` da 13 a 18 club e lo scarto
mediano dal 14,8% all'8,6%. È **circolarità**: le 16 celle recuperate da
Transfermarkt sono state nel frattempo scritte nello snapshot
(`applica_squad_value_tm.py`), quindi il confronto TM↔player-scores finisce per
confrontare Transfermarkt con sé stesso. La misura della scala vale solo nella
versione congelata, fatta **prima** dell'applicazione.

## Cosa manca

- **`caccia_understat.md`**: delle quattro «cacce» è l'unica senza la sua
  lettura per un umano (c'è solo il `.json`).
  `scripts/cerca_segnaposto.py` la promette nel docstring e la scrive a fine
  run, ma il run richiede i grezzi di `data/fonti/`, oggi non versionati
  (`.gitignore`): serve prima `python scripts/fetch_sources.py`.
- **`tracer_pred_{lega}.csv`** (5 file, 10.735 righe di predizioni walk-forward
  del DC): cancellati con il cantiere senza destinazione, ma cinque script li
  rileggono **da questa cartella** — `tranche3_mercati.py` si ferma con
  `SystemExit` se non li trova. Si rigenerano con
  `python scripts/tranche3_tracer.py`, da eseguire prima di `leve_apertura`,
  `leve_dc_panchina`, `nuovo_calibrazione`, `tranche3_mercati` e
  `tranche3_ritaratura`.
