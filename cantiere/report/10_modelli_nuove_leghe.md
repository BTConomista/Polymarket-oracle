# Report 10 — La rosa dei modelli messa alla prova su Bundesliga e Ligue 1

Richiesta: *«valutare quanti più modelli, piste o cose possibili per queste due
leghe appena aggiunte»*.

**Dieci fronti**, tutti con parametri scelti **fuori campione** e bootstrap
appaiato B = 10.000. Il quadro in una riga: **nessuna leva del mercato si replica
sulle due leghe nuove**, il motore invece sì (funziona identico anche partendo
dalle quote di apertura), e diverse lezioni che il progetto dava per acquisite
risultano più fragili di quanto scritto — comprese due di questo stesso report,
smontate dalla verifica avversariale.

Questo report è il seguito di [`06_tranche3.md`](06_tranche3.md) e in un punto lo
corregge (§2.2). Il mercato GG/NG, che qui compare solo come calibrazione, ha un
report suo perché tocca una premessa del progetto:
[`11_ggng.md`](11_ggng.md).

---

## 1 · Il quadro

**Primo giro — le leve del mercato sulle quote di chiusura**

| fronte | Bundesliga | Ligue 1 | mercati con CI conclusivo |
|---|---|---|--:|
| router double-Poisson θ (griglia) | ❌ negativo | ❌ negativo | **0 / 25** (e 2 e 4 *peggiorati*) |
| φ(\|λ−μ\|) (griglia 341 punti) | nel rumore | nel rumore | 0 (e 1 e 3 *peggiorati*) |
| devig di Shin | nel rumore | nel rumore | pooled: 1 (Brier), che non regge a cluster |
| ricalibrazione per-classe del mercato | nel rumore | nel rumore | 0 |
| power-devig | ❌ **peggiora** (CI conclusivo) | nel rumore | — |
| ricalibrazione dei tassi sul GG/NG | ~~🪑 +0.00059~~ → **non confermata** | nel rumore | 0 dopo verifica |

**Secondo giro — i fronti nuovi**

| fronte | esito in una riga | §|
|---|---|--:|
| **beat-the-close** (`sharpen_1x2`) | ❌ **chiusa**: peggiora la chiusura, in Bundesliga con CI conclusivo | §7 |
| **motore dall'apertura** | ⚽ **funziona**: 25/25 mercati contro il DC; sui totali la chiusura resta migliore | §8 |
| **mercato campione di stagione** | ❌ funziona ma non aggiunge nulla a «vince il Bayern» / «vince il PSG» | §9 |
| **fronte generale (pooled vs per-lega)** | **non deciso**: la statistica che lo sosteneva non distingue il vero dal placebo | §10 |
| **audit di calibrazione** | prezzi calibrati **quanto il book**, ma il difetto di forma esiste ed era stato dichiarato assente | §11 |
| **leve di panchina del DC + covariate** | ❌ 6 covariate su 6 bocciate; un solo candidato vivo (ensemble di emivite), non dimostrato | §12 |

Con ~2.100-2.300 partite per lega la soglia di risoluzione del bootstrap è
**1-2 millesimi di log-loss**: sotto quella soglia «non dimostrato» non significa
«dimostrato nullo». È il limite strutturale di tutto ciò che segue, e va tenuto
presente prima di leggere qualunque riga come una chiusura definitiva.

---

## 2 · Il router θ: negativo — e due lezioni da riscrivere

### 2.1 · Il risultato

Griglia θ ∈ {1.000 … 1.400}, passo 0.025, applicata via `price_markets(dp_theta)`
a **tutti i 25 mercati** del listino, 5 leghe × 7 stagioni, selezione
leave-one-season-out e leave-future-out.

**Controllo di sanità superato in modo totale:** riprodotte tutte e **18** le
quantità pubblicate dal progetto (3 leghe × 6 mercati) con discrepanza massima
**4.9 × 10⁻¹⁰**, incluse le sequenze di θ scelte anno per anno. La verifica
esterna ha rifatto lo stesso controllo con la piena precisione di
`experiments/runs.jsonl` e ha ottenuto **2.98 × 10⁻¹⁷**: meglio ancora.
L'apparato, quando la leva c'è, la trova.

Sulle due leghe nuove: **0 mercati su 25** con CI95 sotto zero, in entrambe;
2 (Bundesliga) e 4 (Ligue 1) mercati **conclusivamente peggiorati**. L'unico
residuo nominale — i totali in Bundesliga (over 1.5 −0.0013, over 2.5 −0.0008) —
non sopravvive a Bonferroni ed è rovesciato dal selettore in Ligue 1 (over 1.5
**+0.0008**, CI [+0.0002, +0.0015]).

**Perché resta bocciato, ma con il motivo corretto.** La verifica ha rifatto il
test a **θ fisso**, senza alcuna selezione. Lì l'effetto in Bundesliga esiste
(over 2.5 −0.00076, CI [−0.00135, −0.00016] a θ = 1.10; resta sotto zero anche
con la costante di produzione 1.225) ma vale p = 0.011 contro una soglia di
Bonferroni su 25 mercati di 0.002. E il «rovesciamento» della Ligue 1 sparisce a
θ fisso (over 1.5 +0.00009, p = 0.86): era una proprietà del selettore, non del
mercato. Il verdetto corretto non è «mancanza di effetto» ma **«effetto sotto la
soglia, e un selettore su griglia di 17 punti che non sa prenderlo»**.

La profondità della valle in-sample sul risultato esatto:

| lega | θ MLE | profondità valle | il router paga? |
|---|--:|--:|:-:|
| serie_a | 1.232 | **−0.0081** | sì |
| la_liga | 1.242 | **−0.0081** | sì |
| premier_league | 1.085 | −0.0012 | no |
| **bundesliga** | **1.080** | **−0.0012** | **no** |
| **ligue_1** | **1.103** | **−0.0017** | **no** |

Le leghe si dividono in due famiglie nette: «latine» θ ≈ 1.24, dove la
sotto-dispersione è forte e sfruttabile, e le altre θ ≈ 1.08-1.10, dove non lo è.
**Bundesliga e Ligue 1 stanno con la Premier.**

### 2.2 · Due lezioni del progetto: una corretta, una che era sbagliata a sua volta

**(a) «griglia > MLE» non è una proprietà dello stimatore — è una tautologia.**
Sul risultato esatto la griglia ricade sul θ di massima verosimiglianza **entro
mezzo passo in 5 leghe su 5** (SA 1.225 vs 1.232; Liga 1.250 vs 1.242;
Bundesliga 1.075 vs 1.080; Ligue 1 1.100 vs 1.103; Premier 1.075 vs 1.085). La
verifica ha chiuso la questione mostrando che `price_markets` e `dp_matrices`
danno lo **stesso identico oggetto** (max diff 0.0 su 300 matrici) e che
`fit_theta` minimizza *esattamente* quel log-loss: non c'è nulla da confrontare.
Griglia e MLE divergono solo quando si cambia **metrica** — la frase giusta non è
«la griglia stima meglio», ma «mercati diversi vogliono θ diversi».

**(b) «Il ribaltamento sulla Liga era la finestra dati, non lo stimatore» — è
FALSO, e va ritirato.** Era la nostra correzione a un numero del progetto
(θ = 1.097 per la Liga), e la verifica l'ha ricostruito da zero: quel numero è la
**media di 8 fit MLE a finestra espandente**, non un fit unico. Riprodotto:
**1.103** per la Liga e **1.075** per la Premier (pubblicato 1.069). Il pooled
sulla stessa finestra a 9 stagioni dà **1.199**.

| stimatore | finestra | θ Liga |
|---|---|--:|
| media di fit espandenti (quello della fonte originale) | 9 stagioni | **1.103** |
| pooled | 9 stagioni | **1.199** |
| pooled | 7 stagioni (questo report) | **1.242** |
| pooled sul solo 2017-19, con chiusura vera 1xBet | 2 stagioni | 1.062 |

Cioè: **due terzi del divario sono l'aggregazione dello stimatore, un terzo la
finestra.** Il 2017-19 è davvero un'epoca a θ basso (1.062 anche con la chiusura
reale), ma non arriva mai a 1.097 da sola. La formulazione onesta è: *i due
numeri differiscono per entrambe le ragioni, e la parte maggiore è come si
aggregano i fit.*

**(c) Un corollario contro-intuitivo, invariato:** applicare a tutto il listino
il θ alto scelto sull'1X2 produce **meno** mercati conclusivi che usare il θ MLE
(Serie A 4/25 contro 10/25; Liga 2/25 contro 6/25). Come costante unica per
l'intero listino, il θ da massima verosimiglianza resta il migliore.

---

## 3 · φ(|λ−μ|): nel rumore, e la confutazione non è forte come sembrava

Griglia bidimensionale di **341 punti** (φ₀ 0→1 × κ 0→4), selezione
leave-one-season-out, 11 mercati per lega.

