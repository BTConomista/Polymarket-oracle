# `data/football_data_raw/` — CSV grezzi originali football-data (fonte congelata)

Questa cartella contiene i **CSV originali di football-data.co.uk** per la Serie A
(codice provider `I1`), una stagione per file: `serie_a_1718.csv` … `serie_a_2526.csv`
(9 stagioni, 2017-18 → 2025-26). Sono i file **grezzi e completi**, con TUTTE le
colonne del provider — incluse le quote di **apertura** (`AvgH`, `B365H`, …) e di
**chiusura** (`AvgCH`, `B365CH`, …), che lo snapshot pulito non conserva tutte.

## Perché sono versionati qui (e non solo scaricati al volo)

Il motivo **storico** era l'irraggiungibilità: il mirror GitHub
(`Mentaturan/ScoutFootball_for_World_Cup`) **è sparito** — 404, riverificato alla
Fase 101-bis — e all'epoca il sito ufficiale era bloccato dal proxy, quindi dal
cloud non si scaricava nulla a monte.

> ⚠️ **SUPERATA dalla Fase 100** — la premessa non vale più: **`football-data.co.uk`
> risponde 200** dall'ambiente (per questo Bundesliga e Ligue 1 sono state
> scaricate direttamente, senza bundle né congelamento manuale). In
> `src/data/sources.py` il default è tornato al sito ufficiale
> (`BASE_URL = OFFICIAL_BASE_URL`); il mirror resta nel codice solo come
> `MIRROR_BASE_URL`, marcato «MORTO». Stato della rete in
> `docs/MANUALE_SOPRAVVIVENZA.md` §1.

**Il motivo che regge oggi è un altro, ed è più solido della rete: la
riproducibilità.** Questi file sono la **fonte grezza di verità congelata**,
l'analogo per i dati *raw* di ciò che `data/serie_a_matches.csv` è per lo
*snapshot* pulito: chi clona il repo ha esattamente gli stessi input, senza rete
e senza dipendere dal fatto che il provider non riscriva la storia sotto i piedi.

Provenienza: scaricati manualmente da
`https://www.football-data.co.uk/mmz4281/{stagione}/I1.csv` e non modificati
(encoding `latin-1`, separatore virgola).

## ⚠️ Copre solo la Serie A — le altre quattro leghe hanno percorsi diversi

Questa cartella **non** è la fonte grezza congelata di tutto il progetto. Le
cinque leghe stanno in tre regimi distinti (dettaglio in `docs/DATI.md` §4):

| lega | fonte grezza | congelata in repo? |
|---|---|---|
| Serie A | `data/football_data_raw/` (questa cartella, 9 file) | ✅ sì |
| Premier League, La Liga | `files/football_data_*_bundle.json` (Fase 54) | ✅ sì |
| **Bundesliga, Ligue 1** | scaricate al volo da `scripts/fetch_sources.py` in `data/fonti/` | ❌ **no** (135 MB, in `.gitignore`): versionato è lo *snapshot*, più le **90 impronte SHA256** di `data/ricerca_esterna/manifest_fonti_audit.json`, che permettono di ri-scaricare e verificare l'identità — non di lavorare offline sul grezzo |

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
