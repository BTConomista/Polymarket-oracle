# Statistiche per giocatore, Serie A 2025-26 — diretta.it / Flashscore

> **Il primo dato "Tier B" mai entrato nel progetto.** Fino al 31/07/2026 il
> progetto aveva, per ogni giocatore, solo minuti/gol/assist/cartellini. Qui ci
> sono **97 statistiche per giocatore per partita** — tocchi, passaggi, dribbling,
> contrasti, recuperi, falli individuali, xG/xA individuali — cioè esattamente
> l'elenco che `docs/PIANO_DATABASE_GIOCATORI.md` §1.2 e le righe 4-7/17-21 della
> checklist §1.9 davano come **irraggiungibile**.

---

## 1 · Provenienza — da leggere PRIMA di usare questi dati (regola R2)

| | |
|---|---|
| **fonte** | **diretta.it (Flashscore)** — edizione italiana del gruppo Livesport s.r.o. |
| **titolare del dato a monte** | **Opta / Stats Perform**. diretta.it dichiara sul proprio sito: *«Utilizziamo Opta come fornitore di dati sul calcio per tutte le principali competizioni»* |
| **come sono stati raccolti** | **a mano dall'utente**, aprendo il sito e trascrivendo, poi aggregando. **Nessuno scraping**, nessuno strumento automatico, nessuna protezione aggirata |
| **data di estrazione** | 31 luglio 2026 |
| **chi ha deciso di inserirli** | l'utente (`camarda.federico1@gmail.com`), il 31/07/2026, dopo che la sessione aveva esposto il quadro di §1-bis |

### 1-bis · Cosa NON stiamo rivendicando

**Il progetto non rivendica alcuna licenza né alcun diritto su questi dati**, e
non li ridistribuisce sotto una licenza propria. Sono qui **con la provenienza
dichiarata**, il che è precisamente ciò che distingue una **fonte dichiarata**
(regola R2) da una **fonte avvelenata** — cioè da uno scrape ricaricato da terzi
sotto una licenza che chi la dichiara non ha il diritto di concedere. Il progetto
ne ha respinte **cinque** con quel profilo (`docs/CACCIA_EVENT_DATA.md` §2, §3).

**Il quadro giuridico, per onestà e per intero** (`docs/CACCIA_EVENT_DATA.md` §1):
- i **Termini d'uso Livesport** vietano lo scraping **per nome** (cl. 2.10),
  rivendicano il **diritto sui generis** sulla banca dati (cl. 2.9) e limitano
  all'**uso personale** (cl. 2.2);
- la raccolta manuale **non è scraping**: la cl. 2.10 non è quindi in gioco;
- ma il **diritto sui generis** (Dir. 96/9/CE art. 7) copre l'estrazione di una
  parte sostanziale *«con qualsiasi mezzo e in qualsiasi forma»* — il metodo di
  raccolta non lo tocca, e **379 partite su 380 sono il 99,7% di una stagione**;
- il repo è **pubblico**: la pubblicazione è **reimpiego**, un atto distinto
  dall'estrazione e a sua volta riservato.

**È una valutazione di rischio civile, presa consapevolmente dal titolare del
repo**, non un fatto tecnico e non un'assoluzione. È scritta qui perché chiunque
— noi fra sei mesi, o un terzo — deve poterla valutare da sé invece di ereditarla
implicitamente. *(Regola R4: un'anomalia si dichiara anche quando non è un
errore.)*

---

## 2 · I file

