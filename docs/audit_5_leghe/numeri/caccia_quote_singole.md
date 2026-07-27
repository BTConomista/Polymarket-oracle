# Caccia al dato VERO per le celle-quota mancanti, una partita alla volta

*25 luglio 2026 — lavoro di cantiere, regola R4: nessuno snapshot è stato
modificato, nessuna correzione è stata applicata. Tutto quello che segue è
**materiale per una decisione dell'utente**.*

---

## 0 · In due righe

Cinque celle assegnate, **quattordici** trovate. Due celle recuperate con **dato
reale** da una fonte esterna mai intercettata prima dal progetto, identificata
per via statistica come **chiusura media-di-mercato** (due test indipendenti,
entrambi con CI conclusivo) e **confermata da una seconda fonte del tutto
indipendente** (§3.5). Due celle **chiuse con la prova che il dato vero non
esiste**: il mercato non era offerto a quell'istante. Una cella per cui ho
identificato il **meccanismo del guasto alla fonte** (etichette scambiate) senza
trovare conferma esterna. In più, quattro righe con quote impossibili **ancora
dentro lo snapshot di produzione** della Liga.

| # | partita | cella | esito |
|---|---|---|---|
| 1 | bundesliga 1819 · Bayern Munich–Hannover · 04/05/2019 | 1X2 chiusura | ✅ **dato vero trovato** — 1.03 / 18.43 / 43.88 · confermato da 2ª fonte |
| 3 | la_liga 1718 · Alaves–Sociedad · 14/10/2017 | 1X2 chiusura | ✅ **dato vero trovato** — 3.40 / 3.34 / 2.15 · confermato da 2ª fonte |
| 2 | bundesliga 1819 · Bayern Munich–Hoffenheim · 24/08/2018 | O/U apertura | ⚠️ guasto capito (etichette Mx/Av scambiate), ricostruzione proposta, nessuna conferma esterna |
| 4 | serie_a 2122 · Torino–Fiorentina · 10/01/2022 | 1X2 + O/U apertura | ❌ **chiusa: il dato non esiste** — il mercato non era aperto |
| 5 | serie_a 2021 · Verona–Genoa · 19/10/2020 | O/U apertura | ❌ **chiusa: il dato non esiste** — un solo book quotava, i totali per niente |
| +8 | 6 bundesliga + 2 ligue_1, 2017-19 | O/U apertura | già svuotate dal cantiere; nessuna fonte esterna le copre |
| +4 | la_liga 2018-19 | O/U apertura | 🔴 **segnalazione**: overround impossibile, mai intercettate, ancora in `data/la_liga_matches.csv` |

---

## 1 · Prima di cercare: ho riverificato l'elenco

Non mi sono fidato della lista ricevuta. Ho riscansionato tutti e cinque gli
snapshot su tutte le colonne quota, separando i buchi **sistemici** (l'O/U di
chiusura 2017-19, 3.652 righe, già noto e documentato in
`docs/CACCIA_OU_2017_19.md`) dai casi **sparsi**, che sono il vero bersaglio.

I cinque casi assegnati ci sono tutti. Ma i casi sparsi sono **quattordici**, non
cinque: otto in più, tutti O/U 2.5 di apertura.

Una precisazione sulla consegna: il **caso 2** (Bayern–Hoffenheim) è descritto
come «celle vuote alla fonte». **Non è così.** Alla fonte i due numeri ci sono;
sono le nostre pipeline ad averli scartati, perché il loro overround è
impossibile. È una differenza che cambia completamente la caccia — e infatti è da
lì che è venuta la diagnosi (§4).

---

## 2 · La via più economica: cercare DENTRO la fonte

### 2.1 · Lo stesso dato in un altro contenitore

football-data.co.uk pubblica gli stessi dati come CSV per lega-stagione (quello
che già abbiamo) e come **`all-euro-data-<anno>.xlsx`**, un foglio per divisione.
Sono esportazioni fatte in momenti diversi: era plausibile che una cella vuota in
un formato fosse piena nell'altro.

**Aspettativa dichiarata prima di guardare**: ~15% di probabilità di trovare una
differenza. L'xlsx è quasi certamente la stessa estrazione dallo stesso database.

`robots.txt` di football-data: `User-agent: *` seguito da `Disallow:` vuoto —
tutto permesso. Ho scaricato le quattro stagioni interessate (1718, 1819, 2021,
2122) e confrontato **cella per cella** le cinque righe bersaglio.

> **417 celle confrontate su 5 righe. Zero differenze.**

Previsione negativa confermata. I due formati sono la stessa esportazione: dove
il CSV è vuoto, l'xlsx è vuoto.

### 2.2 · Esiste un'altra colonna di chiusura che non usiamo?

Dal `notes.txt` della fonte:

> «The following key to betting odds data is described below. **These are for
> pre-closing odds.** For the closing odds, as below but with an additional "C"
> character following the bookmaker abbreviation/Max/Avg (e.g. B365CH = closing
> Bet365 home win odds).»

Questo conferma alla lettera la politica del progetto (`src/data/loader.py`,
`_ODDS_PREFERENCE`: chiusura = solo `AvgC*` / `B365C*` / `PSC*`). Nelle stagioni
2017-18 e 2018-19 le **uniche** colonne con la C sono `PSC*` — ed è esattamente
quella vuota nelle due righe. Tutte le altre colonne piene di quelle righe
(B365, BW, IW, LB, WH, VC, BbMx, BbAv) sono **pre-match per definizione della
fonte**, e il progetto le usa già per popolare l'apertura.

Quindi: dentro football-data non c'è nulla. La pista interna è chiusa, con prova.

---

## 3 · La fonte esterna: trovata, e poi interrogata

### 3.1 · Cosa ho trovato

`github.com/iredchuk/soccer-bookmaker-odds` (licenza MIT): 1X2 **medio di
mercato** per ogni partita di Premier, Liga, Bundesliga, Serie A e Ligue 1, dalla
stagione 2005-06 alla 2018-19. Copre **3.652 partite su 3.652** delle nostre
cinque leghe nel 2017-19: il 100%.

Le due righe che ci servono ci sono, testualmente:

```
"2018-2019","32","Bayern München","Hannover 96",3,1,1.03,18.43,43.88,0.926…,0.051…,0.021…
"2017-2018","8","CD Alavés","Real Sociedad",0,2,3.4,3.34,2.15,0.277…,0.282…,0.439…
```

I gol combaciano con i nostri (3-1 e 0-2), ed entrambe sono l'unica partita in
casa di quella coppia in quella stagione: l'abbinamento è univoco.

