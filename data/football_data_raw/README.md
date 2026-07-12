# `data/football_data_raw/` — CSV grezzi originali football-data (fonte congelata)

Questa cartella contiene i **CSV originali di football-data.co.uk** per la Serie A
(codice provider `I1`), una stagione per file: `serie_a_1718.csv` … `serie_a_2526.csv`
(9 stagioni, 2017-18 → 2025-26). Sono i file **grezzi e completi**, con TUTTE le
colonne del provider — incluse le quote di **apertura** (`AvgH`, `B365H`, …) e di
**chiusura** (`AvgCH`, `B365CH`, …), che lo snapshot pulito non conserva tutte.

## Perché sono versionati qui (e non solo scaricati al volo)

Il mirror GitHub storico usato da `sources.BASE_URL`
(`Mentaturan/ScoutFootball_for_World_Cup`) **è sparito** (404 verificato
2026-07): dal cloud non è più scaricabile nulla a monte. Questi file sono la
**fonte grezza di verità congelata**, l'analogo per i dati *raw* di ciò che
`data/serie_a_matches.csv` è per lo *snapshot* pulito: chi clona il repo ha
esattamente gli stessi input, senza rete.

Provenienza: scaricati manualmente da
`https://www.football-data.co.uk/mmz4281/{stagione}/I1.csv` (raggiungibile da una
rete/browser normali) e non modificati (encoding `latin-1`, separatore virgola).

## Rapporto con `data/raw/` (la cache di lavoro)

- **questa cartella** (`data/football_data_raw/`) = **versionata**, congelata,
  non si tocca;
- **`data/raw/`** = cache di lavoro **rigenerabile** (in `.gitignore`), quella
  che il loader legge davvero.

`python scripts/_restore_raw_cache.py` copia da qui a `data/raw/` (verificando che
la stagione dedotta dalle date del file coincida col nome). Poi la pipeline gira
offline:

```bash
python scripts/_restore_raw_cache.py           # da qui → data/raw/
python scripts/build_database.py --open-odds   # aggancia le quote di apertura allo snapshot
```
