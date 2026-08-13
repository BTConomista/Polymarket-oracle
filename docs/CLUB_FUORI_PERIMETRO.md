# I club che non sono nei nostri campionati — come funziona il dataset, e come ci si comporta

*13/08/2026. Nasce da una domanda dell'utente: «capiterà sempre più spesso di
avere nel dataset squadre che non sono nei nostri campionati... come ci
comportiamo in quei casi? magari cerchiamo di capire bene il funzionamento del
dataset per capire come comportarci».*

Ogni numero di questo file esce da **`scripts/_run_anatomia_club.py`** (analisi
descrittiva: nessuna riga in `runs.jsonl`, nessun modello toccato).

---

## 1. Il fatto di partenza: il dataset copre **32 prime divisioni** e nient'altro

`files/player_scores/` è la fonte che ci dà club, partite, giocatori e minuti
fuori dai nostri cinque campionati. La sua struttura è più semplice di come
sembra, e capirla scioglie quasi tutta la domanda.

| file | righe | che cos'è |
|---|---|---|
| `club_names.csv` | 3.173 | il **registro** dei nomi: `club_id`, `name`, `domestic_competition_id` |
| `clubs.csv` | 796 | il **contesto**: rosa, età media, stadio, valore, allenatore |
| `games.csv` | 88.958 | i **fatti**: una riga per partita, 65 competizioni, 2005-2025 |
| `appearances.csv` | 1.894.350 | i fatti per giocatore-partita |
| `players.csv` | 50.149 | l'anagrafica dei giocatori |
| `competitions.csv` | 65 | l'anagrafica delle competizioni (31 campionati domestici) |

Il nome c'è per **tutti e 3.173** i club. Il campionato domestico c'è per
**796 (25,1%)**, e sono esattamente gli stessi che stanno in `clubs.csv`.

> ⚠️ **Le coperture si misurano per COLONNA, non per file.** Questa riga è
> costata un annuncio ritirato il 12/08: «il file giusto è `club_names`» è vero
> per il *nome* e falso per la *lega*. Sono due colonne dello stesso file con
> due coperture diverse.

---

## 2. La cosa da capire: **non manca il club, manca il suo contesto**

È la sorpresa dell'analisi, ed è quella che cambia il modo di ragionare. Divisi
i 3.274 `club_id` che hanno giocato almeno una partita in tre cerchi:

| cerchio | club | partite | formazioni | presenze giocatore | anagrafica giocatore | `clubs.csv` |
|---|---:|---:|---:|---:|---:|---:|
| **A** · nei nostri 5 campionati | 176 | 61.104 | 92,0% | 851.904 | 100% | 176/176 |
| **B** · in uno degli altri 27 coperti | 617 | 92.752 | 91,4% | 1.031.384 | 100% | 617/617 |
| **C** · fuori: nessun campionato | 2.481 | 24.060 | 85,6% | 11.062 | 100% | **0**/2.481 |

Le **partite ci sono**. I **giocatori ci sono**, e la loro anagrafica è piena al
100% in tutti e tre i cerchi. Le **formazioni** sono all'85,6% anche nel cerchio
C, contro il 92% del cerchio A: sei punti di differenza, non un abisso.

Quello che manca al cerchio C è **l'etichetta di campionato** e **la riga di
contesto** (rosa, stadio, valore). Nient'altro.

---

## 3. Il cerchio C non è una cosa sola: sono **quattro famiglie**, con quattro risposte

Trattare i 2.481 come un unico problema è l'errore da evitare. Misurati:

| famiglia | club | che cosa sono | che cosa si fa |
|---|---:|---|---|
| **nazionali** | 109 | Italia, Brasile, Spagna… stanno nello **stesso spazio dei `club_id`** | niente: non hanno un campionato perché non sono club |
| **orfani** | 104 | `club_id` che giocano ma non sono nel registro, e `games.csv` ha `home_club_name` **vuoto** su quelle righe | niente da recuperare: si dichiarano |
| **paese deducibile** | 1.997 | giocano una **coppa nazionale** (FA Cup, Copa del Rey, DFB-Pokal…) | il paese si deduce dal dato, **0 ambiguità su 1.997** |
| **solo coppe UEFA** | 375 | non giocano nessuna competizione che ne riveli il paese | è l'unica famiglia dove serve informazione da fuori |

