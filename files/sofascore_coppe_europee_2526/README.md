# Coppe europee 2025-26 — raccolta SofaScore

Consegnata dall'utente l'**11/08/2026** in otto file. È la prima volta che il
progetto ha dati sulle **competizioni UEFA**: fino a qui il perimetro storico
erano i 5 campionati (16.111 partite) e le 6 coppe nazionali 2025-26 (662),
e l'Europa era un buco dichiarato.

**Fonte**: SofaScore. **Estrazione**: 11 agosto 2026 (dichiarata dalla fonte
stessa nel foglio `Note e copertura` di `originale_sofascore.xlsx`).

---

## Cosa c'è

**912 partite**: 281 Champions, 271 Europa, 360 Conference — dal **1° turno
preliminare alla finale**, qualificazioni comprese.

| file | righe | colonne | partite coperte |
|---|--:|--:|--:|
| `giocatori.csv.gz` | 40.067 | 104 | 912 |
| `statistiche_squadra.csv.gz` | 86.807 | 12 | 728 |
| `eventi.csv.gz` | 21.152 | 21 | 912 |
| `tiri.csv.gz` | 16.929 | 20 | 643 |
| `momentum.csv.gz` | 61.758 | 9 | 665 |
| `cambi.csv.gz` | 8.268 | 14 | 911 |