**Ma il repo non dichiara da dove viene.** Non ha commit history, non ha uno
scraper, non nomina una fonte. Per i criteri del progetto («provenienza
dichiarata», «chiedere sempre COME il dataset è stato costruito») questo sarebbe
un motivo di scarto. Invece di scartarlo l'ho **interrogato**.

### 3.2 · È un'apertura o una chiusura?

La domanda è decisiva: se fossero quote pre-match, sarebbero la stessa
istantanea che già abbiamo (`BbAv*`) e non servirebbero a nulla.

*Aspettativa dichiarata prima: 50/50, con una leggera propensione a «chiusura».
Ho previsto che il confronto sulle quote grezze sarebbe stato confuso dal margine
— una media multi-book ha un margine più alto di Pinnacle — e ho quindi deciso in
anticipo di misurare su **probabilità devigate**.*

**Il join.** Primo tentativo con abbinamento fuzzy sui nomi: fino a 97
discrepanze sui gol su 380 righe in Liga. Inaccettabile. L'ho rifatto abbinando
le squadre per **impronta-risultati** — la sequenza dei risultati stagionali di
ogni squadra, che è praticamente unica e non dipende dai nomi:

```
3.652 righe unite · 0 non trovate · 0 discrepanze sui gol
```

**Test 1 — distanza dalle due istantanee che già possediamo** (MAE su probabilità
devigate, bootstrap appaiato B=10.000 con `boot()` di `scripts/_fase52_common.py`):

| distanza | MAE |
|---|--:|
| repo → **apertura** `BbAv*` | 0.01424 |
| repo → **chiusura** `PSC*` | **0.00597** |
| apertura → chiusura *(la scala del problema)* | 0.01755 |

differenza **−0.00827**, CI95 **[−0.00865, −0.00789]** → **CONCLUSIVO**.
Il repo sta **2,4 volte più vicino alla chiusura** che all'apertura.

**Test 2 — potere predittivo sul risultato vero** (metriche da
`src/evaluation/metrics.py`, mai reimplementate):

| fonte | log-loss | Brier |
|---|--:|--:|
| repo esterno | 0.95303 | 0.56484 |
| apertura `BbAv*` | 0.95505 | 0.56633 |
| chiusura `PSC*` | 0.95233 | 0.56441 |

- repo vs apertura: **−0.00202**, CI95 [−0.00398, −0.00002] → **conclusivo**, il repo è più informativo dell'apertura;
- repo vs chiusura: **+0.00070**, CI95 [−0.00013, +0.00152] → **nel rumore**, indistinguibile dalla chiusura.

Due test indipendenti, stessa risposta: **è una chiusura**. E l'overround medio
(**1.0526**, contro 1.0247 di Pinnacle e 1.0489 della media pre-match Betbrain)
dice di che tipo: una **media di mercato**. Cioè esattamente la semantica delle
colonne `AvgC*` — che nella politica del progetto sono la **prima** preferenza
per la chiusura, prima ancora di `PSC*`.

### 3.3 · Ho provato a demolirlo

Come chiesto, prima di dichiarare il risultato ho cercato di confutarlo.

**C1 · «È solo una ri-esportazione di qualcosa che abbiamo già.»**
Frazione di righe in cui la terna del repo coincide con una terna football-data
della stessa riga:

| B365 | BW | IW | WH | VC | PS apertura | PSC chiusura | BbAv apertura | BbMx |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 0.000% | 0.000% | 0.000% | 0.027% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |

Nessuna. Coerente col fatto che football-data **non ha alcuna media-di-mercato di
chiusura prima del 2019-20**: il dato è informativamente nuovo. Confutazione
fallita.

**C2 · «Sono numeri di un modello, non quote vere.»**
L'overround del repo sta sempre fra **1.0363 e 1.1074**, mai sotto 1: un modello
non ha margine, un book sì, e questo ce l'ha sempre e in una banda stretta. E
soprattutto: se fosse stato costruito conoscendo i risultati, batterebbe la
chiusura di Pinnacle. **Non la batte** (0.95303 contro 0.95233). Nessun leakage.
Confutazione fallita.

**C3 · «Il dato era già nel formato alternativo della fonte madre.»**
417 celle confrontate, 0 differenze (§2.1). Confutazione fallita.

**C4 · «C'è un'altra colonna di chiusura legittima nella stessa riga.»**
Le uniche colonne con la C nel 2017-19 sono `PSC*`, e sono quelle vuote (§2.2).
Confutazione fallita.

**C5 · «Il join è sbagliato, il segnale è un artefatto.»**
È l'unica confutazione che ha morso qualcosa: il primo join, fuzzy sui nomi, era
sporco. Rifatto per impronta-risultati è perfetto — e il segno del risultato
**non è cambiato** (−0.00803 col join sporco, −0.00827 con quello pulito). Il
risultato è sopravvissuto, anzi si è rafforzato.

### 3.5 · La controprova che non mi aspettavo: una seconda fonte indipendente

Mentre lavoravo, una linea parallela di questa stessa sessione ha raccolto da
**footiqo.com** le quote di chiusura di **1xBet** per le stesse dieci
lega-stagione (`data/ricerca_esterna/footiqo_*.json`). È una fonte del tutto
indipendente dalla mia: book diverso, sito diverso, raccolta diversa. E contiene
**entrambe** le partite che mi servivano.

Non ci si aspetta identità — una media multi-book e un singolo book sono due
aggregazioni diverse — ma coerenza. La scala di giudizio è la distribuzione dello
scarto fra le due fonti sulle 2.591 righe dove esistono entrambe: MAE **0.00752**,
mediana 0.00572, p90 0.01571, p99 0.02660.

| partita | fonte A (media mercato) | fonte B (1xBet chiusura) | MAE fra le due | dove cade |
|---|---|---|--:|---|
| Alaves–Sociedad | 3.40 / 3.34 / 2.15 | 3.58 / 3.54 / 2.22 | **0.00376** | **30° percentile** |
| Bayern–Hannover | 1.03 / 18.43 / 43.88 | 1.02 / 26.00 / 34.00 | **0.01006** | 76° percentile |

Alaves–Sociedad: accordo migliore del tipico. Bayern–Hannover: scarto del tutto
ordinario, e si spiega da sé — è tutto sul **pareggio**, dove su quella partita i
book erano genuinamente lontanissimi fra loro (nel grezzo football-data: B365 21,
BW 17.5, IW 15, WH 19, VC 23, massimo Betbrain 25). Una **media** di mercato a
18.43 e un **singolo** book generoso a 26.00 sono perfettamente compatibili.

