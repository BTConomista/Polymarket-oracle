# Report 11 — Il GG/NG contro le quote vere: cade una premessa del progetto

Il GG/NG ha un report suo perché non è un mercato come gli altri. È il mercato
su cui il progetto ha scritto, in `CLAUDE.md` §1.8, la frase che ne ha guidato
le priorità:

> il **GG/NG non ha quote nei dati** (football-data non le include), quindi è
> l'unico dove non possiamo dimostrare l'efficienza del mercato — l'unico con
> «spazio» non ancora chiuso dai risultati [delle fasi precedenti]. Priorità lì.

Il lavoro sui dati ([`09_chiusura_buchi.md`](09_chiusura_buchi.md) §2.4) ha
portato **quote di chiusura GG/NG reali** (1xBet, via footiqo) per 5 leghe e 3
stagioni. La premessa quindi non regge più: le quote esistono. Questo report
misura che cosa c'era, dentro quello «spazio».

La risposta, in una riga: **il mercato GG/NG è informativo, il nostro miglior
prezzo lo pareggia e non lo batte, il Dixon-Coles perde di netto.** Lo «spazio»
non era una proprietà del mercato: era la nostra ignoranza. Quella frase di
`CLAUDE.md` va riscritta.

---

## 1 · Che cosa è stato misurato, e con quale apparato

Join footiqo(1xBet) ↔ snapshot per (lega, stagione, squadre canonicalizzate),
data usata come controllo: **5.337 partite finali** su 5 leghe × 3 stagioni
(2017-18: 1.825; 2018-19: 1.825; 2019-20: 1.687).

**Lucchetti superati prima di misurare:** gol della fonte identici ai nostri su
3.652 righe su 3.652 (0 discordanze); 0 righe con data fuori da ±1 giorno;
scartate 38 righe senza quota GG/NG (Premier 2019-20) e 2 senza 1X2 nello
snapshot.

**Controllo di sanità contro un numero già pubblicato dal progetto**
(report 9 §2.4, che dava il «primo sguardo» sulla finestra 2017-19):

| quantità | atteso (report 9 §2.4) | ottenuto |
|---|--:|--:|
| p medio GG del book | 0.526 | **0.5268** |
| frequenza reale GG | 0.516 | **0.5140** |
| log-loss del book | 0.687 | **0.6851** |
| overround | 1.043 | **1.0433** |
| n | 3.652 | **3.650** |

L'apparato riproduce il riferimento. Tutti i parametri delle leve sono scelti
**fuori campione**, bootstrap appaiato B = 10.000, seed 20260726.

**Aspettativa dichiarata prima di misurare** (nell'intestazione dello script,
prima di guardare qualunque numero): il mercato GG/NG è informativo ma meno
lavorato dell'1X2; il market-implied nutrito dalle quote dello *stesso* book gli
sarà molto vicino; il DC standalone perderà; un edge, se appare, è quasi
certamente il margine del book letto male.

---

## 2 · Il mercato GG/NG è informativo, ma è il fanalino di coda del listino

| metrica | riferimento | Δ | CI95 | n | verdetto |
|---|--:|--:|---|--:|---|
| log-loss GG/NG del book **0.6840** | baseline LOSO di lega 0.6921 | **−0.00814** | [−0.01164, −0.00464] | 5.337 | **conclusivo: informativo** |
| log-loss O/U 2.5 **stesso book** 0.6661 | baseline LOSO 0.6913 | **−0.02517** | [−0.03085, −0.01950] | 5.337 | **3,1× più informativo** |

La *skill* del prezzo GG/NG sulla baseline è dello **0,65%**. Sulle stesse
partite, con lo stesso book, il prezzo dell'Over/Under 2.5 ne ha tre volte
tanta. E costa di meno:

| mercato | overround del book |
|---|--:|
| GG/NG | **1.0461** |
| Over/Under 2.5 | 1.0295 |
| 1X2 | 1.0284 |

