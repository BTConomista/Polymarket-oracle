# Serie A 2025-26 da tre fonti — SofaScore, Opta (WhoScored), Understat

Consegnata dall'utente l'11/08/2026 in sei file. **Sono qui come sono arrivati**:
nessuna cella è stata toccata (regola R3). Le riparazioni vivono in
`src/data/tre_fonti.py` e si applicano **in lettura**, così restano verificabili
e reversibili.

**Usa il modulo, non i file.** `pd.read_csv` diretto su questi `.csv.gz` ti
consegna intatti i cinque difetti descritti sotto.

```python
from src.data import tre_fonti as tf
tf.squadre(periodo="Totale")   # 760 squadra-partita, 214 colonne
tf.giocatori()                 # 17.829 giocatore-partita, 190 colonne
tf.eventi("Tiro")              # tiro-per-tiro con xG e xGOT da DUE fonti
tf.eventi_opta()               # 562.672 eventi, ogni tocco con X/Y e secondo
tf.heatmap()                   # 556.996 posizioni
tf.classifica()                # le 60 righe di classifica (generale/casa/trasferta)
```

## Cosa porta che il progetto non aveva

| | |
|---|---|
| **event data Opta** | 562.672 righe, 380/380 partite, 39 tipi, coordinate al 100%, qualificatori e secondo esatto. Categoria mai avuta |
| **posizioni** | 556.996 righe: dove ogni giocatore ha toccato |
| **arbitro** | 42 arbitri, 99,7% — per il campionato non l'avevamo (solo per le coppe) |
| **stadio, città, capienza, spettatori** | 18 stadi; spettatori al 91,1% |
| **tracking fisico** | km percorsi, km ad alta intensità, sprint, velocità massima (56,7% delle righe giocatore) |
| **momentum** | la curva di pressione, ~92 punti a partita |
| **xPts** | punti attesi Understat, 95% |
| **classifica** | posizione, punti, qualificazione — in tre versioni |

Copertura: **380/380 partite viste da tutte e tre le fonti**.

## Le cinque riparazioni applicate in lettura

**1 · «Verona» contro «Hellas Verona».** Understat scrive `Verona`, le altre due
`Hellas Verona`: la fusione a monte ha lasciato **2 righe orfane** senza
`Avversario`. È il caso che il §5 del CLAUDE.md porta come esempio storico. Il
dato **non è perso** — la partita c'è già completa sotto l'altra grafia, quelle
2 righe sono un duplicato parziale. Vengono scartate: `762 → 760` righe «Totale».

**2 · La colonna `ID partita` avvelenata.** Ce ne sono **quattro**. Le tre
per-fonte hanno 380 valori distinti; la quarta ne ha **436** perché impila tre
numerazioni (SofaScore ~14M, WhoScored ~1,9M, Understat ~30k). Un join su quella
appaierebbe partite diverse **senza dare errore** — finto pieno (R6). Viene
**rinominata** `ID partita (misto, NON usare)`, non cancellata: cancellarla
nasconderebbe che nel grezzo c'è.

**3 · Colonne dichiarate e vuote.** `Meteo (WhoScored)` è piena allo **0,0%**,
`Tocchi` in `heatmap` al **100% NaN**. Elencate da `colonne_vuote()`.

**4 · Understat perde 2 gol veri.** Il file dichiara 6.616 righe discordanti
(34,6%): 6.597 minuti, 44 tiri, **2 gol**. I gol sono il bersaglio del modello,
quindi istruiti uno per uno:

```
2026-02-15  Nikola Moro    (Bologna)   SofaScore 1 · Understat 0
2025-12-27  Pierre Kalulu  (Juventus)  SofaScore 1 · Understat 0
```

⚠️ L'ipotesi ovvia — «sarà la convenzione sugli autogol» — è **falsa**, e l'ho
verificata invece di assumerla: `Autogol` vale 0 su entrambe le fonti, gli eventi
danno `Gol / regular` con un `Tiro` e uno `scoreChange` allo stesso minuto, e il
nostro snapshot football-data conferma i punteggi (Torino 1-2 Bologna,
Pisa 0-2 Juventus). **Quattro fonti indipendenti concordi**: è una lacuna di
Understat. Le due celle vengono allineate a SofaScore e marcate in
`gol_corretto_da_noi`.

**5 · Chi vince quando due fonti divergono**, dichiarato invece che implicito:

| grandezza | fonte | perché |
|---|---|---|
| gol | SofaScore | verificata su 4 fonti |
| minuti | SofaScore | Understat differisce di ±1-4' su 6.597 righe: è la convenzione sul minuto del cambio, non un errore. Si sceglie per coerenza, non per qualità |
| xG | **entrambe, separate** | sono due *modelli* diversi (971,4 contro 1077,5 di somma stagionale). Fonderle non ha senso; la differenza è informazione |

