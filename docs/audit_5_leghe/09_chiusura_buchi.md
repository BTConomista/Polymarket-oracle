# Report 9 — Chiudere i buchi: cosa si è recuperato davvero, cosa si è stimato

Richiesta: *«risolviamo quanti più buchi nei dati abbiamo (o trovandoli su
internet o da qualche parte, o facendo delle stime quanto più accurate)»*.

Il bilancio in una riga: **il buco più grande è chiuso** — 1.362 partite delle
due leghe nuove hanno ora una chiusura O/U stimata con errore misurato ~0.013, e
per il 2017-19 esiste anche un **dato reale** che prima si riteneva
irrecuperabile. Ma il risultato più onesto è che il dato reale trovato **non
batte la stima**, e va usato per quello che è.

Un secondo giro di lavoro (§5-§7) ha poi ripreso i tre buchi rimasti: le 9 linee
O/U di apertura corrotte, le celle residue una per una, e il tiro in porta di
una partita. Ne sono usciti un miglioramento netto della stima peggiore del
lotto, due celle chiuse con dato vero, due lasciate `NaN` per scelta, e — il
risultato più grande — la scoperta che **il buco maggiore rimasto non è un
`NaN`**: sono 1.603 celle di `midweek_europe` che valgono 0 e non dovrebbero.

Una verifica avversariale successiva ha poi **ritirato una conclusione** di
questo report: lo stimatore della chiusura O/U **non** passa da pooled a
per-lega (§3). Le 1.362 stime **sono state rigenerate** col pooled e l'errore
dichiarato è ora quello del regime d'uso — 0.0143 e 0.0125, non 0.0122 e 0.0110
(§3-bis).

---

## 1 · Il bilancio

| buco | prima | dopo | come |
|---|--:|--:|---|
| chiusura O/U 2017-19, bundesliga + ligue_1 | 2.744 celle vuote | **1.362 partite stimate** (MAE **0.0143 / 0.0125** nel regime d'uso; 0.0124/0.0114 in interpolazione) | stima E3 **pooled** (§3) |
| chiusura O/U 2017-19, tutte e 5 le leghe | nessun dato reale | **3.652 partite di dato reale** (1xBet) | fonte esterna nuova |
| quote GG/NG 2017-19 | **inesistenti** in tutto il progetto | **3.652 partite** → misurate in [`11_ggng.md`](11_ggng.md) | stessa fonte |
| calendari di coppa | 3.045 righe mancanti | **3.045 righe recuperate** (50 CSV) | Wikipedia + terza fonte |
| 1X2 di chiusura mancante (2 partite) | vuoto | **dato reale proposto**, con una riserva nuova sul profilo (§7.1) | fonte esterna nuova |
| xG segnaposto | 1 riga sospetta trovata a mano | **cercato con 9 test su 16.110 partite** → 1, confermata | batteria di firme |
| **9 linee O/U di apertura corrotte** | stimate (MAE 0.0267) | **stima migliorata: MAE 0.0143** (o 0.0197 senza dato nuovo) | bakeoff di 26 varianti (§5) |
| **tiro in porta mancante** (Union-Bochum, 2 celle) | vuoto | regola di ricostruzione **misurata**, non applicata (§6) | Understat tiro-per-tiro |
| **xG mancanti** (2 partite, 12 celle) | vuoto | restano **`NaN` dichiarato**, con la prova che è la scelta giusta (§7.2-§7.3) | stima sopra soglia / fonte non consolidata |
| **`midweek_europe` falsi zero** | invisibile: sembrava dato | **1.603 celle** e 1.700 riposi sbagliati, quantificati (§7.4) | dai calendari già recuperati |

Nessuna correzione è stata applicata agli snapshot: tutto è **proposta**, in
attesa di decisione (§9).

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

**Il risultato che sembrava ribaltare una convinzione del progetto — e che una
verifica successiva ha smontato.** Lo stimatore ufficiale è pooled perché, con 3
leghe, il pooled batteva il per-lega; qui con 5 leghe e 12.457 partite di fit il
per-lega vinceva con CI conclusivo, e si era concluso «lo stimatore passa a
per-lega».

**Non regge.** La verifica avversariale (report 10 §15) ha reimplementato
lo stimatore da zero e provato sette protocolli di validazione. Il ribaltamento
è un artefatto del protocollo:

| protocollo | Δ MAE (per-lega − pooled) | CI95 | n | chi vince |
|---|--:|---|--:|---|
| leave-one-cella-out, scope **2 leghe nuove** (quello usato sopra) | −0.000309 | [−0.000425, −0.000193] | 4.479 | per-lega |
| k-fold casuale, 2 leghe nuove | −0.000475 | [−0.000584, −0.000365] | 4.479 | per-lega |
| leave-one-stagione-out, 2 leghe nuove | −0.000320 | [−0.000436, −0.000207] | 4.479 | per-lega |
| stesso stimatore, scope **tutte e 5 le leghe** | **+0.000078** | [+0.000010, +0.000147] | 12.457 | **pooled** |
| stesso stimatore, **serie_a** | **+0.001104** | CI conclusivo | 2.658 | **pooled** (3,5× il guadagno rivendicato) |
| **estrapolazione all'indietro** (fit sulle stagioni tarde → stima sul 2017-19: il regime d'uso vero) | **+0.000662** | **[+0.000402, +0.000916]** | 1.957 | **pooled, conclusivo** |
| idem con 5 / 6 stagioni di training | +0.000656 / +0.000690 | CI conclusivi | 1.271 / 585 | pooled |
| idem, bundesliga / ligue_1 separate | +0.00047 / +0.00083 | CI conclusivi | 918 / 1.039 | pooled su ciascuna |