Il terzo blocco è quello che rende il problema più piccolo di quanto sembri:
**chi gioca la FA Cup è inglese.** La deduzione è deterministica, viene dal
dato e non da una ricerca esterna, e su 1.997 club non produce **nemmeno una**
ambiguità. I paesi che ne escono: Spagna 345, Danimarca 261, Grecia 230,
Olanda 223, Inghilterra 198, Russia 198, Germania 150, Italia 133, Scozia 130,
Ucraina 111.

E dice anche **chi sono**: sono le divisioni inferiori dei paesi che già
copriamo. Il dataset li vede solo quando incontrano una squadra di prima
divisione in coppa.

---

## 4. Il limite vero, e perché non è un difetto da riparare

**Misurato: i club del cerchio C giocano 0 partite di campionato domestico.**
Zero, non «poche». Le loro 24.060 partite sono coppe nazionali, qualificazioni
UEFA, fasi finali UEFA, tornei per nazionali.

Questo chiude la questione «come recuperiamo la loro lega»: non è recuperabile
per deduzione perché **il dataset non li vede mai giocare in casa loro**. E
soprattutto rende la domanda meno interessante di quanto sembri — un club di cui
non abbiamo nemmeno una partita di campionato non è modellabile con niente di
quello che abbiamo, qualunque etichetta gli si appiccichi.

Il limite non è un buco da tappare: è **il perimetro della fonte**.

---

## 5. L'etichetta di lega è **statica**, e non si contraddice mai (R8)

`domestic_competition_id` non è «la lega di oggi» né «la lega di quella
stagione». Misurato:

- club con partite in **più di un** campionato domestico: **0 su 793**;
- club la cui etichetta **contraddice** le sue partite: **0**;
- 39 club hanno giocato in Serie A: **tutti e 39** sono etichettati `IT1`,
  compresi quelli il cui `last_season` è 2013.

È «l'unico dei 32 campionati coperti in cui quel club è mai apparso». **Non
mente mai**, e si può usare senza paura per dire «questo è un club di Serie A».
Ma **non risponde** alla domanda «in che serie era nel 2019»: per quella serve
`games.csv`, cioè le partite.

---

## 6. La regola operativa: si guarda **il ruolo**, non il club

Il criterio non è «questo club è dentro o fuori». È: **che cosa devo farci?**

| ruolo | che cosa serve | dove si può | che cosa si fa |
|---|---|---|---|
| **avversario** — incontra una nostra squadra in coppa | identità + risultato | ovunque, A/B/C | **niente.** Il dato c'è già |
| **soggetto** — voglio prezzare le sue partite | storia di campionato | solo A e B | nel cerchio C **è impossibile**, e non per un difetto: 0 partite di campionato |
| **candidato all'allargamento** — «apriamo l'Olanda?» | quale campionato è | solo B, dove l'etichetta c'è già | si legge, non si costruisce |

Da cui le tre righe che valgono come procedura:

1. **Non si va a caccia della lega di un club del cerchio C.** Non c'è, non si
   deduce, e servirebbe per una cosa (modellarlo) che comunque non si può fare.
2. **Il paese sì, e solo dove serve**: per i 1.997 si deduce dalla coppa
   nazionale, dentro il dato. Per i 375 l'unica fonte in casa è la colonna
   `Paese (SofaScore)` delle raccolte UEFA — piena al 100%, recupera **101** dei
   158 club delle coppe 2024-25/2025-26, e ne lascia 57.
   ⚠️ **con la trappola del campo neutro**: 7 club su 200 giocano «in casa» in
   più di un paese (lo Shakhtar Donetsk **mai** in Ucraina).
3. **Un club nuovo entra dal nome, e il nome è il vero punto debole** — §7.

---

## 7. Il rischio che cresce davvero non è il club mancante: è **l'aggancio sbagliato**

Un club assente si vede. Un club agganciato **al club sbagliato** no — ed è la
regola R6 in azione: non un buco, un finto pieno.

Due casi, entrambi reali e trovati nell'audit dell'identità:

