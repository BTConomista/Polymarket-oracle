> ⚠️ **DOCUMENTO DELL'UTENTE, RIPORTATO INTEGRALMENTE E NON MODIFICATO.**
> È il report di verifica prodotto da chi ha raccolto i dati (31/07/2026).
> La sessione lo ha **ricontrollato numero per numero** contro il file: il
> riscontro sta in `README.md` §8, ed è **quasi interamente confermato** — con
> **un rilievo su §3.1** e una svista di intestazione. Leggi §8 del README
> prima di citare i numeri di questo file.

# Report di verifica — Statistiche giocatori Serie A 2025/2026

**Dataset verificato:** 11.894 righe giocatore-partita, 380 partite, 20 squadre, 97 statistiche + rating
**Fonte:** diretta.it (Flashscore)
**Data della verifica:** 31 luglio 2026

Il controllo è stato fatto su tre livelli indipendenti: coerenza aritmetica interna, confronto con quello che il sito mostra a schermo, confronto con fonti esterne a diretta.it.

---

## 1. Coerenza interna — 379 partite, nessun errore

Su ogni partita sono state verificate cinque identità che devono valere per costruzione. Se anche una sola riga fosse stata attribuita alla squadra sbagliata, o un punteggio letto male, queste quadrature si romperebbero.

| Controllo | Esito |
|---|---|
| Il risultato registrato per la squadra A è il reciproco di quello di B | 379/379 |
| Gol della squadra = gol dei suoi giocatori + autogol degli avversari | 758/758 squadra-partita |
| Gol subiti registrati sui giocatori = gol fatti dall'avversaria | 758/758 |
| Esattamente 11 titolari per squadra per partita | 379/379 |
| Righe duplicate (stessa giornata, squadra, giocatore) | 0 |
| Minuti fuori dal range 1–120, percentuali fuori da 0–100, valori negativi impossibili | 0 |

### Il caso dei minuti "anomali"

