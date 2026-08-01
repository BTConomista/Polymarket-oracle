> ⚠️ **DOCUMENTO DELL'UTENTE, RIPORTATO INTEGRALMENTE E NON MODIFICATO.**
> Report di verifica di chi ha raccolto i dati (31/07/2026). La sessione lo ha
> **ricontrollato rieseguendo i controlli sul file**: riscontro in `README.md`
> §4, **interamente confermato** — a differenza del gemello sulla Serie A, che
> aveva un rilievo su §3.1.

# Report di verifica — Statistiche giocatori Premier League 2025/2026

**Dataset verificato:** 11.492 righe giocatore-partita, 380 partite, 20 squadre, 97 statistiche + rating
**Fonte:** diretta.it (Flashscore)
**Data della verifica:** 31 luglio 2026

Stessa metodologia usata per la Serie A: coerenza aritmetica interna, confronto con quello che il sito mostra a schermo, confronto con fonti esterne a diretta.it.

---

## 1. Coerenza interna — 380 partite, nessun errore

| Controllo | Esito |
|---|---|
| Il risultato registrato per la squadra A è il reciproco di quello di B | 380/380 |
| Gol della squadra = gol dei suoi giocatori + autogol degli avversari | 760/760 squadra-partita |
| Gol subiti registrati sui giocatori = gol fatti dall'avversaria | 760/760 |
| Esattamente 11 titolari per squadra per partita | 760/760 |
| Righe duplicate (stessa giornata, squadra, giocatore) | 0 |
| Minuti fuori dal range 1–120, percentuali fuori da 0–100, valori negativi impossibili | 0 |
| Gol fatti totali = gol subiti totali | 1.045 = 1.045 |

**Copertura completa:** a differenza della Serie A, dove mancavano le statistiche di Lecce–Como, qui tutte e 380 le partite hanno dati completi per giocatore.

### I minuti "anomali"

36 squadra-partita hanno un totale minuti sotto 985 invece dei ~990 attesi. **Tutte e 36** corrispondono a partite in cui quella squadra ha subito un'espulsione: nessun caso di minuti bassi senza cartellino rosso.

---

## 2. Confronto con le tabelle mostrate sul sito — 1.939 confronti, 0 differenze

**Quattro partite, foglio "Statistiche Top" (8 metriche × tutti i giocatori):**

| Partita | Giocatori | Confronti | Differenze |
|---|---|---|---|
| Brighton–Tottenham 2-2 (g. 5) | 31 | 248 | 0 |
| Manchester Utd–West Ham 1-1 (g. 14) | 30 | 240 | 0 |
| Bournemouth–Aston Villa 1-1 (g. 25) | 31 | 248 | 0 |
| Sunderland–Nottingham 0-5 (g. 34) | 29 | 232 | 0 |

**Una partita su tutte e cinque le categorie del sito** (Sunderland–Nottingham, 40 metriche distinte):

| Categoria | Confronti | Differenze |
|---|---|---|
| Tiri | 290 | 0 |
| Attacco | 174 | 0 |
| Passaggi | 232 | 0 |
| Difesa | 261 | 0 |
| Portiere | 14 | 0 |

