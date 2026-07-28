# `_anagrafica/` — la fotografia di inizio stagione

Dati che cambiano **raramente** e che vengono raccolti una volta, poi aggiornati
per differenza. Il trattino basso iniziale li tiene in cima all'elenco: si
leggono prima di tutto il resto.

| file | contenuto | nota |
|---|---|---|
| `competizioni.json` | tornei della stagione: formato, date, regole di classifica e spareggi | le regole di spareggio sono **per lega** (`src/models/season_sim.py`) |
| `stadi.json` | nome, capienza, superficie, **coordinate**, altitudine | le coordinate servono al meteo: senza, il §4.2 non parte |
| `ranking_uefa_club.json` | coefficienti per club | |
| `ranking_fifa_nazionali.json` | ranking per nazionali | per il lavoro del §7 |

⚠️ **Perché va fatto PRIMA del 15 agosto.** Rose, valori di mercato e obiettivi
dichiarati sono la fotografia di **agosto**: le fonti li **riscrivono** durante
la stagione senza conservare lo storico, e le dichiarazioni di luglio non le
ripubblica nessuno a maggio. È la stessa lezione di `newseason.md` §2.