Il GG/NG costa **1,7 punti di margine in più** e porta un terzo
dell'informazione. L'intuizione del progetto — «è un mercato meno lavorato» —
è confermata e ora quantificata. Ma «meno lavorato» non significa «battibile»:
è la differenza fra le due cose il contenuto del §3.

---

## 3 · Il nostro prezzo non batte il book. Il DC perde di netto.

Sei predittori contro il prezzo GG/NG del book. Δ > 0 significa che il book è
migliore.

| # | predittore | log-loss | riferimento | Δ | CI95 | n | verdetto |
|---|---|--:|--:|--:|---|--:|---|
| a | market-implied dalle quote **dello stesso book** | 0.6846 | book 0.6851 | −0.00045 | [−0.00207, +0.00121] | 3.650 | nel rumore |
| a | idem, 3 stagioni | 0.6836 | 0.6840 | −0.00041 | [−0.00174, +0.00086] | 5.337 | nel rumore |
| a2 | idem, dalla **scaletta completa** del book | 0.6833 | 0.6840 | −0.00067 | [−0.00182, +0.00048] | 5.337 | nel rumore |
| b1 | snapshot: 1X2 chiusura + **O/U apertura reale** | 0.6845 | 0.6840 | +0.00060 | [−0.00123, +0.00244] | 5.328 | nel rumore |
| b2 | snapshot + **stima** O/U del progetto | 0.6848 | 0.6851 | −0.00015 | [−0.00267, +0.00231] | 3.641 | nel rumore |
| b0 | snapshot + O/U **chiusura reale** (solo 2019-20) | 0.6820 | 0.6816 | +0.00035 | [−0.00209, +0.00274] | 1.687 | nel rumore |
| c | **DC gol+xG walk-forward** | 0.6934 | 0.6840 | **+0.01036** | **[+0.00632, +0.01454]** | 3.512 | **il book vince** |

Il path (b1) è la variante **primaria dichiarata**: nel 2017-19 l'unico input
O/U reale è quello di apertura, mentre la stima del progetto (b2) ha
coefficienti fittati su stagioni successive ed è quindi un benchmark storico,
non una predizione.

Il market-implied, comunque lo si nutra, è **indistinguibile** dal prezzo del
book (correlazione 0.962, MAE 0.019). Il DC perde in modo conclusivo in tutti e
tre i blocchi, con calibrazione pessima (pendenza 0.438, bias −0.025).

