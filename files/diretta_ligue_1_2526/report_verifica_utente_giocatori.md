# Report di verifica — Statistiche giocatori Ligue 1 2025/2026

**Dataset verificato:** 9.536 righe giocatore-partita, 310 partite, 18 squadre di Ligue 1, 97 statistiche + rating
**Fonte:** diretta.it (Flashscore)
**Data della verifica:** 10 agosto 2026

Stessa metodologia usata per Serie A, Premier League, LaLiga e Bundesliga: coerenza aritmetica interna, confronto con quello che il sito mostra a schermo, confronto con fonti esterne a diretta.it.

Il perimetro comprende le 306 partite di campionato più le 4 del tabellone play off retrocessione, marcate a parte nella colonna *Fase*: quarti (Red Star–Rodez) e semifinale (St. Etienne–Rodez) sono turni interni alla Ligue 2, la finale andata e ritorno St. Etienne–Nizza mette in palio il posto in Ligue 1.

---

## 1. Coerenza interna — 310 partite, nessun errore

| Controllo | Esito |
|---|---|
| Il risultato registrato per la squadra A è il reciproco di quello di B | 620/620 squadra-partita |
| Gol della squadra = gol dei suoi giocatori + autogol degli avversari | 620/620 |
| Gol subiti registrati sul portiere = gol fatti dall'avversaria | 620/620 |
| Esattamente 11 titolari per squadra per partita | 620/620 |
| Righe duplicate (stessa giornata, squadra, giocatore) | 0 |
| Percentuali fuori da 0–100, valori negativi impossibili, minuti oltre il limite | 0 |
| Gol fatti totali = gol subiti totali (campionato) | 863 = 863 |

**Copertura completa:** tutte e 310 le partite hanno statistiche complete per giocatore.

### I minuti "anomali" — 65 casi, 62 da espulsione e 3 spiegati uno per uno

- **62 squadra-partita sotto i 985 minuti hanno un'espulsione** in quella squadra. Vale la pena notare che nessuna delle due fonti del sito basta da sola: dieci espulsioni sono registrate come secondo giallo nella cronaca ma come cartellino rosso nelle statistiche del giocatore, e in un caso (Tabibou, Nantes–Brest g. 30, rosso dopo review VAR) succede l'opposto. Il conteggio qui sopra usa l'unione delle due.
- **Nantes–Tolosa, giornata 34: 242 minuti per parte.** La partita è stata interrotta al 22' per invasione di campo. La Lega ha poi omologato lo 0-0, quindi il risultato conta in classifica, ma le statistiche coprono i soli 22 minuti giocati. 22 × 11 = 242 per squadra: il dato è coerente con quanto è stato effettivamente giocato.
- **Nantes, giornata 20 (Lorient–Nantes 2-1): 900 minuti.** Ali Youssef risulta titolare con 0 minuti giocati. Che sia sceso in campo è certo — ha rating 6,5 e un cartellino giallo all'88' — ma diretta.it non gli attribuisce minuti. Sono esattamente i 90 minuti che mancano all'appello. È l'unica riga del dataset con 0 minuti e l'ho lasciata come sulla fonte, segnalandola.

---

## 2. Confronto con le tabelle mostrate sul sito — 2.980 confronti, 0 differenze

**Una partita su tutte e sette le categorie del sito** (PSG–Nantes 3-0, giornata 26):

| Categoria | Confronti | Differenze |
|---|---|---|
| Statistiche Top | 352 | 0 |
| Tiri | 320 | 0 |
| Attacco | 224 | 0 |
| Passaggi | 452 | 0 |
| Difesa | 468 | 0 |
| Portiere | 14 | 0 |
| Generali | 224 | 0 |

**Altre tre partite, foglio "Statistiche Top":**

| Partita | Confronti | Differenze |
|---|---|---|
| Rennes–Marsiglia 1-0 (g. 1) | 344 | 0 |
| Nizza–St. Etienne 4-1 (finale play off, ritorno) | 352 | 0 |
| Nantes–Tolosa 0-0 (g. 34, partita interrotta) | 230 | 0 |

Tutti i giocatori abbinati automaticamente, nessuno rimasto fuori dal confronto. Il caso della partita interrotta è utile due volte: il sito mostra 22 righe, esattamente i 22 titolari che il dataset registra, senza subentrati.

---

## 3. Confronto con fonti esterne

### 3.1 Classifica finale ricostruita dai dati — 18/18 esatta, gol compresi

Ricostruendo la classifica dalle 306 partite di campionato e confrontandola con quella pubblicata da deux-zero.com: **partite, vittorie, pareggi, sconfitte, gol fatti, gol subiti e punti coincidono per tutte e 18 le squadre.**

| Pos | Squadra | V-N-P | Gol fatti:subiti | Punti |
|---|---|---|---|---|
| 1 | PSG | 24-4-6 | 74:29 | 76 |
| 2 | Lens | 22-4-8 | 66:35 | 70 |
| 3 | Lilla | 18-7-9 | 52:37 | 61 |
| 4 | Lione | 18-6-10 | 53:40 | 60 |
| 5 | Marsiglia | 18-5-11 | 63:45 | 59 |
| 6 | Rennes | 17-8-9 | 59:50 | 59 |
| 7 | Monaco | 16-6-12 | 60:54 | 54 |
| 8 | Strasburgo | 15-8-11 | 58:47 | 53 |
| 9 | Tolosa | 12-9-13 | 47:46 | 45 |
| 10 | Lorient | 11-12-11 | 48:51 | 45 |
| 11 | Paris FC | 11-11-12 | 47:50 | 44 |
| 12 | Brest | 10-9-15 | 43:55 | 39 |
| 13 | Angers | 9-9-16 | 29:48 | 36 |
| 14 | Le Havre | 7-14-13 | 32:44 | 35 |
| 15 | Auxerre | 8-10-16 | 34:44 | 34 |
| 16 | Nizza | 7-11-16 | 37:60 | 32 |
| 17 | Nantes | 5-9-20 | 29:52 | 24 |
| 18 | Metz | 3-8-23 | 32:76 | 17 |

