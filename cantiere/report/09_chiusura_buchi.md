# Report 9 — Chiudere i buchi: cosa si è recuperato davvero, cosa si è stimato

Richiesta: *«risolviamo quanti più buchi nei dati abbiamo (o trovandoli su
internet o da qualche parte, o facendo delle stime quanto più accurate)»*.

Il bilancio in una riga: **il buco più grande è chiuso** — 1.362 partite delle
due leghe nuove hanno ora una chiusura O/U stimata con errore misurato ~0.012, e
per il 2017-19 esiste anche un **dato reale** che prima si riteneva
irrecuperabile. Ma il risultato più onesto è che il dato reale trovato **non
batte la stima**, e va usato per quello che è.

---

## 1 · Il bilancio

| buco | prima | dopo | come |
|---|--:|--:|---|
| chiusura O/U 2017-19, bundesliga + ligue_1 | 2.744 celle vuote | **1.362 partite stimate** (MAE 0.0122 / 0.0110) | stima E3 per-lega |
| chiusura O/U 2017-19, tutte e 5 le leghe | nessun dato reale | **3.652 partite di dato reale** (1xBet) | fonte esterna nuova |
| quote GG/NG 2017-19 | **inesistenti** in tutto il progetto | **3.652 partite** | stessa fonte |
| calendari di coppa | 3.045 righe mancanti | **3.045 righe recuperate** (50 CSV) | Wikipedia + terza fonte |
| 1X2 di chiusura mancante (2 partite) | vuoto | **dato reale proposto** | fonte esterna nuova |
| xG segnaposto | 1 riga sospetta trovata a mano | **cercato con 9 test su 16.110 partite** → 1, confermata | batteria di firme |
| 9 linee O/U di apertura corrotte | stimate (MAE 0.0267) | invariate: nessuna fonte le ha | pista chiusa con prova |

Nessuna correzione è stata applicata agli snapshot: tutto è **proposta**, in
attesa di decisione (§6).

---

## 2 · Il dato reale della chiusura O/U 2017-19: trovato, e ridimensionato

### 2.1 · Come si è trovato

Le due cacce precedenti del progetto avevano cercato lungo un solo asse: *chi
ri-esporta football-data*. Tutti i candidati ereditavano lo stesso buco, perché
la sorgente a monte è la stessa. L'angolo nuovo è stato cercare **un book che
football-data non contiene**: `footiqo.com` pubblica **1xBet**, con mercati che
da noi non esistono (linee 0.5/1.5/3.5/4.5 e GG/NG), su un endpoint che il suo
`robots.txt` permette esplicitamente.

Scaricate 5 leghe × 3 stagioni (throttle 1,8 s): **3.652 partite su 3.652** per
la finestra bersaglio, copertura 100% su tutte e 10 le coppie lega-stagione,
**gol identici ai nostri su tutte le righe**.

### 2.2 · È davvero una chiusura? (la parte che conta)

L'ipotesi da battere non era «è l'apertura rietichettata» — quella cade subito
(coincide con la nostra apertura nello 0,03% delle righe). Era: **«è una
ricostruzione da modello»**, perché la stima E3 del progetto già raggiunge
correlazione 0.75-0.86 col movimento vero partendo dal solo 1X2. Somigliare a
una chiusura, quindi, non è una prova.

Il test decisivo sfrutta un fatto: nel 2017-19 l'1X2 ha **sia** apertura **sia**
chiusura reali (Pinnacle), e footiqo pubblica anche il proprio 1X2. Se è una
fotografia scattata all'ora di chiusura, deve somigliare alla chiusura più che
all'apertura — dentro la finestra bersaglio, non per estrapolazione.

