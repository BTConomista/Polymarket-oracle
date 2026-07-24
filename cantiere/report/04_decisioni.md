# Report 4 — Le tre decisioni: cosa dicono i dati

Documento di supporto alle tre decisioni aperte. Le prime due sono state
istruite andando a **cercare i dati**, non ragionando a tavolino.

---

## Decisione 1 — Union Berlin-Bochum: come è finita davvero?

### Cosa è successo (fonti: stampa tedesca + dati Understat per-partita)

La partita è stata **giocata per intero**. Non è stata sospesa e non è rimasta
incompiuta:

1. al **92′**, in pieno recupero, il portiere del Bochum Patrick Drewes viene
   colpito alla testa da un accendino lanciato dal settore dell'Union;
2. l'arbitro Martin Petersen interrompe per **oltre 25 minuti**;
3. poi **fa riprendere il gioco** e concede altri ~3 minuti di recupero. Il
   Bochum aveva esaurito i cambi: l'attaccante Philipp Hofmann va in porta, e le
   due squadre si passano la palla fino al fischio finale;
4. la partita **finisce 1-1 sul campo**;
5. il Bochum fa ricorso: il tribunale sportivo del DFB assegna il **2-0** a
   tavolino; l'Union si appella; l'appello viene **respinto** e il massimo
   organo di giustizia sportiva conferma. Risultato ufficiale definitivo: 0-2.

### Abbiamo i dati completi? Sì, e sono coerenti

Dall'endpoint per-partita di Understat (`getMatchData/27866`):

| | Union Berlin | Bochum |
|---|--:|--:|
| giocatori a referto | 16 | 15 |
| minuti dei titolari | 90 | 90 |
| tiri | 22 | 13 |
| ultimo tiro | 90′ | 83′ |
| gol | 1 (Hollerbach 32′) | 1 (Sissoko 22′) |
| xG | 3.03 | 1.25 |

Nessun autogol, nessun dato mancante: è una partita di 90 minuti **completa e
regolarmente documentata**. L'unica cosa che manca è la colonna statistiche di
football-data (tiri, primo tempo: tutte NaN), perché quella fonte registra il
risultato **d'ufficio**, non quello del campo.

### Cosa ne consegue

Il quadro è più semplice di come l'avevo posto: non c'è una partita monca da
escludere. C'è una partita intera, con dati completi, il cui **punteggio
sportivo è 1-1** e il cui **punteggio amministrativo è 0-2**.

Argomento decisivo per un oracolo orientato ai mercati: le scommesse si
regolano sul risultato **al fischio finale**, non su una sentenza successiva.
Un book ha pagato il pareggio. Se il nostro bersaglio è «la probabilità
dell'evento che il mercato regola», l'esito da usare è **1-1 (pareggio)**.

**Opzioni:**

| opzione | pro | contro |
|---|---|---|
| **usare 1-1** (raccomandata) | è ciò che è successo in campo, è ciò su cui il mercato si regola, e i dati sono completi (xG, tiri, minuti) | diverge dal record ufficiale DFB; va dichiarato |
| tenere 0-2 ed escludere la riga dal fit | non tocca il dato di football-data | butta via una partita vera e completa |
| tenere 0-2 e usarla normalmente | zero lavoro | il modello impara da un punteggio che nessuno ha segnato |

Costo di implementazione: **una riga di eccezione dichiarata**, in nessun caso
un cambio di schema.

---

## Decisione 2 — Valori rosa 2025-26: risalire ai dati Transfermarkt

### Fatto nuovo: Transfermarkt è raggiungibile

Il manuale lo dà tra gli host **bloccati** (fu la ragione del recupero manuale
via browser esterno). Oggi risponde **200**: il recupero è diventato
**scriptabile** (`cantiere/scripts/recupero_squad_value_tm.py`).

### I 16 valori mancanti: recuperati

`cantiere/data/squad_value_2526_transfermarkt.csv` — 5 celle Bundesliga
(Augsburg 168.4 M€, FC Koln 156.6, Hamburg 179.4, Hoffenheim 278.8, St Pauli
64.2) e 11 Ligue 1 (Angers 78.8, Auxerre 92.7, Le Havre 75.0, Lens 236.8,
Lorient 127.8, Lyon 300.8, Metz 65.2, Nantes 110.3, Nice 183.8, Paris FC 153.4,
Toulouse 165.3), con fonte, data di recupero e dimensione/età media della rosa.

### Ma prima ho verificato tre cose