I primi tre protocolli sono di **interpolazione** (il fit vede stagioni prima e
dopo la riga stimata); l'ultimo è il **regime in cui la stima viene davvero
usata**, perché la chiusura O/U del 2017-19 non esiste e i coefficienti possono
venire solo da stagioni successive. Lì vince il pooled, su entrambe le leghe
separatamente e con 4, 5 o 6 stagioni di training — quindi non è una questione
di taglia del campione di fit.

**Conseguenza:** lo stimatore ufficiale resta **E3 pooled**; il per-lega è
bocciato per questo uso.

### 3-bis · Il file è stato rigenerato (e il criterio di scelta corretto)

Non bastava correggere il testo: il CSV che finirà in produzione era stato
prodotto col per-lega. Lo script è stato **riscritto nel punto che contava** —
la scelta non si fa più in interpolazione ma **nel regime d'uso**, e ogni
candidato viene rifittato lì.

Nel farlo è saltato fuori un difetto **del nuovo protocollo**, ed è giusto
scriverlo perché è lo stesso errore che la verifica aveva punito altrove: il
candidato «finestra vicina» si allenava sulle stagioni 2019-20 e 2020-21, cioè
**proprio quelle su cui veniva valutato**, e con quel vantaggio vinceva. Chiuso
alla radice: ora nessun candidato vede la stagione di test.

Rifatto pulito, il quadro nel regime d'uso (MAE, 2 leghe nuove insieme):

| candidato | MAE | vs pooled | CI95 | Bonferroni (4 test) |
|---|--:|--:|---|---|
| finestra vicina 2019-21 | 0.01307 | −0.00031 | [−0.00055, −0.00007] | [−0.00061, **−0.0000006**] |
| pooled 4 leghe (LOLO) | 0.01336 | −0.00002 | [−0.00007, +0.00004] | nel rumore |
| **pooled 5 leghe** | **0.01338** | — | — | — |
| pooled 3 storiche | 0.01338 | +0.00000 | [−0.00012, +0.00013] | nel rumore |
| per-lega | 0.01442 | **+0.00104** | [+0.00072, +0.00136] | **conclusivo: peggiora** |

La «finestra vicina» è nominalmente prima, ma il suo intervallo di Bonferroni
**tocca lo zero** (limite superiore −6 × 10⁻⁷: un risultato che non esiste). E
soprattutto **il segno non si replica**: −0.00102 in Bundesliga, **+0.00035 in
Ligue 1**. Vale qui la stessa regola che il progetto applica a ogni leva — se
non regge su entrambe le leghe, non è una leva. Scelto **E3 pooled a 5 leghe**,
che è anche la formula già in produzione.

**L'errore dichiarato ora è quello del regime d'uso**, non quello ottimistico:

