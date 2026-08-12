# Premier League 2025-26 da tre fonti — SofaScore, Opta (WhoScored), Understat

Seconda lega della raccolta a tre fonti, consegnata l'11/08/2026. Stessa forma
della Serie A (`files/tre_fonti_serie_a_2526/`, leggi il suo README per il
metodo): i file restano **come consegnati**, le riparazioni vivono in
`src/data/tre_fonti.py` e si applicano **in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("premier_league", periodo="Totale")   # 760 squadra-partita
tf.giocatori("premier_league")                   # 15.193 giocatore-partita
tf.eventi("premier_league", categoria="Tiro")
tf.eventi_opta("premier_league")                 # 577.884 eventi
tf.heatmap("premier_league")                      # 573.203 posizioni
```

✅ **Raccolta completa**: sei file su sei. La `heatmap` (573.203 righe, 380
partite, 534 giocatori) è arrivata poco dopo gli altri cinque e aggancia
**760/760**. Schema identico alla Serie A, `Tocchi` vuota al 100% su entrambe
le leghe — è del formato, non della consegna.

## Cosa insegna la seconda lega

È il momento in cui si vede quali difetti sono **del formato** e quali erano
**incidenti della prima consegna**. Misurato:

### I tre che si ripetono → riparazione generale

| difetto | Serie A | Premier |
|---|---|---|
| `ID partita` impila tre numerazioni | 436 valori per 380 partite | **384** |
| discordanza `possesso` falsa | 760/762 righe | **760/760** |
| Understat perde gol | 2 righe | **3 righe** |

Sui gol la direzione è **sempre la stessa**: +1 a favore di SofaScore, `Autogol`
sempre 0, su tutte e 5 le righe delle due leghe. Per questo l'allineamento è
diventato una **regola** invece che una lista di eccezioni — una lista sarebbe
girata sulla Premier correggendo *zero* righe e senza dire niente, un silenzio
indistinguibile da «qui non ci sono difetti». La regola porta il suo tripwire:
se una riga discordasse nell'altro verso, `_allinea_gol` **alza**.

### I due che NON si ripetono → riparazione per-lega

| | Serie A | Premier |
|---|---|---|
| righe orfane della fusione | 2 (`Verona` / `Hellas Verona`) | **0** — 760/760 pulite |
| colonna `Meteo (WhoScored)` | **0,0%** piena | **95,9%** piena |

Le orfane erano un incidente su un nome, non un difetto sistematico. E `Meteo`
non era un difetto affatto: è una copertura diversa della fonte. Trattarla come
costante avrebbe fatto scartare un dato buono su una lega per un buco che stava
sull'altra — è la ragione per cui `colonne_vuote()` prende la lega.

## Lo schema è un sovrainsieme

216 colonne in `squadre` contro 215, 192 in `giocatori` contro 190: **3 colonne
in più, nessuna mancante**.

`Average rating (SofaScore)` · `Km camminati (SofaScore)` · `Km di corsa lenta
(SofaScore)`

## L'aggancio

**760/760** squadra-partita contro `data/premier_league_matches.csv`, sia su
`squadre` sia su `giocatori`.

Ha richiesto **un alias**: SofaScore scrive `Wolverhampton`, il nostro snapshot
`Wolves`, e `TEAM_ALIASES` conosceva solo `Wolverhampton Wanderers`. Le altre 19
squadre passavano già. Aggiunto in `src/data/sources.py`.

## Le discordanze dichiarate dal file

| livello | righe | dettaglio |
|---|--:|---|
| squadra | **21** vere | corner 11 · falli 6 · passaggi 4 |
| giocatore | 6.089 | minuti 5.950 · passaggi chiave 160 · tiri 69 · passaggi totali 63 · assist 3 · **gol 3** |

⚠️ A queste il file aggiunge **760 righe marcate `possesso`**, che sono un
**falso positivo**: `Ball possession` di SofaScore è una percentuale,
`possession` di WhoScored un conteggio. Non possono coincidere mai. Vedi il
README della Serie A per la misura; `discordanze_squadra()` toglie il token
falso e lascia le 21 vere.