**(a) Il recupero manuale già fatto in passato è corretto.** Le 13 celle
riempite a mano a suo tempo (Bologna, Como, Cremonese, Parma, Pisa, Udinese,
Leeds, Sunderland, Celta, Elche, Espanol, Levante, Oviedo) combaciano oggi con
la pagina Transfermarkt: rapporto **1.000** su 11 celle su 13; Cremonese 0.981 e
Udinese 0.986 (Transfermarkt ha ritoccato quei due valori nel frattempo). Il
diario diceva esplicitamente che quei numeri «non erano mai stati verificati in
prima persona»: **ora lo sono**.

**(b) Le due definizioni NON sono la stessa grandezza.** Il nostro
`squad_value` è la somma, sui giocatori che hanno giocato ≥1′ in campionato,
dell'ultima valutazione ≤ 1 settembre; Transfermarkt pubblica il valore
aggregato della rosa registrata. Misurato sui club dove esistono **entrambi** i
valori (stagione 2025-26):

| lega | club confrontati | rapporto TM/nostro (mediana) | scarto assoluto mediano | correlazione |
|---|--:|--:|--:|--:|
| serie_a | 14 | 0.926 | ~7% | — |
| premier_league | 18 | 1.065 | ~7% | — |
| la_liga | 15 | 1.030 | ~3% | — |
| **bundesliga** | 13 | **1.131** | **14.8%** | 0.987 |
| **ligue_1** | 7 | **1.286** | **28.6%** | 0.966 |

E su stagioni vecchie il divario è ancora maggiore (2018-19: 1.35-1.44 in tutte
le leghe testate), quindi **non** è una semplice questione di aggiornamento
recente. Le due misure sono fortemente correlate (0.97-0.99) ma su **scale
diverse**, e la differenza di scala varia per lega.

**(c) La causa vera del buco: il dataset a monte è indietro sulla 2025-26.** La
copertura delle valutazioni (quota di minuti giocati da calciatori valutati)
crolla solo nell'ultima stagione, in **tutte e cinque** le leghe:

| lega | copertura mediana 2024-25 | copertura mediana 2025-26 | celle sotto soglia 2025-26 |
|---|--:|--:|--:|
| serie_a | 0.998 | 0.910 | 6/20 |
| premier_league | 1.000 | 0.979 | 2/20 |
| la_liga | 0.970 | 0.906 | 5/20 |
| bundesliga | 1.000 | 0.929 | 5/18 |
| ligue_1 | 0.984 | **0.837** | **11/18** |

**Ho ri-scaricato il dataset da Kaggle** (altro fatto nuovo: si scarica
direttamente da questa sessione, prima serviva il runner Actions) — ed è
**identico** a quello in repo: 507.815 valutazioni, ultima datata 2026-02-27.
L'ipotesi «basta un re-import» è **falsa**: la via è chiusa finché non si muove
l'upstream.

Nota che il problema non riguarda solo le 16 celle mancanti: anche le celle che
*passano* la soglia nel 2025-26 sono sotto-contate, ed è per questo che il
rapporto TM/nostro è 1.13 in Bundesliga e 1.29 in Ligue 1 (dove la copertura è
peggiore) contro ~1.0 nelle tre leghe con copertura migliore.

### Opzioni

| opzione | conseguenza |
|---|---|
| **riempire con i valori TM** (precedente già seguito) | 16 celle diventano un numero reale e pubblico, verificabile; ma la colonna 2025-26 mescola due scale che nelle leghe nuove differiscono del 13-29% |
| **NaN dichiarato** (raccomandata) | nessuna scala mista; `squad_value` è comunque **bocciata come covariata**, quindi il buco non costa nulla in predizione; il file coi valori TM resta pronto se un giorno servisse |
| riempire l'INTERA colonna 2025-26 da TM per tutte e 5 le leghe | l'unica soluzione davvero coerente sul piano della scala, ma cambia dati già consolidati e va rifatta ogni volta |
| stima di modello | errore atteso 17-29%, peggiore del dato TM: non ha senso avendo il TM |

Raccomandazione: **NaN dichiarato**, con il file `squad_value_2526_transfermarkt.csv`
tenuto nel cantiere come dato di riserva già validato. Se invece la coerenza
«zero NaN» conta più della coerenza di scala, la seconda scelta è riempire con
TM dichiarando il rapporto misurato lega per lega (la colonna del file lo
riporta già).

---

## Decisione 3 — Isolamento del lavoro (presa)

Tutto resta **in `cantiere/`**, senza numerazione di fase e senza toccare i
documenti condivisi (`DIARIO.md`, `README.md`, `PANCHINA.md`, `DATI.md`,
`runs.jsonl`): così non c'è modo di entrare in conflitto con il lavoro in corso
su `main`. Le checklist di integrazione nei report restano **proposte**, da
eseguire solo quando si deciderà di unire i due filoni.