43 squadra-partita hanno un totale minuti sotto 985 invece dei ~990 attesi (11 giocatori × 90'). Non è un errore: **tutte e 43** corrispondono a partite in cui quella squadra ha subito un'espulsione. Nessun caso di minuti bassi senza cartellino rosso. Le 18 espulsioni che non riducono i minuti sono rossi dati dopo il 90'.

---

## 2. Confronto con le tabelle mostrate sul sito — 2.062 confronti, 0 differenze

Il dataset è stato costruito leggendo i feed dati di diretta.it, non le tabelle HTML. Per escludere errori di interpretazione dei campi, ho aperto alcune partite nel browser e confrontato valore per valore quello che il sito mostra a schermo con quello che ho estratto.

**Quattro partite, foglio "Statistiche Top" (8 metriche × tutti i giocatori):**

| Partita | Giocatori | Confronti | Differenze |
|---|---|---|---|
| Sassuolo–Lazio 1-0 (g. 3) | 32 | 256 | 0 |
| Verona–Parma 1-2 (g. 12) | 30 | 240 | 0 |
| Roma–Milan 1-1 (g. 22) | 30 | 240 | 0 |
| Udinese–Como 0-0 (g. 31) | 32 | 256 | 0 |

**Una partita su tutte e cinque le categorie del sito** (Udinese–Como, 40 metriche distinte):

| Categoria | Confronti | Differenze |
|---|---|---|
| Tiri | 320 | 0 |
| Attacco | 192 | 0 |
| Passaggi | 256 | 0 |
| Difesa | 288 | 0 |
| Portiere | 14 | 0 |

Nessun giocatore rimasto non abbinato in nessuna delle verifiche.

---

## 3. Confronto con fonti esterne

### 3.1 Classifica finale ricostruita dai dati — 20/20 esatta

Ricostruendo punti, vittorie, pareggi, sconfitte dalle 380 partite del dataset e confrontando con la classifica finale pubblicata da Football Italia: **ordine, partite giocate, V-N-P e punti coincidono per tutte e 20 le squadre.**

| Pos | Squadra | V-N-P | Punti | Gol fatti:subiti |
|---|---|---|---|---|
| 1 | Inter | 27-6-5 | 87 | 89:35 |
| 2 | Napoli | 23-7-8 | 76 | 58:36 |
| 3 | Roma | 23-4-11 | 73 | 59:31 |
| 4 | Como | 20-11-7 | 71 | 65:29 |
| 5 | Milan | 20-10-8 | 70 | 53:35 |
| 6 | Juventus | 19-12-7 | 69 | 61:34 |
| 7 | Atalanta | 15-14-9 | 59 | 51:36 |
| 8 | Bologna | 16-8-14 | 56 | 49:46 |
| 9 | Lazio | 14-12-12 | 54 | 41:40 |
| 10 | Udinese | 14-8-16 | 50 | 45:48 |
| 11 | Sassuolo | 14-7-17 | 49 | 46:50 |
| 12 | Parma | 11-12-15 | 45 | 28:46 |
| 13 | Torino | 12-9-17 | 45 | 44:63 |
| 14 | Cagliari | 11-10-17 | 43 | 40:53 |
| 15 | Fiorentina | 9-15-14 | 42 | 41:50 |
| 16 | Genoa | 10-11-17 | 41 | 41:51 |
| 17 | Lecce | 10-8-20 | 38 | 28:50 |
| 18 | Cremonese | 8-10-20 | 34 | 32:57 |
| 19 | Verona | 3-12-23 | 21 | 25:61 |
| 20 | Pisa | 2-12-24 | 18 | 26:71 |

Totale gol del campionato: 922 in 380 partite (2,43 a partita). Gol fatti e gol subiti quadrano a 922 su entrambi i lati.

### 3.2 Classifica marcatori — 16 su 18 identici, 2 scostamenti spiegati

Confronto con la classifica marcatori finale di Sky Sport:

| Giocatore | Dataset | Sky Sport | |
|---|---|---|---|
| Lautaro Martínez (Inter) | 17 | 17 | ✓ |
| Malen (Roma) | 14 | 14 | ✓ |
| Douvikas (Como) | 13 | 14 | **−1** |
| Thuram (Inter) | 13 | 13 | ✓ |
| Højlund (Napoli) | 12 | 12 | ✓ |
| Nico Paz (Como) | 11 | 12 | **−1** |
| Simeone (Torino) | 11 | 11 | ✓ |
| Bonazzoli, McTominay, Scamacca, Davis, Orsolini, Krstović, Yıldız | 10 | 10 | ✓ |
| Çalhanoğlu, Pinamonti, Leão, Pellegrino | 9 | 9 | ✓ |

**I due scostamenti sono entrambi giocatori del Como e sono entrambi spiegati dall'unica lacuna nota del dataset.** Lecce–Como 0-3 della giornata 17 è la sola partita per cui diretta.it non pubblica statistiche per giocatore. Il riepilogo testuale della partita sul sito riporta i marcatori: **Paz 20', Ramon 66', Douvikas 75'**. Sono esattamente i gol mancanti: Paz e Douvikas −1 ciascuno, più Ramon che nel dataset risulta a 1 gol invece di 2. Nessun altro giocatore della Serie A si discosta.

Nota: una seconda fonte (Calciomercato.com) riportava numeri diversi per Malen (13) e Højlund (10). Il dataset concorda con Sky Sport, che è coerente anche con la somma partita per partita.

### 3.3 Classifica assist

Il dato più caratteristico della stagione — i **17 assist di Federico Dimarco**, record storico della Serie A — è confermato identico dalle fonti esterne. Su altri giocatori si trovano differenze di ±1 (Barella 8 nel dataset contro 9, Jesús Rodríguez 9 contro 8, Dybala 6 contro 7). Queste non sono errori di estrazione: l'assist non ha una definizione unica e i vari provider lo attribuiscono diversamente in caso di deviazioni, respinte e tocchi intermedi. Il dataset riporta l'attribuzione di diretta.it, coerente al suo interno.

---

## Conclusione

Su oltre 1,2 milioni di valori estratti non è emerso alcun errore di estrazione o di attribuzione. Tutti i controlli aritmetici quadrano, il confronto diretto con le tabelle del sito non produce una sola differenza su 2.062 valori campionati, e la classifica finale ricostruita dai dati coincide esattamente con quella ufficiale.

**L'unico limite del dataset è noto e circoscritto:** Lecce–Como 0-3 del 27.12.2025 non ha statistiche per giocatore alla fonte. Como e Lecce hanno quindi 37 partite invece di 38, e tre marcatori del Como (Paz, Ramon, Douvikas) hanno un gol in meno del totale reale. È documentato nel foglio "Note e copertura" dei file Excel, dove sono riportati anche i 29 rating che diretta.it pubblica per quella partita.

---

### Fonti usate per il confronto esterno

- Sky Sport — classifica marcatori Serie A 2025/2026
- Football Italia — Serie A 2025-26 final standings
- SpazioCalcio — classifica assist Serie A 2025/2026
- Calciomercato.com — classifica marcatori finale 2025/2026
- diretta.it — pagine partita e riepiloghi (fonte primaria)
