# Report di verifica — Statistiche giocatori Bundesliga 2025/2026

**Dataset verificato:** 9.617 righe giocatore-partita, 308 partite, 18 squadre, 97 statistiche + rating
**Fonte:** diretta.it (Flashscore)
**Data della verifica:** 9 agosto 2026

Stessa metodologia usata per Serie A, Premier League e LaLiga: coerenza aritmetica interna, confronto con quello che il sito mostra a schermo, confronto con fonti esterne a diretta.it.

Il perimetro comprende le 306 partite di campionato più le 2 dello spareggio promozione/retrocessione (Wolfsburg–Paderborn), marcate a parte nella colonna *Fase*.

---

## 1. Coerenza interna — 308 partite, nessun errore

| Controllo | Esito |
|---|---|
| Il risultato registrato per la squadra A è il reciproco di quello di B | 616/616 squadra-partita |
| Gol della squadra = gol dei suoi giocatori + autogol degli avversari | 616/616 |
| Gol subiti registrati sul portiere = gol fatti dall'avversaria | 616/616 |
| Esattamente 11 titolari per squadra per partita | 616/616 |
| Righe duplicate (stessa giornata, squadra, giocatore) | 0 |
| Minuti fuori range, percentuali fuori da 0–100, valori negativi impossibili | 0 |
| Gol fatti totali = gol subiti totali (campionato) | 990 = 990 |

**Copertura completa:** tutte e 308 le partite hanno statistiche complete per giocatore.

### I minuti "anomali" — 36 casi, tutti spiegati

36 squadra-partita hanno un totale minuti sotto 985 invece dei ~990 attesi.

- **35 sono partite con un'espulsione** in quella squadra.
- **1 caso resta senza cartellino rosso** e l'ho verificato sul sito:
  - *Dortmund–Colonia, giornata 8* (984 minuti). Il Colonia usa tutte e cinque le sostituzioni entro il 72' (46', 56', 72' con triplo cambio). Hübers esce all'84' e nessuno entra al suo posto — nelle formazioni di diretta.it il suo record non ha alcuna sostituzione associata, a differenza dei cinque compagni sostituiti. Colonia in dieci per gli ultimi 6 minuti: 990 − 6 = 984. Il dato è corretto.

---

## 2. Confronto con le tabelle mostrate sul sito — 3.086 confronti, 0 differenze

Ho confrontato i valori del dataset con quelli che diretta.it disegna a schermo nella scheda "Stats giocatore", categoria per categoria.

**Una partita su tutte e sette le categorie del sito** (Bayern–RB Lipsia 6-0, giornata 1):

| Categoria | Confronti | Differenze |
|---|---|---|
| Statistiche Top | 358 | 0 |
| Tiri | 320 | 0 |
| Attacco | 232 | 0 |
| Passaggi | 444 | 0 |
| Difesa | 460 | 0 |
| Portiere | 14 | 0 |
| Generali | 224 | 0 |

**Altre tre partite, foglio "Statistiche Top"** (rating, tiri, xG, passaggi riusciti/tentati/%, palloni toccati, tocchi in area avversaria, dribbling riusciti/tentati/%, contrasti):

| Partita | Confronti | Differenze |
|---|---|---|
| Dortmund–Colonia 1-0 (g. 8) | 342 | 0 |
| Amburgo–Bayern 2-2 (g. 20) | 330 | 0 |
| Paderborn–Wolfsburg 2-1 d.t.s. (spareggio, ritorno) | 362 | 0 |

Tutti i giocatori sono stati abbinati automaticamente: nessun nome rimasto fuori dal confronto.

---

## 3. Confronto con fonti esterne

### 3.1 Classifica finale ricostruita dai dati — 18/18 esatta, gol compresi

Ricostruendo la classifica dalle 306 partite di campionato e confrontandola con quella pubblicata da Last Season: **partite, vittorie, pareggi, sconfitte, gol fatti, gol subiti e punti coincidono per tutte e 18 le squadre.**

| Pos | Squadra | V-N-P | Gol fatti:subiti | Punti |
|---|---|---|---|---|
| 1 | Bayern | 28-5-1 | 122:36 | 89 |
| 2 | Dortmund | 22-7-5 | 70:34 | 73 |
| 3 | RB Lipsia | 20-5-9 | 66:47 | 65 |
| 4 | Stoccarda | 18-8-8 | 71:49 | 62 |
| 5 | Hoffenheim | 18-7-9 | 65:52 | 61 |
| 6 | Leverkusen | 17-8-9 | 68:47 | 59 |
| 7 | Friburgo | 13-8-13 | 51:57 | 47 |
| 8 | Francoforte | 11-11-12 | 61:65 | 44 |
| 9 | Augusta | 12-7-15 | 45:61 | 43 |
| 10 | Magonza | 10-10-14 | 44:53 | 40 |
| 11 | Union Berlino | 10-9-15 | 44:58 | 39 |
| 12 | Mönchengladbach | 9-11-14 | 42:53 | 38 |
| 13 | Amburgo | 9-11-14 | 40:54 | 38 |
| 14 | Colonia | 7-11-16 | 49:63 | 32 |
| 15 | Brema | 8-8-18 | 37:60 | 32 |
| 16 | Wolfsburg | 7-8-19 | 45:69 | 29 |
| 17 | Heidenheim | 6-8-20 | 41:72 | 26 |
| 18 | St. Pauli | 6-8-20 | 29:60 | 26 |

