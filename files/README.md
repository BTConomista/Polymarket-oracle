# `files/` — bundle dati grezzi caricati a mano (offline-first)

Questa cartella contiene i **dati grezzi versionati** da cui si costruiscono gli
snapshot congelati di Premier League e La Liga. Nacquero come bundle caricati a
mano perché all'epoca (Fase 54/67) la rete era bloccata nell'ambiente di
sviluppo.

> ⚠️ **SUPERATA dalla Fase 100/101-bis.** La premessa è caduta:
> `football-data.co.uk` e `understat.com` sono **tornati raggiungibili** (per
> questo Bundesliga e Ligue 1 sono state scaricate direttamente, senza bundle —
> CLAUDE.md §7). I bundle **restano** e non vanno rimossi: sono la fonte
> congelata di Premier e Liga, e **10 script** li leggono direttamente. Il loro
> valore ora è la **riproducibilità** (la fonte non cambia sotto i piedi), non
> l'irraggiungibilità della rete. Stato della rete in
> `docs/MANUALE_SOPRAVVIVENZA.md` §1.

Pesa **63 MB** (`du -sh files/`): è **intenzionale** (riproducibilità senza
rete). Contenuto:

| file/cartella | cosa | usato da |
|---|---|---|
| `football_data_premier_league_bundle.json` | risultati + quote football-data.co.uk (Premier, 9 stagioni) | `scripts/build_league_snapshot.py` |
| `football_data_la_liga_bundle.json` | idem per La Liga | idem |
| `understat_premier_league_bundle.json` | xG/npxG/PPDA/deep Understat (Premier) | idem |
| `understat_la_liga_bundle.json` | idem per La Liga | idem |
| `player_scores/` | dataset player-scores (valutazioni rosa reali, dcaribou/transfermarkt-datasets, dichiarato CC0 — ⚠️ **ma vedi la decisione aperta sulla catena della licenza in `docs/DATI.md` §4**: Transfermarkt pubblica una riserva `ai-all` machine-readable e il sui generis sulla banca dati resta suo), **4 file `.csv.gz`**: `appearances` (41 MB), `player_valuations` (5,4 MB), `players` (3,9 MB), `clubs` (47 KB) — è la voce che pesa | `scripts/build_squad_values.py` (Fase 67), `src/data/player_scores.py` |

**Chi li legge** (`grep` su `scripts/` e `src/`): 10 script —
`build_league_snapshot.py`, `_run_ah_benchmark.py`, `_run_counts_nb.py`,
`_run_fase53_crossleague.py`, `_run_fase73_ou_close_disp.py`,
`_run_lineup_proxy.py`, `_run_listino_validazione.py`, `_run_outside_matrix.py`,
`_run_polymarket_tier3.py`, `_run_referee_feature.py` — più `src/data/sources.py`
e `src/data/player_scores.py`. Rimuovere un bundle rompe tutti questi.

Gli snapshot prodotti (`data/{premier_league,la_liga}_matches.csv`) sono la fonte
di verità congelata usata dai backtest; questi bundle servono a **rigenerarli**.
Il workflow d'import di `player_scores/` (runner GitHub con rete libera) vive in
`.github/workflows/import_dataset.yml`; si innesca con un push di
`.github/import-dataset-trigger`.

> **Le altre tre leghe non passano da qui.** La Serie A ha i CSV grezzi
> congelati in `data/football_data_raw/`; Bundesliga e Ligue 1 **non hanno una
> fonte grezza congelata** — si riscaricano con `scripts/fetch_sources.py` in
> `data/fonti/` (135 MB, in `.gitignore`), e ciò che è versionato sono le 90
> impronte SHA256 di `data/ricerca_esterna/manifest_fonti_audit.json`. Il
> quadro completo dei tre regimi è in `docs/DATI.md` §4.