Totale gol del campionato: 863 in 306 partite (2,82 a partita). PSG campione per la quinta volta di fila, Nantes e Metz retrocessi diretti.

**Un falso allarme risolto.** Una prima fonte (ski-nordique.net) dava Tolosa e Nantes a 33 partite giocate, con 44 e 23 punti invece dei miei 45 e 24. Lo scarto è esattamente il pareggio di Nantes–Tolosa, la partita interrotta al 22'. Wikipedia riporta che la Lega ha omologato lo 0-0 infliggendo al Nantes una gara a porte chiuse, e la tabella di deux-zero.com conferma 34 partite per tutte e 18 le squadre con Tolosa a 45 e Nantes a 24: quella fonte era semplicemente ferma a prima della decisione.

### 3.2 Play off retrocessione — confermato

Dal dataset: St. Etienne–Nizza 0-0 all'andata, Nizza–St. Etienne 4-1 al ritorno. Aggregato 4-1 per il Nizza, che resta in Ligue 1; il St. Etienne resta in Ligue 2. Coincide con Wikipedia.

### 3.3 Classifica marcatori — corrispondenza piena

Confronto con meilleursbuteurs.fr:

| Giocatore | Dataset | Fonte esterna | |
|---|---|---|---|
| Estéban Lepaul | 20 (Rennes) + 1 (Angers) = 21 | 21 | ✓ |
| Joaquín Panichelli (Strasburgo) | 16 | 16 | ✓ |
| Mason Greenwood (Marsiglia) | 16 | 16 | ✓ |
| Folarin Balogun (Monaco) | 13 | 13 | ✓ |
| Lassine Sinayoko (Auxerre) | 12 | 12 | ✓ |

Lepaul ha cambiato squadra a inizio stagione e nel foglio riepilogo compare con due righe, una per club: 1 gol in 2 presenze con l'Angers e 20 in 32 con il Rennes. Sommate danno i 21 della classifica ufficiale.

### 3.4 Portieri

Dal dataset, con almeno 15 presenze: **Lucas Chevalier (PSG)** ha il miglior rapporto con 0,76 gol subiti a partita in 17 presenze e 9 clean sheet, davanti al compagno Safonov (0,93). Sulla stagione piena i migliori sono **Robin Risser (Lens)** e **Berke Özer (Lilla)**, entrambi a 1,06 gol subiti a partita, con Özer a quota 13 clean sheet.

---

## 4. Cosa sapere sui dati

**Due partite senza scheda giocatori sul sito.** Per Lorient–Auxerre e Metz–Brest (giornata 24) diretta.it non pubblica la scheda "Stats giocatore": la pagina non ha quella sezione. Le statistiche individuali però esistono nei dati del sito e le ho estratte complete. Nome e ruolo di quei giocatori li ho ricostruiti dalle altre partite della stagione — tutti risolti, nessuno rimasto senza nome. Sono le uniche due partite le cui statistiche non si possono confrontare a video.

**Foglio Eventi.** Riporta la cronaca pubblicata da diretta.it. In 71 partite su 310 questa cronaca non elenca tutti i gol: è una lacuna della cronaca del sito, non del dataset. Gol, assist e cartellini per giocatore nei fogli principali non vengono da lì ma dalle statistiche individuali, che sono complete — lo conferma il controllo "gol di squadra = gol dei giocatori" riuscito su 620 squadra-partita su 620.

**Foglio Cambi.** 2.751 sostituzioni, ottenute unendo cronaca e formazioni per coprire i buchi dell'una con l'altra.

**Squadre di Ligue 2 nel dataset.** Red Star, Rodez e St. Etienne compaiono solo nelle righe con *Fase* = "Play Off retrocessione". Filtrando su *Fase* = "Campionato" restano le sole 18 squadre di Ligue 1.

---

## Conclusione

Nessun errore di estrazione o di attribuzione. Tutti i controlli aritmetici quadrano su 310 partite su 310, il confronto diretto con le tabelle del sito non produce una sola differenza su 2.980 valori campionati su sette categorie, e la classifica finale ricostruita dai dati coincide con quella ufficiale in ogni singola voce, gol fatti e subiti inclusi. Classifica marcatori e play off trovano entrambi riscontro.

I tre scostamenti apparenti si sono risolti tutti: la partita interrotta di Nantes–Tolosa con lo 0-0 poi omologato, i minuti mancanti di Ali Youssef che sono una lacuna della fonte su una sola riga, e la differenza di una partita in classifica per Tolosa e Nantes che era della fonte esterna, non del dato.

---

### Fonti usate per il confronto esterno

- deux-zero.com — classifica finale Ligue 1 2025-2026
- Wikipedia (2025–26 Ligue 1) — interruzione di Nantes–Tolosa e omologazione dello 0-0, esito del play off
- meilleursbuteurs.fr — classifica marcatori 2025/2026
- ski-nordique.net — classifica finale (fonte risultata ferma a prima dell'omologazione)
- diretta.it — pagine partita, formazioni e statistiche giocatore (fonte primaria)
