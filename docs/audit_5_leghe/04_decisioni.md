# Report 4 — Le tre decisioni: istruttoria, esito e applicazione

> **Che cos'è questo documento.** Il quarto degli **11 report integrali
> dell'audit a 5 leghe (Fase 100)** — verbale esteso di ciò che `docs/DIARIO.md`
> riassume nella voce «Cinque leghe». Indice: [`00_indice.md`](00_indice.md).
> Documento **storico**.

Le prime due decisioni sono state istruite andando a **cercare i dati**, non
ragionando a tavolino. **Tutte e tre sono state prese e applicate** (§4).

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
| **usare 1-1** ✅ **SCELTA** | è ciò che è successo in campo, è ciò su cui il mercato si regola, e i dati sono completi (xG, tiri, minuti) | diverge dal record ufficiale DFB; va dichiarato |
| tenere 0-2 ed escludere la riga dal fit | non tocca il dato di football-data | butta via una partita vera e completa |
| tenere 0-2 e usarla normalmente | zero lavoro | il modello impara da un punteggio che nessuno ha segnato |

Costo di implementazione: **una riga di eccezione dichiarata**, in nessun caso
un cambio di schema.

---

## Decisione 2 — Valori rosa 2025-26: risalire ai dati Transfermarkt

### Fatto nuovo: Transfermarkt è raggiungibile

Il manuale lo dà tra gli host **bloccati** (fu la ragione del recupero manuale
via browser esterno). Oggi risponde **200**: il recupero è diventato
**scriptabile** (`scripts/recupero_squad_value_tm.py`).

### I 16 valori mancanti: recuperati

`data/squad_value_2526_transfermarkt.csv` — 5 celle Bundesliga
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
le leghe testate). Le due misure sono fortemente correlate (0.97-0.99) ma su
**scale diverse**, e la differenza di scala varia per lega. → *questa lettura è
stata poi affinata: vedi §4, dove si mostra che in una stagione con dati
completi le due definizioni coincidono.*

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
| **riempire con i valori TM** ✅ **SCELTA** | 16 celle diventano un numero reale e pubblico, verificabile; copertura al 100%; la colonna 2025-26 mescola due misure, con il rapporto dichiarato per lega |
| NaN dichiarato | nessuna scala mista, ma un buco al posto di un dato che esiste |
| riempire l'INTERA colonna 2025-26 da TM per tutte e 5 le leghe | l'unica soluzione davvero coerente sul piano della scala, ma cambia dati già consolidati e va rifatta ogni volta |
| stima di modello | errore atteso 17-29%, peggiore del dato TM: non ha senso avendo il TM |

*(La raccomandazione che avevo scritto qui — NaN dichiarato — è stata superata
dalla decisione dell'utente e, come si vede nel §4, anche dai numeri: la verifica
fatta durante l'applicazione mostra che le celle riempite da Transfermarkt sono
semmai più corrette di quelle vicine prese dalla fonte primaria.)*

---

## Decisione 3 — Isolamento del lavoro (presa)

> ⚠️ **Regola decaduta all'integrazione.** La cartella `cantiere/` non esiste
> più: report, script, snapshot e artefatti sono stati spostati nella struttura
> del progetto (la tabella di corrispondenza è in testa a
> [`00_indice.md`](00_indice.md)), e i documenti condivisi sono stati aggiornati.
> Attenzione anche alle **sigle delle regole**: la R4-isolamento di cui si parla
> qui è quella del cantiere; nella numerazione vigente (`CLAUDE.md` §5-bis) la
> R4 è un'altra cosa.

Tutto resta **in `cantiere/`**, senza numerazione di fase e senza toccare i
documenti condivisi (`DIARIO.md`, `README.md`, `PANCHINA.md`, `DATI.md`,
`runs.jsonl`): così non c'è modo di entrare in conflitto con il lavoro in corso
su `main`. Le checklist di integrazione nei report restano **proposte**, da
eseguire solo quando si deciderà di unire i due filoni.


---

## 4 · Esito: cosa è stato deciso e applicato

**Decisione 1 → si usa il risultato del campo (1-1).** Applicata con
`scripts/applica_correzioni.py` sul registro
[`data/correzioni_dichiarate.csv`](../../data/correzioni_dichiarate.csv): tre celle
(`home_goals` 0→1, `away_goals` 2→1, `result` A→D), ognuna con motivo e fonte.
La regola generale è scritta in [`REGOLE.md`](REGOLE.md) **R1**, con l'obbligo
di trattare **ogni caso analogo singolarmente**, mai con un automatismo.

Effetto collaterale positivo, misurato: l'audit sui **gol da fonte indipendente**
(Understat) ora **coincide** per la Bundesliga, che passa a **0 FAIL e 0 WARN**
su 24 controlli. Il confronto con football-data, che continua a riportare lo 0-2
d'ufficio, viene escluso solo per quella riga e segnalato come `INFO`: l'audit
resta severo su tutto il resto.

*Non applicata* (registrata come proposta): i tiri in porta ricavabili da
Understat (4 e 3). La definizione Understat non è identica a quella
football-data della colonna, e mescolare due definizioni dentro una cella è
peggio di un NaN dichiarato. Il dato è nel registro se si vorrà usarlo.

**Decisione 2 → valori rosa da Transfermarkt.** Applicata con
`scripts/applica_squad_value_tm.py`: **16 celle** (5 Bundesliga, 11 Ligue 1),
544 celle-partita riempite, copertura del valore rosa da 94.6%/91.5% a
**100%/100%**. Lo script rifiuta di sovrascrivere un valore esistente: la fonte
primaria resta primaria.

Durante l'applicazione è emersa una verifica che **cambia il caveat** che avevo
scritto prima (§2, punto b). Rifacendo il conto con due date-ancora diverse:

| lega | 2018-19 | 2021-22 | 2025-26 |
|---|--:|--:|--:|
| serie_a | 1.353 | **1.033** | 1.055 |
| premier_league | 1.171 | **1.004** | 1.077 |
| la_liga | 1.302 | **1.003** | 1.118 |
| bundesliga | 1.392 | **1.012** | 1.161 |
| ligue_1 | 1.439 | **1.204** | 1.473 |

1. la pagina Transfermarkt per stagione è **storica**, non odierna: ricalcolando
   il nostro valore con le valutazioni di oggi il rapporto salirebbe a 1.14-6.67,
   non a ~1.00. Nessuna contaminazione dal futuro;
2. in una stagione con dati completi (2021-22) le due definizioni **coincidono**
   (1.003-1.033 su 4 leghe su 5). Quindi il divario del 2025-26 **non nasce da
   Transfermarkt**: nasce dal fatto che la fonte primaria in quella stagione
   sotto-conta, perché le valutazioni non ci sono ancora tutte.

Detto altrimenti: le 16 celle riempite sono, semmai, **più corrette** di quelle
vicine prese dalla fonte primaria. Il caveat resta (la colonna 2025-26 mescola
due misure e va dichiarato), ma il segno del rischio è opposto a quello che
temevo.

**Decisione 3 → isolamento.** Scritta in [`REGOLE.md`](REGOLE.md) R4.

**Verifiche dopo l'applicazione:** audit sulle 5 leghe (Bundesliga 0 FAIL/0 WARN,
Ligue 1 0 FAIL/2 WARN noti), audit avversariale invariato, `pytest` verde
(153 test — ⚠️ **numero STORICO**, quello dichiarato allora; la suite di oggi ne
conta **841**, ri-misurati alla Fase 101-ter).
