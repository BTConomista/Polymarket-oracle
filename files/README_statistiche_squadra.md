# Statistiche di SQUADRA per periodo — 5 leghe, 2025-26 (diretta.it / Flashscore)

> **Il primo dato del progetto che separa i due tempi.** Fino al 01/08/2026 ogni
> metrica del repo era di fine partita. Qui ogni squadra-partita esiste in **tre
> righe** — Totale, 1° tempo, 2° tempo — su **45 metriche**. È il dato che serve
> al residuo aperto delle Fasi 96/99: *«il secondo tempo è mal calibrato mentre
> il primo no → serve un modello a due stadi»*.

Vive **accanto** al dato per giocatore, nelle stesse cartelle
`files/diretta_{lega}_{stagione}/`, ed è una cosa diversa: statistiche di
squadra, non aggregati di giocatori (vedi §6).

---

## 1 · Provenienza — da leggere PRIMA di usare questi dati (regola R2)

| | |
|---|---|
| **fonte** | **diretta.it (Flashscore)** — edizione italiana del gruppo Livesport s.r.o. |
| **titolare del dato a monte** | **Opta / Stats Perform**, che diretta.it dichiara come proprio fornitore |
| **come sono stati raccolti** | **a mano dall'utente**. Nessuno scraping, nessuno strumento automatico, nessuna protezione aggirata |
| **data di consegna** | 1 agosto 2026 |
| **chi ha deciso di inserirli** | l'utente (`camarda.federico1@gmail.com`), il 01/08/2026 |

**La posizione di licenza è la stessa già dichiarata per il dato per giocatore, e
non è risolta**: il progetto **non rivendica alcuna licenza** su questi dati e non
li ridistribuisce sotto una licenza propria. Il quadro giuridico per intero —
Termini Livesport, diritto *sui generis* sulla banca dati, distinzione fra
estrazione e reimpiego — è in `files/diretta_serie_a_2526/README.md` §1-bis e in
`docs/CACCIA_EVENT_DATA.md` §1. È una **valutazione di rischio civile presa
consapevolmente dal titolare del repo**, non un fatto tecnico e non
un'assoluzione: chiunque deve poterla valutare da sé.

---

## 2 · I file, e cosa contengono

In ognuna delle 5 cartelle `files/diretta_{lega}_2526/`:

| file | cos'è |
|---|---|
| `squadra_per_partita.csv.gz` | una riga per **(squadra, partita, periodo)**, 53 colonne |
| `legenda_squadra.csv` | 35 statistiche → codice della fonte (es. `Calci d'angolo` → 16) |
| `note_fonte.csv` | il foglio «Note» della fonte, conservato **come dichiarazione** (⚠️ contiene un'affermazione falsa: §4.2) |
| `manifesto_squadra.json` | perimetro e copertura attesa, che il caricatore verifica |

**Peso totale: 604 KB** per tutte e 5 le leghe, contro ~11 MB di `.xlsx`.

| lega | righe | di cui campionato | play-off | partite | squadre |
|---|--:|--:|--:|--:|--:|
| Serie A | 2.280 | 2.280 | 0 | 380 | 20 |
| Premier League | 2.280 | 2.280 | 0 | 380 | 20 |
| La Liga | 2.280 | 2.280 | 0 | 380 | 20 |
| Bundesliga | 1.850 | 1.836 | 14 | 306 | 18 |
| Ligue 1 | 1.860 | 1.836 | 24 | 306 | 18 |
| **totale** | **10.550** | **10.512** | **38** | **1.752** | |

Il foglio wide «Per partita» degli `.xlsx` **non** è conservato: è un reshape
esatto del foglio long, verificato su entrambe le metà (colonne `Casa -` e
`Ospite -`), **0 celle divergenti** su 102.600 / 83.700 / 83.250. È una vista,
non un dato in più.

---

## 3 · La verifica indipendente eseguita all'inserimento (01/08/2026)

Non ci si è fidati della dichiarazione della fonte. Due controlli forti, contro
**football-data.co.uk**, che è una fonte completamente diversa.

### 3.1 · Contro i nostri snapshot

| controllo | esito |
|---|---|
| **join** (data + squadra + avversario) su tutte e 5 le leghe | **3.504/3.504 team-partita = 100,00%** |
| **risultato** coerente con lo snapshot | **3.504/3.504 = 100,00%** |
| **additività** `1T + 2T (+ Suppl.) = Totale` sulle metriche di conteggio | **137.124/137.124 celle**, 0 violazioni |
| round-robin completo, casa/trasferta bilanciate, 0 duplicati | 5 leghe su 5 |

### 3.2 · Contro i conteggi grezzi di football-data (le stesse metriche, altro fornitore)

Su **3.504 lati-partita**, periodo Totale:

| metrica | accordo esatto | scarto medio |
|---|--:|--:|
| Cartellini rossi | 99,74% | +0,0014 |
| Falli | 99,57% | +0,0006 |
| Calci d'angolo | 99,34% | −0,0040 |
| Tiri in porta | 99,03% | +0,0023 |
| Cartellini gialli | 97,86% | +0,0148 |
| Tiri totali | 97,72% | −0,0080 |

Lo scarto medio è ~0 su tutte: **non c'è differenza sistematica di definizione**,
è rumore di raccolta ±1 fra due fornitori. È anche la prova che i vuoti valgono
**zero** (§4.1): se significassero «ignoto», riempirli di zeri avrebbe distrutto
l'accordo sul 90% delle righe.

### 3.3 · Lo split 1T/2T è genuino, e non è invertito

Il controllo decisivo: i gol del primo tempo **dedotti dal file** contro
`HTHG/HTAG` di football-data, che sono i gol veri dell'intervallo.

| | accordo |
|---|--:|
| gol del **1° tempo** | **3.444/3.502 = 98,34%** |
| gol del **2° tempo** | **3.428/3.502 = 97,89%** |
| distribuzione dello scarto | `0` in 6.872 casi, `−1` in 131, `−2` in 1, **`+1` mai** |

Lo scarto è **a senso unico** perché gli autogol non entrano nell'xGOT di chi ne
beneficia: la deduzione può solo **sottostimare**. Con le etichette invertite
l'accordo crolla a 77/380 e 66/380 e compaiono 144 e 167 casi fisicamente
impossibili — quindi «1° tempo» è davvero il primo tempo.

---

## 4 · Le cinque cose che si sbagliano leggendo questi file

Tutte misurate, tutte con un test che le fissa (`tests/test_team_stats.py`).

### 4.1 · Il vuoto è uno ZERO, non un dato mancante
Tre colonne (`Cartellini gialli`, `Cartellini rossi`, `Gol di testa`) sono vuote
quando la statistica vale zero: il sito omette la riga. Fino al **94%** di NaN.
Caricarle come mancanti **non farebbe sparire dei cartellini: farebbe sparire gli
zeri**, gonfiando ogni media per partita. Il file su disco resta fedele alla
fonte (regola R3, nessuna modifica silenziosa); è `load_team_matches()` a
riempirli, con `zeri_espliciti=True`.

### 4.2 · ⚠️ La fonte documenta male sé stessa: i supplementari
Il foglio «Note» della Bundesliga dichiara *«i tempi supplementari NON sono
compresi nel Totale»*. **È falso.** Sull'unica partita con supplementari
(spareggio di ritorno, 25/05/2026) `1T+2T+Suppl = Totale` torna su **39/39**
metriche additive per entrambe le squadre, `1T+2T` solo su 8 e 7. È un errore
della *documentazione*, non del dato — ed è il motivo per cui `note_fonte.csv` è
conservato: per poter mostrare la differenza fra il dichiarato e il misurato (R4).

### 4.3 · Le righe `Play-off` non sono campionato
Bundesliga (2 partite) e Ligue 1 (4) includono gli spareggi
promozione/retrocessione, che coinvolgono club di **seconda divisione** (Paderborn,
Rodez, Red Star) assenti dai nostri snapshot. `load_team_matches()` le esclude di
default; la colonna `Fase` resta a dichiararle. ⚠️ In Ligue 1 si **sovrappongono
per data** alla stagione regolare (12→29 maggio contro un campionato che finisce
il 17): **solo `Fase` le separa, mai la data.**

### 4.4 · ⚠️ Una partita è incompleta, e sembra completa (R6, «finto pieno»)
**Nantes-Toulouse, 17/05/2026, giornata 34 di Ligue 1.** Il 2° tempo manca alla
fonte (42/45 metriche vuote) e la riga `Totale` **coincide esattamente con il
1° tempo** su tutte e 45 le metriche: 146 passaggi totali, impossibili in una
partita intera. È una riga che *sembra* il totale di una partita e copre 45
minuti.
⚠️ **football-data concorda** con quei totali su tutte e 6 le metriche
confrontabili: non è un difetto di diretta.it, ed è per questo che **la causa non
è accertata** dai dati che abbiamo — la si dichiara invece di inventarla (R5).
Nota che l'additività `1T+2T=Totale` **torna lo stesso** su questa partita,
perché il Totale è troncato quanto la somma: l'additività non certifica la
copertura.

### 4.5 · `Risultato squadra` ed `Esito` sono di FINE partita, anche sulle righe di periodo
Sono identici nelle tre righe (3.504/3.504): la riga «1° tempo» porta il
risultato **finale**. È il caso da manuale della regola **R8** — un dato `post`
incollato su una riga che sembra descrivere un periodo. E ne segue una cosa da
sapere: **il punteggio all'intervallo NON è in questo dataset**. Va preso da
`HTHG/HTAG`, o dedotto accettando l'errore di §3.3.
Inoltre `Risultato squadra` è scritto **dal punto di vista della riga** (invertito
in trasferta): leggerlo come casa-ospite sbaglierebbe il segno su tutte le
partite non pareggiate.

### 4.6 · Due tackle impossibili
`Tackles riusciti` (4) > `Tackles totali` (3) in **2 righe su 10.512** — Barcelona
25/04/2026 e Napoli 11/05/2026, entrambe nel 2° tempo, entrambe con `Tackles %` a
**133**. Incoerenza della fonte, non corretta (R3) e non nascosta (R4).

---

## 5 · ⏱️ Disponibilità temporale (regola R8)

| colonne | ⏱️ |
|---|---|
| `Giornata`, `Data`, `Squadra`, `Campo`, `Avversario`, `Periodo`, `Fase` | **`pre`** |
| `Risultato squadra`, `Esito` | **`post`** (vedi §4.5) |
| **tutte le 45 metriche** | **`post`** |

**Forma normale d'uso**: `team_stats.team_form()`, che aggrega le partite
**precedenti** (`shift(1)`). Il parametro `periodo=PERIODO_1T` dà la forma del
solo primo tempo — che è la ragione per cui questo dataset esiste. **Mai** le
colonne `post` della partita in corso.

---

## 6 · Non è un doppione del dato per giocatore

Le metriche **continue** non si ricostruiscono sommando il partita-per-partita
dei giocatori: l'xG combacia in **55/758** celle, l'xGOT in 104/758, l'xA in
66/758. Le discrete sì (97,5-100%). Quindi questo file è **misura autonoma**, non
un aggregato — e in ogni caso il per-giocatore non esiste per Bundesliga e
Ligue 1, e non ha lo split 1T/2T.

---

## 7 · Schema: normalizzato, perché la fonte non lo era

I 5 file consegnati avevano **quattro ordini di colonna diversi**: ogni file segue
l'ordine con cui il sito mostrava le statistiche per *quella* lega (verificato
contro il foglio Legenda di ciascuno — è coerenza della fonte, non corruzione).
`scripts/registra_raccolta_squadra_diretta.py` normalizza su un ordine unico e
aggiunge `Fase` dove manca, così il repo mantiene la garanzia di schema identico
fra leghe. **Corollario**: le colonne si leggono per **nome**, mai per posizione.