| lega | MAE dichiarato (regime d'uso) | (in interpolazione sarebbe) |
|---|--:|--:|
| bundesliga | **0.0143** | 0.0124 |
| ligue_1 | **0.0125** | 0.0114 |

Entrambi i valori sono scritti riga per riga nel CSV, in due colonne distinte,
perché non si possano confondere.

**Errore in interpolazione, lega per lega** (il numero *ottimistico*, tenuto qui
solo per confronto — quello che vale è la tabella del §3-bis):

| lega | MAE (interpolazione) | | lega | MAE (interpolazione) |
|---|--:|---|---|--:|
| bundesliga | 0.0124 | | serie_a | 0.0134 |
| ligue_1 | 0.0114 | | premier_league | 0.0122 |
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

→ `data/estimates/ou_close_2017_19.csv`, le 1.362 righe `bundesliga`/`ligue_1`
(il file pubblicato copre tutte e 5 le leghe, 3.638 righe; probabilità, mai
quote).

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

## 5 · Le 9 linee O/U di apertura corrotte: il campione in carica è stato battuto

Erano date per chiuse: 9 righe con la linea O/U di apertura svuotata perché
aritmeticamente impossibile, stimate invertendo il solo 1X2 e correggendo con un
bias costante (MAE 0.0267 contro 0.0743 di baseline). Un bakeoff di **26
varianti** su 3.643 partite con la linea integra — stesse 5 leghe, stesse
stagioni 2017-19, k-fold k = 5, ogni parametro fittato solo sulle fold di train —
mostra che quella stima **non era al suo tetto**, e che il suo limite non è
l'inversione ma il **bias costante**.

| variante | MAE | Δ vs campione | CI95 | verdetto |
|---|--:|--:|---|---|
| **M1** inversione 1X2 + bias costante (campione in carica) | **0.0267** | — | — | riferimento, p90 0.0559 |
| M2b logit(y) ~ logit 1X2, per-lega | 0.0211 | −0.0056 | — | batte M1 |
| M3 bias = a + b·(λ+μ), per-lega | 0.0209 | −0.0058 | — | l'ipotesi «il bias dipende dal totale» è giusta |
| **M4** superficie di debias quadratica su (T = λ+μ, D = \|λ−μ\|), per-lega | **0.0197** | **−0.00700** | **[−0.00764, −0.00636]** | **conclusivo** (Bonferroni ×26 superato) |
| M4d isotonica su p grezza, per-lega | 0.0204 | +0.0007 vs M4 | — | panchina |
| M4e GBM su 1X2 + inversione | 0.0212 | +0.0015 vs M4 | — | bocciato: la struttura batte la flessibilità |
| M5 chiusura 1xBet grezza (nessun fit) | 0.0228 | −0.0039 | — | serve la ricalibrazione |
| **M5g** logit(y) ~ scaletta 1xBet + 1X2 di apertura, per-lega | **0.0143** | **−0.01240** | **[−0.01314, −0.01165]** | **conclusivo**, p90 0.0299 |

**Due vincitori, per due usi diversi.** M5g (0.0143) usa il dato nuovo — la
chiusura 1xBet del §2 — e quindi **assorbe il movimento apertura→chiusura**:
quelle 9 righe non vanno mai usate per misurare quel movimento. M4 (0.0197) usa
**solo l'1X2 di apertura**, non contamina niente, ed è il metodo di riferimento
fuori dalla finestra in cui esiste footiqo. Entrambi sono nel CSV.

**Le due domande collaterali hanno risposta netta.** ρ = −0.06 non è il valore
giusto per l'inversione dal solo 1X2 (il valore a bias nullo è ≈ −0.083, e col
solo bias costante il migliore della griglia è −0.20) — ma **diventa irrilevante
sotto una superficie di debias**: con M4 la curva è piatta a 0.0197-0.0198 su
tutta la griglia da −0.20 a +0.12. Il θ double-Poisson invece non aiuta:
migliora l'inversione grezza (minimo a θ ≈ 1.15) e peggiora dopo il debias.

**Le confutazioni che tengono.** Permutando la chiusura 1xBet il MAE di M5g
risale a 0.0212, cioè al livello dei metodi di sola apertura: il vantaggio viene
davvero dal dato nuovo. Leave-one-season-out (M5g 0.0173, M4 0.0229, M1 0.0266) e
leave-one-league-out (0.0149 / 0.0216 / 0.0267) restano conclusivi. Cambiando il
devig (Shin) la graduatoria non si muove. E sullo **strato dei 100 vicini più
prossimi di ciascuna delle 9** (n = 668, le partite che il metodo deve davvero
stimare) il campione in carica **peggiora** a 0.0302 mentre M5g resta a 0.0151:
il vantaggio è più grande, non minore, proprio dove serve.

### 5.1 · La scoperta collaterale: il lato Over di quelle righe è integro

L'overround della linea O/U Betbrain 2017-19 è quasi costante (media 1.0558, sd
entro cella lega-stagione 0.0050). Leggendo **un solo lato** e imputando
l'overround della cella si ricostruisce la probabilità vera con **MAE 0.00157**
su 3.643 righe integre — un ordine di grandezza sotto qualunque stima.

Applicato alle 8 righe corrotte che hanno entrambi i lati: il lato **Over** cade,
per tutte e 8, entro il percentile 81 della distribuzione di disaccordo misurata
su righe integre; il lato **Under** cade oltre il percentile 100 per tutte e 8. E
il meccanismo è identificato: la quota finita nella colonna Under 2.5 è quella
dell'**Under 3.5** (MAE 0.0371 contro la chiusura 1xBet U3.5, contro 0.2474 per
U2.5, 0.4241 per U1.5, 0.1494 per U4.5). **Slittamento di linea sul solo lato
Under.**