**Test di encompassing** (lo stesso disegno con cui il progetto aveva già
mostrato che la chiusura ingloba il modello sull'1X2): si fitta il peso α del
blend fra prezzo del book e nostro prezzo.

| blend | α\* medio | quota di fit con α\* = 0 | Δ vs book | CI95 |
|---|--:|--:|--:|---|
| book + market-implied | 0.717 | 7% | −0.00047 | [−0.00144, +0.00048] |
| book + **DC** | **0.060** | **70%** | +0.00022 | [−0.00016, +0.00060] |

Sul GG/NG **il prezzo del book ingloba il DC**, esattamente come sull'1X2. Il
market-implied invece pesa 0.717 — ma non guadagna nulla, perché è lo stesso
oggetto letto due volte.

---

## 4 · Nessuna leva aiuta, su nessuno dei due fronti

Le leve che il progetto associa al GG/NG, misurate contro il nostro path (a) sui
due fronti del principio §1.9 — **per-lega** (leave-one-season-out) e
**generale** (leave-one-league-out, pooled).

| leva | fronte | Δ | CI95 | verdetto |
|---|---|--:|---|---|
| ricalibrazione dei livelli **λ+μ** | per-lega | **+0.00092** | [+0.00007, +0.00178] | **peggiora, conclusivo** |
| ricalibrazione **λ+μ** | generale (pooled) | **+0.00075** | [+0.00012, +0.00137] | **peggiora, conclusivo** |
| ricalibrazione del **solo μ** | per-lega | +0.00008 | [−0.00044, +0.00060] | nel rumore |
| ricalibrazione del **solo μ** | generale | +0.00027 | [−0.00001, +0.00055] | nel rumore (sfiora il peggioramento) |
| φ(\|λ−μ\|) | per-lega | −0.00006 | [−0.00033, +0.00022] | nel rumore |
| φ **costante** (κ = 0) | per-lega | +0.00002 | [−0.00018, +0.00021] | nel rumore |
| ricalibrazione Platt del **prezzo del book** | per-lega | **+0.00198** | [+0.00064, +0.00333] | **peggiora, conclusivo** |
| ricalibrazione Platt del book | generale | +0.00012 | [−0.00037, +0.00062] | nel rumore |
| offset puro (pendenza fissa a 1) sul book | generale | +0.00007 | [−0.00043, +0.00055] | nel rumore |

Il fronte generale non salva niente: dove la leva peggiora, peggiora su
entrambi i fronti; dove è nel rumore, è nel rumore su entrambi. È la prima volta
che i due fronti vengono misurati appaiati su questo mercato, e nessuno dei due
vince.

**Il segnale che questo lavoro non conferma.** Il report 10 §6 riportava, come
unica cella conclusiva positiva di quel blocco, la ricalibrazione-μ sul GG/NG in
Bundesliga (+0.00059, CI conclusivo) — misurata però contro **noi stessi**
(calibrazione contro la realtà). Col giudice esterno, cioè contro il prezzo di un
book, quella stessa leva in Bundesliga dà:

| | Δ | CI95 | n |
|---|--:|---|--:|
| ricalibrazione-μ, bundesliga, giudice esterno | **−0.00008** | [−0.00092, +0.00075] | **917** |

Cioè nulla. **Non lo dichiaro smentito**: finestra diversa (2017-20 invece di
2019-26), tassi diversi (1xBet invece della chiusura multi-book), n più che
dimezzato — è un test meno risolvente, non una confutazione. Lo dichiaro **non
confermato dal test esterno**. Il dettaglio per lega dice comunque che non c'è
niente da nessuna parte: serie_a +0.00002, premier +0.00025, la_liga −0.00017,
bundesliga −0.00008, ligue_1 +0.00040 — nessuna lega con CI conclusivo.

---

## 5 · Il fatto nuovo, e perché non è un edge

Il risultato più conclusivo di tutto il lavoro non riguarda chi prevede meglio,
ma **quanto i due prezzi differiscono**:

| | Δ | CI95 | n |
|---|--:|---|--:|
| scarto **appaiato** book − nostro path (a) sul GG | **+0.0160** | **[+0.0155, +0.0165]** | 5.337 |

Il book prezza il GG **1,60 punti percentuali sopra la proiezione dei suoi
stessi marginali 1X2 + O/U**. È l'intervallo più stretto e più lontano dallo
zero di tutto il report.

Ma **chi dei due abbia ragione non è decidibile**:

| bias di livello contro l'esito reale | Δ | CI95 |
|---|--:|---|
| del **book** (freq. reale 0.5233) | +0.0084 | [−0.0049, +0.0218] |
| del **nostro path (a)** | −0.0076 | [−0.0208, +0.0056] |

Entrambi contengono lo zero. Sappiamo che i due prezzi differiscono; non
sappiamo quale sia storto.

E la confutazione (§6, C7-C8) mostra che **lo scarto non è nemmeno
attribuibile al book**: un terzo è il nostro vincolo ρ = −0.06, e il resto è
della stessa taglia dell'errore con cui la nostra famiglia Poisson sbaglia le
linee O/U che non ha usato come bersaglio.

---

## 6 · Otto tentativi di distruggere il risultato, e i due che hanno colpito

**C1 — «è il margine del book letto male?»** Era l'ipotesi che l'aspettativa
dichiarata indicava come più probabile. Rifatto il devig della quota GG/NG in
due modi alternativi: additivo (+0.00010, CI [−0.00009, +0.00030], nel rumore) e
*power* con η risolto riga per riga (+0.00370, CI [+0.00111, +0.00629],
**conclusivamente peggiore**). Il devig moltiplicativo, fonte unica del
progetto, resta il migliore: il vantaggio apparente del nostro prezzo non nasce
da un devig sbagliato. Confutazione fallita — ma il vantaggio non era comunque
conclusivo.

**C2 — «il prezzo GG/NG del book aggiunge informazione ai suoi stessi
marginali?»** Regressione y ~ logit(p_nostro) + [logit(p_book) −
logit(p_nostro)]: coefficiente dello scarto +0.212, CI95 bootstrap
[−0.49, +0.97]. Il CI contiene sia 0 sia 1: **il test è sotto-potenziato e non
decide nulla.** Lo dichiaro invece di leggerlo come «coefficiente ≈ 0, quindi il
book non sa niente».

**C3 — «la scaletta completa è davvero meglio?»** a2 contro a: −0.00026, CI
[−0.00067, +0.00016], nel rumore. Le altre linee O/U del book non aggiungono
niente di dimostrabile.

**C4 — stabilità.** Il vantaggio (minuscolo) del nostro path (a) sul book è
negativo in 3/3 stagioni (−0.00079, −0.00011, −0.00032) ma **cambia segno fra
leghe**: negativo in 4 (bundesliga −0.00108, la_liga −0.00129, ligue_1 −0.00089,
premier −0.00034), **positivo in Serie A** (+0.00138). Un effetto che non regge
il cambio di lega non è un effetto.

**C5 — ordine di grandezza.** Overround 1.0461 significa 2,3% di margine per
lato. Qualunque «edge» dell'ordine di 10⁻⁴–10⁻³ di log-loss è **due ordini di
grandezza sotto il margine**: anche se fosse reale, non sarebbe monetizzabile.

**C6 — l'allarme rosso.** Se la nostra matrice non riproducesse i bersagli del
book, il «nostro prezzo» non sarebbe la proiezione dei suoi marginali e lo
scarto di 1,60 punti sarebbe un artefatto. Residui medi assoluti dell'inversione
a ρ = −0.06: 1X2 [0.0038, **0.0087**, 0.0049], O/U 2.5 0.0030 — **lo stesso
ordine di grandezza dello scarto da spiegare.**

**C7 — la prova decisiva, contro di me.** Liberando ρ (3 parametri, 4 bersagli)
l'inversione centra 1X2 e O/U 2.5 **esattamente** (residui 0.0000 su tutti e
quattro), con ρ medio **−0.0928** (sd 0.0505), più negativo del −0.06 ufficiale.
Lo scarto book − noi scende da **+0.0160 a +0.0107**: **un terzo dello scarto era
il nostro vincolo su ρ, non il book.** Il nostro prezzo a ρ libero diventa quasi
non-biased (−0.0022, CI [−0.0152, +0.0112]) ma in log-loss resta nel rumore
contro il book (−0.00050, CI [−0.00165, +0.00059]).

