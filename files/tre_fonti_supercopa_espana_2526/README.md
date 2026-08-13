# Supercopa de España 2025-26 — final four

Consegnata il 13/08/2026 insieme alle altre cinque supercoppe. Metodo identico
alle altre raccolte (`files/tre_fonti_serie_a_2526/README.md`): i file restano
**come consegnati**, le riparazioni vivono in `src/data/tre_fonti.py` e si
applicano **in lettura**.

```python
from src.data import tre_fonti as tf
tf.squadre("supercopa_espana", periodo="Totale")
```

**3 partite** (07–11/01/2026) — Barcelona, Athletic, Atlético, Real Madrid.

- **2026-01-07** (Semifinali) — Barcelona – Ath Bilbao
- **2026-01-08** (Semifinali) — Ath Madrid – Real Madrid
- **2026-01-11** (Finale) — Barcelona – Real Madrid

| blocco | righe |
|---|---:|
| `eventi` | 891 |
| `giocatori` | 269 |
| `heatmap` | 4.777 |
| `legenda` | 342 |
| `squadre` | 18 |

## Le fonti sono UNA

`tf.fonti("supercopa_espana")` → `('SofaScore',)`.

⚠️ La raccolta porta comunque **19 colonne `(WhoScored)` completamente vuote**:
lo schema le prevede e la consegna non le riempie. Non è un finto pieno — sono
`NaN` oneste — ma è la sua anticamera: chi legge l'elenco delle colonne conclude
«c'è anche WhoScored» e ha torto. `tf.fonti()` dice quali fonti coprono
**davvero** la raccolta.

## Il punteggio è già pulito (verificato, non assunto)

Nessuna partita è stata decisa ai rigori, e `Gol casa/trasferta (SofaScore)` è comunque il risultato della
**partita**: la serie finale sta nella sua colonna (`Rigori casa/trasferta`).

Non è una promessa dell'export: in Europa League e Conference la stessa colonna
**somma** la lotteria («Partizan-AEK Larnaca 7-7» era 2-1). Qui la verifica è
l'identità dei tempi — `Gol = 1T + 2T` regge su **3/3** partite —
e la si rifà con `python scripts/_run_punteggio_coppe.py`.

## Le colonne vuote sono 43, in tre famiglie

Dichiarate in `tf.colonne_vuote("supercopa_espana")`, e non sono un difetto unico:

1. le **`(WhoScored)`** — la fonte non copre questa competizione;
2. le **6 dei tempi supplementari** — vuote perché i supplementari non si sono
   giocati. ⭐ È la conferma indipendente del tripwire sul punteggio: se un
   giorno si giocassero, queste si riempirebbero **e** l'identità `Gol = 1T + 2T`
   salterebbe. Due segnali che si controllano a vicenda;
3. le **14 di classifica** (`Punti`, `Posizione`, `Girone`…) — una supercoppa
   non ha una classifica.

## `E_CAMPIONATO` è False

Il turno è «Finale» e «Semifinali». Trattarla da campionato butterebbe via **tutta** la
raccolta, perché nessun turno si chiama «Giornata N».

## Le righe `Rosa` sono un dato diverso, e va letto come tale

`giocatori()` filtra `Livello == "Partita"` per default. Il blocco contiene anche
righe `Livello == "Rosa"`: anagrafica del giocatore (maglia, ruolo, altezza,
nazionalità, valore di mercato, data di nascita).

⚠️ **R8** — quel club e quel valore sono **di oggi**, non della partita: fra le
squadre della `Rosa` compaiono le riserve (`Bologna U20`, `Bayern München II`,
`Real Madrid Castilla U21`), che sono il club *attuale* del giocatore secondo
SofaScore. Usarli per prevedere la partita che li ha prodotti è look-ahead.