| lega | mercato | senza φ | con φ | Δ | CI95 | verdetto |
|---|---|--:|--:|--:|---|---|
| bundesliga | 1X2 | 0.9744 | 0.9738 | +0.00064 | [−0.0014, +0.0027] | nel rumore |
| bundesliga | pareggio | 0.5519 | 0.5512 | +0.00064 | [−0.0014, +0.0027] | nel rumore |
| bundesliga | **doppia 1X** | 0.5488 | 0.5496 | **−0.00076** | [−0.0013, −0.0003] | **peggiora** |
| bundesliga | GG/NG | 0.6654 | 0.6646 | +0.00086 | [−0.0011, +0.0028] | nel rumore |
| ligue_1 | 1X2 | 0.9850 | 0.9851 | −0.00016 | [−0.0005, +0.0002] | nel rumore |
| ligue_1 | **over 2.5** | 0.6714 | 0.6718 | **−0.00039** | [−0.0007, −0.0000] | **peggiora** |
| ligue_1 | **over 1.5 / multigol** | — | — | −0.0002 | CI < 0 | **peggiora** |

In Ligue 1 la selezione sceglie φ₀ = 0 in ogni stagione: la lega **non ha
deficit di pareggi**, come previsto dall'EDA prima di misurare. Previsione
dichiarata in anticipo e confermata.

**La confutazione che era stata scritta come decisiva, ridimensionata.** Si era
detto: rifatta la selezione sulla sotto-griglia κ = 0 — cioè un'inflazione-pareggio
*costante* — la φ costante fa «meglio o uguale» della φ35, quindi la parte
intelligente della leva non si ripaga. La verifica ha mostrato che quel confronto
**non ha alcun intervallo di confidenza**, e che gli effetti in gioco stanno fra
7 × 10⁻⁶ e 4 × 10⁻⁴, cioè **da 5 a 100 volte sotto la soglia di risoluzione
dichiarata da questo stesso report**. Di più: su `dc_2x` in entrambe le leghe e
sul GG/NG in Bundesliga è la **φ35 a vincere**, quindi il segno non è nemmeno
uniforme.

Formulazione corretta: **φ35 e φ costante sono indistinguibili fra loro e dallo
zero.** La bocciatura della φ35 sulle due leghe nuove resta (nel rumore, peggiora
la doppia 1X), ma non si può promuovere la φ costante a rivale vincente — e in
effetti il §12 la misura direttamente sul path DC, dove non paga in nessuna delle
due leghe.

---

## 4 · Il devig di Shin: la quarta e quinta replica

Il progetto misurava Shin ≥ moltiplicativo su 3/3 leghe senza mai concludere.
Con 5 leghe e 12.459 partite:

| confronto (pooled 5 leghe) | Δ | CI95 | verdetto |
|---|--:|---|---|
| Shin vs moltiplicativo, **log-loss 1X2** | −0.00034 | [−0.00068, +0.0000] | nel rumore (p = 0.052) |
| Shin vs moltiplicativo, **Brier 1X2** | −0.00021 | [−0.00039, −0.00001] | conclusivo (meglio) |
| power-devig vs moltiplicativo | −0.00042 | [−0.0011, +0.0002] | nel rumore |
| Shin vs power-devig | +0.00009 | [−0.0004, +0.0006] | nel rumore |

**La verifica ha riprodotto i numeri e poi ha tolto la conclusività.** Il
bootstrap per riga tratta 12.459 partite come indipendenti; rifatto **a cluster
di lega**, il CI sul Brier diventa [−0.000414, −0.0000008], cioè **tocca lo
zero**. E il dettaglio per lega mostra che migliorano solo 3 su 5:

| lega | Δ Brier |
|---|--:|
| serie_a | −0.00038 |
| la_liga | −0.00054 |
| ligue_1 | −0.00009 |
| premier_league | +0.00002 |
| bundesliga | +0.00003 |

Sulla finestra a 9 stagioni delle due leghe nuove (che include il 2017-19, dove
il book è Pinnacle e il margine è la metà): **nel rumore in entrambe**, e il
parametro z di Shin passa da ~0.0128 nel 2017-19 a ~0.0245 dal 2019-20 —
coerente col fatto che il margine raddoppia.

Un dato indipendente dal §7 rafforza la lettura «per-lega, non generale»: nel
lavoro sul beat-the-close, Shin batte il moltiplicativo con **CI conclusivo in
La Liga su entrambi i protocolli** (−0.0008 LOSO, −0.0009 LFO) e in Serie A LFO
(−0.0008), mentre è nel rumore in Bundesliga, Ligue 1 e Premier. La partizione è
la stessa delle «latine».

**Lettura onesta:** Shin è *probabilmente* un filo meglio, e nelle leghe latine
lo è in modo conclusivo. Ma il pooled non regge a un bootstrap che rispetti la
struttura dei dati, e il log-loss — la metrica ufficiale — resta a p = 0.052. Non
basta per toccare la fonte unica delle metriche.

---

## 5 · Le ricalibrazioni del mercato

**A · per-classe (pesi w_D, w_A).** Nel rumore in entrambe le leghe
(Bundesliga +0.00078, Ligue 1 +0.00076: entrambe *peggiorano* di poco).

Qui c'era **un errore di tabella**, trovato dalla verifica: si era classificata
la Liga fra le leghe con w_D > 1 («latina»), ma il run stesso dà **0.978**.
Tabella corretta:

| lega | w_D fittato |
|---|--:|
| serie_a | > 1 |
| **la_liga** | **0.978** |
| **bundesliga** | **1.089** |
| premier_league | < 1 |
| **ligue_1** | **0.981** |

Con il numero giusto la tassonomia «latine / inglesi» **non esiste**: il segno è
sparso, e l'archiviazione originale del progetto («segno non universale») era
corretta. La spiegazione che era stata proposta qui va ritirata. Il §12 aggiunge
il colpo di grazia: portata sul path DC, la stessa leva peggiora — in Ligue 1 con
CI conclusivo — e il motivo misurato è che il bias per classe non è stabile
**nemmeno nel tempo dentro la stessa lega** (oscilla di ±0.03 stagione su
stagione, cioè quanto la sua stessa incertezza campionaria).

**B · tilt dei livelli.** Bundesliga c_λ = +0.019, c_μ = +0.022 (il mercato
sotto-stima i gol di ~2% su entrambi i lati); Ligue 1 c_λ = −0.010, c_μ = +0.022
(asimmetrico). Coerenti col tracer, nessun guadagno conclusivo a valle. Il §7 ne
dà l'interpretazione: quello che conta non è il livello ma la sua parte
**asimmetrica**, e nelle due leghe nuove è ≈ 0.

**C · power-devig.** In Bundesliga **peggiora con CI conclusivo** (+0.00035,
CI [+0.00004, +0.00066]) sia a 7 sia a 9 stagioni; in Ligue 1 nel rumore.
Pista chiusa anche fuori dalla Serie A.

---

## 6 · Il GG/NG in Bundesliga: il segnale che non si è confermato

Era l'unica cella conclusiva positiva del primo giro: **ricalibrazione dei tassi
(livello di μ) prima di derivare il GG/NG**, parametri leave-one-season-out.

| lega | senza | con | Δ | CI95 | verdetto originale |
|---|--:|--:|--:|---|---|
| bundesliga | 0.6654 | 0.6648 | **+0.00059** | [+0.00006, +0.00113] | conclusivo |
| ligue_1 | 0.6847 | 0.6845 | +0.00023 | [−0.00029, +0.00072] | nel rumore |

