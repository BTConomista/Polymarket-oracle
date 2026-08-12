# Ligue 1 2025-26 da tre fonti — SofaScore, Opta (WhoScored), Understat

Quinta e ultima lega della raccolta. Schema **identico** alla Serie A, aggancio
**612/612** su squadre, giocatori, heatmap ed eventi_opta.

```python
from src.data import tre_fonti as tf
tf.squadre("ligue_1", periodo="Totale")   # 612 squadra-partita, 18 squadre
tf.eventi_opta("ligue_1")
```

## ⚠️ Lo spareggio francese è a TRE turni, non uno

In Bundesliga lo spareggio è un turno solo (`Finale`, 2 partite). Qui sono
**tre** — `1° turno preliminare`, `2° turno preliminare`, `Finale` — per 4
partite e **3 squadre di Ligue 2** (Red Star, Rodez, Saint-Étienne).

La costante `Turno == "Finale"` scritta per la Bundesliga ne avrebbe preso **un
quarto**, lasciando dentro 3 squadre estranee e portando il conteggio a 620
invece di 612. Da qui la regola generale: **in un campionato, tutto ciò che non
è «Giornata N» è spareggio** — e `E_CAMPIONATO` la disattiva per le UEFA, dove
i turni fuori schema *sono* la competizione.

## ⭐ Il tripwire sui gol è scattato, ed era giusto così

`_allinea_gol` allineava Understat a SofaScore in **un verso solo**, con una
guardia che alzava se Understat avesse mai dichiarato *più* gol. Qui è successo:

```
Emersonn (Toulouse), 05/10/2025 — SofaScore 1, Understat 2
```

Istruito a mano: **Lyon 1-2 Toulouse**, e dei due gol del Tolosa uno è
l'**autogol di Clinton Mata all'87'**, che Understat accredita a Emersonn.

E qui c'è l'ironia utile: l'ipotesi «sarà la convenzione sugli autogol» era
**falsa** per i primi 9 casi — verificata e smentita su quattro fonti — ed è
**vera** per il decimo. Stesso sintomo, due cause.

Misurato su tutte e cinque le leghe, la separazione è perfetta:

| verso | righe | autogol nella partita |
|---|--:|--:|
| SofaScore > Understat (Understat *perde* un gol) | 12 | **0/12** |
| Understat > SofaScore (Understat *accredita* l'autogol) | 1 | **1/1** |

Ora la regola vale in entrambi i versi, e il tripwire è diventato più stretto:
alza se lo scarto supera 1 gol, o se un `Understat > SofaScore` capita in una
partita **senza** autogol.