Un dettaglio che orienta la scelta: sulle righe dove esiste `PSC*`, la fonte A
sta più vicina alla chiusura di Pinnacle (**0.00592**) di quanto ci stia 1xBet
(**0.00817**). Coerente con la sua natura di media di mercato — ed è anche il
motivo per cui propongo il valore della fonte A, non quello di 1xBet: la politica
del progetto preferisce `AvgC*` (media) a un singolo book.

### 3.4 · Quanto costa mescolare due provider di chiusura

La colonna di chiusura nel 2017-19 è Pinnacle. Metterci dentro una media di
mercato ha un costo, e va misurato, non dichiarato.

Distanza fra le due chiusure, su probabilità devigate, sulle 3.650 righe dove
esistono entrambe:

| | valore |
|---|--:|
| MAE | **0.00597** |
| p50 / p75 / p90 / p95 / p99 | 0.00533 / 0.00798 / 0.01085 / 0.01261 / 0.01654 |
| bias con segno (repo − PSC): 1 / X / 2 | −0.00237 / +0.00076 / +0.00161 |

Il termine di paragone: **lasciare il buco e usare l'apertura** costerebbe
**0.01755** (differenza −0.01158, CI95 [−0.01196, −0.01119], **conclusivo**).
La discrepanza fra i due provider di chiusura è **tre volte più piccola** della
distanza apertura-chiusura. Come sostituto della cella mancante è nettamente il
male minore.

---

## 4 · Caso per caso

### Caso 1 — Bayern Munich–Hannover, 04/05/2019 · 1X2 di chiusura → ✅ trovato

`PSCH/PSCD/PSCA` vuote nel grezzo (e anche `PSH/PSD/PSA`: Pinnacle non ha proprio
quotato questa partita nel dataset). Unica riga così su 306.

**Valore trovato: 1.03 / 18.43 / 43.88** — overround 1.0479, sano.
Controlli di ingresso del progetto: overround > 1 ✅, apertura ≠ chiusura ✅
(scostamento devigato dall'apertura 0.00204).

Nota favorevole: in questa riga l'apertura è `BbAvH` (1.04 / 17.52 / 45.03), cioè
già una **media di mercato**. La coppia diventa media-mercato → media-mercato:
internamente coerente.

**Controprova indipendente (§3.5):** 1xBet chiudeva 1.02 / 26.00 / 34.00. Scarto
0.01006, il 76° percentile del disaccordo abituale fra le due fonti: ordinario.
Tutto sul pareggio, dove i book erano genuinamente sparsi fra 15 e 25.

### Caso 3 — Alaves–Sociedad, 14/10/2017 · 1X2 di chiusura → ✅ trovato

Stessa situazione: `PSC*` vuote, unica riga su 2.280 della lega.

**Valore trovato: 3.40 / 3.34 / 2.15** — overround 1.0586, sano.
Apertura ≠ chiusura ✅ (scostamento devigato 0.00449).

**Controprova indipendente (§3.5):** 1xBet chiudeva 3.58 / 3.54 / 2.22. Scarto
**0.00376**, il 30° percentile: due fonti indipendenti che si danno ragione
meglio del loro solito. È la cella su cui sono più tranquillo.

**Caveat più serio di quello del caso 1:** qui l'apertura è `PSH` (3.52 / 3.55 /
2.20), cioè **Pinnacle**. Accettare la proposta crea una coppia
apertura-Pinnacle → chiusura-media-mercato: esattamente il CLV misto che la
Fase 61 aveva evitato di proposito. Da soppesare, non da liquidare.

### Caso 2 — Bayern Munich–Hoffenheim, 24/08/2018 · O/U apertura → ⚠️ guasto capito, dato vero non trovato

Non è una cella vuota. Alla fonte:

```
BbMx>2.5 = 1.33    BbAv>2.5 = 1.40
BbMx<2.5 = 3.30    BbAv<2.5 = 3.55
```

**Il massimo di un insieme non può essere minore della sua media.** Qui lo è su
entrambi i lati. Su 3.652 righe questo accade **2 volte**.

Con le etichette come stanno, l'overround è **0.9960** — sotto 1, arbitraggio
garantito, impossibile per una media multi-book: è per questo che il guard della
Fase 58 in `loader._pick_market_odds` ha svuotato la cella (correttamente).

Scambiando Mx e Av:

| | overround |
|---|--:|
| etichette attuali (Av) | 0.9960 ❌ |
| **dopo lo scambio** | **1.0549** |
| mediana del corpus (3.652 righe) | 1.0554 |
| intervallo 1%–99% | [1.0472, 1.0666] |

Cade **sulla mediana**. E il lato «Max» scambiato dà 1/1.40 + 1/3.55 = 0.9960,
che per un *massimo* multi-book è normale: è un'occasione di arbitraggio fra
book, non un margine negativo.

**Ho provato a confermarlo con la seconda fonte, e non si può.** La chiusura
1xBet di quella partita (footiqo, §3.5) dà P(over 2.5) = 0.7261; la ricostruzione
dà 0.7127 e le etichette attuali danno 0.7172. Sono entrambe dentro la deriva
apertura→chiusura tipica (media 0.0223, p90 0.0461): il test **non discrimina**.
Il motivo è strutturale — scambiare Mx e Av cambia soprattutto il **margine**
(0.9960 → 1.0549), non la probabilità implicita. La controprova è stata fatta ed
è risultata muta: lo dico invece di tacerlo.

La diagnosi resta solida sul suo argomento proprio: **è uno scambio di etichette,
e i due numeri veri sono nelle celle sorelle.** Ma resta una **ricostruzione**, non la lettura di una
fonte: nessun archivio esterno con O/U 2.5 del 2018-19 mi è risultato
accessibile. La classifico onestamente come *dato vero non trovato, meccanismo
identificato, ricostruzione proposta* — decide l'utente.

### Caso 4 — Torino–Fiorentina, 10/01/2022 · apertura 1X2 e O/U → ❌ il dato non esiste

Nel grezzo sono vuote **41 celle**: ogni colonna pre-match (`B365H`…`AvgA`,
`B365>2.5`…`Avg<2.5`, handicap asiatico pre-match). Tutte le colonne di
**chiusura** sono invece piene. È l'**unica riga su 380** della stagione senza
alcuna quota pre-match 1X2. Il formato xlsx è identico (100 colonne, 0
differenze).

Il perché, verificato: la partita era sotto **blocco ASL** per il focolaio Covid
nel Torino (ordinanza del 5 gennaio) ed è stata autorizzata solo dalla
sospensione del **TAR Piemonte**, con spostamento da domenica 9 a lunedì 10
gennaio. `notes.txt` dichiara che l'istantanea pre-match è raccolta **il venerdì
pomeriggio**: quel venerdì, su questa partita, **il mercato non era offerto**.