**Il numero è vero — e non significa niente.** La verifica lo ha riprodotto a 7
cifre con codice indipendente e lo ha trovato stabile su 60 semi di bootstrap
(l'accusa più ovvia, la fragilità del seme, non regge). Poi lo ha collocato:

- vive in un blocco di **300 celle** (5 leghe × mercati × varianti) che ne produce
  **7 conclusive positive** e 38 negative. Sette su 300 è **esattamente quanto ne
  produce il caso a α = 0.05**;
- **non replica**: la_liga dà −0.00026 con CI **conclusivamente negativo**;
  premier −0.00007 (p = 0.58); ligue_1 +0.00023 (p = 0.36);
- la variante **contigua** — ricalibrare λ *e* μ invece del solo μ — sugli stessi
  dati è «nel rumore» (+0.00078, CI [−0.00007, +0.00165]): un verdetto che si
  ribalta cambiando un dettaglio non è un verdetto;
- e il numero sta in `leve_phi_griglia.json`, non nello script a cui era stato
  attribuito.

**E adesso c'è il giudice esterno.** Il lavoro sulle quote GG/NG reali
([`11_ggng.md`](11_ggng.md)) ha misurato la stessa leva contro il prezzo di un
book, invece che contro la sola realtà: in Bundesliga dà **−0.00008, CI
[−0.00092, +0.00075]** su 917 partite, cioè nulla. Non è una smentita (finestra,
tassi e n sono diversi, e quel test è meno risolvente) ma è **una mancata
conferma**.

**Verdetto:** la cella passa da 🪑 panchina a ⬜ **non dimostrata**. Condizione
di promozione: replica prospettica su una lega non usata per scoprirla, o una
finestra con più di 2.000 partite di quel campionato.

---

## 7 · Beat-the-close su Bundesliga e Ligue 1: pista chiusa

`sharpen_1x2` (θ double-Poisson + ricalibrazione dei livelli dei tassi) è
l'unica cosa nel progetto che batta la chiusura devigata in log-loss, in Serie A.
Aspettativa dichiarata prima: negativa su entrambe le leghe nuove, perché la
leva poggia sulla sotto-dispersione e lì θ ≈ 1.08-1.10.

**Controllo di sanità superato,** e non era scontato: la cache su cui gira lo
script di produzione non esiste più, e nel frattempo la semantica dell'unica
linea O/U del 2018-19 è cambiata di colonna. Ricostruita la vista d'epoca e
verificata per identità contro lo snapshot in git (380/380 righe uguali), la
chiusura devigata si riproduce a **2.2 × 10⁻¹⁶** e i cinque θ MLE per lega
coincidono con i valori pubblicati.

**Test primario** (`dp_lvl` vs chiusura devigata, selettore leave-one-season-out;
Δ > 0 = la chiusura è migliore):

| lega | chiusura | dp_lvl | Δ | CI95 | n | stagioni migliorate | verdetto |
|---|--:|--:|--:|---|--:|:-:|---|
| **bundesliga** | 0.9739 | 0.9754 | **+0.0016** | [+0.0004, +0.0027] | 2.142 | 1/7 | **conclusivo CONTRO** |
| **ligue_1** | 0.9850 | 0.9853 | +0.0003 | [−0.0009, +0.0014] | 2.337 | 3/7 | nel rumore |
| serie_a *(controllo)* | 0.9625 | 0.9605 | −0.0020 | [−0.0036, −0.0003] | 2.660 | 7/7 | conclusivo a favore |
| premier *(controllo)* | 0.9639 | 0.9649 | +0.0010 | [−0.0001, +0.0022] | 2.660 | 3/7 | nel rumore |
| la_liga *(controllo)* | 0.9697 | 0.9687 | −0.0010 | [−0.0022, +0.0003] | 2.660 | 5/7 | nel rumore |

Col protocollo walk-forward (l'unico giocabile) **entrambe le leghe nuove
peggiorano con CI conclusivo**: Bundesliga +0.0026 [+0.0007, +0.0045], Ligue 1
+0.0020 [+0.0001, +0.0039]. Lo stesso vale contro il devig di Shin, e rifittando
tutto su Shin.

### 7.1 · Il perché, che è il risultato più utile

Scomponendo la correzione dei livelli in **tilt** (parte asimmetrica, bias-casa, a
scala invariata) e **scala** (parte simmetrica):

| lega | θ MLE | λ× / μ× | **tilt** | **scala** | dp solo | tilt solo | dp+tilt |
|---|--:|--:|--:|--:|--:|--:|--:|
| **serie_a** | **1.232** | 0.9727 / 1.0267 | **−0.0270** | −0.0006 | −0.0010 | +0.0002 | **−0.0020 ✓** |
| la_liga | 1.242 | 0.9981 / 0.9936 | +0.0023 | −0.0042 | −0.0012 | +0.0007 | −0.0010 |
| premier | 1.085 | 0.9764 / 1.0091 | −0.0164 | −0.0074 | +0.0002 | +0.0009 | +0.0009 |
| **ligue_1** | 1.103 | 0.9905 / 1.0217 | −0.0155 | +0.0060 | −0.0001 | +0.0004 | +0.0003 |
| **bundesliga** | 1.080 | 1.0193 / 1.0221 | **−0.0014** | **+0.0205** | +0.0003 | +0.0014 | +0.0012 |

L'affinamento della Serie A è **quasi puro tilt**: un bias-casa che sopravvive al
devig. In Bundesliga il tilt è essenzialmente **zero** e tutta la correzione è
scala — una riscalatura dei due tassi che non porta informazione sull'1X2 e
aggiunge solo rumore, da cui il peggioramento conclusivo. E l'effetto Serie A è
un'**interazione, non una somma**: da soli θ dà −0.0010 (non conclusivo) e il
tilt +0.0002 (nulla); insieme −0.0020 (conclusivo, 7/7).

Servono **entrambi** gli ingredienti, θ ≈ 1.23 *e* tilt ≈ −0.027. Le due leghe
nuove non hanno né l'uno né l'altro. L'ipotesi «la Ligue 1 ha il margine più
alto del campione (4,78%), quindi è la candidata» è **falsificata**.

### 7.2 · Il test che conta per l'utente: il ROI

Anatomia del perché non può funzionare — l'affinamento medio contro la soglia di
pareggio Δ\* = 1/quota − p_mercato:

| lega | margine book | \|Δp\| medio | soglia Δ\* | rapporto |
|---|--:|--:|--:|--:|
| bundesliga | 4,54% | 0.0068 | 0.0159 | **2,3×** |
| ligue_1 | 4,78% | 0.0070 | 0.0167 | **2,4×** |
| serie_a | 4,64% | 0.0117 | 0.0162 | 1,4× |

ROI a quote di chiusura reali, strategia EV > 0, protocollo walk-forward:

| lega | n scommesse | ROI | CI95 | puntare TUTTO (rif.) |
|---|--:|--:|---|--:|
| **bundesliga** | 427 | **−22,46%** | [−36,79%, −7,10%] | −4,66% |
| **ligue_1** | 581 | **−12,90%** | [−23,21%, −2,20%] | −5,74% |
| serie_a | 924 | +0,75% | [−6,86%, +8,61%] | −7,41% |
| premier | 969 | −8,11% | [−19,50%, +3,90%] | −5,36% |

**Il risultato più importante di tutto il blocco:** nelle due leghe nuove
seguire i «value bet» del modello perde **3-5 volte più in fretta** che
scommettere alla cieca, con CI conclusivo. E perfino in Serie A, dove il
vantaggio in log-loss è reale e conclusivo, il ROI è indistinguibile da zero. Un
affinamento di 2 millesimi di log-loss contro un margine del 4,5-4,8% **non è un
edge economico**.

### 7.3 · Quattro tentativi di far apparire la leva

Tutti falliti. (1) Costanti della Serie A copiate di peso — l'errore che
`CLAUDE.md` §7 vieta, qui misurato invece che ipotizzato: Bundesliga −0.0003,
Ligue 1 −0.0000, entrambe nel rumore. (2) **In-sample, barando apertamente** (θ e
livelli fittati e valutati sulle stesse 7 stagioni, cioè il tetto teorico della
leva): in Bundesliga dp_lvl resta **+0.0005**, cioè peggiore della chiusura anche
barando; in Ligue 1 −0.0003, nullo; il controllo Serie A in-sample dà −0.0022
conclusivo, quindi la procedura *sa* trovare l'effetto dove c'è. (3) Potenza: la
semiampiezza del CI è 0.0012 contro un effetto Serie A di −0.0016/−0.0020, e in
Bundesliga il CI **esclude** l'effetto Serie A — è il caso raro in cui si può
dire «dimostrato assente». (4) Tre semi di bootstrap: stesso Δ e stesso CI alla
quarta cifra.

**Una scoperta laterale, sulle leghe storiche:** `dp_tilt` (θ + solo tilt,
**senza** la scala) in Serie A dà −0.0020 su entrambi i protocolli, 7/7 e 6/6 —
cioè **eguaglia `dp_lvl` con un parametro in meno**, ed è l'unica variante
conclusiva anche in walk-forward. Candidata a sostituire i due livelli con un
solo tilt in `sharpen_1x2`; non promossa qui perché è una sola lega.

---

## 8 · Il motore market-implied dall'APERTURA: funziona, e dice una cosa nuova

Fin qui il motore è sempre stato misurato dalle quote di **chiusura**. Qui è
stato invertito dall'**apertura** (1X2 + O/U) su tutte e 9 le stagioni in cui
esiste — **5.842 partite**, +30% rispetto alla finestra-chiusura — e fatto
prezzare i 25 mercati Tier 1.

**Due controlli di sanità, ora incisi come asserzioni nello script:** il router
vettoriale coincide con `mi.price_markets` cella per cella (errore max
4 × 10⁻¹⁶), e la selezione delle righe riproduce il log-loss di mercato del
tracer (1X2 0.9738 / 0.9851, O/U 0.6459 / 0.6730). Il secondo, va detto, **non
valida il devig**: chiama la stessa funzione, quindi lo scarto è esattamente 0
per costruzione. Valida l'allineamento delle righe, che non è poco.

| confronto | Bundesliga | Ligue 1 |
|---|---|---|
| apertura batte il **DC-da-gol** | **25/25** mercati (1X2 −0.0151 [−0.0215, −0.0087]) | **25/25** (1X2 −0.0169 [−0.0229, −0.0107]) |
| apertura batte la **baseline** | 24/25 | 24/25 |
| apertura batte la **chiusura** | 2/25 | 3/25 |

**Il «25/25» va letto per quello che è**, e la verifica lo ha precisato: è un
conteggio di **segni**; i mercati con CI95 che esclude lo zero sono 18/25 e
21/25. E i 25 mercati sono proiezioni della *stessa* coppia (λ, μ) attraverso la
stessa matrice: valgono 1-2 gradi di libertà effettivi, non 25 conferme
indipendenti. Con questa precisazione, il fatto resta: **il motore funziona
identico partendo dal prezzo che si vede prima del kickoff.**

### 8.1 · La domanda chiave: l'apertura affinata arriva a valere la chiusura?

Δ > 0 = la chiusura è migliore. R0 = apertura grezza; R2 = +θ LOSO; R4 = +livelli
LOSO (`sharpen_1x2` rifittato). Bonferroni α = 0.05/20 = 0.0025.

| ricetta | mercato | Δ | CI95 | n | verdetto |
|---|---|--:|---|--:|---|
| R0 apertura grezza | **1X2**, 9 stagioni | +0.0016 | [−0.0001, +0.0034] | 5.841 | nel rumore |
| R0 apertura grezza | **1X2**, 7 stagioni (finestra pulita) | +0.0019 | p = 0.055 | 4.479 | a un capello dalla soglia |
| R2 + θ LOSO | 1X2 | +0.0018 | [−0.0001, +0.0037] | 5.841 | nel rumore |
| R4 + livelli LOSO | 1X2 | +0.0024 | [+0.0003, +0.0043] | 5.841 | peggio (non Bonferroni) |
| **R0 apertura grezza** | **O/U 2.5**, 7 stagioni | **+0.0044** | **[+0.0027, +0.0061]** | 4.479 | **PEGGIO, Bonferroni sì** |
| R2 + θ LOSO (migliore) | O/U 2.5 | +0.0036 | [+0.0016, +0.0056] | 4.479 | peggio (recupera il 18%) |

Sui **totali** la chiusura vince in modo conclusivo e Bonferroni-resistente (13/14
stagioni-lega), e nessuna ricetta di affinamento chiude il divario. Sull'**1X2**
il divario è più piccolo e non raggiunge la soglia.

**Ma la dicotomia non è dimostrata**, e questo è il punto in cui la verifica ha
colpito il titolo del lavoro. Confrontare un «non significativo» con un
«significativo» non è un test. Rifatto come **differenza-di-differenze** sulle
stesse 4.479 partite:

| | Δ | CI95 | p |
|---|--:|---|--:|
| 1X2 | +0.0019 | [−0.0001, +0.0039] | 0.055 |
| O/U 2.5 | +0.0044 | [+0.0027, +0.0060] | < 0.0001 |
| **O/U − 1X2 (diff-in-diff)** | **+0.0024** | **[+0.0001, +0.0049]** | **0.043** |

Nominalmente al limite, ma **non regge in nessuna delle due leghe presa da sola**
(Bundesliga p = 0.28, Ligue 1 p = 0.09) e **fallisce la soglia di Bonferroni che
il lavoro stesso si è dato** (0.0025) di un fattore 17. La formulazione onesta:
*sui totali la chiusura batte l'apertura in modo conclusivo; sull'1X2 il divario è
più piccolo e non raggiunge la soglia; che i due mercati si comportino
diversamente è un indizio, non un risultato.*

La verifica ha però anche **rafforzato** il lavoro su un fianco scoperto:
rifacendo la domanda chiave col devig di **Shin**, il 1X2 resta nel rumore
(+0.0016) e l'O/U resta conclusivo (+0.0045). La conclusione è invariante al
devig.

### 8.2 · Il resto del fronte apertura

- **θ e φ, di nuovo bocciati con più dati.** Il router a griglia resta **0/25**
  su entrambe anche con il 30% di partite in più (1 e 4 mercati conclusivamente
  peggiorati), e la φ replica quasi esattamente il danno sulla doppia 1X in
  Bundesliga (−0.00070 [−0.00120, −0.00021] sull'apertura contro −0.00076 sulla
  chiusura) mentre in Ligue 1 la griglia sceglie φ₀ = 0 in **9 stagioni su 9**. Il
  rimedio al limite di potenza ha funzionato *come rimedio*, e ha confermato che
  non c'era effetto da trovare. (Anche qui la verifica ammorbidisce l'aggettivo:
  quei «CI conclusivi» delle bocciature non sopravvivono alla molteplicità —
  φ p = 0.0054 su 10 test, router 4 mercati con p ≥ 0.002 su 50.)
- **Una leva nuova, proposta e uccisa nella stessa sessione.** Il movimento
  apertura→chiusura sembrava sotto-correggere sui totali (β 1.75 in Bundesliga,
  1.90 in Ligue 1): estrapolarlo avrebbe battuto la chiusura. Cinque prove lo
  demoliscono — β LOSO e β walk-forward entrambi nel rumore, 4/7 stagioni,
  sensibile al devig (con Shin 1.75 → 1.65 e 1.90 → 1.75), in gran parte spiegato
  dal fatto che la **chiusura O/U devigata è sotto-estrema** (estremizzandola con
  α ≈ 1.15-1.33 il β residuo crolla a 1.40 e 1.60), e ROI −3,95% e +0,91% con CI
  larghissimi. **Rumore selezionato, non edge.**
- **Il cambio di provider non crea uno scalino.** Era l'obiezione più seria: nel
  2017-19 l'apertura è Pinnacle, dopo è una media multi-book. Costruito
  l'esperimento controllato sulle **stesse partite** (le colonne Pinnacle esistono
  in tutte e 9 le stagioni), le due aperture danno lo **stesso** log-loss
  (Δ ±0.0002, CI ±0.0008) e lo **stesso** θ a tre decimali, nonostante 2 punti di
  overround di differenza. Attenzione però all'attribuzione: quell'esperimento
  gira solo dal 2019-20; a scagionare l'epoca Pinnacle è il **percorso
  tutto-Pinnacle su 9 stagioni** (PS → PSC: +0.0011 e +0.0023, nel rumore), non
  l'esperimento controllato.