**Questo non è nuovo, ed è giusto dirlo.** La stessa diagnosi — Over coerente,
Under no — è già scritta in [`REGOLE.md`](REGOLE.md) R6 Passo 2 e nel `motivo`
di tutte e 16 le righe di `correzioni_dichiarate.csv`. Nuove sono la
**quantificazione** della lettura di un lato e l'**identificazione della linea**
(U3.5), ottenute qui per due vie indipendenti (dalla scaletta 1xBet e — nella
verifica — dalla matrice DC invertita dal solo 1X2, che dà MAE 0.0399 contro
U3.5 e 0.1989 contro U2.5).

**Non è stato applicato.** La regola R6 approvata dall'utente dice che il mercato
si scarta **in blocco**, mai un lato solo. Se l'utente cambiasse quella regola, 8
righe su 9 passerebbero da stima (0.0143) a quasi-dato — ma con l'errore
**stratificato**, cioè ~0.002-0.004 per quelle righe e non lo 0.0016 medio
(l'errore di lettura cresce con p_over: 0.00197 nella loro fascia, 0.00364 per
y ≥ 0.66). La nona riga (bundesliga 2018-19, Bayern-Hoffenheim, senza alcun
lato) resterebbe stimata comunque.

### 5.2 · Che cosa ha corretto la verifica

Il lavoro è stato riprodotto a freddo (26 varianti × 4 metriche identiche a
1e-12, tutti gli 8 CI identici), re-implementato per una via indipendente (M4
0.01974 contro 0.01974, M5g 0.01430 contro 0.01434, con una CV e un solutore
diversi), rifatto con un bootstrap **a cluster** di lega-stagione (M5g − M1
[−0.01429, −0.01075]: ancora lontano da zero) e replicato su ciascuna delle due
leghe che hanno davvero i buchi. Il nucleo regge. Sono cadute tre affermazioni
di contorno, corrette qui sopra:

- **il fattore non è «2,6×» ma 1,87×** (0.0267 → 0.0143). Il numero d'effetto
  onesto è −0.0124 di MAE, cioè il **46% dell'errore in meno**, e 4,1× sulle 8
  righe reali (0.0429 → 0.0105);
- la «scoperta collaterale» **aveva un precedente** in R6, ora citato;
- l'errore atteso va **stratificato**: 0.0151 (non 0.0143) per le 9 righe, che
  hanno totale atteso alto e overround 1xBet al 66° percentile medio ma **6 su 9
  sopra l'88°** — e l'errore di M5g cresce col margine del book (0.0115 nel
  quintile basso contro 0.0150-0.0167 nei tre alti).

Restano aperti due controlli dichiarati non fatti: la griglia di ρ col solo bias
costante ha l'ottimo **al bordo** (−0.20) e non è identificata, e θ non è mai
stato provato *sotto* la superficie M4 — quindi il suo verdetto vale solo per il
debias povero.

→ `data/estimates/ou_open_corrotte_2017_19.csv` (9 righe, probabilità, con
entrambe le colonne M5g e M4)

---

## 6 · Il tiro in porta ricostruito da Understat: la regola misurata, la cella non riempita

Union Berlin - Bochum del 14/12/2024 è la sola riga di tutti i 16.111 record con
il **blocco statistico interamente vuoto**: football-data riporta il risultato
del tribunale (0-2) e lascia vuote 12 colonne su 12 (tiri, tiri in porta, corner,
falli, cartellini). Lo snapshot tiene l'1-1 del campo (regola R1), e Understat è
l'unico record del campo: lista completa, minuti 0-90, 22 tiri Union / 13 Bochum.

La domanda vera non è «quanto vale la cella» ma «**con che errore si può
ricostruire il tiro-in-porta di football-data dai tiri di Understat?**», visto
che le due fonti usano definizioni diverse. Campione casuale stratificato di 20
partite per ciascuna delle 45 celle lega × stagione (900 partite, 1.800
squadra-partita), dato tiro-per-tiro, 8 regole candidate più una a pesi stimati.