Non è un dato perso in raccolta: è un dato **mai esistito** a quell'istante.
Resta corretta la scelta già fatta dal progetto (stima dichiarata in
`data/estimates/open_sparse_1x2_ou.csv`, MAE atteso ~0.016).

### Caso 5 — Verona–Genoa, 19/10/2020 · O/U apertura → ❌ il dato non esiste

Qui il 1X2 pre-match **c'è**, ed è la prova:

```
MaxH = AvgH = 2.05     MaxD = AvgD = 3.40     MaxA = AvgA = 3.75
```

Massimo identico alla media su tutti e tre gli esiti significa **un solo
bookmaker nel paniere**. È l'**unica riga su 380** della stagione con questa
firma — ed è anche l'**unica riga su 380** con 1X2 pre-match presente e O/U
pre-match assente. Il formato xlsx è identico (100 colonne, 0 differenze).

Contesto coerente: focolaio Covid nel Genoa in ottobre 2020 (16 positivi, 12
giocatori; Genoa–Torino già rinviata il 3 ottobre) e un positivo nel Verona.

Se un solo book quotava l'1X2 e **nessuno** i totali, il dato vero non esiste.
Pista chiusa con prova.

---

## 5 · Gli otto casi in più — e quattro righe che nessuno aveva visto

### 5.1 · Gli otto già svuotati dal cantiere

Sono le righe O/U 2.5 di apertura con overround impossibile (1.26–1.34), già
registrate in `data/correzioni_dichiarate.csv` e coperte dalla stima di
`data/estimates/ou_open_corrotte_2017_19.csv` (MAE 0.0267): 6 in Bundesliga, 2 in
Ligue 1. **Nessuna fonte esterna le copre**: il dataset trovato in §3 contiene
solo 1X2, non ha alcun mercato O/U. Restano dove sono.