Due giocatori (Diouf del West Ham, Konsa dell'Aston Villa) non venivano abbinati automaticamente perché il sito li abbrevia in "Diouf M." e "Konsa E." mentre il dataset conserva il nome completo "Diouf El Hadji Malick" e "Konsa Ngoyo Ezri". Li ho confrontati a mano: tutti e 16 i valori coincidono. È un limite del mio script di confronto, non del dato.

---

## 3. Confronto con fonti esterne

### 3.1 Classifica finale ricostruita dai dati — 20/20 esatta

Ricostruendo punti e V-N-P dalle 380 partite del dataset e confrontando con la classifica finale pubblicata: **ordine, partite giocate, vittorie, pareggi, sconfitte e punti coincidono per tutte e 20 le squadre.**

| Pos | Squadra | V-N-P | Punti | Gol fatti:subiti |
|---|---|---|---|---|
| 1 | Arsenal | 26-7-5 | 85 | 71:27 |
| 2 | Manchester City | 23-9-6 | 78 | 77:35 |
| 3 | Manchester Utd | 20-11-7 | 71 | 69:50 |
| 4 | Aston Villa | 19-8-11 | 65 | 56:49 |
| 5 | Liverpool | 17-9-12 | 60 | 63:53 |
| 6 | Bournemouth | 13-18-7 | 57 | 58:54 |
| 7 | Sunderland | 14-12-12 | 54 | 42:48 |
| 8 | Brighton | 14-11-13 | 53 | 52:46 |
| 9 | Brentford | 14-11-13 | 53 | 55:52 |
| 10 | Chelsea | 14-10-14 | 52 | 58:52 |
| 11 | Fulham | 15-7-16 | 52 | 47:51 |
| 12 | Newcastle | 14-7-17 | 49 | 53:55 |
| 13 | Everton | 13-10-15 | 49 | 47:50 |
| 14 | Leeds | 11-14-13 | 47 | 49:56 |
| 15 | Crystal Palace | 11-12-15 | 45 | 41:51 |
| 16 | Nottingham | 11-11-16 | 44 | 48:51 |
| 17 | Tottenham | 10-11-17 | 41 | 48:57 |
| 18 | West Ham | 10-9-19 | 39 | 46:65 |
| 19 | Burnley | 4-10-24 | 22 | 38:75 |
| 20 | Wolves | 3-11-24 | 20 | 27:68 |

Totale gol del campionato: 1.045 in 380 partite (2,75 a partita).

### 3.2 Classifica marcatori — corrispondenza piena

| Giocatore | Dataset | Fonte esterna | |
|---|---|---|---|
| Erling Haaland (Man City) | 27 | 27 | ✓ (confermato dal sito ufficiale della Premier League) |
| Igor Thiago (Brentford) | 22 | 22 | ✓ |
| Antoine Semenyo | 10 (Bournemouth) + 7 (Man City) = **17** | 17 | ✓ |
| Ollie Watkins (Aston Villa) | 16 | 16 | ✓ |
| João Pedro (Chelsea) | 15 | 15 | ✓ |
| Morgan Gibbs-White (Nottingham) | 15 | 15 | ✓ |

Semenyo è passato dal Bournemouth al Manchester City a gennaio: nel foglio riepilogo compare con una riga per club, e la somma dà esattamente i 17 gol della classifica ufficiale. Vale lo stesso per gli altri 13 giocatori che hanno cambiato squadra in stagione.

### 3.3 Classifica assist — 8 su 8 identici

| Giocatore | Dataset | Fonte esterna |
|---|---|---|
| Bruno Fernandes (Man Utd) | 21 | 21 ✓ |
| Rayan Cherki (Man City) | 12 | 12 ✓ |
| Jarrod Bowen (West Ham) | 11 | 11 ✓ |
| Erling Haaland (Man City) | 8 | 8 ✓ |
| Szoboszlai, Garner, Salah, Wilson | 7 ciascuno | 7 ciascuno ✓ |

Corrispondenza migliore rispetto alla Serie A, dove sugli assist si trovavano differenze di ±1 tra provider.

### 3.4 Il caso Golden Glove — apparente scostamento, in realtà una conferma

Il dataset attribuisce a **David Raya 19 clean sheet**, mentre l'annuncio ufficiale della Premier League parla di 18. Ho ricostruito le giornate: l'Arsenal ha tenuto la porta inviolata alle giornate 1, 2, 4, 7, 8, 9, 10, 14, 17, 21, 22, 24, 25, 29, 30, 34, 35, 36, 37. Sono **18 fino alla 36ª giornata** — il momento in cui il premio è stato annunciato come matematicamente assegnato — e la diciannovesima è arrivata alla 37ª contro il Burnley. Raya ha giocato 90 minuti pieni in tutte e 19.

Il 18 della fonte è quindi una fotografia a due giornate dalla fine, non un dato finale: il numero del dataset è quello corretto a fine stagione, e la ricostruzione giornata per giornata lo dimostra.

---

## Conclusione

Nessun errore di estrazione o di attribuzione. Tutti i controlli aritmetici quadrano su 380 partite su 380, il confronto diretto con le tabelle del sito non produce una sola differenza su 1.939 valori campionati, la classifica finale ricostruita dai dati coincide esattamente con quella ufficiale e marcatori, assist e Golden Glove trovano riscontro nelle fonti esterne.

**Copertura completa: non ci sono partite mancanti.** L'unico scostamento apparente (i clean sheet di Raya) si è risolto in una conferma della correttezza del dato.

---

### Fonti usate per il confronto esterno

- Premier League (sito ufficiale) — Golden Boot e Golden Glove 2025/26
- Sports Illustrated — top scorers, most assists, Golden Glove 2025/26
- StatsMagazine — classifica finale Premier League 2025-26
- diretta.it — pagine partita e statistiche giocatore (fonte primaria)