| regola | esatte | entro ±1 | MAE | bias |
|---|--:|--:|--:|--:|
| **R1 = Goal + SavedShot** | **0.864** | **0.977** | **0.171** | −0.139 |
| R3 = R1 + autogol avversari | — | — | +0.0283 peggio, CI [−0.0383, −0.0189] appaiato | — |
| R4 = R3 + pali | 0.684 | — | +0.1783 peggio | — |
| R5 = R1 + tiri bloccati | 0.084 | — | +2.99 peggio | — |
| pesi liberi NNLS, fuori campione (LOO-lega e LOO-stagione) | 0.861 | — | 0.174 | — |
| placebo (R1 sui tiri di un'altra partita) | 0.117 | — | 2.744 | — |
| baseline «moda» / «media di lega-stagione» | 0.224 / 0.169 | — | 2.017 | — |

**R1 è un tetto, non una scelta fortunata:** la regressione a pesi non negativi
su *tutte* le categorie — la famiglia lineare più larga che contiene tutte le
candidate — converge sui pesi di R1 (1.018 su Goal, 0.994 su SavedShot, ~0 su
tutto il resto) e fuori campione fa **peggio** (0.861 contro 0.864). Il
censimento di **tutte** le 305 partite di bundesliga 2024-25 — la cella dove vive
la partita bersaglio — replica: 0.857 [0.830, 0.885].

### 6.1 · Due fatti collaterali che valgono più della cella

**(a) La nota del progetto sugli autogol non è una regola.** La docstring di
`audit_anomalie.check_xg` afferma che football-data conta l'autogol come tiro in
porta di chi ne beneficia. Isolando il sottogruppo con autogol avversario, R1 è
esatta nell'**80%** dei casi e R3 (che aggiunge l'autogol) solo nel **15%**. Il
caso singolo da cui la nota nasce (Bielefeld-Leverkusen 21/11/2020) è vero e
verificato, ma non si generalizza: la nota va riscritta come «capita in circa un
caso su sei», non «è la regola». La verifica ha ricontrollato la stessa nota
anche sui **tiri totali** — che è ciò che il codice legge davvero — e trova un
differenziale di ~0,10 tiri: approssimativa su entrambe le letture.

**(b) Il cambio di raccolta di football-data, circoscritto e misurato.** R1
crolla in 3 celle su 45: Serie A 2018-19, 2019-20 e 2020-21 (esatte 0.375 / 0.325
/ 0.500, bias −0.83 / −0.88 / −0.70). Il perché si legge sui tiri **totali**: lo
scarto Understat − football-data vale +3.40 / +3.65 / +1.05 lì e sta entro 0.2 in
39 celle su 45 — ed è esattamente quanto valgono i tiri **bloccati** di Understat
in quelle stagioni (3.48 / 3.40 / 3.00). Nel 2018-21 il fornitore Serie A di
football-data non contava i respinti fra i tiri e ne contava una parte fra quelli
in porta. Confermato per una via che non tocca Understat: la quota di tiri in
porta (HST+AST)/(HS+AS) in Serie A fa 0.342 → **0.513 / 0.540 / 0.484** → 0.343,
mentre nelle altre quattro leghe resta fra 0.32 e 0.38 in tutte e nove le
stagioni. Un fornitore che dichiara che il 54% dei tiri finisce in porta non sta
misurando la stessa cosa.

Questo **precisa** e in parte corregge quanto scritto al §8 («i conteggi di
football-data non sono confrontabili fra stagioni»): l'anomalia è massiccia solo
lì, ma **non è del tutto circoscritta**. La verifica ha mostrato che le celle
anomale della **Bundesliga** (2020-21 esatte 0.625, 2022-23 0.700) non sono
«dentro l'errore di campionamento» come si era scritto: contro il tasso medio
delle celle pulite p_Bonferroni vale 2·10⁻⁴ e 0.02, tredici righe su 40 hanno
scarto esattamente −1 (spostamento sistematico, non rumore sparso), e la quota di
tiri in porta di football-data in quelle celle è sopra la mediana di lega. Esiste
quindi una **deriva di fornitore più lieve anche altrove, Bundesliga inclusa**.

### 6.2 · Perché la cella non è stata riempita

La stima aritmetica è `home_sot = 4`, `away_sot = 3`, e la verifica l'ha
ricontrollata riscaricando la partita dal vivo. Ma l'affidabilità da dichiarare
**non è il 75,1%** che si era scritto (la media su tutte le righe del
censimento): la riga bersaglio ha **22 tiri sul lato casa**, cioè cade nel
secchio in cui R1 degrada (0.779 contro 0.926 nella fascia 0-7 tiri). L'attesa
condizionata per *questa* riga è **0,69-0,72**, cioè al limite o **sotto** la
soglia del 70% che lo script stesso si era dato.

Le due strade oneste sono: non riempire e tenere il lavoro per il metodo e per i
due fatti collaterali; oppure riempire **solo** in `data/estimates/`, mai nella
colonna `home_sot`/`away_sot` dello snapshot — che la verifica ha dimostrato
essere una copia fedele di football-data su 16.111 righe su 16.111, e infilarci
una stima romperebbe proprio quella proprietà. La proposta è la seconda, con
l'errore condizionato al volume.