## L'aggancio, misurato

| file | aggancio a `data/serie_a_matches.csv` |
|---|---|
| `squadre` | **760/760** squadra-partita |
| `giocatori` | **760/760** |
| `heatmap` | **760/760** |
| `eventi_opta` | **760/760** |
| `eventi` | **380/380** partite · **760/760** e **759/759** squadra-partita |

Controprova indipendente: 323 partite appaiate contro lo snapshot,
**323 gol identici, 0 divergenze**.

⚠️ **La grana di `eventi` cambia con la categoria, e sbagliarla sembra un difetto
dei dati.** Cinque categorie su sette descrivono la *partita*: su quelle
`Squadra` è `NaN` per costruzione, e agganciarle per `(data, squadra)` produce
**96.510 righe «orfane» che orfane non sono**. Usa `tf.chiave_di(categoria)`.

## Due limiti che restano — e uno chiuso

✅ **La legenda incompleta è stata chiusa** l'11/08/2026, con una seconda
consegna. La prima (`legenda_v1_incompleta.csv.gz`, 440 righe) lasciava scoperte
**53 colonne**, fra cui *tutto* `eventi_opta`. La seconda (`legenda.csv.gz`, 522
righe, schema diverso) documenta **503 colonne su 503, zero scoperte** —
misurato, non dichiarato: `tf.colonne_non_documentate()` torna vuoto su tutti e
cinque i file, e un test lo inchioda.

La v1 resta nel repo: è l'originale come consegnato (regola 5-ter), il manifesto
ne registra lo sha256, e `tf.legenda(versione="v1")` la legge ancora. Buttarla
renderebbe non verificabile la storia della raccolta.

- **`Spettatori` è `post`, non `pre`**: sta fra `Stadio` e `Capienza`, che sono
  anagrafici, ma si sa solo a partita giocata. Usarlo come feature è
  look-ahead (R8). Vedi `disponibilita()`.
- **Le 6.597 discordanze sui minuti restano**: sono una differenza di
  convenzione fra due fonti, non un errore da correggere. `discordanze()` le
  restituisce.

## ⚠️ Una discordanza dichiarata dal file è FALSA

La terza consegna porta la colonna `Discordanze` anche a livello squadra, e
marca **`possesso` su 760 righe su 762** — praticamente tutte. Sembra dire «le
due fonti non vanno d'accordo sul possesso palla». Misurato, non è così:

```
Ball possession (SofaScore)  →  21-79,   somma 100 fra le due squadre
possession (WhoScored)       →  201-800, somma ~898
```

La prima è una **percentuale**, la seconda un **conteggio**. Non possono
coincidere mai: il flag è vero *per costruzione* e non porta informazione. È
un'unità diversa, non un disaccordo — la regola R7 applicata a una
dichiarazione invece che a una misura.

**Il contro-esempio dimostra che il resto regge**: la discordanza sui `corner`
è marcata su 18 righe, e ri-calcolandola in modo indipendente (SofaScore contro
`cornersTotal`, la colonna omogenea) escono **le stesse 18**, tutte a −1. Lì il
confronto è fra grandezze confrontabili e il file ha ragione.

`discordanze()` e `discordanze_squadra()` tolgono il **token** falso, non la
riga: tutte e 18 le righe con `corner` portano anche `possesso`, e un filtro
per riga le azzererebbe.

## Cosa NON c'è, rispetto a diretta.it

La raccolta è molto più ricca, ma non è un sovrainsieme. Misurato colonna per
colonna e, dove il nome non bastava, **confrontando i valori sulle stesse 760
squadra-partita**:

*Livello squadra* — `Long balls` e `Crosses` di SofaScore sono i **riusciti**
(verificato: 746/760 e 756/760 identici ai «riusciti» di diretta.it), quindi
mancano i **totali** e le **percentuali** di passaggi lunghi e cross. Mancano
del tutto: **xA di squadra**, **xGOT affrontati**, **gol di testa**, e i
**passaggi offensivi**.

*Livello giocatore* — mancano: **passaggi nel terzo finale**, **ingressi nel
terzo finale**, **ingressi in area**, **gol concessi** (l'individuale, quelli
presi mentre era in campo), **sponde**, **colpi di testa verso la porta**,
**grandi occasioni parate**, **salvataggi del portiere**.

**Le due raccolte vanno tenute entrambe.** Non si sostituiscono: diretta.it ha
il dettaglio «riusciti/totali/%» che qui è collassato, e questa ha tre fonti,
gli eventi e le posizioni.
