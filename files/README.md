# `files/` — bundle dati grezzi caricati a mano (offline-first)

Questa cartella contiene i **dati grezzi versionati** da cui si costruiscono gli
snapshot congelati di Premier League e La Liga. Nacquero come bundle caricati a
mano perché all'epoca (Fase 54/67) la rete era bloccata nell'ambiente di
sviluppo.

> ⚠️ **Aggiornamento Fase 101-bis.** La premessa è caduta: `football-data.co.uk`
> e `understat.com` sono **tornati raggiungibili** (per questo Bundesliga e
> Ligue 1 sono state scaricate direttamente, senza bundle — CLAUDE.md §7). I
> bundle **restano** e non vanno rimossi: sono la fonte congelata di Premier e
> Liga, e `_run_ah_benchmark.py` e altri 9 script li leggono direttamente. Il
> loro valore ora è la **riproducibilità** (la fonte non cambia sotto i piedi),
> non l'irraggiungibilità della rete. Stato aggiornato in
> `docs/MANUALE_SOPRAVVIVENZA.md`.

Pesa ~63 MB: è **intenzionale** (riproducibilità senza rete). Contenuto:

| file/cartella | cosa | usato da |
|---|---|---|
| `football_data_premier_league_bundle.json` | risultati + quote football-data.co.uk (Premier, 9 stagioni) | `scripts/build_league_snapshot.py` |
| `football_data_la_liga_bundle.json` | idem per La Liga | idem |
| `understat_premier_league_bundle.json` | xG/npxG/PPDA/deep Understat (Premier) | idem |
| `understat_la_liga_bundle.json` | idem per La Liga | idem |
| `player_scores/` | dataset player-scores (valutazioni rosa reali, dcaribou/transfermarkt-datasets, CC0): `players`, `clubs`, `appearances`, `player_valuations` in `.csv.gz` | `scripts/build_squad_values.py` (Fase 67) |

Gli snapshot prodotti (`data/{premier_league,la_liga}_matches.csv`) sono la fonte
di verità congelata usata dai backtest; questi bundle servono a **rigenerarli**.
Il workflow d'import (runner GitHub con rete libera) vive in
`.github/workflows/import_dataset.yml`.