**Rilevanza pratica: bassa, e va detto.** `home_sot`/`away_sot` alimentano solo
il `blend_signal = 'sot'`, superato dal blend su xG che è la configurazione
ufficiale. Riempire questa cella non muove nessun backtest.

→ `scripts/stima_sot_understat.py`,
`docs/audit_5_leghe/numeri/stima_sot_understat.json`

---

## 7 · Le celle residue, e il buco che non è un `NaN`

Quattro casi, presi uno per uno, ognuno con la domanda «si può chiudere con un
dato vero? se no, la stima è abbastanza buona?».

### 7.1 · Le 6 celle di 1X2 di chiusura: sì al dato vero, ma con la riserva giusta

La fonte esterna delle celle-quota singole (§8) è **davvero una chiusura**, e la
prova nuova è decisiva: il suo «movimento» rispetto alla media prematch **correla 0.959 /
0.901 / 0.957** (H/D/A) col movimento vero di Pinnacle sulla stessa partita —
praticamente identico al riferimento fra due provider veri nel 2019-26 (0.964 /
0.903 / 0.961) — mentre il **pavimento** (due fotografie simultanee
dell'apertura) sta a −0.05 / −0.18 / −0.05. Una seconda apertura, o una
ricostruzione da modello, non riproducono il movimento idiosincratico del mercato
con r = 0.96; e infatti una ricostruzione da modello, misurata, dà 0.026 / 0.038
/ 0.034.

Che sia una **media** e non un book singolo lo dice la granularità: sulle quote
≥ 8 solo lo 0,6% finisce per `.00` (B365 87,7%, Pinnacle 11,3%, media Betbrain
1,3%) e l'ultima cifra è uniforme. **Onestà:** il margine 1.0526 è più *alto*
della media prematch 1.0489, mentre la media di chiusura etichettata di
football-data è più *bassa* della sua apertura — il paniere di book non è quello
di Betbrain, quindi «media di mercato» resta un'inferenza sulla forma dei prezzi,
non una dichiarazione del produttore.

Simulando il buco sulle 3.650 righe dove la chiusura esiste davvero, il dato
esterno sbaglia **0.00597** contro **0.01695** della migliore stima (Δ −0.01098,
CI [−0.01138, −0.01058]): 2,84 volte più preciso.

**Ma quel «2,84×» non vale sulle celle a cui è stato attaccato,** e la verifica
lo ha dimostrato. Il vantaggio del dato esterno crolla in modo monotono con la
forza del favorito:

| p_max dell'apertura | rapporto MAE stima / MAE fonte |
|---|--:|
| [0, 0.5) | 3.33 |
| [0.5, 0.7) | 2.83 |
| [0.7, 0.8) | 2.12 |
| [0.8, 0.88) | 1.46 |
| **[0.88, 1.01)** | **1.01** |

**Bayern-Hannover ha p_max = 0.924.** Nello strato p_max ≥ 0.88 (n = 32) il Δ
fonte − stima è −0.00010, CI [−0.00271, +0.00242]: **non conclusivo**. Nelle 11
partite con p_max ≥ 0.90 il dato esterno è in media *peggiore* del semplice
copiare l'apertura (0.01080 contro 0.00965), e lo è in 7 casi su 11. Il verdetto
onesto per quelle 3 celle è: **si usa il dato reale perché è un prezzo di mercato
osservato e non un'estrapolazione, non perché sia misurabilmente più accurato su
questa riga**; l'errore atteso da dichiarare è ~0.008-0.011, non 0.00597. Le 3
celle di **Alaves-Sociedad** invece reggono e anzi migliorano (strato p_max in
[0.40, 0.50): 0.00540 contro 0.01726, cioè 3,2×).

Cade anche la «conferma reciproca» che era stata usata a sostegno: il percentile
dell'accordo (1,0% per Bayern-Hannover) era calcolato sulla distribuzione
**incondizionata** del movimento, dominata da partite equilibrate. Rifatto sulla
coppia di provider corretta e condizionando a p_max ≥ 0.88, l'accordo entro
0.00122 capita nel **15,4%** delle partite confrontabili: circa 1 su 6,5, non 1
su 100.

### 7.2 · L'xG di Holstein Kiel-Bochum: `NaN`, e la prova che è giusto

Regressione xG ~ tiri in porta + gol + forza su 32.216 squadra-partita:

| modello | MAE | R² |
|---|--:|--:|
| regressione k-fold | **0.4525** | 0.570 |
| leave-one-league-out | 0.4643 | 0.560 |
| gradient boosting (tetto) | 0.4522 | — |
| baseline `k` × tiri, k ottimo 0.3040 | 0.5188 | 0.426 |
| baseline media di lega e campo | 0.6864 | 0.038 |
| baseline xG = gol | 0.7582 | −0.189 |

Con una sd dell'xG di 0.89, l'errore è metà del segnale, e il **35,6%** delle
stime sbaglia di oltre mezzo gol. Il gradient boosting non batte la retta
(Δ −0.00028, CI [−0.00128, +0.00074]): **il limite è informativo, non del
modello** — i tiri in porta di football-data non contengono la posizione del
tiro, che è l'intera sostanza dell'xG. La verifica ha rafforzato questa
conclusione dimostrandola meglio: aggiungendo la forza xG stagionale
(leave-one-out di squadra e di avversario) la retta migliora in modo conclusivo
(0.4525 → **0.4466**, CI [−0.00694, −0.00495]) e resta comunque **ben sopra la
soglia dichiarata di 0,4**. L'errore condizionato al profilo esatto delle celle
bersaglio è 0.446 e 0.514: sopra soglia su entrambi i lati. **Resta `NaN`.**

Per npxG, PPDA e `deep` non si è nemmeno provato: nello schema interno non esiste
alcun proxy del pressing o della posizione dei passaggi. Sono 12 celle che
restano `NaN` **per assenza di informazione**, non per scelta metodologica.

### 7.3 · L'xG di Nantes-Toulouse: non «non stimabile», ma «non serve stimare»

La partita (ligue_1, 17/05/2026) non è stata consolidata dalla fonte:
`isResult = false`, xG `null`, e `getMatchData/29840` risponde **404** mentre gli
altri 8 id della stessa giornata rispondono 200 con 12-27 tiri; le history di
Nantes e Toulouse hanno 33 partite su 34. Il buco è della fonte, non del parser —
e le altre 8 partite dell'ultima giornata sono già corrette nello snapshot (0
discrepanze).