### 8.3 · Un fatto strutturale nuovo: θ è una scala, non una costante di lega

Misurato sulle stesse partite, con tre fonti di tassi diverse:

| lega | θ DC-da-gol | θ apertura | θ chiusura | scala rispettata |
|---|--:|--:|--:|:-:|
| bundesliga | 1.045 | 1.083 | 1.092 | 5/6 stagioni |
| ligue_1 | 1.034 | 1.081 | 1.096 | 6/6 stagioni |

**θ_DC < θ_apertura < θ_chiusura in 11 stagioni-lega su 12** (atteso per caso 1/6
a stagione). La verifica ha aggiunto gli intervalli che mancavano, e tutti e sei i
gradini sono conclusivi (il più debole è chiusura − apertura in Bundesliga,
+0.0092 [+0.0024, +0.0162]).

**L'interpretazione va però corretta.** Era stata scritta come «θ è un termometro
della *qualità* del prezzo». La verifica ha simulato: aggiungere rumore ai tassi
abbassa θ (1.092 → 0.899 con sd 0.30) ✓, ma **anche lo shrinkage puro lo abbassa**
(×0.6 → 1.041) **e anche la dilatazione pura** (×1.3 → 1.077). θ è *massimo* alla
dispersione corretta e scende in entrambe le direzioni: misura il
**disallineamento di dispersione**, non il rumore né la qualità.

La conseguenza operativa — che è la parte che vale — resta: **ogni volta che
cambia la fonte dei tassi (modello, apertura, chiusura, blend) il θ del router va
rifittato su quella fonte, non ereditato.**

---

## 9 · Il mercato campione di stagione: il simulatore trasferisce, il valore no

Il mercato **campione** è il primo che non si deriva dalla matrice di una
partita: dipende da 306 o 380 partite congiuntamente più la regola di classifica,
quindi va simulato (Monte Carlo, 20.000 stagioni per stagione-lega).

**Le regole di spareggio sono state verificate su fonte ufficiale, non
indovinate.** Bundesliga: DFL *Spielordnung* §2 c.3 lett. c) → differenza reti,
gol fatti, scontri diretti, cioè `("gd","gf","h2h")`, come la Premier. Ligue 1:
LFP *Règlement des Compétitions* art. 518 TER → differenza reti generale, punti
negli scontri diretti, differenza reti negli scontri diretti, …, gol fatti, cioè
`("gd","h2h","gf")` — un **terzo set distinto** da entrambi quelli già nel
progetto. La riforma 2025-26 tocca solo i criteri dal 4° in giù. Eccezione COVID
2019-20: classifica al quoziente punti/partita, verificato in codice che il
campione non cambia (PSG, 2.5185 contro 2.0000).

**Controllo di sanità superato in modo totale:** le 6 quantità pubblicate dal
progetto per le 3 leghe storiche riprodotte con scarto **esattamente 0.0**.

| confronto (8 stagioni per lega) | Bundesliga | Ligue 1 |
|---|---|---|
| modello | **0.7392** | **0.9132** |
| vs uniforme (2.89 / 2.96) | +2.1512 [+1.06, +2.76], 7/8 | +2.0431 [+0.67, +2.79], 7/8 |
| vs campione uscente | +0.7175 [+0.18, +1.73], 8/8 | +0.5713 [−0.20, +1.84], nel rumore |
| vs **«vince la rosa più cara»** (LOO) | +0.2359 [−0.15, +0.86] | +0.0759 [−0.15, +0.43] |
| vs stessa baseline **al suo meglio** (q = 0.87) | **−0.0082** [−0.17, +0.15] | **−0.1682 [−0.33, −0.05], 0/8** |
| vs baseline morbida p ∝ valore^β | −0.1104 | −0.2422 |

**Contro la baseline che conta, il modello non aggiunge nulla di dimostrabile —
e in Ligue 1 è conclusivamente peggiore.** Bayern e PSG sono la rosa più cara in
9 stagioni su 9 (fattore 1,34-2,92 sulla seconda) e indovinano 7 volte su 8.
Nota di onestà: la baseline «al suo meglio» ha il parametro scelto in-sample e
non è implementabile in prospettiva, quindi la lettura corretta è *il modello non
dimostra valore aggiunto*, non *il modello è peggio del portafoglio*. E il solo
CI conclusivo contro il modello non sopravvive a Bonferroni (soglia 0.0031): ciò
che regge è la **replica del segno**, negativo in 4 confronti su 4 nel regime
oracolo.

