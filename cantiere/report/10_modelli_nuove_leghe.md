# Report 10 — La rosa dei modelli messa alla prova su Bundesliga e Ligue 1

Richiesta: *«valutare quanti più modelli, piste o cose possibili per queste due
leghe appena aggiunte»*.

Quattro fronti completati, tutti con parametri scelti **fuori campione** e
bootstrap appaiato B=10.000. Il quadro in una riga: **nessuna leva del mercato
si replica sulle due leghe nuove**, e due lezioni che il progetto dava per
acquisite risultano più fragili di quanto scritto. L'unico segnale positivo è
sul GG/NG.

Questo report è il seguito di [`06_tranche3.md`](06_tranche3.md) e in un punto
lo corregge (§2.2).

---

## 1 · Il quadro

| fronte | Bundesliga | Ligue 1 | mercati con CI conclusivo |
|---|---|---|--:|
| router double-Poisson θ (griglia) | ❌ negativo | ❌ negativo | **0 / 25** (e 2 e 4 *peggiorati*) |
| φ(\|λ−μ\|) (griglia 341 punti) | nel rumore | nel rumore | 0 (e 1 e 3 *peggiorati*) |
| devig di Shin | nel rumore | nel rumore | pooled: 1 (Brier) |
| ricalibrazione per-classe del mercato | nel rumore | nel rumore | 0 |
| power-devig | ❌ **peggiora** (CI conclusivo) | nel rumore | — |
| **ricalibrazione dei tassi sul GG/NG** | 🪑 **+0.00059, CI conclusivo** | nel rumore | 1 |

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
**4.9 × 10⁻¹⁰**, incluse le sequenze di θ scelte anno per anno. L'apparato, quando
la leva c'è, la trova.

Sulle due leghe nuove: **0 mercati su 25** con CI95 sotto zero, in entrambe;
2 (Bundesliga) e 4 (Ligue 1) mercati **conclusivamente peggiorati**. L'unico
residuo nominale — i totali in Bundesliga (over 1.5 −0.0013, over 2.5 −0.0008) —
non sopravvive a Bonferroni ed è **rovesciato in modo conclusivo in Ligue 1**
(over 1.5 **+0.0008**, CI [+0.0002, +0.0015]). Fallita la replica, resta rumore.

**Non è mancanza di potenza, è mancanza di effetto.** La profondità della valle
in-sample sul risultato esatto:

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

### 2.2 · Due lezioni del progetto che vanno corrette

**(a) «griglia > MLE» non è una proprietà dello stimatore.** Sul risultato
esatto la griglia ricade sul θ di massima verosimiglianza **entro mezzo passo in
5 leghe su 5** (SA 1.225 vs 1.232; Liga 1.250 vs 1.242; Bundesliga 1.075 vs
1.080; Ligue 1 1.100 vs 1.103; Premier 1.075 vs 1.085). Non è un caso: `fit_theta`
minimizza *esattamente* quel log-loss. Griglia e MLE divergono solo quando si
cambia **metrica** — cioè la frase giusta non è «la griglia stima meglio», ma
«mercati diversi vogliono θ diversi».

**(b) Il ribaltamento sulla Liga era la finestra dati, non lo stimatore.** Il
θ = 1.097 che era stato «ribaltato» **non è riproducibile su questa finestra**:
qui il MLE della Liga è **1.242**, stabilissimo (LOSO [1.202, 1.290]). La
differenza fra i due numeri è quali stagioni entrano nel fit, non quale
stimatore si usa.

**(c) Un corollario contro-intuitivo:** applicare a tutto il listino il θ alto
scelto sull'1X2 produce **meno** mercati conclusivi che usare il θ MLE (Serie A
4/25 contro 10/25; Liga 2/25 contro 6/25). Come costante unica per l'intero
listino, il θ da massima verosimiglianza resta il migliore.

---

## 3 · φ(|λ−μ|): nel rumore, e una confutazione la smonta

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

