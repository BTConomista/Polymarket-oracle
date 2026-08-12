# UEFA Conference League 2025-26 — solo SofaScore

409 partite, **164 squadre**, 15 turni. È la raccolta più larga per numero di
club e la più stretta per fonti.

```python
from src.data import tre_fonti as tf
tf.squadre("uefa_conference_league", periodo="Totale")
tf.heatmap("uefa_conference_league")
```

⏳ **`eventi_opta` non è arrivato** (5 file su 6).
`tf.eventi_opta("uefa_conference_league")` alza un errore che lo dice.

## ⚠️ UNA fonte, non tre

Mancano tutte le colonne Understat (-37) **e** tutte quelle WhoScored (-75):
niente `ratings`, `passesTotal`, `touches`, `tacklesTotal`. Restano le
statistiche SofaScore.

Chiamarla «a tre fonti» sarebbe un finto pieno nel nome:
`tf.fonti("uefa_conference_league")` restituisce `("SofaScore",)`.

Delle nostre squadre ce ne sono **5**: `Crystal Palace` · `Fiorentina` ·
`Mainz` · `Strasbourg` · `Vallecano`.

## ⚠️⚠️ Il punteggio somma la lotteria dei rigori

`Gol casa (SofaScore)` su una partita decisa ai rigori **non è il risultato
della partita**:

```
Omonia Nicosia – Wolfsberger AC, 28/08/2025
  Gol casa (SofaScore)              6      ← 1 sul campo + 5 rigori
  Gol casa senza rigori (derivata)  1      ← il punteggio vero
```

È **lo stesso difetto** che il CLAUDE.md documenta per `games.csv` sulle coppe
nazionali (68 partite su 458), dove è costato una ricostruzione dagli eventi.

⭐ **Qui però l'export lo dichiara**, con tre colonne derivate:
`Decisa ai rigori (derivata)` (si/no), `Gol casa senza rigori (derivata)`,
`Gol trasferta senza rigori (derivata)`. Sono **6 partite su 409**.

Usa `tf.punteggio_vero(df)`, che prende le derivate dove ci sono e le colonne
normali dove non servono (nei campionati non c'è lotteria).