**La normalizzazione spiega tutto.** Bundesliga e Ligue 1 hanno la stessa
entropia dell'esito campione (0.349 nats, 2 campioni distinti in 9 stagioni) e
sono le due leghe **più prevedibili** del campione (Serie A 1.311, La Liga 0.937,
Premier 0.849). Sulle 5 leghe:

| correlazione | valore |
|---|--:|
| entropia della lega ↔ skill contro l'uniforme | **−0.765** |
| entropia della lega ↔ guadagno contro «la rosa più cara» | **+0.791** |

Cioè: **il modello *sembra* bravo dove la lega è già decisa, ed è *davvero* utile
dove non lo è.** Serie A +1.1638 e Premier +1.5751 contro la rosa più cara,
entrambi conclusivi 8/8. (Le correlazioni sono su 5 punti: direzione, non
misura.)

Due risultati collaterali scomodi, che valgono oltre le due leghe nuove:

- su tutte e 40 le stagioni-lega il Monte Carlo da 20.000 stagioni **pareggia**
  una baseline a **un solo parametro** p ∝ valore^β (+0.0303, CI [−0.16, +0.21]);
- 12 stagioni su 16 sono «ovvie» (il campione è sia l'uscente sia la rosa più
  cara) e lì il modello fa log-loss 0.198; nelle 4 restanti fa **2.710**. Tutta
  la prestazione viene da stagioni che un bambino avrebbe indovinato, tutto il
  costo da quelle che contano (Leverkusen 2023-24 prezzato 1,15%; Lille 2020-21
  **0,36%**).

**Sulla sovra-confidenza** (il difetto noto del simulatore) la domanda posta non
è risolvibile qui: il controllo sul favorito **non discrimina**. Con 7/8 favoriti
azzeccati, *ogni* probabilità dichiarata fra il **50,0% e il 99,2%** passa il test
al 5%. Applicando lo stesso metro al −18,4 pp già pubblicato dal progetto sulle
3 leghe storiche, il p-value esatto è **0.074**: nemmeno quello è conclusivo.

**Non esistono quote outright storiche**, quindi «battiamo il mercato» su questo
mercato **non è testabile all'indietro**. Tutto quello che c'è sono baseline.

---

## 10 · Il fronte generale (§1.9): non deciso — e la statistica che diceva il contrario non regge

La domanda del principio §1.9: per ogni leva, meglio una costante **per-lega** o
una **generale** cross-lega? Misurata su cinque leve con protocollo identico —
per-lega = leave-one-season-out dentro la lega, pooled = **leave-one-league-out**
(il pooled non vede mai la lega su cui è valutato) — su 12.459 partite (path
mercato) e 10.734 (path DC).

**Controlli di sanità superati:** θ MLE riprodotto sulle 5 leghe (scarto max
0.0005), log-loss di mercato a θ = 1 riprodotto, e il DC walk-forward riproduce
il tracer con scarto massimo 6.4 × 10⁻⁵.

Sui **mercati primari** il confronto è nel rumore ovunque: θ sull'1X2 +0.00030
[−0.00020, +0.00082], φ +0.00003, ρ +0.00019. Il lavoro concludeva però che «il
pooled non perde mai», sulla base del conteggio delle celle lega × mercato con CI
conclusivo: **73 a 8** in favore del pooled, test dei segni p ≈ 3 × 10⁻¹⁴.

**Quel conteggio non misura quello che sembra.** La verifica ha rimescolato a
caso le 12.459 righe in 5 pseudo-leghe × 7 pseudo-stagioni delle stesse
dimensioni — distruggendo *ogni* traccia di identità di lega, quindi zero
eterogeneità e zero «struttura universale» da scoprire — e ha rilanciato
l'apparato identico:

| dati | pooled vs per-lega (celle conclusive, leva θ) |
|---|---|
| **veri** | 29 / 3 |
| placebo, seme 11 | 16 / 1 |
| placebo, seme 22 | **29 / 0** |
| placebo, seme 33 | 24 / 2 |

Indistinguibile. Il conteggio delle celle e il test dei segni misurano **solo che
il selettore pooled dispone di quattro volte più dati di selezione**: non
contengono informazione sull'universalità della struttura. Il p-value aggregato
va cancellato, non «letto con cautela». Va anche corretto il denominatore: 4 dei
25 mercati sono complementi esatti di altri 4, quindi i mercati distinti sono 21
e l'aggregato è **59-8**, non 73-8.

**E «non perde mai» è falso a livello di pool** fuori dai mercati primari: sulla
leva θ il per-lega vince conclusivamente su `odd_total` (+0.00005),
`home_by_2plus` (+0.00058 [+0.00004, +0.00116]) e `away_by_2plus` (+0.00075
[+0.00009, +0.00138]) — margini più grandi di qualunque vittoria del pooled sulla
stessa leva, e «scarto ≥ 2» è Tier 1 dichiarato.

**Le due voci che erano state promosse cadono entrambe.**

1. **«ρ = −0.06 non è ottimale».** Un ρ pooled scelto fuori campione batteva
   −0.06 su 10 mercati su 25, con in testa il **GG/NG** (−0.00099
   [−0.00153, −0.00043]). Ma l'intera leva è misurata col router **spento**
   (θ = 1), mentre il motore adottato applica θ ≈ 1.225 a tutto il listino.
   Rifatto al θ di produzione, il segno **si capovolge**:

   | mercato | θ = 1.000 | θ = 1.225 (router v3) |
   |---|---|---|
   | GG/NG | −0.00099 [−0.00153, −0.00044] | **+0.00117 [+0.00057, +0.00177]** |
   | clean sheet ospite | −0.00037 | **+0.00037** (conclusivo) |
   | clean sheet casa | −0.00029 | +0.00014 |

   La griglia completa mostra il perché: l'ottimo di ρ è −0.16 a θ = 1, −0.12 a
   θ = 1.1 e **0.00 a θ = 1.225**, e il minimo raggiungibile è lo stesso nelle tre
   colonne (0.6794 / 0.6793 / 0.6794). **ρ e θ sono sostituti quasi perfetti su
   questo mercato**: non c'è informazione nuova, c'è la stessa correzione
   riscritta con un'altra lettera. Raccomandazione ritirata; il ρ ereditato
   −0.06 è innocuo.