**La confutazione che conta.** Se la φ35 funzionasse *come dichiara*, la sua
dipendenza da |λ−μ| dovrebbe valere qualcosa. Rifatta la selezione sulla
sotto-griglia **κ = 0** — cioè un'inflazione-pareggio *costante*, la vecchia
draw-inflation già chiusa dal progetto — la φ costante fa **meglio o uguale**
alla φ35 sui mercati principali (Bundesliga pareggio 0.55103 contro 0.55125;
Ligue 1 doppia 1X identica, φ₀ = 0 in tutte e 7 le stagioni). La parte
«intelligente» della leva non si ripaga: quello che resta è una costante.

In Ligue 1 la selezione sceglie φ₀ = 0 in ogni stagione: la lega **non ha
deficit di pareggi**, come previsto dall'EDA prima di misurare. Previsione
dichiarata in anticipo e confermata.

---

## 4 · Il devig di Shin: la quarta e quinta replica

Il progetto misurava Shin ≥ moltiplicativo su 3/3 leghe senza mai concludere.
Con 5 leghe e 12.459 partite:

| confronto (pooled 5 leghe) | Δ | CI95 | verdetto |
|---|--:|---|---|
| Shin vs moltiplicativo, **log-loss 1X2** | −0.00034 | [−0.00068, +0.0000] | nel rumore (p = 0.052) |
| Shin vs moltiplicativo, **Brier 1X2** | −0.00021 | [−0.00039, −0.00001] | **conclusivo (meglio)** |
| power-devig vs moltiplicativo | −0.00042 | [−0.0011, +0.0002] | nel rumore |
| Shin vs power-devig | +0.00009 | [−0.0004, +0.0006] | nel rumore |

Leghe migliorate: **3 su 5**. Sulla finestra a 9 stagioni delle due leghe nuove
(che include il 2017-19, dove il book è Pinnacle e il margine è la metà): **nel
rumore in entrambe**, e il parametro z di Shin passa da ~0.0128 nel 2017-19 a
~0.0245 dal 2019-20 — coerente col fatto che il margine raddoppia.

**Lettura onesta:** Shin è *molto probabilmente* un filo meglio, e ora lo si può
dire con una metrica conclusiva (Brier) su 12.459 partite. Ma il log-loss —
la metrica ufficiale del progetto — resta a p = 0.052, cioè appena al di qua
della soglia. Non basta per toccare la fonte unica delle metriche.

---

## 5 · Le ricalibrazioni del mercato

**A · per-classe (pesi w_D, w_A).** Nel rumore in entrambe le leghe
(Bundesliga +0.00078, Ligue 1 +0.00076: entrambe *peggiorano* di poco). Ma il
dato interessante non è il guadagno, è il **segno**:

| lega | w_D fittato | famiglia |
|---|--:|---|
| serie_a | > 1 | «latina» (il mercato sotto-prezza il pareggio) |
| la_liga | > 1 | «latina» |
| **bundesliga** | **1.089** | **latina** |
| premier_league | < 1 | «inglese» |
| **ligue_1** | **0.981** | **inglese** |

Il progetto aveva archiviato la leva come «segno non universale». Con 5 leghe si
vede che il segno **non è casuale**: segue la natura della lega, la stessa che
l'EDA aveva letto in anticipo su φ₀. È una regolarità, non un rumore — solo che
è troppo piccola per pagare.

**B · tilt dei livelli.** Bundesliga c_λ = +0.019, c_μ = +0.022 (il mercato
sotto-stima i gol di ~2% su entrambi i lati); Ligue 1 c_λ = −0.010, c_μ = +0.022
(asimmetrico). Coerenti col tracer, nessun guadagno conclusivo a valle.

**C · power-devig.** In Bundesliga **peggiora con CI conclusivo** (+0.00035,
CI [+0.00004, +0.00066]) sia a 7 sia a 9 stagioni; in Ligue 1 nel rumore.
Pista chiusa anche fuori dalla Serie A.

---

## 6 · L'unico segnale positivo: il GG/NG in Bundesliga

**Ricalibrazione dei tassi (livello di μ) prima di derivare il GG/NG**,
parametri leave-one-season-out:

| lega | senza | con | Δ | CI95 | verdetto |
|---|--:|--:|--:|---|---|
| **bundesliga** | 0.6654 | **0.6648** | **+0.00059** | **[+0.00006, +0.00113]** | **conclusivo** |
| ligue_1 | 0.6847 | 0.6845 | +0.00023 | [−0.00029, +0.00072] | nel rumore |

