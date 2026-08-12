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
tf.eventi_opta("la_liga")                 # 577.205 eventi, da due parti
```

✅ **Raccolta completa.** `eventi_opta` è arrivato in **due parti** (288.798 +
288.407 righe): `tf.eventi_opta("la_liga")` le ricompone in **577.205** eventi
su 380 partite, e aggancia **760/760**.

⚠️ **Il taglio è grezzo, non logico, e cade dentro una partita.**
Levante-Espanyol dell'11/01/2026 ha **166 eventi in parte1** (fino al 7' del
primo tempo) e **1.327 in parte2**, contro una mediana di 1.517 a partita. Chi
leggesse una parte sola la vedrebbe monca **senza che nulla glielo dica**: 166
è un numero plausibile per una riga di dati, e nessun conteggio se ne accorge.
Zero eventi duplicati fra le due parti — quindi la concatenazione è corretta e
necessaria.

⚠️ **`ID evento` non è una chiave univoca**: 44 doppioni in Liga, 45 in Serie A,
82 in Premier — e ci sono anche nei file **non** spezzati, quindi non è un
effetto della ricomposizione. Parte cadono dentro la stessa partita, parte fra
partite diverse. Non usarlo come chiave primaria.

## ⚠️ Due convenzioni di nome nello stesso file

`eventi_opta` scrive **`Atletico`** nudo nella colonna `Squadra` e
**`Atlético Madrid`** in `Casa`/`Trasferta`. Effetto misurato prima della
riparazione: l'aggancio si fermava a **722/760** squadra-partita, e le 38
mancanti erano **tutte dell'Atletico** — mentre le *partite* agganciavano
380/380, il che rendeva il difetto **invisibile a un controllo per partita**.

L'alias sta in `tre_fonti.ALIAS_RACCOLTA`, **non** in `sources.TEAM_ALIASES`:
quella mappa è globale al progetto e «Atletico» da solo è ambiguo fuori dalla
Liga (Mineiro, Nacional, decine di altri). Metterlo lì sarebbe un join che
indovina — la cosa che la regola d'oro vieta. Il difetto **non si ripete**:
in Serie A e Premier la colonna `Squadra` di `eventi_opta` aggancia tutto.

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
