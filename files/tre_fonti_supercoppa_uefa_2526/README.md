# Supercoppa UEFA 2025-26 — UEFA Super Cup

Consegnata il 13/08/2026 insieme alle altre cinque supercoppe. Metodo identico
alle altre raccolte (`files/tre_fonti_serie_a_2526/README.md`): i file restano
**come consegnati**, le riparazioni vivono in `src/data/tre_fonti.py` e si
applicano **in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("supercoppa_uefa", periodo="Totale")
```

**1 partita** (13/08/2025) — Paris Saint-Germain – Tottenham Hotspur.

- **2025-08-13** (Finale) — Paris SG – Tottenham

| blocco | righe |
|---|---:|
| `eventi` | 200 |
| `eventi_opta` | 1.393 |
| `giocatori` | 106 |
| `heatmap` | 1.354 |
| `legenda` | 439 |
| `squadre` | 6 |

## Le fonti sono DUE

`tf.fonti("supercoppa_uefa")` → `('SofaScore', 'WhoScored')`.
Understat non copre le coppe europee.

## Il punteggio è già pulito (verificato, non assunto)

**1** partita decisa ai rigori, e `Gol casa/trasferta (SofaScore)` è comunque il risultato della
**partita**: la serie finale sta nella sua colonna (`Rigori casa/trasferta`).

Non è una promessa dell'export: in Europa League e Conference la stessa colonna
**somma** la lotteria («Partizan-AEK Larnaca 7-7» era 2-1). Qui la verifica è
l'identità dei tempi — `Gol = 1T + 2T` regge su **1/1** partite —
e la si rifà con `python scripts/_run_punteggio_coppe.py`.

## Le colonne vuote sono 20, in tre famiglie

Dichiarate in `tf.colonne_vuote("supercoppa_uefa")`, e non sono un difetto unico:

1. le **`(WhoScored)`** — nessuna: la fonte c'è;
2. le **6 dei tempi supplementari** — vuote perché i supplementari non si sono
   giocati. ⭐ È la conferma indipendente del tripwire sul punteggio: se un
   giorno si giocassero, queste si riempirebbero **e** l'identità `Gol = 1T + 2T`
   salterebbe. Due segnali che si controllano a vicenda;
3. le **14 di classifica** (`Punti`, `Posizione`, `Girone`…) — una supercoppa
   non ha una classifica.

## `E_CAMPIONATO` è False

Il turno è «Finale». Trattarla da campionato butterebbe via **tutta** la
raccolta, perché nessun turno si chiama «Giornata N».

## Le righe `Rosa` sono un dato diverso, e va letto come tale

`giocatori()` filtra `Livello == "Partita"` per default. Il blocco contiene anche
righe `Livello == "Rosa"`: anagrafica del giocatore (maglia, ruolo, altezza,
nazionalità, valore di mercato, data di nascita).

⚠️ **R8** — quel club e quel valore sono **di oggi**, non della partita: fra le
squadre della `Rosa` compaiono le riserve (`Bologna U20`, `Bayern München II`,
`Real Madrid Castilla U21`), che sono il club *attuale* del giocatore secondo
SofaScore. Usarli per prevedere la partita che li ha prodotti è look-ahead.