È l'unica cella conclusiva positiva di tutto il blocco. Va presa con le molle:
**non sopravvive alla correzione di Bonferroni** per il numero di mercati
provati, e non si replica sull'altra lega. Ma cade sul mercato che il progetto
indica come prioritario — il GG/NG, l'unico senza quote nei dati — e nella
stessa direzione di un risultato già registrato altrove.

**E adesso quel mercato è verificabile.** Il lavoro sui dati (report 9 §2.4) ha
portato quote di chiusura GG/NG reali per 3.652 partite del 2017-19. Per la
prima volta si può misurare se il nostro prezzo GG/NG batte un book, invece di
limitarsi alla calibrazione. È la cosa più promettente uscita da tutta la
sessione, e non è ancora stata fatta.

---

## 7 · La rosa aggiornata, per le due leghe nuove

| leva | Bundesliga | Ligue 1 | motivo |
|---|---|---|---|
| market-implied (chiusura → matrice) | ⚽ titolare | ⚽ titolare | batte il DC-da-gol su 15/15 mercati |
| DC gol+xG (fallback senza quote) | ⚽ titolare | ⚽ titolare | batte la baseline, non il mercato |
| **router θ (dp)** | ❌ **bocciato** | ❌ **bocciato** | 0/25 conclusivi; θ ≈ 1.08-1.10, valle 6× più piatta che in Serie A |
| **φ(\|λ−μ\|)** | ❌ **bocciata** | ❌ **bocciata** | nel rumore, peggiora la doppia 1X; una φ *costante* fa meglio |
| **devig di Shin** | 🪑 panchina | 🪑 panchina | pooled 5 leghe: conclusivo su Brier, p = 0.052 su log-loss |
| **ricalibrazione per-classe** | 🪑 panchina | ❌ bocciata | segno corretto ma guadagno negativo |
| **power-devig** | ❌ bocciato | ❌ bocciato | peggiora con CI conclusivo in Bundesliga |
| **ricalibrazione-μ per il GG/NG** | 🪑 **panchina** | ❌ bocciata | +0.00059 CI conclusivo, non Bonferroni |
| stimatore chiusura O/U | ⚽ titolare | ⚽ titolare | **per-lega**, MAE 0.0122 / 0.0110 (report 9 §3) |

---

## 8 · Cosa resta da fare

Non completato per esaurimento del limite di sessione, in ordine di valore:

1. **GG/NG contro le quote vere** — ora possibile per 3.652 partite. È la pista
   con il valore più alto del progetto, e la sua premessa («non abbiamo quote
   GG/NG») è appena caduta;
2. **mercato campione di stagione** (simulatore Monte Carlo) per le due leghe —
   nuova famiglia di mercati, mai portata qui;
3. **beat-the-close** sulle due leghe (la Ligue 1 ha il margine più alto del
   campione: 5,02%);
4. **market-implied dall'apertura** (finestra di 9 stagioni invece di 7: più
   potenza statistica, e ora con i calendari di coppa corretti);
5. **audit di calibrazione** sui ~17 mercati che il book non quota;
6. **fronte generale pooled a 5 leghe** — la domanda «θ è una proprietà del
   calcio o del singolo mercato?» ha ora una risposta parziale (§2.1: due
   famiglie, non un valore unico), ma non è stata misurata come modello pooled;
7. le 4 leve di panchina del path DC e le covariate.

---

## 9 · Nota di metodo

I quattro fronti di questo report sono stati eseguiti da agenti che hanno
**completato i calcoli** ma sono stati interrotti prima di riportare: i numeri
qui sopra sono stati estratti dai loro output grezzi
(`cantiere/out/leve_*.json`) e non sono passati dalla verifica avversariale
prevista, tranne quella che ciascun agente ha svolto su sé stesso (documentata
nei rispettivi JSON). Il controllo di sanità del fronte θ — riproduzione esatta
di 18 numeri noti — è l'unica verifica esterna forte disponibile. **Un secondo
giro di confutazione su §4 e §6 resta da fare** prima di considerare quelle due
righe stabili.
