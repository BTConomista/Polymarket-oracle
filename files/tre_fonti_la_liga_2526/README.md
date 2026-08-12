# La Liga 2025-26 da tre fonti — SofaScore, Opta (WhoScored), Understat

Terza lega della raccolta, consegnata l'11/08/2026. Il metodo è quello della
Serie A (`files/tre_fonti_serie_a_2526/README.md`): i file restano **come
consegnati**, le riparazioni vivono in `src/data/tre_fonti.py` e si applicano
**in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("la_liga", periodo="Totale")   # 760 squadra-partita, 215 colonne
tf.giocatori("la_liga")                   # giocatore-partita, 190 colonne
tf.eventi("la_liga", categoria="Tiro")
tf.heatmap("la_liga")                     # 570.768 posizioni
```

⏳ **`eventi_opta` non è ancora arrivato** — l'utente lo consegna in **due
file**. `tf.eventi_opta("la_liga")` alza un errore che dice quale file manca.

## Il modulo ha retto senza modifiche

È il risultato che conta di questa terza consegna: **760/760 al primo colpo**,
senza toccare una riga del codice di lettura. Lo schema è **identico** alla
Serie A su tutti e cinque i file (la Premier aveva 3 colonne in più).

L'unico intervento è stato aggiungere uno **stato nuovo** — vedi sotto.

## I difetti: la divisione regge, con una correzione

### Si ripetono su tutte e tre → riparazione generale

| difetto | Serie A | Premier | **La Liga** |
|---|--:|--:|--:|
| `ID partita` misto (valori distinti per 380 partite) | 436 | 384 | **538** |
| Understat perde gol | 2 | 3 | **4** |
| discordanza `possesso` falsa | 760 | 760 | **760** |

Sui gol la direzione è **sempre la stessa**: +1 a favore di SofaScore, `Autogol`
sempre 0, ora su **9 righe su 9** in tre leghe. La regola con tripwire regge.

### Non si ripetono → riparazione per-lega

| | Serie A | Premier | **La Liga** |
|---|---|---|---|
| righe orfane della fusione | 2 | 0 | **0** |
| copertura `Meteo (WhoScored)` | 0,0% | 98,4% | **0,3%** |

## ⚠️ La terza lega ha rotto una dicotomia

`Meteo` in La Liga è piena su **2 righe su 760**. Non è vuota e non è piena: è
il terzo stato, e con due leghe non esisteva.

```
Serie A     0,0%   (0 righe su 760)   → vuota
La Liga     0,3%   (2 righe su 760)   → QUASI VUOTA
Premier    98,4% (748 righe su 760)   → piena
```

**Lo stato di mezzo è il più insidioso dei tre.** Una colonna a zero si dichiara
da sola; una a 0,3% risponde «sì, funziona» a un `notna().any()`, e chi ci
costruisce sopra lavora su 2 righe credendone 760. È finto pieno (R6) in
miniatura.

Da qui `tf.copertura(colonna, lega)`, che restituisce lo **stato** invece di un
booleano — proprio per non far ricollassare tre casi in due. E la Liga **non**
compare fra le `colonne_vuote`, perché dichiararla vuota sarebbe falso quanto
ignorarla.

## L'Espanyol

La raccolta scrive `Espanyol`, `TEAM_ALIASES` lo porta a `Espanol` come il
nostro snapshot: **aggancia correttamente**.

⚠️ Da non confondere con il reperto dell'audit d'identità (`docs/audit_identita/`),
che riguarda un ponte diverso — `club_matching.Agganciatore`, dove `Espanol`
risolve univocamente al club **sbagliato** (*Jove Español San Vicente*). Quello
resta aperto e non è toccato da questa raccolta.

## Le discordanze dichiarate dal file

| livello | righe vere | dettaglio |
|---|--:|---|
| squadra | **27** | corner 22 · falli 3 · passaggi 2 |
| giocatore | 6.972 | minuti 6.608 · passaggi chiave 161 · tiri 102 · passaggi totali 90 · assist 7 · **gol 4** |

Più le 760 righe marcate `possesso`, che sono il falso positivo noto:
`discordanze_squadra("la_liga")` toglie il token e lascia le 27 vere.