- **`Espanol` → `Jove Español San Vicente`** (25462, Tercera División, UNA
  partita in `games.csv`), invece di RCD Espanyol (714). Il motivo è il nome
  canonico interno del progetto, che scrive «Espanol» senza la y mentre il
  registro scrive «Espanyol» con la y: `{espanol}` non pescava il club giusto,
  ne pescava un altro, e usciva etichettato **univoco**. **266 partite di La
  Liga.** ✅ Riparato il 13/08/2026 (alias in `club_matching.ALIAS`); misura di
  controllo indipendente: la ricomposizione snapshot↔`games.csv` passa da
  15.839 a **16.105 su 16.111 (99,96%)**.
- **`Red Star FC` → Red Star Belgrade** (159). La voce di divieto esisteva già
  per la forma corta «Red Star», ma il confronto è **letterale**: bastava
  scrivere il nome un filo più lungo per aggirarla. ✅ Riparato il 13/08/2026
  aggiungendo le forme lunghe.

> ⚠️ **La riparazione ovvia era sbagliata, ed è stata misurata prima di
> committarla.** Confrontare il divieto sugli *insiemi di token* invece che
> sulla stringa sembra la soluzione pulita — e su 3.339 nomi rompe **due
> agganci giusti**: `Athletic Bilbao` (621) e `FC Lusitanos` (28958) sparirebbero,
> perché `normalizza` perde l'ordine («Bilbao Athletic» = «Athletic Bilbao») e
> butta le sigle («Lusitanos» = «FC Lusitanos»). Le due classi di divieto —
> squadre riserve e omonimi stranieri — hanno bisogni **opposti**, e nessuno
> schema unico le serve entrambe. La regola resta **letterale e per-voce**: un
> test in `tests/test_coppe_aggancio.py` la tiene ferma.

**Quindi, quando entra una fonte con club stranieri nuovi**, in quest'ordine:

1. si passa dall'`Agganciatore` di `src/data/club_matching.py`, che su un
   ambiguo **lascia vuoto** invece di indovinare (è la regola aurea del join);
2. si guarda la lista degli **ambigui e degli assenti** — sono innocui, si vedono;
3. si cercano gli **univoci sospetti**: un `club_id` con pochissime partite in
   `games.csv`, o con partite in un paese che non c'entra. È lì che si nasconde
   il finto pieno, e nessun conteggio di celle piene lo trova;
4. l'alias o il divieto si scrive **per-voce**, con la verifica indipendente
   accanto (le partite che quel `club_id` gioca davvero), mai per somiglianza
   di stringa.

---

## 8. Due anomalie dichiarate (R4: si scrivono anche quando non sono errori)

- **5 `competition_id` di `games.csv` non esistono in `competitions.csv`**:
  `CGB` (coppa inglese di lega minore, 246 partite), `COL1` (Colombia, 200),
  `KLUB` (Mondiale per club, 156), `POCP` (coppa di lega portoghese, 602),
  `UKRS` (Supercoppa ucraina, 10). `COL1` è anche l'unico codice usato come
  etichetta di lega senza avere una riga in `competitions.csv`: i campionati
  domestici *usati* sono 32, quelli *anagrafati* 31.
- **6 partite su 16.111 non ricompongono** contro `games.csv` dopo la
  riparazione dell'Espanyol: sono slittamenti di ±1 giorno con squadre e
  punteggio identici (Ath Madrid-Elche 29 vs 30/12/2022; Granada-Ath Bilbao 11
  vs 10/12/2023; quattro partite di Ligue 1 2019-20). Restano inoltre i **2**
  scarti di punteggio già noti e già spiegati dalla regola R1 (Verona-Roma
  19/09/2020, Union Berlin-Bochum 14/12/2024).

---

## 9. Che cosa cambierebbe con il ranking UEFA

L'utente sta procurando il ranking UEFA per club e per federazione. Quando
arriva, **non risolve** il problema di §4 (la lega dei club del cerchio C
continua a non esistere) ma risolve meglio quello di §6.2: dà il paese **e** una
misura di forza per i club che oggi non hanno né contesto né valore rosa.
⚠️ Con la trappola R8 già segnalata: il coefficiente **di oggi** non è quello
**del momento** della partita, e usare il primo per prevedere la seconda è
look-ahead.

Per questo `data/nazionalita_club.csv` **non è stato costruito**: nascerebbe da
una fonte peggiore di quella che sta arrivando.