Sono stati aggiunti **18 alias** a `src/data/sources.py` — esonimi italiani
(`Nizza`→`Nice`, `Colonia`→`FC Koln`, `Brema`→`Werder Bremen`…). Senza, il join
si fermava a **264/612** in Ligue 1 e **60/612** in Bundesliga.

---

## 8 · Come si usa, e come si aggiunge una raccolta

```python
from src.data import team_stats as ts

ts.load_team_matches("serie_a", "2526")          # campionato, vuoti a zero
ts.load_team_matches(tutte=True)                 # 10.512 righe, 5 leghe
ts.load_team_matches("ligue_1", "2526", solo_campionato=False)   # + play-off
ts.periodi_affiancati(...)                       # 1T/2T/Totale in colonne
ts.team_form(..., periodo=ts.PERIODO_1T)         # ⏱️ l'unica forma sicura (R8)
```

```bash
python scripts/registra_raccolta_squadra_diretta.py \
    --xlsx ~/Bundesliga_202627_STATISTICHE_SQUADRA.xlsx \
    --lega bundesliga --stagione 2627
```

Lo script **verifica prima di accettare** e si ferma se qualcosa non torna:
colonne canoniche · date leggibili · tre periodi per squadra-partita ·
round-robin completo e casa/trasferta bilanciate · nessun duplicato ·
additività dei periodi · e — dove esiste uno snapshot — **join totale e
risultato coerente** contro di esso, che è il controllo forte perché la fonte è
indipendente. Aggiungere una lega o una stagione **non richiede di toccare
`src/`**.

> ⚠️ Il manifesto si chiama `manifesto_squadra.json`, non `manifesto.json`: non è
> pignoleria. `player_stats.raccolte()` scopre le raccolte cercando
> `manifesto.json`, quindi le cartelle che contengono **solo** dati di squadra
> (Bundesliga e Ligue 1) restano invisibili a quel caricatore invece di farlo
> fallire su un file che non c'è. I due dataset convivono senza vedersi, e un
> test lo verifica.

---

## 9 · Stato e limiti dichiarati

**Dati inseriti + caricatore e 28 test (01/08/2026). Nessuna feature costruita,
nessun backtest eseguito, nessun modello li usa.**

1. **Una stagione sola.** 1.752 partite di campionato, tutte 2025-26. Non regge
   un walk-forward multi-stagione: la finestra di addestramento non esiste.
2. **Potenza.** 1.752 partite sono sopra le ~574 che la Fase 98 stima servire per
   l'80% di potenza sull'1X2 — ma quel calcolo vale per un confronto col mercato
   su partite indipendenti, non per uno studio 1T/2T su una stagione singola. Un
   risultato **nullo** sarà meno conclusivo di quanto sembri, e va detto **prima**
   del test, non dopo.
3. **Il punteggio all'intervallo non c'è** (§4.5): senza, il modello a due stadi
   condizionato al risultato dell'intervallo ha bisogno di `HTHG/HTAG` da
   football-data, oppure della deduzione con l'errore misurato di §3.3.
4. **`Gol evitati` e `xGot affrontati` sono un modello**, non una misura: l'xGOT
   di Opta ha una ricetta non pubblica ed è diverso dall'xG di Understat che il
   repo già usa (correlazione ~0,93, medie 1,35 vs 1,50). Non mescolarli.