2. **Gli iperparametri del DC in walk-forward** (−0.00018 [−0.00034, −0.00001]
   sull'1X2, dichiarato conclusivo pro-pooled) poggiano su **una sola stagione da
   306 partite**: il selettore per-lega sceglie la config di riferimento in 29
   stagioni-lega su 30, e l'unica eccezione è Bundesliga 2023-24, che da sola
   riproduce esattamente il Δ pubblicato. n efficace = 306, non 10.734. E sullo
   stesso asse, sull'O/U 2.5, il segno si ribalta.

**Quello che resta, e vale.** (a) L'**auto-confutazione** del lavoro è reale e
punta nella direzione opposta al suo titolo: dando al fronte per-lega un θ scelto
*in-sample* (tetto teorico, non giocabile), il per-lega **batte** il pooled
sull'1X2 (+0.00057) e sul risultato esatto (+0.00136). Un segnale per-lega
esiste; è troppo piccolo perché un selettore onesto lo estragga con 7 stagioni.
Anzi, sull'1X2 a livello di pool il **per-lega è l'unico fronte che batta il
riferimento** (−0.00094 [−0.00166, −0.00018]), mentre il pooled non ci arriva.
(b) La **falsificazione di un'ipotesi pre-registrata dal progetto**: «θ decresce
con la liquidità del mercato» è **falsa come covariata** — la correlazione di
rango fra margine mediano del book e θ MLE è **+0.10**, e un pooled a due
famiglie predetto dal margine non batte mai il pooled semplice. Le due famiglie
esistono, ma non sono predicibili dal margine. (c) Il **DC congiunto** su 5 leghe
(γ, ρ e livello vincolati a essere comuni) pareggia 5 DC separati (+0.00028,
CI [−0.00088, +0.00145]) nonostante γ vari da 0.149 a 0.308 e ρ da −0.155 a
+0.027 — ma con n = 5.256 e la semi-ampiezza di CI più grande di tutto il lavoro
(±0.00117), «pareggio perfetto» è una sovra-affermazione: il test esclude solo
effetti maggiori di ~1,2 millesimi.

**Verdetto:** su tutte e cinque le leve il confronto per-lega vs generale resta
**non deciso**. Nessuna promozione, nessuna bocciatura, nessuna modifica a
`src/config.py` né al ρ di produzione. È comunque un risultato utile: chiude
cinque leve come «non c'è niente da guadagnare a scegliere per lega, ma nemmeno a
mettere insieme».

**Difetto di protocollo da dichiarare:** entrambi i selettori guardano il futuro
(LOSO usa le stagioni successive della stessa lega, LOLO tutte le stagioni delle
altre). Poiché il progetto stesso ha stabilito che θ **cresce nel tempo**,
nessuno dei due fronti è giocabile come misurato: la domanda va rifatta con un
selettore walk-forward.

---

## 11 · Audit di calibrazione: calibrati quanto il book, ma non «onesti nella forma»

Domanda: i prezzi che il motore produce sui ~17 mercati che il book non quota
sono probabilità oneste? Misurato su 28 mercati × 3 leghe (le due nuove più la
Serie A di controllo), 7 stagioni.

**Controllo di sanità superato:** sulle 3 leghe storiche l'apparato riproduce
bias ed ECE del registro del progetto con scarto massimo **1.1 × 10⁻¹⁶** su 76
confronti per lega, e le frequenze realizzate riverificate direttamente dagli
snapshot coincidono.

**Quello che regge.**

1. **Dove la quota esiste, siamo calibrati quanto il book:** tutti e 12 gli
   intervalli di ΔECE contengono lo zero, |ΔECE| massimo 0.0072. E il bias è in
   larga parte **ereditato** dal mercato, non prodotto da noi (Bundesliga over
   2.5: motore −0.0214 contro book −0.0196, aggiungiamo −0.0018).
2. **Il difetto vero è una famiglia sola**, e si replica: GG/NG **sotto**-prezzato
   e clean-sheet / vince-a-zero **sovra**-prezzati.

   | mercato | bundesliga | ligue_1 | serie_a | pooled 2 leghe nuove |
   |---|--:|--:|--:|--:|
   | GG/NG | **−0.0238** [−0.0443, −0.0033] | −0.0206 [−0.0406, +0.0001] | −0.0292 [−0.0477, −0.0105] | −0.0221 (z −3.01) |
   | clean sheet casa | — | — | — | +0.0180 (z +2.77) |
   | vince-a-zero casa | — | — | — | +0.0132 (z +2.23) |

   Il pooled del GG **non supera Bonferroni** (z 3.01 contro soglia 3.04). Ciò che
   regge non è la significatività di una lega, è la **replica**: 4 leghe su 5 con
   lo stesso segno e ordine di grandezza, e la quinta (Premier) è quella dove il
   difetto è assente e dove il router già usa θ = 1.
3. **La θ raddrizza quel bias**, in tutte e tre le leghe: Bundesliga −0.0238 →
   −0.0106, Ligue 1 −0.0206 → −0.0049, Serie A −0.0292 → +0.0049. Dopo la θ il CI
   del GG contiene lo zero ovunque. Il guadagno in log-loss è minuscolo
   (0.6847 → 0.6842) — ed è esattamente il motivo per cui la griglia sul log-loss
   l'aveva bocciata: **è un argomento per la leva che il log-loss non sa vedere**.
   La verifica ha aggiunto tre controlli che mancavano e che *reggono*: con il
   devig di Shin il bias è −0.0234 invece di −0.0238 (non è un artefatto di
   devig); ri-ancorando in modo coerente sotto la matrice double-Poisson il
   rimedio resta (−0.0119 contro −0.0106); e una θ **walk-forward** (solo stagioni
   passate) ripara comunque.

**Quello che non regge.**

- **«I prezzi sono onesti nella FORMA ovunque»** era la conclusione di testa, e
  poggiava su un solo indicatore (r = ECE / ECE_null95 ≤ 1.49 su 84 celle, contro
  una soglia di bocciatura di 3.0). La verifica ne ha misurato la **potenza**:
  generando dati da una verità deliberatamente storta nella forma, con errori di
  probabilità fino a **11,8 punti percentuali**, quell'indicatore dà r ≈ 1.16 →
  «affidabile». Non può vedere un difetto di forma a questo n. L'assenza di
  potenza era stata convertita in un'affermazione positiva sul modello.
- **E il difetto di forma c'è.** Con un test che ha potenza (ricalibrazione
  logistica y ~ a + b·logit(p), Wald su b = 1, più Hosmer-Lemeshow): pendenza
  b > 1 in **10 celle su 12**, cioè prezzi sistematicamente troppo compressi verso
  il tasso base — che è esattamente la sotto-dispersione che la θ presuppone.
  Conclusive: Bundesliga over 2.5 b = 1.282 (p = 0.030), Bundesliga clean sheet
  casa 1.244 (p = 0.023), Serie A 1X2-casa 1.182 (p = 0.002), Serie A clean sheet
  casa 1.264 (p = 0.003). Quindi «difetto solo di livello» non è solo non
  dimostrato: **è sbagliato nel verso**.
- **Il miglioramento di ECE della Ligue 1** (0.0225 → 0.0066, r 0.90 → 0.26), che
  era la sola ragione per promuovere la θ a titolare lì, è **fortuna**: sotto
  calibrazione perfetta di quelle stesse probabilità l'ECE ha mediana 0.0135 e 5°
  percentile 0.0052, quindi l'osservato 0.0066 sta al 9,5° percentile — *meglio*
  di quanto riesca tipicamente a un modello perfettamente calibrato. r < 1 non
  significa «meglio che calibrato», significa che il rumore fra le fasce si è
  cancellato.
- **Una baseline onesta manca:** uno shift LOSO del bias medio (**un** parametro)
  azzera il bias GG esattamente (+0.0000 / −0.0005 / +0.0000), meglio della θ in
  tutte e tre le leghe. Il vantaggio vero della θ — coerenza su tutto il listino —
  è un argomento, non una misura.
- **Il «fronte generale non applicabile» era asserito, non misurato:** una θ
  leave-one-**league**-out (mai vista la lega bersaglio, θ 1.09-1.17) riduce il
  bias GG in tutte e tre le leghe (Bundesliga → +0.0037, Ligue 1 → +0.0033,
  Serie A → −0.0155). Una θ unica cross-lega migliora tutte e tre.

**Un difetto strutturale nascosto dietro «calibrati quanto il book».** L'ECE ha
un pavimento di rumore di ~0.02 e non vede scarti deterministici. Il motore
prezza il **pareggio** sistematicamente sotto la chiusura devigata: −0.0052
(Bundesliga), −0.0050 (Ligue 1), −0.0075 (Serie A), stesso segno in tre leghe. È
il residuo del minimo quadrati a 2 parametri su 4 bersagli (residui medi
Bundesliga: H +0.0025, D −0.0052, A +0.0027, O −0.0018), e in Serie A **raddoppia**
il bias del pareggio rispetto al book (−0.0157 contro −0.0083). Un test appaiato
con potenza dice che sull'esito-casa il motore è conclusivamente, benché
trascurabilmente, **peggio** del book (Bundesliga +0.00038 [+0.00005, +0.00070];
Serie A +0.00054 [+0.00012, +0.00096]). Rimedio candidato, non testato: pesare i
4 bersagli nell'inversione, o liberare un terzo parametro.

**L'alternativa ρ, e perché il verdetto resta aperto.** Se il GG fosse
sotto-prezzato per il vincolo ρ = −0.06 e non per la dispersione, basterebbe
ri-tarare un parametro che il motore ha già. Misurata l'intera griglia: **ρ\* =
−0.240** (Bundesliga) e **−0.199** (Ligue 1) azzerano il bias del GG. In
Bundesliga un ρ ri-tarato è persino un rimedio globale **migliore** della θ
(media |bias| su 9 mercati: 0.0075 contro 0.0132); in Ligue 1 fallisce (0.0108
contro 0.0069). Quindi **non si può dichiarare che la θ sia la spiegazione unica
o necessaria** — e va detto che ρ\* è scelto in-sample sulla statistica in esame,
mentre la θ è leave-one-season-out. Nota tecnica corretta durante il lavoro:
cambiare ρ *muove* l'1X2, perché `implied_lambda_mu` è un minimo quadrati con 2
parametri su 4 bersagli e non può centrarli tutti.

---

## 12 · Le leve di panchina del DC e le covariate

Il path **standalone** (Dixon-Coles senza quote), portato per la prima volta
fuori dalla Serie A: 112 backtest walk-forward, config Serie A pura, 6 stagioni
di test per lega.

**Controlli di sanità superati:** log-loss 1X2 0.991937 e 1.004075 contro i
0.9919 / 1.0041 del report 6; T del temperature scaling in Serie A **0.9414**
contro lo ~0.94 pubblicato.

**Le quattro leve di panchina.**

| leva | bundesliga | ligue_1 | verdetto |
|---|--:|--:|---|
| A · temperature scaling | −0.000236 [−0.00163, +0.00116], 5/6 | +0.000370 [−0.00072, +0.00144], 2/6 | nel rumore / peggiora |
| B · ricalibrazione per-classe | +0.002807 [−0.00009, +0.00572], 1/6 | **+0.002200 [+0.00036, +0.00402]**, 1/6 | **conclusivo CONTRO** |
| C · diagonale inflazionata (φ costante) | +0.000687 [−0.00018, +0.00154], 2/6 | −0.000056 [−0.00120, +0.00106], 2/6 | nel rumore |
| D · **ensemble di emivite 180+730** | −0.000496 [−0.00137, +0.00037], 4/6 | **−0.000938 [−0.00177, −0.00013]**, 5/6 | l'unico positivo |