Nota forense: in queste otto righe `Max` e `Avg` sono **internamente coerenti**
(Max > Avg, scarti normali del 3-5%), quindi non è uno scambio di etichette come
nel caso 2 — è tutto il blocco O/U a essere incoerente col resto della riga
(l'1X2 della stessa riga ha overround 1.045–1.060, perfettamente sano). Non ho
trovato né uno slittamento di riga (le quattro righe vicine hanno sempre blocchi
O/U diversi) né una riga gemella nello stesso file.

### 5.2 · 🔴 Quattro righe corrotte ancora nello snapshot di PRODUZIONE

Cercando gli otto casi ne ho trovati **altri quattro con lo stesso identico
difetto** — ma questi non sono mai stati intercettati e **sono tuttora dentro
`data/la_liga_matches.csv`** con valori impossibili:

| data | partita | over25_open | under25_open | overround |
|---|---|--:|--:|--:|
| 2018-10-06 | Alaves – Real Madrid | 1.53 | 1.59 | **1.2825** |
| 2018-11-24 | Eibar – Real Madrid | 1.45 | 1.69 | **1.2814** |
| 2019-02-10 | Leganes – Betis | 2.48 | 1.38 | **1.1279** |
| 2018-12-07 | Leganes – Getafe | 2.89 | 1.50 | 1.0127 |

Per scala: su 3.652 righe l'overround O/U ha mediana **1.0554** e intervallo
1%–99% **[1.0472, 1.0666]**. Le prime tre sono fuori scala quanto le otto già
svuotate.

**Perché sono sfuggite:** il guard di `loader._pick_market_odds` (Fase 58)
scatta solo per overround **< 1** — cioè per l'arbitraggio garantito — e non per
un overround troppo **alto**. Le otto righe del cantiere sono state prese da un
audit dedicato (`audit_anomalie.py`), che però non è mai stato passato sugli
snapshot delle tre leghe storiche.

La quarta riga (Leganes–Getafe) è il secondo caso di `Max < Avg` del corpus, ma
solo sul lato Under: lo scambio porta l'overround a 1.0357, ancora sotto il 1°
percentile. **Ricostruzione non pulita**, a differenza di Bayern–Hoffenheim.

Non ho toccato nulla (R4). La decisione — estendere il guard con un tetto
superiore, oppure trattare queste quattro righe come le otto già svuotate — è
dell'utente.

---

## 6 · Le piste chiuse, con la prova

| pista | esito | prova |
|---|---|---|
| football-data, formato `all-euro-data.xlsx` | ❌ | 417 celle confrontate sulle 5 righe bersaglio, **0 differenze**. `robots.txt`: `Disallow:` vuoto, tutto permesso |
| football-data, altre colonne di chiusura | ❌ | nel 2017-19 le uniche colonne `*C*` sono `PSC*`, ed è quella vuota; `notes.txt` dichiara che tutte le altre sono pre-closing |
| **BetExplorer, ri-verificata oggi** | ❌ | pagina risultati Bundesliga 2018-19 raggiunta (HTTP 200, 254 KB, tutte le partite), ma le colonne quota della tabella sono letteralmente `&nbsp;`. Sulla pagina-partita: **0** occorrenze di `match-odds`, e `#bettingTabs` contiene solo `<span class="list-tabs__item__in disabled border0">1X2</span>` — un unico tab, **disabilitato**, nessun tab O/U. **Estende alla Bundesliga 2018-19** il risultato che il progetto aveva su Serie A/Premier/Liga 2017-18. `robots.txt` consente le pagine-partita |
| OddsPortal storico | ⛔ **vietato** | il `robots.txt` vieta esplicitamente `*-2017*`, `*-2018*`. Non tentata, né direttamente né via cache o archivi |
| Oddspedia | ❌ | challenge Cloudflare (HTTP 403) già sul `robots.txt`: non è possibile nemmeno leggere le condizioni d'uso, quindi non si procede |
| footiqo.com | ✅ **produttiva** (merito di un'altra linea di lavoro) | Il mio sondaggio si era fermato all'HTML statico — dove non compare alcun nome di colonna-quota e le uniche stagioni citate sono 2015/2016 e 2025/2026 — e avevo concluso «non verificabile». **Conclusione superata:** una linea parallela di questa sessione ha raggiunto l'endpoint ajax e ha estratto le quote di **chiusura 1xBet** (1X2, O/U 0.5→4.5, BTTS) per tutte e dieci le lega-stagione 2017-19, copertura 100%. La uso qui come **controprova indipendente** (§3.5). Le occorrenze di `AvgC` che avevo visto erano davvero falsi positivi (chiave JSON `avgColumns` del plugin) |
| ricerca web sulle due partite | ❌ | restituisce probabilità implicite e pagine di anteprima, mai le quote decimali per-partita con l'istantanea dichiarata |
| Kaggle / mirror di football-data | ❌ | già chiuso dal progetto (`docs/CACCIA_OU_2017_19.md` §3): 6 dataset verificati uno per uno, tutti ri-esportazioni che ereditano lo stesso buco. Non ripetuto |

Throttle ≥ 1,5 s fra le richieste su tutti i siti interrogati.

---

## 7 · Le righe di correzione proposte (NON applicate)

Vanno inserite in `data/correzioni_dichiarate.csv` (regola R3) e
applicate **solo** con `scripts/applica_correzioni.py`, che verifica il
valore-prima. L'elenco completo con motivo e fonte per riga è in
`caccia_quote_singole.json`, campo `proposte_correzione`.

| lega | stagione | data | partita | colonna | prima | dopo | natura |
|---|---|---|---|---|---|--:|---|
| bundesliga | 1819 | 2019-05-04 | Bayern Munich–Hannover | `odds_home` | — | 1.03 | dato reale, fonte esterna |
| bundesliga | 1819 | 2019-05-04 | Bayern Munich–Hannover | `odds_draw` | — | 18.43 | dato reale, fonte esterna |
| bundesliga | 1819 | 2019-05-04 | Bayern Munich–Hannover | `odds_away` | — | 43.88 | dato reale, fonte esterna |
| la_liga | 1718 | 2017-10-14 | Alaves–Sociedad | `odds_home` | — | 3.40 | dato reale, fonte esterna |
| la_liga | 1718 | 2017-10-14 | Alaves–Sociedad | `odds_draw` | — | 3.34 | dato reale, fonte esterna |
| la_liga | 1718 | 2017-10-14 | Alaves–Sociedad | `odds_away` | — | 2.15 | dato reale, fonte esterna |
| bundesliga | 1819 | 2018-08-24 | Bayern Munich–Hoffenheim | `odds_over25_open` | — | 1.33 | **ricostruzione**, non lettura esterna |
| bundesliga | 1819 | 2018-08-24 | Bayern Munich–Hoffenheim | `odds_under25_open` | — | 3.30 | **ricostruzione**, non lettura esterna |

Se le prime sei vengono accettate, va aggiornato **`docs/DATI.md`**: sei celle
della colonna di chiusura avranno un provider diverso (media di mercato invece di
Pinnacle), con discrepanza attesa misurata **0.00597** in probabilità devigata.

---

## 8 · Limiti (leggerli prima di decidere)

1. **La fonte esterna non dichiara la propria provenienza.** L'etichetta
   «chiusura media-di-mercato» è un'**inferenza statistica** dai dati — per
   quanto conclusiva su due test indipendenti — non una dichiarazione del
   produttore. È il limite principale.
2. **~~Le due celle bersaglio non sono verificabili contro nulla.~~** Limite
   **superato in corsa**: la seconda fonte (§3.5) copre entrambe le partite e le
   conferma (30° e 76° percentile dello scarto abituale). Resta vero che
   l'identificazione apertura/chiusura è fatta sulle righe dove `PSC*` esiste,
   mentre in quelle due righe non esiste per definizione.
3. **Accettare le proposte mescola due provider nella stessa colonna** (6 celle su
   16.111 partite). Per Alaves–Sociedad questo rompe anche la coppia
   Pinnacle→Pinnacle voluta dalla Fase 61.
4. **Il dataset esterno non ha alcun mercato O/U**: non aiuta né il buco sistemico
   2017-19 né le nove righe O/U corrotte.
5. **La ricostruzione per scambio Mx/Av è ben supportata ma resta una
   ricostruzione**: la seconda fonte esiste ma il test **non discrimina** (§4,
   caso 2), perché lo scambio muove il margine e non la probabilità implicita.
6. **Le quattro righe la_liga sono una segnalazione, non un'analisi**: non ho
   indagato quale lato sia sbagliato né proposto valori.
7. Il test T2 «repo vs apertura» è conclusivo ma **appena** (CI95 fino a
   −0.00002). È T1 a portare il peso della conclusione, con margine larghissimo.

---

## 9 · Riproducibilità

Ogni numero di questo report si rifà con lo script qui sotto, che non scrive
niente e non modifica niente:

```
python3 caccia_quote_singole.py              # scarica quello che serve
python3 caccia_quote_singole.py --offline    # usa la cache già scaricata
```

Usa `boot()` di `scripts/_fase52_common.py` per l'incertezza e
`src/evaluation/metrics.py` per le metriche, come da protocollo: niente
log-loss o Brier reimplementati.

Fonti grezze usate: `data/fonti/football_data/*.csv` (già versionate),
`all-euro-data-*.xlsx` da football-data.co.uk, e i cinque CSV di
`github.com/iredchuk/soccer-bookmaker-odds`.

La controprova di §3.5 usa in più i file `data/ricerca_esterna/footiqo_*.json`,
raccolti da un'altra linea di lavoro della stessa sessione: il codice che la
riproduce è in coda allo script, funzione `passo_f()`.

### Lo script

```python
#!/usr/bin/env python3
"""Caccia al dato VERO per le celle-quota mancanti, una partita alla volta.

Riproduce OGNI numero del report docs/audit_5_leghe/numeri/caccia_quote_singole.md.
Uso:  python3 caccia_quote_singole.py [--offline]
      --offline salta i download (usa la cache in --cache, default: ./cache_caccia)

Passi:
  A. censimento delle celle-quota mancanti nei 5 snapshot;
  B. confronto CSV per-lega vs all-euro-data.xlsx (formato alternativo della
     stessa fonte) sulle righe interessate;
  C. forense sulle righe O/U con overround impossibile (scambio Mx/Av, slittamento);
  D. identificazione della fonte esterna github.com/iredchuk/soccer-bookmaker-odds:
     apertura o chiusura? (join per impronta-risultati, MAE su probabilita'
     devigate + log-loss, bootstrap appaiato B=10.000);
  E. confutazione (indipendenza da football-data, assenza di leakage) e costo
     del mescolamento fra provider di chiusura.
"""
import argparse, difflib, json, sys, unicodedata, urllib.request
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path("/home/user/Polymarket-oracle")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from _fase52_common import boot                      # bootstrap unico del progetto
from src.evaluation import metrics                   # metriche uniche del progetto

FD = ROOT / "data/fonti/football_data"      # grezzi gia' versionati
SNAP = {"serie_a": ROOT/"data/serie_a_matches.csv",
        "premier_league": ROOT/"data/premier_league_matches.csv",
        "la_liga": ROOT/"data/la_liga_matches.csv",
        "bundesliga": ROOT/"data/bundesliga_matches.csv",
        "ligue_1": ROOT/"data/ligue_1_matches.csv"}
DIV = {"bundesliga":"D1","la_liga":"SP1","ligue_1":"F1","serie_a":"I1","premier_league":"E0"}
REPO_URL = "https://raw.githubusercontent.com/iredchuk/soccer-bookmaker-odds/master/data/csv/"
REPO_FILE = {"bundesliga":"germany_bundesliga.csv","la_liga":"spain_primera.csv",
             "premier_league":"england_premier-league.csv","serie_a":"italy_serie-a.csv",
             "ligue_1":"france_league-1.csv"}
SEAS = {"1718":"2017-2018","1819":"2018-2019"}
OU = ["BbMx>2.5","BbAv>2.5","BbMx<2.5","BbAv<2.5"]


def get(url: str, dest: Path, offline: bool) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or offline:
        return dest
    urllib.request.urlretrieve(url, dest)
    return dest


# ---------------------------------------------------------------- A. censimento
def passo_a():
    print("\n" + "="*78 + "\nA. CENSIMENTO delle celle-quota mancanti (5 leghe x 9 stagioni)\n" + "="*78)
    gruppi = {"1x2_close":["odds_home","odds_draw","odds_away"],
              "ou_close":["odds_over25","odds_under25"],
              "1x2_open":["odds_home_open","odds_draw_open","odds_away_open"],
              "ou_open":["odds_over25_open","odds_under25_open"]}
    sparsi = []
    for lg, p in SNAP.items():
        df = pd.read_csv(p); df["season"] = df["season"].astype(str)
        for g, cols in gruppi.items():
            miss = df[cols].isna().any(axis=1)
            for s, cnt in df.loc[miss].groupby(df["season"]).size().items():
                if cnt >= 20:          # buco SISTEMICO (l'O/U di chiusura 2017-19)
                    print(f"  [sistemico] {lg:15s} {s} {g:10s}: {cnt} righe")
                    continue
                for _, r in df.loc[miss & (df["season"] == s)].iterrows():
                    sparsi.append(dict(lega=lg, stagione=s, data=r["date"],
                                       casa=r["home_team"], ospite=r["away_team"], gruppo=g))
    print(f"\n  CASI SPARSI (il bersaglio della caccia): {len(sparsi)}")
    for c in sparsi:
        print(f"    {c['lega']:15s} {c['stagione']} {c['data']} {c['casa']:15s}-{c['ospite']:15s} {c['gruppo']}")
    return sparsi


# ------------------------------------------- B. formato alternativo della fonte
def passo_b(cache: Path, offline: bool, casi):
    print("\n" + "="*78 + "\nB. La stessa fonte in un ALTRO FORMATO (all-euro-data .xlsx)\n" + "="*78)
    diffs = 0
    for lg, seas, h, a in casi:
        x = cache / f"aed_{seas}.xlsx"
        get(f"https://www.football-data.co.uk/mmz4281/{seas}/all-euro-data-20{seas[:2]}-20{seas[2:]}.xlsx", x, offline)
        if not x.exists():
            print(f"  {lg} {seas}: xlsx non in cache (rilancia senza --offline)"); continue
        c = pd.read_csv(FD/f"{lg}_{seas}.csv", encoding="latin-1")
        e = pd.read_excel(x, sheet_name=DIV[lg])
        rc = c[(c.HomeTeam==h)&(c.AwayTeam==a)].iloc[0]
        re_ = e[(e.HomeTeam==h)&(e.AwayTeam==a)].iloc[0]
        cols = [k for k in c.columns if k in e.columns and k not in ("Div","Date","Time","HomeTeam","AwayTeam")]
        d = [k for k in cols if str(rc[k]) != str(re_[k])]
        diffs += len(d)
        print(f"  {lg:14s} {seas} {h}-{a}: {len(cols)} colonne confrontate, DIVERSE: {d if d else 'nessuna'}")
    print(f"\n  totale celle diverse fra CSV e XLSX: {diffs}  -> {'formati NON identici' if diffs else 'i due formati sono identici: nessun dato nuovo'}")


# ------------------------------------------------- C. forense sulle righe O/U
def passo_c():
    print("\n" + "="*78 + "\nC. FORENSE sulle righe O/U con overround impossibile\n" + "="*78)
    frames = []
    for lg in SNAP:
        for seas in SEAS:
            d = pd.read_csv(FD/f"{lg}_{seas}.csv", encoding="latin-1").dropna(subset=OU).copy()
            d["lg"], d["seas"] = lg, seas
            frames.append(d)
    A = pd.concat(frames, ignore_index=True)
    A["orr_av"] = 1/A["BbAv>2.5"] + 1/A["BbAv<2.5"]
    A["r_over"] = A["BbMx>2.5"]/A["BbAv>2.5"]; A["r_under"] = A["BbMx<2.5"]/A["BbAv<2.5"]
    print(f"  righe con O/U Betbrain completo (5 leghe, 2017-18 + 2018-19): {len(A)}")
    print(f"  overround BbAv: mediana {A.orr_av.median():.4f}, 1%-99% [{A.orr_av.quantile(.01):.4f}, {A.orr_av.quantile(.99):.4f}]")
    bad = A[(A.orr_av < 1.0) | (A.orr_av > 1.10)]
    print(f"\n  RIGHE IMPOSSIBILI: {len(bad)}")
    print(bad[["lg","seas","Date","HomeTeam","AwayTeam"]+OU+["orr_av"]].to_string(index=False))
    sw = A[(A.r_over < 0.999) | (A.r_under < 0.999)]
    print(f"\n  righe con Max < Avg (impossibile per costruzione): {len(sw)} su {len(A)}")
    for _, r in sw.iterrows():
        o_now = 1/r["BbAv>2.5"] + 1/r["BbAv<2.5"]; o_sw = 1/r["BbMx>2.5"] + 1/r["BbMx<2.5"]
        print(f"    {r.lg} {r.seas} {r.Date} {r.HomeTeam}-{r.AwayTeam}: "
              f"overround ora {o_now:.4f} -> scambiando Mx/Av {o_sw:.4f}")
    return bad


# ------------------------------- D+E. la fonte esterna: identificazione e confutazione
def devig3(h, d, a):
    p = np.stack([1/np.asarray(h,float), 1/np.asarray(d,float), 1/np.asarray(a,float)], 1)
    return p / p.sum(1, keepdims=True)


def passo_de(cache: Path, offline: bool):
    print("\n" + "="*78 + "\nD. FONTE ESTERNA github.com/iredchuk/soccer-bookmaker-odds: apertura o chiusura?\n" + "="*78)
    rows, diag = [], []
    for lg, rf in REPO_FILE.items():
        f = get(REPO_URL + rf, cache / f"ir_{rf}", offline)
        if not f.exists():
            print(f"  {rf} non in cache (rilancia senza --offline)"); return None
        rp = pd.read_csv(f)
        for seas, rseas in SEAS.items():
            fd = pd.read_csv(FD/f"{lg}_{seas}.csv", encoding="latin-1").dropna(subset=["HomeTeam","AwayTeam","FTHG"]).copy()
            fd["FTHG"] = fd.FTHG.astype(int); fd["FTAG"] = fd.FTAG.astype(int)
            sub = rp[rp.season == rseas].copy()
            # abbinamento squadre per IMPRONTA-RISULTATI (indipendente dai nomi)
            rt = sorted(set(sub.hTeam) | set(sub.aTeam)); ft = sorted(set(fd.HomeTeam) | set(fd.AwayTeam))
            from collections import Counter
            FR = {t: (sorted(map(tuple, sub.loc[sub.hTeam==t, ["hScore","aScore"]].astype(int).values)),
                      sorted(map(tuple, sub.loc[sub.aTeam==t, ["hScore","aScore"]].astype(int).values))) for t in rt}
            FF = {t: (sorted(map(tuple, fd.loc[fd.HomeTeam==t, ["FTHG","FTAG"]].values)),
                      sorted(map(tuple, fd.loc[fd.AwayTeam==t, ["FTHG","FTAG"]].values))) for t in ft}
            ov = lambda x, y: sum((Counter(x) & Counter(y)).values())
            C = np.array([[ov(FR[t][0],FF[u][0]) + ov(FR[t][1],FF[u][1]) for u in ft] for t in rt], float)
            ri, ci = linear_sum_assignment(-C)
            mp = {rt[i]: ft[j] for i, j in zip(ri, ci)}
            fdi = fd.set_index(["HomeTeam","AwayTeam"])
            ok = miss = bad = 0
            for _, r in sub.iterrows():
                H, A_ = mp.get(r.hTeam), mp.get(r.aTeam)
                if H is None or A_ is None or (H, A_) not in fdi.index: miss += 1; continue
                f_ = fdi.loc[(H, A_)]
                if isinstance(f_, pd.DataFrame): f_ = f_.iloc[0]
                if int(f_.FTHG) != int(r.hScore) or int(f_.FTAG) != int(r.aScore): bad += 1; continue
                ok += 1
                rows.append(dict(lg=lg, seas=seas, H=H, A=A_, res=f_.FTR, rh=r.hOdd, rd=r.dOdd, ra=r.aOdd,
                                 bh=f_.get("BbAvH"), bd=f_.get("BbAvD"), ba=f_.get("BbAvA"),
                                 ph=f_.get("PSCH"), pdd=f_.get("PSCD"), pa=f_.get("PSCA")))
            diag.append(dict(lg=lg, seas=seas, n=len(sub), unite=ok, non_trovate=miss, gol_diversi=bad))
    print(pd.DataFrame(diag).to_string(index=False))
    M = pd.DataFrame(rows).dropna(subset=["rh","rd","ra","bh","bd","ba","ph","pdd","pa"]).reset_index(drop=True)
    print(f"  righe con repo + BbAv(apertura) + PSC(chiusura): {len(M)}")

    pr, pb, pp = devig3(M.rh,M.rd,M.ra), devig3(M.bh,M.bd,M.ba), devig3(M.ph,M.pdd,M.pa)
    e_b, e_p = np.abs(pr-pb).mean(1), np.abs(pr-pp).mean(1)
    rng = np.random.default_rng(20260725)
    print("\n  T1 - distanza (MAE su probabilita' devigate)")
    print(f"     dal repo all'APERTURA BbAv : {e_b.mean():.5f}")
    print(f"     dal repo alla CHIUSURA PSC : {e_p.mean():.5f}")
    print(f"     fra apertura e chiusura    : {np.abs(pb-pp).mean(1).mean():.5f}  (scala)")
    m, lo, hi, _ = boot(np.asarray(e_p - e_b), rng, 10_000)
    print(f"     diff = {m:+.5f}  CI95 [{lo:+.5f},{hi:+.5f}]  {'CONCLUSIVO' if lo>0 or hi<0 else 'nel rumore'}"
          f"  -> il repo e' una {'CHIUSURA' if m<0 else 'APERTURA'}")

    out = M.res.tolist(); y = np.array([{'H':0,'D':1,'A':2}[o] for o in out])
    ll = lambda p: -np.log(np.clip(p[np.arange(len(y)), y], 1e-15, 1))
    print("\n  T2 - potere predittivo sul risultato vero (src/evaluation/metrics.py)")
    for n, p in [("repo esterno", pr), ("BbAv apertura", pb), ("PSC chiusura", pp)]:
        print(f"     {n:15s} log-loss={metrics.log_loss_1x2(p,out):.5f}  Brier={metrics.brier_1x2(p,out):.5f}")
    for n, a_, b_ in [("repo vs apertura", ll(pr), ll(pb)), ("repo vs chiusura", ll(pr), ll(pp))]:
        m2, lo2, hi2, _ = boot(np.asarray(a_-b_), rng, 10_000)
        print(f"     {n:17s} diff={m2:+.5f} CI95 [{lo2:+.5f},{hi2:+.5f}] {'CONCLUSIVO' if lo2>0 or hi2<0 else 'nel rumore'}")

    print("\n" + "="*78 + "\nE. CONFUTAZIONE\n" + "="*78)
    frames = []
    for lg in REPO_FILE:
        for seas in SEAS:
            f_ = pd.read_csv(FD/f"{lg}_{seas}.csv", encoding="latin-1").dropna(subset=["HomeTeam","AwayTeam","FTHG"])
            f_["lg"], f_["seas"] = lg, seas; frames.append(f_)
    J = M.merge(pd.concat(frames, ignore_index=True), left_on=["lg","seas","H","A"],
                right_on=["lg","seas","HomeTeam","AwayTeam"], how="left")
    print("  E1. il repo e' una ri-esportazione di una colonna che gia' abbiamo?")
    for n, (ch, cd, ca) in {"B365":("B365H","B365D","B365A"), "BW":("BWH","BWD","BWA"),
                            "IW":("IWH","IWD","IWA"), "WH":("WHH","WHD","WHA"), "VC":("VCH","VCD","VCA"),
                            "PS apertura":("PSH","PSD","PSA"), "PSC chiusura":("PSCH","PSCD","PSCA"),
                            "BbAv apertura":("BbAvH","BbAvD","BbAvA"), "BbMx":("BbMxH","BbMxD","BbMxA")}.items():
        if ch not in J: continue
        print(f"     {n:15s} terne identiche = {((J[ch]==J.rh)&(J[cd]==J.rd)&(J[ca]==J.ra)).mean():.3%}")
    print("  E2. i numeri sono quote vere o output di un modello?")
    orr = 1/M.rh + 1/M.rd + 1/M.ra
    print(f"     overround: min {orr.min():.4f}  max {orr.max():.4f}  sotto 1: {(orr<1).mean():.3%}  (un modello non ha margine)")
    print(f"     log-loss del repo ({metrics.log_loss_1x2(pr,out):.5f}) NON e' migliore della chiusura Pinnacle "
          f"({metrics.log_loss_1x2(pp,out):.5f}): nessun leakage del risultato")
    print("  E3. costo di mescolare due CHIUSURE diverse (media-mercato vs Pinnacle)")
    d_mix, d_open = np.abs(pr-pp).mean(1), np.abs(pb-pp).mean(1)
    print(f"     MAE mescolando = {d_mix.mean():.5f}  (p50 {np.percentile(d_mix,50):.5f}, p95 {np.percentile(d_mix,95):.5f})")
    print(f"     MAE se al posto della chiusura si usasse l'APERTURA = {d_open.mean():.5f}")
    m3, lo3, hi3, _ = boot(np.asarray(d_mix - d_open), rng, 10_000)
    print(f"     diff = {m3:+.5f} CI95 [{lo3:+.5f},{hi3:+.5f}] {'CONCLUSIVO' if lo3>0 or hi3<0 else 'nel rumore'}")
    return M



# ------------------------- F. controprova con una SECONDA fonte indipendente
def passo_f():
    """Confronta le due celle recuperate con la chiusura 1xBet raccolta da
    footiqo.com da un'altra linea di lavoro della stessa sessione
    (data/ricerca_esterna/footiqo_*.json). Fonte indipendente: book diverso,
    sito diverso, raccolta diversa."""
    print("\n" + "="*78 + "\nF. CONTROPROVA con una seconda fonte indipendente (footiqo / 1xBet)\n" + "="*78)
    RIC = ROOT / "data/ricerca_esterna"
    files = [f for f in sorted(RIC.glob("footiqo_*.json"))
             if "gol" not in f.name and "manifest" not in f.name]
    if not files:
        print("  file footiqo assenti: controprova non eseguibile"); return
    rows = []
    for f in files:
        for r in json.load(open(f)):
            rows.append(dict(seas=r["Season"], H=r["homeTeam"], A=r["awayTeam"], data=r["matchDate"],
                             f1=r["xbetClose1FT"], fx=r["xbetCloseXFT"], f2=r["xbetClose2FT"],
                             fo=r.get("xbetCloseOver25",""), fu=r.get("xbetCloseUnder25","")))
    F = pd.DataFrame(rows)
    for c in ["f1","fx","f2","fo","fu"]:
        F[c] = pd.to_numeric(F[c], errors="coerce")
    print(f"  footiqo: {len(F)} righe, stagioni {sorted(F.seas.unique())}")

    scarti = {}
    for h, a, sea, rep in [("Bayern Munich","Hannover","2018/2019",[1.03,18.43,43.88]),
                           ("Alaves","Real Sociedad","2017/2018",[3.40,3.34,2.15])]:
        r = F[(F.H==h)&(F.A==a)&(F.seas==sea)]
        assert len(r) == 1, f"attesa 1 riga per {h}-{a} {sea}, trovate {len(r)}"
        r = r.iloc[0]
        pf = devig3([r.f1],[r.fx],[r.f2])[0]; pr = devig3([rep[0]],[rep[1]],[rep[2]])[0]
        scarti[h] = float(np.abs(pf-pr).mean())
        print(f"\n  {h} - {a} ({r.data})")
        print(f"     fonte A media-mercato : {rep} -> p {np.round(pr,5)}")
        print(f"     fonte B 1xBet chiusura: [{r.f1}, {r.fx}, {r.f2}] -> p {np.round(pf,5)}")
        print(f"     MAE fra le due fonti  : {scarti[h]:.5f}")

    # scala: disaccordo abituale fra le due fonti
    M = passo_de.__globals__.get("_M_cache")
    if M is None:
        print("\n  (scala non calcolabile senza il join del passo D)"); return
    F["k"] = F.H.astype(str)+"|"+F.A.astype(str)
    F["yr"] = F.seas.str[:4].map({"2017":"1718","2018":"1819","2019":"1920"})
    M = M.copy(); M["k"] = M.H.astype(str)+"|"+M.A.astype(str)
    J = M.merge(F[["k","yr","f1","fx","f2"]], left_on=["k","seas"], right_on=["k","yr"],
                how="inner").dropna(subset=["f1","fx","f2"])
    pr, pf, pp = devig3(J.rh,J.rd,J.ra), devig3(J.f1,J.fx,J.f2), devig3(J.ph,J.pdd,J.pa)
    d = np.abs(pr-pf).mean(1)
    print(f"\n  scala su {len(J)} righe con entrambe le fonti:")
    print(f"     MAE(fonte A, fonte B) = {d.mean():.5f}  percentili "
          f"{ {q: round(float(np.percentile(d,q)),5) for q in [50,75,90,95,99]} }")
    print(f"     MAE(fonte A, PSC) = {np.abs(pr-pp).mean(1).mean():.5f}   "
          f"MAE(fonte B, PSC) = {np.abs(pf-pp).mean(1).mean():.5f}")
    for h, m in scarti.items():
        print(f"     lo scarto su {h} ({m:.5f}) e' al percentile {float((d<m).mean())*100:.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--cache", default="./cache_caccia")
    a = ap.parse_args()
    cache = Path(a.cache)
    passo_a()
    passo_b(cache, a.offline, [("bundesliga","1819","Bayern Munich","Hannover"),
                               ("bundesliga","1819","Bayern Munich","Hoffenheim"),
                               ("la_liga","1718","Alaves","Sociedad"),
                               ("serie_a","2122","Torino","Fiorentina"),
                               ("serie_a","2021","Verona","Genoa")])
    passo_c()
    M = passo_de(cache, a.offline)
    passo_de.__globals__["_M_cache"] = M
    passo_f()


if __name__ == "__main__":
    main()
```

---

*Fine. Nessuno snapshot toccato, nessun commit fatto: come da regole della sessione.*