Qui la verifica ha corretto il deliverable: il CSV portava il verdetto «NON
STIMABILE (MAE 0,45)», ma per il profilo di *questa* partita (0-0, 1 tiro in
porta per parte) l'errore condizionato è **0.2785**, cioè **sotto** la soglia. La
formulazione giusta è **«non serve stimare: la fonte si consoliderà»**, con
ri-download periodico a costo zero — non «non si può».

### 7.4 · Il buco più grande rimasto non è un `NaN`

Il censimento delle celle vuote non è cambiato (7.353 `NaN` su 612.218, 1,20%; di
cui 7.304 = 99,3% è il buco sistemico O/U chiusura 2017-19; 49 celle sparse,
identiche al censimento precedente; **0 celle nuove**, 0 nuovi segnaposto xG). Ma
il buco maggiore rimasto è invisibile a quel conteggio:

| lega | celle `midweek_europe` che valgono 0 e non dovrebbero | partite con riposo sbagliato |
|---|--:|--:|
| serie_a | 236 | |
| premier_league | 251 | |
| la_liga | 454 | |
| bundesliga | 180 | |
| ligue_1 | 482 | |
| **totale** | **1.603** | **1.700** |

**Non è una stima: è dato di calendario**, chiudibile con i 3.045 fixture di
coppa già su disco (§4), errore atteso zero. La verifica lo ha riprodotto cella
per cella e ha aggiunto tre controlli che mancavano: 0 inversioni 1 → 0, 0 nomi
squadra orfani, 0 collisioni fra date di coppa recuperate e date di campionato
della stessa squadra, 0 duplicati, 3.045 righe esatte. È la parte più solida di
questo blocco. Resta il caveat del §4: chiude un buco di **correttezza del dato**,
non di previsione — e il report 10 §12 ha ora misurato che, col dato corretto, la
covariata resta rumore.

Una segnalazione nuova, **da verificare e non da eseguire**: bundesliga
Dortmund-Hannover 26/01/2019 ha overround 1.0947 sulla O/U di apertura (|z
robusto| = 10.3), ma la coppia `BbMx` corrispondente (1.40 / 3.10) ha overround
1.037, perfettamente normale, e la riga dichiara 36 book. Media larga ≠ cella
corrotta: le 8 righe gemelle già svuotate arrivavano a 1.339, cioè
aritmeticamente impossibili. Svuotarla svuoterebbe plausibilmente una cella vera.

→ `data/estimates/celle_residue.csv`,
`docs/audit_5_leghe/numeri/stima_celle_residue.json`

---

## 8 · Il resto, in breve

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