**C8 — e il resto?** La matrice a ρ libero riproduce le linee O/U che *non* ha
usato come bersaglio? No:

| linea | scarto della nostra matrice dal book |
|---|--:|
| over 0.5 | +0.0107 |
| over 1.5 | +0.0132 |
| over 3.5 | −0.0102 |
| over 4.5 | −0.0151 |

La distribuzione dei gol totali del book ha **code più grasse della Poisson**, e
questi residui sono **della stessa taglia dello scarto GG/NG residuo**
(+0.0107). Conclusione contro il mio stesso risultato: **lo scarto sul GG/NG non
è attribuibile al book, è indistinguibile dalla cattiva specificazione della
nostra famiglia di modelli.** L'unica cosa dimostrata è che i due prezzi
differiscono, non chi ha ragione.

---

## 7 · Il ROI, e perché non è stato misurato

**Regola dichiarata prima:** nessun ROI se nessun nostro prezzo batte il book
con CI conclusivo. Nessuno lo fa, quindi **non è stato misurato**.

Le sole cifre di ROI riportate sono di strategie cieche, e servono a misurare il
margine:

| strategia | ROI | CI95 | margine atteso |
|---|--:|---|--:|
| sempre GG | **−5,92%** | [−8,33%, −3,48%] | −4,41% |
| sempre NG | −2,59% | [−5,34%, +0,19%] | −4,41% |