| file | righe × col | cos'è |
|---|---|---|
| `partita_per_partita.csv.gz` | **11.894 × 108** | una riga per **giocatore-partita** (solo chi è sceso in campo: titolari + subentrati) |
| `riepilogo_stagionale.csv.gz` | **607 × 107** | una riga per **giocatore-stagione**, somme e medie. ⚠️ **derivato**, non una misura indipendente: è la somma del file sopra |
| `legenda.csv` | 97 × 3 | mappa `codice fonte → etichetta italiana` (es. `BALL_RECOVERIES` → «Palloni recuperati`) |

I tre file caricati in origine erano **cinque**: due `.xlsx` partita-per-partita,
due `.xlsx` di riepilogo e un `.csv`. Verificato con `DataFrame.equals`: i tre
partita-per-partita contengono **dati identici** (`True` su valori e colonne) e i
due riepiloghi pure — le copie `_1` differivano solo per il foglio
`Note e copertura`, il cui contenuto è confluito in questo README. Qui è
conservata **una sola copia** di ciascuno, in CSV compresso: **868 KB** contro i
**29 MB** degli `.xlsx` originali.

---

## 3 · Copertura, e l'unico buco (dichiarato dalla fonte stessa)

- **379 partite su 380** hanno le statistiche per giocatore;
- **758 team-partita**, 20 squadre, **584 giocatori** distinti;
- finestra: **23/08/2025 → 24/05/2026** (stagione completa).

> ⚠️ **UNICA PARTITA SENZA STATISTICHE: Lecce-Como 0-3, giornata 17, 27/12/2025.**
> Su diretta.it quella partita ha **solo i rating**: tutte le statistiche per
> giocatore sono assenti **alla fonte**. Effetto: **Como e Lecce hanno 37 partite
> invece di 38** nel file partita-per-partita e nei totali del riepilogo. I 29
> rating disponibili per quella partita sono in `note_coverage_lecce_como.csv`.

**Colonne escluse a monte perché sempre a zero in tutta la stagione**: legni
colpiti, rigori segnati/sbagliati/parati nella serie finale.

---

## 4 · Verifica indipendente eseguita al momento dell'inserimento (31/07/2026)

Non ci si è fidati della dichiarazione della fonte: è stata **controllata contro
i nostri snapshot**, che vengono da football-data.co.uk, cioè da una fonte
**completamente diversa**.

| controllo | esito |
|---|---|
| **join** al nostro `data/serie_a_matches.csv` (data + squadra + avversario) | **758/758 team-partita = 100,00%** |
| **nomi squadra** | **zero alias necessari** — tutti e 20 combaciano già con i nostri |
| **coerenza dei gol**: `gol dei giocatori + autogol degli avversari == risultato dello snapshot` | **758/758 = 100,00%** |
| partite dello snapshot senza dati diretta | **1**, ed è **esattamente** quella dichiarata (Lecce-Como 27/12/2025) |
| minuti per squadra-partita | mediana **990** = 11 × 90 ✓ (min 890: partite con espulsione) |
| giocatori per squadra-partita | 13-16, mediana 16 ✓ |
| completezza delle colonne Tier B | **100%** su tutte (tocchi, passaggi, dribbling, contrasti, intercetti, recuperi, falli, xG/xA). Il `Rating` è al **91,9%**, l'unica sotto |

**758 verifiche indipendenti, 758 passate.** La dichiarazione di copertura del
file è onesta e il dato è coerente con una fonte terza.

---

## 5 · ⏱️ Disponibilità temporale (regola R8) — leggere prima di costruire feature

**Quasi tutto qui dentro è `post`**: esiste solo a partita finita. Usarlo per
prevedere la partita che l'ha prodotto è look-ahead.

| colonne | ⏱️ |
|---|---|
| `Giornata`, `Data`, `Squadra`, `Campo`, `Avversario` | **`pre`** |
| `Giocatore`, `Ruolo` | `statico` |
| `Titolare/Subentrato` | `post` nel dato storico — ⚠️ diventa **`pre`** solo se raccolto dalla formazione ufficiale ~1h prima |
| `Risultato squadra`, `Esito` | **`post`** |
| **tutte le 97 statistiche** (tocchi, passaggi, dribbling, contrasti, xG, xA, rating…) | **`post`** |

**Forma normale d'uso**: aggregare le colonne `post` delle partite **precedenti**
di quel giocatore (media mobile, forma recente) e usarle come feature `pre` della
partita successiva. **Mai** le colonne `post` della partita in corso.

⚠️ Il `riepilogo_stagionale` è un aggregato di **fine stagione**: è utilizzabile
**solo ritardato** (stagione precedente), mai per la stagione che descrive.

---

## 6 · Limiti, dichiarati

1. **Una lega e una stagione**: Serie A 2025-26. Non c'è nulla per le altre 4
   leghe né per le 8 stagioni precedenti. Non regge un walk-forward multi-stagione.
2. **Potenza**: 379 partite, contro le **~574** che la Fase 98 misura servire per
   l'80% di potenza sull'1X2 contro il mercato. Un risultato **positivo** sarebbe
   informativo; un risultato **nullo** sarà meno conclusivo di quanto sembri, e va
   detto **prima** del test, non dopo.
3. **Il riepilogo non è una seconda misura**: è la somma del partita-per-partita.
   Non usarlo come controllo incrociato di sé stesso.
4. **`Rating` è un modello proprietario** di diretta.it, non una misura. È un
   giudizio di terzi con una ricetta non pubblica: trattarlo come tale, mai come
   un'osservazione. (Stesso principio già applicato all'xG di FotMob, che è un
   modello **diverso** da quello di Understat e non va mescolato.)
5. **La domanda a monte ha già una risposta parziale, e non incoraggiante**: il
   plus-minus (`docs/CACCIA_EVENT_DATA.md` §6) misura che sapere **chi** gioca
   vale **r = +0,0354** su 10.161 partite. Questi dati permettono di chiedere
   quanto valga sapere **come** ha giocato — domanda diversa, ma con una
   probabilità a priori già abbassata.

---

## 7 · Stato

**Dati inseriti, nessun codice scritto, nessuna feature costruita, nessun
backtest eseguito.** Non sono letti da nulla in `src/` né in `scripts/`.
Il primo passo proposto è in `docs/PIANO_DATABASE_GIOCATORI.md` §12.