**Tre aspettative su quattro sono state smentite.** (A) La T è > 1, non < 1: la
Bundesliga è l'unica delle 5 leghe con T > 1 (1.063, 5/6 stagioni) — ma la
verifica ha applicato il test del rapporto di verosimiglianza e **nemmeno quella
T è distinguibile da 1** (LR = 1.32, p = 0.25); l'unica lega con T diversa da 1 al
5% è La Liga (0.890, p = 0.018), che non supera Bonferroni su 5 leghe. La
domanda «il DC è più sovra-confidente sulle leghe nuove?» non ha risposta
misurabile. (B) Non solo il guadagno manca: la leva **peggiora**, in Ligue 1 con
CI conclusivo. (C) La leva a più alta probabilità a priori — quella che il §3
suggeriva promettente, perché una φ costante sembrava fare meglio della φ35 —
**non paga in nessuna delle due leghe**. Quell'indicazione va letta come «la parte
intelligente della φ35 non si ripaga», non come «la φ costante funziona».

**L'unico candidato vivo, e perché non viene promosso.** L'ensemble 180+730 è
negativo in 12/12 sottoinsiemi leave-one-season-out, e il meccanismo è
verificato: 180g e 730g **prese da sole sono entrambe peggiori** della base in
entrambe le leghe (il guadagno viene dalla media, cioè da riduzione di varianza,
non da un'emivita migliore). Ma il pooled dà p = 0.019 contro una soglia di
Bonferroni sugli 8 test pre-dichiarati di **0.00625**, e **non replica** in
Bundesliga. Promettente, **non dimostrato**. Il test che deciderebbe è un pooled a
5 leghe (~10.000 partite), con 24 dei 60 walk-forward già su disco — e va
**pre-registrato prima**, altrimenti si ricade nella molteplicità che ha già
ucciso questo giro.

### 12.1 · Le covariate: sei su sei bocciate, e una pista che si chiude

| covariata | Δ bundesliga | Δ ligue_1 | β medio | segno stabile |
|---|--:|--:|--:|:-:|
| `rest_full` | +0.000796 | +0.000371 | −0.029 / +0.002 | 5/6 · 4/6 |
| `midweek` | −0.000393 | +0.000321 | +0.004 / +0.008 | 4/6 · 5/6 |
| `midweek` **ricostruito** | −0.000345 | +0.000227 | −0.001 / −0.000 | 4/6 · 4/6 |
| `squad_value` | +0.000873 (**0/6 stagioni**) | +0.000799 | **+0.056 / +0.095** | **6/6 · 6/6** |
| `absence` *(su una stima dichiarata)* | +0.000252 | +0.000313 | −0.009 / +0.003 | 4/6 |

Nessuna ha CI conclusivo a favore; 12 delta su 14 sono peggiorativi. `rest_full`
è ora rumore su **5 leghe su 5**.

**La pista che si chiude, ed era indicata come la più interessante.** Il report 9
§4 aveva recuperato 3.045 calendari di coppa e dichiarato onestamente che un
`midweek_europe` sbagliato nel 6-13% delle righe «rendeva qualunque test su quella
covariata inconcludente per costruzione». Il test è stato rifatto **col dato
buono** (patch del loader a runtime; 68 celle 0 → 1 in Bundesliga e 212 in Ligue
1; tasso 12,07% → 15,34% e 5,02% → **12,80%**; tutte e 6 le stagioni di test sono
affette, quindi rifare il test sulle sole stagioni sane era impossibile). Il
confronto **diretto** fra covariata bucata e covariata corretta:

| | Δ | CI95 |
|---|--:|---|
| bundesliga | +0.000048 | [−0.00074, +0.00083] |
| ligue_1 | −0.000094 | [−0.00127, +0.00104] |

**Misurare bene la congestione non la fa funzionare**, e non rende nemmeno il β
più stabile — in Ligue 1 la correzione ribalta il segno delle prime due stagioni.
Il difetto del dato non era la ragione per cui la covariata non funzionava.
L'integrazione dei 3.045 calendari resta giusta per **correttezza del dato**
(report 9 §7.4), non per guadagno predittivo.

**Il caso più istruttivo è `squad_value`:** ha il β più grande e più stabile mai
visto fra le covariate (6/6 dello stesso segno in **entrambe** le leghe, +0.056 e
+0.095, direzione sensata) e non guadagna nulla — in Bundesliga peggiora in 6
stagioni su 6, e dalla 6ª giornata in poi **peggiora con CI conclusivo**
(+0.0012 [+0.00034, +0.00207]). Da mettere agli atti: **la stabilità del segno di
un β non è evidenza di valore predittivo incrementale**; misura solo che la
covariata è correlata col risultato, cosa che attacco e difesa già catturano.

**Che cosa ha corretto la verifica.** (a) La narrazione sulla **calibrazione**
delle leve A e C è in gran parte un artefatto: il MCE di riferimento della
Bundesliga (0.1758), da cui discendevano sia «A: 0.176 → 0.083» sia «C: 0.176 →
0.075», viene da un bin con **8 celle su 5.508**, e bootstrappando le differenze i
CI attraversano lo zero (MCE Δ −0.101 [−0.262, +0.040]; ECE Ligue 1 Δ −0.0034
[−0.0087, +0.0029]). Le due voci di panchina «solo calibrazione» non hanno base.
(b) Il **bias per classe** su cui era costruita la lezione della leva B non è
significativo in nessuna delle 6 celle (|z| ≤ 1.26): la causa vera è che il bias
per classe non è stabile **nel tempo dentro la stessa lega**. (c) Il rendiconto
della molteplicità era incompleto: i CI calcolati sono **67**, non ~24, perché
ogni confronto produceva anche un test sull'O/U mai riportato — e uno di quelli è
conclusivo e favorevole (`midweek` Bundesliga O/U −0.000491 [−0.00088, −0.00010]),
il che rende la frase «nessuna covariata ha CI conclusivo a favore» falsa rispetto
al proprio artefatto. Con 67 test la soglia di Bonferroni è 0.00075 e **nulla vi
si avvicina**, quindi la bocciatura resta.

### 12.2 · Un fatto strutturale, post-hoc e dichiarato tale

La T del temperature scaling e il θ di sotto-dispersione del mercato sono in
corrispondenza di rango **perfetta e inversa** su tutte e 5 le leghe
(Spearman −1.000; p esatto di permutazione 2/120 = 0.017). Due diagnostiche
indipendenti — una sul nostro modello senza quote, una sul mercato — sembrano
misurare la stessa proprietà latente della lega.

**Va però ridimensionato:** quattro delle cinque T sono indistinguibili da 1 e
tre dei cinque θ stanno dentro una valle sei volte più piatta. Il contenuto reale
è la spaccatura a **due gruppi** (latine contro il resto), la cui concordanza
casuale vale 1/10, non 1/60. È una pista, non un risultato.

---

## 13 · La rosa aggiornata, per le due leghe nuove

| leva | Bundesliga | Ligue 1 | motivo |
|---|---|---|---|
| market-implied dalla **chiusura** | ⚽ titolare | ⚽ titolare | batte il DC-da-gol su 25/25 mercati per segno (18/25 e 21/25 con CI conclusivo) |
| **market-implied dall'APERTURA** (voce nuova) | ⚽ titolare | ⚽ titolare | 25/25 sul DC, 24/25 sulla baseline, 5.842 partite. Attivazione: quando ci sono apertura 1X2 **e** O/U. Con la chiusura O/U si usa la chiusura, conclusivamente migliore (§8.1) |
| DC gol+xG (fallback senza quote) | ⚽ titolare | ⚽ titolare | batte la baseline, non il mercato. I suoi tassi sono i più rumorosi dei tre (θ 1.045 / 1.034) |
| **router θ (dp)** | ❌ bocciato | ❌ bocciato | 0/25 conclusivi su chiusura **e** su apertura (+30% partite). Motivo corretto: effetto sotto soglia, selettore che non lo prende. Promozione solo dove θ MLE ≥ ~1.20 |
| **φ(\|λ−μ\|)** | ❌ bocciata | ❌ bocciata | nel rumore, peggiora la doppia 1X su entrambe le fonti di quote; in Ligue 1 φ₀ = 0 in 9 stagioni su 9. **Indistinguibile** da una φ costante, che a sua volta non paga (§12) |
| **devig di Shin** | 🪑 panchina | 🪑 panchina | pooled: conclusivo su Brier ma **non a cluster di lega**; migliora 3 leghe su 5. Conclusivo solo nelle «latine» |
| **ricalibrazione per-classe del mercato** | 🪑 panchina | ❌ bocciata | guadagno negativo; la spiegazione «segue la natura della lega» è **ritirata** (w_D Liga = 0.978) |
| **power-devig** | ❌ bocciato | ❌ bocciato | peggiora con CI conclusivo in Bundesliga, a 7 e a 9 stagioni |
| **ricalibrazione-μ per il GG/NG** | ⬜ **non dimostrata** (era 🪑) | ❌ bocciata | 7 celle conclusive su 300 = quante ne dà il caso; non replica; non confermata dal giudice esterno (§6, [`11_ggng.md`](11_ggng.md)) |
| **`sharpen_1x2` / beat-the-close** | ❌ bocciato | ❌ bocciato | peggiora la chiusura (BL conclusivo su entrambi i protocolli, L1 conclusivo in walk-forward); bocciato anche **in-sample**. ROI −22% e −13% |
| **estrapolazione β del movimento apertura→chiusura** (leva nuova) | ❌ bocciata | ❌ bocciata | proposta e uccisa nella stessa sessione: LOSO, walk-forward, Shin, estremizzazione, ROI |
| **estremizzazione della chiusura O/U** (α ≈ 1.15-1.33) | 🪑 panchina | 🪑 panchina | nel rumore in entrambe, ma α > 1 in tutte le stagioni: la chiusura O/U devigata è sistematicamente meno estrema dei fatti. Unico candidato vivo del fronte apertura. Promozione: replica su una terza lega |
| **θ sulla famiglia GG/clean-sheet in calibrazione** | 🪑 panchina | 🪑 panchina | raddrizza il bias in 3 leghe su 3 e regge a devig di Shin, ancoraggio coerente e walk-forward. **Ma** una baseline a un parametro (shift del bias) fa meglio, e l'alternativa ρ non è esclusa (§11) |
| **simulatore campione di stagione** | 🪑 panchina | ❌ bocciato | batte uniforme e uscente ma non «vince la rosa più cara»; in Ligue 1 conclusivamente peggiore della baseline al suo meglio (§9) |
| **ensemble di emivite 180+730** (path DC) | 🪑 panchina | 🪑 **panchina alta** | l'unico segnale positivo del path DC: L1 −0.00094 CI conclusivo, ma p = 0.019 > Bonferroni e non replica in BL |
| temperature scaling · ricalibrazione per-classe · draw inflation (path DC) | 🪑 / ❌ / ❌ | ❌ / ❌ | nessuna paga; B peggiora con CI conclusivo in Ligue 1 (§12) |
| **6 covariate** (rest, midweek, midweek ricostruito, squad_value, absence) | ❌ bocciate | ❌ bocciate | 12 Δ su 14 peggiorativi; il dato corretto non cambia il verdetto |
| stimatore chiusura O/U | ⚽ titolare | ⚽ titolare | **pooled**, non per-lega: il ribaltamento non regge nel regime d'uso (report 9 §3) |
| regole di spareggio per-lega (dato, non modello) | ⚽ adottate `("gd","gf","h2h")` | ⚽ adottate `("gd","h2h","gf")` | verificate su DFL e LFP; 0 divergenze sui campioni reali, rilevanti nel 3,4-3,7% delle stagioni simulate |

---

## 14 · Cosa resta da fare

I sette punti della lista precedente sono stati tutti affrontati: GG/NG contro le
quote vere ([`11_ggng.md`](11_ggng.md)), mercato campione (§9), beat-the-close
(§7), market-implied dall'apertura (§8), audit di calibrazione (§11), fronte
generale (§10), leve di panchina del DC e covariate (§12). Quello che resta è
diverso, e per la maggior parte è **rifare bene** cose fatte una volta sola:

1. **rimisurare il fronte generale con un selettore walk-forward** (§10): è
   l'unico protocollo che autorizzi a dire «è il vantaggio che si incassa in
   pratica», e con θ che cresce nel tempo può dare un risultato diverso da
   entrambi quelli misurati;
2. **il pooled a 5 leghe sull'ensemble di emivite** (§12), **pre-registrato**:
   ~10.000 partite, 24 dei 60 walk-forward già su disco, un solo confronto. È
   l'unica domanda del path DC ancora aperta e risolvibile;
3. **chiudere le due griglie tronche**: ρ del bakeoff O/U con l'ottimo al bordo
   (report 9 §5.2) e la griglia **congiunta ρ × θ** del §10, dove i due parametri
   risultano sostituti;
4. **testare i rimedi al residuo dell'inversione** (§11): pesare i 4 bersagli o
   liberare un terzo parametro, per togliere lo scarto deterministico di −0.005
   sul pareggio;
5. **una θ leave-one-league-out** come voce di rosa vera (§11): migliora la
   calibrazione GG in 3 leghe su 3 e non è mai stata testata come fronte
   generale;
6. **`dp_tilt` al posto di `dp_lvl` in `sharpen_1x2`** per la Serie A (§7.3): un
   parametro in meno, stesso risultato, e conclusivo anche in walk-forward;
7. **Tier 2 e Tier 3** (handicap asiatico, HT/FT e tempi): mercati mai coperti,
   su nessuna lega.

---

## 15 · Nota di metodo: che cosa ha detto la verifica avversariale

I quattro fronti del primo giro (§2-§6) erano stati eseguiti da agenti che
avevano **completato i calcoli** ma erano stati interrotti prima di riportare: i
numeri erano stati estratti dai loro output grezzi (`cantiere/out/leve_*.json`) e
**non erano passati dalla verifica avversariale prevista**. Quella verifica è
stata fatta. Esito: **tre analisi su cinque reggono con riserva, due non
reggono.**

**La riproducibilità è impeccabile, e va detto per primo.** Gli script rieseguiti
danno delta identici a 1 × 10⁻¹⁶; i θ scelti coincidono; le 18 quantità del
controllo di sanità del §2 si riproducono a **2.98 × 10⁻¹⁷** contro il
4.9 × 10⁻¹⁰ dichiarato. Le cache non sono stantie (re-inversione fresca: max diff
4.4 × 10⁻¹⁶) e i bootstrap non sono fragili al seme (60 semi diversi sia sul
GG/NG sia sul Brier di Shin). Nessuno dei difetti trovati è un errore di calcolo:
sono tutti di **lettura** dei calcoli.

| affermazione | esito della verifica | dove |
|---|---|---|
| «griglia > MLE non è una proprietà dello stimatore» | **regge**, ed è più forte: è una tautologia (`price_markets` ≡ `dp_matrices`, max diff 0.0) | §2.2(a) |
| «il ribaltamento sulla Liga era la finestra, non lo stimatore» | ❌ **falso**: il 1.097 è la media di 8 fit espandenti (riprodotta 1.103); il pooled sulla stessa finestra dà 1.199 → due terzi è lo stimatore | §2.2(b) |
| router θ bocciato su Bundesliga e Ligue 1 | **regge**, con motivo corretto: a θ fisso l'effetto BL esiste (p = 0.011) ma non supera Bonferroni | §2.1 |
| «una φ costante fa meglio della φ35» | ❌ **non sostenuto**: nessun CI, effetti 5-100× sotto la soglia, e su 3 mercati vince la φ35 | §3 |
| Shin ≥ moltiplicativo, pooled | **regge come direzione**, non come conclusione: a cluster di lega il CI tocca lo zero, 3 leghe su 5 | §4 |
| w_D > 1 in La Liga («latina») | ❌ **errore di tabella**: il run dà 0.978 | §5A |
| il segnale GG/NG in Bundesliga | ❌ **non dimostrato**: 7 celle conclusive su 300 = quante ne dà il caso; non replica; la variante contigua è nel rumore | §6 |
| lo stimatore O/U passa da pooled a per-lega | ❌ **artefatto del protocollo**: nel regime d'uso vero vince il pooled con CI conclusivo | report 9 §3 |

**I fronti nuovi hanno avuto ciascuno la propria verifica**, con esiti diversi:

| fronte | verifica | difetto principale |
|---|---|---|
| stima O/U di apertura (report 9 §5) | ✅ regge | fattore d'effetto gonfiato (1,87× non 2,6×), precedente non citato, errore atteso non stratificato |
| celle residue (report 9 §7) | ❌ **non regge** | il «2,84×» è attaccato alla cella dove non vale (Bayern-Hannover, favorito a 0.92) |
| tiro in porta da Understat (report 9 §6) | ✅ regge | «42 celle su 45» erano 39; l'anomalia Bundesliga non è campionamento; affidabilità della riga bersaglio 0,69-0,72, non 0,751 |
| motore dall'apertura (§8) | ✅ regge | il titolo: la dicotomia 1X2/totali non è dimostrata (diff-in-diff p = 0.043, fallisce Bonferroni) |
| fronte generale (§10) | ❌ **non regge** | il 73-8 è quello che esce anche da leghe rimescolate a caso; la scoperta su ρ si capovolge al θ di produzione |
| calibrazione (§11) | ❌ **non regge** | «onesti nella forma» era assenza di potenza; con un test potente la forma è storta |
| leve di panchina del DC (§12) | ✅ regge | narrazione sulla calibrazione basata su un bin da 8 celle; 18 test mai riportati |

**Tre fronti non hanno avuto una verifica esterna** e vanno letti con la sola
auto-confutazione dei rispettivi agenti (documentata nei JSON): il beat-the-close
(§7), il mercato campione (§9) e il GG/NG contro le quote vere
([`11_ggng.md`](11_ggng.md)). Per i primi due il rischio è basso — sono risultati
**negativi**, e un negativo sovra-dichiarato costa meno di un positivo
sovra-dichiarato; il terzo contiene la sua confutazione più forte al proprio
interno (C7-C8), che smonta il suo stesso fatto nuovo.

**La lezione trasversale**, che vale più dei singoli difetti: in **cinque casi su
sette** il problema non era il numero ma la statistica scelta per raccontarlo —
un conteggio di celle che non distingue il vero dal placebo, un indicatore senza
potenza letto come conferma, un ECE senza intervallo, una *z* anti-monotona nella
dimensione dell'effetto, una dicotomia fra «significativo» e «non significativo»
mai testata come differenza. Il rimedio è procedurale e va scritto: **ogni
statistica di testa deve avere il suo intervallo, e ogni «non c'è effetto» deve
avere la sua misura di potenza.**
