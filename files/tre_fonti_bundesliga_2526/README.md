# Bundesliga 2025-26 da tre fonti — SofaScore, Opta (WhoScored), Understat

Quarta lega della raccolta, consegnata l'11/08/2026 in due zip. Il metodo è
quello della Serie A (`files/tre_fonti_serie_a_2526/README.md`): i file restano
**come consegnati**, le riparazioni vivono in `src/data/tre_fonti.py` e si
applicano **in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("bundesliga", periodo="Totale")   # 612 squadra-partita
tf.giocatori("bundesliga")
tf.eventi_opta("bundesliga")                 # 478.270 eventi
tf.heatmap("bundesliga")                     # 477.252 posizioni
```

## ⚠️ Non è 760: qui sono 612

**18 squadre e 306 partite**, non 20 e 380. Ogni numero che nelle prime tre
leghe era «760 squadra-partita» qui è **612**. `tf.DIMENSIONI` tiene i due
formati, e i test confrontano col numero della lega invece di inchiodarne uno —
altrimenti la Bundesliga sarebbe sembrata rotta quando era solo più piccola.

Aggancio: **612/612 su tutti e quattro i blocchi.**

## ⚠️ Le ultime due partite non sono di campionato

`Wolfsburg-Paderborn`, andata e ritorno, marcate `Turno == "Finale"`: è lo
**spareggio promozione/retrocessione** contro una squadra di *seconda*
divisione. Nei nostri snapshot quelle partite **non esistono**.

Lasciarle dentro fa due danni: porta il conteggio a **616** dove le
squadra-partita di campionato sono 612, e tira dentro una **19ª squadra**
(Paderborn) che nel campionato non c'è.

Sono **escluse per default** — stessa convenzione di
`player_stats.load_player_matches`, che usa la colonna `Fase`. Qui `Fase` non
c'è e il marcatore è `Turno`; «Finale» è l'unico dei 35 valori che non sia
«Giornata N», e un test lo inchioda. `spareggio=True` le rimette.

## ⭐ Un difetto CHIUSO a monte

Fino alla Liga il file marcava `possesso` come discordanza su **760 righe su
760** — un falso positivo, perché confrontava una percentuale (SofaScore) con
un conteggio (WhoScored). Questa consegna aggiunge la colonna
**`possession % (normalizzato) (WhoScored)`**, e funziona: coincide con
SofaScore entro 1 punto su **610 righe su 612**.

Effetto: la discordanza dichiarata sul possesso scende da 760 a **2**.

È il primo difetto della serie riparato **nell'export** invece che in lettura.

## ⚠️ E uno che si ripete, per la seconda volta

La colonna `Squadra` di `eventi_opta` usa la **sigla `RBL`** per RB Leipzig,
mentre `Casa`/`Trasferta` dello stesso file scrivono il nome intero. L'aggancio
si fermava a **578/612**.

È lo stesso difetto della Liga (`Atletico` nudo): **due leghe su quattro,
sempre una squadra sola, sempre quella colonna**. Non è più un incidente — è
una proprietà di `eventi_opta`. E in entrambi i casi **l'aggancio per partita
resta perfetto**, quindi solo il controllo per squadra-partita lo rivela.

Riparato in `tre_fonti.ALIAS_RACCOLTA["bundesliga"]`, scoped alla raccolta.

## Alias aggiunti a `TEAM_ALIASES`

Due, e sono forme *vicine* a quelle già note, che differiscono di un carattere:

| raccolta | canonico | il progetto conosceva già |
|---|---|---|
| `1. FC Heidenheim` | `Heidenheim` | `1. FC Heidenheim 1846`, `FC Heidenheim` |
| `Borussia M'gladbach` | `M'gladbach` | `Borussia M.Gladbach` (col punto) |

Erano le uniche 2 squadre su 18 a non agganciare, e insieme valevano **136
squadra-partita su 612**.

## Le discordanze dichiarate

| livello | dettaglio |
|---|---|
| squadra | corner 8 · possesso **2** · passaggi 2 · tiri 1 · tiri in porta 1 |
| giocatore | minuti 5.248 · passaggi chiave 151 · tiri 84 · passaggi totali 34 · assist 8 · **gol 2** · tiri in porta 2 |

`ID evento` non è una chiave univoca: **79 doppioni** (contro 45 in Serie A,
82 in Premier, 44 in Liga).