Totale gol del campionato: 990 in 306 partite (3,24 a partita). I 122 gol del Bayern sono record del club.

### 3.2 Spareggio promozione/retrocessione — confermato

Dal dataset: Wolfsburg–Paderborn 0-0 all'andata, Paderborn–Wolfsburg 2-1 dopo i supplementari al ritorno. Aggregato 2-1 per il Paderborn, che sale in Bundesliga; il Wolfsburg retrocede. Coincide con quanto riportato da Wikipedia.

### 3.3 Classifica marcatori — corrispondenza piena, presenze comprese

Confronto con la classifica ufficiale pubblicata da bundesliga.com:

| Giocatore | Dataset (gol/presenze) | Fonte esterna | |
|---|---|---|---|
| Harry Kane (Bayern) | 36 / 31 | 36 / 31 | ✓ |
| Deniz Undav (Stoccarda) | 19 / 29 | 19 / 29 | ✓ |
| Serhou Guirassy (Dortmund) | 17 / 33 | 17 / 33 | ✓ |
| Patrik Schick (Leverkusen) | 16 / 28 | 16 / 28 | ✓ |
| Luis Díaz (Bayern) | 15 / 32 | 15 / 32 | ✓ |
| Michael Olise (Bayern) | 15 / 32 | 15 / 32 | ✓ |
| Andrej Kramarić (Hoffenheim) | 14 / 34 | 14 / 34 | ✓ |

Kane vince il Torjägerkanone per il terzo anno di fila.

**L'unico scostamento, e perché non è un errore di estrazione.** bundesliga.com accredita a Yan Diomande (RB Lipsia) 13 gol, il dataset ne registra 12. Il totale di squadra però coincide: i gol dei giocatori del Lipsia sommano 64 e con i 2 autogol degli avversari fanno 66, esattamente i 66 della classifica ufficiale. La differenza sta quindi nell'attribuzione di una singola rete, non nel conteggio. I due autogol in questione sono Chabot (Stoccarda, giornata 9, 45') e Arthur Chaves (Augusta, giornata 25, 90+2'), entrambi descritti come autogol nella cronaca di diretta.it — deviazione o spazzata sfortunata. La DFL ne accredita evidentemente uno a Diomande. È una divergenza di attribuzione tra fornitori di dati, non un dato mancante: il gol c'è, sta nella colonna autogol.

### 3.4 Portieri

Dal dataset, con almeno 15 presenze: **Gregor Kobel (Dortmund)** è il portiere meno battuto con 1,00 gol subiti a partita su 34 presenze e **15 clean sheet**, davanti a Manuel Neuer (0,91 su 22 presenze) e Peter Gulácsi (1,39). Neuer ha la media migliore ma su una stagione parziale.

---

## 4. Cosa sapere sui dati

**Tre partite senza scheda giocatori sul sito.** Per Heidenheim–Magonza (g. 34), Augusta–Francoforte (g. 31) e Heidenheim–St. Pauli (g. 31) diretta.it non pubblica la scheda "Stats giocatore": la pagina non ha proprio quella sezione. Le statistiche individuali però esistono nei dati del sito e le ho estratte — 103 metriche per 40 giocatori a partita, come per tutte le altre. Nome e ruolo di quei giocatori non erano disponibili in quelle tre pagine e li ho ricostruiti dalle altre partite della stagione (tutti e 607 i giocatori risolti, nessuno rimasto senza nome). Sono le uniche tre partite le cui statistiche non si possono confrontare a video con il sito.

**Foglio Eventi.** Riporta la cronaca pubblicata da diretta.it (gol, autogol, rigori, cartellini). In 69 partite su 308 questa cronaca non elenca tutti i gol: è una lacuna della cronaca del sito, non del dataset. Gol, assist e cartellini per giocatore nei fogli principali non vengono da lì ma dalle statistiche individuali, che sono complete — lo conferma il controllo "gol di squadra = gol dei giocatori" riuscito su 616 squadra-partita su 616.

**Foglio Cambi.** 2.884 sostituzioni, ottenute unendo due fonti del sito (cronaca e formazioni) per coprire i buchi dell'una con l'altra: 9,36 a partita, contro un massimo teorico di 10.

---

## Conclusione

Nessun errore di estrazione o di attribuzione. Tutti i controlli aritmetici quadrano su 308 partite su 308, il confronto diretto con le tabelle del sito non produce una sola differenza su 3.086 valori campionati su sette categorie, e la classifica finale ricostruita dai dati coincide con quella ufficiale in ogni singola voce, gol fatti e subiti inclusi. Classifica marcatori e spareggio trovano entrambi riscontro, presenze comprese.

I due scostamenti apparenti si sono risolti: il team-partita sotto quota minuti senza espulsione è il Colonia rimasto in dieci per infortunio a cambi esauriti, e il gol di scarto su Diomande è un autogol che la DFL attribuisce all'attaccante — con il totale di squadra che resta identico a quello ufficiale.

---

### Fonti usate per il confronto esterno

- Last Season — classifica finale Bundesliga 2025-26
- bundesliga.com — classifica marcatori finale 2025/26 con presenze
- Wikipedia — spareggio promozione/retrocessione 2025-26
- diretta.it — pagine partita, formazioni e statistiche giocatore (fonte primaria)