Più i due **originali come consegnati** (regola §5-ter del CLAUDE.md: senza
l'originale, un bug della nostra conversione diventa indistinguibile dal dato):

- `originale_giocatori.xlsx` — un foglio, uguale a `giocatori.csv.gz`;
- `originale_sofascore.xlsx` — **sette fogli**, e tre di questi **non hanno un
  CSV corrispondente**: `Partite` (912 × 40), `Posizioni medie` (19.848 × 11),
  `Colori maglie` (912 × 11), oltre a `Note e copertura`.

⚠️ **Il foglio `Partite` è il più ricco della consegna e vive SOLO nell'`.xlsx`**:
risultati per tempo/supplementari/rigori, moduli, allenatori, stadio con
capienza e coordinate, spettatori, e l'**arbitro con lo storico di carriera**.

**Fedeltà della conversione**: i sei `.csv.gz` rileggono **identici** ai CSV
consegnati — **6.662.998 celle confrontate, 0 divergenti**.

---

## La copertura è a STRATI, e lo strato si vede da un numero solo

Il riempimento mediano delle 91 colonne-metrica di `giocatori` è **19,5%**, che
letto male sembra un dato mezzo vuoto. Non lo è: sono tre cose diverse
sovrapposte, e vanno separate prima di usarlo.

**1. 269 partite su 912 non hanno NESSUNA statistica** — solo formazione e
risultato. La colonna-spia è `Minuti giocati`: chi scende in campo ne ha per
forza, quindi una partita in cui *nessuno* ha minuti è una partita senza dati.

| dove mancano | partite |
|---|--:|
| Conference — 2° e 3° turno preliminare | 113 |
| Europa — preliminari e spareggi | 82 |
| Champions — 1°, 2°, 3° turno preliminare | 55 |
| Conference — spareggi | 19 |

Sono i **preliminari minori**, e il confine è netto: dalla fase campionato in
poi c'è tutto. Le 643 partite con statistiche sono **esattamente** le 643 con i
tiri — due segnali indipendenti che concordano.

**2. Il 29,5% delle righe sono panchinari mai entrati.** `NaN` legittimo, non
un buco: la riga esiste perché la formazione li elenca.

**3. Molte colonne sono eventi RARI.** `Rigori parati` allo 0,10%, `Autogol`
allo 0,13%: lì il `NaN` significa zero. Sulle sole righe di chi è sceso in
campo il riempimento mediano sale a **39,8%**, con **19 colonne su 90 oltre il
90%**.

Controlli di coerenza fatti: i minuti sommano a **990 di mediana** per
squadra-partita (38 fuori dalla forchetta 900-1100 su 1.286, coerente con le
espulsioni); i gol del foglio `Partite` coincidono con quelli contati negli
eventi nel **98,6% / 98,5%** dei casi (il residuo non è un difetto: i gol di
partita e i rigori della serie finale sono tipi separati).

Colonne dichiarate ma **vuote**, da non scambiare per dati: `Valore di mercato`
**0,00%**, `Superficie` 0,1%. `Spettatori` è al 50,9%, come la fonte dichiara.

---

## ⚠️ Due trappole MISURATE, da leggere prima di usare questi dati

### 1. I nomi delle squadre NON sono i nostri, e il quasi-uguale è peggio del diverso

Su **96 squadre** dei nostri cinque campionati 2025-26, **solo 13 combaciano
per nome esatto** con SofaScore:

| lega | trovate per nome esatto |
|---|--:|
| Serie A | 5/20 |
| Premier | 4/20 |
| La Liga | 2/20 |
| Ligue 1 | 2/18 |
| **Bundesliga** | **0/18** |

`Bayern Munich` è `FC Bayern München`, `Barcelona` è `FC Barcelona`, `Roma` è
`AS Roma`, `Man City` è `Manchester City`. Un join per nome esatto trova **150
partite su 912** e quel numero è **falso per difetto** — non è la misura di
quante partite ci riguardano, è la misura di quanto sono diversi i nomi.

⚠️ **E il fuzzy matching non è la soluzione**: applicato qui produce
`Alaves → Ilves`, `Celta → Celtic`, `Angers → Rangers`,
`Man United → Dundee United`, `FC Koln → FC Koper`, `Paris FC → Paksi FC`.
Sei accoppiamenti **sbagliati** su squadre reali, che un join accetterebbe in
silenzio. È la stessa famiglia del bug «Hellas Verona» già pagato dal progetto
(§5 del CLAUDE.md).

**Serve una tabella di alias verificata a mano**, come `TEAM_ALIASES` in
`src/data/sources.py`. Finché non c'è, **questi dati non si agganciano al
resto del repo**.

### 2. Lo storico dell'arbitro è al momento dell'ESTRAZIONE, non della partita (R8)

Il foglio `Partite` porta `Partite arbitro`, `Gialli arbitro`, `Rossi arbitro`,
`Gialli per partita`. Sono i totali di carriera **all'11 agosto 2026** — cioè
**dopo** ogni partita del file.

Usarli per prevedere una gara del 2025 è **look-ahead**: il numero è giusto, è
il *momento* a essere sbagliato, ed è l'errore più difficile da vedere perché
il dato non ha niente di anomalo. Per una feature legittima va ricostruito il
valore **alla data della partita**, contando solo le gare precedenti — la
forma normale che `allenatori.esperienza_prima()` già usa per gli allenatori.

Disponibilità temporale delle altre colonne: `pre` per arbitro designato,
stadio, capienza, coordinate; `post` per tutto il resto (moduli e formazioni
sono noti ~1h prima, ma qui arrivano a partita finita).

---

## Cosa NON c'è, e la fonte lo dichiara

- **Nessuna quota** — né pre-partita né chiusura. Il confronto col mercato,
  che è il metro di tutto il progetto, qui **non è possibile** con questi dati.
- Cronaca testuale, migliori in campo, serie aperte, heatmap per giocatore:
  esistono su SofaScore, non sono stati raccolti.
- **Meteo**: non c'è su SofaScore (sta su WhoScored).
- **Understat non copre le competizioni UEFA** → per queste 912 partite non
  esiste l'xG della fonte che usiamo sui campionati. L'xG dei tiri qui è di
  SofaScore: **un'altra definizione**, da non mescolare con `home_xg`/`away_xg`
  degli snapshot senza prima misurarne la scala (regola R2).

---

## Stato: RACCOLTO, non USATO

Nessun modello legge questi file, e non c'è ancora un loader in `src/data/`.
È uno stato legittimo e dichiarato (§5-ter): raccogliere e usare sono due
decisioni separate, e il dato non recuperabile è quello che non si prende.

Prima di poterli usare servono, in ordine: **(a)** la tabella di alias delle
squadre, **(b)** un ponte partita→`game_id` verso il resto del repo,
**(c)** la ricostruzione R8-sicura dello storico arbitro.
