# Le sette trappole, in ordine di costo

Ognuna è stata incontrata davvero. Le prime tre non fanno rumore: producono un
numero plausibile e sbagliato, che è la categoria peggiore.

---

## 1 · Due convenzioni di `X` nello stesso bundle ⚠️ la più cara

Nella stessa cartella, due file, la stessa lettera, significati **opposti**:

| file | `X` significa | 0 è | 100 sarebbe |
|---|---|---|---|
| `heatmap.csv.gz` | posizione lungo il campo | **porta propria** | porta avversaria |
| `eventi.csv.gz` (categoria `Tiro`) | **distanza dalla porta avversaria** | **linea di porta avversaria** | la porta opposta |

Stessa scala (centesimi di lunghezza del campo), origine ai due capi opposti. Nei
tiri realmente osservati la `X` arriva a 67,6 in Serie A, 74,2 in Liga e 89,3 in
Premier — quel massimo è un tiro da centrocampo, non un valore fuori scala.

La heatmap è già **normalizzata per la direzione d'attacco**: non serve
ribaltare le squadre in trasferta, ci ha pensato la fonte.

Per disegnare un tiro sullo stesso campo della heatmap serve la conversione:

```python
x_frame_heatmap = 100 - X_tiro
```

**Perché non fa rumore:** entrambe le colonne stanno in 0-100, entrambe hanno
valori credibili, *nessun controllo di intervallo si accorge di niente*. Il caso
concreto: un **rigore** ha `X = 11,5`. Disegnato senza la conversione finisce a
11,5 nel frame della heatmap, cioè **davanti alla porta del suo portiere**. La
mappa dei tiri esce con il grappolo dalla parte sbagliata del campo, e la
conclusione sarà «che strano» invece di «ho invertito un asse».

**Il controllo che lo prende, e costa due righe.** Il dischetto del rigore è il
punto di taratura gratuito: sta sempre nello stesso posto, in ogni lega e in ogni
stagione.

```
Serie A : 106 rigori, X media 11.50, Y media 50.00
Premier :  92 rigori, X media 11.50, Y media 50.00
La Liga : 134 rigori, X media 11.50, Y media 50.00
```

**332 rigori su 332** identici a due decimali, su tre campionati raccolti in
momenti diversi. Se questo numero non torna, la convenzione non è quella che
credi: **fermati**.

## 2 · Il rigore da solo non dice il VERSO

Il dischetto conferma la scala, non l'orientamento: una `X` invertita
(0 = porta avversaria) darebbe lo stesso 11,5 se anche i rigori fossero
invertiti. Serve un secondo controllo, indipendente, e il ruolo lo fornisce
gratis — la `X` media deve **crescere** da portiere ad attaccante:

| ruolo | Serie A | Premier | La Liga |
|---|--:|--:|--:|
| portiere | 10,2 | 10,8 | 10,6 |
| difensore | 39,5 | 40,8 | 40,2 |
| centrocampista | 51,0 | 52,8 | 52,9 |
| attaccante | 61,6 | 61,0 | 62,2 |

Monotòna in tutte e tre, e con valori così vicini fra campionati diversi da
essere di per sé una conferma che la scala è la stessa. Due controlli
indipendenti: la scala (rigori) e il verso (ruoli). `heatmap_giocatore.py` li
esegue entrambi e **esce con errore** se uno fallisce, invece di produrre numeri.

## 3 · Il nome non è un'identità

Nell'archivio delle coppe europee convivono **due Haaland**:

| ID | chi | dove |
|---|---|---|
| `839956` | Erling Haaland | Manchester City |
| `1126486` | un omonimo | SK Brann, 12 partite fra Champions ed Europa League |

Un `grep "Haaland"` li fonde, e il risultato — statistiche di due giocatori
diversi sommate — non ha nessun segno esterno di essere sbagliato.

Non è una sorpresa: il progetto lo sa già per gli allenatori
(`allenatori.conflitti_identita()` trova 11 omonimi). Vale identico per i
giocatori. **Si seleziona per `ID giocatore`, sempre**; se hai solo il nome,
verifica che corrisponda a un ID unico prima di procedere — lo script si ferma se
ne trova più di uno, e ti dà i comandi da rilanciare:

```
$ heatmap_giocatore.py --lega premier_league --giocatore "Silva"
'Silva' corrisponde a 3 giocatori diversi:
  --id 331209   Bernardo Silva
  --id 856260   Josh Dasilva
  --id 1011895  Jota Silva
Il nome non basta a identificare: ri-lancia con --id.
```

Nota il terzo caso, che è la ragione per cui la ricerca è per sottostringa e non
per cognome: **`Josh Dasilva`** contiene «silva» senza chiamarsi Silva. Un filtro
scritto a mano su un cognome può prendere di più di quello che intende, e in
silenzio.

## 4 · Ogni tiro è scritto due volte

`eventi.csv.gz` categoria `Tiro` contiene una riga per tiro **per fonte**:

```
tiri di Malen: 140 righe -> SofaScore 70, Understat 70
```

