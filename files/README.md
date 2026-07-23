# `files/` — bundle dati grezzi caricati a mano (offline-first)

Questa cartella contiene i **dati grezzi versionati** da cui si costruiscono gli
snapshot congelati di Premier League e La Liga (la rete è bloccata nell'ambiente
di sviluppo, quindi i dati arrivano come bundle caricati a mano o importati via
GitHub Actions — vedi `docs/MANUALE_SOPRAVVIVENZA.md` e Fase 54/67).

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