Il mercato non è battibile alla cieca, e non abbiamo niente con cui non
esserlo. **Nulla in questo lavoro autorizza a scommettere soldi veri.**

---

## 8 · La rosa, limitata al mercato GG/NG

Finestra: 1xBet chiusura 2017-20, giudice esterno = il prezzo GG/NG del book.

| voce | per-lega (5 leghe) | generale | motivo |
|---|---|---|---|
| **market-implied** (`price_markets` da 1X2+O/U) | ⚽ titolare | ⚽ titolare | pareggia il book (Δ fra −0.00045 e +0.00060, sempre nel rumore) e batte il DC in modo conclusivo. Nessuna costante per-lega è risultata necessaria: coincide col fronte generale perché non ha parametri fittati |
| variante dalla **scaletta completa** del book | 🪑 panchina, promettente | 🪑 idem | segno favorevole 3/3 blocchi, MAE dal book più bassa (0.0159 contro 0.0186), mai conclusiva. Promozione se replica su più partite o su un secondo book |
| variante a **ρ libero** (3 parametri) | 🪑 panchina | 🪑 panchina | centra i marginali esattamente e azzera il bias di livello, ma in log-loss è nel rumore. Vale come **diagnostico**: il ρ implicito del book è −0.093, non −0.06 |
| **DC gol+xG** | ❌ bocciato come alternativa al mercato · ⚽ titolare come fallback senza quote | idem | +0.01036 [+0.00632, +0.01454]; encompassing α\* = 0.060 con α\* = 0 nel 70% dei fit. Non applicabile al 2017-18 (nessuno storico) |
| ricalibrazione livelli **λ+μ** | ❌ bocciata | ❌ bocciata | peggiora con CI conclusivo su entrambi i fronti |
| ricalibrazione **solo μ** | 🪑 panchina | 🪑 panchina | nel rumore ovunque; il segnale Bundesliga del report 10 §6 **non si ritrova**. Promozione solo con >2.000 partite di quel campionato |
| **φ(\|λ−μ\|)** | 🪑 panchina | ⬜ mai testato | nel rumore; parametri instabili fra stagioni (φ₀ da 0.00 a 0.62, κ da 1.6 a 5.0) = sovradattamento del fit |
| **φ costante** (κ = 0) | 🪑 panchina | ⬜ | nel rumore, indistinguibile dalla φ35 e dallo zero |
| **ricalibrazione Platt del book** (leva nuova) | ❌ bocciata | 🪑 panchina | per-lega peggiora con CI conclusivo (2 stagioni di training per lega = pura varianza); pooled nel rumore. Il bias di livello del book (+0,84 pt) esiste ma **non è correggibile in modo dimostrabile** |

**Nota trasversale sul principio §1.9.** Il segno non è universale solo per una
cosa: il bias di livello del book. La Liga sovra-prezza il GG di 2,3 punti, la
Serie A lo sotto-prezza di 1,3 — la stessa lezione già trovata sul draw-bias
delle leghe.

---

## 9 · Limiti

1. **Risoluzione.** Con 5.337 partite la semi-ampiezza attesa del CI95 sul
   confronto in log-loss è **0.00130** (sd delle differenze per riga 0.0485).
   *Tutti* i confronti fra il nostro prezzo e il book stanno fra −0.0007 e
   +0.0021, cioè **dentro la soglia**: «non dimostrato» non è «dimostrato
   nullo». Per risolvere 0.0005 servirebbero ~36.000 partite, sei volte questo
   campione.