Senza filtro sulla colonna `Fonte`, i tiri raddoppiano e ogni per-90 è il doppio
del vero. E il de-duplicato ingenuo **non funziona**: le coordinate delle due
fonti differiscono di poco, quindi un `drop_duplicates` su
`(Data, Minuto, X, Y)` non unisce niente — 140 righe restano 140.

Si scegli**e una fonte** e si dichiara quale. Qui SofaScore, perché è la stessa
che produce la heatmap: così posizioni e tiri stanno nella stessa convenzione.

## 5 · Le posizioni non sono i tocchi

Confronto sulle stesse 18 partite di Malen:

| | |
|---|--:|
| punti in `heatmap.csv.gz` | 605 |
| «Palloni toccati» in `diretta_serie_a_2526` | 492 |
| correlazione partita per partita | **0,95** |
| scarto | **+23%** |

Correlazione altissima, livello diverso: sono **due convenzioni**, non un
errore. La heatmap campiona la *posizione* del giocatore, non solo l'istante in
cui tocca il pallone.

Conseguenza pratica: il numero di punti di una heatmap **non è** un conteggio di
tocchi e non va confrontato con quello di un'altra fonte. Le mappe si leggono
come *forme*; per il volume si usa la colonna che il volume lo misura davvero.

## 6 · `Tocchi` è vuota al 100%

La colonna `Tocchi` di `heatmap.csv.gz` è `NaN` su tutte le righe, in **entrambe**
le leghe. Essendo vuota su due consegne indipendenti è un fatto del formato, non
un incidente. Dichiarata nel manifesto e da `tre_fonti.colonne_vuote(lega)`.

È il caso buono: un buco **dichiarato** è innocuo. Il pericolo è il finto pieno
(regola R6 del `CLAUDE.md`) — e qui non ce n'è, perché il campo è vuoto invece di
contenere uno zero che sembra una misura.

## 7 · «Il dato non esiste» ha una data di scadenza

Alle 14:13 le posizioni di Haaland non erano nel repo. Verificato bene, con
**tre meccanismi diversi** (regola 3 della skill di raccolta):

| tentativo | esito |
|---|---|
| `curl` diretto | 403 |
| `curl` con User-Agent da browser | 403 |
| Chromium vero, chiamata same-origin dall'interno del sito | **403 sulla pagina stessa** |

E con la diagnosi del **livello** del blocco, che è la parte utile: nella stessa
prova `understat.com` e `football-data.co.uk` rispondevano **200**. Quindi non
era la rete né il proxy: era il bordo di SofaScore contro questo indirizzo. Un
403 «di rete» si aggira cambiando ambiente; un 403 «del sito» no.

Alle 14:36 un commit ha aggiunto il bundle e la heatmap c'era.

**Cosa ha salvato l'analisi:** la conclusione era scritta *«non è in questo
progetto»*, con il perimetro accanto — non *«non esiste»*. Dichiarare
un'assenza **con il perimetro e il commit** è la differenza fra una frase che si
aggiorna e una pista chiusa per sbaglio.

**E poi è successo di nuovo, mentre scrivevo questo capitolo.** La tabella del
perimetro diceva «La Liga: nessuna coordinata». Un'ora dopo il commit `e663302`
ha aggiunto `files/tre_fonti_la_liga_2526/` con **570.768 posizioni**, e la
tabella era da riscrivere una seconda volta.

Due volte in un'ora, sullo stesso quaderno. Il perimetro dei dati di questo
progetto si muove più veloce della documentazione che lo descrive: per questo
ogni tabella di copertura qui dentro porta il comando per **ri-generarsela**
invece del solo elenco.

## 7-bis · Un `git log` corto non è una storia corta

Corollario dello stesso errore, sul repo invece che sui dati. Cercando quei
commit ho concluso che il `main` locale contenesse **43 commit unici** — raccolte
giornaliere, coppe, allenatori — assenti da `origin/main`. Stavo per segnalare
del lavoro perso.

Era falso. Il clone è **shallow** (troncato): sotto il punto di taglio git non
vede niente, e `git log origin/main | grep <soggetto>` risponde «non c'è» per un
commit che c'è benissimo.

```bash
git rev-parse --is-shallow-repository      # true  → NON fidarti dei conteggi
git fetch --deepen=200 origin main         # 57 commit visibili → 444
git merge-base --is-ancestor main origin/main   # ✅ antenato puro, zero perso
```

Prima di dire «questo commit non esiste sul remoto», controlla se stai guardando
una storia intera. E la domanda giusta non è mai «quanti commit divergono» —
quello è un conteggio — ma **`git merge-base --is-ancestor`**, che risponde alla
domanda vera: *c'è del lavoro solo qui?*

---

## Il vincolo che non è tecnico

`understat.com` risponde 200, copre la Premier, e **non si scarica**: il suo
`robots.txt` vieta tutto (`Disallow: /`) e il progetto l'ha messo in
sola-lettura-da-cache alla Fase 120. Raggiungibile non significa lecito.

Quando si chiude una fonte va scritto **a quale livello** sta il vincolo — legale
o tecnico — perché un vincolo tecnico scade (il caso Playwright del
`MANUALE_SOPRAVVIVENZA`, dove una pista era stata chiusa con una motivazione che
il tempo ha smentito) e un vincolo legale no.