| | valore | verifica indipendente (rifatta dall'orchestratore) |
|---|--:|--:|
| corr(footiqo, **chiusura** vera) | 0.9976 | **0.99773** |
| corr(footiqo, **apertura** vera) | 0.9897 | **0.99091** |
| corr(apertura, chiusura) — la scala | 0.9898 | **0.99101** |
| MAE dalla chiusura / dall'apertura | — | **0.0082 / 0.0170** |
| righe identiche a Pinnacle | 0 | **0** |

Il numero 0.9976 da solo non direbbe niente: è stato **calibrato** misurando
quanto si somigliano due book *veri* allo stesso istante (B365-VC 0.9987,
B365-WH 0.9982, VC-WH 0.9986). footiqo sta a 0.9976 dalla chiusura e a 0.9897
dall'apertura: esattamente la posizione di **un book diverso fotografato
all'ora di chiusura**. Firme corroboranti: margine 1.0269, che non coincide con
nessun book di football-data (B365 1.0476, WH 1.0567, Pinnacle 1.0249); ultima
cifra decimale fortemente non uniforme (30,5% finisce per 0) mentre un modello o
una media darebbero una distribuzione uniforme; scaletta O/U monotona su tutte
le righe; Ligue 1 2019-20 con **279 righe**, il troncamento COVID esatto.

### 2.3 · E però non batte la stima

Qui il risultato si ridimensiona, ed è giusto che sia il paragrafo più
importante.

| confronto | Δ log-loss O/U | CI95 | verdetto |
|---|--:|---|---|
| 1xBet vs **apertura reale** (n=3.643) | −0.00229 | [−0.00423, −0.00035] | **conclusivo**: il dato vero è migliore |
| 1xBet vs **stima E3** (n=2.279) | −0.00021 | [−0.00278, +0.00243] | **indistinguibili** |

E come *proxy della chiusura media multi-book* — che è ciò che gli snapshot
contengono dal 2019-20 — il book grezzo è **peggiore della stima**: sulla
stagione 2019-20, dove esistono entrambi, MAE 0.0156 contro ~0.012 della stima.
Overround 1.035 contro 1.054, bias +0.0088 verso l'Over.

**Conseguenza operativa:** inserire 1xBet nelle colonne di chiusura del 2017-19
sostituirebbe un oggetto (media multi-book) con un altro (un singolo book)
**a metà colonna**, creando una rottura di regime, in cambio di nessun
miglioramento dimostrabile. La raccomandazione è: tenerlo come **dato di
verifica e di ricerca**, non come riempimento della colonna.

### 2.4 · Il ritrovamento collaterale vale più del bersaglio

La stessa fonte porta le **quote di chiusura GG/NG al 100%** (3.652 partite).
Il progetto dichiara il GG/NG «l'unico mercato senza quote nei dati, quindi
l'unico dove non possiamo dimostrare l'efficienza del mercato» — ed è per questo
che è stato indicato come la pista prioritaria. Per tre stagioni, ora si può.

Primo sguardo: il mercato prezza GG in media 0.526 contro una frequenza reale di
0.516; log-loss 0.687 contro 0.693 di baseline costante; overround 1.043. Il
mercato GG/NG **è informativo** — quanto sia battibile è una domanda aperta, e
adesso è una domanda *rispondibile*.

---

## 3 · La stima che chiude il buco: chiusura O/U per Bundesliga e Ligue 1

**1.362 partite stimate** su 1.372 (10 non stimabili: sono le righe la cui
apertura O/U era corrotta e già svuotata — l'input dello stimatore).

Lo stimatore non è stato applicato al buio: è stato **rimesso in discussione**
ora che le leghe sono 5 invece di 3. Tutte le varianti valutate fuori campione,
bootstrap appaiato B=10.000.

| domanda | Δ MAE | CI95 | verdetto |
|---|--:|---|---|
| pooled a **5 leghe** vs pooled a 3 | −0.00026 | [−0.00030, −0.00022] | **conclusivo**: le leghe nuove migliorano lo stimatore anche per le altre |
| intercetta per-lega sopra il pooled | −0.00002 | [−0.00007, +0.00004] | nel rumore |
| **per-lega puro** vs pooled a 5 | **−0.00031** | [−0.00043, −0.00019] | **conclusivo: il per-lega vince** |
| finestra corta (2019-21) vs tutte le stagioni | +0.00011 | [+0.00002, +0.00020] | **conclusivo: più storia è meglio** |
| pooled vs **identità** (chiusura = apertura) | −0.00917 | [−0.00961, −0.00873] | conclusivo |
| pooled vs **media di lega** | −0.05839 | [−0.05997, −0.05684] | conclusivo |

**Il risultato che ribalta una convinzione del progetto.** Lo stimatore ufficiale
è pooled perché, con 3 leghe, il pooled batteva il per-lega. Con 5 leghe e
12.457 partite di fit **il per-lega vince, con CI conclusivo**. Non è una
sorpresa teorica — più dati per lega rendono il fit locale affidabile — ma è una
riga della documentazione da riscrivere, e lo stimatore scelto qui è di
conseguenza **E3 per-lega**.

**Errore atteso, misurato lega per lega** (non ereditato dalle altre):

| lega | MAE atteso | | lega | MAE atteso |
|---|--:|---|---|--:|
| **bundesliga** | **0.0122** | | serie_a | 0.0134 |
| **ligue_1** | **0.0110** | | premier_league | 0.0122 |
| | | | la_liga | 0.0115 |

Le due leghe nuove non sono più difficili delle altre: la Ligue 1 è anzi la
**più facile** del campione.

**Due prove di stress, entrambe superate.** (a) *Fit solo su stagioni
successive*, che è la condizione reale dell'applicazione: MAE 0.0140 contro
0.0134 in Bundesliga, 0.0112 contro 0.0112 in Ligue 1 — il degrado è
trascurabile. (b) *La stima batte l'apertura sulle stagioni bersaglio?* In
Ligue 1 sì con CI conclusivo (−0.0072); in Bundesliga **no, è nel rumore**
(+0.0012). Va detto: in Bundesliga la stima non è dimostrabilmente meglio del
prezzo di apertura da cui parte.

**Limiti dichiarati, riga per riga nel CSV:** i coefficienti sono fittati su
stagioni *successive* a quelle stimate (unico dato possibile: va bene per un
benchmark storico, non per una predizione); nel 2017-19 l'input O/U è Betbrain e
il movimento 1X2 è Pinnacle, mentre il fit usa le medie — semantiche diverse.

→ `cantiere/data/stime/ou_close_2017_19_nuove_leghe.csv` (1.362 righe,
probabilità, mai quote).

---

## 4 · I calendari di coppa: 3.045 righe recuperate

Il buco che **non appare come NaN**: dove openfootball non copre una
competizione, `midweek_europe` dice 0 e sembra un'informazione.

Censimento contro Wikipedia (362 pagine, parser dei template), riga per riga su
(squadra, data). Il buco era più grande dell'ipotesi:

| lega | righe recuperate | righe snapshot toccate | `midweek_europe` prima → dopo |
|---|--:|--:|---|
| serie_a | 499 | 220 (6,4%) | 8,6% → 12,0% |
| premier_league | 526 | 216 (6,3%) | 13,6% → 17,3% |
| la_liga | 677 | 362 (10,6%) | 10,2% → 16,9% |
| bundesliga | 326 | 159 (5,8%) | 12,1% → 15,3% |
| **ligue_1** | **1.017** | **391 (12,6%)** | **5,0% → 12,8%** |
| **totale** | **3.045** | | |

Il riposo cambia in media di **4,5 giorni** sulle celle toccate (max 11).

**Controlli superati:** 0 nomi squadra non agganciati (nessun alias inventato),
0 doppie partite lo stesso giorno dopo il merge, 0 date fuori finestra.
**Verifica su terza fonte indipendente** (openligadb, né openfootball né
Wikipedia) sulla DFB-Pokal in 3 stagioni: **0 righe non confermate su 114**.
Trovati anche 8 disaccordi di data in cui openfootball sbaglia di un giorno
(Wikipedia e openligadb concordi) → proposte di correzione.

**Onestà sul valore:** la congestione è già stata misurata come **rumore** nel
progetto. Il valore qui è la **correttezza del dato**, non il guadagno
predittivo — ma un `midweek_europe` sbagliato nel 6-13% delle righe rendeva
qualunque test su quella covariata inconcludente per costruzione.

---

## 5 · Il resto, in breve

**Celle-quota singole.** I casi sparsi sono **14, non 5**. Due (1X2 di chiusura:
Bayern-Hannover e Alaves-Sociedad) hanno ora un **dato reale** da una fonte
esterna identificata empiricamente come chiusura media-di-mercato (MAE 0.0060
dalla chiusura vera contro 0.0142 dall'apertura, CI conclusivo). Due piste
chiuse con prova: il formato alternativo `all-euro-data.xlsx` di football-data è
**la stessa esportazione in un altro contenitore** (417 celle confrontate, 0
differenze), e nel 2017-19 l'unica colonna di chiusura è `PSC*`, che è proprio
quella vuota.

**Un guasto di lettura, non un dato mancante.** Bayern-Hoffenheim 24/08/2018 non
era vuota alla fonte: i numeri ci sono con le etichette `Mx`/`Av` **scambiate**,
ed è la nostra pipeline ad averli scartati.

**Quattro righe corrotte mai intercettate — in produzione.** In
`data/la_liga_matches.csv` ci sono 4 righe con lo stesso difetto delle 8 già
svuotate qui (overround dell'apertura O/U fino a 1.2825), ancora dentro lo
snapshot: il guard esistente scatta solo per overround < 1, non per overround
troppo alto. È la segnalazione più scomoda del lotto e riguarda le leghe
storiche, non quelle nuove.

**xG segnaposto: cercati sul serio.** Nove firme indipendenti (xG intero uguale
ai gol, cifre povere, forecast degenere, ppda nulla, deep zero, xPts intero,
rigore finto, history mancante, xG zero con tiri) applicate a **16.110 partite**.
Esito: **una sola riga** positiva (Holstein Kiel-Bochum, già corretta), che
accende **7 firme su 9** — mentre gli altri candidati ne accendono una sola e
sono legittimi. Prova di potenza con **500 segnaposto piantati artificialmente**:
la batteria li riscopre **tutti**. Limite dichiarato onestamente: riscopre i
segnaposto *totali*, non le degradazioni parziali (con xG residuo al 90% ne
riscopre lo 0,2%).

**Un difetto nuovo di football-data.** Riconciliando i tiri con Understat emerge
che i conteggi di football-data **non sono confrontabili fra stagioni**: in
Serie A la somma dei tiri passa da 5.359 (2017-18) a 4.269 (2018-19) e torna a
5.326 (2021-22), con tutte le 380 righe popolate. Non è un buco: è un cambio di
raccolta a monte. Poco rilevante oggi (il blend usa l'xG, non i tiri), ma va
scritto.

---

## 6 · Le proposte, nessuna applicata

| # | cosa | dove | perché serve una decisione |
|---|---|---|---|
| 1 | 1X2 di chiusura per **Bayern-Hannover** e **Alaves-Sociedad** (6 celle) | snapshot | il provider è diverso dal resto della colonna (discrepanza attesa 0.0060) |
| 2 | 8 correzioni di **data** nei calendari di club | `club_fixtures_bundesliga.csv` | openfootball sbaglia di un giorno, due fonti concordi |
| 3 | integrare le **3.045 righe di coppa** | `club_fixtures_*.csv` (5 leghe) | Wikipedia non è fonte primaria: verificata su terza fonte solo per la DFB-Pokal |
| 4 | guard sull'**overround alto** + le **4 righe La Liga** | `src/`, `data/` | tocca la produzione (tranche 2) |
| 5 | usare o no il **dato 1xBet** | — | non migliora la stima e romperebbe il regime della colonna: la raccomandazione è **no** |
| 6 | pubblicare la **stima O/U delle 2 leghe nuove** | `data/estimates/` | tranche 2 |
| 7 | passare lo stimatore ufficiale da **pooled a per-lega** | `scripts/build_estimates.py` | CI conclusivo, ma cambia un numero pubblicato |

---

## 7 · Cosa NON si è chiuso, e perché

- **le 9 linee O/U di apertura corrotte** restano stimate (MAE 0.0267): nessuna
  fonte esterna espone l'O/U per-partita del 2017-19 (BetExplorer ri-verificato
  oggi su una lega-stagione nuova: stesso ritiro; OddsPortal vietato dal
  `robots.txt`);
- **l'xG di Holstein Kiel-Bochum** resta NaN: la fonte non ha mai acquisito la
  partita, e un xG dedotto dai tiri sarebbe un numero inventato con la faccia di
  una misura;
- **la chiusura O/U 2017-19 come media multi-book** non esiste da nessuna parte:
  quello che esiste è un singolo book, ed è meno utile della stima.