2. **Un solo book.** Tutte le quote GG/NG vengono da 1xBet, overround 1.0461.
   Non è la chiusura media multi-book che gli snapshot contengono dal 2019-20: è
   il prezzo di un singolo operatore, e le sue idiosincrasie — per esempio il
   +1,6 pt di GG sopra i propri marginali — potrebbero non essere del mercato.
3. **Tre stagioni, due delle quali contigue.** 2017-18/2018-19 (bersaglio) +
   2019-20 (controllo, troncata dal COVID in Ligue 1: 279 partite). Il LOSO
   per-lega fitta su due sole stagioni (~730 righe): è quasi certamente questo a
   far fallire la ricalibrazione per-lega del book, mentre la pooled resta nel
   rumore.
4. **Il DC non copre il 2017-18** (`run_backtest` fallisce: «Nessuna partita
   disponibile prima di as_of_date», perché gli snapshot iniziano lì). Il path
   (c) vive su 3.512 partite di 2018-19 e 2019-20, e il 2018-19 è un anno di
   cold-start con una sola stagione di storico: il DC è misurato nella sua
   condizione peggiore. Il segno però non è in discussione — perde in entrambe
   le stagioni separatamente.
5. **Il path (b2) usa una stima anti-causale** (coefficienti fittati su stagioni
   successive). Dichiarato, e per questo la primaria è (b1).
6. **Molteplicità.** Confronti totali contro il book: 6 predittori × 3 blocchi +
   6 leve = **24**. Famiglia pre-registrata per l'headline: 4. Bonferroni sulla
   famiglia headline α = 0.0125; su tutti i confronti α = 0.0021. I tre risultati
   dichiarati conclusivi — il mercato è informativo, il DC perde, lo scarto
   appaiato di 1,6 punti — superano ampiamente anche il Bonferroni più severo;
   nessuno degli altri lo avvicina.
7. **Attribuzione.** Come mostra C8, la famiglia Poisson + correzione DC non
   riproduce la distribuzione dei gol totali del book entro ~1,3 punti. Un test
   più forte (fit congiunto di λ, μ, ρ e θ double-Poisson sull'intera scaletta)
   sarebbe la strada giusta ma costa ~40 minuti di CPU per riga: **non fatto, e
   dichiarato non fatto**.
8. **Nessun ROI misurato**, per regola pre-dichiarata (§7).

---

## 10 · Che cosa ne consegue per il progetto

1. **`CLAUDE.md` §1.8 va riscritto.** La frase «il GG/NG è l'unico mercato dove
   non possiamo dimostrare l'efficienza del mercato — l'unico con spazio non
   ancora chiuso. Priorità lì» è superata dai fatti: le quote esistono per 3
   stagioni e 5 leghe, e la risposta è che il mercato GG/NG è informativo, il
   nostro prezzo lo pareggia, il DC perde. Il GG/NG **non è più il mercato
   prioritario** per assenza di prove: le prove ci sono.
2. **Il perimetro di quanto è stato dimostrato va detto per intero.** Vale per
   *un book*, per *tre stagioni*, e con una soglia di risoluzione di 1,3
   millesimi. Non è la dimostrazione che il GG/NG di *tutto il mercato* è
   efficiente: è la dimostrazione che il GG/NG di 1xBet nel 2017-20 non è
   battuto da niente di ciò che abbiamo.
3. **Il ρ del progetto merita un'occhiata, ma non da qui.** Il ρ implicito del
   book su questo campione è −0.093, non −0.06, e liberarlo cancella un terzo
   dello scarto. È un indizio, non un mandato: in log-loss non guadagna nulla, e
   il fronte generale (report 10 §10) ha trovato che ρ e θ sono in gran parte
   sostituti.
4. **Il valore residuo del GG/NG resta quello dichiarato altrove:** prezzarlo
   *calibrato* dove il book non lo quota. Non batterlo dove lo quota.

→ `cantiere/scripts/ggng_contro_quote.py`, `cantiere/out/ggng_contro_quote.json`
