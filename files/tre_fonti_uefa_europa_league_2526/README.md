# UEFA Europa League 2025-26 — SofaScore + Opta (WhoScored)

**Non è un campionato**, ed è la prima raccolta di questo tipo: 271 partite, 77
squadre di tutta Europa, 17 turni dai preliminari alla finale.

```python
from src.data import tre_fonti as tf
tf.squadre("uefa_europa_league", periodo="Totale")
tf.eventi_opta("uefa_europa_league")
```

## Non ha uno snapshot a cui agganciarsi

Non esiste `data/uefa_europa_league_matches.csv`: il criterio non è «612/612»
ma **quante delle nostre squadre ci sono**. Sono **11**:

`Aston Villa` · `Betis` · `Bologna` · `Celta` · `Freiburg` · `Lille` · `Lyon` ·
`Nice` · `Nott'm Forest` · `Roma` · `Stuttgart`

Le altre 66 sono squadre di campionati che non modelliamo.

## ⚠️ Due fonti, non tre

**Understat non copre le competizioni UEFA**: mancano tutte e 37 le sue
colonne (xG, npxG, PPDA, deep completions, xPts). Non è un difetto della
consegna — è il perimetro della fonte. `tf.fonti("uefa_europa_league")` lo
dichiara, e chiedere `xG (Understat)` dà **KeyError**, non NaN.

## Otto colonne che i campionati non hanno

Servono al formato a eliminazione: `Casa 90'`, `Casa suppl. totale`,
`Casa 2° suppl.`, `Casa totale doppio confronto` (e i gemelli trasferta). Il
doppio confronto è pieno sul 22,9% delle righe, i supplementari sul 5,9%.

## ⚠️ Il punteggio somma la lotteria dei rigori

Vedi il README della Conference: stesso difetto, stessa riparazione
(`tf.punteggio_vero()`).

`ID evento` non è una chiave univoca: **199 doppioni**, il valore più alto
delle sei raccolte con eventi Opta.