**Un difetto nuovo di football-data — ora quantificato.** Riconciliando i tiri
con Understat emerge che i conteggi di football-data **non sono confrontabili fra
stagioni**: in Serie A la somma dei tiri passa da 5.359 (2017-18) a 4.269
(2018-19) e torna a 5.326 (2021-22), con tutte le 380 righe popolate. Non è un
buco: è un cambio di raccolta a monte. Il §6.1 lo circoscrive (Serie A 2018-21,
dove i respinti non venivano contati fra i tiri e in parte finivano fra quelli in
porta) e mostra che una deriva **più lieve esiste anche altrove**, Bundesliga
inclusa. Poco rilevante oggi (il blend ufficiale usa l'xG), ma va scritto.

---

## 9 · Le proposte, nessuna applicata

| # | cosa | dove | perché serve una decisione |
|---|---|---|---|
| 1 | 1X2 di chiusura per **Alaves-Sociedad** (3 celle) | snapshot | il provider è diverso dal resto della colonna; qui il vantaggio sulla stima è 3,2× e regge |
| 1-bis | 1X2 di chiusura per **Bayern-Hannover** (3 celle) | snapshot | **motivazione da riscrivere**: su quel profilo (favorito a 0.92) il dato esterno non è misurabilmente più preciso della stima (§7.1). Si usa perché è un prezzo osservato, con errore atteso ~0.008-0.011 |
| 2 | 8 correzioni di **data** nei calendari di club | `club_fixtures_bundesliga.csv` | openfootball sbaglia di un giorno, due fonti concordi |
| 3 | integrare le **3.045 righe di coppa** e chiudere i **1.603 falsi zero** di `midweek_europe` | `club_fixtures_*.csv` (5 leghe) | dato di calendario, errore atteso zero, 5 controlli superati (§7.4). È la proposta più solida del lotto |
| 4 | guard sull'**overround alto** + le **4 righe La Liga** | `src/`, `data/` | tocca la produzione (tranche 2). Da NON estendere a Dortmund-Hannover senza verifica (§7.4) |
| 5 | usare o no il **dato 1xBet** per la colonna O/U di chiusura | — | non migliora la stima e romperebbe il regime della colonna: la raccomandazione resta **no** |
| 6 | pubblicare la **stima O/U delle 2 leghe nuove** | `data/estimates/` | tranche 2 |
| 7 | ~~passare lo stimatore da pooled a per-lega~~ → **rigenerare le 1.362 stime col pooled** e alzare il MAE dichiarato del 15-25% | `scripts/build_estimates.py`, CSV | il ribaltamento non regge nel regime d'uso (§3) |
| 8 | pubblicare la **stima delle 9 righe O/U di apertura v2** (M5g 0.0143, o M4 0.0197 senza contaminazione) | `data/estimates/` | sostituisce una stima peggiore già pubblicata (§5) |
| 9 | leggere il **solo lato Over** delle 8 righe corrotte | `REGOLE.md` R6 | contraddice una regola approvata dall'utente: decisione sua (§5.1) |
| 10 | riempire o no il **tiro in porta** di Union-Bochum | `data/estimates/` | affidabilità condizionata 0,69-0,72, al limite della soglia che lo script stesso si dà (§6.2) |
| 11 | riscrivere la **nota sugli autogol** in `audit_anomalie.check_xg` | `scripts/` | «capita in un caso su sei», non «è la regola» (§6.1) |

---

## 10 · Cosa NON si è chiuso, e perché

- **la chiusura O/U 2017-19 come media multi-book** non esiste da nessuna parte:
  quello che esiste è un singolo book, ed è meno utile della stima;
- **l'O/U di apertura per-partita del 2017-19** non è recuperabile da nessuna
  fonte lecita (BetExplorer ri-verificato su una lega-stagione nuova: stesso
  ritiro; OddsPortal vietato dal `robots.txt`). Le 9 righe corrotte restano
  **stimate** — ma con MAE 0.0143 invece di 0.0267 (§5);
- **l'xG di Holstein Kiel-Bochum** (e npxG/PPDA/`deep` di entrambe le partite)
  resta `NaN`: un xG dedotto dai tiri sarebbe un numero inventato con la faccia
  di una misura, e ora c'è la misura che lo dimostra (§7.2);
- **l'xG di Nantes-Toulouse** resta `NaN` per una ragione diversa: la fonte non
  ha ancora consolidato la partita. Da ri-scaricare, non da stimare (§7.3);
- **il tiro in porta di Union-Bochum** resta vuoto in attesa di decisione: la
  regola di ricostruzione è misurata, ma su *quella* riga l'affidabilità attesa
  è al limite della soglia (§6.2);
- **le griglie di ρ e θ del bakeoff** non sono chiuse: l'ottimo di ρ col solo
  bias costante è al bordo (−0.20) e θ non è mai stato provato sotto la
  superficie di debias (§5.2).
